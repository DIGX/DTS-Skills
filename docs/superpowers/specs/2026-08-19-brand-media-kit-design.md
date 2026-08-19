# brand-media-kit — design

**Date:** 2026-08-19
**Status:** approved for planning
**Repo:** DTS-Skills (new skill), consumed by `d:/Claude Code/plugins`

---

## 1. The problem

Every DTS WordPress plugin renders a "DTS Plugins Home" admin page containing a
card grid of all DTS plugins. Each card carries a banner image. Those banners
were made at different times by different means, and they do not read as one
product family.

Measured against the ten card banners currently shipping in
`assets/images/dts-plugins/`:

| Failure | Observed |
|---|---|
| No type system | five-plus typefaces and weights across ten images — bold condensed, italic display, light grotesque |
| No lockup rule | six centred, three left-aligned, one with half the canvas empty |
| No badge rule | the WooCommerce mark appears as a top-left pill, a bottom-right lockup, an inline glyph, or not at all |
| No margin rule | `dts-bluedart-shipping` bleeds art to all four edges; `dts-zoho-payments` leaves the right half empty |
| Mixed illustration style | neon line-art isometric on most, semi-photoreal 3D on Blue Dart, near-empty on Zoho |
| Literal duplicates | `dts-banner-default.webp` ≡ `dts-shipment-tracking.webp`; `dts-gfe-banner.webp` ≡ `dts-gst-file-exporter.webp` (identical bytes) |
| Missing assets | no `header-banner.*` exists in any plugin — every plugin's page header falls back to a CSS gradient; `dts-ai-commerce`, `dts-online-users`, `dts-woomie` and `zapcart-bom` have no card banner at all |
| Wrong-shape asset | `dts-home-banner.webp` is a 1024×1024 square rendered into a wide hero slot |

The root cause is not taste. It is that **there is no artefact anywhere that
states what a DTS banner is**, so each one was decided again from scratch.

## 2. Goal

One reusable Claude Code skill that turns a brand definition plus a per-item
subject list into a complete, verifiably consistent media set — and a DTS
configuration of that skill that regenerates every DTS plugin's media.

Consistency must be **verified, not assumed**. A pipeline that produces
plausible-looking output while silently substituting a fallback font is the same
class of failure this repository exists to prevent, and it is treated as such
(§8).

## 3. Decisions taken

| Question | Decision |
|---|---|
| Generation route | **Hybrid.** Gemini API (Nano Banana Pro) when `GEMINI_API_KEY` is present; manual Gemini-app handoff otherwise. Manual is the default path and is built first. |
| Asset scope | **Everything** — card banners, page header banners, home hero, and WordPress.org repository assets (banners + icons). |
| Visual direction | **Refine the existing neon dark-tech look.** Deep navy → violet → magenta, neon line-art isometric illustration. Not a rebrand. |
| Title lockup | **Left lockup, art right.** Chosen because the page header banner *requires* a quiet left half — live HTML `h1` and tagline are rendered over it under a left-to-right scrim — so this rule makes card and header the same composition. |
| Text production | **Code-composited over AI art.** Nano Banana renders background art with no lettering; text is drawn by Pillow at fixed coordinates. |
| Typefaces | **Bebas Neue** (display headline), **Montserrat** (subtitle/body), **JetBrains Mono** (accents). All OFL; committed to the consuming repo for reproducible builds. |
| Packaging | Generic, brand-agnostic skill in the **DTS-Skills** repo, installed via `scripts/install-skill`. All DTS specifics live in a `.brandkit/` config in the plugins repo. |

### Why code-composited text

Typography is where the current set fails worst, and it is the one thing image
models cannot hold constant. Nano Banana Pro renders text well, but it will not
reproduce the same typeface at the same optical size on the same baseline across
thirteen independent generations. Drawing text in code makes that property
structural rather than probabilistic, and it makes a tagline change a
two-second recomposite instead of a re-render.

## 4. Roster

Thirteen subjects. All twelve DTS-owned plugins in `d:/Claude Code/plugins`
receive media, **including those not currently registered with DTS Plugins
Home**, plus `dts-pincode-checker`, which ships in every plugin's cross-promo
grid but whose source lives outside this workspace.

| # | Directory | Plugin Name | Registered in Home | Card banner today |
|---|---|---|---|---|
| 1 | `dts-abandoned-recovery` | Abandoned Cart Recovery for WooCommerce | no | yes |
| 2 | `dts-ai-commerce` | DTS AI Commerce Suite | yes | **missing** |
| 3 | `dts-bluedart-shipping` | Blue Dart WooCommerce Integration | yes | yes |
| 4 | `dts-gmc-autopricing` | DTS GMC Auto Pricing | no | yes |
| 5 | `dts-gst-file-exporter` | DTS GST File Exporter | yes | yes (duplicated) |
| 6 | `dts-gst-invoice` | DTS GST Invoice | yes | yes |
| 7 | `dts-online-users` | DTS Online Users | no | **missing** |
| 8 | `dts-order-exporter` | DTS Order Exporter | yes | yes |
| 9 | `dts-shipment-tracking` | DTS Shipment Tracking | yes | yes (duplicated) |
| 10 | `dts-zoho-payments` | Payments Gateway for Zoho | yes | yes |
| 11 | `Woomie` (`dts-woomie.php`) | Woomie: AI Chat Bot for WooCommerce | no | **missing** |
| 12 | `zapcart-bom` | ZapCart BOM | no | **missing** |
| 13 | *(no local directory)* | Pincode Checker | n/a | yes |

