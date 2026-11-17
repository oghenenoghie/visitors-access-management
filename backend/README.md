# Backend

Django 5.2, Django REST Framework, PostgreSQL, Simple JWT, Celery and Redis.

## Run locally

```bash
cp .env.example .env            # edit DJANGO_SECRET_KEY
python -m venv .venv && . .venv/bin/activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

Or with Docker from the repository root: `docker compose up --build` (development defaults are set in `docker-compose.yml`).

API base path `/api/v1/`. With `API_DOCS_ENABLED=true`: schema at `/api/v1/schema/`, Swagger UI at `/api/v1/docs/`.

## Checks (same as CI)

```bash
ruff check . && ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py spectacular --file /tmp/schema.yml --validate --fail-on-warn
pytest
```

Tests need PostgreSQL (`DATABASE_URL`, default `postgres://estate:estate@localhost:5432/estate_access`).

## Layout

- `config/` settings (`base`, `test`), URLs, Celery.
- `apps/common/` base model, estate scoping, error envelope, health endpoint.
- `apps/users/` custom user (email login, UUID, Argon2).
- `apps/estates/` estates and estate-scoped memberships.

Estate isolation: query estate-owned models through `.for_user(request.user)`.
