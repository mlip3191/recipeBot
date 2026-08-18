# recipeBot

Recipe Vault — a self-hosted recipe repository. Pick a protein (or "Any"), hit
Random, get a full recipe. Add, edit, delete, search, and bulk import/export
your own recipes. Single container, SQLite, no external services required.

## Running it

```sh
docker compose up -d --build
```

The `recipes` service does not publish a host port — it's only reachable
from other containers on the compose network (`expose: 8000`), by design, so
that the [Cloudflare Tunnel](#remote-access-via-cloudflare-tunnel) is the
only path in. For local-only access without a tunnel, either temporarily add
a `ports: ["8000:8000"]` mapping back to the `recipes` service, or reach it
via `docker compose exec recipes curl http://localhost:8000/health`.

Data lives in the `recipe_data` named Docker volume (mounted at `/data` in
the container) — it is untouched by `docker compose down`, container
recreation, or image rebuilds. The only way to lose it is
`docker compose down -v` (which explicitly deletes volumes) or manually
removing the volume.

Health check: `GET /health` (also wired into the container's Docker
`HEALTHCHECK`, polled every 30s).

## Environment variables

| Variable       | Default                          | Purpose                                                                 |
|----------------|-----------------------------------|--------------------------------------------------------------------------|
| `PORT`         | `8000`                            | Port uvicorn listens on inside the container. Not published to the host by default (see [Running it](#running-it)). Note: `expose: 8000` and the tunnel's public hostname target (`http://recipes:8000`) are hardcoded to `8000` in `docker-compose.yml` — if you override `PORT`, update those too. |
| `DATABASE_URL` | `sqlite:////data/recipes.db`      | SQLAlchemy/SQLModel database URL. The default is chosen automatically — `sqlite:////data/recipes.db` when `/data` exists (i.e. running in the container with the volume mounted), otherwise `sqlite:///./recipes.db` for local, non-Docker runs. Override only for non-default setups. |

Both can be set via a `.env` file next to `docker-compose.yml` (auto-loaded
by Docker Compose) or exported in your shell before `docker compose up`:

```sh
PORT=9090 docker compose up -d
```

## Remote access via Cloudflare Tunnel

The `cloudflared` service in `docker-compose.yml` exposes the app to the
internet through a [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
— no port forwarding or public IP needed. It connects outbound to
Cloudflare and routes traffic to the `recipes` service over the internal
compose network (`http://recipes:8000`), which is why `recipes` doesn't need
a published host port.

**One-time setup:**

1. In the [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/),
   go to **Networks → Tunnels** and create a new tunnel (choose the
   "Docker" connector type when prompted).
2. Add a **Public Hostname** for the tunnel pointing at service
   `http://recipes:8000` — this is the hostname you'll visit to reach the
   app (e.g. `recipes.yourdomain.com`).
3. Copy the tunnel token shown in the dashboard.
4. Copy `.env.example` to `.env` and paste the token in:

   ```sh
   cp .env.example .env
   ```

   ```env
   TUNNEL_TOKEN=your-token-here
   ```

   `.env` is gitignored — never commit it.
5. Start (or restart) the stack:

   ```sh
   docker compose up -d --build
   ```

The app is now reachable at the public hostname you configured in step 2.
`cloudflared` is set to `restart: unless-stopped` and depends on `recipes`
being up.

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
