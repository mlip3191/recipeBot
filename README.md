# recipeBot

## Backup & restore

Recipes can be exported to / imported from a JSON file (see `docs/recipe-schema.json`
for the format — an array of recipe objects, each with nested `ingredients` and
`instructions`). Imports upsert by recipe name, so re-running an import is safe.

The `./backups` folder on the host is mounted into the container at `/backups`,
so anything written there is visible on both sides.

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

`FILE`/import paths are resolved *inside the container* — either a path baked into
the image (like `docs/recipe-schema.json`) or a path under `/backups` (which maps to
`./backups` on the host).
