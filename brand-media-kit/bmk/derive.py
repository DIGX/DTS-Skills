"""One 16:9 master becomes every wide format by a centre-band crop.

Generating each format separately would mean each is a different image, which
is how the current banners ended up with no family resemblance. Cropping one
master guarantees the family resemblance is literal - it is the same picture.

The cost is that the subject must live in the vertical band every crop keeps.
The tightest format here is 4:1, which keeps roughly 28%-72% of the master's
height, and that is exactly the band the generation prompt asks for.
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

from PIL import Image
import sys

from bmk import project
from bmk.config import ConfigError

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


def main(argv=None):
    p = project.parser("Crop every delivery format out of each composited master.")
    p.add_argument("slugs", nargs="*", help="subjects to act on (default: all)")
    args = p.parse_args(argv)

    try:
        proj = project.load(args.project)
        subjects = proj.select(args.slugs)

        missing = [
            s["slug"] for s in subjects if not (proj.build(s["slug"]) / "master.png").is_file()
        ]
        if missing:
            print(
                "brand-media-kit: no composite for: {} - run python bmk/composite.py first".format(
                    ", ".join(missing)
                ),
                file=sys.stderr,
            )
            return 1

        for subject in subjects:
            out_dir = proj.build(subject["slug"])
            written = derive(out_dir / "master.png", out_dir)
            print("derived {} format(s) for {}".format(len(written), subject["slug"]))
        return 0
    except (project.ProjectError, ConfigError, DeriveError) as exc:
        print("brand-media-kit: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
