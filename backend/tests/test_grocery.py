from decimal import Decimal
from types import SimpleNamespace

from app.grocery import generate_items, normalize_name


def ingredient(name, quantity, unit, package_detail=None):
    return SimpleNamespace(ingredient=SimpleNamespace(display_name=name), quantity=quantity, unit=unit, package_detail=package_detail)


def deck(recipe_id, title, ingredients, servings=4, base_servings=4):
    recipe = SimpleNamespace(id=recipe_id, title=title, ingredients=ingredients, base_servings=base_servings)
    return SimpleNamespace(recipe=recipe, servings=servings, cooked_at=None)


def generated(entries):
    return generate_items(entries, [])[0]


def test_ingredient_names_normalize_plurals_formatting_spelling_and_safe_aliases():
    assert normalize_name('Onions, diced') == normalize_name('onion') == 'onion'
    assert normalize_name('CHILLI powder') == 'chili powder'
    assert normalize_name('Scallions') == normalize_name('green onions') == 'green onion'
    assert normalize_name("Confectioners' sugar") == normalize_name('powdered sugar') == 'powdered sugar'
    assert normalize_name('salted butter') != normalize_name('unsalted butter')


def test_duplicate_counts_and_aliases_consolidate_and_retain_sources():
    items = generated([
        deck('one', 'First Dinner', [ingredient('Green onions', 2, 'whole')]),
        deck('two', 'Second Dinner', [ingredient('Scallions', 3, 'whole')]),
    ])
    assert len(items) == 1
    assert items[0].normalized_name == 'green onion'
    assert [(part.quantity, part.unit) for part in items[0].components] == [(Decimal('5'), 'whole')]
    assert {source.title for source in items[0].sources} == {'First Dinner', 'Second Dinner'}


def test_practical_volume_mass_and_spice_units_are_selected():
    items = {item.normalized_name: item for item in generated([deck('one', 'Baking', [
        ingredient('Milk', 4, 'cup'),
        ingredient('Cinnamon', 3, 'tsp'),
        ingredient('All-purpose flour', 1, 'cup'),
        ingredient('All purpose flour', 4, 'oz'),
    ])])}
    assert [(part.quantity, part.unit) for part in items['milk'].components] == [(Decimal('1'), 'qt')]
    assert [(part.quantity, part.unit) for part in items['cinnamon'].components] == [(Decimal('1'), 'tbsp')]
    flour = items['all purpose flour'].components[0]
    assert flour.unit == 'oz' and Decimal('8.2') < flour.quantity < Decimal('8.3')


def test_incompatible_volume_and_weight_remain_components_of_one_item():
    item = generated([deck('one', 'Two Measurements', [ingredient('Milk', 1, 'cup'), ingredient('milk', 8, 'oz')])])[0]
    assert item.normalized_name == 'milk'
    assert {(part.unit, round(part.quantity, 2)) for part in item.components} == {('fl oz', Decimal('8.00')), ('oz', Decimal('8.00'))}


def test_meaningfully_different_ingredients_do_not_consolidate():
    items = generated([deck('one', 'Butter Test', [ingredient('Salted butter', 1, 'lb'), ingredient('Unsalted butter', 1, 'lb')])])
    assert {item.normalized_name for item in items} == {'salted butter', 'unsalted butter'}


def test_grocery_labels_put_name_first_and_preserve_package_counts():
    item = generated([deck('one', 'Casserole', [ingredient('Cream of chicken', 2, 'can', '10.5 oz each')])])[0]
    from app.grocery import format_item_label
    assert format_item_label(item.name, components=item.components) == 'Cream of chicken — 2 × 10.5 oz cans'
    assert format_item_label('Lemon', components=[item.components[0].__class__(None, None)]) == 'Lemon'
    assert format_item_label('Sugar', Decimal('1.5'), 'lb') == 'Sugar — 1 1/2 lb'
