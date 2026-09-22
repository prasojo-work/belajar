import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "crud_supabase.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
