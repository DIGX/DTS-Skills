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

    # Tracking eats horizontal room, so fit() is given the column minus the
    # worst case it could add. Without this the longest title fits at measure
    # time and overflows at draw time.
    title_tracking = TITLE_TRACKING * scale
    tagline_tracking = TAGLINE_TRACKING * scale

    title_budget = column - title_tracking * 12
    title_lines, title_font = fit(
        draw,
        subject["title"],
        display_path,
        title_budget,
        TITLE_LINES,
        int(round(TITLE_HI * scale)),
        int(round(TITLE_LO * scale)),
    )

    tagline_budget = column - tagline_tracking * 12
    tagline_lines, tagline_font = fit(
        draw,
        subject["tagline"],
        body_path,
        tagline_budget,
        TAGLINE_LINES,
        int(round(TAGLINE_SIZE_HI * scale)),
        int(round(TAGLINE_SIZE_LO * scale)),
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
