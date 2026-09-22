FROM python:3.13-slim

# Install uv (dependency manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8000
EXPOSE 8000

# --proxy-headers lets uvicorn trust the platform proxy, so request.client.host
# is the real visitor IP (needed for per-IP rate limiting and correct logging).
CMD ["sh", "-c", "uvicorn crud_supabase.app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
