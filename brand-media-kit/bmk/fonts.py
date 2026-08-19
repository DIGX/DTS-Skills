"""Strict font loading.

Pillow raises OSError for an unreadable truetype file, and the conventional
response is to fall back to ImageFont.load_default(). That fallback is exactly
what this kit exists to prevent: one product silently rendered in a bitmap face
at the wrong size defeats the point of compositing text in code at all. So the
only fallback here is an exception.
"""

import pathlib

from PIL import ImageFont


class FontError(Exception):
    pass


def load_font(path, size):
    if not isinstance(size, int) or size <= 0:
        raise FontError("font size must be a positive int, got {!r}".format(size))

    path = pathlib.Path(path)
    if not path.is_file():
        raise FontError("font not found: {}".format(path))

    try:
        return ImageFont.truetype(str(path), size)
    except OSError as exc:
        raise FontError("font could not be loaded: {} ({})".format(path, exc))
