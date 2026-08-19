---
name: brand-media-kit
description: Use when product banners, plugin headers, hero images, or repository listing images look inconsistent across a family of products; when adding a new product that needs artwork matching an existing set; when generated art keeps coming back with lettering in it; or when the same image has to ship at card, header, hero, and WordPress.org banner sizes without being redrawn each time.
version: 1.0.0
user-invocable: true
argument-hint: "[install|generate|composite|derive|deploy|verify] — omit to route on the state of .brandkit/"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TodoWrite
---

# Brand Media Kit

Turns a product list into a consistent set of banners: one AI-generated art
master per product, all typography drawn in code, every delivery size cut from
that one master, and a checker that re-reads what actually landed on disk.

The consistency is not a matter of care. It is structural: the style prompt is
one constant string, the type is drawn by one function with fixed sizes, and
every format is a crop of the same file. There is nothing per-product to keep
in sync, so nothing per-product drifts.

## Route on what you were given

| Situation | Do this |
|---|---|
| No `.brandkit/` in the project | `bash scripts/install <project>`, then edit the two configs |
| `install` | Same, then read `reference/config-schema.md` |
| Configs exist, no art yet | `python bmk/generate.py` — read `reference/manual-handoff.md` first |
| `generate`, and no API key is set | `python bmk/generate.py --handoff`, then follow `reference/manual-handoff.md` |
| Art is in place | `python bmk/composite.py`, then `derive`, `deploy`, `verify` |
| Adding one product to an existing set | Add the subject to `assets.json`, then run all five stages with that slug |
| Type is the wrong size, or lands on the art | `reference/layout-grid.md` |
| Art keeps coming back with lettering in it | `reference/prompt-recipe.md`, then reject and regenerate |
| A deployed image is missing, oversized, or stale | `python bmk/verify.py` and act on what it names |
| Changing the look of the whole set | `reference/prompt-recipe.md`, "Changing the recipe" |

## Install

```
bash scripts/install [project-dir]     # --dry-run to see what it would write
```

Scaffolds `.brandkit/` with `brand.json` and `assets.json` copied from
`assets/brand.example.json` and `assets/assets.example.json`. It refuses to
overwrite an existing config without `--force`.

Then, before anything else:

1. Edit `.brandkit/brand.json` — palette, font filenames, geometry, byte budget.
2. Put the font files themselves in `.brandkit/fonts/`.
3. Edit `.brandkit/assets.json` — one entry per product, and the target
   directories the media is copied into.

Every key is described in `reference/config-schema.md`, including what breaks
when it is wrong. `geometry.master` must be 16:9 and at least 1920 x 1080.

Dependencies: Python 3.9+ and Pillow (`pip install -r requirements.txt`).

## The five stages

Each runs over every product by default, or over the slugs you name. All of
them take `--project DIR`; without it they find the nearest `.brandkit/` above
the working directory.

### 1. `python bmk/generate.py`

One 16:9 art master per product, into `.brandkit/art/<slug>.png`.

With `GEMINI_API_KEY` or `GOOGLE_API_KEY` set it calls the model directly.
Without one it writes `.brandkit/art/PROMPTS.md` to paste into the Gemini app —
same prompt, same bytes. `--handoff` forces that path; `--check` reports what is
still missing and exits non-zero.

**Every master is checked by a person before it is saved**: reject anything
containing lettering, logos, or UI chrome. Nothing downstream can catch this —
`verify` checks bytes and sizes and cannot read. See
`reference/manual-handoff.md`.

### 2. `python bmk/composite.py`

Draws the title and tagline onto the art, writing
`.brandkit/build/<slug>/master.png`.

All typography happens here, in code, at fixed sizes with fixed tracking, so it
is identical across products. Long titles shrink to fit; short ones never grow
to fill. Geometry is in 1376-unit reference space and scaled to whatever master
it is handed — `reference/layout-grid.md`.

### 3. `python bmk/derive.py`

Cuts every delivery format out of that one master, into
`.brandkit/build/<slug>/<format>.png`:

| Format | Size | Where it goes |
|---|---|---|
| `card` | 1376 x 768 | Product cards |
| `header` | 1376 x 400 | Page headers |
| `hero` | 1920 x 480 | Hero strips |
| `wporg-banner` | 1544 x 500 | WordPress.org listing |
| `wporg-banner-sm` | 772 x 250 | WordPress.org listing, small |

Each is a full-width centred slice, resized down. Nothing is ever upscaled — a
master too small for a format is a hard error, because upscaled art looks fine
at review size and soft in the listing.

### 4. `python bmk/deploy.py`

Encodes each format to WebP under `budget_bytes`, dropping quality until it
fits, and copies it into every target directory as `<slug>-<format>.webp`.

Every target gets every product's media: the card grid on any one product's
screen shows the whole range.

### 5. `python bmk/verify.py`

Re-reads what is actually on disk and reports anything wrong: missing files,
missing target directories, wrong dimensions, over budget, unreadable, copies
that differ between targets, or two different assets that are byte-identical.

It imports no other module in the kit. Every other stage reports what it
believes it did; this one looks. It also refuses to pass when handed an empty
expected set — a fence that reports clean because it was given nothing is worse
than no fence, because it is trusted.

## Rules that are not negotiable

- **One master per product.** Every format is a crop of it. Generating a
  separate image per size is how a set drifts.
- **No text in the art.** Type is composited in code, always.
- **The style prompt is a constant, not a template.** If it changes, every
  product is regenerated from the new text — a half-regenerated set looks like
  a mistake rather than a style.
- **Never upscale.** Fix the master size instead.
- **`verify` is the last word.** A stage reporting success is a claim; verify
  is the evidence.

## Selftest

```
bash scripts/selftest
```

Runs the whole suite offline against a vendored test font. It never calls a
model and never spends quota.
