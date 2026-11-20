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
        'categories': ['Weeknight Dinner'], 'cuisines': ['Italian'], 'tags': ['Quick-Fix'],
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
