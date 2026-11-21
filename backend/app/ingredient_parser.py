from __future__ import annotations

import re
from typing import Any

from .units import UNIT_ALIASES, normalize_unit


UNICODE_FRACTIONS = {
    '¼': '1/4', '½': '1/2', '¾': '3/4', '⅐': '1/7', '⅑': '1/9',
    '⅒': '1/10', '⅓': '1/3', '⅔': '2/3', '⅕': '1/5', '⅖': '2/5',
    '⅗': '3/5', '⅘': '4/5', '⅙': '1/6', '⅚': '5/6', '⅛': '1/8',
    '⅜': '3/8', '⅝': '5/8', '⅞': '7/8',
}

IMPORT_UNITS = set(UNIT_ALIASES) | {value.casefold() for value in UNIT_ALIASES.values()}

QUANTITY_RE = re.compile(
    r'^(?P<quantity>(?:\d+(?:\.\d+)?|\.\d+)(?:\s+\d+/\d+)?|\d+/\d+)(?=\s|$)\s*'
)


def capitalize_first_letter(value: str) -> str:
    """Uppercase only the first alphabetic character and preserve everything else."""
    for index, character in enumerate(value):
        if character.isalpha():
            return f'{value[:index]}{character.upper()}{value[index + 1:]}'
    return value


def _expand_unicode_fractions(value: str) -> str:
    expanded: list[str] = []
    for character in value:
        fraction = UNICODE_FRACTIONS.get(character)
        if fraction is None:
            expanded.append(character)
            continue
        if expanded and expanded[-1] and expanded[-1][-1].isdigit():
            expanded.append(' ')
        expanded.append(fraction)
    return ''.join(expanded)


def _quantity(value: str) -> float | None:
    try:
        if ' ' in value:
            whole, fraction = value.split(None, 1)
            numerator, denominator = fraction.split('/', 1)
            if int(denominator) == 0:
                return None
            return float(whole) + int(numerator) / int(denominator)
        if '/' in value:
            numerator, denominator = value.split('/', 1)
            if int(denominator) == 0:
                return None
            return int(numerator) / int(denominator)
        return float(value)
    except (ValueError, ZeroDivisionError):
        return None


def _take_unit(value: str) -> tuple[str | None, str]:
    for candidate in sorted(IMPORT_UNITS, key=len, reverse=True):
        pattern = re.compile(rf'^{re.escape(candidate).replace(r"\ ", r"\s+")}(?:\.)?(?=$|\s|,)', re.IGNORECASE)
        match = pattern.match(value)
        if match:
            unit = normalize_unit(match.group(0).rstrip('.'))
            return unit, value[match.end():].lstrip()
    return None, value


def _append_package_detail(name: str, detail: str) -> str:
    main, separator, preparation = name.partition(',')
    combined = f'{main.rstrip()} ({detail.strip()})'
    return f'{combined},{preparation}' if separator else combined


WEIGHT_UNITS = {'mg', 'g', 'kg', 'oz', 'lb'}
VOLUME_UNITS = {'tsp', 'tbsp', 'cup', 'fl oz', 'mL', 'L', 'pt', 'qt', 'gal'}


def _measurement_priority(unit: str | None) -> int:
    if unit in WEIGHT_UNITS:
        return 0
    if unit in VOLUME_UNITS:
        return 1
    return 2


def _parenthetical_measurement(value: str) -> tuple[float, str | None, bool] | None:
    expanded = _expand_unicode_fractions(value.strip()).replace('-ounce', ' ounce').replace('-ounces', ' ounces')
    expanded = re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', expanded)
    match = QUANTITY_RE.match(expanded)
    if not match:
        return None
    quantity = _quantity(match.group('quantity'))
    unit, remainder = _take_unit(expanded[match.end():].strip())
    each = remainder.strip().casefold() == 'each'
    if quantity is None or unit is None or (remainder.strip() and not each):
        return None
    return quantity, unit, each


