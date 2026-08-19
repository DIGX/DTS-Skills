# Brand Media Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `brand-media-kit`, a user-invocable skill in the DTS-Skills repo that turns one AI-generated 16:9 art master per product into every banner, header, hero and repository image a WordPress plugin needs, with every piece of typography composited in code so it is identical across products.

**Architecture:** A thin SKILL.md routes the operator through five stages, each a small Python module under `brand-media-kit/bmk/` run as `python bmk/<stage>.py`. `config.py` loads two JSON files from the adopting project's `.brandkit/` directory: `brand.json` (palette, fonts, geometry — the things that must never vary) and `assets.json` (one entry per product — the things that must). `generate.py` builds a prompt whose style paragraph is byte-identical for every product and differs only in a `SUBJECT:` clause, then either calls the Gemini image API or writes a manual handoff file. `composite.py` draws the text lockup onto the returned art with Pillow. `derive.py` centre-band-crops the one master into every wide format. `deploy.py` encodes WebP under a byte budget and fans the files out to every target directory. `verify.py` is the fence: it re-reads what actually landed on disk and fails on anything missing, mismatched, oversized, or accidentally identical.

**Tech Stack:** Python 3.9+, Pillow >= 10, pytest, bash, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-19-brand-media-kit-design.md` (commit `ebff6bb`)

**Repo / branch:** `DTS-Skills`, working on `feat/brand-media-kit`.

## Global Constraints

Every task's requirements implicitly include this section.

- **TDD is the one firm rule.** `CONTRIBUTING.md`: "No change to a skill without a failing test first." Every task below is written RED then GREEN then commit. Do not write implementation before you have watched its test fail for the right reason.
- **`description:` in SKILL.md frontmatter states *when to use the skill*, never what it does.** Trigger phrases only.
- **SKILL.md frontmatter must be at most 1024 bytes.** CI counts it. Over the cap the skill fails to load at runtime with no useful message.
- **Every skill directory must ship `scripts/install` and `scripts/selftest`.** CI asserts both by name.
- **Every backticked `reference/...` or `assets/...` path anywhere under the skill directory must resolve to a real file.** CI greps the whole directory, not just SKILL.md, so a path named inside a reference doc counts too.
- **Bash scripts:** `#!/usr/bin/env bash`, `set -uo pipefail`, tab indentation, `shellcheck -S warning -e SC1090,SC1091,SC2317` clean.
- **LF line endings** pinned in `.gitattributes` for every extensionless script, and CI greps for CR bytes.
- **Comments explain why, not what.** A comment restating the line above it is noise; a comment recording the trap that made the line necessary is the point.
- **`scripts/selftest` must spend no API quota and must pass offline.** No network, no Gemini call, no key required.
- **Python stages live at `brand-media-kit/bmk/*.py` and are invoked as `python bmk/<stage>.py`.** They are not chmod +x and must not depend on being executable: `scripts/install-skill` only sets the executable bit on files named `install`, `selftest`, `dispatch`, `tripwire`, `gates`, `review-pkg`, so an executable-invoked Python stage would ship non-executable and fail for every adopter.
- **`scripts/install` keeps its repo-conventional meaning:** it installs/scaffolds for the adopting project. Here that means writing `.brandkit/` from the shipped examples. Media deployment is `bmk/deploy.py`, not `scripts/install`.
- **Master reference size is 1376x768.** Every existing DTS card banner is exactly that, so it is the size the WordPress card CSS has always been fed.

## File Structure

```
brand-media-kit/
  SKILL.md                    routing: five stages, when to use each
  README.md                   what this is, for a human browsing the repo
  requirements.txt            Pillow>=10, pytest
  scripts/
    install                   scaffold .brandkit/ into an adopting project
    selftest                  offline: deps present, then pytest
  bmk/
    __init__.py
    config.py                 load + validate brand.json / assets.json
    fonts.py                  strict font loading (no silent fallback)
    layout.py                 measure, wrap, shrink-to-fit
    composite.py              draw the lockup onto art
    derive.py                 centre-band crop into every wide format
    deploy.py                 WebP under budget, fan out to targets
    verify.py                 the fence
    generate.py               prompt building, API call, manual handoff
  reference/
    prompt-recipe.md          the locked style paragraph and how to extend it
    layout-grid.md            the geometry: margins, column, band
    manual-handoff.md         the no-API-key path, incl. the human no-text check
    config-schema.md          every key in both JSON files
  assets/
    brand.example.json
    assets.example.json
  tests/
    conftest.py
    fixtures/BebasNeue-Regular.ttf
    test_config.py
    test_fonts.py
    test_layout.py
    test_composite.py
    test_derive.py
    test_deploy.py
    test_verify.py
    test_generate.py
    test_install_script.py
```

Split by responsibility. `layout.py` knows nothing about images, `composite.py` knows nothing about crops, and `verify.py` imports none of them — it only reads bytes off disk, which is the whole reason it can catch the others lying.

---

### Task 1: Skeleton, test harness, CI wiring

Nothing here is interesting on its own; every later task needs all of it. Fold it into one task so a reviewer gates it once.

**Files:**
- Create: `brand-media-kit/bmk/__init__.py`
- Create: `brand-media-kit/requirements.txt`
- Create: `brand-media-kit/pytest.ini`
- Create: `brand-media-kit/scripts/selftest`
- Create: `brand-media-kit/scripts/install` (stub)
- Create: `brand-media-kit/SKILL.md` (minimal)
- Create: `brand-media-kit/tests/conftest.py`
- Create: `brand-media-kit/tests/fixtures/BebasNeue-Regular.ttf` (downloaded)
- Create: `brand-media-kit/tests/test_harness.py`
- Modify: `.github/workflows/ci.yml`
- Modify: `.gitattributes`

