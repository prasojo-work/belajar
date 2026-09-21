# hello-fastapi

Minimal "Hello World" API built with [FastAPI](https://fastapi.tiangolo.com/)
and [uv](https://docs.astral.sh/uv/), ready to run in the cloud.

## Features

- `GET /` -> `{"message": "Hello World"}` (rate limited to **10 requests/second** per client IP)
- `GET /health` -> `{"status": "ok"}` (excluded from rate limiting so cloud health checks always pass)
- Rate limiting via [slowapi](https://github.com/laurentS/slowapi)

## Run locally

```bash
uv run uvicorn hello_fastapi.app:app --reload
```

Or via the project script:

```bash
uv run hello-fastapi
```

Then open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs.

## Test the rate limit

```bash
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
done
```

You should see `200` for the first 10 requests and `429` after that.

## Run with Docker

```bash
docker build -t hello-fastapi .
docker run -p 8000:8000 hello-fastapi
```

The container reads the `PORT` environment variable (default `8000`), so it works
on most cloud platforms (Render, Railway, Fly.io, Google Cloud Run, etc.).

## Run with Docker Compose

```bash
docker compose up -d --build
```

The service exposes the API on http://127.0.0.1:8000 and has a built-in
health check that polls `GET /health`. To stop it:

```bash
docker compose down
```
