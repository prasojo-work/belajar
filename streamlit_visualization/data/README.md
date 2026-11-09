# Data sumber

| File | Isi | Tahun |
|---|---|---|
| `aps_2025.xlsx` | Angka Partisipasi Sekolah menurut provinsi & kelompok umur | 2025 |
| `penyelesaian_2023.xlsx` | Tingkat Penyelesaian Pendidikan menurut jenjang & provinsi | 2023 |
| `pendidik_2025.xls` | Jumlah Pendidik & Tenaga Kependidikan menurut jenjang & jenis kelamin | 2025 |
| `indonesia_provinces.geojson` | Batas administrasi 38 provinsi Indonesia | — |

Tiga file pertama berasal dari Portal Data Kementerian Pendidikan dan digunakan
apa adanya untuk visualisasi. Nama provinsi diseragamkan di dalam aplikasi
(`D.K.I. Jakarta` → `DKI Jakarta`, `Kepulauan Riau` → `Kep. Riau`, dan
`Daerah Istimewa Yogyakarta` → `DI Yogyakarta`).

## Atribusi batas wilayah

`indonesia_provinces.geojson` berasal dari
[Indonesia GeoJSON & TopoJSON Maps (38 Provinces)](https://github.com/denyherianto/indonesia-geojson-topojson-maps-with-38-provinces)
oleh Deny Herianto, lisensi
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Geometri telah dinormalisasi dengan Shapely (`make_valid` + `normalize`) agar
dapat dirender dengan benar oleh Plotly. Aplikasi menambahkan properti
`PROV_CANON` pada setiap feature GeoJSON agar nama provinsi dapat dicocokkan
dengan dataset pendidikan. Batas wilayah dapat berubah dan sebaiknya
diverifikasi dengan sumber resmi (BIG/Kemendagri) untuk penggunaan formal.
