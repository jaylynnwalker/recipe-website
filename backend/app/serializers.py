from .models import Recipe


def recipe_to_dict(recipe: Recipe) -> dict:
    photos = sorted(recipe.photos, key=lambda photo: photo.position)
    cover = next((photo for photo in photos if photo.is_cover), photos[0] if photos else None)
    ingredient_sections = sorted((section for section in recipe.sections if section.kind == 'ingredient'), key=lambda section: section.position)
    instruction_sections = sorted((section for section in recipe.sections if section.kind == 'instruction'), key=lambda section: section.position)
    ingredient_section_indexes = {section.id: index for index, section in enumerate(ingredient_sections)}
    instruction_section_indexes = {section.id: index for index, section in enumerate(instruction_sections)}
    return {
        'id': recipe.id,
        'title': recipe.title,
        'description': recipe.description,
        'status': recipe.status,
        'cuisine': recipe.cuisine,
        'proteins': [protein.name for protein in recipe.proteins],
        'tags': [tag.name for tag in recipe.tags],
        'categories': [category.name for category in recipe.categories],
        'prep_minutes': recipe.prep_minutes,
        'cook_minutes': recipe.cook_minutes,
        'additional_time_minutes': recipe.additional_time_minutes,
        'additional_time_label': recipe.additional_time_label,
        'base_servings': recipe.base_servings,
        'yield_unit': recipe.yield_unit,
        'ingredient_sections': [{'heading': section.heading} for section in ingredient_sections],
        'instruction_sections': [{'heading': section.heading} for section in instruction_sections],
        'ingredients': [{'id': item.id, 'name': item.ingredient.display_name, 'quantity': float(item.quantity) if item.quantity is not None else None, 'unit': item.unit, 'note': item.note, 'optional': item.optional, 'package_detail': item.package_detail, 'section_index': ingredient_section_indexes.get(item.section_id), 'alternative_measurements': [{'quantity': float(measurement.quantity), 'unit': measurement.unit} for measurement in item.alternative_measurements]} for item in recipe.ingredients],
        'steps': [{'id': step.id, 'instruction': step.instruction, 'tip': step.tip, 'section_index': instruction_section_indexes.get(step.section_id)} for step in recipe.steps],
        'notes': recipe.notes,
        'source': {'type': recipe.source_type, 'label': recipe.source_label, 'url': recipe.source_url, 'page': recipe.source_page},
        'image': f'/media/{cover.storage_name}' if cover else None,
        'image_alt': cover.alt_text if cover else 'Neutral illustrated recipe placeholder',
        'photos': [{'id': photo.id, 'url': f'/media/{photo.storage_name}', 'alt_text': photo.alt_text, 'media_type': photo.media_type} for photo in photos],
        'created_at': recipe.created_at,
        'updated_at': recipe.updated_at,
        'cooking_history': [event.cooked_at for event in sorted(recipe.cooking_events, key=lambda event: event.cooked_at, reverse=True)],
    }
