"""
Dasbor Pendidikan Indonesia
===========================
Visualisasi interaktif tiga dataset pendidikan:
1. Angka Partisipasi Sekolah (APS) menurut provinsi & kelompok umur, 2025
2. Tingkat Penyelesaian Pendidikan menurut jenjang & provinsi, 2023
3. Jumlah Pendidik & Tenaga Kependidikan menurut jenjang & jenis kelamin, 2025

Jalankan dengan:
    uv run eduscope-id
atau:
    uv run streamlit run src/eduscope_id/app.py
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.colors import sample_colorscale

# =============================================================================
# KONFIGURASI HALAMAN & TEMA
# =============================================================================
st.set_page_config(
    page_title="Dasbor Pendidikan Indonesia",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parents[1]
DATA_DIR = PROJECT_ROOT / "data"

BLUE = "#2563EB"
CYAN = "#0EA5E9"
AMBER = "#F59E0B"
TEAL = "#0D9488"
PINK = "#EC4899"
PURPLE = "#7C3AED"
DARK = "#0F172A"
SLATE = "#64748B"
MUTED = "#94A3B8"
BORDER = "#E6EBF3"

AGE_ORDER = ["7-12", "13-15", "16-18", "19-23"]
AGE_DISPLAY = {
    "7-12": "7–12 th",
    "13-15": "13–15 th",
    "16-18": "16–18 th",
    "19-23": "19–23 th",
}
AGE_COLORS = {
    "7-12": "#93C5FD",
    "13-15": "#60A5FA",
    "16-18": "#3B82F6",
    "19-23": "#1D4ED8",
}
LEVELS = ["SD", "SMP", "SMA"]
LEVEL_DISPLAY = {"SD": "SD", "SMP": "SMP", "SMA": "SMA"}
LEVEL_COLORS = {"SD": "#0EA5E9", "SMP": "#6366F1", "SMA": "#F59E0B"}

TEACHER_LEVELS = ["TK", "KB", "TPA", "SPS", "SD", "SMP", "SMA", "SMK", "SLB"]
GENDER_COLORS = {"Laki-laki": "#2563EB", "Perempuan": "#EC4899"}

MAP_INDICATORS = {
    "APS 7–12 th (2025)": {
        "col": "7-12", "kind": "pct", "source": "aps",
        "label": "APS 7–12 th", "short": "APS", "scale": "blue",
    },
    "APS 13–15 th (2025)": {
        "col": "13-15", "kind": "pct", "source": "aps",
        "label": "APS 13–15 th", "short": "APS", "scale": "blue",
    },
    "APS 16–18 th (2025)": {
        "col": "16-18", "kind": "pct", "source": "aps",
        "label": "APS 16–18 th", "short": "APS", "scale": "blue",
    },
    "APS 19–23 th (2025)": {
        "col": "19-23", "kind": "pct", "source": "aps",
        "label": "APS 19–23 th", "short": "APS", "scale": "blue",
    },
    "Penyelesaian SD (2023)": {
        "col": "SD", "kind": "pct", "source": "comp",
        "label": "Penyelesaian SD", "short": "Penyelesaian", "scale": "teal",
    },
    "Penyelesaian SMP (2023)": {
        "col": "SMP", "kind": "pct", "source": "comp",
        "label": "Penyelesaian SMP", "short": "Penyelesaian", "scale": "teal",
    },
    "Penyelesaian SMA (2023)": {
        "col": "SMA", "kind": "pct", "source": "comp",
        "label": "Penyelesaian SMA", "short": "Penyelesaian", "scale": "teal",
    },
    "Total pendidik (2025)": {
        "col": "Total Pendidik", "kind": "count", "source": "teacher",
        "label": "Total pendidik", "short": "Pendidik", "scale": "purple",
    },
    "Proporsi pendidik perempuan (2025)": {
        "col": "% Pendidik Perempuan", "kind": "share", "source": "teacher",
        "label": "Proporsi pendidik perempuan", "short": "Perempuan", "scale": "diverging",
    },
}

MAP_SCALES = {
    "blue": [[0, "#EFF6FF"], [0.25, "#BFDBFE"], [0.5, "#60A5FA"], [0.75, "#2563EB"], [1, "#1E3A8A"]],
    "teal": [[0, "#FFFBEB"], [0.25, "#FDE68A"], [0.55, "#99F6E4"], [0.8, "#2DD4BF"], [1, "#0F766E"]],
    "purple": [[0, "#F5F3FF"], [0.3, "#C4B5FD"], [0.6, "#8B5CF6"], [0.8, "#6D28D9"], [1, "#4C1D95"]],
    "diverging": [[0, "#2563EB"], [0.25, "#93C5FD"], [0.5, "#F8FAFC"], [0.75, "#F9A8D4"], [1, "#BE185D"]],
}

BLUE_SCALE = ["#DBEAFE", "#93C5FD", "#60A5FA", "#2563EB", "#1E3A8A"]
TEAL_SCALE = ["#CCFBF1", "#5EEAD4", "#14B8A6", "#0F766E", "#134E4A"]
AMBER_SCALE = ["#FEF3C7", "#FCD34D", "#F59E0B", "#D97706", "#92400E"]
MIXED_SCALE = ["#BFDBFE", "#E2E8F0", "#FBCFE8", "#EC4899"]
PURPLE_SCALE = ["#EDE9FE", "#C4B5FD", "#8B5CF6", "#6D28D9", "#4C1D95"]

REGION_ORDER = [
    "Sumatera",
    "Jawa",
    "Bali & Nusa Tenggara",
    "Kalimantan",
    "Sulawesi",
    "Maluku",
    "Papua",
]
REGION_COLORS = {
    "Sumatera": "#2563EB",
    "Jawa": "#7C3AED",
    "Bali & Nusa Tenggara": "#0EA5E9",
    "Kalimantan": "#059669",
    "Sulawesi": "#F59E0B",
    "Maluku": "#EC4899",
    "Papua": "#EF4444",
}

REGION_MEMBERS = {
    "Sumatera": [
        "ACEH", "SUMATERA UTARA", "SUMATERA BARAT", "RIAU", "JAMBI",
        "SUMATERA SELATAN", "BENGKULU", "LAMPUNG", "KEP. BANGKA BELITUNG",
        "KEP. RIAU",
    ],
    "Jawa": ["DKI JAKARTA", "JAWA BARAT", "JAWA TENGAH", "DI YOGYAKARTA", "JAWA TIMUR", "BANTEN"],
    "Bali & Nusa Tenggara": ["BALI", "NUSA TENGGARA BARAT", "NUSA TENGGARA TIMUR"],
    "Kalimantan": [
        "KALIMANTAN BARAT", "KALIMANTAN TENGAH", "KALIMANTAN SELATAN",
        "KALIMANTAN TIMUR", "KALIMANTAN UTARA",
    ],
    "Sulawesi": [
        "SULAWESI UTARA", "SULAWESI TENGAH", "SULAWESI SELATAN",
        "SULAWESI TENGGARA", "GORONTALO", "SULAWESI BARAT",
    ],
    "Maluku": ["MALUKU", "MALUKU UTARA"],
    "Papua": [
        "PAPUA BARAT", "PAPUA BARAT DAYA", "PAPUA", "PAPUA SELATAN",
        "PAPUA TENGAH", "PAPUA PEGUNUNGAN",
    ],
}
PROVINCE_REGION = {p: r for r, provs in REGION_MEMBERS.items() for p in provs}

ALIASES = {
    "D.K.I. JAKARTA": "DKI JAKARTA",
    "D.K.I JAKARTA": "DKI JAKARTA",
    "DKI JAKARTA": "DKI JAKARTA",
    "D.I. YOGYAKARTA": "DI YOGYAKARTA",
    "D.I YOGYAKARTA": "DI YOGYAKARTA",
    "DI YOGYAKARTA": "DI YOGYAKARTA",
    "DAERAH ISTIMEWA YOGYAKARTA": "DI YOGYAKARTA",
    "KEPULAUAN BANGKA BELITUNG": "KEP. BANGKA BELITUNG",
    "KEP. BANGKA BELITUNG": "KEP. BANGKA BELITUNG",
    "BANGKA BELITUNG": "KEP. BANGKA BELITUNG",
    "KEPULAUAN RIAU": "KEP. RIAU",
    "KEP. RIAU": "KEP. RIAU",
    "INDONESIA": "INDONESIA",
}
DISPLAY = {
    "DKI JAKARTA": "DKI Jakarta",
    "DI YOGYAKARTA": "DI Yogyakarta",
    "KEP. BANGKA BELITUNG": "Kep. Bangka Belitung",
    "KEP. RIAU": "Kep. Riau",
}

PLOT_FONT = "'Source Sans', 'Segoe UI', system-ui, -apple-system, sans-serif"

# =============================================================================
# UTILITAS
# =============================================================================
def canon_province(value) -> str:
    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return ALIASES.get(text, text)


def prov_name(key: str) -> str:
    if key in DISPLAY:
        return DISPLAY[key]
    if key == "INDONESIA":
        return "Indonesia"
    return key.title()


def fmt_pct(value, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "–"
    return f"{value:.{digits}f}".replace(".", ",") + "%"


def fmt_num(value, digits: int = 0) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "–"
    text = f"{value:,.{digits}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_short(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "–"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}".replace(".", ",") + " jt"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}".replace(".", ",") + " rb"
    return fmt_num(value)


def find_file(*patterns: str) -> Path:
    """Cari file data di folder data/, root project, atau direktori kerja."""
    search_dirs: list[Path] = []
    env_dir = os.environ.get("EDUSCOPE_DATA_DIR")
    if env_dir:
        search_dirs.append(Path(env_dir).expanduser())
    search_dirs += [DATA_DIR, PROJECT_ROOT, Path.cwd() / "data", Path.cwd()]

    checked: set[Path] = set()
    for directory in search_dirs:
        if directory in checked or not directory.is_dir():
            continue
        checked.add(directory)
        for pattern in patterns:
            matches = sorted(directory.glob(pattern))
            if matches:
                return matches[0]

    locations = ", ".join(str(d) for d in checked)
    raise FileNotFoundError(
        f"File data dengan pola {patterns} tidak ditemukan. Lokasi yang dicek: {locations}"
    )


# =============================================================================
# PEMUATAN & PEMBERSIHAN DATA
# =============================================================================
@st.cache_data(show_spinner="Memuat dan menyiapkan data…")
def load_data():
    aps_path = find_file("aps_2025.xlsx", "Angka Partisipasi Sekolah*.xlsx")
    comp_path = find_file("penyelesaian_2023.xlsx", "Tingkat Penyelesaian Pendidikan*.xlsx")
    teacher_path = find_file("pendidik_2025.xls", "Jumlah Pendidik Dan Tenaga Pendidik*.xls")
    geo_path = find_file("indonesia_provinces.geojson", "indonesia-38-provinces.geojson")

    # ---------- 1) APS ----------
    raw = pd.read_excel(aps_path, header=None, engine="openpyxl")
    age_labels = [str(v).strip() for v in raw.iloc[2, 1:5].tolist()]
    rows = raw.iloc[4:43].copy()
    rows = rows[rows[0].notna()].copy()
    rows = rows[rows[0].astype(str).str.strip() != ""]
    rows = rows.iloc[:, [0, 1, 2, 3, 4]]
    rows.columns = ["provinsi", *age_labels]
    rows["provinsi"] = rows["provinsi"].map(canon_province)
    for label in age_labels:
        rows[label] = pd.to_numeric(rows[label], errors="coerce")
    aps_nat = rows[rows["provinsi"] == "INDONESIA"].iloc[0]
    aps = rows[rows["provinsi"] != "INDONESIA"].copy()
    aps_nat_values = {label: float(aps_nat[label]) for label in age_labels}

    # ---------- 2) Tingkat Penyelesaian ----------
    raw = pd.read_excel(comp_path, header=None, engine="openpyxl")
    level_labels = [str(v).strip() for v in raw.iloc[2, 1:4].tolist()]
    level_labels = [re.split(r"\s*/\s*", v)[0].strip().upper() for v in level_labels]
    rows = raw.iloc[4:43].copy()
    rows = rows[rows[0].notna()].copy()
    rows = rows[rows[0].astype(str).str.strip() != ""]
    rows = rows.iloc[:, [0, 1, 2, 3]]
    rows.columns = ["provinsi", *level_labels]
    rows["provinsi"] = rows["provinsi"].map(canon_province)
    for label in level_labels:
        rows[label] = pd.to_numeric(rows[label], errors="coerce")
    comp_nat = rows[rows["provinsi"] == "INDONESIA"].iloc[0]
    comp = rows[rows["provinsi"] != "INDONESIA"].copy()
    comp_nat_values = {label: float(comp_nat[label]) for label in level_labels}

    # ---------- 3) Pendidik ----------
    raw = pd.read_excel(teacher_path, header=None, engine="xlrd")
    level_header = raw.iloc[3].ffill()
    gender_header = raw.iloc[4]
    records = []
    for i in range(5, 44):
        prov = raw.iat[i, 0]
        if pd.isna(prov) or str(prov).strip() == "":
            continue
        prov_key = canon_province(prov)
        for col in range(1, 19):
            level = str(level_header.iat[col]).split(" ")[0].strip().upper()
            gender_raw = str(gender_header.iat[col]).upper()
            gender = "Laki-laki" if "LAKI" in gender_raw else "Perempuan"
            value = pd.to_numeric(raw.iat[i, col], errors="coerce")
            records.append((prov_key, level, gender, float(value) if pd.notna(value) else np.nan))
    tch_all = pd.DataFrame(records, columns=["provinsi", "jenjang", "gender", "jumlah"])
    tch_nat = tch_all[tch_all["provinsi"] == "INDONESIA"].copy()
    tch = tch_all[tch_all["provinsi"] != "INDONESIA"].copy()
    tch["region"] = tch["provinsi"].map(PROVINCE_REGION)

    # ---------- Gabungan ----------
    base = pd.DataFrame({"provinsi": aps["provinsi"].tolist()})
    base["Provinsi"] = base["provinsi"].map(prov_name)
    base["region"] = base["provinsi"].map(PROVINCE_REGION).fillna("Lainnya")

    aps_clean = aps.rename(columns={"provinsi": "provinsi"})
    comp_clean = comp.rename(columns={"provinsi": "provinsi"})

    teacher_total = tch.groupby("provinsi")["jumlah"].sum().rename("Total Pendidik")
    teacher_female = (
        tch[tch["gender"] == "Perempuan"].groupby("provinsi")["jumlah"].sum().rename("Pendidik Perempuan")
    )
    teacher_male = (
        tch[tch["gender"] == "Laki-laki"].groupby("provinsi")["jumlah"].sum().rename("Pendidik Laki-laki")
    )

    master = (
        base.merge(aps_clean[["provinsi", *AGE_ORDER]], on="provinsi", how="left")
        .merge(comp_clean[["provinsi", *LEVELS]], on="provinsi", how="left")
        .merge(teacher_total, on="provinsi", how="left")
        .merge(teacher_female, on="provinsi", how="left")
        .merge(teacher_male, on="provinsi", how="left")
    )
    master["% Pendidik Perempuan"] = master["Pendidik Perempuan"] / master["Total Pendidik"] * 100

    teacher_wide = (
        tch.pivot_table(index="provinsi", columns="jenjang", values="jumlah", aggfunc="sum")
        .reindex(columns=TEACHER_LEVELS)
        .fillna(0)
    )

    # ---------- 4) Batas wilayah provinsi ----------
    geojson = json.loads(geo_path.read_text(encoding="utf-8"))
    for feature in geojson["features"]:
        raw_name = feature["properties"].get("PROVINSI", "")
        feature["properties"]["PROV_CANON"] = canon_province(raw_name)

    return {
        "master": master,
        "geojson": geojson,
        "aps_nat": aps_nat_values,
        "comp_nat": comp_nat_values,
        "tch": tch,
        "tch_all": tch_all,
        "tch_nat": tch_nat,
        "teacher_wide": teacher_wide,
        "files": {
            "aps": aps_path.name,
            "comp": comp_path.name,
            "teacher": teacher_path.name,
            "geo": geo_path.name,
        },
    }


DATA = load_data()
MASTER = DATA["master"]
APS_NAT = DATA["aps_nat"]
COMP_NAT = DATA["comp_nat"]
TCH = DATA["tch"]
TCH_NAT = DATA["tch_nat"]
TEACHER_WIDE = DATA["teacher_wide"]
GEOJSON = DATA["geojson"]

# =============================================================================
# GAYA & KOMPONEN UI
# =============================================================================
CSS = """
<style>
html, body, .stApp {
    font-family: 'Source Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
}
[data-testid="stHeader"], header[data-testid="stHeader"] {
    background: transparent !important;
}
.stApp {
    background:
        radial-gradient(900px 420px at 8% -8%, rgba(37,99,235,.075), transparent 60%),
        radial-gradient(800px 400px at 96% 2%, rgba(14,165,233,.06), transparent 55%),
        #F5F7FB;
}
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 4rem;
    max-width: 1440px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A1120 0%, #101C31 100%);
    border-right: 1px solid rgba(148,163,184,.16);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.4rem; }
