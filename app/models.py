from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class Protein(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    recipes: list["Recipe"] = Relationship(back_populates="protein")


class Recipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    protein_id: int = Field(foreign_key="protein.id")
    genre: str
    cook_time_min: int
    total_time_min: int
    servings: int
    source: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    protein: Protein = Relationship(back_populates="recipes")
    ingredients: list["Ingredient"] = Relationship(
        back_populates="recipe",
        sa_relationship_kwargs={
            "order_by": "Ingredient.position",
            "cascade": "all, delete-orphan",
        },
    )
    instructions: list["Instruction"] = Relationship(
        back_populates="recipe",
        sa_relationship_kwargs={
            "order_by": "Instruction.step_number",
            "cascade": "all, delete-orphan",
        },
    )


class Ingredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")
    position: int
    quantity: str | None = None
    unit: str | None = None
    item: str
    prep_note: str | None = None

    recipe: Recipe = Relationship(back_populates="ingredients")


class Instruction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")
    step_number: int
    text: str

    recipe: Recipe = Relationship(back_populates="instructions")
