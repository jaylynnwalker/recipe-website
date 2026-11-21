from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


recipe_tags = Table("recipe_tags", Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True))
recipe_categories = Table("recipe_categories", Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True))
recipe_proteins = Table("recipe_proteins", Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("protein_id", ForeignKey("proteins.id", ondelete="CASCADE"), primary_key=True))


class Household(Base):
    __tablename__ = "households"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), default="Our Kitchen")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    users: Mapped[list[User]] = relationship(back_populates="household", cascade="all, delete-orphan")
    deck_entries: Mapped[list[DeckEntry]] = relationship(back_populates="household", cascade="all, delete-orphan")
    grocery_list: Mapped[GroceryList | None] = relationship(back_populates="household", cascade="all, delete-orphan", uselist=False)
    import_jobs: Mapped[list[ImportJob]] = relationship(back_populates="household", cascade="all, delete-orphan")
    ai_budgets: Mapped[list[AIMonthlyBudget]] = relationship(back_populates="household", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    household: Mapped[Household] = relationship(back_populates="users")
    sessions: Mapped[list[UserSession]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(back_populates="sessions")


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (UniqueConstraint("household_id", "title", name="uq_household_recipe_title"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), index=True)
    cuisine: Mapped[str] = mapped_column(String(100), default="")
    protein: Mapped[str] = mapped_column(String(100), default="")
    prep_minutes: Mapped[int] = mapped_column(Integer, default=0)
    cook_minutes: Mapped[int] = mapped_column(Integer, default=0)
    additional_time_minutes: Mapped[int] = mapped_column(Integer, default=0)
    additional_time_label: Mapped[str] = mapped_column(String(60), default="Additional")
    base_servings: Mapped[int] = mapped_column(Integer, default=4)
    yield_unit: Mapped[str] = mapped_column(String(60), default="servings")
    notes: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_label: Mapped[str] = mapped_column(String(300), default="Household recipe")
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_page: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    ingredients: Mapped[list[RecipeIngredient]] = relationship(back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeIngredient.position")
    steps: Mapped[list[RecipeStep]] = relationship(back_populates="recipe", cascade="all, delete-orphan", order_by="RecipeStep.position")
    tags: Mapped[list[Tag]] = relationship(secondary=recipe_tags)
    categories: Mapped[list[Category]] = relationship(secondary=recipe_categories)
    proteins: Mapped[list[Protein]] = relationship(secondary=recipe_proteins)
    photos: Mapped[list[RecipePhoto]] = relationship(back_populates="recipe", cascade="all, delete-orphan", order_by="RecipePhoto.position")
    cooking_events: Mapped[list[CookingEvent]] = relationship(back_populates="recipe", cascade="all, delete-orphan")


class Ingredient(Base):
    __tablename__ = "ingredients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    normalized_name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (UniqueConstraint("recipe_id", "position", name="uq_recipe_ingredient_position"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    ingredient_id: Mapped[str] = mapped_column(ForeignKey("ingredients.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    package_detail: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()
    alternative_measurements: Mapped[list[IngredientMeasurement]] = relationship(cascade="all, delete-orphan", order_by="IngredientMeasurement.position")


class IngredientMeasurement(Base):
    __tablename__ = "ingredient_measurements"
    __table_args__ = (UniqueConstraint("recipe_ingredient_id", "position", name="uq_ingredient_measurement_position"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipe_ingredient_id: Mapped[str] = mapped_column(ForeignKey("recipe_ingredients.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)


class RecipeStep(Base):
    __tablename__ = "recipe_steps"
    __table_args__ = (UniqueConstraint("recipe_id", "position", name="uq_recipe_step_position"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)
    tip: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipe: Mapped[Recipe] = relationship(back_populates="steps")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Protein(Base):
    __tablename__ = "proteins"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class RecipePhoto(Base):
    __tablename__ = "recipe_photos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    storage_name: Mapped[str] = mapped_column(String(255), unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(80))
    alt_text: Mapped[str] = mapped_column(String(300), default="Recipe photo")
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=True)
    recipe: Mapped[Recipe] = relationship(back_populates="photos")


class CookingEvent(Base):
    __tablename__ = "cooking_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    cooked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    recipe: Mapped[Recipe] = relationship(back_populates="cooking_events")


class PantryStaple(Base):
    __tablename__ = "pantry_staples"
    __table_args__ = (UniqueConstraint("household_id", "normalized_name", name="uq_household_staple"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    normalized_name: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeckEntry(Base):
    __tablename__ = "deck_entries"
    __table_args__ = (UniqueConstraint("household_id", "recipe_id", name="uq_household_deck_recipe"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    recipe_id: Mapped[str] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), index=True)
    servings: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer, default=0)
    cooked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    household: Mapped[Household] = relationship(back_populates="deck_entries")
    recipe: Mapped[Recipe] = relationship()


class GroceryList(Base):
    __tablename__ = "grocery_lists"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), unique=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    household: Mapped[Household] = relationship(back_populates="grocery_list")
    items: Mapped[list[GroceryItem]] = relationship(back_populates="grocery_list", cascade="all, delete-orphan")
    excluded_staples: Mapped[list[GroceryExcludedStaple]] = relationship(back_populates="grocery_list", cascade="all, delete-orphan")


class GroceryItem(Base):
    __tablename__ = "grocery_items"
    __table_args__ = (UniqueConstraint("grocery_list_id", "source_key", name="uq_grocery_generated_source"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    grocery_list_id: Mapped[str] = mapped_column(ForeignKey("grocery_lists.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(240))
    normalized_name: Mapped[str] = mapped_column(String(160), index=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    category: Mapped[str] = mapped_column(String(80), default="Other")
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    source_key: Mapped[str | None] = mapped_column(String(260), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    grocery_list: Mapped[GroceryList] = relationship(back_populates="items")


class GroceryExcludedStaple(Base):
    __tablename__ = "grocery_excluded_staples"
    __table_args__ = (UniqueConstraint("grocery_list_id", "normalized_name", name="uq_grocery_excluded_staple"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    grocery_list_id: Mapped[str] = mapped_column(ForeignKey("grocery_lists.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    normalized_name: Mapped[str] = mapped_column(String(160))
    grocery_list: Mapped[GroceryList] = relationship(back_populates="excluded_staples")


class ImportJob(Base):
    __tablename__ = "import_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(30))
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="Pending")
    title: Mapped[str] = mapped_column(String(240), default="Untitled import")
    draft_payload: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duplicate_recipe_id: Mapped[str | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    saved_recipe_id: Mapped[str | None] = mapped_column(ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    household: Mapped[Household] = relationship(back_populates="import_jobs")
    assets: Mapped[list[ImportAsset]] = relationship(back_populates="job", cascade="all, delete-orphan", order_by="ImportAsset.position")


class ImportAsset(Base):
    __tablename__ = "import_assets"
    __table_args__ = (UniqueConstraint("import_job_id", "position", name="uq_import_asset_position"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    import_job_id: Mapped[str] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True)
    storage_name: Mapped[str] = mapped_column(String(255), unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(80))
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    job: Mapped[ImportJob] = relationship(back_populates="assets")


class AIMonthlyBudget(Base):
    __tablename__ = "ai_monthly_budgets"
    __table_args__ = (UniqueConstraint("household_id", "month", name="uq_ai_household_month"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    month: Mapped[str] = mapped_column(String(7), index=True)
    spent_microusd: Mapped[int] = mapped_column(Integer, default=0)
    reserved_microusd: Mapped[int] = mapped_column(Integer, default=0)
    household: Mapped[Household] = relationship(back_populates="ai_budgets")


class AIRequest(Base):
    __tablename__ = "ai_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    household_id: Mapped[str] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    budget_id: Mapped[str] = mapped_column(ForeignKey("ai_monthly_budgets.id", ondelete="CASCADE"), index=True)
    feature: Mapped[str] = mapped_column(String(60), index=True)
    model: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="reserved", index=True)
    reserved_microusd: Mapped[int] = mapped_column(Integer)
    estimated_cost_microusd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
