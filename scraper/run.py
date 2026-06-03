"""Orchestrator: run one scrape end to end.

Wires the source (discover + parse), fetcher, normalizer, and repository together:

    discover URLs -> fetch each -> parse -> normalize -> upsert + record price change
                  -> reconcile delistings -> finalize the run with counts

A single bad listing is logged and skipped; it never aborts the run. Every run writes a
``scrape_runs`` row with the resulting counts.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

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

        try:
            for url in self._source.discover():
                if limit is not None and stats.found >= limit:
                    break
                stats.found += 1
                self._process(url, stats, dry_run=dry_run)

            if not dry_run:
                stats.delisted = self._repo.reconcile_delistings(
                    self._source.name, started_at
                )
                self._finish(stats, "completed")
        except Exception:
            stats.status = "failed"
            if not dry_run:
                self._finish(stats, "failed")
            raise

        self._log.info(
            "run %s done: found=%d new=%d updated=%d delisted=%d errors=%d",
            run_id,
            stats.found,
            stats.new,
            stats.updated,
            stats.delisted,
            stats.errors,
        )
        return stats

    def _process(self, url: str, stats: RunStats, *, dry_run: bool) -> None:
        try:
            html = self._fetcher.get(url)
            record = self._normalize(self._source.parse(html))
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


def build_scrape_run(config: Config, repository: Repository) -> ScrapeRun:
    """Construct a production ScrapeRun (httpx fetcher + Rumah123 source)."""
    fetcher = HttpxFetcher(config)
    source = Rumah123Source(config, fetcher)
    return ScrapeRun(repository, fetcher, source)
