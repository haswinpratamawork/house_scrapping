"""Shared test fixtures."""

from __future__ import annotations

import os

import pytest

# Importing config loads .env (if python-dotenv is installed), populating the DSN.
from scraper import config  # noqa: F401  (import for side effect)

psycopg = pytest.importorskip("psycopg")
from scraper.db.repository import Repository  # noqa: E402


def test_dsn() -> str | None:
    """A DSN for a database clearly marked as a test DB, or None."""
    dsn = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        return None
    if "test" not in dsn.rsplit("/", 1)[-1].lower():
        pytest.skip("DSN does not look like a test database (name must contain 'test')")
    return dsn


@pytest.fixture()
def clean_repo():
    """A Repository on a freshly-reset test database (tables dropped + recreated)."""
    dsn = test_dsn()
    if dsn is None:
        pytest.skip("No TEST_DATABASE_URL / DATABASE_URL configured")
    conn = psycopg.connect(dsn, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS price_history, scrape_runs, listings CASCADE")
    repo = Repository(conn)
    repo.apply_schema()
    try:
        yield repo
    finally:
        conn.close()
