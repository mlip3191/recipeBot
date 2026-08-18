from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Ingredient, Instruction, Protein, Recipe
from app.schemas import (
    IngredientCreate,
    InstructionCreate,
    ProteinRead,
    RecipeCreate,
    RecipeRead,
    RecipeSummary,
)

router = APIRouter(prefix="/api", tags=["api"])

NO_MATCH_DETAIL = "No recipes match those filters."


def resolve_protein_id(session: Session, protein: str) -> int | None:
    try:
        protein_id = int(protein)
    except ValueError:
        result = session.exec(
            select(Protein).where(func.lower(Protein.name) == protein.lower())
        ).first()
        return result.id if result else None

    return protein_id if session.get(Protein, protein_id) else None


def apply_children(
    session: Session,
    recipe_id: int,
    ingredients: list[IngredientCreate],
    instructions: list[InstructionCreate],
) -> None:
    for index, ingredient in enumerate(ingredients, start=1):
        session.add(
            Ingredient(
                recipe_id=recipe_id,
                position=ingredient.position or index,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
                item=ingredient.item,
                prep_note=ingredient.prep_note,
            )
        )
    for index, instruction in enumerate(instructions, start=1):
        session.add(
            Instruction(
                recipe_id=recipe_id,
                step_number=instruction.step_number or index,
                text=instruction.text,
            )
        )


@router.get("/proteins", response_model=list[ProteinRead])
def list_proteins(session: Session = Depends(get_session)):
    return session.exec(select(Protein).order_by(Protein.name)).all()


@router.get("/genres", response_model=list[str])
def list_genres(session: Session = Depends(get_session)):
    return session.exec(select(Recipe.genre).distinct().order_by(Recipe.genre)).all()


@router.get("/recipes", response_model=list[RecipeSummary])
def list_recipes(
    protein: str | None = None,
    genre: str | None = None,
    session: Session = Depends(get_session),
):
    statement = select(Recipe)
    if protein is not None:
        protein_id = resolve_protein_id(session, protein)
        if protein_id is None:
            return []
        statement = statement.where(Recipe.protein_id == protein_id)
    if genre is not None:
        statement = statement.where(func.lower(Recipe.genre) == genre.lower())

    recipes = session.exec(statement).all()
    return [
        RecipeSummary(
            id=recipe.id,
            name=recipe.name,
            protein=recipe.protein.name,
            genre=recipe.genre,
            cook_time_min=recipe.cook_time_min,
            total_time_min=recipe.total_time_min,
        )
        for recipe in recipes
    ]


@router.get("/recipes/random", response_model=RecipeRead)
def random_recipe(
    protein: str | None = None,
    genre: str | None = None,
    session: Session = Depends(get_session),
):
    statement = select(Recipe)
    if protein is not None:
        protein_id = resolve_protein_id(session, protein)
        if protein_id is None:
            raise HTTPException(status_code=404, detail=NO_MATCH_DETAIL)
        statement = statement.where(Recipe.protein_id == protein_id)
    if genre is not None:
        statement = statement.where(func.lower(Recipe.genre) == genre.lower())

    statement = statement.order_by(func.random()).limit(1)
    recipe = session.exec(statement).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail=NO_MATCH_DETAIL)
    return recipe


@router.get("/recipes/{recipe_id}", response_model=RecipeRead)
def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    recipe = session.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found.")
    return recipe


@router.post("/recipes", response_model=RecipeRead, status_code=201)
def create_recipe(payload: RecipeCreate, session: Session = Depends(get_session)):
    if session.get(Protein, payload.protein_id) is None:
        raise HTTPException(
            status_code=400, detail=f"Protein {payload.protein_id} not found."
        )

    recipe = Recipe(
        name=payload.name,
        protein_id=payload.protein_id,
        genre=payload.genre,
        cook_time_min=payload.cook_time_min,
        total_time_min=payload.total_time_min,
        servings=payload.servings,
        source=payload.source,
        notes=payload.notes,
    )
    session.add(recipe)
    session.flush()

    apply_children(session, recipe.id, payload.ingredients, payload.instructions)
    session.commit()
    session.refresh(recipe)
    return recipe


@router.put("/recipes/{recipe_id}", response_model=RecipeRead)
def replace_recipe(
    recipe_id: int, payload: RecipeCreate, session: Session = Depends(get_session)
):
    recipe = session.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found.")
    if session.get(Protein, payload.protein_id) is None:
        raise HTTPException(
            status_code=400, detail=f"Protein {payload.protein_id} not found."
        )

    recipe.name = payload.name
    recipe.protein_id = payload.protein_id
    recipe.genre = payload.genre
    recipe.cook_time_min = payload.cook_time_min
    recipe.total_time_min = payload.total_time_min
    recipe.servings = payload.servings
    recipe.source = payload.source
    recipe.notes = payload.notes
    session.add(recipe)

    for ingredient in list(recipe.ingredients):
        session.delete(ingredient)
    for instruction in list(recipe.instructions):
        session.delete(instruction)
    session.flush()

    apply_children(session, recipe.id, payload.ingredients, payload.instructions)
    session.commit()
    session.refresh(recipe)
    return recipe


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, session: Session = Depends(get_session)):
    recipe = session.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found.")
    session.delete(recipe)
    session.commit()
