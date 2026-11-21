from decimal import Decimal
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..grocery import QuantityComponent, format_item_label, generate_items, ingredient_category, normalize_name, normalize_unit
from ..models import DeckEntry, GroceryExcludedStaple, GroceryItem, GroceryList, PantryStaple, Recipe
from ..schemas import GroceryItemCreate, GroceryItemUpdate
from .deck import entry_options

router = APIRouter(prefix='/grocery-list', tags=['grocery list'])


def list_options():
    return (selectinload(GroceryList.items).selectinload(GroceryItem.source_recipes), selectinload(GroceryList.excluded_staples))


def get_list(household_id: str, db: Session, create: bool = True) -> GroceryList:
    grocery = db.scalar(select(GroceryList).options(*list_options()).where(GroceryList.household_id == household_id))
    if not grocery and create:
        grocery = GroceryList(household_id=household_id)
        db.add(grocery); db.commit()
        grocery = db.scalar(select(GroceryList).options(*list_options()).where(GroceryList.id == grocery.id))
    return grocery


def item_dict(item: GroceryItem) -> dict:
    try: details = json.loads(item.quantity_details or '[]')
    except json.JSONDecodeError: details = []
    if not details and item.quantity is not None:
        details = [{'quantity': str(item.quantity), 'unit': item.unit, 'package_detail': None}]
    components = [QuantityComponent(Decimal(str(value['quantity'])) if value.get('quantity') is not None else None, value.get('unit'), value.get('package_detail')) for value in details]
    api_components = [{'quantity': float(value.quantity) if value.quantity is not None else None, 'unit': value.unit, 'package_detail': value.package_detail} for value in components]
    if item.is_manual:
        display_name = item.label
    elif item.source_key and item.source_key.startswith('ingredient:'):
        display_name = item.label.split(' — ', 1)[0]
    else:
        display_name = item.normalized_name.capitalize()
    display_label = format_item_label(display_name, components=components) if components else display_name
    return {'id': item.id, 'label': item.label, 'display_label': display_label, 'name': item.normalized_name, 'quantity': float(item.quantity) if item.quantity is not None else None, 'unit': item.unit, 'components': api_components, 'sources': [{'id': recipe.id, 'title': recipe.title} for recipe in item.source_recipes], 'category': item.category, 'checked': item.checked, 'manual': item.is_manual}


def list_dict(grocery: GroceryList) -> dict:
    items = sorted(grocery.items, key=lambda item: (item.category.casefold(), item.position, item.label.casefold()))
    excluded = sorted(grocery.excluded_staples, key=lambda item: item.name.casefold())
    return {'id': grocery.id, 'updated_at': grocery.updated_at, 'items': [item_dict(item) for item in items], 'excluded_staples': [{'id': item.id, 'name': item.name} for item in excluded]}


def generated_snapshot(household_id: str, db: Session):
    deck = db.scalars(select(DeckEntry).options(*entry_options()).where(DeckEntry.household_id == household_id).order_by(DeckEntry.position)).all()
    staples = db.scalars(select(PantryStaple).where(PantryStaple.household_id == household_id)).all()
    return generate_items(deck, staples)


def component_payload(item) -> list[dict]:
    return [{'quantity': str(component.quantity) if component.quantity is not None else None, 'unit': component.unit, 'package_detail': component.package_detail} for component in item.components]


def stored_component_signature(item: GroceryItem) -> list[tuple[str | None, str | None, str | None]]:
    try: values = json.loads(item.quantity_details or '[]')
    except json.JSONDecodeError: values = []
    if not values and item.quantity is not None: values = [{'quantity': str(item.quantity), 'unit': item.unit}]
    return [(str(value.get('quantity')) if value.get('quantity') is not None else None, value.get('unit'), value.get('package_detail')) for value in values]


def generated_component_signature(item) -> list[tuple[str | None, str | None, str | None]]:
    return [(str(component.quantity) if component.quantity is not None else None, component.unit, component.package_detail) for component in item.components]


def generated_label(item) -> str:
    return format_item_label(item.name, components=item.components)


def generated_by_name(grocery: GroceryList) -> dict[str, list[GroceryItem]]:
    result: dict[str, list[GroceryItem]] = {}
    for item in grocery.items:
        if not item.is_manual:
            result.setdefault(normalize_name(item.normalized_name), []).append(item)
    return result


