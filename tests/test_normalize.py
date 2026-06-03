"""Tests for scraper.normalize (Phase 4). Unit rules + end-to-end on real fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from scraper.config import Config
from scraper.db.repository import _LISTING_COLS
from scraper.normalize import (
    _parse_area,
    _parse_int,
    _parse_price_text,
    _property_type,
    normalize,
)
from scraper.sources.rumah123 import Rumah123Source

FIXTURES = Path(__file__).parent / "fixtures"


def _raw(fixture: str) -> dict:
    source = Rumah123Source(Config(), fetcher=None)  # fetcher unused for parse
    return source.parse((FIXTURES / fixture).read_text())


# --- unit rules -------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [("6", 6), ("", None), (None, None), ("3 kamar", 3), ("0", 0)],
)
def test_parse_int(value, expected):
    assert _parse_int(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [("136 m²", 136.0), ("1.234 m²", 1234.0), ("88 m2", 88.0), ("", None), (None, None)],
)
def test_parse_area(value, expected):
    assert _parse_area(value) == expected


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("Rp 3,87 Miliar", 3_870_000_000),
        ("Rp 950 Juta", 950_000_000),
        ("Rp 1,5 Miliar", 1_500_000_000),
        ("", None),
    ],
)
def test_parse_price_text(tag, expected):
    assert _parse_price_text(tag) == expected


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Rumah", "house"),
        ("Apartemen", "apartment"),
        ("Tanah", "land"),
        ("Ruko", "shophouse"),
        ("Gudang", "warehouse"),
        ("Vila", "other"),
        ("", "other"),
        (None, "other"),
    ],
)
def test_property_type(label, expected):
    assert _property_type(label) == expected


# --- end-to-end on fixtures -------------------------------------------------------


def test_normalize_house():
    rec = normalize(_raw("rumah123_listing_house.html"))
    assert rec.listing_id == "hos41544728"
    assert rec.property_type == "house"
    assert rec.price_idr == 3_870_000_000
    assert rec.bedrooms == 6
    assert rec.bathrooms == 4
    assert rec.land_area_m2 == 136.0
    assert rec.building_area_m2 == 230.0
    assert rec.certificate == "SHM"
    assert rec.city == "Jakarta Selatan"
    # coords are obfuscated (lat == lon) -> dropped
    assert rec.latitude is None and rec.longitude is None
    assert rec.agent_name


def test_normalize_apartment_has_no_land():
    rec = normalize(_raw("rumah123_listing_apartment.html"))
    assert rec.property_type == "apartment"
    assert rec.bedrooms == 3
    assert rec.land_area_m2 is None       # apartments have no land
    assert rec.building_area_m2 == 88.0
    assert rec.certificate == "PPJB"
    assert rec.price_idr and rec.price_idr > 0


def test_normalize_land_has_no_rooms():
    rec = normalize(_raw("rumah123_listing_land.html"))
    assert rec.property_type == "land"
    assert rec.bedrooms is None           # land has no rooms
    assert rec.bathrooms is None
    assert rec.land_area_m2 == 519.0
    assert rec.building_area_m2 is None
    assert rec.certificate == "HGB"


def test_extra_specs_excludes_promoted_columns():
    rec = normalize(_raw("rumah123_listing_house.html"))
    # promoted fields live in their own columns, not in extra_specs
    for promoted in ("bedroom", "bathroom", "landSize", "builtSize", "certificate"):
        assert promoted not in rec.extra_specs
    # a non-promoted spec is captured (this house has electricalPower)
    assert rec.extra_specs.get("electricalPower")


def test_record_keys_match_repository_columns():
    """normalize() output must map exactly onto the columns upsert_listing writes."""
    rec = normalize(_raw("rumah123_listing_house.html"))
    assert set(rec.model_dump().keys()) == set(_LISTING_COLS)
