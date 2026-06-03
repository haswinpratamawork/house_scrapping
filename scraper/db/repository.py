"""Repository: all PostgreSQL access for the scraper.

Decoupled from the scraping/normalization layers — ``upsert_listing`` takes a plain
mapping of column values (not a pydantic model), so the DB layer has no dependency on
the rest of the pipeline. The orchestrator (Phase 5) converts a ``ListingRecord`` to a
dict before calling in.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Columns written by upsert_listing (whitelisted to avoid surprises). first_seen_at,
# last_seen_at, and is_active are managed by the DB / upsert logic, not passed in.
_LISTING_COLS: tuple[str, ...] = (
    "listing_id",
    "source",
    "url",
    "title",
    "property_type",
    "province",
    "city",
    "district",
    "area",
    "latitude",
    "longitude",
    "price_idr",
    "bedrooms",
    "bathrooms",
    "land_area_m2",
    "building_area_m2",
    "certificate",
    "extra_specs",
    "agent_name",
    "raw",
)
_JSON_COLS = {"extra_specs", "raw"}


class Repository:
    """Thin data-access layer over a psycopg connection."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    @classmethod
    def connect(cls, dsn: str) -> Repository:
        """Open an autocommit connection to ``dsn`` and return a Repository."""
        return cls(psycopg.connect(dsn, autocommit=True))

    def close(self) -> None:
        self.conn.close()

    # --- schema -----------------------------------------------------------------

    def apply_schema(self) -> None:
        """Create tables and indexes if absent. Safe to call repeatedly."""
        with self.conn.cursor() as cur:
            cur.execute(SCHEMA_PATH.read_text())

    # --- runs -------------------------------------------------------------------

    def start_run(self, source: str = "rumah123") -> tuple[int, datetime]:
        """Insert a 'running' scrape_runs row. Returns (run_id, started_at)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scrape_runs (source) VALUES (%s) RETURNING run_id, started_at",
                (source,),
            )
            run_id, started_at = cur.fetchone()
        return run_id, started_at

    def finish_run(
        self,
        run_id: int,
        *,
        status: str = "completed",
        found: int = 0,
        new: int = 0,
        updated: int = 0,
        delisted: int = 0,
        errors: int = 0,
        notes: str | None = None,
    ) -> None:
        """Finalize a run with status + counts."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE scrape_runs
                   SET finished_at = now(), status = %s, listings_found = %s,
                       listings_new = %s, listings_updated = %s,
                       listings_delisted = %s, errors = %s, notes = %s
                 WHERE run_id = %s
                """,
                (status, found, new, updated, delisted, errors, notes, run_id),
            )

    # --- listings ---------------------------------------------------------------

    def upsert_listing(self, data: Mapping[str, Any]) -> str:
        """Insert or update a listing by listing_id.

        On update, refreshes the row, bumps last_seen_at, and reactivates it.
        first_seen_at is preserved. Returns 'new' or 'updated'.
        """
        values = []
        for col in _LISTING_COLS:
            value = data.get(col)
            if col in _JSON_COLS:
                value = Jsonb(value if value is not None else {})
            values.append(value)

        placeholders = ", ".join(["%s"] * len(_LISTING_COLS))
        update_cols = [c for c in _LISTING_COLS if c != "listing_id"]
        set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
        sql = f"""
            INSERT INTO listings ({", ".join(_LISTING_COLS)})
            VALUES ({placeholders})
            ON CONFLICT (listing_id) DO UPDATE SET
                {set_clause}, last_seen_at = now(), is_active = true
            RETURNING (xmax = 0) AS inserted
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, values)
            inserted = cur.fetchone()[0]
        return "new" if inserted else "updated"

    def record_price_if_changed(
        self,
        listing_id: str,
        price_idr: int | None,
        observed_at: datetime | None = None,
    ) -> bool:
        """Append a price_history row only if the price differs from the latest one.

        Returns True if a row was inserted (incl. the first-ever observation), else False.
        A null price is never recorded.
        """
        if price_idr is None:
            return False
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT price_idr FROM price_history
                 WHERE listing_id = %s
                 ORDER BY observed_at DESC, id DESC
                 LIMIT 1
                """,
                (listing_id,),
            )
            row = cur.fetchone()
            if row is not None and row[0] == price_idr:
                return False
            if observed_at is None:
                cur.execute(
                    "INSERT INTO price_history (listing_id, price_idr) VALUES (%s, %s)",
                    (listing_id, price_idr),
                )
            else:
                cur.execute(
                    "INSERT INTO price_history (listing_id, price_idr, observed_at) "
                    "VALUES (%s, %s, %s)",
                    (listing_id, price_idr, observed_at),
                )
        return True

    def reconcile_delistings(self, source: str, since: datetime) -> int:
        """Mark active listings not seen since ``since`` (the run start) as inactive.

        Listings touched this run have last_seen_at >= since (set by upsert), so they are
        left active. Returns the number of listings delisted.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE listings
                   SET is_active = false
                 WHERE source = %s AND is_active = true AND last_seen_at < %s
                """,
                (source, since),
            )
            return cur.rowcount
