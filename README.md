# house_scrapping

Weekly scraper for Indonesian property-for-sale listings from **Rumah123**, starting with
the **Jabodetabek** region. Built to support a BRI use case: comparing **agunan (collateral)
valuations against real market prices**. Data lands in **PostgreSQL** (local now, Cloud SQL
later) with weekly price-change history.

See [`docs/`](./docs) for the full design:
- [architecture.md](./docs/architecture.md) — design, data model, components
- [plan.md](./docs/plan.md) — runtime workflow + build phases
- [implementation-plan.md](./docs/implementation-plan.md) — step-by-step build tasks
- [indonesia-property-websites.md](./docs/indonesia-property-websites.md) — source research

## Status

Phase 0 (scaffold) in progress. See the implementation plan for phase order.

## Requirements

- Python **3.11+** (3.13 recommended)
- PostgreSQL (local) — used from Phase 1 onward

## Setup

```bash
# create and activate a virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# install the package with dev tools
pip install -e ".[dev]"

# configure environment
cp .env.example .env
# then edit .env (DATABASE_URL, throttle settings, etc.)
```

## Configuration

All settings come from environment variables (loaded from `.env` if present). See
[.env.example](./.env.example):

| Variable | Default | Meaning |
|----------|---------|---------|
| `DATABASE_URL` | _(empty)_ | PostgreSQL DSN for the **real data** DB |
| `TEST_DATABASE_URL` | _(empty)_ | DSN for the **test** DB (name must contain `test`; tables are wiped each run) |
| `REQUEST_DELAY_MIN` / `REQUEST_DELAY_MAX` | `2.0` / `5.0` | random delay (s) between requests |
| `MAX_CONCURRENCY` | `2` | max simultaneous requests |
| `MAX_RETRIES` | `4` | retries on 429/5xx/timeout |
| `USER_AGENT` | _(project UA)_ | how the scraper identifies itself |
| `BASE_URL` | `https://www.rumah123.com` | source base URL |

## Running tests

```bash
pytest          # run the test suite
ruff check .    # lint
```

Tests never call the live site — they use saved fixtures and mocks.

## Running the scraper

```bash
# safe trial: discover/fetch/parse a few listings, write nothing
python -m scraper.run --dry-run --limit 5

# scrape one city + type, capped pages (good first live test)
python -m scraper.run --cities jakarta-selatan --types rumah --max-pages 2

# full weekly run (all Jabodetabek cities + property types)
python -m scraper.run
```

Equivalent console script after `pip install -e .`: `house-scrape …`.

**Flags:** `--cities a,b` · `--types rumah,tanah` · `--max-pages N` · `--limit N` ·
`--dry-run` · `--log-level INFO`. A non-dry run requires `DATABASE_URL` and applies the
schema automatically (safe to re-run).

### Weekly schedule (local cron)

The local Homebrew PostgreSQL must be running on its configured port first. Example:
run every Monday at 02:00, logging to a file:

```cron
0 2 * * 1 cd /path/to/house_scrapping && .venv/bin/python -m scraper.run >> scrape.log 2>&1
```

Edit your crontab with `crontab -e`. When the project moves to Vertex/Cloud SQL, this is
replaced by Cloud Scheduler + a Cloud Run job.
