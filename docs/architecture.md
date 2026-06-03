# Architecture — Rumah123 Property Scraper

> **Project goal:** Scrape Indonesian property-for-sale listings (Rumah123, Jabodetabek
> first) on a weekly schedule to support a BRI use case — comparing **agunan (collateral)
> valuations against real market prices**. Asset types: houses, apartments, land, and other
> property (shophouse/ruko, warehouse). Local first, portable to Vertex AI / Cloud SQL later.
>
> Last updated: 2026-06-03

## 1. Decisions at a glance

| Decision | Choice | Rationale |
|----------|--------|-----------|
| First source | **Rumah123.com** | Largest Jabodetabek inventory; served plain requests in probe; Next.js with embedded JSON |
| Region (v1) | **Jabodetabek** | Jakarta, Bogor, Depok, Tangerang, Bekasi (+ Tangsel) |
| Asset types | House, apartment, land, shophouse, warehouse — **for sale** | Match collateral (agunan) scope |
| Cadence | **Weekly** | Property prices move slowly; keeps under anti-bot radar |
| Fetch method | **Approach A — HTTP + `__NEXT_DATA__` JSON** | Fast, light, structured; no fragile HTML scraping |
| Language | **Python** | Best fit for scraping + Postgres + future Vertex |
| Storage | **Local PostgreSQL** → Cloud SQL later | User will migrate to Cloud SQL |

## 2. Pipeline overview

A modular pipeline, run once per weekly job. Each stage is isolated and independently
testable.

```
                 ┌──────────────────────────────────────────────┐
   weekly run →  │  scrape_run (orchestrator)                    │
                 └──────────────────────────────────────────────┘
                     │
   1. Discover   ──► iterate (property_type × Jabodetabek city) index pages,
                     paginate, collect listing IDs + URLs
                     │
   2. Fetch      ──► httpx GET each listing/index page (polite throttle + retries)
                     │
   3. Parse      ──► extract embedded __NEXT_DATA__ JSON → raw record
                     │
   4. Normalize  ──► clean into typed fields
                     ("Rp 1,56 Miliar"→1_560_000_000, "120 m²"→120.0, SHM, etc.)
                     │
   5. Persist    ──► upsert into Postgres; record price change in history;
                     mark listings seen/unseen this run
```

## 3. Components & boundaries

Each component has one purpose, a well-defined interface, and can be tested alone.

| Component | Responsibility | Depends on |
|-----------|----------------|------------|
| `Fetcher` (interface) | Get raw HTML/JSON for a URL with throttling + retries | httpx |
| `HttpxFetcher` | Approach A implementation | `Fetcher` |
| *(future)* `PlaywrightFetcher` | Approach C fallback, swappable | `Fetcher` |
| `Source` (interface) | `discover()` listing URLs + `parse()` a page into a raw record | `Fetcher` |
| `Rumah123Source` | Rumah123-specific discovery + `__NEXT_DATA__` parsing | `Source` |
| `Normalizer` | Raw record → typed, cleaned `ListingRecord` | — |
| `Repository` | Upsert listings, write price history, manage run metadata | psycopg / SQLAlchemy |
| `ScrapeRun` (orchestrator) | Wire stages together, drive the weekly job, log metrics | all above |
| `config` | Targets (cities, types), throttle settings, DB DSN | — |

**Extensibility:** adding 99.co later = a new `Source` subclass; swapping to a browser =
a new `Fetcher` subclass. The pipeline, normalizer, and storage stay unchanged.

## 4. Data model (PostgreSQL)

### `listings` — latest state, one row per unique listing
| column | type | notes |
|--------|------|-------|
| `listing_id` | text PK | natural ID from Rumah123 |
| `source` | text | `'rumah123'` |
| `url` | text | |
| `title` | text | |
| `property_type` | text | house / apartment / land / shophouse / warehouse / other |
| `province`, `city`, `district`, `area` | text | parsed Jabodetabek location |
| `latitude`, `longitude` | numeric | if available |
| `price_idr` | bigint | current price, integer rupiah |
| `bedrooms`, `bathrooms` | int | |
| `land_area_m2` | numeric | LT (luas tanah) |
| `building_area_m2` | numeric | LB (luas bangunan) |
| `certificate` | text | SHM, HGB, etc. |
| `extra_specs` | jsonb | carport, floors, furnishing, etc. |
| `agent_name` | text | |
| `first_seen_at`, `last_seen_at` | timestamptz | |
| `is_active` | bool | false once it disappears from listings |
| `raw` | jsonb | full raw record (re-parse without re-scraping) |

### `price_history` — append-only, one row only when price changes
| `id` bigserial PK | `listing_id` text FK → listings | `price_idr` bigint | `observed_at` timestamptz |

### `scrape_runs` — one row per weekly run (monitoring)
| `run_id` bigserial PK | `started_at` | `finished_at` | `status` | `listings_found` | `new` | `updated` | `delisted` | `errors` int | `notes` |

**Indexes:** `listings(city, property_type)`, `listings(is_active)`,
`price_history(listing_id, observed_at)`.

## 5. Normalization rules

| Field | Raw example | Normalized |
|-------|-------------|------------|
| Price | `"Rp 1,56 Miliar"`, `"Rp 48 Miliar"`, `"Rp 950 Juta"` | bigint rupiah (`1_560_000_000`) — handle Miliar/Juta and `,`/`.` decimal |
| Area | `"120 m²"`, `"120 m2"` | numeric m² |
| Certificate | `"SHM - Sertifikat Hak Milik"` | code `"SHM"` |
| Property type | category/URL slug | enum (house/apartment/land/shophouse/warehouse/other) |
| Location | breadcrumb / address | province, city, district, area split |
| Bed/bath | counts | int (null if absent, e.g. land) |

Unparseable values → null, with the original kept in `raw` for later reprocessing.

## 6. Error handling & politeness

- **Throttle:** randomized delay between requests; concurrency cap (small).
- **Retries:** exponential backoff on 429/5xx/timeouts; cap attempts, then skip and log.
- **Identification:** real User-Agent; respect `robots.txt`.
- **Resilience:** a single bad listing is logged and skipped, never aborts the run.
- **Idempotent runs:** re-running a week is safe — upserts by `listing_id`, history only
  appends on real price change.
- **Delisting:** listings not seen in a run keep their data but get `is_active = false`.
- **Observability:** every run writes a `scrape_runs` row with counts + error totals.

## 7. Tech stack

- Python 3.11+
- `httpx` (fetch), `selectolax`/`parsel` (locate `__NEXT_DATA__`), stdlib `json`
- `psycopg` (v3) or SQLAlchemy Core for Postgres
- `pydantic` for the typed `ListingRecord`
- `tenacity` for retry/backoff
- `pytest` for tests
- Config via `.env` / environment variables (DB DSN, throttle settings)

## 8. Future migration (Vertex AI / GCP)

- **Postgres → Cloud SQL:** same schema; swap the DSN.
- **Scheduling:** local cron → Cloud Scheduler + Cloud Run job / Vertex pipeline.
- **Fetcher:** drop in `PlaywrightFetcher` if anti-bot tightens (Approach C).
- **Analytics:** optional periodic export to BigQuery for the agunan-vs-market analysis.
