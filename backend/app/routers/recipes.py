import uuid
import re
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..models import Category, CookingEvent, Ingredient, IngredientMeasurement, Protein, Recipe, RecipeIngredient, RecipePhoto, RecipeStep, Tag
from ..schemas import PhotoRead, RecipeRead, RecipeWrite
from ..serializers import recipe_to_dict
from ..units import COMMON_UNITS, UNIT_ALIASES, normalize_unit


router = APIRouter(prefix='/recipes', tags=['recipes'])
ALLOWED_IMAGES = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}
COMMON_PROTEINS = ['Chicken', 'Beef', 'Pork', 'Turkey', 'Lamb', 'Fish', 'Shellfish', 'Eggs', 'Tofu', 'Tempeh', 'Beans', 'Lentils', 'Other', 'None']


def recipe_options():
    return (selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient), selectinload(Recipe.ingredients).selectinload(RecipeIngredient.alternative_measurements), selectinload(Recipe.steps), selectinload(Recipe.tags), selectinload(Recipe.categories), selectinload(Recipe.proteins), selectinload(Recipe.photos), selectinload(Recipe.cooking_events))


def get_household_recipe(recipe_id: str, household_id: str, db: Session) -> Recipe:
    recipe = db.scalar(select(Recipe).options(*recipe_options()).where(Recipe.id == recipe_id, Recipe.household_id == household_id))
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Recipe not found')
    return recipe


def get_or_create_named(db: Session, model, name: str):
    value = ' '.join(name.split())
    normalized = normalize_classification(value)
    existing = next((item for item in db.scalars(select(model)).all() if normalize_classification(item.name) == normalized), None)
    if existing:
        return existing
    item = model(name=value)
    db.add(item)
    db.flush()
    return item


def normalize_classification(value: str) -> str:
    return re.sub(r'[\s_-]+', ' ', value.strip()).casefold()


def canonical_cuisine(db: Session, household_id: str, value: str) -> str:
    cleaned = ' '.join(value.split())
    if not cleaned:
        return ''
    normalized = normalize_classification(cleaned)
    existing = db.scalars(select(Recipe.cuisine).where(Recipe.household_id == household_id, Recipe.cuisine != '')).all()
    return next((name for name in existing if normalize_classification(name) == normalized), cleaned)


def apply_recipe_payload(recipe: Recipe, payload: RecipeWrite, db: Session):
    recipe.title = payload.title.strip()
    recipe.description = payload.description
    recipe.status = payload.status
    recipe.cuisine = canonical_cuisine(db, recipe.household_id, payload.cuisine)
    recipe.prep_minutes = payload.prep_minutes
    recipe.cook_minutes = payload.cook_minutes
    recipe.additional_time_minutes = payload.additional_time_minutes
    recipe.additional_time_label = payload.additional_time_label or 'Additional'
    recipe.base_servings = payload.base_servings
    recipe.yield_unit = payload.yield_unit or 'servings'
    recipe.notes = payload.notes
    recipe.source_type = payload.source.type
    recipe.source_label = payload.source.label
    recipe.source_url = str(payload.source.url) if payload.source.url else None
    recipe.source_page = payload.source.page
    recipe.tags = [get_or_create_named(db, Tag, name) for name in payload.tags]
    recipe.categories = [get_or_create_named(db, Category, name) for name in payload.categories]
    recipe.proteins = [get_or_create_named(db, Protein, name) for name in payload.proteins]
    if recipe.ingredients:
        recipe.ingredients.clear()
        db.flush()
    for position, item in enumerate(payload.ingredients):
        normalized = ' '.join(item.name.split()).casefold()
        ingredient = db.scalar(select(Ingredient).where(Ingredient.normalized_name == normalized))
        if not ingredient:
            ingredient = Ingredient(display_name=' '.join(item.name.split()), normalized_name=normalized)
            db.add(ingredient)
            db.flush()
        recipe.ingredients.append(RecipeIngredient(position=position, ingredient=ingredient, quantity=item.quantity, unit=item.unit, note=item.note, optional=item.optional, package_detail=item.package_detail, alternative_measurements=[IngredientMeasurement(position=index, quantity=measurement.quantity, unit=measurement.unit) for index, measurement in enumerate(item.alternative_measurements)]))
    if recipe.steps:
        recipe.steps.clear()
        db.flush()
    recipe.steps.extend(RecipeStep(position=position, instruction=step.instruction, tip=step.tip) for position, step in enumerate(payload.steps))