**Excluded:** `wp-useronline` — third-party (lesterchan.net), not DTS property.

`dts-online-users` already carries WordPress.org assets under the older
`assets/banner-1544x500.png` convention; those are replaced in place. It is also
the only plugin with a `wordpress.org/plugins/` Plugin URI, so it is the one
whose repository assets are live today.

## 5. Architecture

A generic skill that knows nothing about DTS, and a per-project configuration
directory that holds everything that does.

```
DTS-Skills/brand-media-kit/
  SKILL.md                       routing + workflow
  README.md
  reference/
    prompt-recipe.md             the locked art prompt formula
    layout-grid.md               safe zones, crop maths, coordinate grid
    manual-handoff.md            the Gemini-app path, step by step
    config-schema.md             brand.json / assets.json reference
  assets/
    brand.example.json
    assets.example.json
  scripts/
    generate                     art  — API path
    composite                    art + text → master PNG
    derive                       master → every output format
    install                      convert, budget, fan out to target dirs
    verify                       the consistency fence
    selftest                     TDD suite (repo's firm rule)
```

```
d:/Claude Code/plugins/.brandkit/      DTS configuration, committed
  brand.json      palette · fonts · grid · locked style paragraph
  assets.json     roster · formats · per-plugin subject clause
  fonts/          BebasNeue-Regular.ttf, Montserrat-{Medium,SemiBold}.ttf,
                  JetBrainsMono-Bold.ttf          (OFL, committed)
  art/            raw AI backgrounds — committed, so re-texting is free
  out/            build output
```

Committing `art/` is deliberate. Art generation is the only step that costs
money or human time; every downstream change — a reworded tagline, a nudged
coordinate, a new output size — must be reproducible without touching Gemini
again.

## 6. Pipeline

Four stages, each runnable independently, each with a file-on-disk boundary so a
failure never forces a re-run of the stage before it.

### Stage 1 — art

Nano Banana Pro renders **background art only**. Every prompt is the same locked
style paragraph plus one per-plugin subject clause, and carries two hard
constraints:

- no text, lettering, words, numerals, logos or watermarks anywhere in frame
- the left 44% of the frame is quiet dark gradient with no subject matter

Output: `.brandkit/art/{slug}.png`, 16:9, 2K.

- **API path** (`GEMINI_API_KEY` set): `scripts/generate` calls the model
  directly, one file per subject, retrying on a failed no-text constraint.
- **Manual path** (default): the skill prints numbered, copy-paste-ready prompts
  and the exact filename each result must be saved as. No API key, no per-image
  cost, uses the existing Gemini Pro subscription.

Both paths converge on the same directory, so stages 2–4 cannot tell which was
used.

### Stage 2 — composite

`scripts/composite` draws the lockup onto the art with Pillow, at coordinates
read from `brand.json`. Starting grid for the 1376×768 card:

| Element | Face | Spec |
|---|---|---|
| Eyebrow `DTS PLUGINS` | JetBrains Mono Bold 20 | tracking +0.18em, cyan accent, y=96 |
| Title | Bebas Neue, auto-fit 96→64 | caps, ≤3 lines, leading 0.92, white, y=140 |
| Accent rule | — | 4×64 magenta bar, 24 below title |
| Tagline | Montserrat Medium 22 | wrap to column, ≤3 lines, 82% white |
| Woo badge + version | vector + JetBrains Mono 16 | footer row, baseline y=690 |

Text column: left margin 88, width 517 — the 44% quiet column (605 px) less the
left margin, leaving no right gutter, so text may reach the quiet/art boundary
but never cross it. Auto-fit shrinks the title until it fits the column; it
never widens the column.

### Stage 3 — derive

One master → every format. The card, header, hero and WordPress.org banners are
all crops of the same 16:9 art, which is why the art must keep its subject
inside a **vertical band from 28% to 72%** — the band that survives the tightest
crop (4:1 hero, which retains 44.4% of frame height).

| Format | Size | Text | Crop of master |
|---|---|---|---|
| card | 1376×768 | full lockup | full frame |
| header | 1376×400 | **none** — live HTML sits there | centre band |
| hero | 1920×480 | `DTS PLUGINS` + suite tagline | centre band |
| wporg-banner | 1544×500 | title + tagline | centre band |
| wporg-banner-sm | 772×250 | title only | centre band |
| wporg-icon | 256×256, 128×128 | mark only | **separate 1:1 generation** |

Icons are not a crop. A 1:1 icon is a mark, not a scene, and cropping a wide
illustration produces a fragment. They get their own prompt recipe and their own
art file.

