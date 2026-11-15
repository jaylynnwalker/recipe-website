from io import BytesIO

from PIL import Image
import pytest

pytestmark = pytest.mark.anyio


def png_bytes():
    output = BytesIO()
    Image.new('RGB', (4, 4), '#8a9b6a').save(output, format='PNG')
    return output.getvalue()


async def test_validated_recipe_image_upload(authenticated, recipe_payload):
    recipe_id = (await authenticated.post('/api/recipes', json=recipe_payload)).json()['id']
    response = await authenticated.post(f'/api/recipes/{recipe_id}/photos', files={'file': ('dinner.png', png_bytes(), 'image/png')}, data={'alt_text': 'Dinner on a plate'})
    assert response.status_code == 201
    stored = (await authenticated.get(f'/api/recipes/{recipe_id}')).json()
    assert stored['image'].startswith('/media/')
    assert stored['image_alt'] == 'Dinner on a plate'


async def test_invalid_image_is_rejected(authenticated, recipe_payload):
    recipe_id = (await authenticated.post('/api/recipes', json=recipe_payload)).json()['id']
    response = await authenticated.post(f'/api/recipes/{recipe_id}/photos', files={'file': ('fake.png', b'not an image', 'image/png')})
    assert response.status_code == 422
