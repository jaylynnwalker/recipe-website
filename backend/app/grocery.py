from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
import re

from .units import UNIT_FACTORS, normalize_unit

PRODUCE = {'apple', 'avocado', 'basil', 'broccoli', 'carrot', 'cilantro', 'cucumber', 'garlic', 'ginger', 'lemon', 'lime', 'mushroom', 'onion', 'pepper', 'potato', 'spinach', 'tomato'}
MEAT = {'beef', 'chicken', 'fish', 'pork', 'salmon', 'sausage', 'shrimp', 'steak', 'turkey'}
DAIRY = {'butter', 'cheese', 'cream', 'egg', 'milk', 'parmesan', 'yogurt'}
BAKERY = {'bagel', 'bread', 'bun', 'tortilla'}
FROZEN = {'frozen', 'ice cream'}

# Only deterministic shopping aliases belong here. Qualifiers such as salted,
# unsalted, low-sodium, or smoked intentionally remain part of the identity.
NAME_ALIASES = {
    'confectioner sugar': 'powdered sugar',
    'confectioners sugar': 'powdered sugar',
    'icing sugar': 'powdered sugar',
    'scallion': 'green onion',
    'chickpea': 'garbanzo bean',
}
SPELLING_ALIASES = {'chilli': 'chili', 'yoghurt': 'yogurt'}
PREPARATION_WORDS = {'chopped', 'diced', 'minced', 'rinsed', 'drained', 'sliced', 'peeled', 'crushed', 'shredded', 'grated'}
COUNT_UNITS = {'whole', 'clove', 'slice', 'can', 'bunch', 'package', 'packet', 'stick', 'piece', 'head', 'sprig', 'stalk', 'bottle', 'jar', 'box', 'pinch', 'dash'}
SPICE_TERMS = {'spice', 'seasoning', 'salt', 'pepper', 'cinnamon', 'cumin', 'paprika', 'oregano', 'thyme', 'nutmeg', 'clove', 'chili powder'}

# Conservative, standard US baking conversions. No other volume-to-weight
# conversion is attempted because fluid volume and weight are not equivalent.
GRAMS_PER_CUP = {
    'all purpose flour': Decimal('120'),
    'flour': Decimal('120'),
    'granulated sugar': Decimal('200'),
    'sugar': Decimal('200'),
    'brown sugar': Decimal('220'),
    'butter': Decimal('227'),
    'unsalted butter': Decimal('227'),
    'salted butter': Decimal('227'),
}


def _singularize(word: str) -> str:
    if word.endswith('ies') and len(word) > 4: return f'{word[:-3]}y'
    if word.endswith(('oes', 'ses', 'xes', 'zes', 'ches', 'shes')) and len(word) > 4: return word[:-2]
    if word.endswith('s') and not word.endswith(('ss', 'us')) and len(word) > 3: return word[:-1]
    return word


def normalize_name(value: str) -> str:
    cleaned = re.sub(r'\([^)]*\)', ' ', value.casefold())
    cleaned = re.sub(r'[^a-z0-9 ]+', ' ', cleaned)
    words = [SPELLING_ALIASES.get(word, word) for word in cleaned.split() if word not in PREPARATION_WORDS]
    if words: words[-1] = _singularize(words[-1])
    normalized = ' '.join(words)
    return NAME_ALIASES.get(normalized, normalized)


def shopping_name(value: str, normalized: str) -> str:
    cleaned = re.sub(r'\([^)]*\)', ' ', value)
    cleaned = re.sub(r'[,;].*$', '', cleaned)
    words = [word for word in cleaned.split() if word.casefold().strip('.,') not in PREPARATION_WORDS]
    display = ' '.join(words).strip()
    if normalize_name(display) != normalized or normalized in NAME_ALIASES.values():
        display = normalized
    return display[:1].upper() + display[1:] if display else normalized.capitalize()


def ingredient_category(name: str) -> str:
    words = set(normalize_name(name).split())
    if words & PRODUCE: return 'Produce'
    if words & MEAT: return 'Meat & seafood'
    if words & DAIRY: return 'Dairy & eggs'
    if words & BAKERY: return 'Bakery'
    if words & FROZEN: return 'Frozen'
    return 'Pantry'


@dataclass
class QuantityComponent:
    quantity: Decimal | None
    unit: str | None
    package_detail: str | None = None


@dataclass
class SourceRecipe:
    id: str
    title: str


@dataclass
class GeneratedItem:
    name: str
    normalized_name: str
    components: list[QuantityComponent]
    category: str
    source_key: str
    sources: list[SourceRecipe] = field(default_factory=list)

    @property
    def quantity(self) -> Decimal | None:
        return self.components[0].quantity if len(self.components) == 1 else None

    @property
    def unit(self) -> str | None:
        return self.components[0].unit if len(self.components) == 1 else None


def _dimension(normalized_name: str, unit: str | None, package_detail: str | None = None) -> tuple[str, Decimal]:
    if unit in UNIT_FACTORS:
        dimension, factor = UNIT_FACTORS[unit]
        if dimension == 'volume' and normalized_name in GRAMS_PER_CUP:
            grams_per_ml = GRAMS_PER_CUP[normalized_name] / UNIT_FACTORS['cup'][1]
            return 'mass', factor * grams_per_ml
        return dimension, factor
    if unit in COUNT_UNITS: return f'count:{unit}:{" ".join((package_detail or "").casefold().split())}', Decimal('1')
    return f'unit:{unit or "none"}', Decimal('1')


