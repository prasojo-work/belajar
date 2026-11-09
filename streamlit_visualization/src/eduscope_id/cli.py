"""Entry point CLI untuk menjalankan dasbor Streamlit."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Jalankan aplikasi Streamlit yang dibundel di dalam package."""
    from streamlit.web import cli as stcli

    app_path = Path(__file__).with_name("app.py")
    sys.argv = ["streamlit", "run", str(app_path), *sys.argv[1:]]
    raise SystemExit(stcli.main())