**Interfaces:**
- Consumes: nothing.
- Produces: pytest fixtures `font_path` (a `pathlib.Path` to the Bebas Neue TTF) and `art_factory` (callable `(w: int, h: int, colour: tuple, name: str) -> pathlib.Path`, writes a solid PNG into the test's tmp dir and returns its path). Every later test file uses these.

- [ ] **Step 1: Create the directory skeleton and fetch the test font**

The suite must not depend on a system font — CI runners disagree about what is installed, and a substituted face would make the layout tests measure something other than what ships.

```bash
mkdir -p brand-media-kit/bmk brand-media-kit/scripts brand-media-kit/tests/fixtures \
         brand-media-kit/reference brand-media-kit/assets
: > brand-media-kit/bmk/__init__.py
curl -fsSL -o brand-media-kit/tests/fixtures/BebasNeue-Regular.ttf \
  https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf
file brand-media-kit/tests/fixtures/BebasNeue-Regular.ttf
```

Expected: `TrueType Font data`. If curl 404s the upstream path moved — find it under `https://github.com/google/fonts/tree/main/ofl/bebasneue` and do not substitute a different face.

- [ ] **Step 2: Write `requirements.txt` and `pytest.ini`**

`requirements.txt`:

```
Pillow>=10
pytest>=7
```

`pytest.ini` — without it, `import bmk` resolves only by luck of the rootdir:

```ini
[pytest]
testpaths = tests
```

- [ ] **Step 3: Write `tests/conftest.py`**

```python
"""Shared fixtures.

The font is vendored rather than resolved from the system: CI runners disagree
about what is installed, and Pillow silently substitutes a bitmap default when
a truetype load fails, which would make every layout assertion measure a font
that is not the one we ship.
"""

import pathlib
import sys

import pytest
from PIL import Image

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


@pytest.fixture
def font_path():
    path = FIXTURES / "BebasNeue-Regular.ttf"
    assert path.is_file(), "test font missing; see Task 1 of the plan"
    return path


@pytest.fixture
def art_factory(tmp_path):
    """Make a flat-colour PNG standing in for generated art."""

    def _make(w, h, colour, name):
        out = tmp_path / name
        Image.new("RGB", (w, h), colour).save(out)
        return out

    return _make
```

- [ ] **Step 4: Write the failing harness test**

```python
# brand-media-kit/tests/test_harness.py
from PIL import Image, ImageFont

import bmk


def test_package_imports():
    assert bmk is not None


def test_font_fixture_loads_at_a_real_size(font_path):
    font = ImageFont.truetype(str(font_path), 64)
    assert font.getlength("DTS") > 0


def test_art_factory_makes_the_size_asked_for(art_factory):
    path = art_factory(1376, 768, (10, 30, 60), "art.png")
    assert Image.open(path).size == (1376, 768)
```

- [ ] **Step 5: Run it and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_harness.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk'`, before `bmk/__init__.py` and `pytest.ini` are in place.

- [ ] **Step 6: Run it and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_harness.py -v`
Expected: 3 passed.

- [ ] **Step 7: Write `scripts/selftest`**

```bash
#!/usr/bin/env bash
#
# Offline. Spends no API quota and needs no key: CI runs this on every push,
# and a selftest that could bill someone is a selftest nobody runs.
set -uo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here" || exit 1

py=""
for c in python3 python; do
	if command -v "$c" >/dev/null 2>&1; then py="$c"; break; fi
done
if [ -z "$py" ]; then
	echo "FAIL: no python on PATH" >&2
	exit 1
fi

for mod in PIL pytest; do
	if ! "$py" -c "import $mod" 2>/dev/null; then
		echo "FAIL: $mod missing - pip install -r requirements.txt" >&2
		exit 1
	fi
done

"$py" -m pytest tests -q
rc=$?
[ "$rc" -eq 0 ] && echo "brand-media-kit selftest: OK"
exit "$rc"
```

- [ ] **Step 8: Write the `scripts/install` stub**

CI requires the file to exist from the first commit. Task 10 replaces the body.

```bash
#!/usr/bin/env bash
#
# Stub. Task 10 of docs/superpowers/plans/2026-08-19-brand-media-kit.md
# replaces this with the .brandkit scaffolder.
set -uo pipefail

echo "brand-media-kit: install not implemented yet" >&2
exit 78
```

Exit 78 is `EX_CONFIG` — "configured but not usable" — which reads correctly in a log and is not 0.

- [ ] **Step 9: Write a minimal `SKILL.md`**

CI validates frontmatter on every `*/SKILL.md` from this commit forward, and resolves every backticked `reference/` path in the directory — so ship no reference links yet.

```markdown
---
name: brand-media-kit
description: Use when product banners, plugin headers, hero images, or repository listing images look inconsistent across a family of products, or when adding a new product that needs artwork matching an existing set.
---

# Brand Media Kit

Under construction. See `docs/superpowers/plans/2026-08-19-brand-media-kit.md`.
```

- [ ] **Step 10: Wire CI**

In `.github/workflows/ci.yml`, add to the `selftest` job after the agy-agents step (currently lines 33-34):

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install brand-media-kit deps
        run: python -m pip install --quiet -r brand-media-kit/requirements.txt

      # Offline by construction: no key is set, so the generate stage's API
      # path is never reached.
      - name: Run the brand-media-kit selftest
        run: bash brand-media-kit/scripts/selftest
```

In the `lint` job, add both new scripts to the `bash -n` loop (lines 45-48) and to the `shellcheck` argument list (lines 56-60) — the same continuation line in each:

```
                   brand-media-kit/scripts/install brand-media-kit/scripts/selftest \
```

In the CRLF step, add the new glob to the `git ls-files` list on line 80:

```
          done < <(git ls-files 'agy-agents/assets/*' 'agy-agents/scripts/*' 'brand-media-kit/scripts/*' 'scripts/*' '*.sh' '*.ps1')
```

- [ ] **Step 11: Pin line endings**

Append to `.gitattributes`, after the `scripts/install-skill` line:

```
brand-media-kit/scripts/install     text eol=lf
brand-media-kit/scripts/selftest    text eol=lf
```

and at the end of the file:

```
# The vendored test font and any generated media are binary; normalization
# would corrupt them.
*.ttf       binary
*.webp      binary
*.png       binary
```

- [ ] **Step 12: Verify the harness locally**

```bash
bash -n brand-media-kit/scripts/install brand-media-kit/scripts/selftest
bash brand-media-kit/scripts/selftest
```
Expected: `brand-media-kit selftest: OK`.

- [ ] **Step 13: Commit**

```bash
git add brand-media-kit .github/workflows/ci.yml .gitattributes
git commit -m "feat(brand-media-kit): harness - vendor the font, because a fallback face measures the wrong thing"
```

---

### Task 2: `bmk/config.py` — the two JSON files

**Files:**
- Create: `brand-media-kit/bmk/config.py`
- Test: `brand-media-kit/tests/test_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class ConfigError(Exception)`
  - `load_brand(path) -> dict` — validated `brand.json`
  - `load_assets(path) -> dict` — validated `assets.json`

  Later stages take the returned dicts as plain dicts. No dataclass wrapper: the JSON is the schema of record, and a second representation would drift from it.

Validated `brand.json` shape:

```json
{
  "name": "DTS",
  "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
  "fonts": {"display": "BebasNeue-Regular.ttf", "body": "Montserrat-SemiBold.ttf", "mono": "JetBrainsMono-Regular.ttf"},
  "geometry": {"master": [1376, 768], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
  "budget_bytes": 90000
}
```

Validated `assets.json` shape:

```json
{
  "subjects": [
    {"slug": "dts-gst-invoice", "title": "GST INVOICE", "tagline": "Compliant invoicing for WooCommerce", "art": "a stylised invoice document"}
  ],
  "targets": ["../plugins/dts-gst-invoice/assets/images/dts-plugins"]
}
```

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_config.py
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
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.config'`.

- [ ] **Step 3: Implement `bmk/config.py`**

```python
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
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_config.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/config.py brand-media-kit/tests/test_config.py
git commit -m "feat(brand-media-kit): config - invariants in one file, differences in the other"
```

---

### Task 3: `bmk/fonts.py` — refuse to substitute

**Files:**
- Create: `brand-media-kit/bmk/fonts.py`
- Test: `brand-media-kit/tests/test_fonts.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class FontError(Exception)`
  - `load_font(path, size) -> PIL.ImageFont.FreeTypeFont`

This is the smallest module in the kit and the one most worth a task of its own. Pillow's habit, when a truetype load fails, is to let the caller fall back to `ImageFont.load_default()` — a bitmap face at a fixed size. A kit whose entire premise is "typography is identical across products" cannot silently render one product in a different face. The fail-safe direction is: no font, no output.

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_fonts.py
import pytest
from PIL import ImageFont

from bmk.fonts import FontError, load_font


def test_loads_a_real_font(font_path):
    font = load_font(font_path, 72)
    assert font.getlength("DTS") > 0


def test_a_missing_font_raises(tmp_path):
    with pytest.raises(FontError, match="font not found"):
        load_font(tmp_path / "nope.ttf", 72)


def test_a_corrupt_font_raises(tmp_path):
    bad = tmp_path / "bad.ttf"
    bad.write_bytes(b"this is not a font")
    with pytest.raises(FontError, match="could not be loaded"):
        load_font(bad, 72)


def test_it_never_falls_back_to_the_default_face(tmp_path, monkeypatch):
    # The whole point of the module. If a future edit adds a try/except that
    # reaches for load_default, this test detonates rather than shipping one
    # product rendered in a bitmap face nobody notices until print.
    def explode(*_args, **_kwargs):
        raise AssertionError("load_default must never be reached")

    monkeypatch.setattr(ImageFont, "load_default", explode)

    bad = tmp_path / "bad.ttf"
    bad.write_bytes(b"nope")
    with pytest.raises(FontError):
        load_font(bad, 72)


def test_a_nonpositive_size_raises(font_path):
    with pytest.raises(FontError, match="size"):
        load_font(font_path, 0)
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_fonts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.fonts'`.

- [ ] **Step 3: Implement `bmk/fonts.py`**

```python
"""Strict font loading.

Pillow raises OSError for an unreadable truetype file, and the conventional
response is to fall back to ImageFont.load_default(). That fallback is exactly
what this kit exists to prevent: one product silently rendered in a bitmap face
at the wrong size defeats the point of compositing text in code at all. So the
only fallback here is an exception.
"""

import pathlib

from PIL import ImageFont


class FontError(Exception):
    pass


def load_font(path, size):
    if not isinstance(size, int) or size <= 0:
        raise FontError("font size must be a positive int, got {!r}".format(size))

    path = pathlib.Path(path)
    if not path.is_file():
        raise FontError("font not found: {}".format(path))

    try:
        return ImageFont.truetype(str(path), size)
    except OSError as exc:
        raise FontError("font could not be loaded: {} ({})".format(path, exc))
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_fonts.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/fonts.py brand-media-kit/tests/test_fonts.py
git commit -m "feat(brand-media-kit): fonts - no font is an error, never a substitution"
```

---

### Task 4: `bmk/layout.py` — measure, wrap, shrink to fit

**Files:**
- Create: `brand-media-kit/bmk/layout.py`
- Test: `brand-media-kit/tests/test_layout.py`

**Interfaces:**
- Consumes: `bmk.fonts.load_font`.
- Produces:
  - `class LayoutError(Exception)`
  - `measure(draw, text, font) -> float` — advance width in px
  - `wrap(draw, text, font, max_width) -> list[str]` — greedy word wrap
  - `fit(draw, text, font_path, max_width, max_lines, size_hi, size_lo, step=2) -> tuple[list[str], PIL.ImageFont.FreeTypeFont]`

`fit` shrinks from `size_hi` toward `size_lo` until the wrapped text fits in `max_lines` at `max_width`, and raises if it never does. It never *grows* a short title to fill the column: a one-word product name set larger than a three-word one is precisely the inconsistency this kit exists to remove.

`COLUMN = 517` is the text column width in the 1376px master: `1376 - 96 (left margin) - 96 (gutter before the art) = 1184`, of which the lockup takes the left 517px so the art's subject, which sits right of centre, is never crowded. The full derivation is in `reference/layout-grid.md` (Task 10).

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_layout.py
import pytest
from PIL import Image, ImageDraw

from bmk.fonts import load_font
from bmk.layout import LayoutError, fit, measure, wrap


@pytest.fixture
def draw():
    return ImageDraw.Draw(Image.new("RGB", (1376, 768)))


def test_measure_grows_with_the_string(draw, font_path):
    font = load_font(font_path, 64)
    assert measure(draw, "DTS", font) < measure(draw, "DTS INVOICE", font)


def test_wrap_keeps_one_line_when_it_fits(draw, font_path):
    font = load_font(font_path, 48)
    assert wrap(draw, "GST INVOICE", font, 10000) == ["GST INVOICE"]


def test_wrap_breaks_on_words_not_characters(draw, font_path):
    font = load_font(font_path, 96)
    lines = wrap(draw, "ABANDONED CART RECOVERY", font, 400)
    assert len(lines) > 1
    assert " ".join(lines) == "ABANDONED CART RECOVERY"
    assert all(line == line.strip() for line in lines)


def test_a_single_word_wider_than_the_column_still_returns_it(draw, font_path):
    # Better to overflow visibly on one word than to hyphenate a product name.
    # fit() is what turns this into a shrink; wrap() must not lose characters.
    font = load_font(font_path, 200)
    assert wrap(draw, "SUPERCALIFRAGILISTIC", font, 50) == ["SUPERCALIFRAGILISTIC"]


def test_fit_shrinks_until_it_fits(draw, font_path):
    lines, font = fit(draw, "ABANDONED CART RECOVERY", font_path, 517, 2, 120, 40)
    assert len(lines) <= 2
    assert all(measure(draw, line, font) <= 517 for line in lines)
    assert font.size <= 120


def test_fit_never_grows_a_short_title(draw, font_path):
    _, small = fit(draw, "GST", font_path, 517, 2, 96, 40)
    _, big = fit(draw, "ABANDONED CART RECOVERY", font_path, 517, 2, 96, 40)
    assert small.size == 96
    assert big.size <= small.size


def test_fit_raises_when_nothing_fits(draw, font_path):
    with pytest.raises(LayoutError, match="does not fit"):
        fit(draw, "ABANDONED CART RECOVERY", font_path, 40, 1, 120, 100)


def test_fit_rejects_a_backwards_size_range(draw, font_path):
    with pytest.raises(LayoutError, match="size_hi"):
        fit(draw, "X", font_path, 517, 2, 40, 120)
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_layout.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.layout'`.

- [ ] **Step 3: Implement `bmk/layout.py`**

```python
"""Text geometry. Knows nothing about images beyond needing a draw context
for font metrics.

fit() shrinks and never grows. A one-word product name set larger than a
three-word one to "fill the space" is the exact inconsistency this kit was
built to remove, so the largest size any title can take is fixed by the brand,
not by how short the title happens to be.
"""

from bmk.fonts import load_font


class LayoutError(Exception):
    pass


def measure(draw, text, font):
    return draw.textlength(text, font=font)


def wrap(draw, text, font, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = "{} {}".format(current, word)
        if measure(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit(draw, text, font_path, max_width, max_lines, size_hi, size_lo, step=2):
    if size_hi < size_lo:
        raise LayoutError("size_hi ({}) must be >= size_lo ({})".format(size_hi, size_lo))

    for size in range(size_hi, size_lo - 1, -step):
        font = load_font(font_path, size)
        lines = wrap(draw, text, font, max_width)
        if len(lines) <= max_lines and all(measure(draw, line, font) <= max_width for line in lines):
            return lines, font

    raise LayoutError(
        "{!r} does not fit {}px x {} lines even at {}px".format(text, max_width, max_lines, size_lo)
    )
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_layout.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/layout.py brand-media-kit/tests/test_layout.py
git commit -m "feat(brand-media-kit): layout - shrink to fit, never grow to fill"
```

---

### Task 5: `bmk/composite.py` — draw the lockup

**Files:**
- Create: `brand-media-kit/bmk/composite.py`
- Test: `brand-media-kit/tests/test_composite.py`

**Interfaces:**
- Consumes: `bmk.fonts.load_font`, `bmk.layout.fit`, `bmk.layout.measure`.
- Produces:
  - `draw_tracked(draw, xy, text, font, fill, tracking) -> float` — draws letterspaced text, returns the advance width
  - `compose(art_path, subject, brand, fonts_root, out_path) -> pathlib.Path`

`draw_tracked` exists because Pillow has no letterspacing parameter at all, and Bebas Neue set without tracking reads as a solid block at banner sizes. Drawing glyph by glyph is the only way.

`compose` opens the art, converts to RGB, lays the title and tagline into the left column at the brand margin, and writes a PNG. It does not resize, crop or encode — `derive.py` and `deploy.py` do that.

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_composite.py
import pytest
from PIL import Image, ImageDraw

from bmk.composite import compose, draw_tracked
from bmk.fonts import load_font

BRAND = {
    "name": "DTS",
    "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
    "fonts": {"display": "BebasNeue-Regular.ttf", "body": "BebasNeue-Regular.ttf", "mono": "BebasNeue-Regular.ttf"},
    "geometry": {"master": [1376, 768], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
    "budget_bytes": 90000,
}

SUBJECT = {"slug": "gst", "title": "GST INVOICE", "tagline": "Compliant invoicing", "art": "an invoice"}


@pytest.fixture
def fonts_root(tmp_path, font_path):
    # compose() resolves brand["fonts"] names against a directory, so the test
    # supplies one holding the vendored face under the three brand names.
    root = tmp_path / "fonts"
    root.mkdir()
    (root / "BebasNeue-Regular.ttf").write_bytes(font_path.read_bytes())
    return root


def test_tracking_widens_the_line(font_path):
    draw = ImageDraw.Draw(Image.new("RGB", (1376, 768)))
    font = load_font(font_path, 64)
    tight = draw_tracked(draw, (0, 0), "DTS", font, (255, 255, 255), 0)
    loose = draw_tracked(draw, (0, 0), "DTS", font, (255, 255, 255), 6)
    assert loose > tight


def test_compose_writes_an_image_the_size_of_the_art(art_factory, fonts_root, tmp_path):
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    out = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "out.png")
    assert Image.open(out).size == (1376, 768)


def test_compose_is_deterministic(art_factory, fonts_root, tmp_path):
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    a = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "a.png")
    b = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "b.png")
    assert a.read_bytes() == b.read_bytes()


