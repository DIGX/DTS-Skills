import json

import pytest

from bmk.config import ConfigError, load_assets, load_brand

GOOD_BRAND = {
    "name": "DTS",
    "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
    "fonts": {"display": "D.ttf", "body": "B.ttf", "mono": "M.ttf"},
    "geometry": {"master": [1376, 768], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
    "budget_bytes": 90000,
}

GOOD_ASSETS = {
    "subjects": [
        {"slug": "a", "title": "A", "tagline": "t", "art": "a thing"},
        {"slug": "b", "title": "B", "tagline": "t", "art": "another thing"},
    ],
    "targets": ["out"],
}


def write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def test_loads_a_good_brand(tmp_path):
    got = load_brand(write(tmp_path, "brand.json", GOOD_BRAND))
    assert got["geometry"]["column"] == 517


def test_missing_file_is_a_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_brand(tmp_path / "nope.json")


def test_malformed_json_is_a_config_error(tmp_path):
    p = tmp_path / "brand.json"
    p.write_text("{oops", encoding="utf-8")
    with pytest.raises(ConfigError, match="not valid JSON"):
        load_brand(p)


@pytest.mark.parametrize("key", ["name", "palette", "fonts", "geometry", "budget_bytes"])
def test_every_top_level_key_is_required(tmp_path, key):
    bad = {k: v for k, v in GOOD_BRAND.items() if k != key}
    with pytest.raises(ConfigError, match=key):
        load_brand(write(tmp_path, "brand.json", bad))


@pytest.mark.parametrize("key", ["primary", "primary_dark", "ink", "paper"])
def test_every_palette_key_is_required(tmp_path, key):
    bad = json.loads(json.dumps(GOOD_BRAND))
    del bad["palette"][key]
    with pytest.raises(ConfigError, match=key):
        load_brand(write(tmp_path, "brand.json", bad))


@pytest.mark.parametrize(
    "band",
    [[72, 28], [28, 28], [-1, 72], [28, 101], [28], [28, 50, 72], "28-72"],
)
def test_a_nonsensical_subject_band_is_rejected(tmp_path, band):
    bad = json.loads(json.dumps(GOOD_BRAND))
    bad["geometry"]["subject_band_pct"] = band
    with pytest.raises(ConfigError, match="subject_band_pct"):
        load_brand(write(tmp_path, "brand.json", bad))


def test_loads_good_assets(tmp_path):
    got = load_assets(write(tmp_path, "assets.json", GOOD_ASSETS))
    assert len(got["subjects"]) == 2


def test_empty_subjects_is_a_config_error(tmp_path):
    bad = {"subjects": [], "targets": ["out"]}
    with pytest.raises(ConfigError, match="at least one"):
        load_assets(write(tmp_path, "assets.json", bad))


def test_duplicate_slugs_are_rejected(tmp_path):
    # Two subjects sharing a slug means the second silently overwrites the
    # first's output files, and the operator gets 12 banners for 13 products.
    bad = json.loads(json.dumps(GOOD_ASSETS))
    bad["subjects"][1]["slug"] = "a"
    with pytest.raises(ConfigError, match="duplicate slug"):
        load_assets(write(tmp_path, "assets.json", bad))


@pytest.mark.parametrize("key", ["slug", "title", "tagline", "art"])
def test_every_subject_key_is_required(tmp_path, key):
    bad = json.loads(json.dumps(GOOD_ASSETS))
    del bad["subjects"][0][key]
    with pytest.raises(ConfigError, match=key):
        load_assets(write(tmp_path, "assets.json", bad))


def test_empty_targets_is_a_config_error(tmp_path):
    bad = json.loads(json.dumps(GOOD_ASSETS))
    bad["targets"] = []
    with pytest.raises(ConfigError, match="at least one"):
        load_assets(write(tmp_path, "assets.json", bad))
