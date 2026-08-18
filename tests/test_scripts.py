import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Protein, Recipe
from scripts.export_recipes import recipe_to_dict
from scripts.import_recipes import upsert_recipe, validate_recipe_data


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Protein(name="Chicken"))
        session.add(Protein(name="Beef"))
        session.commit()
        yield session


def recipe_data(**overrides) -> dict:
    data = {
        "name": "Test Recipe",
        "protein_id": 1,
        "genre": "Test",
        "cook_time_min": 10,
        "total_time_min": 15,
        "servings": 2,
        "source": "Unit test",
        "notes": "Some notes",
        "ingredients": [
            {"item": "salt", "quantity": "1", "unit": "tsp"},
            {"item": "pepper", "quantity": "1", "unit": "tsp"},
        ],
        "instructions": [
            {"text": "First step"},
            {"text": "Second step"},
        ],
    }
    data.update(overrides)
    return data


def test_validate_recipe_data_requires_fields() -> None:
    with pytest.raises(ValueError, match="missing required field"):
        validate_recipe_data({"name": "Incomplete"})


def test_validate_recipe_data_requires_ingredient_item() -> None:
    data = recipe_data(ingredients=[{"quantity": "1"}])
    with pytest.raises(ValueError, match="item"):
        validate_recipe_data(data)


def test_validate_recipe_data_requires_instruction_text() -> None:
    data = recipe_data(instructions=[{"step_number": 1}])
    with pytest.raises(ValueError, match="text"):
        validate_recipe_data(data)


def test_upsert_creates_then_updates(session: Session) -> None:
    action = upsert_recipe(session, recipe_data())
    session.commit()
    assert action == "created"

    recipes = session.exec(select(Recipe)).all()
    assert len(recipes) == 1
    assert [i.item for i in recipes[0].ingredients] == ["salt", "pepper"]

    updated_data = recipe_data(genre="Updated Genre", ingredients=[{"item": "cumin"}])
    action = upsert_recipe(session, updated_data)
    session.commit()
    assert action == "updated"

    recipes = session.exec(select(Recipe)).all()
    assert len(recipes) == 1
    assert recipes[0].genre == "Updated Genre"
    assert [i.item for i in recipes[0].ingredients] == ["cumin"]


def test_upsert_rejects_unknown_protein(session: Session) -> None:
    with pytest.raises(ValueError, match="protein_id"):
        upsert_recipe(session, recipe_data(protein_id=999))


def test_recipe_to_dict_round_trips_through_upsert(session: Session) -> None:
    upsert_recipe(session, recipe_data(name="Original"))
    session.commit()

    original = session.exec(select(Recipe).where(Recipe.name == "Original")).first()
    exported = recipe_to_dict(original)

    exported["name"] = "Copy"
    upsert_recipe(session, exported)
    session.commit()

    copy = session.exec(select(Recipe).where(Recipe.name == "Copy")).first()
    assert copy is not None
    assert copy.genre == original.genre
    assert [i.item for i in copy.ingredients] == [i.item for i in original.ingredients]
    assert [i.text for i in copy.instructions] == [i.text for i in original.instructions]