def test_different_subjects_produce_different_pixels(art_factory, fonts_root, tmp_path):
    # Guards the failure where every product gets the same banner because the
    # subject was read from the wrong variable. deploy.py's duplicate check
    # catches this too, but by then the operator has already generated 13
    # images and paid for them.
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    other = dict(SUBJECT, slug="cart", title="ABANDONED CART", tagline="Recover lost sales")
    a = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "a.png")
    b = compose(art, other, BRAND, fonts_root, tmp_path / "b.png")
    assert a.read_bytes() != b.read_bytes()


def test_ink_stays_inside_the_left_column(art_factory, fonts_root, tmp_path):
    # Solid black art, so every non-black pixel is text this module drew. If
    # the lockup runs past the column it collides with the art's subject on
    # the right, and on the plugin home header it collides with the live HTML
    # h1 that WordPress renders on top.
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    long_title = dict(SUBJECT, title="ABANDONED CART RECOVERY", tagline="Recover lost sales automatically for stores")
    out = compose(art, long_title, BRAND, fonts_root, tmp_path / "out.png")

    img = Image.open(out).convert("RGB")
    bbox = Image.eval(img, lambda v: v).getbbox()  # non-black extent
    assert bbox is not None, "compose drew nothing"
    left, _, right, _ = bbox
    margin = BRAND["geometry"]["margin"]
    column = BRAND["geometry"]["column"]
    assert left >= margin - 4          # a few px of glyph bearing is fine
    assert right <= margin + column + 4
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_composite.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.composite'`.

