from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from .units import normalize_unit


RecipeStatus = Literal['Our Rotation', 'Want to Try', 'Archived']


class IngredientWrite(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=60)
    note: str | None = Field(default=None, max_length=300)
    optional: bool = False

    @field_validator('unit')
    @classmethod
    def standardize_unit(cls, value: str | None) -> str | None:
        return normalize_unit(value)


class IngredientRead(IngredientWrite):
    id: str


class StepWrite(BaseModel):
    instruction: str = Field(min_length=1, max_length=5000)
    tip: str | None = Field(default=None, max_length=2000)


class StepRead(StepWrite):
    id: str


class SourceWrite(BaseModel):
    type: str | None = Field(default=None, max_length=30)
    label: str = Field(default='Household recipe', max_length=300)
    url: HttpUrl | None = None
    page: str | None = Field(default=None, max_length=100)


class PhotoRead(BaseModel):
    id: str
    url: str
    alt_text: str
    media_type: str


class RecipeWrite(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=5000)
    status: RecipeStatus
    cuisine: str = Field(default='', max_length=100)
    protein: str = Field(default='', max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=30)
    categories: list[str] = Field(default_factory=list, max_length=20)
    prep_minutes: int = Field(default=0, ge=0, le=10080)
    cook_minutes: int = Field(default=0, ge=0, le=10080)
    base_servings: int = Field(default=4, ge=1, le=100)
    ingredients: list[IngredientWrite] = Field(default_factory=list, max_length=200)
    steps: list[StepWrite] = Field(default_factory=list, max_length=200)
    notes: str = Field(default='', max_length=20000)
    source: SourceWrite = Field(default_factory=SourceWrite)

    @field_validator('tags', 'categories')
    @classmethod
    def clean_names(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            name = value.strip()
            if name and name.casefold() not in {item.casefold() for item in cleaned}:
                cleaned.append(name[:100])
        return cleaned

    @field_validator('cuisine')
    @classmethod
    def clean_cuisine(cls, value: str) -> str:
        return ' '.join(value.split())[:100]


class RecipeRead(RecipeWrite):
    id: str
    image: str | None
    image_alt: str
    photos: list[PhotoRead]
    created_at: datetime
    updated_at: datetime
    cooking_history: list[datetime]


class PantryStapleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class PantryStapleRead(BaseModel):
    id: str
    name: str
    model_config = ConfigDict(from_attributes=True)


class DeckEntryCreate(BaseModel):
    recipe_id: str
    servings: int | None = Field(default=None, ge=1, le=100)


class DeckEntryUpdate(BaseModel):
    servings: int | None = Field(default=None, ge=1, le=100)
    cooked: bool | None = None


class GroceryItemCreate(BaseModel):
    label: str = Field(min_length=1, max_length=240)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=60)
    category: str = Field(default='Other', min_length=1, max_length=80)


class GroceryItemUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=240)
    quantity: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=60)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    checked: bool | None = None


class InboxUrlCreate(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


class IngredientIdeaRequest(BaseModel):
    ingredients: list[str] = Field(default_factory=list, max_length=50)
    include_pantry_staples: bool = True
    generate_ai: bool = False


class HelpPickRequest(BaseModel):
    mode: Literal['Our Rotation', 'Forgotten Favorites', 'Want to Try', 'Mix'] = 'Mix'
    generate_ai: bool = False


class CookingAssistRequest(BaseModel):
    recipe_id: str
    question: str = Field(min_length=2, max_length=1000)
    current_step: int | None = Field(default=None, ge=0)
