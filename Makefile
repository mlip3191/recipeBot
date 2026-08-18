FILE ?= docs/recipe-schema.json
OUT ?= /backups/recipes-export.json

.PHONY: import export

import:
	docker compose exec -T recipes python scripts/import_recipes.py $(FILE)

export:
	docker compose exec -T recipes python scripts/export_recipes.py $(OUT)