[data-testid="stSidebar"] * { color: #CBD5E1; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #fff; }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #8FA3BF !important;
}
[data-testid="stSidebar"] [role="radiogroup"] { gap: 5px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 9px 12px;
    border-radius: 11px;
    border: 1px solid transparent;
    transition: all .15s ease;
    cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(59,130,246,.13);
    border-color: rgba(96,165,250,.22);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(37,99,235,.92), rgba(14,165,233,.62));
    border-color: rgba(147,197,253,.48);
    box-shadow: 0 6px 18px rgba(2,6,23,.38);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {
    color: #ffffff !important;
    font-weight: 600;
}
[data-testid="stSidebar"] [role="radiogroup"] label p { font-size: .9rem; }
[data-testid="stSidebar"] hr { border-color: rgba(148,163,184,.18); }

.brand {
    display: flex; align-items: center; gap: 11px;
    padding: 0 6px 18px 6px;
}
.brand-mark {
    width: 42px; height: 42px; border-radius: 13px;
    display: grid; place-items: center; font-size: 1.25rem;
    background: linear-gradient(135deg, #2563EB, #0EA5E9);
    box-shadow: 0 8px 20px rgba(37,99,235,.35);
}
.brand-name { color: #fff; font-weight: 800; font-size: 1.08rem; letter-spacing: -.02em; }
.brand-sub { color: #8FA3BF; font-size: .72rem; margin-top: 1px; }

.side-note {
    background: rgba(148,163,184,.08);
    border: 1px solid rgba(148,163,184,.14);
    border-radius: 13px;
    padding: 12px 13px;
    font-size: .76rem;
    line-height: 1.6;
    color: #9FB2CB !important;
}
.side-note b { color: #E2E8F0; }
.side-dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:6px; }

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    border-radius: 22px;
    padding: 30px 34px 28px;
    margin-bottom: 18px;
    background: linear-gradient(115deg, #0A1120 0%, #122743 52%, #1D4ED8 145%);
    box-shadow: 0 22px 55px -24px rgba(15,23,42,.6);
    color: #fff;
}
.hero.compact { padding: 22px 28px 20px; border-radius: 19px; }
.hero::after {
    content: "";
    position: absolute;
    width: 340px; height: 340px; right: -90px; top: -170px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(56,189,248,.38), transparent 66%);
    pointer-events: none;
}
.hero::before {
    content: "";
    position: absolute;
    width: 220px; height: 220px; right: 160px; bottom: -160px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(236,72,153,.18), transparent 68%);
    pointer-events: none;
}
.hero .eyebrow {
    font-size: .72rem; font-weight: 700; letter-spacing: .13em;
    text-transform: uppercase; color: #7DD3FC; margin-bottom: 9px;
}
.hero h1 {
    font-size: 2rem; line-height: 1.18; font-weight: 800;
    letter-spacing: -.035em; margin: 0 0 9px 0; color: #fff;
}
.hero.compact h1 { font-size: 1.55rem; margin-bottom: 7px; }
.hero p {
    font-size: .9rem; line-height: 1.6; color: #C7D5E8;
    margin: 0; max-width: 880px;
}
.hero .chips { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 16px; }
.hero .chip {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 10px; border-radius: 999px;
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.14);
    color: #DBEAFE; font-size: .71rem; font-weight: 600;
    backdrop-filter: blur(4px);
}
.hero.compact .chips { margin-top: 12px; }

