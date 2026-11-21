import pytest

pytestmark = pytest.mark.anyio


async def create_recipe(client, payload, title='Deck Supper'):
    body = {**payload, 'title': title, 'ingredients': [
        {'name': 'Carrots', 'quantity': 2, 'unit': 'lb', 'note': None, 'optional': False},
        {'name': 'Salt', 'quantity': 1, 'unit': 'tsp', 'note': None, 'optional': False},
    ]}
    response = await client.post('/api/recipes', json=body)
    assert response.status_code == 201
    return response.json()


async def test_deck_persistence_completion_and_cooking_history(authenticated, recipe_payload):
    recipe = await create_recipe(authenticated, recipe_payload)
    added = await authenticated.post('/api/deck', json={'recipe_id': recipe['id'], 'servings': 6})
    assert added.status_code == 201
    entry = added.json()
    assert entry['servings'] == 6
    assert (await authenticated.get('/api/deck')).json()[0]['recipe']['id'] == recipe['id']

    cooked = await authenticated.patch(f"/api/deck/{entry['id']}", json={'cooked': True})
    assert cooked.status_code == 200
    assert cooked.json()['cooked'] is True
    assert len((await authenticated.get(f"/api/recipes/{recipe['id']}")).json()['cooking_history']) == 1
    assert (await authenticated.delete('/api/deck/completed')).status_code == 204
    assert (await authenticated.get('/api/deck')).json() == []


async def test_grocery_snapshot_preserves_manual_and_checked_items(authenticated, recipe_payload):
    recipe = await create_recipe(authenticated, recipe_payload, 'Grocery Supper')
    await authenticated.post('/api/pantry-staples', json={'name': 'Salt'})
    deck = (await authenticated.post('/api/deck', json={'recipe_id': recipe['id'], 'servings': 8})).json()

    preview = (await authenticated.post('/api/grocery-list/preview')).json()
    assert any('Carrots — 4 lb' == item for item in preview['additions'])
    assert preview['excluded_staples'] == ['Salt']
    applied = (await authenticated.post('/api/grocery-list/apply')).json()
    carrots = next(item for item in applied['items'] if item['name'] == 'carrot')
    assert carrots['quantity'] == 4
    assert applied['excluded_staples'][0]['name'] == 'Salt'

    manual = (await authenticated.post('/api/grocery-list/items', json={'label': 'Coffee', 'category': 'Pantry'})).json()
    await authenticated.patch(f"/api/grocery-list/items/{carrots['id']}", json={'checked': True})
    await authenticated.delete(f"/api/deck/{deck['id']}")
    refreshed = (await authenticated.post('/api/grocery-list/apply')).json()
    assert any(item['id'] == manual['id'] for item in refreshed['items'])
    assert any(item['id'] == carrots['id'] and item['checked'] for item in refreshed['items'])


async def test_excluded_staple_can_be_added_back(authenticated, recipe_payload):
    recipe = await create_recipe(authenticated, recipe_payload, 'Staple Supper')
    await authenticated.post('/api/pantry-staples', json={'name': 'Salt'})
    await authenticated.post('/api/deck', json={'recipe_id': recipe['id']})
    grocery = (await authenticated.post('/api/grocery-list/apply')).json()
    excluded = grocery['excluded_staples'][0]
    added = await authenticated.post(f"/api/grocery-list/excluded/{excluded['id']}/add-back")
    assert added.status_code == 200
    stored = (await authenticated.get('/api/grocery-list')).json()
    assert any(item['label'] == 'Salt' and item['manual'] for item in stored['items'])
    assert stored['excluded_staples'] == []


async def test_multiple_deck_recipes_consolidate_and_refresh_after_lineup_changes(authenticated, recipe_payload):
    first = {**recipe_payload, 'title': 'Carrot Stew', 'ingredients': [
        {'name': 'Carrots', 'quantity': 1, 'unit': 'lb', 'note': None, 'optional': False},
        {'name': 'Fresh herbs', 'quantity': None, 'unit': None, 'note': None, 'optional': False},
    ]}
    second = {**recipe_payload, 'title': 'Roasted Carrots', 'base_servings': 2, 'ingredients': [
        {'name': 'Carrots', 'quantity': 8, 'unit': 'oz', 'note': None, 'optional': False},
    ]}
    first_recipe = (await authenticated.post('/api/recipes', json=first)).json()
    second_recipe = (await authenticated.post('/api/recipes', json=second)).json()
    first_deck = (await authenticated.post('/api/deck', json={'recipe_id': first_recipe['id'], 'servings': 4})).json()
    await authenticated.post('/api/deck', json={'recipe_id': second_recipe['id'], 'servings': 4})
    manual = (await authenticated.post('/api/grocery-list/items', json={'label': 'Coffee', 'category': 'Pantry'})).json()

    applied = (await authenticated.post('/api/grocery-list/apply')).json()
    carrots = next(item for item in applied['items'] if item['name'] == 'carrot')
    herbs = next(item for item in applied['items'] if item['name'] == 'fresh herb')
    assert carrots['quantity'] == 2 and carrots['unit'] == 'lb'
    assert {source['title'] for source in carrots['sources']} == {'Carrot Stew', 'Roasted Carrots'}
    assert herbs['quantity'] is None and herbs['unit'] is None
    assert any(item['id'] == manual['id'] for item in applied['items'])

    await authenticated.delete(f"/api/deck/{first_deck['id']}")
    preview = (await authenticated.post('/api/grocery-list/preview')).json()
    assert preview['updates'] == ['Carrots — 1 lb']
    assert preview['removals'] == ['Fresh herbs']
    refreshed = (await authenticated.post('/api/grocery-list/apply')).json()
    remaining_carrots = next(item for item in refreshed['items'] if item['name'] == 'carrot')
    assert remaining_carrots['quantity'] == 1 and remaining_carrots['unit'] == 'lb'
    assert not any(item['name'] == 'fresh herb' for item in refreshed['items'])
    assert any(item['id'] == manual['id'] for item in refreshed['items'])