def _practical_component(name: str, dimension: str, base_quantity: Decimal | None, original_unit: str | None, package_detail: str | None = None) -> QuantityComponent:
    if base_quantity is None: return QuantityComponent(None, original_unit, package_detail)
    if dimension == 'mass':
        ounces = base_quantity / UNIT_FACTORS['oz'][1]
        return QuantityComponent(ounces / Decimal('16'), 'lb') if ounces >= 16 else QuantityComponent(ounces, 'oz')
    if dimension == 'volume':
        fluid_ounces = base_quantity / UNIT_FACTORS['fl oz'][1]
        if any(term in name for term in SPICE_TERMS):
            teaspoons = base_quantity / UNIT_FACTORS['tsp'][1]
            return QuantityComponent(teaspoons / Decimal('3'), 'tbsp') if teaspoons >= 3 else QuantityComponent(teaspoons, 'tsp')
        if fluid_ounces >= 128: return QuantityComponent(fluid_ounces / Decimal('128'), 'gal')
        if fluid_ounces >= 32: return QuantityComponent(fluid_ounces / Decimal('32'), 'qt')
        if fluid_ounces >= 1: return QuantityComponent(fluid_ounces, 'fl oz')
        teaspoons = base_quantity / UNIT_FACTORS['tsp'][1]
        return QuantityComponent(teaspoons / Decimal('3'), 'tbsp') if teaspoons >= 3 else QuantityComponent(teaspoons, 'tsp')
    return QuantityComponent(base_quantity, original_unit, package_detail)


def generate_items(deck_entries, pantry_staples) -> tuple[list[GeneratedItem], list[str]]:
    staples = {normalize_name(item.name): item.name for item in pantry_staples}
    excluded: dict[str, str] = {}
    buckets: dict[str, dict] = {}
    for entry in deck_entries:
        if entry.cooked_at is not None: continue
        scale = Decimal(entry.servings) / Decimal(entry.recipe.base_servings)
        for recipe_item in entry.recipe.ingredients:
            original_name = recipe_item.ingredient.display_name
            normalized = normalize_name(original_name)
            if normalized in staples:
                excluded[normalized] = staples[normalized]
                continue
            unit = normalize_unit(recipe_item.unit)
            quantity = Decimal(str(recipe_item.quantity)) * scale if recipe_item.quantity is not None else None
            package_detail = getattr(recipe_item, 'package_detail', None)
            dimension, factor = _dimension(normalized, unit, package_detail)
            bucket = buckets.setdefault(normalized, {'name': shopping_name(original_name, normalized), 'dimensions': {}, 'unknown': [], 'sources': {}})
            recipe_id = getattr(entry.recipe, 'id', None)
            if recipe_id:
                bucket['sources'][recipe_id] = getattr(entry.recipe, 'title', 'Recipe')
            if quantity is None:
                marker = (dimension, unit, package_detail)
                if marker not in bucket['unknown']: bucket['unknown'].append(marker)
            else:
                current = bucket['dimensions'].get(dimension, {'quantity': Decimal('0'), 'unit': unit, 'package_detail': package_detail})
                current['quantity'] += quantity * factor
                bucket['dimensions'][dimension] = current
    generated = []
    for normalized, bucket in buckets.items():
        components = [_practical_component(normalized, dimension, details['quantity'], details['unit'], details['package_detail']) for dimension, details in sorted(bucket['dimensions'].items())]
        components.extend(_practical_component(normalized, dimension, None, unit, package_detail) for dimension, unit, package_detail in bucket['unknown'])
        generated.append(GeneratedItem(
            name=bucket['name'], normalized_name=normalized, components=components,
            category=ingredient_category(normalized), source_key=f'ingredient:{normalized}',
            sources=[SourceRecipe(id=recipe_id, title=title) for recipe_id, title in bucket['sources'].items()],
        ))
    return sorted(generated, key=lambda item: (item.category, item.name.casefold())), sorted(excluded.values(), key=str.casefold)


def format_quantity(quantity: Decimal) -> str:
    fraction = Fraction(quantity).limit_denominator(16)
    if abs(Decimal(fraction.numerator) / Decimal(fraction.denominator) - quantity) <= Decimal('0.01'):
        whole, remainder = divmod(abs(fraction.numerator), fraction.denominator)
        sign = '-' if fraction.numerator < 0 else ''
        if remainder and whole: return f'{sign}{whole} {remainder}/{fraction.denominator}'
        if remainder: return f'{sign}{remainder}/{fraction.denominator}'
        return f'{sign}{whole}'
    amount = f'{quantity.quantize(Decimal("0.01")):f}'
    return amount.rstrip('0').rstrip('.')


def _plural_unit(unit: str, quantity: Decimal) -> str:
    if quantity == 1 or unit.endswith('s'): return unit
    if unit == 'box': return 'boxes'
    return f'{unit}s'


def _format_component(component: QuantityComponent) -> str:
    if component.quantity is None:
        return f'unspecified {component.unit}' if component.unit else 'amount unspecified'
    amount = format_quantity(component.quantity)
    if component.package_detail and component.unit in COUNT_UNITS:
        detail = re.sub(r'\s+(?:each|ea\.?|per\s+\w+)\s*$', '', component.package_detail.strip(), flags=re.IGNORECASE)
        return f'{amount} × {detail} {_plural_unit(component.unit, component.quantity)}'
    return ' '.join(part for part in (amount, component.unit) if part)


def format_item_label(name: str, quantity: Decimal | None = None, unit: str | None = None, components: list[QuantityComponent] | None = None) -> str:
    values = components if components is not None else [QuantityComponent(quantity, unit)]
    if values and all(value.quantity is None for value in values):
        return name
    details = ' + '.join(_format_component(component) for component in values)
    return f'{name} — {details}'
