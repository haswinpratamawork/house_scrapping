"""Source interface: how the pipeline discovers and parses listings for one site."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


class Source(ABC):
    """A property-listing source (one website)."""

    name: str

    @abstractmethod
    def discover(self) -> Iterator[str]:
        """Yield absolute URLs of listing detail pages to scrape this run."""

    @abstractmethod
    def parse(self, html: str) -> dict[str, Any]:
        """Parse a listing detail page's HTML into a raw record dict.

        Normalization into typed fields happens later (Phase 4); this returns the
        source's values close to as-found. Raises ValueError if no listing is found.
        """
