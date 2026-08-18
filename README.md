# recipeBot

Recipe Vault — a self-hosted recipe repository. Pick a protein (or "Any"), hit
Random, get a full recipe. Add, edit, delete, search, and bulk import/export
your own recipes. Single container, SQLite, no external services required.

## Running it

```sh
docker compose up -d --build
```

The app is served at [http://localhost:8000](http://localhost:8000). Data
lives in the `recipe_data` named Docker volume (mounted at `/data` in the
container) — it is untouched by `docker compose down`, container recreation,
or image rebuilds. The only way to lose it is `docker compose down -v`
(which explicitly deletes volumes) or manually removing the volume.

Health check: `GET /health` (also wired into the container's Docker
`HEALTHCHECK`, polled every 30s).

## Environment variables

| Variable       | Default                          | Purpose                                                                 |
|----------------|-----------------------------------|--------------------------------------------------------------------------|
| `PORT`         | `8000`                            | Port uvicorn listens on inside the container, and the host port `docker compose` publishes it on (both driven off the same value). |
| `DATABASE_URL` | `sqlite:////data/recipes.db`      | SQLAlchemy/SQLModel database URL. The default is chosen automatically — `sqlite:////data/recipes.db` when `/data` exists (i.e. running in the container with the volume mounted), otherwise `sqlite:///./recipes.db` for local, non-Docker runs. Override only for non-default setups. |

Both can be set via a `.env` file next to `docker-compose.yml` (auto-loaded
by Docker Compose) or exported in your shell before `docker compose up`:

```sh
PORT=9090 docker compose up -d
```

## Import / export

Recipes can be exported to / imported from a JSON file (see
`docs/recipe-schema.json` for the format — an array of recipe objects, each
with nested `ingredients` and `instructions`). Imports upsert by recipe name,
so re-running an import is safe and won't create duplicates.

The `./backups` folder on the host is mounted into the container at
`/backups`, so anything written there is visible on both sides.

**With `make`:**

```sh
make import                              # imports docs/recipe-schema.json (bundled example)
make import FILE=backups/my-backup.json  # import a specific file
make export                              # writes ./backups/recipes-export.json
make export OUT=/backups/2026-08-18.json # export to a specific path
```

**Without `make`**, run the same commands directly:

```sh
docker compose exec -T recipes python scripts/import_recipes.py docs/recipe-schema.json
docker compose exec -T recipes python scripts/export_recipes.py /backups/recipes-export.json
```

`FILE`/import paths are resolved *inside the container* — either a path
baked into the image (like `docs/recipe-schema.json`) or a path under
`/backups` (which maps to `./backups` on the host).

## Backing up

A manual backup is just an export (see above) — it writes a complete JSON
snapshot of every recipe to `./backups`, which lives on the host and
survives container/image changes independently of the `recipe_data` volume.

For automated nightly backups, the simplest approach is a host crontab entry
that runs the export script with a timestamped filename. No extra services
or containers needed — it reuses the same `docker compose exec` command from
above:

```sh
crontab -e
```

Add a line like this (adjust the path to wherever this repo lives on the
host; runs nightly at 2am):

```cron
0 2 * * * cd /path/to/recipeBot && docker compose exec -T recipes python scripts/export_recipes.py "/backups/recipes-$(date +\%Y-\%m-\%d).json" >> ./backups/backup.log 2>&1
```

Note the escaped `\%` — cron treats unescaped `%` as a newline in the
command. Backups accumulate in `./backups/` on the host; prune old ones
periodically (e.g. `find ./backups -name 'recipes-*.json' -mtime +30 -delete`
added as its own cron line) if disk space matters.

## Updating

```sh
git pull
docker compose up -d --build
```

This rebuilds the image with the latest code and recreates the container.
The `recipe_data` volume (your actual recipes) is untouched — only the
application code changes.

## Development

- Stack: Python 3.12, FastAPI, SQLModel, SQLite, Jinja2 + vanilla JS, pytest,
  `uv` (falls back to `pip` + `requirements.txt`)
- Run tests: `docker compose exec -T recipes python -m pytest -v` (or build
  the image and `docker run --rm -v "$(pwd)/tests:/app/tests" <image> python -m pytest -v`)
- See `CLAUDE.md` for the data model and code conventions.
