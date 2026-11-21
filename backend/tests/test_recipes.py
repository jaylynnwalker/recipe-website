import pytest

pytestmark = pytest.mark.anyio

async def test_recipe_crud_search_and_inline_tip(authenticated, recipe_payload):
    created = await authenticated.post('/api/recipes', json=recipe_payload)
    assert created.status_code == 201
    recipe_id = created.json()['id']
    assert created.json()['steps'][0]['tip'] == 'Use a wide pan.'
    assert (await authenticated.get('/api/recipes', params={'q': 'Carrots'})).json()[0]['id'] == recipe_id

    updated_payload = {**recipe_payload, 'title': 'Updated Supper', 'base_servings': 6}
    updated = await authenticated.put(f'/api/recipes/{recipe_id}', json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()['base_servings'] == 6
    cooked = await authenticated.post(f'/api/recipes/{recipe_id}/made-this')
    assert cooked.status_code == 200
    assert len(cooked.json()['cooking_history']) == 1
    assert (await authenticated.delete(f'/api/recipes/{recipe_id}')).status_code == 204
    assert (await authenticated.get(f'/api/recipes/{recipe_id}')).status_code == 404


async def test_classifications_reuse_normalized_values(authenticated, recipe_payload):
    first = {**recipe_payload, 'title': 'First Supper', 'cuisine': 'Italian', 'categories': ['Weeknight Dinner'], 'tags': ['Quick-Fix']}
    second = {**recipe_payload, 'title': 'Second Supper', 'cuisine': ' italian ', 'categories': [' weeknight_dinner '], 'tags': ['quick fix']}
    assert (await authenticated.post('/api/recipes', json=first)).status_code == 201
    created = await authenticated.post('/api/recipes', json=second)
    assert created.status_code == 201
    assert created.json()['cuisine'] == 'Italian'
    assert created.json()['categories'] == ['Weeknight Dinner']
    assert created.json()['tags'] == ['Quick-Fix']
    assert (await authenticated.get('/api/recipes/classifications')).json() == {
        'categories': ['Weeknight Dinner'], 'cuisines': ['Italian'], 'proteins': ['Beans', 'Beef', 'Chicken', 'Eggs', 'Fish', 'Lamb', 'Lentils', 'None', 'Other', 'Pork', 'Shellfish', 'Tempeh', 'Tofu', 'Turkey'], 'tags': ['Quick-Fix'],
    }


async def test_recipe_units_are_standardized_and_custom_units_remain_available(authenticated, recipe_payload):
    payload = {**recipe_payload, 'title': 'Measured Supper', 'ingredients': [
        {'name': 'Stock', 'quantity': 2, 'unit': 'cups', 'note': None, 'optional': False},
        {'name': 'Saffron', 'quantity': 4, 'unit': 'threads', 'note': None, 'optional': False},
        {'name': 'Onion', 'quantity': 1, 'unit': '', 'note': None, 'optional': False},
    ]}
    created = await authenticated.post('/api/recipes', json=payload)
    assert created.status_code == 201
    assert [item['unit'] for item in created.json()['ingredients']] == ['cup', 'threads', None]
    units = (await authenticated.get('/api/recipes/units')).json()
    assert {'tsp', 'tbsp', 'cup', 'fl oz', 'oz', 'lb', 'g', 'kg', 'mL', 'L', 'whole', 'clove', 'slice', 'can'} <= set(units['options'])
    assert 'threads' in units['options']
    assert units['aliases']['teaspoons'] == 'tsp' and units['aliases']['ml'] == 'mL'


async def test_recipe_with_multiple_categories_matches_each_category_filter(authenticated, recipe_payload):
    soup = {**recipe_payload, 'title': 'Black Bean Soup', 'categories': ['Soup', 'Main Dish']}
    dessert = {**recipe_payload, 'title': 'Chocolate Cake', 'categories': ['Dessert']}
    soup_id = (await authenticated.post('/api/recipes', json=soup)).json()['id']
    await authenticated.post('/api/recipes', json=dessert)

    for category in ('Soup', 'Main Dish'):
        matches = (await authenticated.get('/api/recipes', params={'category': category})).json()
        assert [recipe['id'] for recipe in matches] == [soup_id]
    search_matches = (await authenticated.get('/api/recipes', params={'q': 'Main Dish'})).json()
    assert [recipe['id'] for recipe in search_matches] == [soup_id]


async def test_recipe_persists_alternative_measurements_and_package_details(authenticated, recipe_payload):
    payload = {**recipe_payload, 'title': 'Measured Bread', 'ingredients': [{
        'name': 'Flour', 'quantity': 226, 'unit': 'g', 'note': None, 'optional': False,
        'package_detail': None, 'alternative_measurements': [{'quantity': 2, 'unit': 'cups'}],
    }, {
        'name': 'Beans', 'quantity': 2, 'unit': 'cans', 'note': None, 'optional': False,
        'package_detail': '15 oz each', 'alternative_measurements': [],
    }]}
    created = await authenticated.post('/api/recipes', json=payload)
    assert created.status_code == 201
    ingredients = created.json()['ingredients']
    assert ingredients[0]['alternative_measurements'] == [{'quantity': 2.0, 'unit': 'cup'}]
    assert ingredients[1]['unit'] == 'can' and ingredients[1]['package_detail'] == '15 oz each'
    retrieved = await authenticated.get(f"/api/recipes/{created.json()['id']}")
    assert retrieved.json()['ingredients'] == ingredients


async def test_recipe_details_deduplicate_tags_and_persist_yield_and_time(authenticated, recipe_payload):
    payload = {**recipe_payload, 'title': 'Roti', 'tags': ['Quick', 'quick', ' Vegetarian '],
        'categories': ['Bread', 'bread', 'Main Dish'], 'base_servings': 12, 'yield_unit': 'rotis',
        'additional_time_minutes': 15, 'additional_time_label': 'Resting'}
    created = await authenticated.post('/api/recipes', json=payload)
    assert created.status_code == 201
    result = created.json()
    assert result['tags'] == ['Quick', 'Vegetarian']
    assert result['categories'] == ['Bread', 'Main Dish']
    assert (result['base_servings'], result['yield_unit']) == (12, 'rotis')
    assert (result['additional_time_minutes'], result['additional_time_label']) == (15, 'Resting')


async def test_recipe_proteins_are_multi_select_deduplicated_and_filterable(authenticated, recipe_payload):
    payload = {**recipe_payload, 'title': 'Chicken and Tofu Bowl', 'proteins': ['Chicken', 'tofu', 'TOFU']}
    created = await authenticated.post('/api/recipes', json=payload)
    assert created.status_code == 201
    assert created.json()['proteins'] == ['Chicken', 'tofu']
    matches = (await authenticated.get('/api/recipes', params={'protein': 'Chicken'})).json()
    assert [recipe['id'] for recipe in matches] == [created.json()['id']]
