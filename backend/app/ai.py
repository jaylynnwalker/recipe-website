import base64
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import json

import httpx
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .models import AIMonthlyBudget, AIRequest

BUDGET_MICROUSD = 10_000_000
WARNING_MICROUSD = 8_000_000
MODEL_PRICING = {
    'gpt-6-luna': {'input': Decimal('0.10'), 'output': Decimal('0.50')},
    'gpt-6.1-terra': {'input': Decimal('1.00'), 'output': Decimal('5.00')},
    'gpt-6.1-sol': {'input': Decimal('2.00'), 'output': Decimal('10.00')},
}
FEATURE_RESERVATIONS = {'image_extraction': 500_000, 'import_fallback': 200_000, 'recipe_ideas': 150_000, 'cooking_assistance': 75_000}


class AIUnavailable(Exception): pass
class BudgetExceeded(Exception): pass
class AIInvalidResponse(Exception): pass


class ResponsesClient:
    def __init__(self, api_key: str): self.api_key = api_key
    async def create(self, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=90) as client:
            try:
                response = await client.post('https://api.openai.com/v1/responses', json=payload, headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'})
            except httpx.HTTPError as error: raise AIUnavailable('The AI service could not be reached') from error
        if response.status_code >= 400:
            raise AIUnavailable('The AI service returned an error')
        return response.json()


def get_responses_client(settings: Settings) -> ResponsesClient:
    if not settings.openai_api_key: raise AIUnavailable('OpenAI API key is not configured')
    return ResponsesClient(settings.openai_api_key.get_secret_value())


def current_month() -> str: return datetime.now(timezone.utc).strftime('%Y-%m')


def pricing(settings: Settings) -> dict[str, Decimal]:
    if settings.openai_model not in MODEL_PRICING: raise AIUnavailable('The configured OpenAI model has no pricing entry')
    return MODEL_PRICING[settings.openai_model]


def usage_summary(db: Session, household_id: str) -> dict:
    month = current_month()
    budget = db.scalar(select(AIMonthlyBudget).where(AIMonthlyBudget.household_id == household_id, AIMonthlyBudget.month == month))
    spent = budget.spent_microusd if budget else 0; reserved = budget.reserved_microusd if budget else 0
    settings = get_settings()
    return {'month': month, 'spent_usd': spent / 1_000_000, 'reserved_usd': reserved / 1_000_000, 'budget_usd': 10, 'warning_usd': 8, 'warning': spent + reserved >= WARNING_MICROUSD, 'blocked': spent + reserved >= BUDGET_MICROUSD, 'model': settings.openai_model, 'configured': bool(settings.openai_api_key), 'disclaimer': 'Usage is estimated from reported tokens. Reservations reduce overspending risk but cannot guarantee an exact provider billing cap.'}


def reserve(db: Session, household_id: str, feature: str, model: str) -> AIRequest:
    month = current_month(); amount = FEATURE_RESERVATIONS[feature]
    budget = db.scalar(select(AIMonthlyBudget).where(AIMonthlyBudget.household_id == household_id, AIMonthlyBudget.month == month))
    if not budget:
        budget = AIMonthlyBudget(household_id=household_id, month=month)
        db.add(budget)
        try: db.commit()
        except IntegrityError:
            db.rollback(); budget = db.scalar(select(AIMonthlyBudget).where(AIMonthlyBudget.household_id == household_id, AIMonthlyBudget.month == month))
    result = db.execute(update(AIMonthlyBudget).where(AIMonthlyBudget.id == budget.id, AIMonthlyBudget.spent_microusd + AIMonthlyBudget.reserved_microusd + amount <= BUDGET_MICROUSD).values(reserved_microusd=AIMonthlyBudget.reserved_microusd + amount))
    if result.rowcount != 1:
        db.rollback(); raise BudgetExceeded('The monthly $10 AI budget is exhausted')
    request = AIRequest(household_id=household_id, budget_id=budget.id, feature=feature, model=model, reserved_microusd=amount)
    db.add(request); db.commit(); db.refresh(request)
    return request


def finish(db: Session, request: AIRequest, usage: dict | None, succeeded: bool):
    prices = MODEL_PRICING[request.model]
    input_tokens = usage.get('input_tokens') if usage else None; output_tokens = usage.get('output_tokens') if usage else None
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        dollars = Decimal(input_tokens) * prices['input'] / Decimal(1_000_000) + Decimal(output_tokens) * prices['output'] / Decimal(1_000_000)
        actual = int((dollars * Decimal(1_000_000)).to_integral_value(rounding=ROUND_CEILING))
    else:
        actual = request.reserved_microusd
    db.execute(update(AIMonthlyBudget).where(AIMonthlyBudget.id == request.budget_id).values(reserved_microusd=AIMonthlyBudget.reserved_microusd - request.reserved_microusd, spent_microusd=AIMonthlyBudget.spent_microusd + actual))
    request.status = 'completed' if succeeded else 'failed'; request.estimated_cost_microusd = actual; request.input_tokens = input_tokens; request.output_tokens = output_tokens; request.completed_at = datetime.now(timezone.utc)
    db.commit()


def output_text(response: dict) -> str:
    if isinstance(response.get('output_text'), str): return response['output_text']
    for item in response.get('output', []):
        for content in item.get('content', []):
            if content.get('type') == 'output_text' and isinstance(content.get('text'), str): return content['text']
    raise AIInvalidResponse('The AI response did not contain usable output')


async def run_structured(db: Session, household_id: str, feature: str, instructions: str, prompt: str, schema: dict, images: list[tuple[bytes, str]] | None = None) -> dict:
    settings = get_settings(); pricing(settings); client = get_responses_client(settings)
    reservation = reserve(db, household_id, feature, settings.openai_model)
    content = [{'type': 'input_text', 'text': prompt}]
    for data, media_type in images or []:
        encoded = base64.b64encode(data).decode('ascii')
        content.append({'type': 'input_image', 'image_url': f'data:{media_type};base64,{encoded}', 'detail': 'high'})
    payload = {'model': settings.openai_model, 'instructions': instructions, 'input': [{'role': 'user', 'content': content}], 'text': {'format': {'type': 'json_schema', 'name': 'our_kitchen_result', 'strict': True, 'schema': schema}}, 'reasoning': {'effort': 'low'}, 'max_output_tokens': 3000, 'store': False}
    response = None
    try:
        response = await client.create(payload)
        parsed = json.loads(output_text(response))
        finish(db, reservation, response.get('usage'), True)
        return parsed
    except Exception:
        finish(db, reservation, response.get('usage') if response else None, False)
        raise


NULL_STRING = {'anyOf': [{'type': 'string'}, {'type': 'null'}]}
NULL_NUMBER = {'anyOf': [{'type': 'number'}, {'type': 'null'}]}
RECIPE_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'title': {'type': 'string'}, 'description': {'type': 'string'}, 'cuisine': {'type': 'string'}, 'protein': {'type': 'string'},
        'tags': {'type': 'array', 'items': {'type': 'string'}}, 'categories': {'type': 'array', 'items': {'type': 'string'}},
        'prep_minutes': {'type': 'integer'}, 'cook_minutes': {'type': 'integer'}, 'base_servings': {'type': 'integer'},
        'ingredients': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'properties': {'name': {'type': 'string'}, 'quantity': NULL_NUMBER, 'unit': NULL_STRING, 'note': NULL_STRING, 'optional': {'type': 'boolean'}}, 'required': ['name', 'quantity', 'unit', 'note', 'optional']}},
        'steps': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'properties': {'instruction': {'type': 'string'}, 'tip': NULL_STRING}, 'required': ['instruction', 'tip']}},
        'notes': {'type': 'string'},
    },
    'required': ['title', 'description', 'cuisine', 'protein', 'tags', 'categories', 'prep_minutes', 'cook_minutes', 'base_servings', 'ingredients', 'steps', 'notes'],
}


def recipe_draft(parsed: dict, source: dict) -> dict:
    from .schemas import RecipeWrite
    payload = {**parsed, 'status': 'Want to Try', 'source': source}
    return RecipeWrite.model_validate(payload).model_dump(mode='json')
