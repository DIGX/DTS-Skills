# brand-media-kit: field report from the first real adoption

**Reporter:** the session that rolled the kit out across `D:\Claude Code\plugins`
**Date:** 2026-08-20
**Outcome:** 180 assets shipped to 12 WordPress plugins, all verified. Three
defects were worked around in the adopting project rather than fixed here.

The workaround lives at `plugins/.brandkit/deploy-wordpress.py` — 120 lines the
adopter should not have had to write. Each defect below is stated as the failing
test to write first, per the repo rule.

---

## 1. `derive` cannot run at the master size the skill's own example ships

`brand.example.json` sets `geometry.master` to `[1376, 768]`. Two of the five
entries in `FORMATS` (`bmk/derive.py:30`) are wider than that:

    hero            1920 x 480   -> wider than 1376
    wporg-banner    1544 x 500   -> wider than 1376

`derive` refuses both as upscales:

    master 1376x768 is too small for format hero (1920x480)

So stage 3 of the documented five-stage pipeline cannot complete on a project
configured exactly as the example says to configure it. The refusal itself is
right — upscaling AI art is worse than not shipping the format. The defect is
that the shipped config guarantees you hit it.

**Failing test:** load `brand.example.json`, derive every format from a master of
its declared `geometry.master` size, assert no `DeriveError`.

**Fix, in preference order:** raise the example master to at least 1920 wide
(1920x1072 keeps 16:9 and covers every format); or make `FORMATS` configurable
per project so an adopter can declare only the formats they consume; or have
`derive` skip-with-warning rather than fail, so one impossible format does not
block the four possible ones.

---

## 2. Every format crops from the *composited* master, which is wrong for headers

`derive` takes its input from `build/<slug>/master.png`, which `composite` has
already drawn the lockup onto. That is correct for a card and wrong for any
format the host renders live text over.

The concrete failure: the WordPress admin renders a live `<h1>` and a
`.dts-tagline` on top of `header-banner.webp` under a left-to-right scrim. A
composited header prints the product name **twice**, slightly offset, in two
different typefaces. It looks like a rendering bug and it ships silently — the
derive stage reports success.

**Failing test:** mark a format as un-composited in config, derive it, and assert
the output is pixel-identical to the same crop taken from the raw art.

**Fix:** let a format declare `"composited": true|false`, defaulting to `true`,
and have `derive` read raw art for the false ones.

---

## 3. `output_name()` hard-codes one naming scheme against one flat target list

`deploy.output_name()` (`bmk/deploy.py:69`) returns `"{slug}-{fmt}.webp"` and
`fan_out` copies it into every entry of a single `targets` list. That is one
routing rule, and it is the only one on offer.

WordPress needs three, none of which it matches:

    card    <plugin>/assets/images/dts-plugins/<slug>.webp
            slug only, no format suffix; every plugin holds a card for every
            product, because the rendering plugin is the fallback source
    header  <plugin>/assets/images/header-banner.webp
            unslugged, and only into that one plugin's own directory
    home    <plugin>/assets/images/dts-home-banner.webp
            one shared image, fanned to every plugin

All three are auto-discovery by *exact filename* in PHP, so a name that is
merely reasonable does not load — the image is simply absent, with no error.
This is not a WordPress quirk worth special-casing; it is what any host with
convention-based asset discovery looks like.

**Failing test:** configure a format with a name template and a target set,
deploy, assert the file lands at the configured path under the configured name.

**Fix:** move naming and routing into `brand.json` per format — a `name`
template (`"{slug}.webp"`, `"header-banner.webp"`) and a target selector
(`all` vs `own`) — rather than one global rule in code.

---

## What worked

Worth saying, because none of the above showed up until deployment: `config`,
`fonts`, `layout` and `composite` needed no workaround at all. Thirteen masters
composited first try. The longest title, `ABANDONED CART RECOVERY`, wrapped to
two lines inside the declared column with the tagline still clear of the frame,
and the shortest, `WOOMIE`, sat correctly without special-casing. The byte
budget held at 87,028 of 90,000 on the largest of 180 files. The layout maths is
sound; the plumbing around it is what needs the work.

## One gap that is still a gap

The spec's "art containing detectable lettering fails verification" has no test
and no code — it became a human check in `reference/manual-handoff.md` at
handoff. That check was performed here on all 13 images, by eye, via contact
sheets. All 13 were clean, so the gap cost nothing this time. It remains the one
requirement the pipeline states and does not enforce.
