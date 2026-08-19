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


def measure(draw, text, font, tracking=0):
    """Width of `text` as composite.draw_tracked will actually paint it.

    Tracking goes between glyphs, never after the last one, so an n-glyph run
    is n-1 gaps wider than Pillow reports. Fitting against the untracked width
    is how type that measured as fitting ends up over the column edge.
    """
    width = draw.textlength(text, font=font)
    if tracking and text:
        width += tracking * (len(text) - 1)
    return width


def wrap(draw, text, font, max_width, tracking=0):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = "{} {}".format(current, word)
        if measure(draw, candidate, font, tracking) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit(draw, text, font_path, max_width, max_lines, size_hi, size_lo, step=2, tracking=0):
    if size_hi < size_lo:
        raise LayoutError("size_hi ({}) must be >= size_lo ({})".format(size_hi, size_lo))

    for size in range(size_hi, size_lo - 1, -step):
        font = load_font(font_path, size)
        lines = wrap(draw, text, font, max_width, tracking)
        if len(lines) <= max_lines and all(
            measure(draw, line, font, tracking) <= max_width for line in lines
        ):
            return lines, font

    raise LayoutError(
        "{!r} does not fit {}px x {} lines even at {}px".format(text, max_width, max_lines, size_lo)
    )
