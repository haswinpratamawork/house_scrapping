# Implementation Plan — Rumah123 Property Scraper

> Detailed, step-by-step build plan derived from [plan.md](./plan.md) and
> [architecture.md](./architecture.md). Each task is small, ordered, and ends with a
> verification. Build test-first where practical; every phase leaves the repo working.
>
> Last updated: 2026-06-03 · Branch: `dev`

## Conventions

- **Package name:** `scraper` (importable as `python -m scraper.run`).
- **Tests:** `pytest`; live HTTP is never called in tests — use saved fixtures and mocks.
- **Definition of done (per task):** code + test written, `pytest` green, `ruff` clean.
- **Commit cadence:** one commit per task (or per small task group), pushed to `dev`.

## Proposed repository layout

```
house_scrapping/
├─ docs/                         # specs (done)
├─ pyproject.toml                # deps + tool config (ruff, pytest)
├─ .env.example                  # DB DSN + throttle settings template
├─ README.md
├─ scraper/
│  ├─ __init__.py
│  ├─ config.py                  # targets, throttle, DSN from env
│  ├─ models.py                  # ListingRecord (pydantic)
│  ├─ fetch/
│  │  ├─ base.py                 # Fetcher interface
│  │  └─ httpx_fetcher.py        # Approach A
│  ├─ sources/
│  │  ├─ base.py                 # Source interface
│  │  └─ rumah123.py             # Rumah123Source (discover + parse)
│  ├─ normalize.py               # raw record -> ListingRecord
│  ├─ db/
│  │  ├─ schema.sql              # tables + indexes
│  │  └─ repository.py           # upsert / price_history / runs / delisting
│  └─ run.py                     # ScrapeRun orchestrator + CLI
└─ tests/
   ├─ fixtures/                  # saved Rumah123 HTML samples
   └─ test_*.py
```

---

## Phase 0 — Project scaffold

**0.1 Create `pyproject.toml`** with deps (`httpx`, `selectolax`, `psycopg[binary]`,
`pydantic`, `tenacity`, `python-dotenv`) and dev deps (`pytest`, `ruff`). Configure ruff +
pytest.
→ *Verify:* `pip install -e .[dev]` succeeds; `pytest` runs (0 tests) and `ruff check` passes.

**0.2 Add `.env.example`** with `DATABASE_URL`, `REQUEST_DELAY_MIN/MAX`, `MAX_CONCURRENCY`,
`MAX_RETRIES`, `USER_AGENT`.
→ *Verify:* file present; documented in README.

**0.3 `scraper/config.py`** — load settings from env; define Jabodetabek target cities and
property-type slugs; provide a `Config` object.
→ *Verify:* unit test asserts defaults load and env overrides apply.

**0.4 `README.md`** — setup, env vars, how to run, how to test.
→ *Verify:* steps followed from scratch work.

---

## Phase 1 — Database layer

**1.1 `scraper/db/schema.sql`** — create `listings`, `price_history`, `scrape_runs` +
indexes exactly per architecture.md §4.
→ *Verify:* applying to an empty Postgres creates all tables; re-applying is safe
(`CREATE TABLE IF NOT EXISTS`).

**1.2 `Repository.start_run()` / `finish_run()`** — insert/update `scrape_runs`.
→ *Verify:* test creates a run, finishes it, row reflects counts + timestamps.

**1.3 `Repository.upsert_listing()`** — insert new (set `first_seen_at`, `is_active=true`)
or update existing (set `last_seen_at`), by `listing_id`.
→ *Verify:* test inserts then upserts the same id; one row; timestamps correct.

**1.4 `Repository.record_price_if_changed()`** — append to `price_history` only when
`price_idr` differs from the latest stored price.
→ *Verify:* test — unchanged price = no new row; changed price = one new row.

**1.5 `Repository.reconcile_delistings(run, scraped_ids)`** — set `is_active=false` for
listings of the scraped types/cities not seen this run.
→ *Verify:* test — a previously-seen, now-absent listing flips to inactive; others stay.

*(Tests use a local throwaway Postgres database / schema; documented in README.)*

---

## Phase 2 — Fetcher

**2.1 `fetch/base.py`** — `Fetcher` ABC with `get(url) -> str`.
→ *Verify:* import + interface test.

