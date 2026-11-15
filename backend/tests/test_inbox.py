from io import BytesIO

from PIL import Image
import pytest

from app.importer import ImportFailure
from app.routers import imports

pytestmark = pytest.mark.anyio


def png_bytes(color):
    output = BytesIO(); Image.new('RGB', (5, 5), color).save(output, format='PNG'); return output.getvalue()


def extracted_draft(recipe_payload, url='https://example.com/supper'):
    return {**recipe_payload, 'title': 'Imported Supper', 'source': {'type': 'web', 'label': 'example.com', 'url': url, 'page': None}}


async def test_url_import_review_save_and_duplicate_detection(authenticated, recipe_payload, monkeypatch):
    url = 'https://example.com/supper'
    existing = {**recipe_payload, 'title': 'Existing Supper', 'source': {'type': 'web', 'label': 'example.com', 'url': url, 'page': None}}
    existing_id = (await authenticated.post('/api/recipes', json=existing)).json()['id']

    async def fake_extract(_url): return extracted_draft(recipe_payload, url), True, url
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    response = await authenticated.post('/api/inbox/url', json={'url': url})
    assert response.status_code == 201
    item = response.json()
    assert item['status'] == 'Ready for Review'
    assert item['duplicate_recipe_id'] == existing_id
    assert (await authenticated.get('/api/inbox')).json()[0]['id'] == item['id']

    draft = {**item['draft'], 'title': 'Reviewed Imported Supper'}
    saved = await authenticated.post(f"/api/inbox/{item['id']}/save", json=draft)
    assert saved.status_code == 201
    assert saved.json()['source']['url'] == url
    stored = (await authenticated.get('/api/inbox')).json()[0]
    assert stored['status'] == 'Saved' and stored['saved_recipe_id'] == saved.json()['id']


async def test_failed_import_can_retry_and_recover(authenticated, recipe_payload, monkeypatch):
    calls = 0
    async def changing_extract(url):
        nonlocal calls
        calls += 1
        if calls == 1: raise ImportFailure('No structured recipe metadata was found.')
        return extracted_draft(recipe_payload, url), True, url
    monkeypatch.setattr(imports, 'extract_url', changing_extract)
    failed = (await authenticated.post('/api/inbox/url', json={'url': 'https://example.com/retry'})).json()
    assert failed['status'] == 'Failed'
    retried = await authenticated.post(f"/api/inbox/{failed['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()['status'] == 'Ready for Review'


async def test_multiple_original_photos_are_preserved_and_deleted(authenticated):
    response = await authenticated.post('/api/inbox/photos', files=[
        ('files', ('page-1.png', png_bytes('#8a9b6a'), 'image/png')),
        ('files', ('page-2.png', png_bytes('#d9c3a5'), 'image/png')),
    ])
    assert response.status_code == 201
    item = response.json()
    assert item['status'] == 'Ready for Review'
    assert len(item['assets']) == 2
    assert 'AI extraction' in item['error_message']
    assert (await authenticated.delete(f"/api/inbox/{item['id']}")).status_code == 204
    assert (await authenticated.get('/api/inbox')).json() == []


async def test_inbox_rejects_invalid_urls_and_uploads(authenticated):
    assert (await authenticated.post('/api/inbox/url', json={'url': 'http://127.0.0.1/private'})).status_code == 422
    invalid = await authenticated.post('/api/inbox/photos', files={'files': ('recipe.png', b'not-an-image', 'image/png')})
    assert invalid.status_code == 422
