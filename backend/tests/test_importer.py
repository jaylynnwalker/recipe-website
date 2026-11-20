import json

import pytest

from app.importer import ImportFailure, duration_minutes, parse_page, social_source_type, validate_external_url
from app.ingredient_parser import normalize_imported_ingredient, parse_imported_ingredient


def test_structured_recipe_extraction_preserves_available_fields():
    data = {
        '@context': 'https://schema.org', '@type': 'Recipe', 'name': 'Lemon Pasta',
        'description': 'A bright supper.', 'recipeYield': '6 servings', 'prepTime': 'PT10M', 'cookTime': 'PT20M',
        'recipeCuisine': 'Italian', 'recipeCategory': 'Dinner, Pasta', 'keywords': ['Quick', 'Vegetarian'],
        'recipeIngredient': ['12 oz pasta', '1 lemon'],
        'recipeInstructions': [{'@type': 'HowToStep', 'text': 'Boil the pasta.'}, {'@type': 'HowToStep', 'text': 'Add lemon.'}],
    }
    draft, complete = parse_page(f'<script type="application/ld+json">{json.dumps(data)}</script>', 'https://recipes.example/lemon-pasta')
    assert complete is True
    assert draft['title'] == 'Lemon Pasta'
    assert draft['base_servings'] == 6
    assert draft['prep_minutes'] == 10 and draft['cook_minutes'] == 20
    assert draft['ingredients'][0]['name'] == 'pasta'
    assert draft['ingredients'][0]['quantity'] == 12
    assert draft['ingredients'][0]['unit'] == 'oz'
    assert draft['steps'][1]['instruction'] == 'Add lemon.'
    assert draft['categories'] == ['Dinner', 'Pasta']
    assert draft['tags'] == ['Quick', 'Vegetarian']


def test_add_a_pinch_structured_recipe_regression_fixture():
    """Representative JSON-LD fields from the named Add a Pinch regression page."""
    data = {
        '@context': 'https://schema.org', '@type': 'Recipe',
        'name': 'Old Fashioned Vanilla Ice Cream Recipe',
        'recipeYield': ['8 servings', '1 quart'], 'prepTime': 'PT5M', 'cookTime': 'PT10M',
        'recipeCategory': ['Dessert'], 'recipeCuisine': ['American'], 'keywords': 'ice cream, vanilla',
        'recipeIngredient': ['4 egg yolks', '1/2 cup granulated sugar', '1 cup whole milk', '2 teaspoons vanilla extract, or vanilla bean paste'],
        'recipeInstructions': [
            {'@type': 'HowToStep', 'text': 'Whisk the egg yolks and sugar.'},
            {'@type': 'HowToStep', 'text': 'Stir in cream and vanilla, then process in an ice cream maker.'},
        ],
    }
    draft, complete = parse_page(f'<script type="application/ld+json">{json.dumps(data)}</script>', 'https://addapinch.com/old-fashioned-vanilla-ice-cream-recipe/')
    assert complete is True
    assert draft['title'] == 'Old Fashioned Vanilla Ice Cream Recipe'
    assert draft['base_servings'] == 8
    assert draft['prep_minutes'] == 5 and draft['cook_minutes'] == 10
    assert draft['ingredients'][1] == {'quantity': .5, 'unit': 'cup', 'name': 'granulated sugar', 'note': None, 'optional': False}
    assert [step['instruction'] for step in draft['steps']] == ['Whisk the egg yolks and sugar.', 'Stir in cream and vanilla, then process in an ice cream maker.']
    assert draft['categories'] == ['Dessert'] and draft['cuisine'] == 'American'
    assert draft['tags'] == ['ice cream', 'vanilla']


def test_youtube_metadata_becomes_manual_review_draft():
    data = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': 'Soup video', 'description': 'Ingredients are listed in the video description.'}
    draft, complete = parse_page(f'<script type="application/ld+json">{json.dumps(data)}</script>', 'https://www.youtube.com/watch?v=abc')
    assert complete is False
    assert draft['title'] == 'Soup video'
    assert draft['source']['type'] == 'youtube'
    assert draft['ingredients'] == []


