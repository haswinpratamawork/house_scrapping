# Jabodetabek Administrative Regions

> Reference for scraping coverage: every **province → city/regency → district (kecamatan)**
> in the Jabodetabek area. "Jabodetabek" = **Ja**karta, **Bo**gor, **De**pok, **Ta**ngerang,
> **Bek**asi, spanning parts of **3 provinces**.
>
> District lists for the three large regencies (Kab. Bogor, Bekasi, Tangerang) were verified
> against Wikipedia (2026-06). Last updated: 2026-06-04.

## Summary

| Province | City / Regency | Type | Kecamatan | Rumah123 city slug |
|----------|----------------|------|-----------|--------------------|
| DKI Jakarta | Jakarta Pusat | Kota | 8 | `jakarta-pusat` |
| DKI Jakarta | Jakarta Utara | Kota | 6 | `jakarta-utara` |
| DKI Jakarta | Jakarta Barat | Kota | 8 | `jakarta-barat` |
| DKI Jakarta | Jakarta Selatan | Kota | 10 | `jakarta-selatan` |
| DKI Jakarta | Jakarta Timur | Kota | 10 | `jakarta-timur` |
| DKI Jakarta | Kepulauan Seribu | Kab. | 2 | _(islands; n/a for housing)_ |
| Jawa Barat | Kota Bogor | Kota | 6 | `bogor` |
| Jawa Barat | Kabupaten Bogor | Kab. | 40 | `kabupaten-bogor` |
| Jawa Barat | Kota Depok | Kota | 11 | `depok` |
| Jawa Barat | Kota Bekasi | Kota | 12 | `bekasi` |
| Jawa Barat | Kabupaten Bekasi | Kab. | 23 | `kabupaten-bekasi` |
| Banten | Kota Tangerang | Kota | 13 | `tangerang` |
| Banten | Kota Tangerang Selatan | Kota | 7 | `tangerang-selatan` |
| Banten | Kabupaten Tangerang | Kab. | 29 | `kabupaten-tangerang` |

**Total: 3 provinces · 14 cities/regencies · 185 kecamatan**
(183 excluding the 2 island kecamatan of Kepulauan Seribu, which are not relevant to housing.)

> **Scraping note:** the current `config.JABODETABEK_CITIES` covers the 10 core kota slugs
> (`bogor`/`bekasi`/`tangerang` resolve to the *kota*). The **kabupaten** of Bogor, Bekasi,
> and Tangerang are separate areas on Rumah123 (slugs likely `kabupaten-bogor`, etc.) and are
> **not yet in the config** — add them when expanding coverage beyond the core cities. Verify
> each kabupaten slug against the live site before relying on it.

---

## DKI Jakarta (province)

### Jakarta Pusat — 8 kecamatan
Gambir · Sawah Besar · Kemayoran · Senen · Cempaka Putih · Menteng · Tanah Abang · Johar Baru

### Jakarta Utara — 6 kecamatan
Penjaringan · Pademangan · Tanjung Priok · Koja · Kelapa Gading · Cilincing

### Jakarta Barat — 8 kecamatan
Cengkareng · Grogol Petamburan · Taman Sari · Tambora · Kebon Jeruk · Kalideres · Palmerah · Kembangan

### Jakarta Selatan — 10 kecamatan
Tebet · Setiabudi · Mampang Prapatan · Pasar Minggu · Kebayoran Lama · Cilandak · Pesanggrahan · Kebayoran Baru · Pancoran · Jagakarsa

### Jakarta Timur — 10 kecamatan
Matraman · Pulogadung · Jatinegara · Kramat Jati · Pasar Rebo · Cakung · Duren Sawit · Makasar · Ciracas · Cipayung

### Kepulauan Seribu — 2 kecamatan
Kepulauan Seribu Utara · Kepulauan Seribu Selatan
*(Island regency, part of DKI Jakarta; not relevant for house-price scraping.)*

---

## Jawa Barat (West Java) — Jabodetabek portion

### Kota Bogor — 6 kecamatan
Bogor Selatan · Bogor Timur · Bogor Utara · Bogor Tengah · Bogor Barat · Tanah Sareal

### Kabupaten Bogor — 40 kecamatan
Nanggung · Leuwiliang · Leuwisadeng · Pamijahan · Cibungbulang · Ciampea · Tenjolaya · Dramaga ·
Ciomas · Tamansari · Cijeruk · Cigombong · Caringin · Ciawi · Cisarua · Megamendung · Sukaraja ·
Babakan Madang · Sukamakmur · Cariu · Tanjungsari · Jonggol · Cileungsi · Klapanunggal ·
Gunung Putri · Citeureup · Cibinong · Bojonggede · Tajurhalang · Kemang · Rancabungur · Parung ·
Ciseeng · Gunungsindur · Rumpin · Cigudeg · Sukajaya · Jasinga · Tenjo · Parung Panjang

### Kota Depok — 11 kecamatan
Sawangan · Bojongsari · Pancoran Mas · Cipayung · Sukmajaya · Cilodong · Cimanggis · Tapos · Beji · Limo · Cinere

### Kota Bekasi — 12 kecamatan
Pondok Gede · Jati Sampurna · Pondok Melati · Jati Asih · Bantar Gebang · Mustika Jaya ·
Bekasi Timur · Rawalumbu · Bekasi Selatan · Bekasi Barat · Medan Satria · Bekasi Utara

### Kabupaten Bekasi — 23 kecamatan
Setu · Serang Baru · Cikarang Pusat · Cikarang Selatan · Cibarusah · Bojongmangu · Cikarang Timur ·
Kedungwaringin · Cikarang Utara · Karangbahagia · Cibitung · Cikarang Barat · Tambun Selatan ·
Tambun Utara · Babelan · Tarumajaya · Tambelang · Sukawangi · Sukatani · Sukakarya · Pebayuran ·
Cabangbungin · Muara Gembong

---

## Banten — Jabodetabek portion

### Kota Tangerang — 13 kecamatan
Ciledug · Larangan · Karang Tengah · Cipondoh · Pinang · Tangerang · Karawaci · Jatiuwung ·
Cibodas · Periuk · Batuceper · Neglasari · Benda

### Kota Tangerang Selatan — 7 kecamatan
Serpong · Serpong Utara · Pondok Aren · Ciputat · Ciputat Timur · Pamulang · Setu

### Kabupaten Tangerang — 29 kecamatan
Balaraja · Jayanti · Tigaraksa · Jambe · Cisoka · Solear · Kronjo · Mekarbaru · Mauk · Kemiri ·
Sukadiri · Rajeg · Sepatan · Sepatan Timur · Pakuhaji · Teluknaga · Kosambi · Pasar Kemis ·
Cikupa · Panongan · Curug · Cisauk · Pagedangan · Legok · Kelapa Dua · Sindang Jaya ·
Sukamulya · Kresek · Gunung Kaler
