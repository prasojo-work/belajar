# crud-supabase

A small CRUD API that connects FastAPI to Postgres (built for Supabase),
managed with [uv](https://docs.astral.sh/uv/). No frontend — use the
interactive docs at `/docs`.

## Stack

- FastAPI + uvicorn
- SQLAlchemy 2.0 (ORM) over psycopg 3
- pydantic-settings for configuration
- slowapi for rate limiting (10 requests/second)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/items` | Create an item |
| GET    | `/items` | List items |
| GET    | `/items/{id}` | Get one item |
| PUT    | `/items/{id}` | Update an item |
| DELETE | `/items/{id}` | Delete an item |
| GET    | `/health` | Health check (not rate limited) |
| GET    | `/docs` | Swagger UI |

## Configuration

All configuration comes from environment variables (see `.env.example`).
Copy it and adjust:

```bash
cp .env.example .env
```

`DATABASE_URL` is a **secret** (it contains the DB password). `.env` is
git-ignored; never commit it.

## Run locally

`DATABASE_URL` is required, so create your `.env` first (see Configuration):

```bash
cp .env.example .env
docker compose up -d db
uv run uvicorn crud_supabase.app:app --reload
```

Open http://127.0.0.1:8000/docs.

To run the whole stack in containers instead:

```bash
docker compose up --build
```

## Connecting to Supabase

Use the **direct Postgres connection string**, not the REST/API-key path.
Prefer the connection pooler host:

- **Session pooler** (port `5432`) — recommended for a long-running backend.
- **Transaction pooler** (port `6543`) — also works, but you must disable
  prepared statements, because the transaction pooler doesn't support them.
  With psycopg 3 + SQLAlchemy, pass `connect_args={"prepare_threshold": None}`
  to `create_engine`.

Keep `sslmode=require` in the URL.

## Security notes (deliberately applied)

- Secrets live in environment variables, never in the repo or the image.
- Input is validated and bounded by Pydantic schemas.
- All DB access goes through the SQLAlchemy ORM (parameterized queries, no
  string-built SQL).
- Each item endpoint is rate limited to 10 requests/second.
- `--proxy-headers` is enabled so rate limiting and logs see the real client IP.

## Roadmap

- [ ] API-key authentication (hashing, scopes, revocation)
- [ ] Alembic migrations instead of `create_all` on startup
- [ ] Automated tests
