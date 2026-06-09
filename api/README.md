# Listing Extractor API

A small HTTP service: given a **Rumah123 listing URL**, it returns the listing's
**luas tanah**, **luas bangunan**, **kode pos**, and **kelurahan**.

- Luas tanah / luas bangunan come straight from the listing page (reusing the `scraper`
  parser).
- Kode pos / kelurahan are **not** in Rumah123's data — they're derived by **reverse
  geocoding** the listing's latitude/longitude via the **Google Maps Geocoding API**.
- Listings with obfuscated/missing coordinates (~6%) return `null` kode_pos/kelurahan
  (we never guess).

## Setup

```bash
pip install -e ".[api]"        # installs fastapi + uvicorn
# add your key to .env:
#   GOOGLE_MAPS_API_KEY=AIza...
```

## Run

```bash
./api/run_api.sh                 # serves on 0.0.0.0:8000 (auto-reload)
./api/run_api.sh 127.0.0.1 9000  # custom host + port
# or directly:
uvicorn api.main:app --reload --port 8000
```

## Use

```bash
curl "http://localhost:8000/extract?url=https://www.rumah123.com/properti/jakarta-pusat/hos41138420/"
```

```json
{
  "luas_tanah": 294.0,
  "luas_bangunan": 482.0,
  "kode_pos": "10410",
  "kelurahan": "Senen"
}
```

Interactive docs: http://localhost:8000/docs · Health check: `GET /health`

## Responses

| Status | Meaning |
|--------|---------|
| 200 | OK (fields may be null if coordinates were unavailable) |
| 400 | `url` is not a rumah123.com listing URL |
| 422 | listing page could not be parsed |
| 502 | listing page could not be fetched |
| 500 | `GOOGLE_MAPS_API_KEY` not set |
