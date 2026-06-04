"""Tests for the scraper.run CLI argument parsing and config overrides (Phase 6).

Offline only — these never build a fetcher or hit the network.
"""

from __future__ import annotations

import pytest

from scraper.config import JABODETABEK_CITIES
from scraper.run import _config_from_args, _parse_args


def test_parse_args_defaults() -> None:
    args = _parse_args([])
    assert args.dry_run is False
    assert args.limit is None
    assert args.max_pages == 150
    assert args.cities is None
    assert args.types is None


def test_parse_args_flags() -> None:
    args = _parse_args(
        ["--dry-run", "--limit", "5", "--cities", "bekasi,depok", "--types", "rumah",
         "--max-pages", "3"]
    )
    assert args.dry_run is True
    assert args.limit == 5
    assert args.max_pages == 3
    assert args.cities == "bekasi,depok"
    assert args.types == "rumah"


def test_config_from_args_applies_overrides() -> None:
    args = _parse_args(["--cities", "bekasi, depok", "--types", "rumah,tanah"])
    config = _config_from_args(args)
    assert config.cities == ("bekasi", "depok")  # trimmed + split
    assert config.property_types == ("rumah", "tanah")


def test_config_from_args_keeps_defaults_without_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config_from_args(_parse_args([]))
    assert config.cities == JABODETABEK_CITIES
    assert "rumah" in config.property_types
