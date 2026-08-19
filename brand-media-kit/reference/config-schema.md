# Config schema

Two files, both under `.brandkit/` in the adopting project. `scripts/install`
copies `assets/brand.example.json` and `assets/assets.example.json` into place;
these are the same keys, described.

Every key listed is required. `bmk/config.py` refuses the file rather than
filling a default in, because a silent default here does not fail — it ships.

## brand.json

The identity. One per project, and it should change about as often as the logo.

| Key | Type | Meaning | If it is wrong |
| --- | --- | --- | --- |
| `name` | string | Brand name, for prompts and headings | Cosmetic |
| `palette.primary` | `#rrggbb` | Tagline colour | Tagline is the wrong colour in every asset |
| `palette.primary_dark` | `#rrggbb` | Reserved for rules and fills | Unused today; kept so the palette is complete |
| `palette.ink` | `#rrggbb` | Dark ground reference | Unused today; see above |
| `palette.paper` | `#rrggbb` | Title colour | Titles vanish against dark art if set dark |
| `fonts.display` | filename | Face for titles, resolved in `.brandkit/fonts/` | `FontError` — the stage stops rather than falling back to Pillow's bitmap default |
| `fonts.body` | filename | Face for taglines | Same |
| `fonts.mono` | filename | Reserved | Must exist even though nothing draws with it yet |
| `geometry.master` | `[w, h]` | Size to ask the model for | See **Master size** below |
| `geometry.margin` | int | Left inset of the lockup, in reference units | Type moves off the quiet zone |
| `geometry.column` | int | Width the lockup may occupy, in reference units | Type wraps wrongly or overruns into the art |
| `geometry.subject_band_pct` | `[low, high]` | Vertical band the art must keep its subject inside | The subject gets cropped out of the wide formats |
| `budget_bytes` | int | Ceiling for any one deployed WebP | Too low: `BudgetError`. Too high: slow admin screens |

Colour syntax is not checked when the config loads: `bmk/composite.py` reads six
hex digits with an optional leading `#`, so three-digit shorthand raises later,
when the first master is drawn.

### Master size

`geometry.master` is checked for shape when the config loads — two positive
ints — and for fitness when `bmk/derive.py` opens the composited master. It must
be 16:9 and at least as large as the biggest delivery format in every dimension — today that means at least 1920 x 1080, because
`hero` is 1920 wide and `wporg-banner` is 500 tall relative to a 1544 width.

`bmk/derive.py` refuses to upscale. Art enlarged past its native size looks
acceptable at review size and soft in the listing, which is exactly the failure
nobody catches before publishing. A 1376 x 768 master — the card size, and an
easy mistake — is rejected with the format that could not be cut from it.

Geometry other than `master` is in **reference units**, not master pixels. See
`reference/layout-grid.md`.

### subject_band_pct

`[low, high]`, both 0–100, `low < high`. It goes into the prompt, and it is a
promise to the model rather than something the code can enforce: every wide
crop keeps only that band of the master's height, so a subject drawn outside it
is cut in half by `derive`.

28–72 is the right pair for the current format table. The derivation is in
`reference/layout-grid.md`; if you add a wider format, recompute it.

## assets.json

The catalogue. This changes whenever the product line does.

| Key | Type | Meaning | If it is wrong |
| --- | --- | --- | --- |
| `subjects` | non-empty list | One entry per product | An empty list is refused: a run that produces nothing must not report success |
| `subjects[].slug` | string | Filename stem for art, build dir, and deployed files | Duplicates are refused — the second product would overwrite the first |
| `subjects[].title` | string | Drawn large, in the display face | Long titles shrink to fit; they never grow to fill |
| `subjects[].tagline` | string | Drawn small, in the body face, in `palette.primary` | Same |
| `subjects[].art` | string | The one clause that differs between prompts | Weak clause, weak art; it is the only per-product input the model gets |
| `targets` | non-empty list | Directories, relative to the project root, that receive the media | A missing directory is created; a wrong one silently populates the wrong plugin |

Every target receives **every** product's media, not just its own — the card
grid on any one plugin's screen shows the whole range. That is why deployed
files carry the slug: `<slug>-<format>.webp`.

`bmk/verify.py` reads `targets` the same way and checks that every expected file
is present, in size, under budget, and byte-identical across all of them.
