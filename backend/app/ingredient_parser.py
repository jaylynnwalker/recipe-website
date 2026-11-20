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


def parse_imported_ingredient(text: str) -> dict[str, Any]:
    """Split an imported ingredient string without guessing beyond its prefix."""
    original = text.strip()
    expanded = _expand_unicode_fractions(original)
    match = QUANTITY_RE.match(expanded)
    if not match:
        return {'name': original, 'quantity': None, 'unit': None, 'note': None, 'optional': False}

    amount = _quantity(match.group('quantity'))
    if amount is None:
        return {'name': original, 'quantity': None, 'unit': None, 'note': None, 'optional': False}

    remainder = expanded[match.end():].strip()
    package_detail = None
    package_match = re.match(r'^\(([^)]+)\)\s*', remainder)
    unit_source = remainder
    if package_match and re.search(r'\d', package_match.group(1)):
        package_detail = package_match.group(1)
        unit_source = remainder[package_match.end():].strip()

    unit, name = _take_unit(unit_source)
    if package_detail and unit:
        name = _append_package_detail(name, package_detail)
    elif package_detail:
        name = remainder

    if not name:
        return {'name': original, 'quantity': None, 'unit': None, 'note': None, 'optional': False}
    return {'name': name, 'quantity': amount, 'unit': unit, 'note': None, 'optional': False}


def normalize_imported_ingredient(ingredient: dict[str, Any]) -> dict[str, Any]:
    """Parse only unstructured imports; explicit fields and notes win unchanged."""
    result = dict(ingredient)
    result['unit'] = normalize_unit(result.get('unit'))
    if result.get('quantity') is not None:
        return result
    parsed = parse_imported_ingredient(str(result.get('name') or ''))
    if parsed['quantity'] is None:
        return result
    result['name'] = parsed['name']
    result['quantity'] = parsed['quantity']
    if not result.get('unit'):
        result['unit'] = parsed['unit']
    return result


def normalize_imported_draft(draft: dict[str, Any]) -> dict[str, Any]:
    result = dict(draft)
    result['ingredients'] = [normalize_imported_ingredient(item) for item in draft.get('ingredients', [])]
    return result
