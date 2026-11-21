from io import BytesIO

from PIL import Image
import pytest

from app.importer import ImportFailure
from app.config import get_settings
from app.models import ImportAsset, ImportJob
from app.routers import imports

pytestmark = pytest.mark.anyio


def png_bytes(color):
    output = BytesIO(); Image.new('RGB', (5, 5), color).save(output, format='PNG'); return output.getvalue()


def extracted_draft(recipe_payload, url='https://example.com/supper'):
    return {**recipe_payload, 'title': 'Imported Supper', 'source': {'type': 'web', 'label': 'example.com', 'url': url, 'page': None}}


async def test_url_import_review_save_and_duplicate_detection(authenticated, recipe_payload, monkeypatch, db_session):
    url = 'https://example.com/supper'
    existing = {**recipe_payload, 'title': 'Existing Supper', 'source': {'type': 'web', 'label': 'example.com', 'url': url, 'page': None}}
    existing_id = (await authenticated.post('/api/recipes', json=existing)).json()['id']

    async def fake_extract(_url): return extracted_draft(recipe_payload, url), True, url, None
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
    assert (await authenticated.get('/api/inbox')).json() == []
    stored = db_session.get(ImportJob, item['id'])
    db_session.refresh(stored)
    assert stored.status == 'Saved' and stored.saved_recipe_id == saved.json()['id']

    repeated = await authenticated.post(f"/api/inbox/{item['id']}/save", json={**draft, 'title': 'A Different Duplicate'})
    assert repeated.status_code == 409
    recipes = (await authenticated.get('/api/recipes')).json()
    assert [recipe['title'] for recipe in recipes].count('Reviewed Imported Supper') == 1
    assert not any(recipe['title'] == 'A Different Duplicate' for recipe in recipes)


async def test_extracted_cover_is_persisted_on_saved_recipe(authenticated, recipe_payload, monkeypatch, db_session):
    url = 'https://example.com/photo-recipe'
    async def fake_extract(_url): return extracted_draft(recipe_payload, url), True, url, None
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    item = (await authenticated.post('/api/inbox/url', json={'url': url})).json()
    storage_name = 'imports/extracted-cover.png'
    destination = get_settings().media_root / storage_name; destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(png_bytes('#8a9b6a'))
    db_session.add(ImportAsset(import_job_id=item['id'], storage_name=storage_name, original_name='cover.png', media_type='image/png', position=0, role='cover')); db_session.commit()
    refreshed = (await authenticated.get('/api/inbox')).json()[0]
    assert refreshed['assets'][0]['role'] == 'cover'
    saved = await authenticated.post(f"/api/inbox/{item['id']}/save", json=refreshed['draft'])
    assert saved.status_code == 201
    assert saved.json()['image'] == f'/media/{storage_name}'


async def test_failed_save_keeps_inbox_item_available(authenticated, recipe_payload, monkeypatch):
    url = 'https://example.com/incomplete'
    async def fake_extract(_url): return extracted_draft(recipe_payload, url), True, url, None
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    item = (await authenticated.post('/api/inbox/url', json={'url': url})).json()

    invalid = {**item['draft'], 'title': ''}
    response = await authenticated.post(f"/api/inbox/{item['id']}/save", json=invalid)
    assert response.status_code == 422
    active = (await authenticated.get('/api/inbox')).json()
    assert [entry['id'] for entry in active] == [item['id']]
    assert active[0]['status'] == 'Ready for Review'