**2.2 `fetch/httpx_fetcher.py`** — `HttpxFetcher`: real User-Agent, randomized delay
(min/max), concurrency cap, `tenacity` retry/backoff on 429/5xx/timeout.
→ *Verify:* tests with mocked transport — retries on 503 then succeeds; gives up after
`MAX_RETRIES`; delay invoked between calls.

**2.3 `robots.txt` respect** — fetch/cache robots, skip disallowed paths.
→ *Verify:* test with a fixture robots disallowing a path → that URL is skipped.

---

## Phase 3 — Rumah123 source

**3.1 Capture fixtures** — save 2–3 real index pages + 3–4 listing pages (house, apartment,
land) into `tests/fixtures/`. (Manual one-time, documented.)
→ *Verify:* fixtures present and contain `__NEXT_DATA__`.

**3.2 `sources/base.py`** — `Source` ABC: `discover() -> Iterable[str]`,
`parse(html) -> dict`.
→ *Verify:* interface test.

**3.3 `Rumah123Source.parse()`** — locate and load `__NEXT_DATA__`, return raw record
(price text, areas, certificate, location, specs, ids, url).
→ *Verify:* parse each fixture listing → expected raw fields; land fixture has no bed/bath.

**3.4 `Rumah123Source.discover()`** — build index URLs per (property_type × city), paginate
until empty/last page, extract listing URLs from index `__NEXT_DATA__`.
→ *Verify:* against index fixtures, returns expected URL set and stops paginating correctly.

---

## Phase 4 — Normalizer

**4.1 `models.py`** — `ListingRecord` pydantic model matching the `listings` columns.
→ *Verify:* model validates a complete record; rejects bad types.

**4.2 `normalize.py` — price** — parse `Rp X Miliar/Juta`, `,`/`.` decimals → bigint rupiah.
→ *Verify:* table-driven tests incl. `"Rp 1,56 Miliar"`→1_560_000_000, `"Rp 950 Juta"`,
`"Rp 48 Miliar"`.

**4.3 area / certificate / property_type / location / bed-bath** rules per architecture.md §5.
→ *Verify:* unit tests per rule incl. missing values → null; land has null bed/bath.

**4.4 `normalize(raw) -> ListingRecord`** — compose all rules; keep `raw` passthrough.
→ *Verify:* end-to-end on each fixture raw record → fully populated `ListingRecord`.

---

## Phase 5 — Orchestrator

**5.1 `run.py: ScrapeRun.execute()`** — wire discover → fetch → parse → normalize →
upsert + price history; collect counts; skip+log per-listing errors.
→ *Verify:* end-to-end test on a handful of fixture listings with a fake fetcher and a test
DB → rows present, counts correct, one bad listing skipped not fatal.

**5.2 Delisting + run finalize** — call `reconcile_delistings`, `finish_run` with metrics.
→ *Verify:* test — second run missing one listing marks it inactive; run row has
found/new/updated/delisted/errors.

**5.3 Structured logging** — per-stage logs + final summary line.
→ *Verify:* run emits expected log fields.

---

## Phase 6 — Scheduling (local)

**6.1 CLI** — `python -m scraper.run` with flags: `--cities`, `--types`, `--max-pages`,
`--dry-run`, `--limit`.
→ *Verify:* `--dry-run --limit 5` discovers+parses without writing to DB.

**6.2 Weekly cron** — documented crontab example in README.
→ *Verify:* example command runs the CLI.

---

## Phase 7 — Polish & validation

**7.1 Small live run** — one city + one type, `--max-pages` capped, real DB.
→ *Verify:* `listings` populated with clean values; no blocking; `scrape_runs` row sane.

**7.2 Spot-check** — compare ~10 normalized rows against the live site.
→ *Verify:* price/area/location/specs match.

**7.3 Tune throttle** — adjust delay/concurrency from observed behavior; note final values.
→ *Verify:* a second small run is stable.

---

## Build order summary

`0 → 1 → 2 → 3 → 4 → 5 → 6 → 7`. Phases 1–4 are independent enough to parallelize, but the
linear order keeps each step verifiable against the previous. Stop and validate after
Phase 5 (full pipeline on fixtures) before any live run in Phase 7.
