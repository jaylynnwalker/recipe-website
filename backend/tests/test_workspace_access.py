import pytest

from app.config import get_settings

pytestmark = pytest.mark.anyio


async def test_explicit_local_mode_opens_shared_workspace(client):
    response = await client.get('/api/recipes')
    assert response.status_code == 200


async def test_cloudflare_mode_fails_closed_without_verified_token(client):
    settings = get_settings()
    settings.auth_mode = 'cloudflare'
    settings.cloudflare_access_team_domain = None
    settings.cloudflare_access_audience = None
    response = await client.get('/api/recipes')
    assert response.status_code == 401
    assert response.json()['detail'] == 'Verified Cloudflare Access identity required'


async def test_cloudflare_mode_rejects_invalid_signed_identity(client):
    settings = get_settings()
    settings.auth_mode = 'cloudflare'
    settings.cloudflare_access_team_domain = 'our-kitchen.cloudflareaccess.com'
    settings.cloudflare_access_audience = 'expected-audience'
    response = await client.get('/api/recipes', headers={'Cf-Access-Jwt-Assertion': 'not-a-jwt'})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid Cloudflare Access identity'
