from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .db import engine
from .limiter import limiter
from .models import Base
from .routers import employees, items


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="crud-supabase", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(items.router)
app.include_router(employees.router)


@app.get("/", tags=["root"])
def root():
    return {"message": "crud-supabase API", "docs": "/docs"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
