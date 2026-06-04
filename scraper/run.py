"""Orchestrator: run one scrape end to end.

Wires the source (discover + parse), fetcher, normalizer, and repository together:

    discover URLs -> fetch each -> parse -> normalize -> upsert + record price change
                  -> reconcile delistings -> finalize the run with counts

A single bad listing is logged and skipped; it never aborts the run. Every run writes a
``scrape_runs`` row with the resulting counts.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace

from scraper.config import Config
from scraper.db.repository import Repository
from scraper.fetch.base import Fetcher
from scraper.fetch.httpx_fetcher import HttpxFetcher
from scraper.models import ListingRecord
from scraper.normalize import normalize as default_normalize
from scraper.sources.base import Source
from scraper.sources.rumah123 import Rumah123Source

logger = logging.getLogger("scraper.run")


@dataclass
class RunStats:
    run_id: int | None = None
    found: int = 0
    new: int = 0
    updated: int = 0
    delisted: int = 0
    errors: int = 0
    skipped: int = 0  # out-of-scope listings dropped (e.g. promoted out-of-area ads)
    status: str = "completed"


class ScrapeRun:
    def __init__(
        self,
        repository: Repository,
        fetcher: Fetcher,
        source: Source,
        *,
        normalize: Callable[[dict], ListingRecord] = default_normalize,
        log: logging.Logger = logger,
    ) -> None:
        self._repo = repository
        self._fetcher = fetcher
        self._source = source
        self._normalize = normalize
        self._log = log

    def execute(self, *, limit: int | None = None, dry_run: bool = False) -> RunStats:
        run_id: int | None = None
        started_at = None
        if not dry_run:
            run_id, started_at = self._repo.start_run(self._source.name)
        stats = RunStats(run_id=run_id)
        seen_districts: set[str] = set()

        try:
            for url in self._source.discover():
                if limit is not None and stats.found >= limit:
                    break
                stats.found += 1
                self._process(url, stats, seen_districts, dry_run=dry_run)

            if not dry_run:
                # Only reconcile districts we actually scraped, so a per-district run
                # never delists the other districts.
                stats.delisted = self._repo.reconcile_delistings(
                    self._source.name, started_at, districts=sorted(seen_districts)
                )
                self._finish(stats, "completed")
        except Exception:
            stats.status = "failed"
            if not dry_run:
                self._finish(stats, "failed")
            raise

        self._log.info(
            "run %s done: found=%d new=%d updated=%d delisted=%d skipped=%d errors=%d",
            run_id,
            stats.found,
            stats.new,
            stats.updated,
            stats.delisted,
            stats.skipped,
            stats.errors,
        )
        return stats

    def _process(
        self, url: str, stats: RunStats, seen_districts: set[str], *, dry_run: bool
    ) -> None:
        try:
            html = self._fetcher.get(url)
            raw = self._source.parse(html)
            if not self._source.matches_scope(raw):
                stats.skipped += 1
                self._log.info("out-of-scope, skip %s", url)
                return
            record = self._normalize(raw)
        except Exception as exc:  # one bad listing must not abort the run
            stats.errors += 1
            self._log.warning("skip %s: %s", url, exc)
            return

        if dry_run:
            self._log.info("[dry-run] %s (%s)", record.listing_id, record.property_type)
            return

        result = self._repo.upsert_listing(record.model_dump())
        if result == "new":
            stats.new += 1
        else:
            stats.updated += 1
        if record.district:
            seen_districts.add(record.district)
        self._repo.record_price_if_changed(record.listing_id, record.price_idr)

    def _finish(self, stats: RunStats, status: str) -> None:
        if stats.run_id is None:
            return
        self._repo.finish_run(
            stats.run_id,
            status=status,
            found=stats.found,
            new=stats.new,
            updated=stats.updated,
            delisted=stats.delisted,
            errors=stats.errors,
        )


def build_scrape_run(
    config: Config,
    repository: Repository | None,
    *,
    max_pages: int = 150,
    district: str | None = None,
) -> ScrapeRun:
    """Construct a production ScrapeRun (httpx fetcher + Rumah123 source)."""
    fetcher = HttpxFetcher(config)
    source = Rumah123Source(config, fetcher, max_pages=max_pages, district=district)
    return ScrapeRun(repository, fetcher, source)


# --- command line -----------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scraper.run",
        description="Scrape Rumah123 property listings into PostgreSQL.",
    )
    parser.add_argument(
        "--cities", help="comma-separated city slugs (override config defaults)"
    )
    parser.add_argument(
        "--types", help="comma-separated property-type slugs (e.g. rumah,tanah)"
    )
    parser.add_argument(
        "--district",
        help="single district/kecamatan slug to scope within --cities (e.g. gambir)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=150, help="max index pages per city x type"
    )
    parser.add_argument(
        "--limit", type=int, help="stop after processing this many listings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="discover/fetch/parse but write nothing to the database",
    )
    parser.add_argument("--log-level", default="INFO", help="logging level")
    return parser.parse_args(argv)


def _config_from_args(args: argparse.Namespace) -> Config:
    config = Config.from_env()
    if args.cities:
        config = replace(config, cities=tuple(_split(args.cities)))
    if args.types:
        config = replace(config, property_types=tuple(_split(args.types)))
    return config


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = _config_from_args(args)

    repository: Repository | None = None
    if not args.dry_run:
        if not config.database_url:
            logger.error("DATABASE_URL is not set; cannot write results")
            return 2
        repository = Repository.connect(config.database_url)
        repository.apply_schema()

    try:
        run = build_scrape_run(
            config, repository, max_pages=args.max_pages, district=args.district
        )
        stats = run.execute(limit=args.limit, dry_run=args.dry_run)
    except Exception:
        logger.exception("scrape run failed")
        return 1
    finally:
        if repository is not None:
            repository.close()

    return 0 if stats.status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
