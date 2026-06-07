"""End-to-end tests for scraper.run.ScrapeRun (Phase 5).

A fake fetcher serves a synthetic index page plus the real listing fixtures into the test
database, so the whole pipeline (discover -> fetch -> parse -> normalize -> persist) runs
without touching the live site.
"""

from __future__ import annotations

from pathlib import Path

from scraper.config import Config
from scraper.fetch.base import Fetcher, FetchError
from scraper.run import ScrapeRun
from scraper.sources.rumah123 import Rumah123Source

FIXTURES = Path(__file__).parent / "fixtures"
BASE = "https://www.rumah123.com"

# Discoverable listing paths -> fixture file (or raw HTML for the bad-listing case).
HOUSE = "/properti/jakarta-selatan-jagakarsa/x-hos41544728/"
APART = "/properti/jakarta-selatan-kuningan/x-aps7274021/"
LAND = "/properti/jakarta-selatan-jagakarsa/x-las9013631/"

_FIXTURE_BY_PATH = {
    HOUSE: "rumah123_listing_house.html",
    APART: "rumah123_listing_apartment.html",
    LAND: "rumah123_listing_land.html",
}


def _index_html(paths: list[str]) -> str:
    return "<html>" + "".join(f'<a href="{p}">x</a>' for p in paths) + "</html>"


class FakeFetcher(Fetcher):
    def __init__(self, paths: list[str], extra: dict[str, str] | None = None) -> None:
        self._index = _index_html(paths)
        self._listings = {
            BASE + p: (FIXTURES / _FIXTURE_BY_PATH[p]).read_text()
            for p in paths
            if p in _FIXTURE_BY_PATH
        }
        if extra:
            self._listings.update({BASE + k: v for k, v in extra.items()})

    def get(self, url: str) -> str:
        if url in self._listings:
            return self._listings[url]
        if "page=" in url:
            return "<html></html>"  # no listings on later pages -> stop
        if "/jual/" in url:
            return self._index
        raise FetchError(url)


def _run(repo, fetcher) -> ScrapeRun:
    config = Config(cities=("jakarta-selatan",), property_types=("rumah",))
    source = Rumah123Source(config, fetcher)
    return ScrapeRun(repo, fetcher, source)


def _count(repo, table: str) -> int:
    with repo.conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table}")
        return cur.fetchone()[0]


def test_execute_populates_database(clean_repo):
    stats = _run(clean_repo, FakeFetcher([HOUSE, APART, LAND])).execute()

    assert (stats.found, stats.new, stats.updated, stats.errors) == (3, 3, 0, 0)
    assert _count(clean_repo, "listings") == 3
    assert _count(clean_repo, "price_history") == 3  # first observation each
    assert _count(clean_repo, "scrape_runs") == 1

    with clean_repo.conn.cursor() as cur:
        cur.execute("SELECT status FROM scrape_runs")
        assert cur.fetchone()[0] == "completed"
        cur.execute("SELECT count(*) FROM listings WHERE is_active")
        assert cur.fetchone()[0] == 3


def test_rerun_updates_without_new_price_rows(clean_repo):
    _run(clean_repo, FakeFetcher([HOUSE, APART, LAND])).execute()
    stats = _run(clean_repo, FakeFetcher([HOUSE, APART, LAND])).execute()

    assert (stats.new, stats.updated) == (0, 3)
    assert _count(clean_repo, "listings") == 3
    assert _count(clean_repo, "price_history") == 3  # prices unchanged -> no new rows


def test_delisting_on_disappearance(clean_repo):
    _run(clean_repo, FakeFetcher([HOUSE, APART, LAND])).execute()
    # second run no longer lists the land property
    stats = _run(clean_repo, FakeFetcher([HOUSE, APART])).execute()

    assert stats.delisted == 1
    with clean_repo.conn.cursor() as cur:
        cur.execute("SELECT is_active FROM listings WHERE listing_id = 'las9013631'")
        assert cur.fetchone()[0] is False
        cur.execute("SELECT count(*) FROM listings WHERE is_active")
        assert cur.fetchone()[0] == 2


