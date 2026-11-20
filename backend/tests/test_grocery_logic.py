from decimal import Decimal
from types import SimpleNamespace

from app.grocery import format_item_label, generate_items


def ingredient(name, quantity, unit):
    return SimpleNamespace(ingredient=SimpleNamespace(display_name=name, normalized_name=name.casefold()), quantity=Decimal(str(quantity)) if quantity is not None else None, unit=unit)


def deck(servings, base_servings, ingredients, cooked=False):
    return SimpleNamespace(servings=servings, cooked_at='done' if cooked else None, recipe=SimpleNamespace(base_servings=base_servings, ingredients=ingredients))


def test_serving_scaling_consolidation_and_staple_exclusion():
    entries = [
        deck(8, 4, [ingredient('Carrot', 2, 'pounds'), ingredient('Salt', 1, 'tsp')]),
        deck(2, 2, [ingredient('Carrot', 1, 'lb'), ingredient('Carrot', 8, 'oz'), ingredient('Garlic', 2, 'cloves')]),
        deck(4, 4, [ingredient('Ignored', 4, None)], cooked=True),
    ]
    staples = [SimpleNamespace(name='Salt')]
    items, excluded = generate_items(entries, staples)
    carrots = next(item for item in items if item.normalized_name == 'carrot')
    assert carrots.quantity == Decimal('5.5')
    assert carrots.unit == 'lb'
    assert carrots.category == 'Produce'
    assert excluded == ['Salt']
    assert all(item.name != 'Ignored' for item in items)
    assert format_item_label('Tomatoes', Decimal('20'), None) == '20 Tomatoes'


def test_incomplete_ingredients_are_preserved_without_unsafe_quantities():
    entries = [
        deck(4, 4, [ingredient('Fresh herbs', None, None), ingredient('Lime', 2, None)]),
        deck(2, 2, [ingredient('Fresh herbs', 1, None), ingredient('Lime', None, None)]),
    ]
    items, excluded = generate_items(entries, [])
    assert excluded == []
    assert next(item for item in items if item.normalized_name == 'fresh herbs').quantity is None
    assert next(item for item in items if item.normalized_name == 'lime').quantity is None
    assert all(item.unit is None for item in items)
