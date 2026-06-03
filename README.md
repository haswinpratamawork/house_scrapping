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
| `DATABASE_URL` | _(empty)_ | PostgreSQL DSN |
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

The CLI lands in Phase 6. It will look like:

```bash
python -m scraper.run --dry-run --limit 5     # safe trial, no DB writes
python -m scraper.run                         # full weekly run
```

A weekly `cron` example will be documented alongside it.