@router.get('')
async def retrieve_list(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    return list_dict(get_list(workspace.household_id, db))


@router.post('/preview')
async def preview_update(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    grocery = get_list(workspace.household_id, db)
    generated, excluded = generated_snapshot(workspace.household_id, db)
    manual_names = {normalize_name(item.normalized_name) for item in grocery.items if item.is_manual}
    excluded = [name for name in excluded if normalize_name(name) not in manual_names]
    existing = generated_by_name(grocery)
    incoming = {item.normalized_name: item for item in generated}
    additions = [generated_label(item) for key, item in incoming.items() if key not in existing]
    updates = [generated_label(item) for key, item in incoming.items() if key in existing and (len(existing[key]) > 1 or stored_component_signature(existing[key][0]) != generated_component_signature(item) or {recipe.id for recipe in existing[key][0].source_recipes} != {source.id for source in item.sources})]
    removals = [stored.label for key, items in existing.items() if key not in incoming for stored in items if not stored.checked]
    unchanged = sum(1 for key in incoming if key in existing and generated_label(incoming[key]) not in updates)
    return {'additions': additions, 'updates': updates, 'removals': removals, 'excluded_staples': excluded, 'unchanged_count': unchanged}


@router.post('/apply')
async def apply_update(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    grocery = get_list(workspace.household_id, db)
    generated, excluded = generated_snapshot(workspace.household_id, db)
    manual_names = {normalize_name(item.normalized_name) for item in grocery.items if item.is_manual}
    excluded = [name for name in excluded if normalize_name(name) not in manual_names]
    existing = generated_by_name(grocery)
    incoming_names = {item.normalized_name for item in generated}
    for position, item in enumerate(generated):
        candidates = existing.get(item.normalized_name, [])
        stored = candidates[0] if candidates else None
        details = component_payload(item)
        if stored:
            stored.checked = any(candidate.checked for candidate in candidates)
            stored.label = generated_label(item); stored.normalized_name = item.normalized_name; stored.quantity = item.quantity; stored.unit = item.unit; stored.quantity_details = json.dumps(details); stored.category = item.category; stored.source_key = item.source_key; stored.position = position
            stored.source_recipes = db.scalars(select(Recipe).where(Recipe.id.in_([source.id for source in item.sources]), Recipe.household_id == workspace.household_id)).all()
            for duplicate in candidates[1:]: db.delete(duplicate)
        else:
            stored = GroceryItem(grocery_list_id=grocery.id, label=generated_label(item), normalized_name=item.normalized_name, quantity=item.quantity, unit=item.unit, quantity_details=json.dumps(details), category=item.category, source_key=item.source_key, position=position)
            stored.source_recipes = db.scalars(select(Recipe).where(Recipe.id.in_([source.id for source in item.sources]), Recipe.household_id == workspace.household_id)).all()
            db.add(stored)
    for name, stored_items in existing.items():
        if name not in incoming_names:
            for stored in stored_items:
                if not stored.checked: db.delete(stored)
    for stored in list(grocery.excluded_staples): db.delete(stored)
    db.flush()
    for name in excluded: db.add(GroceryExcludedStaple(grocery_list_id=grocery.id, name=name, normalized_name=normalize_name(name)))
    db.commit()
    db.expire_all()
    return list_dict(get_list(workspace.household_id, db))


@router.post('/items', status_code=status.HTTP_201_CREATED)
async def add_item(payload: GroceryItemCreate, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    grocery = get_list(workspace.household_id, db)
    normalized = normalize_name(payload.label)
    item = GroceryItem(grocery_list_id=grocery.id, label=payload.label.strip(), normalized_name=normalized, quantity=Decimal(str(payload.quantity)) if payload.quantity is not None else None, unit=normalize_unit(payload.unit), category=payload.category.strip(), is_manual=True, position=len(grocery.items))
    db.add(item); db.commit(); db.refresh(item)
    return item_dict(item)


def household_item(item_id: str, household_id: str, db: Session) -> GroceryItem:
    item = db.scalar(select(GroceryItem).join(GroceryList).where(GroceryItem.id == item_id, GroceryList.household_id == household_id))
    if not item: raise HTTPException(status_code=404, detail='Grocery item not found')
    return item


@router.patch('/items/{item_id}')
async def update_item(item_id: str, payload: GroceryItemUpdate, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    item = household_item(item_id, workspace.household_id, db)
    if payload.label is not None: item.label = payload.label.strip(); item.normalized_name = normalize_name(payload.label)
    if 'quantity' in payload.model_fields_set: item.quantity = Decimal(str(payload.quantity)) if payload.quantity is not None else None
    if 'unit' in payload.model_fields_set: item.unit = normalize_unit(payload.unit)
    if payload.category is not None: item.category = payload.category.strip()
    if payload.checked is not None: item.checked = payload.checked
    db.commit(); db.refresh(item)
    return item_dict(item)


@router.delete('/items/{item_id}', status_code=204)
async def delete_item(item_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    db.delete(household_item(item_id, workspace.household_id, db)); db.commit()


@router.post('/excluded/{excluded_id}/add-back')
async def add_back(excluded_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    excluded = db.scalar(select(GroceryExcludedStaple).join(GroceryList).where(GroceryExcludedStaple.id == excluded_id, GroceryList.household_id == workspace.household_id))
    if not excluded: raise HTTPException(status_code=404, detail='Excluded staple not found')
    item = GroceryItem(grocery_list_id=excluded.grocery_list_id, label=excluded.name, normalized_name=excluded.normalized_name, category=ingredient_category(excluded.name), is_manual=True)
    db.add(item); db.delete(excluded); db.commit(); db.refresh(item)
    return item_dict(item)
