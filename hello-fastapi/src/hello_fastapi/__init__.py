import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "hello_fastapi.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
