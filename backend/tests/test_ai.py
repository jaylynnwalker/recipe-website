from io import BytesIO
import json

from PIL import Image
import pytest

from pydantic import SecretStr

from app.ai import AIInvalidResponse, AIUnavailable, BUDGET_MICROUSD, RECIPE_SCHEMA, output_text, recipe_draft
from app.config import get_settings
from app.models import AIMonthlyBudget
from app import ai as ai_service

pytestmark = pytest.mark.anyio


def test_ai_recipe_schema_requests_multi_select_protein_sources():
    assert RECIPE_SCHEMA['properties']['proteins']['type'] == 'array'
    assert 'proteins' in RECIPE_SCHEMA['required']


def test_ai_recipe_schema_allows_unknown_servings():
    assert {'type': 'null'} in RECIPE_SCHEMA['properties']['base_servings']['anyOf']


def test_ai_recipe_schema_supports_independent_sections():
    assert 'ingredient_sections' in RECIPE_SCHEMA['required']
    assert 'instruction_sections' in RECIPE_SCHEMA['required']
    assert 'section_index' in RECIPE_SCHEMA['properties']['ingredients']['items']['required']
    assert 'section_index' in RECIPE_SCHEMA['properties']['steps']['items']['required']
    assert 'Zero-based index into ingredient_sections' in RECIPE_SCHEMA['properties']['ingredients']['items']['properties']['section_index']['description']


def test_incomplete_ai_response_reports_output_limit_clearly():
    with pytest.raises(AIInvalidResponse, match='ran out of output space'):
        output_text({'status': 'incomplete', 'incomplete_details': {'reason': 'max_output_tokens'}, 'output': []})


def recipe_result(title='Pantry Pasta'):
    return {
        'title': title, 'description': 'A reviewable idea.', 'cuisine': 'Italian', 'protein': 'Vegetarian',
        'tags': ['Quick'], 'categories': ['Dinner'], 'prep_minutes': 10, 'cook_minutes': 20, 'base_servings': 4,
        'ingredients': [{'name': 'Pasta', 'quantity': 8, 'unit': 'oz', 'note': None, 'optional': False}],
        'steps': [{'instruction': 'Cook the pasta.', 'tip': None}], 'notes': '',
    }


class FakeResponses:
    def __init__(self, result=None, raw_text=None, error=None, usage=None):
        self.result = result; self.raw_text = raw_text; self.error = error; self.usage = usage or {'input_tokens': 100, 'output_tokens': 50}

    async def create(self, payload):
        if self.error: raise self.error
        text = self.raw_text if self.raw_text is not None else json.dumps(self.result)
        return {'output': [{'content': [{'type': 'output_text', 'text': text}]}], 'usage': self.usage}


@pytest.fixture(autouse=True)
def configured_openai():
    settings = get_settings(); old_key = settings.openai_api_key; old_model = settings.openai_model
    settings.openai_api_key = SecretStr('test-key'); settings.openai_model = 'gpt-6-luna'
    yield
    settings.openai_api_key = old_key; settings.openai_model = old_model


async def test_structured_recipe_ideas_and_reported_usage(authenticated, recipe_payload, monkeypatch):
    await authenticated.post('/api/recipes', json=recipe_payload)
    monkeypatch.setattr(ai_service, 'get_responses_client', lambda _settings: FakeResponses({'ideas': [recipe_result()]}))
    response = await authenticated.post('/api/ai/what-can-i-make', json={'ingredients': ['carrots'], 'include_pantry_staples': False, 'generate_ai': True})
    assert response.status_code == 200
    assert response.json()['saved_matches'][0]['recipe']['title'] == 'Test Supper'
    assert response.json()['generated_ideas'][0]['status'] == 'Want to Try'
    usage = (await authenticated.get('/api/ai/usage')).json()
    assert usage['spent_usd'] > 0 and usage['reserved_usd'] == 0


async def test_help_me_pick_prefers_saved_recipes_and_keeps_ai_ideas_unsaved(authenticated, recipe_payload, monkeypatch):
    saved = await authenticated.post('/api/recipes', json=recipe_payload)
    archived = {**recipe_payload, 'title': 'Old Archived Dish', 'status': 'Archived'}
    await authenticated.post('/api/recipes', json=archived)
    library = await authenticated.post('/api/ai/help-me-pick', json={'mode': 'Mix', 'generate_ai': False})
    assert [item['title'] for item in library.json()['saved_recipes']] == ['Test Supper']

    monkeypatch.setattr(ai_service, 'get_responses_client', lambda _settings: FakeResponses({'ideas': [recipe_result('New Idea')]}))
    generated = await authenticated.post('/api/ai/help-me-pick', json={'mode': 'Our Rotation', 'generate_ai': True})
    assert generated.status_code == 200
    assert generated.json()['saved_recipes'][0]['id'] == saved.json()['id']
    assert generated.json()['generated_ideas'][0]['title'] == 'New Idea'
    assert len((await authenticated.get('/api/recipes')).json()) == 2


