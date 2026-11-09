"""
Entry point untuk Streamlit Community Cloud.

Di Streamlit Cloud, isi "Main file path" dengan:
    streamlit_app.py

File ini menjalankan aplikasi asli di src/eduscope_id/app.py tanpa
menduplikasi kode. Dengan begini, dependency tetap dibaca dari uv.lock
di root repository.
"""

from __future__ import annotations

import runpy
from pathlib import Path

APP_PATH = Path(__file__).resolve().parent / "src" / "eduscope_id" / "app.py"

runpy.run_path(str(APP_PATH), run_name="__main__")