def parse_imported_ingredient(text: str) -> dict[str, Any]:
    """Split an imported ingredient string without guessing beyond its prefix."""
    original = text.strip()
    expanded = _expand_unicode_fractions(original)
    match = QUANTITY_RE.match(expanded)
    if not match:
        return {'name': capitalize_first_letter(original), 'quantity': None, 'unit': None, 'note': None, 'optional': False}

    amount = _quantity(match.group('quantity'))
    if amount is None:
        return {'name': capitalize_first_letter(original), 'quantity': None, 'unit': None, 'note': None, 'optional': False}

    remainder = expanded[match.end():].strip()
    package_detail = None
    package_match = re.match(r'^\(([^)]+)\)\s*', remainder)
    unit_source = remainder
    if package_match and _parenthetical_measurement(package_match.group(1)):
        package_measurement = _parenthetical_measurement(package_match.group(1))
        package_detail = f'{package_measurement[0]:g} {package_measurement[1]}{" each" if package_measurement[2] else ""}'
        unit_source = remainder[package_match.end():].strip()

    unit, name = _take_unit(unit_source)
    if package_detail and not unit:
        name = remainder

    alternatives = []
    trailing = re.match(r'^\(([^)]+)\)\s*', name)
    if trailing:
        secondary = _parenthetical_measurement(trailing.group(1))
        if secondary:
            name = name[trailing.end():].strip()
            if secondary[2] and unit not in WEIGHT_UNITS | VOLUME_UNITS:
                package_detail = f'{secondary[0]:g} {secondary[1]} each'
            else:
                measurements = [{'quantity': amount, 'unit': unit}, {'quantity': secondary[0], 'unit': secondary[1]}]
                measurements.sort(key=lambda item: _measurement_priority(item['unit']))
                amount, unit = measurements[0]['quantity'], measurements[0]['unit']
                alternatives = measurements[1:]

    if not name:
        return {'name': capitalize_first_letter(original), 'quantity': None, 'unit': None, 'note': None, 'optional': False}
    return {'name': capitalize_first_letter(name), 'quantity': amount, 'unit': unit, 'note': None, 'optional': False, 'package_detail': package_detail, 'alternative_measurements': alternatives}


def normalize_imported_ingredient(ingredient: dict[str, Any]) -> dict[str, Any]:
    """Parse only unstructured imports; explicit fields and notes win unchanged."""
    result = dict(ingredient)
    result['name'] = capitalize_first_letter(str(result.get('name') or ''))
    result['unit'] = normalize_unit(result.get('unit'))
    if 'alternative_measurements' in result:
        result['alternative_measurements'] = [
            {**measurement, 'unit': normalize_unit(measurement.get('unit'))}
            for measurement in result.get('alternative_measurements', [])
        ]
    if result.get('quantity') is not None:
        return result
    parsed = parse_imported_ingredient(str(result.get('name') or ''))
    if parsed['quantity'] is None:
        return result
    result['name'] = parsed['name']
    result['quantity'] = parsed['quantity']
    if not result.get('unit'):
        result['unit'] = parsed['unit']
    if result.get('package_detail') or parsed.get('package_detail'):
        result['package_detail'] = result.get('package_detail') or parsed.get('package_detail')
    if result.get('alternative_measurements') or parsed.get('alternative_measurements'):
        result['alternative_measurements'] = result.get('alternative_measurements') or parsed.get('alternative_measurements', [])
    return result


def normalize_imported_draft(draft: dict[str, Any]) -> dict[str, Any]:
    result = dict(draft)
    description = ' '.join(str(result.get('description') or '').strip().strip('"“”').split())
    sentences = re.split(r'(?<=[.!?])\s+', description)
    result['description'] = ' '.join(sentences[:2])
    result['ingredient_sections'] = [{'heading': ' '.join(str(section.get('heading') or '').split())[:120]} for section in result.get('ingredient_sections', []) if str(section.get('heading') or '').strip()]
    result['instruction_sections'] = [{'heading': ' '.join(str(section.get('heading') or '').split())[:120]} for section in result.get('instruction_sections', []) if str(section.get('heading') or '').strip()]
    for field in ('tags', 'categories', 'proteins'):
        unique: list[str] = []
        for value in result.get(field, []):
            cleaned = ' '.join(str(value).split())
            if cleaned and cleaned.casefold() not in {item.casefold() for item in unique}:
                unique.append(cleaned)
        result[field] = unique
    result['ingredients'] = [normalize_imported_ingredient(item) for item in draft.get('ingredients', [])]
    result['steps'] = [{**step, 'instruction': capitalize_first_letter(str(step.get('instruction') or ''))} for step in draft.get('steps', [])]
    return result
