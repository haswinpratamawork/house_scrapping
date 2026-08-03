# Jabodetabek Administrative Regions — Scraping Checklist

> Reference + progress tracker for scraping coverage: every **province → city/regency →
> district (kecamatan)** in the Jabodetabek area. "Jabodetabek" = **Ja**karta, **Bo**gor,
> **De**pok, **Ta**ngerang, **Bek**asi, spanning parts of **3 provinces**.
>
> District lists for the three large regencies (Kab. Bogor, Bekasi, Tangerang) were verified
> against Wikipedia (2026-06). Last updated: 2026-06-04.

## How to read this

- `- [ ]` district not yet scraped · `- [x]` district scraped (with active listing count + date)
- Scraped per district via `…/jual/{city}/{district}/{type}/` across all property types
  (rumah, apartemen, tanah, ruko, gudang).
- District **slug** = name lowercased with spaces → hyphens (e.g. "Sawah Besar" → `sawah-besar`).

## Summary

| Province | City / Regency | Type | Kecamatan | Rumah123 city slug |
|----------|----------------|------|-----------|--------------------|
| DKI Jakarta | Jakarta Pusat | Kota | 8 | `jakarta-pusat` |
| DKI Jakarta | Jakarta Utara | Kota | 6 | `jakarta-utara` |
| DKI Jakarta | Jakarta Barat | Kota | 8 | `jakarta-barat` |
| DKI Jakarta | Jakarta Selatan | Kota | 10 | `jakarta-selatan` |
| DKI Jakarta | Jakarta Timur | Kota | 10 | `jakarta-timur` |
| DKI Jakarta | Kepulauan Seribu | Kab. | 2 | `kepulauan-seribu` |
| Jawa Barat | Kota Bogor | Kota | 6 | `bogor` |
| Jawa Barat | Kabupaten Bogor | Kab. | 40 | `bogor` (shared with Kota Bogor) |
| Jawa Barat | Kota Depok | Kota | 11 | `depok` |
| Jawa Barat | Kota Bekasi | Kota | 12 | `bekasi` |
| Jawa Barat | Kabupaten Bekasi | Kab. | 23 | `kabupaten-bekasi` |
| Banten | Kota Tangerang | Kota | 13 | `tangerang` |
| Banten | Kota Tangerang Selatan | Kota | 7 | `tangerang-selatan` |
| Banten | Kabupaten Tangerang | Kab. | 29 | `kabupaten-tangerang` |

**Total: 3 provinces · 14 cities/regencies · 185 kecamatan**

> **Slug note:** `kabupaten-bogor` does **not** exist on Rumah123 (404) — Kabupaten Bogor
> districts live under the same `bogor` city slug as Kota Bogor. The `kabupaten-bekasi` and
> `kabupaten-tangerang` slugs are still unconfirmed; verify before scraping those. Confirm a
> slug by `totalCount` > 0, not HTTP 200 — a wrong slug can soft-404 with a live 200 page.

---

## DKI Jakarta (province)

### Jakarta Pusat — `jakarta-pusat` (8 kecamatan)
- [x] Gambir — 672 active listings (2026-06-04)
- [x] Sawah Besar — 528 active listings (2026-06-04)
- [x] Kemayoran — 2,519 active listings (2026-06-05)
- [x] Senen — 1,183 active listings (2026-06-05)
- [x] Cempaka Putih — 1,723 active listings (2026-06-06)
- [x] Menteng — 1,937 active listings (2026-06-06)
- [x] Tanah Abang — 1,618 active listings (2026-06-07)
- [x] Johar Baru — 357 active listings (2026-06-05)

### Jakarta Utara — `jakarta-utara` (6 kecamatan)
- [x] Penjaringan — 1,866 active listings (2026-06-07)
- [x] Pademangan — 1,755 active listings (2026-06-08)
- [x] Tanjung Priok — 1,173 active listings (2026-06-08)
- [x] Koja — 402 active listings (2026-06-08)
- [x] Kelapa Gading — 3,015 active listings (2026-06-08)
- [x] Cilincing — 1,161 active listings (2026-06-08)

