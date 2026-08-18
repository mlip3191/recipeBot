import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Ingredient, Instruction, Protein, Recipe
from app.seed import PROTEIN_NAMES, SAMPLE_RECIPES, seed


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_tables_get_created(session: Session) -> None:
    assert session.exec(select(Protein)).all() == []
    assert session.exec(select(Recipe)).all() == []
    assert session.exec(select(Ingredient)).all() == []
    assert session.exec(select(Instruction)).all() == []


def test_seed_is_idempotent(session: Session) -> None:
    seed(session)
    proteins_after_first = session.exec(select(Protein)).all()
    recipes_after_first = session.exec(select(Recipe)).all()

    assert len(proteins_after_first) == len(PROTEIN_NAMES)
    assert len(recipes_after_first) == len(SAMPLE_RECIPES)

    seed(session)
    proteins_after_second = session.exec(select(Protein)).all()
    recipes_after_second = session.exec(select(Recipe)).all()

    assert len(proteins_after_second) == len(PROTEIN_NAMES)
    assert len(recipes_after_second) == len(SAMPLE_RECIPES)


def test_recipe_round_trips_with_ordered_children(session: Session) -> None:
    protein = Protein(name="Chicken")
    session.add(protein)
    session.commit()
    session.refresh(protein)

    recipe = Recipe(
        name="Test Recipe",
        protein_id=protein.id,
        genre="Test",
        cook_time_min=10,
        total_time_min=15,
        servings=2,
    )
    session.add(recipe)
    session.commit()
    session.refresh(recipe)

    # Insert out of order to verify relationship ordering, not insertion order.
    session.add(Instruction(recipe_id=recipe.id, step_number=2, text="Second step"))
    session.add(Instruction(recipe_id=recipe.id, step_number=1, text="First step"))
    session.add(
        Ingredient(recipe_id=recipe.id, position=2, item="pepper", quantity="1", unit="tsp")
    )
    session.add(
        Ingredient(recipe_id=recipe.id, position=1, item="salt", quantity="1", unit="tsp")
    )
    session.commit()

    session.expire(recipe)
    fetched = session.get(Recipe, recipe.id)

    assert fetched.protein.name == "Chicken"
    assert [i.item for i in fetched.ingredients] == ["salt", "pepper"]
    assert [i.text for i in fetched.instructions] == ["First step", "Second step"]
