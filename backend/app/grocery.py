from dataclasses import dataclass
from decimal import Decimal
import re

from .units import UNIT_FACTORS, normalize_unit

PRODUCE = {'apple', 'avocado', 'basil', 'broccoli', 'carrot', 'cilantro', 'cucumber', 'garlic', 'ginger', 'lemon', 'lime', 'mushroom', 'onion', 'pepper', 'potato', 'spinach', 'tomato'}
MEAT = {'beef', 'chicken', 'fish', 'pork', 'salmon', 'sausage', 'shrimp', 'steak', 'turkey'}
DAIRY = {'butter', 'cheese', 'cream', 'egg', 'milk', 'parmesan', 'yogurt'}
BAKERY = {'bagel', 'bread', 'bun', 'tortilla'}
FROZEN = {'frozen', 'ice cream'}


def normalize_name(value: str) -> str:
    return ' '.join(re.sub(r'[^a-z0-9 ]+', ' ', value.casefold()).split())


def ingredient_category(name: str) -> str:
    words = set(normalize_name(name).split())
    if words & PRODUCE: return 'Produce'
    if words & MEAT: return 'Meat & seafood'
    if words & DAIRY: return 'Dairy & eggs'
    if words & BAKERY: return 'Bakery'
    if words & FROZEN: return 'Frozen'
    return 'Pantry'


@dataclass
class GeneratedItem:
    name: str
    normalized_name: str
    quantity: Decimal | None
    unit: str | None
    category: str
    source_key: str


def generate_items(deck_entries, pantry_staples) -> tuple[list[GeneratedItem], list[str]]:
    staples = {normalize_name(item.name): item.name for item in pantry_staples}
    excluded: dict[str, str] = {}
    combined: dict[str, GeneratedItem] = {}
    for entry in deck_entries:
        if entry.cooked_at is not None:
            continue
        scale = Decimal(entry.servings) / Decimal(entry.recipe.base_servings)
        for recipe_item in entry.recipe.ingredients:
            name = recipe_item.ingredient.display_name
            normalized = recipe_item.ingredient.normalized_name or normalize_name(name)
            if normalized in staples:
                excluded[normalized] = staples[normalized]
                continue
            unit = normalize_unit(recipe_item.unit)
            unit_group = UNIT_FACTORS.get(unit, (unit or '', Decimal('1')))[0]
            key = f'{normalized}|{unit_group}'
            quantity = Decimal(str(recipe_item.quantity)) * scale if recipe_item.quantity is not None else None
            if key in combined:
                existing = combined[key]
                if existing.quantity is not None and quantity is not None:
                    incoming_factor = UNIT_FACTORS.get(unit, (unit, Decimal('1')))[1]
                    existing_factor = UNIT_FACTORS.get(existing.unit, (existing.unit, Decimal('1')))[1]
                    existing.quantity += quantity * incoming_factor / existing_factor
                else:
                    existing.quantity = None
            else:
                combined[key] = GeneratedItem(name=name, normalized_name=normalized, quantity=quantity, unit=unit, category=ingredient_category(name), source_key=key)
    return sorted(combined.values(), key=lambda item: (item.category, item.name.casefold())), sorted(excluded.values(), key=str.casefold)


def format_item_label(name: str, quantity: Decimal | None, unit: str | None) -> str:
    if quantity is None:
        return name
    amount = f'{quantity.normalize():f}' if quantity else '0'
    if '.' in amount:
        amount = amount.rstrip('0').rstrip('.')
    return ' '.join(part for part in (amount, unit, name) if part)
