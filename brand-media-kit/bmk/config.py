"""Load and validate the two files an adopting project owns.

Everything invariant across products lives in brand.json; everything that must
differ lives in assets.json. Splitting them is not tidiness - it is what makes
"add a product" a one-entry edit that cannot accidentally move a margin.
"""

import json
import pathlib


class ConfigError(Exception):
    pass


def _read_json(path):
    path = pathlib.Path(path)
    if not path.is_file():
        raise ConfigError("config not found: {}".format(path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError("{} is not valid JSON: {}".format(path, exc))


def _require(obj, keys, where):
    if not isinstance(obj, dict):
        raise ConfigError("{} must be an object".format(where))
    for key in keys:
        if key not in obj:
            raise ConfigError("{} is missing required key: {}".format(where, key))


def load_brand(path):
    brand = _read_json(path)
    _require(brand, ["name", "palette", "fonts", "geometry", "budget_bytes"], "brand.json")
    _require(brand["palette"], ["primary", "primary_dark", "ink", "paper"], "brand.json palette")
    _require(brand["fonts"], ["display", "body", "mono"], "brand.json fonts")
    _require(
        brand["geometry"],
        ["master", "margin", "column", "subject_band_pct"],
        "brand.json geometry",
    )

    band = brand["geometry"]["subject_band_pct"]
    # The band is the vertical slice of the master every derived crop is
    # guaranteed to keep. Get it backwards and derive.py silently crops the
    # subject out of the tightest format - which nobody notices until the
    # WordPress.org listing is live.
    ok = (
        isinstance(band, list)
        and len(band) == 2
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in band)
        and 0 <= band[0] < band[1] <= 100
    )
    if not ok:
        raise ConfigError(
            "brand.json geometry subject_band_pct must be [low, high] with "
            "0 <= low < high <= 100, got {!r}".format(band)
        )

    master = brand["geometry"]["master"]
    if not (
        isinstance(master, list)
        and len(master) == 2
        and all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in master)
    ):
        raise ConfigError("brand.json geometry master must be [width, height] of positive ints")

    return brand


def load_assets(path):
    assets = _read_json(path)
    _require(assets, ["subjects", "targets"], "assets.json")

    subjects = assets["subjects"]
    if not isinstance(subjects, list) or not subjects:
        raise ConfigError("assets.json subjects must list at least one product")

    seen = set()
    for i, subject in enumerate(subjects):
        _require(subject, ["slug", "title", "tagline", "art"], "assets.json subjects[{}]".format(i))
        slug = subject["slug"]
        if slug in seen:
            raise ConfigError("assets.json has a duplicate slug: {}".format(slug))
        seen.add(slug)

    targets = assets["targets"]
    if not isinstance(targets, list) or not targets:
        raise ConfigError("assets.json targets must list at least one directory")

    return assets
