from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Recipe Vault" in response.text


def test_recipes_list_page() -> None:
    response = client.get("/recipes")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="recipes-table"' in response.text


def test_recipe_new_page() -> None:
    response = client.get("/recipes/new")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="recipe-form"' in response.text
    assert 'data-recipe-id=""' in response.text


def test_recipe_edit_page() -> None:
    response = client.get("/recipes/42/edit")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'data-recipe-id="42"' in response.text