- [ ] **Step 3: Implement `bmk/composite.py`**

```python
"""Draw the text lockup onto generated art.

Everything the eye reads as "brand" - face, size, tracking, colour, position -
is decided here in code rather than by the image model, because a model cannot
hold typography constant across thirteen separate generations. The art carries
the mood; this module carries the identity.
"""

import pathlib

from PIL import Image, ImageDraw

from bmk.fonts import load_font
from bmk.layout import fit, measure

TITLE_HI = 96
TITLE_LO = 48
TITLE_LINES = 2
TITLE_TRACKING = 4

TAGLINE_SIZE_HI = 30
TAGLINE_SIZE_LO = 20
TAGLINE_LINES = 2
TAGLINE_TRACKING = 1

TITLE_TOP_PCT = 0.34
LINE_GAP = 1.06
BLOCK_GAP = 22


def _rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_tracked(draw, xy, text, font, fill, tracking):
    """Pillow has no letterspacing, and Bebas Neue set solid reads as a slab
    at banner sizes. Drawing glyph by glyph is the only way to get tracking."""
    x, y = xy
    start = x
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += measure(draw, ch, font) + tracking
    # Trailing tracking is not part of the visible run.
    return max(0.0, (x - tracking) - start) if text else 0.0


def compose(art_path, subject, brand, fonts_root, out_path):
    fonts_root = pathlib.Path(fonts_root)
    out_path = pathlib.Path(out_path)

    img = Image.open(art_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    margin = brand["geometry"]["margin"]
    column = brand["geometry"]["column"]
    paper = _rgb(brand["palette"]["paper"])
    primary = _rgb(brand["palette"]["primary"])

    display_path = fonts_root / brand["fonts"]["display"]
    body_path = fonts_root / brand["fonts"]["body"]

    # Tracking eats horizontal room, so fit() is given the column minus the
    # worst case it could add. Without this the longest title fits at measure
    # time and overflows at draw time.
    title_budget = column - TITLE_TRACKING * 12
    title_lines, title_font = fit(
        draw, subject["title"], display_path, title_budget, TITLE_LINES, TITLE_HI, TITLE_LO
    )

    tagline_budget = column - TAGLINE_TRACKING * 12
    tagline_lines, tagline_font = fit(
        draw,
        subject["tagline"],
        body_path,
        tagline_budget,
        TAGLINE_LINES,
        TAGLINE_SIZE_HI,
        TAGLINE_SIZE_LO,
    )

    y = int(img.height * TITLE_TOP_PCT)
    for line in title_lines:
        draw_tracked(draw, (margin, y), line, title_font, paper, TITLE_TRACKING)
        y += int(title_font.size * LINE_GAP)

    y += BLOCK_GAP
    for line in tagline_lines:
        draw_tracked(draw, (margin, y), line, tagline_font, primary, TAGLINE_TRACKING)
        y += int(tagline_font.size * LINE_GAP)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_composite.py -v`
Expected: 5 passed. If `test_ink_stays_inside_the_left_column` fails on the right bound, reduce `TITLE_TRACKING` or widen the subtraction in `title_budget` — do not widen the assertion.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/composite.py brand-media-kit/tests/test_composite.py
git commit -m "feat(brand-media-kit): composite - the art carries mood, the code carries identity"
```

---

### Task 6: `bmk/derive.py` — one master, every wide format

**Files:**
- Create: `brand-media-kit/bmk/derive.py`
- Test: `brand-media-kit/tests/test_derive.py`

**Interfaces:**
- Consumes: nothing beyond Pillow.
- Produces:
  - `class DeriveError(Exception)`
  - `FORMATS: dict[str, tuple[int, int]]`
  - `centre_band(size, target_w, target_h) -> tuple[int, int, int, int]` — the crop box
  - `band_bounds_pct(size, target_w, target_h) -> tuple[float, float]` — what vertical slice of the master survives, as percentages
  - `derive(master_path, out_dir, formats=None) -> dict[str, pathlib.Path]`

`FORMATS`:

| key | size | where it lands |
|---|---|---|
| `card` | 1376x768 | the DTS Plugins Home card grid (16:9, `object-fit: cover`) |
| `header` | 1376x400 | the plugin home page header (`background: center right` under a scrim) |
| `hero` | 1920x480 | wide marketing hero |
| `wporg-banner` | 1544x500 | WordPress.org plugin banner |
| `wporg-banner-sm` | 772x250 | WordPress.org small banner |

Every one is wider than 16:9 except `card`, so a centre-band crop from a single 16:9 master serves all of them. The tightest is `hero` at 4:1, which keeps 250/768 = 32.5% of the master's height... which is why the art prompt confines the subject to the 28-72% band: that band survives every crop in the table.

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_derive.py
import pytest
from PIL import Image

from bmk.derive import FORMATS, DeriveError, band_bounds_pct, centre_band, derive


def test_every_format_is_produced_at_its_exact_size(art_factory, tmp_path):
    master = art_factory(1376, 768, (10, 30, 60), "master.png")
    out = derive(master, tmp_path / "out")
    assert set(out) == set(FORMATS)
    for key, path in out.items():
        assert Image.open(path).size == FORMATS[key], key


def test_the_crop_is_vertically_centred(art_factory):
    master = art_factory(1376, 768, (0, 0, 0), "m.png")
    left, top, right, bottom = centre_band((1376, 768), 1920, 480)
    assert left == 0 and right == 1376
    assert abs(top - (768 - (bottom - top)) / 2) <= 1


def test_the_subject_band_survives_the_tightest_crop():
    # The prompt tells the model to keep the subject between 28% and 72% of
    # the frame height. If any format's surviving band is narrower than that,
    # the prompt and the crop maths have drifted apart and some product will
    # ship with its subject sliced off.
    for key, (w, h) in FORMATS.items():
        low, high = band_bounds_pct((1376, 768), w, h)
        assert low <= 28.0 + 0.5, key
        assert high >= 72.0 - 0.5, key


def test_the_tightest_format_is_about_a_quarter_band():
    low, high = band_bounds_pct((1376, 768), 1920, 480)
    assert 27.0 <= low <= 28.0
    assert 72.0 <= high <= 73.0


def test_a_master_smaller_than_a_target_raises(art_factory, tmp_path):
    # Upscaling an AI image past its native resolution produces mush that
    # looks fine at review size and terrible on the WordPress.org listing.
    small = art_factory(400, 225, (0, 0, 0), "small.png")
    with pytest.raises(DeriveError, match="too small"):
        derive(small, tmp_path / "out")


def test_a_non_16_9_master_raises(art_factory, tmp_path):
    square = art_factory(1024, 1024, (0, 0, 0), "square.png")
    with pytest.raises(DeriveError, match="16:9"):
        derive(square, tmp_path / "out")
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_derive.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.derive'`.

- [ ] **Step 3: Implement `bmk/derive.py`**

