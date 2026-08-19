"""Draw the text lockup onto generated art.

Everything the eye reads as "brand" - face, size, tracking, colour, position -
is decided here in code rather than by the image model, because a model cannot
hold typography constant across thirteen separate generations. The art carries
the mood; this module carries the identity.
"""

# `python bmk/<stage>.py` - the form SKILL.md documents - puts bmk/ on sys.path
# rather than the skill root, so `import bmk` would fail on the next line, long
# before main() is reached. This has to sit above the package imports for that
# reason.
if __name__ == "__main__" and __package__ in (None, ""):
    import pathlib as _pathlib
    import sys as _sys

    _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))

import pathlib
import sys

from PIL import Image, ImageDraw

from bmk import project
from bmk.config import ConfigError
from bmk.fonts import FontError, load_font
from bmk.layout import LayoutError, fit, measure

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

# Every number above is in units of the 1376px reference width - the size the
# WordPress card CSS has always been fed. The master the model produces is
# wider (the WordPress.org banner is 1544 and derive refuses to upscale), so
# the lockup is scaled to whatever master it is handed and lands in the same
# place once derive brings the card back down.
REFERENCE_WIDTH = 1376


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

    scale = img.width / float(REFERENCE_WIDTH)
    margin = int(round(brand["geometry"]["margin"] * scale))
    column = int(round(brand["geometry"]["column"] * scale))
    paper = _rgb(brand["palette"]["paper"])
    primary = _rgb(brand["palette"]["primary"])

    display_path = fonts_root / brand["fonts"]["display"]
    body_path = fonts_root / brand["fonts"]["body"]

    # fit() is told the tracking so it measures the line the way draw_tracked
    # will paint it. Deducting a fixed allowance from the column instead only
    # works until a title is longer than the allowance assumed, and then the
    # type runs out of the quiet zone and into the art.
    title_tracking = TITLE_TRACKING * scale
    tagline_tracking = TAGLINE_TRACKING * scale

    title_lines, title_font = fit(
        draw,
        subject["title"],
        display_path,
        column,
        TITLE_LINES,
        int(round(TITLE_HI * scale)),
        int(round(TITLE_LO * scale)),
        tracking=title_tracking,
    )

    tagline_lines, tagline_font = fit(
        draw,
        subject["tagline"],
        body_path,
        column,
        TAGLINE_LINES,
        int(round(TAGLINE_SIZE_HI * scale)),
        int(round(TAGLINE_SIZE_LO * scale)),
        tracking=tagline_tracking,
    )

    y = int(img.height * TITLE_TOP_PCT)
    for line in title_lines:
        draw_tracked(draw, (margin, y), line, title_font, paper, title_tracking)
        y += int(title_font.size * LINE_GAP)

    y += int(round(BLOCK_GAP * scale))
    for line in tagline_lines:
        draw_tracked(draw, (margin, y), line, tagline_font, primary, tagline_tracking)
        y += int(tagline_font.size * LINE_GAP)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def main(argv=None):
    p = project.parser("Draw the text lockup onto each art master.")
    p.add_argument("slugs", nargs="*", help="subjects to act on (default: all)")
    args = p.parse_args(argv)

    try:
        proj = project.load(args.project)
        subjects = proj.select(args.slugs)

        missing = [s["slug"] for s in subjects if not proj.art(s["slug"]).is_file()]
        if missing:
            print(
                "brand-media-kit: no art for: {} - run python bmk/generate.py first".format(
                    ", ".join(missing)
                ),
                file=sys.stderr,
            )
            return 1

        for subject in subjects:
            out = proj.build(subject["slug"]) / "master.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            compose(proj.art(subject["slug"]), subject, proj.brand, proj.fonts_dir, out)
            print("composited {}".format(out))
        return 0
    except (project.ProjectError, ConfigError, FontError, LayoutError) as exc:
        print("brand-media-kit: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
