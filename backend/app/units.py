from decimal import Decimal


COMMON_UNITS = [
    'tsp', 'tbsp', 'cup', 'fl oz', 'oz', 'lb', 'mg', 'g', 'kg', 'mL', 'L',
    'pt', 'qt', 'gal', 'whole', 'clove', 'slice', 'can', 'bunch', 'package',
    'packet', 'stick', 'piece', 'head', 'sprig', 'stalk', 'bottle', 'jar',
    'box', 'pinch', 'dash',
]

_ALIASES = {
    'teaspoon': 'tsp', 'teaspoons': 'tsp', 't': 'tsp',
    'tablespoon': 'tbsp', 'tablespoons': 'tbsp', 'tbs': 'tbsp',
    'cups': 'cup',
    'fluid ounce': 'fl oz', 'fluid ounces': 'fl oz', 'fluid oz': 'fl oz', 'fl. oz.': 'fl oz',
    'ounce': 'oz', 'ounces': 'oz',
    'pound': 'lb', 'pounds': 'lb', 'lbs': 'lb',
    'milligram': 'mg', 'milligrams': 'mg',
    'gram': 'g', 'grams': 'g',
    'kilogram': 'kg', 'kilograms': 'kg', 'kgs': 'kg',
    'ml': 'mL', 'milliliter': 'mL', 'milliliters': 'mL', 'millilitre': 'mL', 'millilitres': 'mL',
    'l': 'L', 'liter': 'L', 'liters': 'L', 'litre': 'L', 'litres': 'L',
    'pint': 'pt', 'pints': 'pt', 'quart': 'qt', 'quarts': 'qt', 'gallon': 'gal', 'gallons': 'gal',
    'cloves': 'clove', 'slices': 'slice', 'cans': 'can', 'bunches': 'bunch',
    'packages': 'package', 'pkg': 'package', 'pkgs': 'package', 'packets': 'packet',
    'sticks': 'stick', 'pieces': 'piece', 'heads': 'head', 'sprigs': 'sprig',
    'stalks': 'stalk', 'bottles': 'bottle', 'jars': 'jar', 'boxes': 'box',
    'pinches': 'pinch', 'dashes': 'dash',
}

UNIT_ALIASES = {unit.casefold(): unit for unit in COMMON_UNITS} | _ALIASES

# Conversion factors use grams for mass and milliliters for volume.
UNIT_FACTORS = {
    'mg': ('mass', Decimal('.001')), 'g': ('mass', Decimal('1')), 'kg': ('mass', Decimal('1000')),
    'oz': ('mass', Decimal('28.349523125')), 'lb': ('mass', Decimal('453.59237')),
    'mL': ('volume', Decimal('1')), 'L': ('volume', Decimal('1000')),
    'tsp': ('volume', Decimal('4.92892159375')), 'tbsp': ('volume', Decimal('14.78676478125')),
    'fl oz': ('volume', Decimal('29.5735295625')), 'cup': ('volume', Decimal('236.5882365')),
    'pt': ('volume', Decimal('473.176473')), 'qt': ('volume', Decimal('946.352946')), 'gal': ('volume', Decimal('3785.411784')),
}


def normalize_unit(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    cleaned = ' '.join(value.strip().split())
    return UNIT_ALIASES.get(cleaned.casefold(), cleaned)