```python
"""One 16:9 master becomes every wide format by a centre-band crop.

Generating each format separately would mean each is a different image, which
is how the current banners ended up with no family resemblance. Cropping one
master guarantees the family resemblance is literal - it is the same picture.

The cost is that the subject must live in the vertical band every crop keeps.
The tightest format here is 4:1, which keeps roughly 28%-72% of the master's
height, and that is exactly the band the generation prompt asks for.
"""

import pathlib

from PIL import Image

FORMATS = {
    "card": (1376, 768),
    "header": (1376, 400),
    "hero": (1920, 480),
    "wporg-banner": (1544, 500),
    "wporg-banner-sm": (772, 250),
}

ASPECT_TOLERANCE = 0.02


class DeriveError(Exception):
    pass


def centre_band(size, target_w, target_h):
    src_w, src_h = size
    band_h = int(round(src_w * target_h / float(target_w)))
    if band_h > src_h:
        # Target is taller than the master's aspect: keep full height and
        # crop width instead, still centred.
        band_w = int(round(src_h * target_w / float(target_h)))
        left = (src_w - band_w) // 2
        return (left, 0, left + band_w, src_h)

    top = (src_h - band_h) // 2
    return (0, top, src_w, top + band_h)


def band_bounds_pct(size, target_w, target_h):
    _, src_h = size
    _, top, _, bottom = centre_band(size, target_w, target_h)
    return (100.0 * top / src_h, 100.0 * bottom / src_h)


def derive(master_path, out_dir, formats=None):
    formats = FORMATS if formats is None else formats
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master = Image.open(master_path).convert("RGB")
    src_w, src_h = master.size

    if abs((src_w / float(src_h)) - (16.0 / 9.0)) > ASPECT_TOLERANCE:
        raise DeriveError(
            "master must be 16:9, got {}x{} ({:.3f})".format(src_w, src_h, src_w / float(src_h))
        )

    written = {}
    for key, (w, h) in formats.items():
        if w > src_w or h > src_h:
            raise DeriveError(
                "master {}x{} is too small for format {} ({}x{}); "
                "upscaling AI art past its native size looks fine at review "
                "size and terrible in the listing".format(src_w, src_h, key, w, h)
            )
        box = centre_band(master.size, w, h)
        out = out_dir / "{}.png".format(key)
        master.crop(box).resize((w, h), Image.LANCZOS).save(out)
        written[key] = out

    return written
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_derive.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/derive.py brand-media-kit/tests/test_derive.py
git commit -m "feat(brand-media-kit): derive - the family resemblance is literal, it is one picture"
```

---

### Task 7: `bmk/deploy.py` — WebP under budget, fanned out

**Files:**
- Create: `brand-media-kit/bmk/deploy.py`
- Test: `brand-media-kit/tests/test_deploy.py`

**Interfaces:**
- Consumes: nothing beyond Pillow.
- Produces:
  - `class BudgetError(Exception)`
  - `to_webp(src, out, budget_bytes, q_hi=92, q_lo=55, step=4) -> pathlib.Path`
  - `fan_out(src, targets, name) -> list[pathlib.Path]`

Existing DTS banners run 13KB-79KB, so a 90KB default budget is generous without letting a 400KB banner into a WordPress admin page.

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_deploy.py
import pytest
from PIL import Image

from bmk.deploy import BudgetError, fan_out, to_webp


def test_it_writes_a_webp(art_factory, tmp_path):
    src = art_factory(1376, 768, (34, 113, 177), "a.png")
    out = to_webp(src, tmp_path / "a.webp", 90000)
    assert out.is_file()
    assert Image.open(out).format == "WEBP"


def test_it_stays_under_budget(art_factory, tmp_path):
    src = art_factory(1376, 768, (34, 113, 177), "a.png")
    out = to_webp(src, tmp_path / "a.webp", 90000)
    assert out.stat().st_size <= 90000


def test_it_preserves_the_pixel_dimensions(art_factory, tmp_path):
    src = art_factory(1544, 500, (34, 113, 177), "a.png")
    out = to_webp(src, tmp_path / "a.webp", 90000)
    assert Image.open(out).size == (1544, 500)


def test_an_unmeetable_budget_raises(art_factory, tmp_path):
    # Silently shipping an over-budget file is the failure mode that matters:
    # nobody reads the byte count, they just notice the admin page got slow.
    src = art_factory(1920, 480, (34, 113, 177), "a.png")
    with pytest.raises(BudgetError, match="budget"):
        to_webp(src, tmp_path / "a.webp", 50)


def test_fan_out_writes_one_copy_per_target(art_factory, tmp_path):
    src = art_factory(64, 36, (0, 0, 0), "a.png")
    targets = [tmp_path / "one", tmp_path / "two", tmp_path / "three"]
    written = fan_out(src, targets, "banner.png")
    assert len(written) == 3
    assert all(p.is_file() for p in written)
    assert all(p.name == "banner.png" for p in written)


def test_fan_out_copies_are_byte_identical(art_factory, tmp_path):
    src = art_factory(64, 36, (0, 0, 0), "a.png")
    written = fan_out(src, [tmp_path / "one", tmp_path / "two"], "banner.png")
    assert written[0].read_bytes() == written[1].read_bytes() == src.read_bytes()


def test_fan_out_creates_missing_directories(art_factory, tmp_path):
    src = art_factory(64, 36, (0, 0, 0), "a.png")
    deep = tmp_path / "plugins" / "new-plugin" / "assets" / "images"
    written = fan_out(src, [deep], "banner.png")
    assert written[0].is_file()
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_deploy.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.deploy'`.

- [ ] **Step 3: Implement `bmk/deploy.py`**

```python
"""Encode to WebP under a byte budget, then copy into every target directory.

Pillow's WebP encoder has no "hit this size" mode, so the budget is met by
descending quality until the file fits. Failing loudly when it never fits is
the point: an over-budget banner is invisible in review and obvious to anyone
loading the WordPress admin over a slow link.
"""

import pathlib
import shutil

from PIL import Image


class BudgetError(Exception):
    pass


def to_webp(src, out, budget_bytes, q_hi=92, q_lo=55, step=4):
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")

    best = None
    for q in range(q_hi, q_lo - 1, -step):
        img.save(out, "WEBP", quality=q, method=6)
        size = out.stat().st_size
        if size <= budget_bytes:
            return out
        best = size

    raise BudgetError(
        "{} will not fit {} bytes; smallest at quality {} was {} bytes".format(
            pathlib.Path(src).name, budget_bytes, q_lo, best
        )
    )


def fan_out(src, targets, name):
    src = pathlib.Path(src)
    written = []
    for target in targets:
        target = pathlib.Path(target)
        target.mkdir(parents=True, exist_ok=True)
        dest = target / name
        # copyfile, not copy2: copy2 carries mtimes across, and verify.py's
        # identity check would then depend on the clock rather than on bytes.
        shutil.copyfile(src, dest)
        written.append(dest)
    return written
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_deploy.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/deploy.py brand-media-kit/tests/test_deploy.py
git commit -m "feat(brand-media-kit): deploy - a budget that raises, because nobody reads byte counts"
```

---

### Task 8: `bmk/verify.py` — the fence

**Files:**
- Create: `brand-media-kit/bmk/verify.py`
- Test: `brand-media-kit/tests/test_verify.py`

**Interfaces:**
- Consumes: nothing. Deliberately imports no other `bmk` module — it re-reads bytes off disk, which is the only reason it can catch the other modules being wrong.
- Produces:
  - `verify(expected, roots, budget_bytes) -> list[str]` — a list of human-readable problems, empty when clean.
  - `expected` is `{filename: (width, height)}`; `roots` is a list of directories each of which must hold every file.

This repo's characteristic failure is a fence that reports clean while guarding nothing: an empty loop passes, a `for f in $(missing)` passes, a check that never runs passes. So the first tests here are the ones asserting that `verify` fails when given nothing to check.

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_verify.py
import pytest
from PIL import Image

from bmk.verify import verify

EXPECTED = {"card.webp": (1376, 768), "header.webp": (1376, 400)}


def put(root, name, size, colour=(34, 113, 177)):
    root.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, colour).save(root / name, "WEBP", quality=80)
    return root / name


@pytest.fixture
def clean(tmp_path):
    roots = [tmp_path / "a", tmp_path / "b"]
    for i, name in enumerate(EXPECTED):
        img = Image.new("RGB", EXPECTED[name], (34, 113 + i * 40, 177))
        for root in roots:
            root.mkdir(parents=True, exist_ok=True)
            img.save(root / name, "WEBP", quality=80)
    return roots


def test_a_clean_tree_reports_nothing(clean):
    assert verify(EXPECTED, clean, 90000) == []


def test_an_empty_expected_set_is_itself_a_failure(clean):
    # A fence given nothing to check must not report clean. This repo has
    # shipped that bug before; it is why this test is first.
    problems = verify({}, clean, 90000)
    assert problems
    assert any("nothing to verify" in p for p in problems)


def test_no_roots_is_itself_a_failure():
    problems = verify(EXPECTED, [], 90000)
    assert problems
    assert any("no target" in p for p in problems)


def test_a_missing_file_is_reported(clean):
    (clean[1] / "header.webp").unlink()
    problems = verify(EXPECTED, clean, 90000)
    assert any("header.webp" in p and "missing" in p for p in problems)


def test_a_missing_root_is_reported(tmp_path, clean):
    problems = verify(EXPECTED, clean + [tmp_path / "ghost"], 90000)
    assert any("ghost" in p for p in problems)


