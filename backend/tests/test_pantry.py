import pytest

pytestmark = pytest.mark.anyio

async def test_pantry_staples_are_shared_and_household_scoped(client):
    created = await client.post('/api/pantry-staples', json={'name': 'Olive oil'})
    assert created.status_code == 201
    assert [item['name'] for item in (await client.get('/api/pantry-staples')).json()] == ['Olive oil']