### Jakarta Barat — `jakarta-barat` (8 kecamatan)
- [x] Cengkareng — 7,101 active listings (2026-06-09)
- [x] Grogol Petamburan — 1,033 active listings (2026-06-10)
- [x] Tamansari — 956 active listings (2026-06-11)
- [x] Tambora — 1,025 active listings (2026-06-11)
- [x] Kebon Jeruk — 4,878 active listings (2026-06-12)
- [x] Kalideres — 6,312 active listings (2026-06-15)
- [x] Palmerah — 1,006 active listings (2026-06-15)
- [x] Kembangan — 3,335 active listings (2026-06-15)

### Jakarta Selatan — `jakarta-selatan` (10 kecamatan)
- [x] Tebet — 4,591 active listings (2026-06-17)
- [x] Setiabudi — 4,167 active listings (2026-06-17)
- [x] Mampang Prapatan — 1,972 active listings (2026-06-18)
- [x] Pasar Minggu — 2,442 active listings (2026-06-20)
- [x] Kebayoran Lama — 2,886 active listings (2026-06-21)
- [x] Cilandak — 1,428 active listings (2026-06-22)
- [x] Pesanggrahan — 3,116 active listings (2026-06-23)
- [x] Kebayoran Baru — 6,046 active listings (2026-06-26)
- [x] Pancoran — 1,943 active listings (2026-06-26)
- [x] Jagakarsa — 2,769 active listings (2026-06-27)

### Jakarta Timur — `jakarta-timur` (10 kecamatan)
- [x] Matraman — 238 active listings (2026-06-29)
- [x] Pulogadung — 2,047 active listings (2026-06-30)
- [x] Jatinegara — 1,133 active listings (2026-07-01)
- [x] Kramat Jati — 833 active listings (2026-07-06)
- [x] Pasar Rebo — 510 active listings (2026-07-06)
- [x] Cakung — 8,771 active listings (2026-07-08)
- [x] Duren Sawit — 1,652 active listings (2026-07-09)
- [x] Makasar — 164 active listings (2026-07-09)
- [x] Ciracas — 1,190 active listings (2026-07-10)
- [x] Cipayung — 1,954 active listings (2026-07-11)

### Kepulauan Seribu — `kepulauan-seribu` (2 kecamatan)
- [x] Kepulauan Seribu Utara — 20 active listings (2026-06-07)
- [x] Kepulauan Seribu Selatan — 5 active listings (2026-06-07)

---

## Jawa Barat (West Java) — Jabodetabek portion

### Kota Bogor — `bogor` (6 kecamatan)
- [x] Bogor Selatan — 797 active listings (2026-07-28)
- [x] Bogor Timur — 668 active listings (2026-07-29)
- [x] Bogor Utara — 647 active listings (2026-07-29)
- [x] Bogor Tengah — 549 active listings (2026-07-31)
- [x] Bogor Barat — 1,942 active listings (2026-08-01)
- [x] Tanah Sareal — 1,562 active listings (2026-08-02)

### Kabupaten Bogor — `bogor` (40 kecamatan)
- [x] Nanggung — 9 active listings (2026-08-03)
- [x] Leuwiliang — 108 active listings (2026-08-03)
- [x] Leuwisadeng — 34 active listings (2026-08-03)
- [ ] Pamijahan
- [ ] Cibungbulang
- [ ] Ciampea
- [ ] Tenjolaya
- [ ] Dramaga
- [ ] Ciomas
- [ ] Tamansari
- [ ] Cijeruk
- [ ] Cigombong
- [ ] Caringin
- [ ] Ciawi
- [ ] Cisarua
- [ ] Megamendung
- [ ] Sukaraja
- [ ] Babakan Madang
- [ ] Sukamakmur
- [ ] Cariu
- [ ] Tanjungsari
- [ ] Jonggol
- [ ] Cileungsi
- [ ] Klapanunggal
- [ ] Gunung Putri
- [ ] Citeureup
- [ ] Cibinong
- [ ] Bojonggede
- [ ] Tajurhalang
- [ ] Kemang
- [ ] Rancabungur
- [ ] Parung
- [ ] Ciseeng
- [ ] Gunungsindur
- [ ] Rumpin
- [ ] Cigudeg
- [ ] Sukajaya
- [ ] Jasinga
- [ ] Tenjo
- [ ] Parung Panjang

