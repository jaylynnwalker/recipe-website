from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..models import CookingEvent, DeckEntry, Recipe
from ..schemas import DeckEntryCreate, DeckEntryUpdate
from ..serializers import recipe_to_dict
from .recipes import recipe_options

router = APIRouter(prefix='/deck', tags=['deck'])


def entry_options():
    return (selectinload(DeckEntry.recipe).options(*recipe_options()),)


def serialize(entry: DeckEntry) -> dict:
    return {'id': entry.id, 'servings': entry.servings, 'cooked': entry.cooked_at is not None, 'cooked_at': entry.cooked_at, 'recipe': recipe_to_dict(entry.recipe)}


def household_entry(entry_id: str, household_id: str, db: Session) -> DeckEntry:
    entry = db.scalar(select(DeckEntry).options(*entry_options()).where(DeckEntry.id == entry_id, DeckEntry.household_id == household_id))
    if not entry:
        raise HTTPException(status_code=404, detail='Meal not found')
    return entry


@router.get('')
async def list_deck(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    entries = db.scalars(select(DeckEntry).options(*entry_options()).where(DeckEntry.household_id == workspace.household_id).order_by(DeckEntry.position, DeckEntry.created_at)).all()
    return [serialize(entry) for entry in entries]


@router.post('', status_code=status.HTTP_201_CREATED)
async def add_to_deck(payload: DeckEntryCreate, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    recipe = db.scalar(select(Recipe).where(Recipe.id == payload.recipe_id, Recipe.household_id == workspace.household_id))
    if not recipe:
        raise HTTPException(status_code=404, detail='Recipe not found')
    position = db.scalar(select(func.count()).select_from(DeckEntry).where(DeckEntry.household_id == workspace.household_id)) or 0
    entry = DeckEntry(household_id=workspace.household_id, recipe_id=recipe.id, servings=payload.servings or recipe.base_servings, position=position)
    db.add(entry)
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail='Recipe is already on Meals on Deck')
    return serialize(household_entry(entry.id, workspace.household_id, db))


@router.patch('/{entry_id}')
async def update_deck_entry(entry_id: str, payload: DeckEntryUpdate, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    entry = household_entry(entry_id, workspace.household_id, db)
    if payload.servings is not None: entry.servings = payload.servings
    if payload.cooked is not None and payload.cooked != (entry.cooked_at is not None):
        if payload.cooked:
            entry.cooked_at = datetime.now(timezone.utc)
            db.add(CookingEvent(recipe_id=entry.recipe_id, actor_email=workspace.email))
        else: entry.cooked_at = None
    db.commit()
    db.expire_all()
    return serialize(household_entry(entry.id, workspace.household_id, db))


@router.delete('/completed', status_code=204)
async def clear_completed(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    entries = db.scalars(select(DeckEntry).where(DeckEntry.household_id == workspace.household_id, DeckEntry.cooked_at.is_not(None))).all()
    for entry in entries: db.delete(entry)
    db.commit()


@router.delete('/{entry_id}', status_code=204)
async def remove_from_deck(entry_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    db.delete(household_entry(entry_id, workspace.household_id, db)); db.commit()