async def test_incompatible_measurements_share_one_item_without_density_guess(authenticated, recipe_payload):
    first = {**recipe_payload, 'title': 'Measured Milk by Volume', 'ingredients': [
        {'name': 'Milk', 'quantity': 1, 'unit': 'cup', 'note': None, 'optional': False},
    ]}
    second = {**recipe_payload, 'title': 'Measured Milk by Weight', 'ingredients': [
        {'name': 'milk', 'quantity': 8, 'unit': 'oz', 'note': None, 'optional': False},
    ]}
    first_recipe = (await authenticated.post('/api/recipes', json=first)).json()
    second_recipe = (await authenticated.post('/api/recipes', json=second)).json()
    await authenticated.post('/api/deck', json={'recipe_id': first_recipe['id']})
    await authenticated.post('/api/deck', json={'recipe_id': second_recipe['id']})
    grocery = (await authenticated.post('/api/grocery-list/apply')).json()
    milk = [item for item in grocery['items'] if item['name'] == 'milk']
    assert len(milk) == 1
    assert {(component['quantity'], component['unit']) for component in milk[0]['components']} == {(8.0, 'fl oz'), (8.0, 'oz')}
    assert milk[0]['quantity'] is None and milk[0]['unit'] is None
    assert {source['title'] for source in milk[0]['sources']} == {'Measured Milk by Volume', 'Measured Milk by Weight'}


async def test_packaged_grocery_item_preserves_count_and_size(authenticated, recipe_payload):
    payload = {**recipe_payload, 'title': 'Pantry Casserole', 'ingredients': [
        {'name': 'Cream of chicken', 'quantity': 2, 'unit': 'can', 'package_detail': '10.5 oz each', 'note': None, 'optional': False},
    ]}
    recipe = (await authenticated.post('/api/recipes', json=payload)).json()
    await authenticated.post('/api/deck', json={'recipe_id': recipe['id']})
    preview = (await authenticated.post('/api/grocery-list/preview')).json()
    assert preview['additions'] == ['Cream of chicken — 2 × 10.5 oz cans']
    grocery = (await authenticated.post('/api/grocery-list/apply')).json()
    item = grocery['items'][0]
    assert item['display_label'] == 'Cream of chicken — 2 × 10.5 oz cans'
    assert item['components'] == [{'quantity': 2.0, 'unit': 'can', 'package_detail': '10.5 oz each'}]


async def test_grocery_generation_includes_every_ingredient_section_once(authenticated, recipe_payload):
    payload = {**recipe_payload, 'title': 'Sectioned Dinner', 'ingredient_sections': [{'heading': 'Marinade'}, {'heading': 'Main'}], 'ingredients': [
        {'name': 'Olive oil', 'quantity': 2, 'unit': 'tbsp', 'note': None, 'optional': False, 'section_index': 0, 'alternative_measurements': [{'quantity': 30, 'unit': 'mL'}]},
        {'name': 'Chicken', 'quantity': 1, 'unit': 'lb', 'note': None, 'optional': False, 'section_index': 1},
    ]}
    recipe = (await authenticated.post('/api/recipes', json=payload)).json()
    await authenticated.post('/api/deck', json={'recipe_id': recipe['id'], 'servings': 8})
    grocery = (await authenticated.post('/api/grocery-list/apply')).json()
    oil = next(item for item in grocery['items'] if item['name'] == 'olive oil')
    chicken = next(item for item in grocery['items'] if item['name'] == 'chicken')
    assert (oil['quantity'], oil['unit']) == (2, 'fl oz')
    assert (chicken['quantity'], chicken['unit']) == (2, 'lb')
    assert len([item for item in grocery['items'] if item['name'] == 'olive oil']) == 1
