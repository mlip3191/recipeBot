# recipeBot

A self-hosted recipe repository web app.

## Stack

- Python 3.12
- FastAPI (backend + serves frontend, single app)
- SQLModel (ORM/schema)
- SQLite — DB file at `/data/recipes.db`, mounted as a Docker volume
- Jinja2 templates + vanilla JS for the frontend
- Single Docker container: `Dockerfile` + `docker-compose.yml`
- Tests: pytest
- Package management: `uv` (fall back to `pip` + `requirements.txt` if `uv` isn't available)

## Data model

- **recipes**: id, name, protein_id (FK), genre, cook_time_min, total_time_min, servings, source, notes, created_at
- **proteins**: id, name (lookup table)
- **ingredients**: id, recipe_id, position, quantity, unit, item, prep_note
- **instructions**: id, recipe_id, step_number, text

## Core user flow

Open the site, pick a protein from a dropdown (or "Any"), click Random, see one full recipe (name, times, genre, ingredients, instructions).

Secondary flows: add/edit/delete recipes via a form, bulk import from JSON.

## Conventions

- Keep it simple, no ORM magic beyond SQLModel
- One module per concern: `models.py`, `db.py`, `routers/`, `templates/`, `static/`
- Type hints everywhere
- Black formatting
- Always run tests and show output before declaring a step done
- Commit after each completed step with a clear message
