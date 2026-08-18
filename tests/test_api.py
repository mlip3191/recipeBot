import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.seed import seed_proteins


@pytest.fixture()
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        seed_proteins(session)
    return test_engine


@pytest.fixture()
def client(engine):
    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def get_protein_id(client: TestClient, name: str) -> int:
    proteins = client.get("/api/proteins").json()
    return next(p["id"] for p in proteins if p["name"] == name)


def recipe_payload(protein_id: int, name: str = "Test Recipe", genre: str = "Test") -> dict:
    return {
        "name": name,
        "protein_id": protein_id,
        "genre": genre,
        "cook_time_min": 10,
        "total_time_min": 15,
        "servings": 2,
        "source": "Unit test",
        "notes": "Some notes",
        "ingredients": [
            {"item": "pepper", "quantity": "1", "unit": "tsp", "position": 2},
            {"item": "salt", "quantity": "1", "unit": "tsp", "position": 1},
        ],
        "instructions": [
            {"text": "Second step", "step_number": 2},
            {"text": "First step", "step_number": 1},
        ],
    }


def test_list_proteins(client: TestClient) -> None:
    response = client.get("/api/proteins")
    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert names == sorted(names)
    assert "Chicken" in names
    assert len(names) == 8


def test_create_and_get_recipe(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    payload = recipe_payload(chicken_id, name="Roast Chicken", genre="American")

    create_response = client.post("/api/recipes", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()

    assert created["name"] == "Roast Chicken"
    assert created["protein"]["name"] == "Chicken"
    assert [i["item"] for i in created["ingredients"]] == ["salt", "pepper"]
    assert [i["text"] for i in created["instructions"]] == ["First step", "Second step"]

    get_response = client.get(f"/api/recipes/{created['id']}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched == created


def test_get_recipe_not_found(client: TestClient) -> None:
    response = client.get("/api/recipes/9999")
    assert response.status_code == 404


def test_list_recipes_filters(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    beef_id = get_protein_id(client, "Beef")

    client.post(
        "/api/recipes",
        json=recipe_payload(chicken_id, name="Chicken Soup", genre="American"),
    )
    client.post(
        "/api/recipes",
        json=recipe_payload(beef_id, name="Beef Stew", genre="American"),
    )
    client.post(
        "/api/recipes",
        json=recipe_payload(chicken_id, name="Chicken Curry", genre="Indian"),
    )

    all_recipes = client.get("/api/recipes").json()
    assert len(all_recipes) == 3

    by_protein_name = client.get("/api/recipes", params={"protein": "Chicken"}).json()
    assert {r["name"] for r in by_protein_name} == {"Chicken Soup", "Chicken Curry"}

    by_protein_id = client.get("/api/recipes", params={"protein": str(beef_id)}).json()
    assert {r["name"] for r in by_protein_id} == {"Beef Stew"}

    by_genre = client.get("/api/recipes", params={"genre": "indian"}).json()
    assert {r["name"] for r in by_genre} == {"Chicken Curry"}

    by_both = client.get(
        "/api/recipes", params={"protein": "Chicken", "genre": "American"}
    ).json()
    assert {r["name"] for r in by_both} == {"Chicken Soup"}

    unknown_protein = client.get("/api/recipes", params={"protein": "Not A Protein"}).json()
    assert unknown_protein == []


def test_random_recipe_respects_filters(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    beef_id = get_protein_id(client, "Beef")

    client.post(
        "/api/recipes",
        json=recipe_payload(chicken_id, name="Chicken Curry", genre="Indian"),
    )
    client.post(
        "/api/recipes",
        json=recipe_payload(beef_id, name="Beef Stew", genre="American"),
    )

    for _ in range(5):
        response = client.get(
            "/api/recipes/random", params={"protein": "Chicken", "genre": "Indian"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Chicken Curry"
        assert body["protein"]["name"] == "Chicken"


def test_random_recipe_not_found(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    client.post(
        "/api/recipes",
        json=recipe_payload(chicken_id, name="Chicken Curry", genre="Indian"),
    )

    unmatched_genre = client.get(
        "/api/recipes/random", params={"protein": "Chicken", "genre": "Mexican"}
    )
    assert unmatched_genre.status_code == 404
    assert "detail" in unmatched_genre.json()

    unknown_protein = client.get(
        "/api/recipes/random", params={"protein": "Not A Protein"}
    )
    assert unknown_protein.status_code == 404

    empty_db_response = client.get("/api/recipes/random", params={"protein": "Beef"})
    assert empty_db_response.status_code == 404


def test_replace_recipe(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    beef_id = get_protein_id(client, "Beef")

    created = client.post(
        "/api/recipes", json=recipe_payload(chicken_id, name="Original", genre="American")
    ).json()

    updated_payload = recipe_payload(beef_id, name="Replaced", genre="Mexican")
    updated_payload["ingredients"] = [
        {"item": "cumin", "quantity": "1", "unit": "tsp", "position": 1},
    ]
    updated_payload["instructions"] = [
        {"text": "Only step", "step_number": 1},
    ]

    put_response = client.put(f"/api/recipes/{created['id']}", json=updated_payload)
    assert put_response.status_code == 200
    updated = put_response.json()

    assert updated["id"] == created["id"]
    assert updated["name"] == "Replaced"
    assert updated["protein"]["name"] == "Beef"
    assert [i["item"] for i in updated["ingredients"]] == ["cumin"]
    assert [i["text"] for i in updated["instructions"]] == ["Only step"]


def test_replace_recipe_not_found(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    response = client.put(
        "/api/recipes/9999", json=recipe_payload(chicken_id, name="Nope")
    )
    assert response.status_code == 404


def test_delete_recipe(client: TestClient) -> None:
    chicken_id = get_protein_id(client, "Chicken")
    created = client.post(
        "/api/recipes", json=recipe_payload(chicken_id, name="To Delete")
    ).json()

    delete_response = client.delete(f"/api/recipes/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/recipes/{created['id']}")
    assert get_response.status_code == 404


def test_delete_recipe_not_found(client: TestClient) -> None:
    response = client.delete("/api/recipes/9999")
    assert response.status_code == 404