def test_two_products_with_identical_bytes_are_reported(tmp_path):
    # The exact defect in the current DTS set: dts-banner-default.webp and
    # dts-shipment-tracking.webp are the same 78792 bytes, so one product is
    # wearing another's picture.
    root = tmp_path / "a"
    img = Image.new("RGB", (1376, 768), (34, 113, 177))
    root.mkdir(parents=True)
    img.save(root / "card.webp", "WEBP", quality=80)
    img.save(root / "header.webp", "WEBP", quality=80)
    problems = verify({"card.webp": (1376, 768), "header.webp": (1376, 768)}, [root], 90000)
    assert any("identical" in p for p in problems)


def test_copies_that_differ_between_roots_are_reported(clean):
    # Same name, different bytes across plugin directories is how the set
    # silently drifts out of sync one deploy at a time.
    Image.new("RGB", (1376, 768), (200, 10, 10)).save(clean[1] / "card.webp", "WEBP", quality=80)
    problems = verify(EXPECTED, clean, 90000)
    assert any("card.webp" in p and "differ" in p for p in problems)


def test_a_wrong_size_is_reported(clean):
    put(clean[0], "card.webp", (800, 600))
    problems = verify(EXPECTED, clean, 90000)
    assert any("card.webp" in p and "1376x768" in p for p in problems)


def test_an_over_budget_file_is_reported(clean):
    problems = verify(EXPECTED, clean, 100)
    assert any("budget" in p for p in problems)
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_verify.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.verify'`.

- [ ] **Step 3: Implement `bmk/verify.py`**

```python
"""The fence.

Imports no other bmk module on purpose. Every other stage reports what it
believes it did; this one re-reads what is actually on disk. A checker that
shares code with the thing it checks inherits its bugs.

The refusal to pass on an empty input set is the whole design. A fence that
reports clean because it was handed nothing is worse than no fence, because
it is trusted.
"""

import hashlib
import pathlib

from PIL import Image


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(expected, roots, budget_bytes):
    problems = []

    if not expected:
        problems.append("nothing to verify: the expected file set is empty")
    if not roots:
        problems.append("no target directories given")
    if problems:
        return problems

    digests = {}

    for root in roots:
        root = pathlib.Path(root)
        if not root.is_dir():
            problems.append("target directory is missing: {}".format(root))
            continue

        for name, size in expected.items():
            path = root / name
            if not path.is_file():
                problems.append("missing: {}".format(path))
                continue

            actual = path.stat().st_size
            if actual > budget_bytes:
                problems.append(
                    "over budget: {} is {} bytes, limit {}".format(path, actual, budget_bytes)
                )

            try:
                with Image.open(path) as img:
                    got = img.size
            except OSError as exc:
                problems.append("unreadable: {} ({})".format(path, exc))
                continue

            if got != tuple(size):
                problems.append(
                    "wrong size: {} is {}x{}, expected {}x{}".format(
                        path, got[0], got[1], size[0], size[1]
                    )
                )

            digests.setdefault(name, {})[str(root)] = _digest(path)

    # Same name, different bytes across roots: the set has drifted out of sync.
    for name, by_root in digests.items():
        if len(set(by_root.values())) > 1:
            problems.append(
                "copies differ between targets: {} ({})".format(name, ", ".join(sorted(by_root)))
            )

    # Different names, same bytes: one product is wearing another's picture.
    first_seen = {}
    for name, by_root in sorted(digests.items()):
        for root, digest in sorted(by_root.items()):
            if digest in first_seen and first_seen[digest] != name:
                problems.append(
                    "identical images for different assets: {} and {}".format(first_seen[digest], name)
                )
            first_seen.setdefault(digest, name)

    return problems
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_verify.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/verify.py brand-media-kit/tests/test_verify.py
git commit -m "feat(brand-media-kit): verify - a fence handed nothing must not report clean"
```

---

### Task 9: `bmk/generate.py` — one style paragraph, thirteen subjects

**Files:**
- Create: `brand-media-kit/bmk/generate.py`
- Test: `brand-media-kit/tests/test_generate.py`

**Interfaces:**
- Consumes: `bmk.config`.
- Produces:
  - `STYLE` — the locked style paragraph, a module constant
  - `has_api_key(env=None) -> bool`
  - `build_prompt(subject, brand) -> str`
  - `handoff(subjects, brand, out_dir) -> pathlib.Path` — writes a numbered prompt file for pasting into the Gemini app
  - `missing_art(subjects, art_dir) -> list[str]` — slugs with no `<slug>.png` yet
  - `generate_via_api(subject, brand, out_path, model="gemini-3-pro-image") -> pathlib.Path`

Two paths, because a consumer Gemini Pro subscription does not grant API access — AI Studio keys are billed separately. With a key, `generate_via_api` runs. Without one, `handoff` writes the prompts and the operator pastes them into the Gemini app and drops the returned PNGs into the art directory. Both paths use the same `build_prompt`, so the manual path cannot drift from the automated one.

`generate_via_api` imports `google.genai` lazily inside the function so the module imports, and the whole suite runs, with the SDK absent. The selftest must never reach it.

- [ ] **Step 1: Write the failing tests**

```python
# brand-media-kit/tests/test_generate.py
import pytest

from bmk.generate import STYLE, build_prompt, handoff, has_api_key, missing_art

BRAND = {
    "name": "DTS",
    "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
    "fonts": {"display": "D.ttf", "body": "B.ttf", "mono": "M.ttf"},
    "geometry": {"master": [1376, 768], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
    "budget_bytes": 90000,
}

SUBJECTS = [
    {"slug": "gst", "title": "GST INVOICE", "tagline": "t", "art": "a stylised invoice document"},
    {"slug": "cart", "title": "ABANDONED CART", "tagline": "t", "art": "a shopping cart mid-motion"},
]


def test_every_prompt_shares_a_byte_identical_style_paragraph():
    # This is the whole mechanism. If the style paragraph is ever built by
    # interpolation rather than copied verbatim, thirteen products drift
    # apart again and the kit has failed at its only job.
    prompts = [build_prompt(s, BRAND) for s in SUBJECTS]
    assert all(STYLE in p for p in prompts)
    assert len(set(prompts)) == len(prompts)


def test_the_prompt_carries_the_subject_clause():
    prompt = build_prompt(SUBJECTS[0], BRAND)
    assert "a stylised invoice document" in prompt
    assert "SUBJECT:" in prompt


def test_the_prompt_forbids_text_in_the_art():
    # Model-rendered lettering is the failure this kit is built around: it
    # arrives in a different face every generation and often misspelled.
    prompt = build_prompt(SUBJECTS[0], BRAND)
    lowered = prompt.lower()
    assert "no text" in lowered
    assert "no letter" in lowered or "no lettering" in lowered


def test_the_prompt_states_the_quiet_left_and_the_subject_band():
    prompt = build_prompt(SUBJECTS[0], BRAND)
    assert "left" in prompt.lower()
    assert "28" in prompt and "72" in prompt


def test_the_prompt_states_the_master_size():
    assert "1376" in build_prompt(SUBJECTS[0], BRAND)


def test_has_api_key_reads_the_environment():
    assert has_api_key({"GEMINI_API_KEY": "x"}) is True
    assert has_api_key({"GOOGLE_API_KEY": "x"}) is True
    assert has_api_key({}) is False
    assert has_api_key({"GEMINI_API_KEY": ""}) is False


def test_handoff_writes_one_numbered_block_per_subject(tmp_path):
    out = handoff(SUBJECTS, BRAND, tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "1." in text and "2." in text
    for s in SUBJECTS:
        assert s["slug"] in text
        assert s["art"] in text


def test_missing_art_lists_only_the_slugs_without_a_file(tmp_path):
    (tmp_path / "gst.png").write_bytes(b"x")
    assert missing_art(SUBJECTS, tmp_path) == ["cart"]


def test_the_module_imports_without_the_sdk():
    # The selftest runs offline on CI with no google-genai installed. If the
    # import moves to module scope, every test in the suite fails on a
    # machine that has no SDK - which is every CI runner.
    import importlib

    import bmk.generate

    importlib.reload(bmk.generate)


def test_generate_via_api_is_never_reached_without_a_key(monkeypatch, tmp_path):
    from bmk import generate

    def explode(*_a, **_k):
        raise AssertionError("the API path must not run in the offline suite")

    monkeypatch.setattr(generate, "generate_via_api", explode)
    assert has_api_key({}) is False
```

- [ ] **Step 2: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_generate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bmk.generate'`.

- [ ] **Step 3: Implement `bmk/generate.py`**