def test_bad_listing_is_skipped_not_fatal(clean_repo):
    bad_path = "/properti/jakarta-selatan/x-hos99999999/"
    fetcher = FakeFetcher([HOUSE, APART, LAND, bad_path], extra={bad_path: "<html>broken</html>"})
    stats = _run(clean_repo, fetcher).execute()

    assert stats.found == 4
    assert stats.new == 3       # three good listings persisted
    assert stats.errors == 1    # the broken one skipped
    assert _count(clean_repo, "listings") == 3


def test_dry_run_writes_nothing(clean_repo):
    stats = _run(clean_repo, FakeFetcher([HOUSE, APART, LAND])).execute(dry_run=True)

    assert stats.found == 3
    assert (stats.new, stats.updated) == (0, 0)
    assert stats.run_id is None
    assert _count(clean_repo, "listings") == 0
    assert _count(clean_repo, "scrape_runs") == 0


def test_limit_caps_processing(clean_repo):
    stats = _run(clean_repo, FakeFetcher([HOUSE, APART, LAND])).execute(limit=2)

    assert stats.found == 2
    assert _count(clean_repo, "listings") == 2


def test_per_district_run_does_not_delist_other_districts(clean_repo):
    # First populate two Jagakarsa listings via a normal (unscoped) run.
    _run(clean_repo, FakeFetcher([HOUSE, LAND])).execute()
    assert _count(clean_repo, "listings") == 2

    # Now scrape a different district (Kuningan) — it must NOT delist Jagakarsa.
    config = Config(cities=("jakarta-selatan",), property_types=("rumah",))
    fetcher = FakeFetcher([APART])
    source = Rumah123Source(config, fetcher, district="kuningan")
    stats = ScrapeRun(clean_repo, fetcher, source).execute()

    assert stats.delisted == 0
    with clean_repo.conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM listings WHERE is_active")
        assert cur.fetchone()[0] == 3  # 2 Jagakarsa + 1 Kuningan, all still active


def test_incomplete_discovery_skips_delisting(clean_repo):
    # Pre-populate two Jagakarsa listings with a clean run.
    _run(clean_repo, FakeFetcher([HOUSE, LAND])).execute()
    assert _count(clean_repo, "listings") == 2

    # Degraded run: index p1 returns only HOUSE, p2 errors (simulated network drop).
    class FlakyFetcher(Fetcher):
        def __init__(self) -> None:
            self.house = (FIXTURES / "rumah123_listing_house.html").read_text()
            self.index = _index_html([HOUSE])

        def get(self, url: str) -> str:
            if url == BASE + HOUSE:
                return self.house
            if "page=2" in url:
                raise FetchError("network drop")
            if "/jual/" in url:
                return self.index
            raise FetchError(url)

    config = Config(cities=("jakarta-selatan",), property_types=("rumah",))
    fetcher = FlakyFetcher()
    source = Rumah123Source(config, fetcher)
    stats = ScrapeRun(clean_repo, fetcher, source).execute()

    assert source.discovery_incomplete is True
    assert stats.status == "completed_with_errors"
    assert stats.delisted == 0
    # LAND was not re-seen but must stay active — no false delisting on a partial crawl.
    with clean_repo.conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM listings WHERE is_active")
        assert cur.fetchone()[0] == 2


def test_district_scope_drops_out_of_area(clean_repo):
    # Fixtures: house + land are Jagakarsa; apartment is Kuningan (an out-of-area ad).
    config = Config(cities=("jakarta-selatan",), property_types=("rumah",))
    fetcher = FakeFetcher([HOUSE, APART, LAND])
    source = Rumah123Source(config, fetcher, district="jagakarsa")
    stats = ScrapeRun(clean_repo, fetcher, source).execute()

    assert stats.found == 3
    assert stats.skipped == 1          # the Kuningan apartment dropped
    assert stats.new == 2              # only the two Jagakarsa listings saved
    assert _count(clean_repo, "listings") == 2
    with clean_repo.conn.cursor() as cur:
        cur.execute("SELECT DISTINCT district FROM listings")
        assert [r[0] for r in cur.fetchall()] == ["Jagakarsa"]