/* KPI */
.kpi {
    position: relative;
    height: 100%;
    background: #ffffff;
    border: 1px solid #E6EBF3;
    border-radius: 16px;
    padding: 17px 17px 15px;
    box-shadow: 0 5px 20px rgba(15,23,42,.045);
    overflow: hidden;
}
.kpi::before {
    content: "";
    position: absolute; inset: 0 0 auto 0; height: 3px;
    background: var(--accent, #2563EB);
}
.kpi-top {
    display: flex; align-items: center; gap: 8px;
    color: #6B7C93; font-size: .71rem; font-weight: 700;
    letter-spacing: .045em; text-transform: uppercase;
}
.kpi-icon {
    width: 27px; height: 27px; border-radius: 9px;
    display: grid; place-items: center; font-size: .86rem;
    background: color-mix(in srgb, var(--accent, #2563EB) 12%, white);
}
.kpi-value {
    font-size: 1.78rem; font-weight: 800; color: #0F172A;
    line-height: 1.15; margin-top: 10px; letter-spacing: -.03em;
}
.kpi-note { font-size: .755rem; color: #64748B; margin-top: 6px; line-height: 1.45; }
.kpi-note b { color: #334155; }

/* Section heading */
.sec { display: flex; align-items: center; gap: 11px; margin: 20px 0 7px; }
.sec-icon {
    width: 37px; height: 37px; border-radius: 12px;
    display: grid; place-items: center; font-size: 1.02rem;
    background: #EFF6FF; color: #2563EB;
    border: 1px solid #DBEAFE;
}
.sec-title { font-weight: 750; color: #0F172A; font-size: 1.01rem; letter-spacing: -.01em; }
.sec-sub { color: #64748B; font-size: .775rem; margin-top: 1px; }

/* Callouts */
.callout {
    border-radius: 14px; padding: 13px 16px; margin: 10px 0;
    font-size: .855rem; line-height: 1.6;
}
.callout b, .callout strong { font-weight: 700; }
.callout.info { background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E3A8A; }
.callout.warn { background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; }
.callout.good { background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; }
.callout.rose { background: #FFF1F2; border: 1px solid #FECDD3; color: #9F1239; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 5px; background: #EDF1F7; padding: 5px;
    border-radius: 12px; width: fit-content;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px; padding: 7px 14px;
    font-weight: 600; color: #52637A; font-size: .85rem;
}
.stTabs [aria-selected="true"] {
    background: #ffffff; color: #1D4ED8;
    box-shadow: 0 1px 5px rgba(15,23,42,.09);
}

/* Widgets & containers */
[data-testid="stExpander"] {
    border: 1px solid #E6EBF3; border-radius: 14px;
    background: #fff; overflow: hidden;
}
[data-testid="stExpander"] summary { font-weight: 600; color: #334155; }
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border-color: #E6EBF3 !important;
    background: rgba(255,255,255,.72);
}
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
/* Plotly treemap: warna root default (#444) dibuat menyatu dengan latar */
.js-plotly-plot path[style*="fill: rgb(68, 68, 68)"] { fill: #EEF2F8 !important; }
.stDownloadButton button, .stButton button {
    border-radius: 10px; font-weight: 600;
}
[data-testid="stMetric"] {
    background: #fff; border: 1px solid #E6EBF3;
    border-radius: 14px; padding: 12px 14px;
}
[data-testid="stCaptionContainer"] { color: #7B8CA3; }

@media (max-width: 760px) {
    .hero { padding: 22px 20px; }
    .hero h1 { font-size: 1.5rem; }
    .kpi-value { font-size: 1.5rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def hero(eyebrow: str, title: str, subtitle: str, chips: list[str], compact: bool = False):
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    cls = "hero compact" if compact else "hero"
    st.markdown(
        f"""
        <div class="{cls}">
            <div class="eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="chips">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="sec">
            <div class="sec-icon">{icon}</div>
            <div>
                <div class="sec-title">{title}</div>
                <div class="sec-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi(label: str, value: str, note: str, accent: str = BLUE, icon: str = "•"):
    st.markdown(
        f"""
        <div class="kpi" style="--accent:{accent};">
            <div class="kpi-top"><span class="kpi-icon">{icon}</span>{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def callout(text: str, kind: str = "info"):
    st.markdown(f'<div class="callout {kind}">{text}</div>', unsafe_allow_html=True)


def polish(fig: go.Figure, height: int = 420, showlegend: bool = False, title: str | None = None):
    top_margin = 54 if title else 28
    bottom_margin = 66 if showlegend else 10
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=PLOT_FONT, color="#475569", size=12),
        margin=dict(l=10, r=16, t=top_margin, b=bottom_margin),
        showlegend=showlegend,
        legend=dict(
            orientation="h", yanchor="top", y=-0.2, x=0.5, xanchor="center",
            traceorder="normal", bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#475569"),
        ),
        hoverlabel=dict(
            bgcolor="#0F172A", font=dict(color="#F8FAFC", family=PLOT_FONT, size=12),
            bordercolor="#0F172A",
        ),
        colorway=[BLUE, CYAN, AMBER, TEAL, PURPLE, PINK],
    )
    if title:
        fig.update_layout(title=dict(text=title, x=0, xanchor="left", font=dict(size=15, color=DARK)))
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(148,163,184,.18)",
        linecolor="rgba(148,163,184,.35)", zeroline=False,
        tickfont=dict(size=11, color=SLATE),
        title_font=dict(size=11, color=MUTED),
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=False, linecolor="rgba(148,163,184,.35)", zeroline=False,
        tickfont=dict(size=11, color=SLATE),
        title_font=dict(size=11, color=MUTED),
        automargin=True,
    )
    return fig


def chart(fig: go.Figure, key: str | None = None):
    st.plotly_chart(
        fig, width="stretch", theme=None, key=key,
        config={"displayModeBar": False, "responsive": True},
    )


def axis_start(values) -> int:
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return 0
    vmin = float(vals.min())
    return 0 if vmin < 70 else max(0, math.floor(vmin - 4))


def pct_range(values) -> list[float]:
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return [0, 104]
    vmax = float(vals.max())
    lo = axis_start(vals)
    hi = 104 if vmax <= 100 else math.ceil(vmax + 4)
    return [lo, hi]


def add_reference_line(fig: go.Figure, value: float, text: str, color: str = AMBER):
    """Garis referensi vertikal dengan label yang aman di atas area plot."""
    fig.add_vline(x=value, line_width=1.6, line_dash="dash", line_color=color)
    fig.add_annotation(
        x=value, y=1.0, yref="paper", text=text, showarrow=False,
        yshift=9, xanchor="center",
        font=dict(size=10, color=color),
        bgcolor="rgba(255,255,255,.88)", borderpad=2,
    )


def ranking_chart(
    df: pd.DataFrame,
    value_col: str,
    label_col: str = "Provinsi",
    national: float | None = None,
    scale: list[str] | None = None,
    height: int | None = None,
    highest_on_top: bool = True,
    value_text=None,
    ticksuffix: str = "%",
    axis_title: str = "",
    show_national_label: str = "Nasional",
    percent: bool = True,
    tickformat: str | None = None,
    national_text: str | None = None,
):
    d = df[[label_col, value_col]].dropna().copy()
    if d.empty:
        return None
    d = d.sort_values(value_col, ascending=highest_on_top)
    vals = d[value_col].to_numpy(dtype=float)
    labels = d[label_col].tolist()
    value_text = value_text or (lambda v: fmt_pct(v))
    texts = [value_text(v) for v in vals]

    scale = scale or BLUE_SCALE
    if len(vals) == 1 or np.isclose(vals.max(), vals.min()):
        norm = np.full(len(vals), 0.55)
    else:
        # Warna berbasis peringkat agar gradasi tetap terbaca ketika nilai
        # provinsi mengumpul di rentang sempit (mis. APS 7–12).
        order_idx = np.argsort(np.argsort(vals))
        norm = order_idx / (len(vals) - 1)
        norm = 0.14 + 0.86 * norm
    colors = sample_colorscale(scale, norm)

    h = height or max(370, int(len(d) * 25 + 100))
    fig = go.Figure(
        go.Bar(
            x=vals,
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=texts,
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=10, color="#334155"),
            customdata=texts,
            hovertemplate="<b>%{y}</b><br>" + axis_title + ": %{customdata}<extra></extra>",
        )
    )
    if percent:
        lo, hi = pct_range(vals)
    else:
        lo = 0
        hi = float(vals.max()) * 1.18
    fig.update_layout(xaxis_range=[lo, hi], margin=dict(l=8, r=54, t=48, b=8))
    fig.update_xaxes(ticksuffix=ticksuffix)
    if tickformat:
        fig.update_xaxes(tickformat=tickformat)
    if national is not None and np.isfinite(national):
        label = national_text or f"{show_national_label} {fmt_pct(national)}"
        add_reference_line(fig, national, label)
    return polish(fig, height=h, title=None)


# =============================================================================
# HALAMAN: RINGKASAN
# =============================================================================
def render_overview():
    hero(
        "Dasbor Pendidikan · 2023–2025",
        "Potret Pendidikan Indonesia dalam Tiga Data",
        "Menjelajahi angka partisipasi sekolah, tingkat penyelesaian pendidikan, "
        "dan sebaran pendidik di 38 provinsi — dirangkum agar mudah dibaca dan dibandingkan.",
        ["38 provinsi", "APS 2025", "Penyelesaian 2023", "Pendidik 2025"],
    )

    total_teacher = float(TCH["jumlah"].sum())
    female_teacher = float(TCH.loc[TCH["gender"] == "Perempuan", "jumlah"].sum())

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi("APS usia 7–12", fmt_pct(APS_NAT["7-12"]), "Angka partisipasi sekolah nasional", BLUE, "🎒")
    with c2:
        kpi("APS usia 19–23", fmt_pct(APS_NAT["19-23"]), "Titik terendah dalam pipeline pendidikan", CYAN, "📉")
    with c3:
        kpi("Penyelesaian SMA", fmt_pct(COMP_NAT["SMA"]), "Penduduk yang menyelesaikan SMA/sederajat", AMBER, "🎓")
    with c4:
        kpi(
            "Total pendidik",
            fmt_short(total_teacher),
            f"{fmt_pct(female_teacher / total_teacher * 100, 1)} di antaranya perempuan",
            PURPLE, "👩‍🏫",
        )

    section("🧭", "Tiga potret utama", "Partisipasi, penyelesaian, dan tenaga pendidik dalam satu pandangan")

    col_a, col_b = st.columns([1.35, 1], gap="large")
    with col_a:
        vals = [APS_NAT[a] for a in AGE_ORDER]
        fig = go.Figure(
            go.Bar(
                x=[AGE_DISPLAY[a] for a in AGE_ORDER],
                y=vals,
                marker=dict(color=[AGE_COLORS[a] for a in AGE_ORDER], line=dict(width=0)),
                text=[fmt_pct(v) for v in vals],
                textposition="outside",
                cliponaxis=False,
                textfont=dict(size=11, color="#334155"),
                hovertemplate="Usia %{x}<br><b>%{text}</b><extra></extra>",
            )
        )
        fig.update_layout(yaxis_range=[0, 112])
        fig.update_yaxes(ticksuffix="%")
        chart(polish(fig, height=390, title="Pipeline partisipasi sekolah nasional (APS 2025)"))

    with col_b:
        vals = [COMP_NAT[l] for l in LEVELS]
        fig = go.Figure(
            go.Bar(
                x=[f"Selesai {l}" for l in LEVELS],
                y=vals,
                marker=dict(color=[LEVEL_COLORS[l] for l in LEVELS], line=dict(width=0)),
                text=[fmt_pct(v) for v in vals],
                textposition="outside",
                cliponaxis=False,
                textfont=dict(size=11, color="#334155"),
                hovertemplate="%{x}<br><b>%{text}</b><extra></extra>",
            )
        )
        fig.update_layout(yaxis_range=[0, 112])
        fig.update_yaxes(ticksuffix="%")
        chart(polish(fig, height=390, title="Penyelesaian jenjang pendidikan (2023)"))

    section("🗺️", "Wajah pendidikan antarwilayah", "Rata-rata provinsi pada tiap wilayah")

    col_c, col_d = st.columns([1.45, 1], gap="large")
    with col_c:
        reg = (
            MASTER.groupby("region")[["16-18", "SMA"]]
            .mean()
            .reindex(REGION_ORDER)
            .reset_index()
            .melt(id_vars="region", var_name="indikator", value_name="nilai")
        )
        reg["indikator"] = reg["indikator"].map(
            {"16-18": "APS 16–18 (2025)", "SMA": "Penyelesaian SMA (2023)"}
        )
        fig = px.bar(
            reg, x="region", y="nilai", color="indikator", barmode="group",
            color_discrete_sequence=["#2563EB", "#F59E0B"],
            labels={"region": "", "nilai": "", "indikator": ""},
            text=reg["nilai"].map(lambda v: f"{v:.1f}".replace(".", ",")),
        )
        fig.update_traces(textposition="outside", cliponaxis=False, textfont=dict(size=9.5))
        fig.update_layout(yaxis_range=[0, 112])
        fig.update_yaxes(ticksuffix="%")
        chart(polish(fig, height=420, showlegend=True, title="Perbandingan indikator kunci per wilayah"))

    with col_d:
        gender = TCH.groupby("gender")["jumlah"].sum()
        vals = [gender.get("Laki-laki", 0), gender.get("Perempuan", 0)]
        fig = go.Figure(
            go.Pie(
                labels=["Laki-laki", "Perempuan"],
                values=vals,
                hole=0.68,
                marker=dict(colors=[GENDER_COLORS["Laki-laki"], GENDER_COLORS["Perempuan"]],
                            line=dict(color="#ffffff", width=3)),
                textinfo="percent",
                textfont=dict(size=13, color="#ffffff", family=PLOT_FONT),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} orang<br>%{percent}<extra></extra>",
                sort=False,
            )
        )
        fig.add_annotation(
            text=f"<b>{fmt_short(total_teacher)}</b><br><span style='font-size:11px;color:#64748B'>total pendidik</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=17, color=DARK, family=PLOT_FONT),
        )
        chart(polish(fig, height=420, showlegend=True, title="Komposisi gender pendidik nasional"))

    section("🏅", "Ujung tombak dan titik tantangan", "Penyelesaian SMA/sederajat, 5 teratas dan 5 terbawah")

    comp_valid = MASTER.dropna(subset=["SMA"]).sort_values("SMA")
    low = comp_valid.head(5).copy()
    high = comp_valid.tail(5).copy()
    low["kategori"] = "5 terendah"
    high["kategori"] = "5 tertinggi"
    extremes = pd.concat([low, high]).sort_values("SMA", ascending=True)
    colors = [AMBER_SCALE[-2] if k == "5 terendah" else TEAL_SCALE[-1] for k in extremes["kategori"]]
    fig = go.Figure(
        go.Bar(
            x=extremes["SMA"], y=extremes["Provinsi"], orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[fmt_pct(v) for v in extremes["SMA"]],
            textposition="outside", cliponaxis=False,
            textfont=dict(size=10, color="#334155"),
            customdata=np.stack([extremes["kategori"], extremes["SMA"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{x:.2f}%<extra></extra>",
        )
    )
    add_reference_line(fig, COMP_NAT["SMA"], f"Nasional {fmt_pct(COMP_NAT['SMA'])}", color="#0F172A")
    lo, hi = pct_range(extremes["SMA"])
    fig.update_xaxes(range=[lo, hi], ticksuffix="%")
    fig.update_layout(margin=dict(l=8, r=56, t=48, b=8))
    chart(polish(fig, height=455, title="Provinsi dengan penyelesaian SMA tertinggi & terendah"))

    best_aps = MASTER.loc[MASTER["16-18"].idxmax()]
    worst_aps = MASTER.loc[MASTER["16-18"].idxmin()]
    best_comp = comp_valid.iloc[-1]
    worst_comp = comp_valid.iloc[0]

    callout(
        f"<b>Yang perlu diapresiasi:</b> {best_aps['Provinsi']} mencatat APS usia 16–18 tertinggi "
        f"({fmt_pct(best_aps['16-18'])}) dan penyelesaian SMA tertinggi ({fmt_pct(best_comp['SMA'])}). "
        f"<b>Yang perlu perhatian:</b> APS 16–18 di {worst_aps['Provinsi']} baru {fmt_pct(worst_aps['16-18'])}, "
        f"sedangkan penyelesaian SMA terendah tercatat di {worst_comp['Provinsi']} ({fmt_pct(worst_comp['SMA'])}).",
        "info",
    )
    callout(
        "Empat provinsi baru di Papua — <b>Papua Barat Daya, Papua Selatan, Papua Tengah, dan Papua Pegunungan</b> — "
        "belum memiliki angka penyelesaian pendidikan 2023 pada dataset ini. Angka tersebut tidak diisi atau diinterpolasi.",
        "warn",
    )


# =============================================================================
# HALAMAN: PETA INDONESIA
# =============================================================================
def render_map():
    hero(
        "Peta Indonesia · Sebaran per provinsi",
        "Bagaimana indikator pendidikan tersebar di 38 provinsi?",
        "Peta choropleth memperlihatkan distribusi nilai antardaerah. Pilih indikator dan wilayah, "
        "lalu arahkan kursor ke provinsi untuk melihat angkanya.",
        ["38 provinsi", "Choropleth", "APS 2025", "Penyelesaian 2023", "Pendidik 2025"],
        compact=True,
    )

    with st.container(border=True):
        c1, c2 = st.columns([1.7, 1], gap="medium")
        indicator = c1.selectbox(
            "Indikator yang dipetakan", list(MAP_INDICATORS),
            index=2, key="map_indicator",
        )
        region_focus = c2.selectbox(
            "Wilayah tampilan", ["Seluruh Indonesia", *REGION_ORDER],
            key="map_region",
            help="Pilih wilayah untuk memperbesar peta ke wilayah tersebut.",
        )

    info = MAP_INDICATORS[indicator]
    col = info["col"]
    kind = info["kind"]
    label = info["label"]

    df = MASTER.copy()
    if region_focus != "Seluruh Indonesia":
        df = df[df["region"] == region_focus].copy()

    valid = df.dropna(subset=[col]).copy()
    missing = df[df[col].isna()].copy()
    if valid.empty:
        callout("Tidak ada data untuk indikator dan wilayah ini.", "warn")
        return

    def fmt_value(v) -> str:
        return fmt_short(v) if kind == "count" else fmt_pct(v)

    if kind == "pct":
        national = APS_NAT[col] if info["source"] == "aps" else COMP_NAT[col]
        national_label = "Nasional"
    elif kind == "count":
        scope = TCH if region_focus == "Seluruh Indonesia" else TCH[TCH["region"] == region_focus]
        national = float(scope["jumlah"].sum())
        national_label = "Total nasional" if region_focus == "Seluruh Indonesia" else "Total wilayah"
    else:
        scope = TCH if region_focus == "Seluruh Indonesia" else TCH[TCH["region"] == region_focus]
        total = float(scope["jumlah"].sum())
        female = float(scope.loc[scope["gender"] == "Perempuan", "jumlah"].sum())
        national = female / total * 100 if total else np.nan
        national_label = "Proporsi nasional" if region_focus == "Seluruh Indonesia" else "Proporsi wilayah"

    top = valid.loc[valid[col].idxmax()]
    bottom = valid.loc[valid[col].idxmin()]
    scope_name = "Indonesia" if region_focus == "Seluruh Indonesia" else region_focus

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi(national_label, fmt_value(national), f"Cakupan {scope_name} · {info['short']}", BLUE, "🇮🇩")
    with c2:
        kpi("Tertinggi", fmt_value(top[col]), top["Provinsi"], TEAL, "🏆")
    with c3:
        kpi("Terendah", fmt_value(bottom[col]), bottom["Provinsi"], "#EF4444", "🔻")
    with c4:
        coverage_note = (
            f"{len(missing)} provinsi belum tersedia" if len(missing)
            else "Semua provinsi tersedia"
        )
        kpi("Provinsi terpetakan", f"{len(valid)}/{len(df)}", coverage_note, AMBER, "🗺️")

    section(
        "🗺️",
        f"Sebaran {label} per provinsi",
        "Warna makin gelap = nilai makin tinggi"
        if kind != "share"
        else "Biru = proporsi perempuan lebih rendah · pink = lebih tinggi",
    )

    fig = go.Figure()

    # Lapisan abu-abu untuk provinsi yang datanya belum tersedia.
    if not missing.empty:
        fig.add_trace(
            go.Choropleth(
                geojson=GEOJSON,
                locations=missing["provinsi"],
                z=[0] * len(missing),
                featureidkey="properties.PROV_CANON",
                colorscale=[[0, "#E2E8F0"], [1, "#E2E8F0"]],
                zmin=0, zmax=1, showscale=False,
                marker=dict(line=dict(color="#FFFFFF", width=0.8)),
                customdata=np.stack([missing["Provinsi"], missing["region"]], axis=-1),
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                              "Data belum tersedia<extra></extra>",
            )
        )

    values = valid[col].astype(float)

    if kind == "count":
        z = np.log10(values + 1)
        zmin = math.log10(max(float(values.min()), 1) + 1)
        zmax = math.log10(float(values.max()) + 1)
        if np.isclose(zmin, zmax):
            zmin -= 0.01
            zmax += 0.01
        count_ticks = [
            t for t in (10 ** e for e in range(2, 8))
            if float(values.min()) * 0.7 <= t <= float(values.max()) * 1.3
        ]
        tickvals = [math.log10(t + 1) for t in count_ticks]
        ticktext = [fmt_short(t) for t in count_ticks]
        colorbar_title = "Pendidik"
    elif kind == "share":
        z = values
        zmin, zmax = 20, 80
        tickvals, ticktext = None, None
        colorbar_title = "% perempuan"
    else:
        z = values
        zmin = max(0, math.floor(float(values.min()) / 5) * 5 - 5)
        zmax = 100
        tickvals, ticktext = None, None
        colorbar_title = "%"

    colorbar = dict(
        title=dict(text=colorbar_title, font=dict(size=10)),
        thickness=12, len=0.55, x=0.98,
        tickfont=dict(size=9),
    )
    if kind == "count":
        colorbar["tickvals"] = tickvals
        colorbar["ticktext"] = ticktext
    else:
        colorbar["ticksuffix"] = "%"

    fig.add_trace(
        go.Choropleth(
            geojson=GEOJSON,
            locations=valid["provinsi"],
            z=z,
            featureidkey="properties.PROV_CANON",
            colorscale=MAP_SCALES[info["scale"]],
            zmin=zmin, zmax=zmax,
            marker=dict(line=dict(color="#FFFFFF", width=0.8)),
            colorbar=colorbar,
            customdata=np.stack(
                [valid["Provinsi"], valid["region"], [fmt_value(v) for v in values]],
                axis=-1,
            ),
            hovertemplate=f"<b>%{{customdata[0]}}</b><br>%{{customdata[1]}}<br>"
                          f"{label}: <b>%{{customdata[2]}}</b><extra></extra>",
        )
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
        showcountries=False,
        showcoastlines=False,
        showland=False,
        showlakes=False,
        showrivers=False,
        showframe=False,
    )
    fig.update_layout(
        height=580,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="#0B1220",
            bordercolor="#38BDF8",
            font=dict(color="#F8FAFC", family=PLOT_FONT, size=12),
            align="left",
        ),
    )

    with st.container(border=True):
        chart(fig, key="map_choropleth")
        st.caption(
            "Batas administrasi provinsi: [Indonesia GeoJSON & TopoJSON Maps (38 Provinces)]"
            "(https://github.com/denyherianto/indonesia-geojson-topojson-maps-with-38-provinces) "
            "· lisensi CC BY 4.0."
        )

    section(
        "🏅",
        f"Provinsi teratas & terbawah — {label}",
        "Delapan nilai tertinggi dan delapan terendah pada cakupan ini",
    )

    n = min(8, max(1, len(valid)))
    extremes = pd.concat([
        valid.nlargest(n, col),
        valid.nsmallest(n, col),
    ]).drop_duplicates(subset=["provinsi"])
    rank_scale = {
        "blue": BLUE_SCALE,
        "teal": TEAL_SCALE,
        "purple": PURPLE_SCALE,
        "diverging": MIXED_SCALE,
    }[info["scale"]]

    if kind == "count":
        rank_fig = ranking_chart(
            extremes, col, scale=rank_scale, value_text=fmt_short,
            ticksuffix="", percent=False, tickformat="~s",
            axis_title="Pendidik",
        )
    else:
        rank_fig = ranking_chart(
            extremes, col, national=national, scale=rank_scale,
            value_text=fmt_pct, ticksuffix="%", percent=True,
            axis_title=label,
        )
    if rank_fig is not None:
        chart(rank_fig, key="map_rank")
        if kind != "count":
            _lo = axis_start(extremes[col])
            if _lo > 0:
                st.caption(
                    f"Catatan: sumbu horizontal dimulai dari {_lo}% agar perbedaan lebih terlihat."
                )

    callout(
        f"Pada cakupan <b>{scope_name}</b>, nilai <b>{label}</b> tertinggi dicatat oleh "
        f"<b>{top['Provinsi']}</b> ({fmt_value(top[col])}), sedangkan yang terendah adalah "
        f"<b>{bottom['Provinsi']}</b> ({fmt_value(bottom[col])}). "
        "Perbedaan ini menggambarkan ketimpangan spasial, bukan hubungan sebab-akibat.",
        "info",
    )

    if len(missing):
        callout(
            "Data belum tersedia untuk: <b>" + ", ".join(missing["Provinsi"].tolist()) + "</b>. "
            "Area tersebut ditampilkan abu-abu dan tidak disertakan dalam peringkat.",
            "warn",
        )

    with st.expander("📋 Lihat tabel peta & unduh data"):
        table = df[["Provinsi", "region", col]].rename(
            columns={"region": "Wilayah", col: "Nilai"}
        ).sort_values("Nilai", ascending=False, na_position="last")
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={
                "Nilai": st.column_config.NumberColumn(
                    "Nilai", format="%d" if kind == "count" else "%.2f"
                )
            },
        )
        st.download_button(
            "⬇️ Unduh CSV data peta",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="peta_indikator_pendidikan.csv",
            mime="text/csv", key="dl_map",
        )


# =============================================================================
# HALAMAN: PARTISIPASI SEKOLAH
# =============================================================================
def render_aps():
    hero(
        "Dataset 1 · Angka Partisipasi Sekolah 2025",
        "Seberapa banyak anak yang masih bersekolah?",
        "APS mengukur proporsi penduduk kelompok umur tertentu yang masih mengikuti pendidikan formal. "
        "Semakin tinggi angkanya, semakin besar keterlibatan anak pada jalur pendidikan.",
        ["38 provinsi", "4 kelompok umur", "Tahun 2025"],
        compact=True,
    )

    with st.container(border=True):
        f1, f2, f3 = st.columns([1.05, 1.65, 1.1], gap="medium")
        focus = f1.selectbox(
            "Kelompok umur fokus", AGE_ORDER, index=2,
            format_func=lambda a: AGE_DISPLAY[a], key="aps_focus",
        )
        selected_regions = f2.multiselect(
            "Wilayah", REGION_ORDER, default=REGION_ORDER, key="aps_regions", wrap=True,
            help="Pilih satu atau beberapa wilayah untuk memfilter peringkat provinsi.",
        )
        order = f3.radio(
            "Urutan peringkat", ["Tertinggi", "Terendah"],
            horizontal=True, key="aps_order",
        )

    if not selected_regions:
        selected_regions = REGION_ORDER
    df = MASTER[MASTER["region"].isin(selected_regions)].copy()
    focus_label = AGE_DISPLAY[focus]
    national = APS_NAT[focus]

    top_row = df.loc[df[focus].idxmax()]
    bottom_row = df.loc[df[focus].idxmin()]
    spread = top_row[focus] - bottom_row[focus]

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi(f"Nasional · {focus_label}", fmt_pct(national), "Seluruh Indonesia", BLUE, "🇮🇩")
    with c2:
        kpi(f"Tertinggi · {focus_label}", fmt_pct(top_row[focus]), top_row["Provinsi"], TEAL, "🏆")
    with c3:
        kpi(f"Terendah · {focus_label}", fmt_pct(bottom_row[focus]), bottom_row["Provinsi"], "#EF4444", "🔻")
    with c4:
        kpi("Rentang antarpovinsi", f"{spread:.2f}".replace(".", ",") + " pp",
            "Selisih provinsi tertinggi & terendah", AMBER, "↔️")

    section(
        "📊", f"Peringkat provinsi — APS {focus_label}",
        f"Diurutkan {'dari tertinggi ke terendah' if order == 'Tertinggi' else 'dari terendah ke tertinggi'}"
        + f" · {len(df)} provinsi",
    )
    fig = ranking_chart(
        df, focus, national=national, scale=BLUE_SCALE,
        highest_on_top=(order == "Tertinggi"), axis_title="APS",
    )
    if fig is not None:
        chart(fig, key="aps_rank")
        _lo = axis_start(df[focus].dropna())
        if _lo > 0:
            st.caption(
                f"Catatan: sumbu horizontal dimulai dari {_lo}% agar perbedaan antarpovinsi lebih terlihat. "
                "Nilai lengkap tersedia pada tabel di bagian bawah."
            )

    col_left, col_right = st.columns([1.25, 1], gap="large")
    with col_left:
        section("🎯", "Sebaran nilai per kelompok umur", "Setiap titik adalah satu provinsi")
        fig = go.Figure()
        for age in AGE_ORDER:
            vals = df[age].dropna()
            fig.add_trace(
                go.Box(
                    y=vals, name=AGE_DISPLAY[age],
                    marker_color=AGE_COLORS[age], fillcolor=AGE_COLORS[age] + "33",
                    line=dict(width=1.5, color=AGE_COLORS[age]),
                    boxpoints="all", jitter=0.48, pointpos=0,
                    marker=dict(size=4, opacity=0.55),
                    hovertemplate=f"<b>%{{y:.2f}}%</b><extra>{AGE_DISPLAY[age]}</extra>",
                )
            )
        nat_vals = [APS_NAT[a] for a in AGE_ORDER]
        fig.add_trace(
            go.Scatter(
                x=[AGE_DISPLAY[a] for a in AGE_ORDER], y=nat_vals,
                mode="markers", name="Nasional",
                marker=dict(symbol="diamond", size=12, color=AMBER,
                            line=dict(color="#ffffff", width=1.5)),
                hovertemplate="Nasional %{x}: <b>%{y:.2f}%</b><extra></extra>",
            )
        )
        fig.update_layout(yaxis_range=[0, 108])
        fig.update_yaxes(ticksuffix="%")
        chart(polish(fig, height=410, showlegend=True, title="Distribusi APS provinsi (2025)"))

    with col_right:
        section("🗺️", "Rata-rata per wilayah", f"APS {focus_label}")
        reg = (
            df.groupby("region")[focus].mean().reindex(selected_regions).dropna()
            .reset_index().sort_values(focus, ascending=True)
        )
        colors = [REGION_COLORS.get(r, BLUE) for r in reg["region"]]
        fig = go.Figure(
            go.Bar(
                x=reg[focus], y=reg["region"], orientation="h",
                marker=dict(color=colors, line=dict(width=0)),
                text=[fmt_pct(v) for v in reg[focus]],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=10, color="#334155"),
                hovertemplate="<b>%{y}</b><br>APS: %{x:.2f}%<extra></extra>",
            )
        )
        lo, hi = pct_range(reg[focus])
        fig.update_xaxes(range=[lo, hi], ticksuffix="%")
        add_reference_line(fig, national, f"Nasional {fmt_pct(national)}")
        fig.update_layout(margin=dict(l=8, r=50, t=48, b=8))
        chart(polish(fig, height=410, title=f"Rata-rata APS {focus_label} per wilayah"))

    section("🌡️", "Peta panas APS semua kelompok umur", "Provinsi diurutkan berdasarkan rata-rata seluruh kelompok umur")
    mat = df.set_index("Provinsi")[AGE_ORDER].copy()
    mat["_avg"] = mat.mean(axis=1)
    mat = mat.sort_values("_avg", ascending=False).drop(columns="_avg")
    z = mat.to_numpy(dtype=float)
    text = [["" if np.isnan(v) else fmt_pct(v, 1) for v in row] for row in z]
    fig = go.Figure(
        go.Heatmap(
            z=z, hoverongaps=False,
            x=[AGE_DISPLAY[a] for a in AGE_ORDER],
            y=mat.index.tolist(),
            colorscale=[[0, "#F8FAFC"], [0.25, "#DBEAFE"], [0.55, "#BFDBFE"], [0.8, "#93C5FD"], [1, "#60A5FA"]],
            zmin=0, zmax=100,
            text=text, texttemplate="%{text}",
            textfont=dict(size=9.5, color="#0F172A"),
            xgap=2, ygap=2,
            colorbar=dict(title=dict(text="APS %", font=dict(size=10)), thickness=10, len=0.55),
            hovertemplate="<b>%{y}</b><br>%{x}: <b>%{text}</b><extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=9.5))
    fig.update_xaxes(side="top", tickfont=dict(size=10))
    chart(polish(fig, height=max(640, len(mat) * 20 + 110), title="Peta panas APS provinsi × kelompok umur (2025)"))

    with st.expander("📋 Lihat tabel lengkap & unduh data APS"):
        table = df[["Provinsi", "region", *AGE_ORDER]].rename(
            columns={"region": "Wilayah", **AGE_DISPLAY}
        )
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={
                AGE_DISPLAY[a]: st.column_config.NumberColumn(AGE_DISPLAY[a], format="%.2f", width="small")
                for a in AGE_ORDER
            },
        )
        st.download_button(
            "⬇️ Unduh CSV APS (provinsi)",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="aps_provinsi_2025.csv",
            mime="text/csv", key="dl_aps",
        )


# =============================================================================
# HALAMAN: PENYELESAIAN PENDIDIKAN
# =============================================================================
def render_completion():
    hero(
        "Dataset 2 · Tingkat Penyelesaian Pendidikan 2023",
        "Sampai jenjang mana penduduk menyelesaikan pendidikan?",
        "Tingkat penyelesaian menunjukkan proporsi penduduk yang berhasil menuntaskan suatu jenjang "
        "pendidikan. Perhatikan bahwa empat provinsi baru di Papua belum memiliki angka pada dataset ini.",
        ["38 provinsi", "SD · SMP · SMA", "Tahun 2023"],
        compact=True,
    )

    with st.container(border=True):
        f1, f2, f3 = st.columns([1.05, 1.65, 1.1], gap="medium")
        focus = f1.selectbox(
            "Jenjang fokus", LEVELS, index=2,
            format_func=lambda l: f"{l} / Sederajat", key="comp_focus",
        )
        selected_regions = f2.multiselect(
            "Wilayah", REGION_ORDER, default=REGION_ORDER, key="comp_regions", wrap=True,
        )
        order = f3.radio(
            "Urutan peringkat", ["Tertinggi", "Terendah"],
            horizontal=True, key="comp_order",
        )

    if not selected_regions:
        selected_regions = REGION_ORDER
    df = MASTER[MASTER["region"].isin(selected_regions)].copy()
    valid = df.dropna(subset=[focus])
    national = COMP_NAT[focus]
    missing_count = int(df[focus].isna().sum())

    if valid.empty:
        callout("Tidak ada data penyelesaian yang tersedia untuk filter ini.", "warn")
        return

    top_row = valid.loc[valid[focus].idxmax()]
    bottom_row = valid.loc[valid[focus].idxmin()]
    spread = top_row[focus] - bottom_row[focus]

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi(f"Nasional · {focus}", fmt_pct(national), "Seluruh Indonesia", BLUE, "🇮🇩")
    with c2:
        kpi(f"Tertinggi · {focus}", fmt_pct(top_row[focus]), top_row["Provinsi"], TEAL, "🏆")
    with c3:
        kpi(f"Terendah · {focus}", fmt_pct(bottom_row[focus]), bottom_row["Provinsi"], "#EF4444", "🔻")
    with c4:
        kpi("Rentang antarpovinsi", f"{spread:.2f}".replace(".", ",") + " pp",
            f"Data belum tersedia: {missing_count} provinsi", AMBER, "↔️")

    section(
        "📊", f"Peringkat provinsi — Penyelesaian {focus}",
        f"Data tahun 2023 · {len(valid)} provinsi dengan data",
    )
    fig = ranking_chart(
        valid, focus, national=national, scale=TEAL_SCALE,
        highest_on_top=(order == "Tertinggi"), axis_title=f"Penyelesaian {focus}",
    )
    if fig is not None:
        chart(fig, key="comp_rank")
        _lo = axis_start(valid[focus])
        if _lo > 0:
            st.caption(
                f"Catatan: sumbu horizontal dimulai dari {_lo}% agar perbedaan antarpovinsi lebih terlihat. "
                "Nilai lengkap tersedia pada tabel di bagian bawah."
            )

    col_left, col_right = st.columns([1.2, 1], gap="large")
    with col_left:
        section("🧩", "Perbandingan tiga jenjang", "Rata-rata provinsi per wilayah")
        reg = df.groupby("region")[LEVELS].mean().reindex(REGION_ORDER).dropna(how="all")
        reg = reg.reset_index().melt(id_vars="region", var_name="jenjang", value_name="nilai")
        fig = px.bar(
            reg, x="region", y="nilai", color="jenjang", barmode="group",
            color_discrete_map=LEVEL_COLORS,
            labels={"region": "", "nilai": "", "jenjang": ""},
            category_orders={"jenjang": LEVELS},
        )
        fig.update_traces(cliponaxis=False)
        fig.update_layout(yaxis_range=[0, 115])
        fig.update_yaxes(ticksuffix="%")
        chart(polish(fig, height=420, showlegend=True, title="Penyelesaian SD, SMP, dan SMA per wilayah"))

    with col_right:
        section("🕳️", "Kesenjangan SD–SMA", "10 provinsi dengan selisih terbesar (poin persentase)")
        gap = df.dropna(subset=["SD", "SMA"]).copy()
        gap["gap"] = gap["SD"] - gap["SMA"]
        gap = gap.nlargest(10, "gap").sort_values("gap", ascending=True)
        fig = go.Figure(
            go.Bar(
                x=gap["gap"], y=gap["Provinsi"], orientation="h",
                marker=dict(
                    color=sample_colorscale(AMBER_SCALE, np.linspace(0.25, 1, len(gap))),
                    line=dict(width=0),
                ),
                text=[f"{v:.1f}".replace(".", ",") + " pp" for v in gap["gap"]],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=9.5, color="#334155"),
                hovertemplate="<b>%{y}</b><br>SD − SMA: %{x:.2f} pp<extra></extra>",
            )
        )
        fig.update_xaxes(range=[0, max(gap["gap"]) * 1.22], ticksuffix=" pp")
        fig.update_layout(margin=dict(l=8, r=54, t=48, b=8))
        chart(polish(fig, height=420, title="Kesenjangan penyelesaian SD vs SMA"))

    section("🌡️", "Peta panas penyelesaian pendidikan", "Nilai kosong = data belum tersedia")
    mat = df.set_index("Provinsi")[LEVELS].copy()
    mat["_avg"] = mat.mean(axis=1, skipna=True)
    mat = mat.sort_values("_avg", ascending=False).drop(columns="_avg")
    z = mat.to_numpy(dtype=float)
    text = [["" if np.isnan(v) else fmt_pct(v, 1) for v in row] for row in z]
    fig = go.Figure(
        go.Heatmap(
            z=z, hoverongaps=False,
            x=[LEVEL_DISPLAY[l] for l in LEVELS],
            y=mat.index.tolist(),
            colorscale=[[0, "#FFFBEB"], [0.3, "#FDE68A"], [0.6, "#99F6E4"], [0.85, "#5EEAD4"], [1, "#2DD4BF"]],
            zmin=30, zmax=100,
            text=text, texttemplate="%{text}",
            textfont=dict(size=10, color="#0F172A"),
            xgap=2, ygap=2,
            colorbar=dict(title=dict(text="%", font=dict(size=10)), thickness=10, len=0.55),
            hovertemplate="<b>%{y}</b><br>%{x}: <b>%{text}</b><extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=9.5))
    fig.update_xaxes(side="top", tickfont=dict(size=10))
    chart(polish(fig, height=max(640, len(mat) * 20 + 110), title="Peta panas penyelesaian pendidikan menurut provinsi (2023)"))

    if missing_count:
        missing = df[df[focus].isna()]["Provinsi"].tolist()
        callout(
            "Data belum tersedia untuk: <b>" + ", ".join(missing) + "</b>. "
            "Provinsi-provinsi tersebut tidak disertakan dalam peringkat dan perhitungan kesenjangan.",
            "warn",
        )

    with st.expander("📋 Lihat tabel lengkap & unduh data penyelesaian"):
        table = df[["Provinsi", "region", *LEVELS]].rename(
            columns={"region": "Wilayah", **{l: f"Selesai {l}" for l in LEVELS}}
        )
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={
                f"Selesai {l}": st.column_config.NumberColumn(f"Selesai {l}", format="%.2f", width="small")
                for l in LEVELS
            },
        )
        st.download_button(
            "⬇️ Unduh CSV penyelesaian pendidikan",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="penyelesaian_pendidikan_2023.csv",
            mime="text/csv", key="dl_comp",
        )


# =============================================================================
# HALAMAN: PENDIDIK
# =============================================================================
def render_teachers():
    hero(
        "Dataset 3 · Pendidik & Tenaga Kependidikan 2025",
        "Siapa yang mengajar di ruang-ruang kelas?",
        "Jumlah pendidik dan tenaga kependidikan menurut jenjang pendidikan dan jenis kelamin. "
        "Data mencakup pendidikan anak usia dini hingga sekolah luar biasa di seluruh provinsi.",
        ["38 provinsi", "9 jenjang", "Jenis kelamin", "Tahun 2025"],
        compact=True,
    )

    with st.container(border=True):
        f1, f2 = st.columns([2, 1.2], gap="medium")
        selected_regions = f1.multiselect(
            "Wilayah", REGION_ORDER, default=REGION_ORDER, key="tch_regions", wrap=True,
        )
        level_focus = f2.selectbox(
            "Sorot jenjang", ["Semua jenjang", *TEACHER_LEVELS], index=0, key="tch_level",
        )

    if not selected_regions:
        selected_regions = REGION_ORDER
    df = TCH[TCH["provinsi"].map(PROVINCE_REGION).isin(selected_regions)].copy()
    if 0 < len(selected_regions) < len(REGION_ORDER):
        prov_scope = df["provinsi"].nunique()
        scope_text = f"{prov_scope} provinsi terpilih"
    else:
        prov_scope = 38
        scope_text = "seluruh Indonesia"

    total = float(df["jumlah"].sum())
    female = float(df.loc[df["gender"] == "Perempuan", "jumlah"].sum())
    female_share = female / total * 100 if total else np.nan
    by_level = df.groupby("jenjang")["jumlah"].sum().reindex(TEACHER_LEVELS).dropna().sort_values(ascending=False)
    largest_level = by_level.index[0] if len(by_level) else "–"
    prov_totals = df.groupby("provinsi")["jumlah"].sum().sort_values(ascending=False)
    top_prov = prov_totals.index[0] if len(prov_totals) else "–"

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi("Total pendidik", fmt_short(total), f"Cakupan: {scope_text}", PURPLE, "👥")
    with c2:
        kpi("Proporsi perempuan", fmt_pct(female_share, 1), f"{fmt_num(female)} perempuan", PINK, "👩")
    with c3:
        kpi("Jenjang terbesar", largest_level, f"{fmt_short(by_level.iloc[0])} pendidik" if len(by_level) else "–", BLUE, "🏫")
    with c4:
        kpi("Provinsi terbesar", prov_name(top_prov), f"{fmt_short(prov_totals.iloc[0])} pendidik", TEAL, "📍")

    section("🏫", "Komposisi pendidik menurut jenjang", "Jumlah pendidik laki-laki dan perempuan")
    col_a, col_b = st.columns([1.45, 1], gap="large")

    with col_a:
        pivot = (
            df.groupby(["jenjang", "gender"])["jumlah"].sum().unstack(fill_value=0)
            .reindex(TEACHER_LEVELS).fillna(0)
        )
        pivot["total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total", ascending=True)
        fig = go.Figure()
        for gender in ["Laki-laki", "Perempuan"]:
            vals = pivot[gender].to_numpy() if gender in pivot.columns else np.zeros(len(pivot))
            fig.add_trace(
                go.Bar(
                    x=vals, y=pivot.index, orientation="h", name=gender,
                    marker=dict(color=GENDER_COLORS[gender], line=dict(width=0)),
                    hovertemplate="<b>%{y}</b><br>" + gender + ": %{x:,.0f}<extra></extra>",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=pivot["total"], y=pivot.index, mode="text",
                text=[fmt_short(v) for v in pivot["total"]],
                textposition="middle right", textfont=dict(size=10, color="#475569"),
                showlegend=False, hoverinfo="skip",
            )
        )
        fig.update_layout(barmode="stack", xaxis_range=[0, pivot["total"].max() * 1.15])
        fig.update_xaxes(tickformat="~s")
        chart(polish(fig, height=460, showlegend=True, title="Pendidik menurut jenjang & gender"))

    with col_b:
        gender_vals = [df.loc[df["gender"] == g, "jumlah"].sum() for g in ["Laki-laki", "Perempuan"]]
        fig = go.Figure(
            go.Pie(
                labels=["Laki-laki", "Perempuan"], values=gender_vals, hole=0.66,
                marker=dict(colors=[GENDER_COLORS["Laki-laki"], GENDER_COLORS["Perempuan"]],
                            line=dict(color="#ffffff", width=3)),
                textinfo="percent", textfont=dict(size=13, color="#ffffff", family=PLOT_FONT),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} orang<br>%{percent}<extra></extra>",
                sort=False,
            )
        )
        fig.add_annotation(
            text=f"<b>{fmt_short(total)}</b><br><span style='font-size:11px;color:#64748B'>total pendidik</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=DARK, family=PLOT_FONT),
        )
        chart(polish(fig, height=460, showlegend=True, title="Komposisi gender pendidik"))

    col_c, col_d = st.columns([1.15, 1], gap="large")
    with col_c:
        section("🏅", "Provinsi dengan pendidik terbanyak", "12 provinsi teratas pada wilayah terpilih")
        prov_pivot = (
            df.groupby(["provinsi", "gender"])["jumlah"].sum().unstack(fill_value=0)
        )
        prov_pivot["total"] = prov_pivot.sum(axis=1)
        prov_pivot = prov_pivot.nlargest(min(12, len(prov_pivot)), "total").sort_values("total", ascending=True)
        prov_pivot.index = [prov_name(p) for p in prov_pivot.index]
        fig = go.Figure()
        for gender in ["Laki-laki", "Perempuan"]:
            vals = prov_pivot[gender].to_numpy() if gender in prov_pivot.columns else np.zeros(len(prov_pivot))
            fig.add_trace(
                go.Bar(
                    x=vals, y=prov_pivot.index, orientation="h", name=gender,
                    marker=dict(color=GENDER_COLORS[gender], line=dict(width=0)),
                    hovertemplate="<b>%{y}</b><br>" + gender + ": %{x:,.0f}<extra></extra>",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=prov_pivot["total"], y=prov_pivot.index, mode="text",
                text=[fmt_short(v) for v in prov_pivot["total"]],
                textposition="middle right", textfont=dict(size=9.5, color="#475569"),
                showlegend=False, hoverinfo="skip",
            )
        )
        fig.update_layout(barmode="stack", xaxis_range=[0, prov_pivot["total"].max() * 1.17])
        fig.update_xaxes(tickformat="~s")
        chart(polish(fig, height=480, showlegend=True, title="12 provinsi dengan pendidik terbanyak"))

    with col_d:
        section("⚖️", "Proporsi pendidik perempuan", "8 provinsi tertinggi & 8 terendah")
        share = df.groupby(["provinsi", "gender"])["jumlah"].sum().unstack(fill_value=0)
        share["total"] = share.sum(axis=1)
        share["female_pct"] = share.get("Perempuan", 0) / share["total"] * 100
        share = share.dropna(subset=["female_pct"])
        if len(share) > 16:
            share = pd.concat([share.nlargest(8, "female_pct"), share.nsmallest(8, "female_pct")])
        share = share.drop_duplicates().sort_values("female_pct", ascending=True)
        share.index = [prov_name(p) for p in share.index]
        colors = [PINK if v >= 50 else BLUE for v in share["female_pct"]]
        fig = go.Figure(
            go.Bar(
                x=share["female_pct"], y=share.index, orientation="h",
                marker=dict(color=colors, line=dict(width=0)),
                text=[fmt_pct(v, 1) for v in share["female_pct"]],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=9.5, color="#334155"),
                hovertemplate="<b>%{y}</b><br>Perempuan: %{x:.2f}%<extra></extra>",
            )
        )
        add_reference_line(fig, 50, "50%", color="#0F172A")
        fig.update_xaxes(range=[0, 105], ticksuffix="%")
        fig.update_layout(margin=dict(l=8, r=52, t=48, b=8))
        chart(polish(fig, height=480, title="Persentase pendidik perempuan menurut provinsi"))

    with st.expander("🧭 Eksplorasi lanjutan: peta treemap wilayah → jenjang"):
        tree = df.groupby(["region", "jenjang", "gender"])["jumlah"].sum().unstack(fill_value=0)
        tree["total"] = tree.sum(axis=1)
        tree["female_share"] = tree.get("Perempuan", 0) / tree["total"] * 100
        tree = tree.reset_index()
        tree["Wilayah"] = tree["region"]
        tree["Jenjang"] = tree["jenjang"]
        tree["total_short"] = tree["total"].map(fmt_short)
        fig = px.treemap(
            tree, path=["Wilayah", "Jenjang"], values="total",
            color="female_share",
            color_continuous_scale=[[0, "#2563EB"], [0.5, "#E2E8F0"], [1, "#EC4899"]],
            range_color=(0, 100),
            custom_data=["total_short", "female_share"],
            labels={"total": "Jumlah pendidik", "female_share": "% perempuan"},
        )
        fig.update_traces(
            textinfo="label+text",
            texttemplate="<b>%{label}</b><br>%{customdata[0]}",
            hovertemplate="<b>%{label}</b><br>Pendidik: %{customdata[0]}<br>"
                          "Perempuan: %{customdata[1]:.1f}%<extra></extra>",
            marker=dict(line=dict(width=2, color="#ffffff")),
            root=dict(color="#F8FAFC"),
            pathbar=dict(visible=False),
        )
        fig.update_layout(coloraxis_colorbar=dict(title="% perempuan", thickness=10, len=0.6))
        chart(polish(fig, height=520, title="Sebaran pendidik: wilayah → jenjang (warna = proporsi perempuan)"))

    with st.expander("📋 Lihat tabel lengkap & unduh data pendidik"):
        table = TEACHER_WIDE.copy()
        table["Total"] = table.sum(axis=1)
        table["% Perempuan"] = 0.0
        for prov in table.index:
            sub = TCH[(TCH["provinsi"] == prov)]
            tot = sub["jumlah"].sum()
            table.loc[prov, "% Perempuan"] = (
                sub.loc[sub["gender"] == "Perempuan", "jumlah"].sum() / tot * 100 if tot else np.nan
            )
        table = table.reset_index()
        table["Provinsi"] = table["provinsi"].map(prov_name)
        table["Wilayah"] = table["provinsi"].map(PROVINCE_REGION)
        table = table[["Provinsi", "Wilayah", *TEACHER_LEVELS, "Total", "% Perempuan"]].sort_values("Provinsi")
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={
                **{l: st.column_config.NumberColumn(l, format="%d", width="small") for l in TEACHER_LEVELS},
                "Total": st.column_config.NumberColumn("Total", format="%d"),
                "% Perempuan": st.column_config.ProgressColumn(
                    "% Perempuan", min_value=0, max_value=100, format="%.1f%%"
                ),
            },
        )
        st.download_button(
            "⬇️ Unduh CSV pendidik (pivot jenjang)",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="pendidik_provinsi_2025.csv",
            mime="text/csv", key="dl_tch",
        )

    if level_focus != "Semua jenjang":
        focus_df = df[df["jenjang"] == level_focus]
        f_total = float(focus_df["jumlah"].sum())
        f_female = float(focus_df.loc[focus_df["gender"] == "Perempuan", "jumlah"].sum())
        callout(
            f"Pada jenjang <b>{level_focus}</b> di wilayah terpilih terdapat <b>{fmt_num(f_total)}</b> pendidik, "
            f"dengan <b>{fmt_pct(f_female / f_total * 100 if f_total else np.nan, 1)}</b> perempuan. "
            "Gunakan filter jenjang di atas untuk menyorot jenjang lain.",
            "info",
        )


# =============================================================================
# HALAMAN: PERBANDINGAN
# =============================================================================
def render_compare():
    hero(
        "Lintas dataset · Perbandingan indikator",
        "Bagaimana partisipasi, penyelesaian, dan pendidik saling terkait?",
        "Halaman ini menggabungkan ketiga dataset pada level provinsi. Karena tahun data berbeda "
        "(APS 2025, penyelesaian 2023, pendidik 2025), hasilnya bersifat indikatif — bukan hubungan sebab-akibat.",
        ["Gabungan provinsi", "Analisis korelasi", "Skor gabungan"],
        compact=True,
    )

    with st.container(border=True):
        f1, f2, f3 = st.columns([1.2, 1.1, 1.6], gap="medium")
        age_focus = f1.selectbox(
            "Indikator APS", AGE_ORDER, index=2,
            format_func=lambda a: AGE_DISPLAY[a], key="cmp_age",
        )
        level_focus = f2.selectbox(
            "Indikator penyelesaian", LEVELS, index=2,
            format_func=lambda l: f"Selesai {l}", key="cmp_level",
        )
        selected_regions = f3.multiselect(
            "Wilayah", REGION_ORDER, default=REGION_ORDER, key="cmp_regions", wrap=True,
        )

    if not selected_regions:
        selected_regions = REGION_ORDER
    df = MASTER[MASTER["region"].isin(selected_regions)].copy()
    pair = df.dropna(subset=[age_focus, level_focus, "Total Pendidik"]).copy()

    if len(pair) < 3:
        callout("Data pasangan indikator tidak cukup untuk dianalisis pada filter ini.", "warn")
        return

    x = pair[age_focus].to_numpy(dtype=float)
    y = pair[level_focus].to_numpy(dtype=float)
    r = float(np.corrcoef(x, y)[0, 1])
    strength = (
        "sangat kuat" if abs(r) >= 0.8 else "kuat" if abs(r) >= 0.6
        else "sedang" if abs(r) >= 0.4 else "lemah" if abs(r) >= 0.2 else "sangat lemah"
    )
    direction = "positif" if r >= 0 else "negatif"

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        kpi("Provinsi dianalisis", f"{len(pair)}", f"Dari {len(df)} provinsi pada filter", BLUE, "📍")
    with c2:
        kpi("Koefisien korelasi", f"{r:.2f}".replace(".", ","), f"Hubungan {direction} {strength}", TEAL if r >= 0 else "#EF4444", "📈")
    with c3:
        top_pair = pair.loc[pair[level_focus].idxmax()]
        kpi(
            f"Tertinggi · Selesai {level_focus}", fmt_pct(top_pair[level_focus]),
            f"APS {AGE_DISPLAY[age_focus]}: {fmt_pct(top_pair[age_focus])}", AMBER, "🏅",
        )

    section(
        "🔵", "Partisipasi vs penyelesaian",
        f"Ukuran gelembung = total pendidik · APS {AGE_DISPLAY[age_focus]} (2025) vs penyelesaian {level_focus} (2023)",
    )
    col_a, col_b = st.columns([1.55, 1], gap="large")

    with col_a:
        fig = px.scatter(
            pair, x=age_focus, y=level_focus,
            size="Total Pendidik", color="region", hover_name="Provinsi",
            size_max=34,
            color_discrete_map=REGION_COLORS,
            labels={age_focus: f"APS {AGE_DISPLAY[age_focus]} (%)", level_focus: f"Penyelesaian {level_focus} (%)", "region": "Wilayah"},
            category_orders={"region": REGION_ORDER},
            hover_data={age_focus: ":.2f", level_focus: ":.2f", "Total Pendidik": ":,.0f"},
        )
        fig.update_traces(marker=dict(line=dict(width=1.5, color="#ffffff"), opacity=0.88))
        coef = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 60)
        fig.add_trace(
            go.Scatter(
                x=xs, y=np.polyval(coef, xs), mode="lines", name="Garis tren",
                line=dict(color="#94A3B8", width=2, dash="dash"),
                hoverinfo="skip", showlegend=True,
            )
        )
        mean_x, mean_y = float(np.mean(x)), float(np.mean(y))
        fig.add_vline(x=mean_x, line_width=1, line_dash="dot", line_color="#CBD5E1")
        fig.add_hline(y=mean_y, line_width=1, line_dash="dot", line_color="#CBD5E1")
        fig.add_annotation(x=mean_x, y=1.02, yref="paper", text=f"rata-rata APS {fmt_pct(mean_x, 1)}",
                           showarrow=False, font=dict(size=9, color="#94A3B8"))
        fig.add_annotation(x=1.01, xref="paper", y=mean_y, text=f"rata-rata {fmt_pct(mean_y, 1)}",
                           showarrow=False, font=dict(size=9, color="#94A3B8"), textangle=90)
        label_rows = pd.concat([
            pair.nlargest(1, level_focus), pair.nsmallest(1, level_focus),
            pair.nlargest(1, age_focus), pair.nsmallest(1, age_focus),
            pair.nlargest(1, "Total Pendidik"),
        ]).drop_duplicates(subset=["provinsi"])
        for _, row in label_rows.iterrows():
            fig.add_annotation(
                x=row[age_focus], y=row[level_focus], text=row["Provinsi"],
                showarrow=False, yshift=15,
                font=dict(size=9, color="#334155"),
                bgcolor="rgba(255,255,255,.78)", borderpad=2,
            )
        fig.update_layout(margin=dict(l=8, r=20, t=58, b=8))
        chart(polish(fig, height=560, showlegend=True, title="Sebaran provinsi: partisipasi, penyelesaian, dan jumlah pendidik"))

    with col_b:
        section("🧮", "Matriks korelasi", "Pearson · semua indikator numerik")
        corr_cols = {
            "7-12": "APS 7–12",
            "13-15": "APS 13–15",
            "16-18": "APS 16–18",
            "19-23": "APS 19–23",
            "SD": "Selesai SD",
            "SMP": "Selesai SMP",
            "SMA": "Selesai SMA",
            "Total Pendidik": "Total pendidik",
        }
        corr = MASTER[list(corr_cols)].dropna().corr()
        labels = [corr_cols[c] for c in corr.columns]
        fig = go.Figure(
            go.Heatmap(
                z=corr.to_numpy(), x=labels, y=labels,
                colorscale=[[0, "#FCA5A5"], [0.35, "#FEE2E2"], [0.5, "#F8FAFC"], [0.65, "#DBEAFE"], [1, "#93C5FD"]],
                zmin=-1, zmax=1,
                text=[[f"{v:.2f}".replace(".", ",") for v in row] for row in corr.to_numpy()],
                texttemplate="%{text}", textfont=dict(size=8.2, color="#0F172A"),
                xgap=2, ygap=2,
                colorbar=dict(title=dict(text="r", font=dict(size=10)), thickness=9, len=0.55),
                hovertemplate="%{y} × %{x}<br>r = <b>%{text}</b><extra></extra>",
            )
        )
        fig.update_yaxes(autorange="reversed", tickfont=dict(size=9))
        fig.update_xaxes(tickfont=dict(size=9), tickangle=-38, side="bottom")
        chart(polish(fig, height=560, title="Korelasi antarindikator pendidikan"))

    callout(
        f"Korelasi antara <b>APS {AGE_DISPLAY[age_focus]}</b> dan <b>penyelesaian {level_focus}</b> pada "
        f"{len(pair)} provinsi adalah <b>r = {r:.2f}</b> ({direction} {strength}). "
        "Angka ini menggambarkan kedekatan pola, bukan bukti sebab-akibat. Perbedaan tahun dan cakupan data "
        "perlu diperhitungkan saat menafsirkan.",
        "info",
    )

    section(
        "🏆", "Skor gabungan pendidikan (ilustratif)",
        "Rata-rata peringkat persentil APS 16–18, APS 19–23, dan penyelesaian SMA",
    )
    score = MASTER.dropna(subset=["16-18", "19-23", "SMA"]).copy()
    for col in ["16-18", "19-23", "SMA"]:
        score[f"rank_{col}"] = score[col].rank(pct=True) * 100
    score["Skor"] = score[[f"rank_{c}" for c in ["16-18", "19-23", "SMA"]]].mean(axis=1)
    score = score.sort_values("Skor", ascending=False)
    top_score = score.head(12).sort_values("Skor", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=top_score["Skor"], y=top_score["Provinsi"], orientation="h",
            marker=dict(color=sample_colorscale(TEAL_SCALE, np.linspace(0.35, 1, len(top_score))), line=dict(width=0)),
            text=[f"{v:.1f}".replace(".", ",") for v in top_score["Skor"]],
            textposition="outside", cliponaxis=False,
            textfont=dict(size=10, color="#334155"),
            customdata=np.stack([
                top_score["16-18"], top_score["19-23"], top_score["SMA"]
            ], axis=-1),
            hovertemplate="<b>%{y}</b><br>Skor: %{x:.1f}<br>"
                          "APS 16–18: %{customdata[0]:.2f}%<br>APS 19–23: %{customdata[1]:.2f}%<br>"
                          "Selesai SMA: %{customdata[2]:.2f}%<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 108])
    fig.update_layout(margin=dict(l=8, r=50, t=48, b=8))
    chart(polish(fig, height=470, title="12 provinsi dengan skor gabungan tertinggi"))

    callout(
        "Skor gabungan dihitung dari rata-rata <b>peringkat persentil</b> tiga indikator: APS 16–18, APS 19–23, "
        "dan penyelesaian SMA. Skor ini hanya alat bantu perbandingan relatif, bukan indeks resmi; "
        "bobot setiap indikator dibuat sama.",
        "warn",
    )

    with st.expander("📋 Lihat peringkat lengkap skor gabungan"):
        table = score[["Provinsi", "region", "16-18", "19-23", "SMA", "Skor"]].copy()
        table = table.rename(columns={
            "region": "Wilayah", "16-18": "APS 16–18", "19-23": "APS 19–23", "SMA": "Selesai SMA",
        })
        st.dataframe(
            table, hide_index=True, width="stretch",
            column_config={
                "APS 16–18": st.column_config.NumberColumn(format="%.2f"),
                "APS 19–23": st.column_config.NumberColumn(format="%.2f"),
                "Selesai SMA": st.column_config.NumberColumn(format="%.2f"),
                "Skor": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
            },
        )
        st.download_button(
            "⬇️ Unduh CSV skor gabungan",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="skor_gabungan_pendidikan.csv",
            mime="text/csv", key="dl_score",
        )


# =============================================================================
# HALAMAN: DATA & UNDUH
# =============================================================================
def render_data():
    hero(
        "Transparansi data",
        "Data, definisi, dan unduhan",
        "Semua visualisasi pada dasbor ini dibangun langsung dari tiga file Excel sumber. "
        "Tabel di bawah adalah versi bersih yang siap diunduh untuk analisis lanjutan.",
        ["3 dataset", "38 provinsi", "2023–2025"],
        compact=True,
    )

    total_teacher = float(TCH["jumlah"].sum())
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        kpi("Provinsi", "38", "Cakupan seluruh Indonesia", BLUE, "📍")
    with c2:
        kpi("Dataset", "3", "APS · Penyelesaian · Pendidik", TEAL, "🗂️")
    with c3:
        kpi("Rentang tahun", "2023–2025", "Tahun terbaru tiap dataset", AMBER, "📅")
    with c4:
        kpi("Total pendidik", fmt_short(total_teacher), "Pendidik & tenaga kependidikan", PURPLE, "👥")

    tab1, tab2, tab3 = st.tabs(["🎒 APS 2025", "🎓 Penyelesaian 2023", "👩‍🏫 Pendidik 2025"])

    with tab1:
        section("🎒", "Angka Partisipasi Sekolah menurut provinsi", "Kelompok umur 7–12, 13–15, 16–18, dan 19–23 tahun")
        table = MASTER[["Provinsi", "region", *AGE_ORDER]].rename(columns={"region": "Wilayah", **AGE_DISPLAY})
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button(
            "⬇️ Unduh CSV APS",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="aps_provinsi_2025.csv", mime="text/csv", key="data_aps",
        )
        st.caption(
            "Definisi: APS adalah proporsi penduduk kelompok umur tertentu yang masih bersekolah "
            "terhadap jumlah penduduk kelompok umur tersebut. Nilai dalam persen."
        )

    with tab2:
        section("🎓", "Tingkat Penyelesaian Pendidikan menurut provinsi", "Jenjang SD, SMP, dan SMA/sederajat")
        table = MASTER[["Provinsi", "region", *LEVELS]].rename(
            columns={"region": "Wilayah", **{l: f"Selesai {l}" for l in LEVELS}}
        )
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button(
            "⬇️ Unduh CSV penyelesaian pendidikan",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="penyelesaian_pendidikan_2023.csv", mime="text/csv", key="data_comp",
        )
        st.caption(
            "Catatan: tanda kosong berarti data belum tersedia (empat provinsi baru di Papua). "
            "Nilai tidak diimputasi. Tahun data: 2023."
        )

    with tab3:
        section("👩‍🏫", "Pendidik & tenaga kependidikan menurut provinsi & jenjang", "Jumlah laki-laki + perempuan")
        table = TEACHER_WIDE.copy()
        table["Total"] = table.sum(axis=1)
        table["% Perempuan"] = 0.0
        for prov in table.index:
            sub = TCH[TCH["provinsi"] == prov]
            tot = sub["jumlah"].sum()
            table.loc[prov, "% Perempuan"] = (
                sub.loc[sub["gender"] == "Perempuan", "jumlah"].sum() / tot * 100 if tot else np.nan
            )
        table = table.reset_index()
        table["Provinsi"] = table["provinsi"].map(prov_name)
        table["Wilayah"] = table["provinsi"].map(PROVINCE_REGION)
        table = table[["Provinsi", "Wilayah", *TEACHER_LEVELS, "Total", "% Perempuan"]].sort_values("Provinsi")
        st.dataframe(table, hide_index=True, width="stretch")
        st.download_button(
            "⬇️ Unduh CSV pendidik",
            data=table.to_csv(index=False).encode("utf-8-sig"),
            file_name="pendidik_provinsi_2025.csv", mime="text/csv", key="data_tch",
        )
        with st.expander("Lihat data panjang per gender"):
            long_table = TCH[["provinsi", "jenjang", "gender", "jumlah"]].copy()
            long_table["Provinsi"] = long_table["provinsi"].map(prov_name)
            long_table = long_table.rename(columns={"jenjang": "Jenjang", "gender": "Jenis Kelamin", "jumlah": "Jumlah"})
            long_table = long_table[["Provinsi", "Jenjang", "Jenis Kelamin", "Jumlah"]].sort_values(
                ["Provinsi", "Jenjang", "Jenis Kelamin"]
            )
            st.dataframe(long_table, hide_index=True, width="stretch", height=380)
            st.download_button(
                "⬇️ Unduh CSV data panjang pendidik",
                data=long_table.to_csv(index=False).encode("utf-8-sig"),
                file_name="pendidik_long_2025.csv", mime="text/csv", key="data_tch_long",
            )
        st.caption(
            "Jenjang: TK, KB, TPA, SPS, SD, SMP, SMA, SMK, dan SLB. "
            "Total merupakan penjumlahan pendidik laki-laki dan perempuan."
        )

    section("📚", "Sumber & catatan metodologi")
    callout(
        f"<b>File sumber:</b><br>"
        f"• {DATA['files']['aps']}<br>"
        f"• {DATA['files']['comp']}<br>"
        f"• {DATA['files']['teacher']}<br>"
        f"• {DATA['files']['geo']} (batas administrasi provinsi, CC BY 4.0)<br><br>"
        "Seluruh angka diambil apa adanya dari file Excel. Nama provinsi diseragamkan agar dapat digabungkan "
        "(contoh: D.K.I. Jakarta → DKI Jakarta, Kepulauan Riau → Kep. Riau).",
        "info",
    )
    callout(
        "<b>Perhatian dalam membandingkan:</b> APS dan data pendidik berasal dari tahun 2025, sedangkan "
        "penyelesaian pendidikan dari tahun 2023. Empat provinsi baru di Papua belum tersedia pada dataset "
        "penyelesaian. Perbandingan lintas dataset bersifat indikatif dan tidak menunjukkan hubungan sebab-akibat.",
        "warn",
    )


# =============================================================================
# NAVIGASI UTAMA
# =============================================================================
PAGES = {
    "🏠  Ringkasan": render_overview,
    "🗺️  Peta Indonesia": render_map,
    "🎒  Partisipasi Sekolah": render_aps,
    "🎓  Penyelesaian Pendidikan": render_completion,
    "👩‍🏫  Pendidik & Tenaga Kependidikan": render_teachers,
    "🔗  Perbandingan Indikator": render_compare,
    "🗂️  Data & Unduh": render_data,
}

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-mark">🎓</div>
            <div>
                <div class="brand-name">EduScope ID</div>
                <div class="brand-sub">Dasbor Pendidikan Indonesia</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:.68rem;font-weight:700;letter-spacing:.12em;color:#6B7C93;'
        'text-transform:uppercase;padding:0 8px 7px;">Navigasi</div>',
        unsafe_allow_html=True,
    )
    selected_page = st.radio("Navigasi", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.markdown(
        """
        <div class="side-note">
            <div style="margin-bottom:7px;"><b>📌 Cakupan data</b></div>
            <div><span class="side-dot" style="background:#3B82F6;"></span>38 provinsi</div>
            <div><span class="side-dot" style="background:#0EA5E9;"></span>APS 2025</div>
            <div><span class="side-dot" style="background:#F59E0B;"></span>Penyelesaian 2023</div>
            <div><span class="side-dot" style="background:#8B5CF6;"></span>Pendidik 2025</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Sumber: file Excel Portal Data Kementerian Pendidikan. Dasbor dibangun dengan Streamlit + Plotly.")

PAGES[selected_page]()