```python
"""Build the image prompt and get art back, by API or by hand.

The style paragraph below is a constant, not a template. Every product's
prompt embeds these exact bytes and differs only in one SUBJECT clause. That
is the entire consistency mechanism on the art side - the moment the style
text is assembled per product, the products drift apart again.

Two paths exist because a consumer Gemini Pro subscription does not include
API access; AI Studio keys are billed separately. Both paths call
build_prompt, so the manual route cannot drift from the automated one.
"""

import os
import pathlib

STYLE = (
    "Dark technical illustration, deep navy-to-black gradient background, "
    "thin luminous cyan and azure line-work, subtle circuit-like geometry, "
    "soft volumetric glow, shallow depth of field, high contrast, no grain, "
    "flat vector-adjacent rendering with a faint glass reflection. "
    "Composition: the left 40 percent of the frame is quiet - background "
    "gradient only, no detail, nothing that competes with overlaid type. "
    "The subject sits right of centre. "
    "Absolutely no text, no letters, no lettering, no numerals, no logos, "
    "no watermarks, no UI chrome anywhere in the image."
)

CONSTRAINTS = (
    "Output a single image, {w} x {h} pixels, 16:9. "
    "Keep the subject entirely between {low} percent and {high} percent of the "
    "frame height, because every derived crop keeps only that vertical band."
)


class GenerateError(Exception):
    pass


def has_api_key(env=None):
    env = os.environ if env is None else env
    return bool(env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY"))


def build_prompt(subject, brand):
    w, h = brand["geometry"]["master"]
    low, high = brand["geometry"]["subject_band_pct"]
    return "{}\n\nSUBJECT: {}\n\n{}".format(
        STYLE,
        subject["art"],
        CONSTRAINTS.format(w=w, h=h, low=low, high=high),
    )


def handoff(subjects, brand, out_dir):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "PROMPTS.md"

    blocks = ["# Image prompts", "", "Paste each block into the Gemini app, then save the returned",
              "image as `<slug>.png` in this directory. See reference/manual-handoff.md.", ""]
    for i, subject in enumerate(subjects, 1):
        blocks.append("## {}. {}".format(i, subject["slug"]))
        blocks.append("")
        blocks.append("```")
        blocks.append(build_prompt(subject, brand))
        blocks.append("```")
        blocks.append("")

    out.write_text("\n".join(blocks), encoding="utf-8")
    return out


def missing_art(subjects, art_dir):
    art_dir = pathlib.Path(art_dir)
    return [s["slug"] for s in subjects if not (art_dir / "{}.png".format(s["slug"])).is_file()]


def generate_via_api(subject, brand, out_path, model="gemini-3-pro-image"):
    # Imported here, not at module scope: the offline selftest runs on CI
    # runners with no SDK installed, and a top-level import would fail the
    # entire suite on every one of them.
    try:
        from google import genai
    except ImportError:
        raise GenerateError("google-genai is not installed; use the manual handoff path instead")

    if not has_api_key():
        raise GenerateError("no GEMINI_API_KEY or GOOGLE_API_KEY in the environment")

    client = genai.Client()
    response = client.models.generate_content(
        model=model, contents=build_prompt(subject, brand)
    )

    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline is not None and inline.data:
            out_path.write_bytes(inline.data)
            return out_path

    raise GenerateError("the model returned no image for {}".format(subject["slug"]))
```

- [ ] **Step 4: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_generate.py -v`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add brand-media-kit/bmk/generate.py brand-media-kit/tests/test_generate.py
git commit -m "feat(brand-media-kit): generate - one style paragraph verbatim, one subject clause apart"
```

---

### Task 10: `scripts/install`, SKILL.md, references, examples

The skill is not usable until an operator can read how to run it, and CI does not let reference links land before the files they point at. Everything documentation-shaped goes in one task.

**Files:**
- Modify: `brand-media-kit/scripts/install` (replace the stub)
- Modify: `brand-media-kit/SKILL.md` (full version)
- Create: `brand-media-kit/README.md`
- Create: `brand-media-kit/reference/prompt-recipe.md`
- Create: `brand-media-kit/reference/layout-grid.md`
- Create: `brand-media-kit/reference/manual-handoff.md`
- Create: `brand-media-kit/reference/config-schema.md`
- Create: `brand-media-kit/assets/brand.example.json`
- Create: `brand-media-kit/assets/assets.example.json`
- Test: `brand-media-kit/tests/test_install_script.py`
- Modify: `README.md` (repo root, skills table)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: everything above.
- Produces: `scripts/install [--dry-run] [--force] [target-dir]`, writing `<target>/.brandkit/brand.json` and `<target>/.brandkit/assets.json`.

- [ ] **Step 1: Write the example configs**

`assets/brand.example.json` — the DTS values, since they are the ones the first adopter needs:

```json
{
  "name": "DTS",
  "palette": {
    "primary": "#2271b1",
    "primary_dark": "#135e96",
    "ink": "#0a1e3c",
    "paper": "#ffffff"
  },
  "fonts": {
    "display": "BebasNeue-Regular.ttf",
    "body": "Montserrat-SemiBold.ttf",
    "mono": "JetBrainsMono-Regular.ttf"
  },
  "geometry": {
    "master": [1376, 768],
    "margin": 96,
    "column": 517,
    "subject_band_pct": [28, 72]
  },
  "budget_bytes": 90000
}
```

`assets/assets.example.json` — two entries, enough to show the shape without pretending to be the real roster:

```json
{
  "subjects": [
    {
      "slug": "example-invoicing",
      "title": "INVOICING",
      "tagline": "Compliant invoices for WooCommerce",
      "art": "a stylised invoice document floating in space, edges catching light"
    },
    {
      "slug": "example-shipping",
      "title": "SHIPPING",
      "tagline": "Track every parcel from one screen",
      "art": "a parcel mid-flight along a luminous route line"
    }
  ],
  "targets": [
    "wp-content/plugins/example-invoicing/assets/images/dts-plugins",
    "wp-content/plugins/example-shipping/assets/images/dts-plugins"
  ]
}
```

- [ ] **Step 2: Write the failing install-script test**

```python
# brand-media-kit/tests/test_install_script.py
import json
import pathlib
import shutil
import subprocess

import pytest

SKILL = pathlib.Path(__file__).resolve().parents[1]
INSTALL = SKILL / "scripts" / "install"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not on PATH")


def run(*args):
    return subprocess.run(
        ["bash", str(INSTALL)] + list(args), capture_output=True, text=True
    )


def test_it_scaffolds_both_config_files(tmp_path):
    result = run(str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / ".brandkit" / "brand.json").read_text(encoding="utf-8"))
    assert json.loads((tmp_path / ".brandkit" / "assets.json").read_text(encoding="utf-8"))


def test_dry_run_writes_nothing(tmp_path):
    result = run("--dry-run", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".brandkit").exists()


def test_it_refuses_to_clobber_an_existing_config(tmp_path):
    # An operator re-running install after months of tuning must not lose the
    # roster. Refusing is recoverable; overwriting is not.
    brandkit = tmp_path / ".brandkit"
    brandkit.mkdir()
    (brandkit / "brand.json").write_text('{"mine": true}', encoding="utf-8")

    result = run(str(tmp_path))
    assert result.returncode != 0
    assert "exists" in (result.stderr + result.stdout)
    assert json.loads((brandkit / "brand.json").read_text(encoding="utf-8")) == {"mine": True}


def test_force_overwrites(tmp_path):
    brandkit = tmp_path / ".brandkit"
    brandkit.mkdir()
    (brandkit / "brand.json").write_text('{"mine": true}', encoding="utf-8")

    result = run("--force", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "mine" not in (brandkit / "brand.json").read_text(encoding="utf-8")
```

- [ ] **Step 3: Run and watch it fail**

Run: `cd brand-media-kit && python -m pytest tests/test_install_script.py -v`
Expected: FAIL — the stub exits 78 and writes nothing.

- [ ] **Step 4: Replace `scripts/install`**

```bash
#!/usr/bin/env bash
#
# Scaffold .brandkit/ into an adopting project.
#
# Refuses to overwrite by default. An operator re-running install after months
# of tuning the roster must not silently lose it; refusing is recoverable,
# clobbering is not.
set -uo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"

dry_run=0
force=0
target="."

while [ $# -gt 0 ]; do
	case "$1" in
		--dry-run) dry_run=1 ;;
		--force)   force=1 ;;
		-h|--help)
			echo "usage: install [--dry-run] [--force] [target-dir]"
			exit 0
			;;
		-*)
			echo "unknown option: $1" >&2
			exit 2
			;;
		*) target="$1" ;;
	esac
	shift
done

dest="$target/.brandkit"