### Kota Depok — `depok` (11 kecamatan)
- [x] Sawangan — 3,205 active listings (2026-07-12)
- [x] Bojongsari — 682 active listings (2026-07-12) · slug `bojong-sari`
- [x] Pancoran Mas — 1,657 active listings (2026-07-13)
- [x] Cipayung — 554 active listings (2026-07-15)
- [x] Sukmajaya — 1,358 active listings (2026-07-17)
- [x] Cilodong — 1,419 active listings (2026-07-17)
- [x] Cimanggis — 2,434 active listings (2026-07-18)
- [x] Tapos — 1,036 active listings (2026-07-18)
- [x] Beji — 1,338 active listings (2026-07-18)
- [x] Limo — 1,237 active listings (2026-07-22)
- [x] Cinere — 6,463 active listings (2026-07-27)

### Kota Bekasi — `bekasi` (12 kecamatan)
- [ ] Pondok Gede
- [ ] Jati Sampurna
- [ ] Pondok Melati
- [ ] Jati Asih
- [ ] Bantar Gebang
- [ ] Mustika Jaya
- [ ] Bekasi Timur
- [ ] Rawalumbu
- [ ] Bekasi Selatan
- [ ] Bekasi Barat
- [ ] Medan Satria
- [ ] Bekasi Utara

### Kabupaten Bekasi — `kabupaten-bekasi` (23 kecamatan)
- [ ] Setu
- [ ] Serang Baru
- [ ] Cikarang Pusat
- [ ] Cikarang Selatan
- [ ] Cibarusah
- [ ] Bojongmangu
- [ ] Cikarang Timur
- [ ] Kedungwaringin
- [ ] Cikarang Utara
- [ ] Karangbahagia
- [ ] Cibitung
- [ ] Cikarang Barat
- [ ] Tambun Selatan
- [ ] Tambun Utara
- [ ] Babelan
- [ ] Tarumajaya
- [ ] Tambelang
- [ ] Sukawangi
- [ ] Sukatani
- [ ] Sukakarya
- [ ] Pebayuran
- [ ] Cabangbungin
- [ ] Muara Gembong

---

## Banten — Jabodetabek portion

### Kota Tangerang — `tangerang` (13 kecamatan)
- [ ] Ciledug
- [ ] Larangan
- [ ] Karang Tengah
- [ ] Cipondoh
- [ ] Pinang
- [ ] Tangerang
- [ ] Karawaci
- [ ] Jatiuwung
- [ ] Cibodas
- [ ] Periuk
- [ ] Batuceper
- [ ] Neglasari
- [ ] Benda

### Kota Tangerang Selatan — `tangerang-selatan` (7 kecamatan)
- [ ] Serpong
- [ ] Serpong Utara
- [ ] Pondok Aren
- [ ] Ciputat
- [ ] Ciputat Timur
- [ ] Pamulang
- [ ] Setu

### Kabupaten Tangerang — `kabupaten-tangerang` (29 kecamatan)
- [ ] Balaraja
- [ ] Jayanti
- [ ] Tigaraksa
- [ ] Jambe
- [ ] Cisoka
- [ ] Solear
- [ ] Kronjo
- [ ] Mekarbaru
- [ ] Mauk
- [ ] Kemiri
- [ ] Sukadiri
- [ ] Rajeg
- [ ] Sepatan
- [ ] Sepatan Timur
- [ ] Pakuhaji
- [ ] Teluknaga
- [ ] Kosambi
- [ ] Pasar Kemis
- [ ] Cikupa
- [ ] Panongan
- [ ] Curug
- [ ] Cisauk
- [ ] Pagedangan
- [ ] Legok
- [ ] Kelapa Dua
- [ ] Sindang Jaya
- [ ] Sukamulya
- [ ] Kresek
- [ ] Gunung Kaler
