import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Ingredient, Instruction, Protein, Recipe, Tag
from app.seed import PROTEIN_NAMES, SAMPLE_RECIPES, TAG_NAMES, seed


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
    tags_after_first = session.exec(select(Tag)).all()

    assert len(proteins_after_first) == len(PROTEIN_NAMES)
    assert len(recipes_after_first) == len(SAMPLE_RECIPES)
    assert len(tags_after_first) == len(TAG_NAMES)

    seed(session)
    proteins_after_second = session.exec(select(Protein)).all()
    recipes_after_second = session.exec(select(Recipe)).all()
    tags_after_second = session.exec(select(Tag)).all()

    assert len(proteins_after_second) == len(PROTEIN_NAMES)
    assert len(recipes_after_second) == len(SAMPLE_RECIPES)
    assert len(tags_after_second) == len(TAG_NAMES)


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


def test_recipe_tags_are_many_to_many_and_shared(session: Session) -> None:
    protein = Protein(name="Beef")
    session.add(protein)
    session.commit()
    session.refresh(protein)

    weeknight = Tag(name="weeknight")
    spicy = Tag(name="spicy")
    session.add(weeknight)
    session.add(spicy)
    session.commit()

    recipe_a = Recipe(
        name="Recipe A",
        protein_id=protein.id,
        genre="Test",
        cook_time_min=10,
        total_time_min=15,
        servings=2,
        tags=[spicy, weeknight],
    )
    recipe_b = Recipe(
        name="Recipe B",
        protein_id=protein.id,
        genre="Test",
        cook_time_min=10,
        total_time_min=15,
        servings=2,
        tags=[weeknight],
    )
    session.add(recipe_a)
    session.add(recipe_b)
    session.commit()

    session.refresh(weeknight)
    assert {r.name for r in weeknight.recipes} == {"Recipe A", "Recipe B"}

    session.refresh(recipe_a)
    assert [t.name for t in recipe_a.tags] == ["spicy", "weeknight"]

    session.delete(recipe_a)
    session.commit()

    remaining_tag = session.get(Tag, weeknight.id)
    assert remaining_tag is not None
    assert [r.name for r in remaining_tag.recipes] == ["Recipe B"]
