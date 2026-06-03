"""Tests for scraper.db.repository (Phase 1).

Requires a local PostgreSQL test database. Set TEST_DATABASE_URL (or DATABASE_URL) to a
database whose name contains 'test' — the fixture DROPS and recreates the tables, so it
refuses to run against a database not clearly marked as a test DB. Tests are skipped if no
such DSN is configured.
"""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

# Importing config loads .env (if python-dotenv is installed), populating the DSN.
from scraper import config  # noqa: F401  (import for side effect: load .env)

psycopg = pytest.importorskip("psycopg")
from scraper.db.repository import Repository  # noqa: E402


def _test_dsn() -> str | None:
    dsn = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        return None
    # Safety: only ever touch a database clearly marked as a test DB.
    if "test" not in dsn.rsplit("/", 1)[-1].lower():
        pytest.skip("DSN does not look like a test database (name must contain 'test')")
    return dsn


@pytest.fixture()
def repo():
    dsn = _test_dsn()
    if dsn is None:
        pytest.skip("No TEST_DATABASE_URL / DATABASE_URL configured")
    conn = psycopg.connect(dsn, autocommit=True)
    with conn.cursor() as cur:
        cur.execute(
            "DROP TABLE IF EXISTS price_history, scrape_runs, listings CASCADE"
        )
    r = Repository(conn)
    r.apply_schema()
    try:
        yield r
    finally:
        conn.close()


def _make_listing(**overrides) -> dict:
    data = {
        "listing_id": "rmh-1",
        "source": "rumah123",
        "url": "https://www.rumah123.com/properti/jakarta-selatan/rmh-1/",
        "title": "Rumah Dijual Pondok Indah",
        "property_type": "house",
        "province": "DKI Jakarta",
        "city": "jakarta-selatan",
        "district": "Pondok Indah",
        "area": "Pondok Indah",
        "latitude": -6.26,
        "longitude": 106.78,
        "price_idr": 1_560_000_000,
        "bedrooms": 4,
        "bathrooms": 3,
        "land_area_m2": 200,
        "building_area_m2": 150,
        "certificate": "SHM",
        "extra_specs": {"carport": 2, "floors": 2},
        "agent_name": "Agen A",
        "raw": {"any": "thing"},
    }
    data.update(overrides)
    return data


def _count(repo, table: str) -> int:
    with repo.conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table}")
        return cur.fetchone()[0]


def test_apply_schema_is_idempotent(repo):
    repo.apply_schema()  # second apply must not error
    for table in ("listings", "price_history", "scrape_runs"):
        assert _count(repo, table) == 0


def test_start_and_finish_run(repo):
    run_id, started_at = repo.start_run()
    assert isinstance(run_id, int)
    repo.finish_run(run_id, status="completed", found=10, new=3, updated=7, delisted=1)
    with repo.conn.cursor() as cur:
        cur.execute(
            "SELECT status, listings_found, listings_new, listings_updated, "
            "listings_delisted, finished_at FROM scrape_runs WHERE run_id = %s",
            (run_id,),
        )
        status, found, new, updated, delisted, finished_at = cur.fetchone()
    assert status == "completed"
    assert (found, new, updated, delisted) == (10, 3, 7, 1)
    assert finished_at is not None


def test_upsert_new_then_update(repo):
    assert repo.upsert_listing(_make_listing()) == "new"
    assert _count(repo, "listings") == 1

    with repo.conn.cursor() as cur:
        cur.execute("SELECT first_seen_at FROM listings WHERE listing_id = 'rmh-1'")
        first_seen = cur.fetchone()[0]

    # Update same id with a new title/price.
    assert repo.upsert_listing(_make_listing(title="Updated", price_idr=1_600_000_000)) == "updated"
    assert _count(repo, "listings") == 1
    with repo.conn.cursor() as cur:
        cur.execute(
            "SELECT title, price_idr, first_seen_at, last_seen_at, is_active "
            "FROM listings WHERE listing_id = 'rmh-1'"
        )
        title, price, first_seen2, last_seen, is_active = cur.fetchone()
    assert title == "Updated"
    assert price == 1_600_000_000
    assert first_seen2 == first_seen          # preserved
    assert last_seen >= first_seen            # bumped
    assert is_active is True


def test_record_price_if_changed(repo):
    repo.upsert_listing(_make_listing())
    # First observation always records.
    assert repo.record_price_if_changed("rmh-1", 1_560_000_000) is True
    # Same price -> no new row.
    assert repo.record_price_if_changed("rmh-1", 1_560_000_000) is False
    # Changed price -> new row.
    assert repo.record_price_if_changed("rmh-1", 1_600_000_000) is True
    assert _count(repo, "price_history") == 2
    # Null price is never recorded.
    assert repo.record_price_if_changed("rmh-1", None) is False
    assert _count(repo, "price_history") == 2


def test_reconcile_delistings(repo):
    _, since = repo.start_run()  # run start reference

    # A listing seen *after* the run start stays active.
    repo.upsert_listing(_make_listing(listing_id="seen"))
    # A listing whose last_seen_at predates the run start is now stale -> delist.
    repo.upsert_listing(_make_listing(listing_id="stale"))
    with repo.conn.cursor() as cur:
        cur.execute(
            "UPDATE listings SET last_seen_at = %s WHERE listing_id = 'stale'",
            (since - timedelta(days=7),),
        )

    delisted = repo.reconcile_delistings("rumah123", since)
    assert delisted == 1
    with repo.conn.cursor() as cur:
        cur.execute("SELECT listing_id, is_active FROM listings ORDER BY listing_id")
        rows = dict(cur.fetchall())
    assert rows["seen"] is True
    assert rows["stale"] is False