async def test_invalid_response_and_provider_failure_charge_reservation(authenticated, recipe_payload, monkeypatch):
    monkeypatch.setattr(ai_service, 'get_responses_client', lambda _settings: FakeResponses(raw_text='not-json'))
    invalid = await authenticated.post('/api/ai/what-can-i-make', json={'ingredients': ['rice'], 'generate_ai': True})
    assert invalid.status_code == 502
    assert (await authenticated.get('/api/ai/usage')).json()['spent_usd'] == .000035

    recipe_id = (await authenticated.post('/api/recipes', json=recipe_payload)).json()['id']
    monkeypatch.setattr(ai_service, 'get_responses_client', lambda _settings: FakeResponses(error=AIUnavailable('provider unavailable')))
    failed = await authenticated.post('/api/ai/assist', json={'recipe_id': recipe_id, 'question': 'Can I substitute it?'})
    assert failed.status_code == 503
    assert (await authenticated.get('/api/ai/usage')).json()['spent_usd'] == .075035


async def test_monthly_budget_blocks_new_requests(authenticated, db_session, monkeypatch):
    from app.ai import current_month
    from app.models import Household
    household = db_session.query(Household).first()
    db_session.add(AIMonthlyBudget(household_id=household.id, month=current_month(), spent_microusd=BUDGET_MICROUSD, reserved_microusd=0)); db_session.commit()
    monkeypatch.setattr(ai_service, 'get_responses_client', lambda _settings: FakeResponses({'ideas': [recipe_result()]}))
    response = await authenticated.post('/api/ai/what-can-i-make', json={'ingredients': ['rice'], 'generate_ai': True})
    assert response.status_code == 429
    assert (await authenticated.get('/api/ai/usage')).json()['blocked'] is True


async def test_multi_image_extraction_requires_review_and_preserves_sources(authenticated, monkeypatch):
    output = BytesIO(); Image.new('RGB', (5, 5), '#8a9b6a').save(output, format='PNG')
    created = await authenticated.post('/api/inbox/photos', files=[('files', ('one.png', output.getvalue(), 'image/png')), ('files', ('two.png', output.getvalue(), 'image/png'))])
    item = created.json()
    extracted_recipe = recipe_result('Grandma’s Soup')
    extracted_recipe['ingredients'] = [{'name': '1 1/2 cups carrots, diced', 'quantity': None, 'unit': None, 'note': None, 'optional': False}]
    extracted_recipe['steps'] = [{'instruction': 'simmer with an Instant Pot for 10 minutes.', 'tip': 'keep this lower-case'}]
    fake = FakeResponses(extracted_recipe)
    monkeypatch.setattr(ai_service, 'get_responses_client', lambda _settings: fake)
    response = await authenticated.post(f"/api/inbox/{item['id']}/ai-extract")
    assert response.status_code == 200
    extracted = response.json()
    assert extracted['status'] == 'Ready for Review'
    assert extracted['draft']['title'] == 'Grandma’s Soup'
    assert {key: extracted['draft']['ingredients'][0][key] for key in ('name', 'quantity', 'unit', 'note', 'optional')} == {'name': 'Carrots, diced', 'quantity': 1.5, 'unit': 'cup', 'note': None, 'optional': False}
    assert extracted['draft']['steps'][0] == {'instruction': 'Simmer with an Instant Pot for 10 minutes.', 'tip': 'keep this lower-case', 'section_index': None}
    assert len(extracted['assets']) == 2


async def test_empty_instagram_title_becomes_readable_review_placeholder():
    parsed = recipe_result('')
    draft = recipe_draft(parsed, {'type': 'instagram', 'label': 'instagram.com', 'url': 'https://www.instagram.com/reel/example/', 'page': None})
    assert draft['title'] == 'Instagram recipe — title needed'


async def test_zero_servings_from_extraction_becomes_unspecified_without_losing_content():
    parsed = recipe_result('Yield unknown')
    parsed['base_servings'] = 0
    parsed['ingredients'] = [{'name': 'rice', 'quantity': 1, 'unit': 'cup', 'note': None, 'optional': False}]
    parsed['steps'] = [{'instruction': 'cook the rice.', 'tip': None}]
    draft = recipe_draft(parsed, {'type': 'instagram', 'label': 'Instagram', 'url': 'https://www.instagram.com/reel/CyjqvC3uLPm/?hl=en', 'page': None})
    assert draft['base_servings'] is None
    assert draft['ingredients'][0]['name'] == 'Rice'
    assert draft['steps'][0]['instruction'] == 'Cook the rice.'
