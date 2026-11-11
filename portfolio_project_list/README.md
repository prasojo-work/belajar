# Portofolio — Prasojo Jiwandono

Static portfolio page, tanpa build step dan tanpa framework. Cukup buka
`index.html` di browser, atau host folder ini di GitHub Pages / Vercel / Netlify.

## Isi folder

```
.
├── index.html                 # seluruh konten halaman
├── favicon.svg
├── portfolio_project.txt      # catatan sumber link project
└── assets/
    ├── css/style.css
    ├── js/main.js             # menu mobile, header, animasi reveal
    ├── fonts/                 # Inter + Instrument Serif (lokal, tanpa CDN)
    └── img/                   # screenshot project (1440px & 720px)
```

## Cara melihat hasilnya

Buka file `index.html` langsung, atau jalankan server lokal:

```bash
cd portfolio_project_list
python3 -m http.server 8000
```

Lalu buka <http://localhost:8000>.

## Menambah project baru

1. Ambil screenshot project (rasio 16:10, lebar 1440px), simpan ke
   `assets/img/nama-project.jpg`. Buat juga versi 720px bila mau
   (`nama-project-720.jpg`).
2. Buka `index.html`, cari blok `<!-- PROJECT 02 -->`, lalu copy satu
   `<article class="project"> ... </article>`.
3. Ganti:
   - `href` dan `aria-label` pada `project__media` serta judul,
   - `src` / `srcset` gambar dan teks `alt`,
   - nomor (`01`, `02`, ...), kategori, judul, deskripsi, dan tag,
   - link di `project__link`.
4. Perbarui juga angka "Project selesai" di bagian hero dan angka kecil di
   navigasi (`PROJECT 02`) bila perlu.

## Mengubah identitas & kontak

Semua ada di `index.html`:

- Nama dan headline: bagian `HERO`.
- Email: cari `jiwandonoprasojo@gmail.com` (ada di header, hero, project, dan kontak).
- GitHub: cari `github.com/prasojo-work`.
- Teks "Tentang" dan daftar teknologi: bagian `TENTANG`.

## Deploy

**GitHub Pages**

1. Push folder ini ke repository GitHub.
2. Buka Settings → Pages → Deploy from a branch.
3. Pilih branch `main` dan folder `/ (root)`.

**Vercel / Netlify**

Import repository, biarkan build command kosong, dan set output directory ke
folder ini. Keduanya mendukung static HTML tanpa konfigurasi tambahan.

## Catatan

- Font di-host lokal di `assets/fonts`, jadi halaman tetap tampil rapi tanpa
  koneksi ke Google Fonts.
- Sebelum deploy, ganti `og:image` di `<head>` dengan URL absolut (misalnya
  `https://domain-kamu.com/assets/img/eduscope.jpg`) agar preview link di
  media sosial tampil benar.
- Halaman responsif, mendukung keyboard navigation, dan menghormati
  `prefers-reduced-motion`.
- Screenshot project diambil langsung dari situs live pada November 2026.
