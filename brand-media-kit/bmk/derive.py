"""One 16:9 master becomes every wide format by a centre-band crop.

Generating each format separately would mean each is a different image, which
is how the current banners ended up with no family resemblance. Cropping one
master guarantees the family resemblance is literal - it is the same picture.

The cost is that the subject must live in the vertical band every crop keeps.
The tightest format here is 4:1, which keeps roughly 28%-72% of the master's
height, and that is exactly the band the generation prompt asks for.
"""

import pathlib

from PIL import Image

FORMATS = {
    "card": (1376, 768),
    "header": (1376, 400),
    "hero": (1920, 480),
    "wporg-banner": (1544, 500),
    "wporg-banner-sm": (772, 250),
}

ASPECT_TOLERANCE = 0.02


class DeriveError(Exception):
    pass


def centre_band(size, target_w, target_h):
    src_w, src_h = size
    band_h = int(round(src_w * target_h / float(target_w)))
    if band_h > src_h:
        # Target is taller than the master's aspect: keep full height and
        # crop width instead, still centred.
        band_w = int(round(src_h * target_w / float(target_h)))
        left = (src_w - band_w) // 2
        return (left, 0, left + band_w, src_h)

    top = (src_h - band_h) // 2
    return (0, top, src_w, top + band_h)


def band_bounds_pct(size, target_w, target_h):
    _, src_h = size
    _, top, _, bottom = centre_band(size, target_w, target_h)
    return (100.0 * top / src_h, 100.0 * bottom / src_h)


def derive(master_path, out_dir, formats=None):
    formats = FORMATS if formats is None else formats
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master = Image.open(master_path).convert("RGB")
    src_w, src_h = master.size

    if abs((src_w / float(src_h)) - (16.0 / 9.0)) > ASPECT_TOLERANCE:
        raise DeriveError(
            "master must be 16:9, got {}x{} ({:.3f})".format(src_w, src_h, src_w / float(src_h))
        )

    written = {}
    for key, (w, h) in formats.items():
        if w > src_w or h > src_h:
            raise DeriveError(
                "master {}x{} is too small for format {} ({}x{}); "
                "upscaling AI art past its native size looks fine at review "
                "size and terrible in the listing".format(src_w, src_h, key, w, h)
            )
        box = centre_band(master.size, w, h)
        out = out_dir / "{}.png".format(key)
        master.crop(box).resize((w, h), Image.LANCZOS).save(out)
        written[key] = out

    return written