@pytest.mark.parametrize(('url', 'source_type'), [
    ('https://www.instagram.com/reel/example/', 'instagram'),
    ('https://www.facebook.com/watch/?v=123', 'facebook'),
    ('https://youtu.be/example', 'youtube'),
])
def test_social_metadata_is_preserved_as_partial_review(url, source_type):
    html = '<meta property="og:title" content="Public recipe post"><meta property="og:description" content="Public caption only">'
    draft, complete = parse_page(html, url)
    assert complete is False
    assert draft['title'] == 'Public recipe post'
    assert draft['description'] == 'Public caption only'
    assert draft['source']['type'] == source_type


def test_instagram_without_title_uses_reviewable_placeholder():
    draft, complete = parse_page('<meta property="og:description" content="Caption available">', 'https://www.instagram.com/reel/example/')
    assert complete is False
    assert draft['title'] == 'Instagram recipe — title needed'
    assert social_source_type('www.instagram.com') == 'instagram'


def test_ssrf_validation_rejects_local_addresses_and_unusual_ports():
    for url in ['http://127.0.0.1/recipe', 'http://10.0.0.4/recipe', 'http://[::1]/recipe', 'https://example.com:8443/recipe']:
        with pytest.raises(ImportFailure): validate_external_url(url)
    assert validate_external_url('https://example.com/recipe') == 'https://example.com/recipe'
    assert duration_minutes('PT1H15M') == 75


@pytest.mark.parametrize(('text', 'quantity', 'unit', 'name'), [
    ('1 medium onion, chopped', 1, None, 'medium onion, chopped'),
    ('2 cloves garlic, minced', 2, 'clove', 'garlic, minced'),
    ('1 tsp ground cumin', 1, 'tsp', 'ground cumin'),
    ('1 1/2 cups vegetable broth', 1.5, 'cup', 'vegetable broth'),
    ('1/2 teaspoon salt', .5, 'tsp', 'salt'),
    ('1 (15-ounce) can black beans, drained', 1, 'can', 'black beans (15-ounce), drained'),
    ('Salt and pepper to taste', None, None, 'Salt and pepper to taste'),
])
def test_imported_ingredient_parsing_examples(text, quantity, unit, name):
    parsed = parse_imported_ingredient(text)
    assert parsed == {'quantity': quantity, 'unit': unit, 'name': name, 'note': None, 'optional': False}


@pytest.mark.parametrize(('text', 'quantity', 'unit', 'name'), [
    ('2½ Tbsp. olive oil', 2.5, 'tbsp', 'olive oil'),
    ('0.75 pounds carrots, diced', .75, 'lb', 'carrots, diced'),
    ('⅓ cup rinsed quinoa', 1 / 3, 'cup', 'rinsed quinoa'),
    ('1-2 jalapeños, sliced', None, None, '1-2 jalapeños, sliced'),
    ('1/0 cup impossible', None, None, '1/0 cup impossible'),
])
def test_imported_ingredient_parsing_edge_cases(text, quantity, unit, name):
    parsed = parse_imported_ingredient(text)
    assert parsed['quantity'] == quantity
    assert parsed['unit'] == unit
    assert parsed['name'] == name


def test_normalization_preserves_explicit_fields_and_notes():
    structured = {'name': 'flour', 'quantity': 2, 'unit': 'cups', 'note': 'existing note', 'optional': True}
    assert normalize_imported_ingredient(structured) == {**structured, 'unit': 'cup'}

    unstructured = {'name': '1 cup flour, sifted', 'quantity': None, 'unit': None, 'note': 'keep me', 'optional': True}
    normalized = normalize_imported_ingredient(unstructured)
    assert normalized == {'name': 'flour, sifted', 'quantity': 1, 'unit': 'cup', 'note': 'keep me', 'optional': True}

    explicit_alias = {'name': 'flour', 'quantity': 2, 'unit': 'cups', 'note': None, 'optional': False}
    assert normalize_imported_ingredient(explicit_alias)['unit'] == 'cup'
