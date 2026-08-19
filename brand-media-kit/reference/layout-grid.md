# Layout grid

Where the type goes, why it goes there, and how one master becomes five
formats without the type moving between them.

## Reference units

Every geometry number except `master` is in units of a **1376px-wide frame** —
the size the WordPress card CSS has always been fed, and the reason the grid
looks the way it does.

The master is bigger than that (1920 x 1080; see `reference/config-schema.md`),
so `bmk/composite.py` scales the whole lockup by `master_width / 1376` before
drawing. A 1920 master gets 39.5% larger type at 39.5% greater inset, and once
`derive` brings the card back down to 1376 the lockup lands where it would have
landed had it been drawn at 1376 directly — within a few pixels either way.

This is why type is identical across products: nothing about the lockup depends
on the product, only on the frame it is drawn in.

## The lockup

| Number | Reference units | As a fraction of the frame |
| --- | --- | --- |
| `margin` (left inset) | 96 | 7.0% |
| `column` (usable width) | 517 | 37.6% |
| Right edge of the column | 613 | 44.6% |
| Title top | — | 34% of frame height |
| Title size | 96 down to 48 | fitted, never grown |
| Title tracking | 4 | between glyphs |
| Gap under the title block | 22 | |
| Tagline size | 30 down to 20 | fitted |
| Tagline tracking | 1 | |
| Line spacing | 1.06 x size | |

The title is set in `fonts.display` in `palette.paper`; the tagline in
`fonts.body` in `palette.primary`.

**Fitting shrinks and never grows.** A two-word product name is set at the same
96 units as a five-word one until the five-word one has to come down. Growing
short titles to fill the column is precisely the per-product drift this kit
exists to remove.

Tracking is counted during fitting, not deducted as a guess afterwards. Pillow
has no letterspacing, so `draw_tracked` paints glyph by glyph and an n-glyph run
is n-1 gaps wider than Pillow reports; `layout.measure` adds those gaps so a
line that measures as fitting also draws as fitting.

Measured worst case on a 1920 master, title "WOOCOMMERCE SHIPMENT TRACKING PRO"
over a 72-character tagline: the drawn lockup occupies x 7.0%–44.1%, y
35.4%–60.0%. It stays inside the 44.6% column edge and inside every crop band
below.

## Why the left 45% must be quiet

The lockup's right edge is at 44.6% of the frame. The prompt in
`reference/prompt-recipe.md` reserves the left **45 percent** as background
gradient only — the smallest number that covers the column with the rounding
in the right direction. Change `margin` or `column` and that sentence in
`bmk/generate.py` has to change with them, or type starts landing on detail.

## The centre band

`bmk/derive.py` cuts every format out of one master by taking a full-width,
centred horizontal slice and resizing it. Nothing is ever letterboxed, stretched,
or upscaled.

From a 1920 x 1080 master:

| Format | Size | Aspect | Band of the master it keeps |
| --- | --- | --- | --- |
| `card` | 1376 x 768 | 1.79 | 0.4% – 99.6% |
| `header` | 1376 x 400 | 3.44 | 24.2% – 75.8% |
| `hero` | 1920 x 480 | 4.00 | 27.8% – 72.2% |
| `wporg-banner` | 1544 x 500 | 3.09 | 21.2% – 78.8% |
| `wporg-banner-sm` | 772 x 250 | 3.09 | 21.2% – 78.8% |

The widest format keeps the least. `hero` at 4:1 keeps 27.8%–72.2%, and that is
the whole derivation of `subject_band_pct = [28, 72]`: it is the tightest band
in the table, rounded inward, and therefore the slice every crop is guaranteed
to keep.

Two consequences worth holding on to:

- **Art outside 28–72% is expendable.** It shows on the card and nowhere else.
  The model is told this, which is why the prompt asks for the subject inside
  the band rather than merely "centred".
- **Add a wider format and the band shrinks.** A 5:1 format from a 16:9 master
  keeps 32.2%–67.8%. Recompute with `bmk.derive.band_bounds_pct` before adding one,
  and update `subject_band_pct` — otherwise the first product generated after
  the change is the one that gets cropped.

The lockup sits higher in the frame the wider the crop, because a fixed 34% of
the master's height is a larger fraction of a narrower band. At y 35.4%–60.0%
it is inside every band in the table, with the tightest margin against `hero`.
