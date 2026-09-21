from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Hello FastAPI", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
@limiter.limit("10/second")
def read_root(request: Request):
    return {"message": "Hello World"}


@app.get("/health")
def health():
    return {"status": "ok"}