@router.get('', response_model=list[RecipeRead])
async def list_recipes(q: str | None = Query(default=None, max_length=200), status_filter: str | None = Query(default=None, alias='status'), cuisine: str | None = Query(default=None, max_length=100), category: str | None = Query(default=None, max_length=100), protein: str | None = Query(default=None, max_length=100), tag: str | None = Query(default=None, max_length=100), max_minutes: int | None = Query(default=None, ge=0), workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    statement = select(Recipe).options(*recipe_options()).where(Recipe.household_id == workspace.household_id)
    if status_filter:
        statement = statement.where(Recipe.status == status_filter)
    if cuisine:
        statement = statement.where(Recipe.cuisine == cuisine)
    if category:
        statement = statement.join(Recipe.categories).where(Category.name == category)
    if protein:
        statement = statement.join(Recipe.proteins).where(Protein.name == protein)
    if tag:
        statement = statement.join(Recipe.tags).where(Tag.name == tag)
    if max_minutes is not None:
        statement = statement.where(Recipe.prep_minutes + Recipe.cook_minutes <= max_minutes)
    if q:
        term = f'%{q.strip()}%'
        ingredient_recipe_ids = select(RecipeIngredient.recipe_id).join(RecipeIngredient.ingredient).where(Ingredient.display_name.ilike(term))
        tag_recipe_ids = select(Recipe.id).join(Recipe.tags).where(Tag.name.ilike(term))
        category_recipe_ids = select(Recipe.id).join(Recipe.categories).where(Category.name.ilike(term))
        protein_recipe_ids = select(Recipe.id).join(Recipe.proteins).where(Protein.name.ilike(term))
        statement = statement.where(or_(Recipe.title.ilike(term), Recipe.cuisine.ilike(term), Recipe.id.in_(ingredient_recipe_ids), Recipe.id.in_(tag_recipe_ids), Recipe.id.in_(category_recipe_ids), Recipe.id.in_(protein_recipe_ids)))
    recipes = db.scalars(statement.order_by(Recipe.updated_at.desc())).unique().all()
    return [recipe_to_dict(recipe) for recipe in recipes]


@router.get('/classifications')
async def list_classifications(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipes = db.scalars(select(Recipe).options(selectinload(Recipe.tags), selectinload(Recipe.categories), selectinload(Recipe.proteins)).where(Recipe.household_id == workspace.household_id)).unique().all()
    def unique(values):
        result = {}
        for value in values:
            cleaned = ' '.join(value.split())
            if cleaned:
                result.setdefault(normalize_classification(cleaned), cleaned)
        return sorted(result.values(), key=str.casefold)
    return {
        'categories': unique(category.name for recipe in recipes for category in recipe.categories),
        'cuisines': unique(recipe.cuisine for recipe in recipes),
        'tags': unique(tag.name for recipe in recipes for tag in recipe.tags),
        'proteins': unique([*COMMON_PROTEINS, *(protein.name for recipe in recipes for protein in recipe.proteins)]),
    }


@router.get('/units')
async def list_units(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    stored = db.scalars(select(RecipeIngredient.unit).join(Recipe).where(Recipe.household_id == workspace.household_id, RecipeIngredient.unit.is_not(None))).all()
    options = list(COMMON_UNITS)
    known = {unit.casefold() for unit in options}
    for value in stored:
        unit = normalize_unit(value)
        if unit and unit.casefold() not in known:
            options.append(unit); known.add(unit.casefold())
    return {'options': options, 'aliases': UNIT_ALIASES}


@router.post('', response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(payload: RecipeWrite, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = Recipe(household_id=workspace.household_id, title=payload.title, status=payload.status)
    db.add(recipe)
    apply_recipe_payload(recipe, payload, db)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A recipe with this title already exists')
    return recipe_to_dict(get_household_recipe(recipe.id, workspace.household_id, db))


@router.get('/{recipe_id}', response_model=RecipeRead)
async def retrieve_recipe(recipe_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    return recipe_to_dict(get_household_recipe(recipe_id, workspace.household_id, db))


@router.put('/{recipe_id}', response_model=RecipeRead)
async def update_recipe(recipe_id: str, payload: RecipeWrite, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = get_household_recipe(recipe_id, workspace.household_id, db)
    apply_recipe_payload(recipe, payload, db)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='A recipe with this title already exists')
    return recipe_to_dict(get_household_recipe(recipe.id, workspace.household_id, db))


@router.delete('/{recipe_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(recipe_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = get_household_recipe(recipe_id, workspace.household_id, db)
    media_root = get_settings().media_root
    for photo in recipe.photos:
        (media_root / photo.storage_name).unlink(missing_ok=True)
    db.delete(recipe)
    db.commit()


@router.post('/{recipe_id}/photos', response_model=PhotoRead, status_code=status.HTTP_201_CREATED)
async def upload_photo(recipe_id: str, file: UploadFile = File(...), alt_text: str = Form(default='Recipe photo', max_length=300), workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = get_household_recipe(recipe_id, workspace.household_id, db)
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail='Only JPEG, PNG, and WebP images are allowed')
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='Image is too large')
    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Image content is invalid')
    settings.media_root.mkdir(parents=True, exist_ok=True)
    storage_name = f'{uuid.uuid4()}{ALLOWED_IMAGES[file.content_type]}'
    destination = settings.media_root / storage_name
    destination.write_bytes(content)
    for existing in recipe.photos:
        existing.is_cover = False
    photo = RecipePhoto(recipe=recipe, storage_name=storage_name, original_name=Path(file.filename or 'upload').name[:255], media_type=file.content_type, alt_text=alt_text, position=len(recipe.photos), is_cover=True)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {'id': photo.id, 'url': f'/media/{photo.storage_name}', 'alt_text': photo.alt_text, 'media_type': photo.media_type}


@router.post('/{recipe_id}/made-this', response_model=RecipeRead)
async def made_this(recipe_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = get_household_recipe(recipe_id, workspace.household_id, db)
    db.add(CookingEvent(recipe=recipe, actor_email=workspace.email))
    db.commit()
    return recipe_to_dict(get_household_recipe(recipe.id, workspace.household_id, db))
