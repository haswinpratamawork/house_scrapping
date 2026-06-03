# Plan — Rumah123 Property Scraper

> Implementation workflow for the weekly Rumah123 scraper. See
> [architecture.md](./architecture.md) for design and data model, and
> [indonesia-property-websites.md](./indonesia-property-websites.md) for source research.
>
> Last updated: 2026-06-03

## A. Runtime workflow (what one weekly run does)

```
1. START RUN
   └─ create scrape_runs row (status = running, started_at = now)

2. DISCOVER
   └─ for each target (property_type × Jabodetabek city):
        └─ fetch index pages, page by page
             └─ extract listing IDs + URLs from __NEXT_DATA__
             └─ stop at last page / empty page
   └─ result: deduplicated set of listing URLs for this run

3. FETCH + PARSE + NORMALIZE  (per listing, throttled)
   └─ fetch listing page (retry w/ backoff; skip + log on hard failure)
   └─ extract __NEXT_DATA__ JSON  → raw record
   └─ normalize → typed ListingRecord (price_idr, areas, certificate, location, specs)
   └─ keep raw JSON for storage

4. PERSIST  (per listing)
   └─ upsert into listings (by listing_id)
        ├─ new listing      → insert, set first_seen_at, is_active = true
        └─ existing listing → update fields, set last_seen_at, is_active = true
   └─ if price_idr changed vs latest → insert price_history row

5. RECONCILE DELISTINGS
   └─ listings of scraped types/cities NOT seen this run → is_active = false

6. END RUN
   └─ update scrape_runs row (finished_at, status, counts: found/new/updated/delisted/errors)
```

Re-running the same week is **idempotent**: upserts by `listing_id`, and `price_history`
only appends when the price actually changes.

## B. Build phases (implementation order)

Each phase is independently testable and leaves the project in a working state.

### Phase 0 — Project scaffold
- Python project layout, dependencies, `.env` template, README.
- `config` module: target cities, property types, throttle settings, DB DSN.

### Phase 1 — Database layer
- Postgres schema migration: `listings`, `price_history`, `scrape_runs` + indexes.
- `Repository`: upsert listing, append price_history on change, run create/finish,
  delisting reconcile.
- Tests against a local test database.

### Phase 2 — Fetcher
- `Fetcher` interface + `HttpxFetcher` with throttle, retries/backoff, User-Agent,
  `robots.txt` respect.
- Tests with mocked HTTP responses.

### Phase 3 — Rumah123 source
- `Rumah123Source.discover()` — build index URLs per (type × city), paginate, extract
  listing URLs from `__NEXT_DATA__`.
- `Rumah123Source.parse()` — extract raw record from a listing page's `__NEXT_DATA__`.
- Tests against saved sample HTML fixtures (no live calls in tests).

### Phase 4 — Normalizer
- Price (Miliar/Juta), area, certificate, property_type, location, bed/bath rules.
- `ListingRecord` pydantic model.
- Unit tests covering tricky formats and missing fields (e.g. land has no bedrooms).

### Phase 5 — Orchestrator
- `ScrapeRun` wiring discover → fetch → parse → normalize → persist → reconcile.
- Structured logging + run metrics into `scrape_runs`.
- A small end-to-end test on a handful of fixture listings.

### Phase 6 — Scheduling (local)
- CLI entry point (`python -m scraper.run`) and a documented weekly `cron` example.
- Dry-run / limit flags for safe manual testing.

### Phase 7 — Polish & validation
- Run a real, **small-scope** live scrape (one city, one type, capped pages) to validate
  end to end and tune throttle.
- Spot-check normalized values against the live site.

## C. Out of scope (v1 — deliberately deferred)

- Additional sources (99.co, Lamudi, Brighton) — design supports them; not built in v1.
- Playwright fallback (Approach C) — only if anti-bot blocking appears.
- Cloud SQL / Vertex deployment, BigQuery export — local first.
- Dashboard / analysis layer — this project produces the dataset; analysis is downstream.
- Regions beyond Jabodetabek.

## D. Success criteria

- A weekly run completes and populates `listings` with clean, typed fields for
  Jabodetabek for-sale assets (house/apartment/land/shophouse/warehouse).
- Re-running detects and records price changes in `price_history` and flags delisted items.
- No site blocking under the weekly cadence; runs are idempotent and logged.
- Schema and code move to Cloud SQL / Vertex with only config (DSN) changes.
