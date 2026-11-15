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
