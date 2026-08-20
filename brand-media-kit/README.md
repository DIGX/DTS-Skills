# `brand-media-kit`

**One art master per product. All type drawn in code. Every size cut from that
one file. A checker that re-reads the disk.**

A Claude Code skill that turns a product list into a consistent set of banners —
product cards, page headers, hero strips, WordPress.org listing images — for a
family of products that should look like they came from the same place.

```
/brand-media-kit          # in Claude Code, from the project you want set up
```

---

## Table of contents

- [Why this exists](#why-this-exists)
- [How consistency is enforced](#how-consistency-is-enforced)
- [Installing](#installing)
- [Configuration](#configuration)
- [The five stages](#the-five-stages)
- [Adopting a set that already has images](#adopting-a-set-that-already-has-images)
- [The one human step](#the-one-human-step)
- [Verifying](#verifying)
- [Layout of this skill](#layout-of-this-skill)
- [Caveats](#caveats)

---

## Why this exists

Thirteen plugins, each with a banner made when that plugin shipped. Every one
was reasonable on its own. Together they read as thirteen unrelated products,
because the type was set by eye, the art was prompted afresh each time, and each
size was made separately from the last.

Consistency by discipline does not survive the fourteenth product, or the second
person, or the six-month gap. So none of the consistency here depends on
discipline.

## How consistency is enforced

| Failure | What stops it |
|---|---|
| Art drifts between products | One constant style string. Every prompt is those exact bytes plus one subject clause |
| Type drifts between products | Type is never in the art. It is drawn by one function at fixed sizes, tracking, and position |
| Sizes drift from each other | Every format is a centred crop of the same master. Nothing is drawn twice |
| Art gets soft in the listing | Upscaling is a hard error, not a warning |
| Images bloat the admin screens | Every deployed file is encoded down to a byte budget |
| A stage lies about what it did | `verify` imports nothing from the kit and re-reads the files |

## Installing

Requires Python 3.9+ and Pillow.

```
pip install -r requirements.txt
bash scripts/install [project-dir]        # --dry-run first if you like
```

(To install the *skill* itself into Claude Code, that is `bash
scripts/install-skill brand-media-kit` from the repo root. On Windows, `--link`
needs Developer Mode or an elevated shell; without either the installer says so
and copies instead, so edits here will not reach the installed copy until you
reinstall.)

That scaffolds `.brandkit/` in the target project:

```
.brandkit/
  brand.json      palette, fonts, geometry, byte budget
  assets.json     one entry per product, plus the target directories
  fonts/          the font files brand.json names
  art/            <slug>.png, one 16:9 master per product
  build/<slug>/   master.png plus one PNG per derived format
```

Only `art/` is precious. Everything under `build/` regenerates from it, and
everything in the targets regenerates from `build/`.

## Configuration

Two files, both created by `scripts/install` from the examples in `assets/`.
Every key, and what breaks when it is wrong, is in
[`reference/config-schema.md`](reference/config-schema.md).

The two that catch people out:

- **`geometry.master`** must be 16:9 and at least 1920 x 1080. The card size
  (1376 x 768) is the natural guess and is rejected — `hero` is 1920 wide, and
  nothing is ever upscaled.
- **`geometry.subject_band_pct`** is `[28, 72]` for the current format table.
  It is the vertical slice of the master that every crop keeps, derived from
  the widest format in the set. Add a wider one and it has to be recomputed —
  see [`reference/layout-grid.md`](reference/layout-grid.md).

Everything else in `geometry` is in **1376-unit reference space**, not master
pixels, and is scaled to whatever master it is handed.

## The five stages

```
python bmk/generate.py     # one 16:9 art master per product
python bmk/composite.py    # draw the title and tagline onto it
python bmk/derive.py       # crop every delivery size out of that one master
python bmk/deploy.py       # encode to WebP under budget, copy into each target
python bmk/verify.py       # re-read the disk and report anything wrong
```

Each takes optional slugs to run over a subset, and `--project DIR` to work on a
project other than the one above the current directory.

`generate` has two routes to the same prompt: the API, if `GEMINI_API_KEY` or
`GOOGLE_API_KEY` is set, or `--handoff`, which writes a `PROMPTS.md` to paste
into the Gemini app. Both call the same builder, so the manual route cannot
drift from the automated one — a consumer Gemini subscription does not include
API access, and that should not mean a different prompt.

Formats produced by `derive`:

| Format | Size |
|---|---|
| `card` | 1376 x 768 |
| `header` | 1376 x 400 |
| `hero` | 1920 x 480 |
| `wporg-banner` | 1544 x 500 |
| `wporg-banner-sm` | 772 x 250 |

## Adopting a set that already has images

Most projects that need this skill already have banners — that is usually why
they need it. Two things are worth settling before the first `generate`, because
both are cheap now and expensive after thirteen products exist.

**Filenames.** `deploy` writes `<slug>-<format>.webp` into every target
directory. The slug is in the filename because every target holds the media for
every product, not just its own, so directory alone cannot disambiguate them.

If the project already loads a different name — a bare `<slug>.webp`, say — you
have two honest choices:

- Update the references in the project, which is a mechanical find-and-replace
  and leaves you with names that say which format they are.
- Narrow `FORMATS` in `bmk/derive.py` to the formats that project actually uses
  and adjust `deploy.output_name`, which keeps the existing references working
  but gives up the multi-format fan-out.

Do not solve it by hand-renaming after each deploy. The next run overwrites.

**Target directories.** `targets` in `assets.json` is a list of directories
relative to the project root, and each one receives the whole set. Point them at
the directories the project already serves images from; `deploy` creates what is
missing and `verify` will tell you if a copy has drifted.

**Formats are all wide crops.** Every format is a centred horizontal slice of
one 16:9 master, so a square or portrait asset cannot come from this pipeline —
cropping 1:1 out of 16:9 keeps only the middle 56% of the width, and the lockup
lives in the left 45%, so the type would be cut in half. A square asset needs
its own layout. Adding it to the format table produces a clipped one.

## The one human step

**Before saving a generated master, look at it and reject it if it contains any
lettering.**

Image models produce letterforms unprompted. The prompt refuses text in six
different ways and they still appear — usually as near-words that read as text
until someone looks closely, at which point they read as a mistake nobody
proofread.

This is a human gate on purpose. OCR was the obvious automation and was
rejected: a cloud vision call breaks the rule that the selftest runs offline and
spends no quota, and a local Tesseract would silently stop enforcing on every
machine that lacks the binary. A check that disables itself quietly is worse
than a documented one that does not. The reasoning, and the full reject list, is
in [`reference/manual-handoff.md`](reference/manual-handoff.md).

Nothing downstream compensates: `verify` checks bytes, sizes and budgets, and
cannot read.

## Verifying

```
python bmk/verify.py
```

Reports missing files, missing target directories, wrong dimensions, files over
budget, unreadable files, copies that differ between targets, and two different
assets that are byte-identical — which means one was copied over the other.

It imports no other module in the kit, on purpose. A checker that shares code
with the thing it checks inherits its bugs. It also refuses to pass when handed
an empty expected set or no target directories: a fence that reports clean
because it was given nothing is worse than no fence, because it is trusted.

The skill's own suite:

```
bash scripts/selftest
```

Offline, against a vendored test font. It never calls a model.

## Layout of this skill

```
SKILL.md                     routing table and the five stages
bmk/                         the pipeline
  config.py                  load and refuse bad configs
  project.py                 find .brandkit and the paths under it
  fonts.py                   load a face, or fail - never a bitmap fallback
  layout.py                  wrap, measure, and shrink-to-fit
  generate.py                build the prompt; API or handoff
  composite.py               draw the lockup
  derive.py                  crop every format from one master
  deploy.py                  WebP under budget, then fan out
  verify.py                  the fence
assets/                      the two example configs
reference/
  config-schema.md           every key, and what breaks if it is wrong
  layout-grid.md             the geometry, with the derivations
  prompt-recipe.md           the locked style paragraph
  manual-handoff.md          the no-key path and the human check
scripts/install              scaffold .brandkit into a project
scripts/selftest             run the suite offline
tests/                       the suite
```

## Caveats

- **The art is only as good as the model.** This kit makes a set consistent; it
  does not make it beautiful. A weak `art` clause produces weak art in a
  perfectly consistent style.
- **The no-lettering check is manual.** See above. It is the one place the kit
  depends on a person.
- **Fonts are not shipped.** `brand.json` names files that must exist in
  `.brandkit/fonts/`; licensing them is yours. The suite vendors Bebas Neue
  (SIL OFL) for tests only.
- **Every target receives every product's media.** That is deliberate — the
  card grid on one product's screen shows the whole range — but it means a
  large product set multiplies across a large number of targets.
- **No square or portrait formats.** Everything is a wide crop of one 16:9
  master. See [Adopting a set](#adopting-a-set-that-already-has-images).
- **The API path needs `google-genai`**, which is deliberately not in
  `requirements.txt`: the selftest must install nothing that could reach the
  network.

---

Part of [DTS-Skills](../README.md). MIT licensed.