for name in brand assets; do
	src="$here/assets/$name.example.json"
	if [ ! -f "$src" ]; then
		echo "missing example config: $src" >&2
		exit 1
	fi
	if [ -e "$dest/$name.json" ] && [ "$force" -eq 0 ]; then
		echo "$dest/$name.json exists; pass --force to overwrite" >&2
		exit 1
	fi
done

if [ "$dry_run" -eq 1 ]; then
	echo "would write $dest/brand.json"
	echo "would write $dest/assets.json"
	exit 0
fi

mkdir -p "$dest" || exit 1
for name in brand assets; do
	cp "$here/assets/$name.example.json" "$dest/$name.json" || exit 1
	echo "wrote $dest/$name.json"
done

echo "Now edit $dest/assets.json: one entry per product, one target per plugin directory."
```

- [ ] **Step 5: Run and watch it pass**

Run: `cd brand-media-kit && python -m pytest tests/test_install_script.py -v && bash -n scripts/install`
Expected: 4 passed, no syntax error.

- [ ] **Step 6: Write the four reference docs**

`reference/config-schema.md` — every key in both files, its type, and what breaks if it is wrong. Table form, one row per key, drawn from Task 2's validation rules.

`reference/layout-grid.md` — the geometry, with the derivation stated explicitly:

> Master 1376x768. Left margin 96px. Text column 517px. Gutter 96px before the art region, which occupies the right 40% of the frame.
>
> 1376 - 96 - 96 = 1184px of usable width. The lockup takes the left 517px of it so that a two-line title at 96px never reaches the art's subject, which the prompt places right of centre.
>
> Title: Bebas Neue, 96px down to 48px, at most 2 lines, 4px tracking, in `palette.paper`.
> Tagline: Montserrat SemiBold, 30px down to 20px, at most 2 lines, 1px tracking, in `palette.primary`.
> Title block top edge: 34% of frame height.
>
> The subject band is 28%-72% of master height. Every format in `derive.FORMATS` keeps at least that band; the tightest, `hero` at 4:1, keeps 27.6%-72.4%.

`reference/prompt-recipe.md` — the locked style paragraph reproduced verbatim, then the rules for extending it: a new product changes only its `art` clause in `assets.json`; changing `STYLE` is a whole-set regeneration and must be treated as one, because a half-regenerated set is worse than the inconsistent set it replaced.

`reference/manual-handoff.md` — the no-key path, and the human check that replaces automated text detection:

> Run `python bmk/generate.py --handoff` to write `PROMPTS.md` into the art directory. Paste each block into the Gemini app. Save each returned image as `<slug>.png` in the same directory.
>
> **Before saving, look at the image and reject it if it contains any lettering.** Image models produce text unbidden and produce it differently every time — a stray word in one banner and not the others is exactly the inconsistency this kit exists to remove. There is no automated check for this: OCR would add a heavyweight dependency and put a network-or-model call inside a suite that must run offline. The check is yours.
>
> Then `python bmk/generate.py --check` lists any slug still missing art.

- [ ] **Step 7: Write the full `SKILL.md`**

Frontmatter must stay under 1024 bytes; the body carries the routing. Keep the `description:` to when-to-use triggers.

```markdown
---
name: brand-media-kit
description: Use when product banners, plugin headers, hero images, or repository listing images look inconsistent across a family of products; when adding a new product that needs artwork matching an existing set; or when asked to regenerate, re-brand, or unify a set of product images.
---

# Brand Media Kit

One 16:9 art master per product becomes every banner the product needs. The art
comes from an image model; all typography is composited in code, because a model
cannot hold a typeface constant across a dozen generations.

## Route on what you were given

| You were given | Go to |
|---|---|
| A project with no `.brandkit/` | `scripts/install`, then edit `.brandkit/assets.json` |
| A roster but no art | Stage 1 - generate |
| Art but no banners | Stages 2-4 - composite, derive, deploy |
| Banners already deployed | Stage 5 - verify |
| One new product to add | Add one entry to `assets.json`, then run all five stages for that slug only |
| "The style should change" | Whole-set regeneration. See `reference/prompt-recipe.md` before touching STYLE |

## Stages

1. `python bmk/generate.py` - with `GEMINI_API_KEY` set, calls the model. Without
   one, writes `PROMPTS.md` for the Gemini app: see `reference/manual-handoff.md`.
2. `python bmk/composite.py` - draws the lockup. Geometry: `reference/layout-grid.md`.
3. `python bmk/derive.py` - centre-band crops the master into every format.
4. `python bmk/deploy.py` - WebP under budget, copied to every target.
5. `python bmk/verify.py` - re-reads the disk. Non-zero exit means do not ship.

Config keys: `reference/config-schema.md`. Prompt rules: `reference/prompt-recipe.md`.

## The one rule

Never let the model render text. Every banner's typography is `bmk/composite.py`
or it is not consistent.
```

- [ ] **Step 8: Write `README.md` and update the repo root**

`brand-media-kit/README.md`: what the skill is, the five stages in a sentence each, how to run the selftest, and a pointer to the spec and plan.

Repo root `README.md`: add a row to the skills table matching the existing format.

`CHANGELOG.md`: add an entry under Unreleased noting the new skill.

- [ ] **Step 9: Full verification**

```bash
bash brand-media-kit/scripts/selftest
bash -n brand-media-kit/scripts/install brand-media-kit/scripts/selftest
shellcheck -S warning -e SC1090,SC1091,SC2317 brand-media-kit/scripts/install brand-media-kit/scripts/selftest

# Reproduce the CI reference-link check locally, since it is the one that
# fails only after the docs land.
for target in $(grep -rhoE '`(reference|assets)/[A-Za-z0-9._/-]+`' brand-media-kit | tr -d '`' | sort -u); do
  [ -e "brand-media-kit/$target" ] || echo "MISSING $target"
done

# And the frontmatter byte count.
awk 'NR==1 && $0=="---"{f=1;next} f && $0=="---"{exit} f' brand-media-kit/SKILL.md | wc -c
```
Expected: selftest OK, no shellcheck output, no `MISSING` lines, frontmatter under 1024.

- [ ] **Step 10: Commit**

```bash
git add brand-media-kit README.md CHANGELOG.md
git commit -m "feat(brand-media-kit): docs and scaffolder - a skill nobody can run is not a skill"
```

---

## Self-Review

**Spec coverage**

| Spec section | Task |
|---|---|
| 3. Decisions: code-composited text | 3, 4, 5 |
| 3. Decisions: left lockup / art right | 5 (column bound), 9 (quiet-left prompt clause) |
| 3. Decisions: typeface system | 5 (`TITLE_*`/`TAGLINE_*`), Task 10 `brand.example.json` |
| 4. Roster | Task 10 example config; the real 13-entry roster is the operator's `.brandkit/assets.json`, written during rollout |
| 5. Architecture: five stages | 2, 5, 6, 7, 8, 9 |
| 6. Pipeline: one master, centre-band crop | 6 |
| 7. Config contract | 2, plus `reference/config-schema.md` in 10 |
| 8. Verification | 8 |
| 9. Testing | every task; harness in 1 |
| 10. Risks: API access not included in Pro | 9 (dual path), `reference/manual-handoff.md` |
| 10. Risks: watermarking unverified | `reference/manual-handoff.md` human check |
| 11. Out of scope: icons, 1:1 renders | not implemented — spec puts them out of scope for this plan |

**Declared gap, needs sign-off before Task 9 is accepted**

The spec's fail-safe "art containing detectable lettering fails verification" has **no task**. Implementing it means OCR — Tesseract or a cloud vision call. Tesseract is a system binary the selftest cannot assume; a cloud call puts the network inside a suite that must run offline and spend no quota. Either breaks a Global Constraint.

It is replaced by a human check documented in `reference/manual-handoff.md`, performed at the moment the operator looks at each returned image. That is weaker than the spec asked for and it should be an explicit decision, not a silent omission.

**Placeholder scan:** clean. Every code step carries real code; the four reference docs in Task 10 Step 6 are specified by content, not by title alone.

**Type consistency:** `ConfigError`, `FontError`, `LayoutError`, `DeriveError`, `BudgetError`, `GenerateError` are each defined once in their own module. `measure(draw, text, font)` has the same signature in `layout.py` and at both call sites in `composite.py`. `FORMATS` keys in `derive.py` match the format names in the SKILL.md routing table and in `reference/layout-grid.md`. `verify(expected, roots, budget_bytes)` takes `expected` as `{filename: (w, h)}` in both the tests and the implementation.
