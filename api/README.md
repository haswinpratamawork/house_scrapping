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
pip install -r requirements.txt   # pinned runtime deps (scraper + api)
# or for local dev (editable + test tools): pip install -e ".[dev]"

# add your key to .env:
#   GOOGLE_MAPS_API_KEY=AIza...
```

Dependencies are pinned in [`requirements.txt`](../requirements.txt) (repo root); the
Docker image installs from it.

## Run

Use the launcher script `run_api.sh` (it lives in `api/` but `cd`s to the repo root so
the `api` package and the project `.venv` resolve — run it from the project root):

```bash
./api/run_api.sh                 # serve on 0.0.0.0:8010 with auto-reload (dev)
./api/run_api.sh 127.0.0.1 8010  # custom host + port (positional args)
```

It picks up the project `.venv` automatically and warns if `GOOGLE_MAPS_API_KEY` is empty.

**Arguments / environment variables:**

| | Default | Meaning |
|---|---------|---------|
| arg 1 / `HOST` | `0.0.0.0` | bind host |
| arg 2 / `PORT` | `8010` | bind port |
| `RELOAD` | `1` | `1` = auto-reload on code change (dev); `0` = production |

```bash
RELOAD=0 ./api/run_api.sh             # production mode (no auto-reload)
HOST=127.0.0.1 PORT=8010 ./api/run_api.sh
```

Or run uvicorn directly without the script:

```bash
uvicorn api.main:app --reload --port 8010
```

## Docker

The API imports the `scraper` package, so **build from the repo root** (the Dockerfile
lives in `api/` but needs the whole project as context):

```bash
docker build -f api/Dockerfile -t collateral_scrapping .
docker run -p 8010:8010 -e GOOGLE_MAPS_API_KEY=AIza... collateral_scrapping
```

- Pass the key at **runtime** with `-e GOOGLE_MAPS_API_KEY=...` (it is never baked into the
  image; `.env` is excluded via `.dockerignore`).
- Override the port with `-e PORT=8010` (and map it: `-p 8010:8010`).
- Image is ~310 MB and runs as a non-root user, with a `/health` HEALTHCHECK.

Run it **detached** (named, restarts with Docker) and manage it:

```bash
docker run -d --name collateral_scrapping --restart unless-stopped \
  -p 8010:8010 -e GOOGLE_MAPS_API_KEY=AIza... collateral_scrapping

docker ps                       # status (health)
docker logs -f collateral_scrapping   # follow logs
docker stop collateral_scrapping      # stop
docker start collateral_scrapping     # start again
docker rm -f collateral_scrapping     # remove
```

## Use

```bash
curl "http://localhost:8010/extract?url=https://www.rumah123.com/properti/jakarta-pusat/hos41138420/"
```

```json
{
  "luas_tanah": 294.0,
  "luas_bangunan": 482.0,
  "kode_pos": "10430",
  "kelurahan": "Kenari"
}
```

Interactive docs: http://localhost:8010/docs · Health check: `GET /health`

### Postman

Import [`collateral_scrapping.postman_collection.json`](./collateral_scrapping.postman_collection.json)
(File → Import). It has the `/health` and `/extract` requests plus example responses. Set the
collection variables `base_url` (default `http://localhost:8010`) and `listing_url`.

## Responses

| Status | Meaning |
|--------|---------|
| 200 | OK (fields may be null if coordinates were unavailable) |
| 400 | `url` is not a rumah123.com listing URL |
| 422 | listing page could not be parsed |
| 502 | listing page could not be fetched |
| 500 | `GOOGLE_MAPS_API_KEY` not set |