async def test_failed_import_can_retry_and_recover(authenticated, recipe_payload, monkeypatch):
    calls = 0
    async def changing_extract(url):
        nonlocal calls
        calls += 1
        if calls == 1: raise ImportFailure('No structured recipe metadata was found.')
        return extracted_draft(recipe_payload, url), True, url, None
    monkeypatch.setattr(imports, 'extract_url', changing_extract)
    failed = (await authenticated.post('/api/inbox/url', json={'url': 'https://example.com/retry'})).json()
    assert failed['status'] == 'Failed'
    retried = await authenticated.post(f"/api/inbox/{failed['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()['status'] == 'Ready for Review'


async def test_partial_social_import_preserves_metadata_with_readable_review_message(authenticated, recipe_payload, monkeypatch):
    url = 'https://www.instagram.com/reel/example/'
    partial = extracted_draft(recipe_payload, url)
    partial['title'] = 'Public post title'
    partial['ingredients'] = []
    partial['steps'] = []
    partial['source']['type'] = 'instagram'
    async def fake_extract(_url): return partial, False, url, None
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    response = await authenticated.post('/api/inbox/url', json={'url': url})
    assert response.status_code == 201
    item = response.json()
    assert item['status'] == 'Ready for Review'
    assert item['title'] == 'Public post title'
    assert 'publicly accessible title and description' in item['error_message']


async def test_url_image_failure_does_not_fail_recipe_import(authenticated, recipe_payload, monkeypatch):
    url = 'https://example.com/recipe-with-broken-image'
    async def fake_extract(_url): return extracted_draft(recipe_payload, url), True, url, 'https://images.example.com/missing.jpg'
    image_attempts = []
    async def failed_image(job, image_url, db):
        image_attempts.append(image_url)
        return False
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    monkeypatch.setattr(imports, 'download_import_image', failed_image)

    item = (await authenticated.post('/api/inbox/url', json={'url': url})).json()
    assert item['status'] == 'Ready for Review'
    assert item['draft']['title'] == 'Imported Supper'
    assert item['assets'] == []
    assert image_attempts == ['https://images.example.com/missing.jpg']


async def test_facebook_ai_extraction_does_not_send_inaccessible_metadata_to_ai(authenticated, recipe_payload, monkeypatch):
    url = 'https://www.facebook.com/reel/example/'
    partial = extracted_draft(recipe_payload, url)
    partial.update(title='Public Facebook post', ingredients=[], steps=[])
    partial['source']['type'] = 'facebook'
    async def fake_extract(_url): return partial, False, url, None
    async def blocked_html(_url): raise ImportFailure('Facebook returned HTTP 403')
    ai_called = False
    async def fake_ai(*args, **kwargs):
        nonlocal ai_called
        ai_called = True
        return recipe_payload
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    monkeypatch.setattr(imports, 'fetch_public_html', blocked_html)
    monkeypatch.setattr(imports, 'run_structured', fake_ai)

    item = (await authenticated.post('/api/inbox/url', json={'url': url})).json()
    response = await authenticated.post(f"/api/inbox/{item['id']}/ai-extract")
    assert response.status_code == 422
    assert 'Paste recipe text or upload screenshots' in response.json()['detail']
    assert ai_called is False


async def test_instagram_ai_fallback_still_uses_accessible_caption(authenticated, recipe_payload, monkeypatch):
    url = 'https://www.instagram.com/reel/example/'
    partial = extracted_draft(recipe_payload, url)
    partial.update(title='Public Instagram recipe', ingredients=[], steps=[])
    partial['source']['type'] = 'instagram'
    async def fake_extract(_url): return partial, False, url, None
    async def public_html(_url):
        return '<html><body>Tomato soup recipe. Mix 2 cups tomatoes, then simmer and cook for 20 minutes.</body></html>', url
    async def no_image(*args): return False
    async def fake_ai(*args, **kwargs): return recipe_payload
    monkeypatch.setattr(imports, 'extract_url', fake_extract)
    monkeypatch.setattr(imports, 'fetch_public_html', public_html)
    monkeypatch.setattr(imports, 'download_import_image', no_image)
    monkeypatch.setattr(imports, 'run_structured', fake_ai)

    item = (await authenticated.post('/api/inbox/url', json={'url': url})).json()
    response = await authenticated.post(f"/api/inbox/{item['id']}/ai-extract")
    assert response.status_code == 200
    assert response.json()['status'] == 'Ready for Review'
    assert response.json()['draft']['ingredients']


async def test_inaccessible_social_import_reports_failure_without_losing_source(authenticated, monkeypatch):
    async def blocked(_url): raise ImportFailure('The recipe website returned HTTP 403')
    monkeypatch.setattr(imports, 'extract_url', blocked)
    url = 'https://www.facebook.com/watch/?v=123'
    response = await authenticated.post('/api/inbox/url', json={'url': url})
    assert response.status_code == 201
    item = response.json()
    assert item['status'] == 'Failed'
    assert item['source_url'] == url
    assert item['error_message'] == 'The recipe website returned HTTP 403'


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
