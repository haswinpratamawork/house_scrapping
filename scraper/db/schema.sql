-- Schema for the Rumah123 property scraper. Idempotent: safe to re-apply.
-- See docs/architecture.md §4 for the data model.

CREATE TABLE IF NOT EXISTS listings (
    listing_id        text PRIMARY KEY,            -- natural ID from the source
    source            text        NOT NULL DEFAULT 'rumah123',
    url               text,
    title             text,
    property_type     text,                        -- house/apartment/land/shophouse/warehouse/other
    province          text,
    city              text,
    district          text,
    area              text,
    latitude          numeric,
    longitude         numeric,
    price_idr         bigint,                      -- current price, integer rupiah
    bedrooms          integer,
    bathrooms         integer,
    land_area_m2      numeric,                     -- LT (luas tanah)
    building_area_m2  numeric,                     -- LB (luas bangunan)
    certificate       text,                        -- SHM, HGB, ...
    extra_specs       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    agent_name        text,
    first_seen_at     timestamptz NOT NULL DEFAULT now(),
    last_seen_at      timestamptz NOT NULL DEFAULT now(),
    is_active         boolean     NOT NULL DEFAULT true,
    raw               jsonb                        -- full raw record, for re-parsing
);

-- Append-only price history: one row only when the price changes.
CREATE TABLE IF NOT EXISTS price_history (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    listing_id   text        NOT NULL REFERENCES listings (listing_id) ON DELETE CASCADE,
    price_idr    bigint      NOT NULL,
    observed_at  timestamptz NOT NULL DEFAULT now()
);

-- One row per weekly run, for monitoring.
CREATE TABLE IF NOT EXISTS scrape_runs (
    run_id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source             text        NOT NULL DEFAULT 'rumah123',
    started_at         timestamptz NOT NULL DEFAULT now(),
    finished_at        timestamptz,
    status             text        NOT NULL DEFAULT 'running',   -- running/completed/failed
    listings_found     integer     NOT NULL DEFAULT 0,
    listings_new       integer     NOT NULL DEFAULT 0,
    listings_updated   integer     NOT NULL DEFAULT 0,
    listings_delisted  integer     NOT NULL DEFAULT 0,
    errors             integer     NOT NULL DEFAULT 0,
    notes              text
);

CREATE INDEX IF NOT EXISTS idx_listings_city_type  ON listings (city, property_type);
CREATE INDEX IF NOT EXISTS idx_listings_is_active   ON listings (is_active);
CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history (listing_id, observed_at);
