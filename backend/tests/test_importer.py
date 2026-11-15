import json

import pytest

from app.importer import ImportFailure, duration_minutes, parse_page, validate_external_url


def test_structured_recipe_extraction_preserves_available_fields():
    data = {
        '@context': 'https://schema.org', '@type': 'Recipe', 'name': 'Lemon Pasta',
        'description': 'A bright supper.', 'recipeYield': '6 servings', 'prepTime': 'PT10M', 'cookTime': 'PT20M',
        'recipeCuisine': 'Italian', 'recipeIngredient': ['12 oz pasta', '1 lemon'],
        'recipeInstructions': [{'@type': 'HowToStep', 'text': 'Boil the pasta.'}, {'@type': 'HowToStep', 'text': 'Add lemon.'}],
    }
    draft, complete = parse_page(f'<script type="application/ld+json">{json.dumps(data)}</script>', 'https://recipes.example/lemon-pasta')
    assert complete is True
    assert draft['title'] == 'Lemon Pasta'
    assert draft['base_servings'] == 6
    assert draft['prep_minutes'] == 10 and draft['cook_minutes'] == 20
    assert draft['ingredients'][0]['name'] == '12 oz pasta'
    assert draft['ingredients'][0]['quantity'] is None
    assert draft['steps'][1]['instruction'] == 'Add lemon.'


def test_youtube_metadata_becomes_manual_review_draft():
    data = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': 'Soup video', 'description': 'Ingredients are listed in the video description.'}
    draft, complete = parse_page(f'<script type="application/ld+json">{json.dumps(data)}</script>', 'https://www.youtube.com/watch?v=abc')
    assert complete is False
    assert draft['title'] == 'Soup video'
    assert draft['source']['type'] == 'youtube'
    assert draft['ingredients'] == []


def test_ssrf_validation_rejects_local_addresses_and_unusual_ports():
    for url in ['http://127.0.0.1/recipe', 'http://10.0.0.4/recipe', 'http://[::1]/recipe', 'https://example.com:8443/recipe']:
        with pytest.raises(ImportFailure): validate_external_url(url)
    assert validate_external_url('https://example.com/recipe') == 'https://example.com/recipe'
    assert duration_minutes('PT1H15M') == 75
