from datetime import datetime

from sqlmodel import SQLModel


class ProteinRead(SQLModel):
    id: int
    name: str


class TagRead(SQLModel):
    id: int
    name: str


class IngredientRead(SQLModel):
    id: int
    position: int
    quantity: str | None
    unit: str | None
    item: str
    prep_note: str | None


class InstructionRead(SQLModel):
    id: int
    step_number: int
    text: str


class IngredientCreate(SQLModel):
    quantity: str | None = None
    unit: str | None = None
    item: str
    prep_note: str | None = None
    position: int | None = None


class InstructionCreate(SQLModel):
    text: str
    step_number: int | None = None


class RecipeSummary(SQLModel):
    id: int
    name: str
    protein: str
    genre: str
    cook_time_min: int
    total_time_min: int


class RecipeRead(SQLModel):
    id: int
    name: str
    protein: ProteinRead
    genre: str
    cook_time_min: int
    total_time_min: int
    servings: int
    source: str | None
    notes: str | None
    created_at: datetime
    ingredients: list[IngredientRead]
    instructions: list[InstructionRead]
    tags: list[TagRead]


class RecipeCreate(SQLModel):
    name: str
    protein_id: int
    genre: str
    cook_time_min: int
    total_time_min: int
    servings: int
    source: str | None = None
    notes: str | None = None
    ingredients: list[IngredientCreate] = []
    instructions: list[InstructionCreate] = []
    tags: list[str] = []
