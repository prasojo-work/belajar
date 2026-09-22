# fastapi-cloud

A minimal FastAPI "Hello World", laid out to deploy on
[FastAPI Cloud](https://fastapicloud.com/). No database, no auth — just the
smallest possible starting point.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Returns `{"message": "Hello World"}` |
| GET | `/docs` | Interactive API docs (Swagger UI) |

## Layout

This project uses the **src layout**:

```
fastapi_cloud/
├── src/fastapi_cloud/
│   ├── app.py        # the FastAPI `app` object
│   └── __init__.py
├── pyproject.toml
└── ...
```

Because the app lives in `src/fastapi_cloud/app.py` — not in a root-level
`main.py`/`app.py`, which are the only files FastAPI Cloud auto-detects — the
entrypoint is declared explicitly in `pyproject.toml`:

```toml
[tool.fastapi]
entrypoint = "fastapi_cloud.app:app"
```

## Run locally

```bash
uv run fastapi dev
```

Then open http://127.0.0.1:8000 for the greeting, and
http://127.0.0.1:8000/docs for the interactive docs.

`fastapi dev` is run **without a path** on purpose: if it starts, the entrypoint
is configured correctly and `fastapi deploy` will work too.

## Deploy

```bash
uv run fastapi deploy
```

The first run opens your browser to log in, then asks you to pick a team and to
create (or link) an app. When it finishes you get a public URL at
`https://<app-name>.fastapicloud.dev`.

Notes:

- Pick a URL-friendly app name (lowercase, hyphens) — it becomes the subdomain.
- Packaging respects `.gitignore`, so `.venv` is not uploaded.
- After the first deploy, a `.fastapicloud/` directory links this local project
  to the cloud deployment. To ship updates, just run `uv run fastapi deploy`
  again from the same directory.

The CLI comes from the `fastapi[standard]` dependency already listed in
`pyproject.toml`, so no extra install is needed.


## Unlink

```bash
uv run fastapi cloud unlink
```
