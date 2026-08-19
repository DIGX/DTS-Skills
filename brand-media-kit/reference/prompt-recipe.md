# Prompt recipe

One prompt shape, thirteen products, one clause different between them.

## The shape

`bmk/generate.py` assembles three parts, in this order, separated by blank
lines:

1. The locked style paragraph below, byte for byte.
2. `SUBJECT: <the subject's "art" string from assets.json>` — the only part
   that varies between products.
3. The constraints clause: size, aspect, and the subject band, filled in from
   `brand.json` geometry.

Run `python bmk/generate.py --handoff` to see the exact text for your own
config; what follows is the constant part.

## The locked style paragraph

Reproduced verbatim from `STYLE` in `bmk/generate.py`:

> Dark technical illustration, deep navy-to-black gradient background, thin
> luminous cyan and azure line-work, subtle circuit-like geometry, soft
> volumetric glow, shallow depth of field, high contrast, no grain, flat
> vector-adjacent rendering with a faint glass reflection. Composition: the
> left 45 percent of the frame is quiet - background gradient only, no detail,
> nothing that competes with overlaid type. The subject sits right of centre.
> Absolutely no text, no letters, no lettering, no numerals, no logos, no
> watermarks, no UI chrome anywhere in the image.

**It is a constant, not a template.** Every product embeds these exact bytes.
The moment the style text is assembled per product — a synonym here, an extra
adjective there — the products drift apart, and drift is the failure this kit
was built to prevent. If the style must change, change it once, and regenerate
every product from the new text.

## The constraints clause

`CONSTRAINTS` is the only part with substitutions:

> Output a single image, {w} x {h} pixels, 16:9. Keep the subject entirely
> between {low} percent and {high} percent of the frame height, because every
> derived crop keeps only that vertical band.

`{w}`/`{h}` come from `geometry.master`, `{low}`/`{high}` from
`geometry.subject_band_pct`. The band is explained — models comply better with
a reason than with a bare number — and the reason is true: see
`reference/layout-grid.md`.

## What the three parts are each doing

- **The quiet left 45%** is the negative space the lockup is drawn into. The
  model is not asked to leave room for text; it is asked for a region with
  nothing in it, and `bmk/composite.py` puts the text there afterwards.
- **The subject band** is what survives cropping to 4:1. Anything the model
  puts above 28% or below 72% of the height exists only on the card.
- **The no-text clause** is repeated in six ways on purpose. Image models
  produce lettering unprompted, and one refusal is weaker than six.

## Text in the art

No prompt reliably stops a model rendering letterforms. The kit therefore does
not rely on the prompt alone: art is checked by a person before it is saved, and
the check is a rejection, not a repair. See `reference/manual-handoff.md`.

## Changing the recipe

Anything here can change. What cannot change is one product's prompt differing
from another's in more than the SUBJECT clause. If you edit `STYLE`:

1. Edit it once, in `bmk/generate.py`.
2. Delete every master in `.brandkit/art/`.
3. Regenerate all of them.
4. Recomposite, rederive, redeploy, verify.

A half-regenerated set is worse than the old one — it looks like a mistake
rather than a style.