### Stage 4 — install

`scripts/install` converts to WebP under a size budget (~80 KB, matching the
current set), then writes to targets declared in `assets.json`:

- `assets/images/dts-plugins/{slug}.webp` → **every** plugin directory,
  preserving the existing convention where each plugin ships the whole
  cross-promo set
- `assets/images/header-banner.webp` → the owning plugin only
- `assets/images/dts-home-banner.webp` → every plugin directory
- WordPress.org assets → `.brandkit/out/wporg/{slug}/`, **not** into the plugin
  directory, because those live in the SVN `/assets/` tree and must not ship
  inside the plugin zip. `dts-online-users` is the documented exception and is
  updated in place.

Install prints a diff of what changed and is idempotent.

## 7. Configuration contract

`brand.json` — everything visual, nothing project-specific:

```jsonc
{
  "palette":   { "bg_deep": "#0B1437", "mid": "#4C1D95", "hot": "#C026A3",
                 "accent_cyan": "#22D3EE", "accent_magenta": "#E945C6" },
  "fonts":     { "display": "fonts/BebasNeue-Regular.ttf", ... },
  "grid":      { "quiet_column_pct": 44, "subject_band_pct": [28, 72],
                 "margin": 88, ... },
  "style_paragraph": "…the locked art prompt, byte-identical for every subject…"
}
```

Palette values are placeholders to be **sampled from the approved reference
banners** during implementation, not eyeballed.

`assets.json` — the roster, the formats, and one subject clause per subject.

Another project adopts the pipeline by writing its own `.brandkit/`. Nothing in
`brand-media-kit/` mentions DTS.

## 8. Verification

`scripts/verify` is a fence, not a report. It asserts:

1. every declared asset exists in every declared target directory
2. copies of the same asset are **byte-identical** across plugin directories
3. dimensions match the declared format exactly
4. **no two different slugs share a file hash** — the check that would have
   caught both existing duplicates
5. every file is within the size budget
6. it rebuilds the contact sheet for human review

Run before and after. Its output is what substantiates the claim of consistency.

### The fail-safes that matter

Drawn directly from this repository's history of fences that reported clean
while guarding nothing:

- **A missing or unreadable font file is a hard error.** Pillow's natural
  behaviour is to fall back to a default bitmap font, which would produce output
  that is internally consistent, superficially plausible, and wrong. The
  compositor must refuse to run.
- **A verify run that finds zero assets to check fails.** An empty fence
  reporting clean is worse than no fence.
- **An art file containing detectable lettering fails the no-text constraint**
  rather than being composited over.

## 9. Testing

The repository's one firm rule applies: **no change to a skill without a failing
test first.** `brand-media-kit/scripts/selftest` builds a throwaway tree, stubs
the art stage with synthetic PNGs, and spends no API quota. Required assertions:

| Assertion | Guards against |
|---|---|
| same input → byte-identical output | non-determinism in the compositor |
| two subjects → *different* hashes | a bug that renders everything identically |
| rendered ink stays inside the text column | silent overflow into the art |
| each format has exactly its declared dimensions | crop maths errors |
| install fans out and copies are byte-identical | partial fan-out |
| verify **fails** on a seeded duplicate | fence that cannot detect the known bug |
| verify **fails** when a target is missing an asset | incomplete install passing |
| verify **fails** on an empty asset set | empty fence reporting clean |
| compositor **fails** on a missing font | silent fallback-font substitution |

The last four are RED-first tests: each must be watched failing before the
guard is written.

## 10. Risks and open items

1. **A Gemini Pro subscription does not grant API access.** Nano Banana Pro via
   API requires a separately billed AI Studio key. This is why manual is the
   default path and the API path is an optional accelerator — the work is never
   blocked on a key.
2. **Watermarking is unverified.** Nano Banana Pro embeds SynthID, and some
   tiers add a *visible* watermark. This must be checked on the first real
   render, before the pipeline is committed to. If a visible mark lands in the
   subject band, the crop maths in §6 changes.
3. **Palette values in §7 are provisional** until sampled from the approved
   reference banners.
4. **The locked style paragraph is not yet written.** It is the single artefact
   that most determines whether the set reads as one family, and it is written
   and test-rendered as the first implementation task — not carried forward as
   prose in this spec.
5. **`dts-pincode-checker` has no local source.** Its media is generated and
   placed in the shared grid, but the plugin's own repository is not updated by
   this work.
6. **Python + Pillow is a new dependency** for this repository, which is
   otherwise bash and Node. Image compositing in bash is not sensible; the
   dependency is accepted, and `selftest` gates on its presence.

## 11. Out of scope

- Screenshots for WordPress.org listings (`screenshot-1.png` …) — these are
  captures of real UI, not generated art.
- Any change to `class-dts-plugins-home.php` rendering logic. This work replaces
  image files and adds the `header-banner.webp` the existing auto-discovery
  already looks for.
- Rebranding the admin UI chrome. The `#2271b1` WP-admin blue of the UI and the
  neon dark banners remain two different palettes by decision, not oversight.
