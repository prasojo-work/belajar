# EduScope ID — Dasbor Pendidikan Indonesia

Dasbor interaktif berbasis **Streamlit + Plotly** yang dibangun dari tiga file Excel:

1. **Angka Partisipasi Sekolah (APS) menurut Provinsi dan Kelompok Umur, 2025**
2. **Tingkat Penyelesaian Pendidikan menurut Jenjang Pendidikan dan Provinsi, 2023**
3. **Jumlah Pendidik dan Tenaga Pendidik menurut Jenjang Pendidikan dan Jenis Kelamin, 2025**

Project ini menggunakan scaffolding [`uv`](https://docs.astral.sh/uv/) (`uv init --package`): dependencies dikelola lewat `pyproject.toml` + `uv.lock`, kode berada di `src/`, dan aplikasi dijalankan lewat entry point CLI.

## Halaman dasbor

| Halaman | Isi |
|---|---|
| 🏠 Ringkasan | KPI nasional, pipeline APS, penyelesaian jenjang, komposisi gender pendidik, dan provinsi teratas/terbawah |
| 🗺️ Peta Indonesia | Choropleth 38 provinsi untuk APS, penyelesaian pendidikan, jumlah pendidik, dan proporsi pendidik perempuan; bisa di-zoom per wilayah |
| 🎒 Partisipasi Sekolah | Peringkat provinsi, distribusi per kelompok umur, rata-rata per wilayah, dan peta panas APS |
| 🎓 Penyelesaian Pendidikan | Peringkat per jenjang, perbandingan SD/SMP/SMA, kesenjangan SD–SMA, dan peta panas |
| 👩‍🏫 Pendidik & Tenaga Kependidikan | Komposisi gender per jenjang, provinsi dengan pendidik terbanyak, proporsi perempuan, dan treemap |
| 🔗 Perbandingan Indikator | Scatter plot lintas dataset, matriks korelasi, dan skor gabungan ilustratif |
| 🗂️ Data & Unduh | Tabel bersih tiap dataset + unduhan CSV |

Semua halaman memiliki filter wilayah, pemilih indikator, dan tabel data yang dapat diunduh.

## Menjalankan

Jika `uv` belum terpasang:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Lalu dari folder project:

```bash
# 1. Masuk ke folder project
cd streamlit_visualization

# 2. Sinkronkan environment & dependencies (sekali saja / setiap ada perubahan)
uv sync

# 3. Jalankan dasbor
uv run eduscope-id
```

Buka `http://localhost:8501` di browser.

Alternatif menjalankan langsung file Streamlit-nya:

```bash
uv run streamlit run src/eduscope_id/app.py
```

Atau lewat module Python:

```bash
uv run python -m eduscope_id
```

### Perintah `uv` yang berguna

```bash
uv add nama-package        # menambah dependency ke pyproject.toml + uv.lock
uv remove nama-package     # menghapus dependency
uv lock                    # memperbarui uv.lock
uv sync --locked           # install persis sesuai uv.lock (cocok untuk CI)
uv run <perintah>          # menjalankan perintah di environment project
```

## Deploy ke Streamlit Community Cloud

1. Commit dan push seluruh project ke GitHub, terutama:
   `pyproject.toml`, `uv.lock`, `streamlit_app.py`, folder `src/`, dan folder `data/`.
2. Buka [share.streamlit.io](https://share.streamlit.io) → **Create app**.
3. Isi repository dan branch, lalu isi **Main file path** sesuai posisi project
   di repository:

   - Jika repository **hanya berisi folder project ini**, isi:

     ```text
     streamlit_app.py
     ```

   - Jika project ini berada di dalam monorepo (misalnya repository root-nya
     `belajar/`), isi:

     ```text
     streamlit_visualization/streamlit_app.py
     ```

   Ini penting: Streamlit Cloud mencari dependency di **folder entrypoint**
   lalu di **root repository**. `uv.lock` harus berada di salah satu lokasi
   tersebut.

4. Buka **Advanced settings** → **Python version**, pilih **3.12** (default
   Community Cloud) atau 3.13. Project ini membutuhkan Python **≥ 3.12**.
5. Klik **Deploy**.

Streamlit Cloud akan otomatis mendeteksi `uv.lock` yang sejajar dengan
`streamlit_app.py` dan menjalankan `uv sync` untuk memasang dependency
(`pandas`, `plotly`, `numpy`, `openpyxl`, `xlrd`, dan Streamlit).
`streamlit_app.py` hanyalah entry point yang menjalankan aplikasi asli di
`src/eduscope_id/app.py`.

Jika masih ada error:

- Buka **Manage app → Logs** untuk melihat pesan asli yang tidak diredaksi.
- `ModuleNotFoundError: No module named 'plotly'` biasanya berarti dependency
  tidak terpasang karena `uv.lock` tidak ditemukan. Pastikan Main file path
  menunjuk ke `streamlit_visualization/streamlit_app.py` (untuk monorepo),
  bukan ke `streamlit_visualization/src/eduscope_id/app.py`.
- Pastikan tidak memilih Python 3.11 atau lebih lama, karena NumPy 2.5
  membutuhkan Python ≥ 3.12.
- Setelah mengubah dependency atau Python version, lakukan **Reboot app**.
- Jangan menambahkan `requirements.txt` selama `uv.lock` masih ada: Community
  Cloud memprioritaskan `uv.lock`. Jika suatu saat perlu fallback ke pip,
  rename/hapus `uv.lock` lalu buat `requirements.txt` dari isi
  `dependencies` di `pyproject.toml`.

## Struktur project

```
streamlit_visualization/
├── pyproject.toml           # metadata project + dependencies
├── uv.lock                  # lockfile dependency
├── .python-version          # versi Python untuk uv
├── streamlit_app.py         # entry point deploy Streamlit Cloud
├── README.md
├── .streamlit/
│   └── config.toml          # tema & konfigurasi server
├── data/
│   ├── aps_2025.xlsx        # Angka Partisipasi Sekolah 2025
│   ├── penyelesaian_2023.xlsx
│   ├── pendidik_2025.xls    # Pendidik & tenaga kependidikan 2025
│   └── indonesia_provinces.geojson  # batas 38 provinsi (CC BY 4.0)
└── src/
    └── eduscope_id/
        ├── __init__.py      # mengekspor main()
        ├── __main__.py      # `python -m eduscope_id`
        ├── cli.py           # entry point `eduscope-id`
        └── app.py           # seluruh UI & visualisasi Streamlit
```

Aplikasi mencari data di `data/`, root project, atau direktori kerja. Jika file Excel disimpan di lokasi lain, arahkan lewat environment variable:

```bash
EDUSCOPE_DATA_DIR=/path/ke/folder/data uv run eduscope-id
```

Nama file sumber tidak perlu diubah: aplikasi juga mengenali nama asli seperti `Angka Partisipasi Sekolah*.xlsx`.

## Catatan data

- Nama provinsi diseragamkan agar bisa digabungkan, misalnya `D.K.I. Jakarta` → `DKI Jakarta` dan `Kepulauan Riau` → `Kep. Riau`.
- Empat provinsi baru di Papua (**Papua Barat Daya, Papua Selatan, Papua Tengah, Papua Pegunungan**) belum memiliki angka penyelesaian pendidikan 2023. Nilainya dibiarkan kosong, tidak diimputasi.
- Perbandingan lintas dataset bersifat **indikatif**, karena APS/pendidik berasal dari 2025 sedangkan penyelesaian pendidikan dari 2023. Korelasi tidak menunjukkan hubungan sebab-akibat.
- Skor gabungan pada halaman Perbandingan adalah rata-rata peringkat persentil tiga indikator dengan bobot sama; ini alat bantu eksplorasi, bukan indeks resmi.

## Lisensi & atribusi batas wilayah

Peta menggunakan file batas administrasi provinsi dari
[**Indonesia GeoJSON & TopoJSON Maps (38 Provinces)**](https://github.com/denyherianto/indonesia-geojson-topojson-maps-with-38-provinces)
oleh Deny Herianto, dengan lisensi
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). File GeoJSON disimpan di
`data/indonesia_provinces.geojson`; batas wilayah tersebut dapat berubah dan
sebaiknya diverifikasi dengan sumber resmi (BIG/Kemendagri) untuk penggunaan formal.

## Kustomisasi cepat

Di bagian atas `src/eduscope_id/app.py` terdapat konstanta yang mudah diubah:

- `BLUE`, `CYAN`, `AMBER`, `TEAL`, `PINK`, `PURPLE` — palet warna
- `AGE_DISPLAY`, `AGE_COLORS` — label dan warna kelompok umur
- `LEVEL_COLORS`, `GENDER_COLORS` — warna jenjang dan gender
- `REGION_ORDER`, `REGION_MEMBERS` — pengelompokan wilayah
- `DISPLAY` — nama provinsi untuk tampilan

## Versi yang diuji

Python 3.12 & 3.13, Streamlit 1.67, pandas 3.1, Plotly 7.1, NumPy 2.5.
