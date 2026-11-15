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
    assert any('4 lb Carrots' == item for item in preview['additions'])
    assert preview['excluded_staples'] == ['Salt']
    applied = (await authenticated.post('/api/grocery-list/apply')).json()
    carrots = next(item for item in applied['items'] if item['name'] == 'carrots')
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
