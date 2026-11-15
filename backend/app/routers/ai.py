from datetime import datetime, timedelta, timezone
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import AIInvalidResponse, AIUnavailable, BudgetExceeded, RECIPE_SCHEMA, recipe_draft, run_structured, usage_summary
from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..grocery import normalize_name
from ..models import PantryStaple, Recipe
from ..schemas import CookingAssistRequest, HelpPickRequest, IngredientIdeaRequest
from ..serializers import recipe_to_dict
from .recipes import get_household_recipe, recipe_options

router = APIRouter(prefix='/ai', tags=['ai'])
IDEAS_SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {'ideas': {'type': 'array', 'items': RECIPE_SCHEMA}}, 'required': ['ideas']}
ANSWER_SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {'answer': {'type': 'string'}}, 'required': ['answer']}


def ai_http_error(error: Exception):
    if isinstance(error, BudgetExceeded): return HTTPException(429, str(error))
    if isinstance(error, AIUnavailable): return HTTPException(503, str(error))
    if isinstance(error, (AIInvalidResponse, json.JSONDecodeError, ValueError)): return HTTPException(502, 'The AI response was invalid. No recipe was saved.')
    return HTTPException(502, 'The AI request failed. Please try again.')


@router.get('/usage')
async def get_usage(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    return usage_summary(db, workspace.household_id)


def all_recipes(db, household_id):
    return db.scalars(select(Recipe).options(*recipe_options()).where(Recipe.household_id == household_id, Recipe.status != 'Archived').order_by(Recipe.updated_at.desc())).unique().all()


@router.post('/what-can-i-make')
async def what_can_i_make(payload: IngredientIdeaRequest, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    available = {normalize_name(value) for value in payload.ingredients if value.strip()}
    if payload.include_pantry_staples:
        available.update(item.normalized_name for item in db.scalars(select(PantryStaple).where(PantryStaple.household_id == workspace.household_id)).all())
    matches = []
    for recipe in all_recipes(db, workspace.household_id):
        required = [item.ingredient.normalized_name for item in recipe.ingredients if not item.optional]
        missing = [item.ingredient.display_name for item in recipe.ingredients if not item.optional and item.ingredient.normalized_name not in available]
        matched = len(required) - len(missing)
        if matched: matches.append({'recipe': recipe_to_dict(recipe), 'missing_ingredients': missing, 'matched_count': matched})
    matches.sort(key=lambda item: (len(item['missing_ingredients']), -item['matched_count']))
    ideas = []
    if payload.generate_ai:
        prompt = f"Available ingredients: {', '.join(sorted(available))}. Suggest up to 3 practical dinner recipes. Use only stated ingredients unless a missing item is clearly listed in the recipe. Never claim unavailable facts."
        try:
            result = await run_structured(db, workspace.household_id, 'recipe_ideas', 'You suggest concise household recipes. Never invent quantities you are uncertain about; use null. Return reviewable drafts only.', prompt, IDEAS_SCHEMA)
            ideas = [recipe_draft(idea, {'type': 'ai', 'label': 'OpenAI generated idea', 'url': None, 'page': None}) for idea in result.get('ideas', [])[:3]]
        except Exception as error: raise ai_http_error(error)
    return {'saved_matches': matches[:10], 'generated_ideas': ideas}


@router.post('/help-me-pick')
async def help_me_pick(payload: HelpPickRequest, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipes = all_recipes(db, workspace.household_id); cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    if payload.mode == 'Our Rotation': selected = [recipe for recipe in recipes if recipe.status == 'Our Rotation']
    elif payload.mode == 'Want to Try': selected = [recipe for recipe in recipes if recipe.status == 'Want to Try']
    elif payload.mode == 'Forgotten Favorites': selected = [recipe for recipe in recipes if recipe.status == 'Our Rotation' and (not recipe.cooking_events or max(event.cooked_at for event in recipe.cooking_events).replace(tzinfo=timezone.utc) < cutoff)]
    else: selected = recipes
    ideas = []
    if payload.generate_ai:
        try:
            result = await run_structured(db, workspace.household_id, 'recipe_ideas', 'Suggest one appealing dinner recipe as a reviewable draft. Do not claim it is saved or tested.', f'Create one new dinner idea complementary to this preference: {payload.mode}.', IDEAS_SCHEMA)
            ideas = [recipe_draft(idea, {'type': 'ai', 'label': 'OpenAI generated idea', 'url': None, 'page': None}) for idea in result.get('ideas', [])[:1]]
        except Exception as error: raise ai_http_error(error)
    return {'saved_recipes': [recipe_to_dict(recipe) for recipe in selected[:6]], 'generated_ideas': ideas}


@router.post('/assist')
async def cooking_assist(payload: CookingAssistRequest, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = get_household_recipe(payload.recipe_id, workspace.household_id, db)
    context = recipe_to_dict(recipe)
    if payload.current_step is not None: context['current_step'] = payload.current_step + 1
    try:
        result = await run_structured(db, workspace.household_id, 'cooking_assistance', 'Answer only about the supplied recipe. Clearly label substitutions or adaptations and never modify the saved recipe.', f'Recipe context: {json.dumps(context, default=str)}\nQuestion: {payload.question}', ANSWER_SCHEMA)
        return {'answer': result['answer']}
    except Exception as error: raise ai_http_error(error)
