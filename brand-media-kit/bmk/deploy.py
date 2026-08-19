"""Encode to WebP under a byte budget, then copy into every target directory.

Pillow's WebP encoder has no "hit this size" mode, so the budget is met by
descending quality until the file fits. Failing loudly when it never fits is
the point: an over-budget banner is invisible in review and obvious to anyone
loading the WordPress admin over a slow link.
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
import shutil
import sys

from PIL import Image

from bmk import project
from bmk.config import ConfigError
from bmk.derive import FORMATS


class BudgetError(Exception):
    pass


def to_webp(src, out, budget_bytes, q_hi=92, q_lo=55, step=4):
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")

    best = None
    for q in range(q_hi, q_lo - 1, -step):
        img.save(out, "WEBP", quality=q, method=6)
        size = out.stat().st_size
        if size <= budget_bytes:
            return out
        best = size

    raise BudgetError(
        "over budget: {} will not fit the {}-byte budget; smallest at "
        "quality {} was {} bytes".format(
            pathlib.Path(src).name, budget_bytes, q_lo, best
        )
    )


def fan_out(src, targets, name):
    src = pathlib.Path(src)
    written = []
    for target in targets:
        target = pathlib.Path(target)
        target.mkdir(parents=True, exist_ok=True)
        dest = target / name
        # copyfile, not copy2: copy2 carries mtimes across, and verify.py's
        # identity check would then depend on the clock rather than on bytes.
        shutil.copyfile(src, dest)
        written.append(dest)
    return written


def output_name(slug, fmt):
    """The filename a deployed asset carries in every target.

    Each target holds the media for every product, not just its own - the card
    grid on any one plugin's screen shows all of them - so the slug has to be in
    the filename or the last product copied would win.
    """
    return "{}-{}.webp".format(slug, fmt)


def main(argv=None):
    p = project.parser("Encode every derived format to WebP and copy it into each target.")
    p.add_argument("slugs", nargs="*", help="subjects to act on (default: all)")
    args = p.parse_args(argv)

    try:
        proj = project.load(args.project)
        subjects = proj.select(args.slugs)
        budget = proj.brand["budget_bytes"]
        targets = proj.targets

        count = 0
        for subject in subjects:
            slug = subject["slug"]
            build = proj.build(slug)
            for fmt in FORMATS:
                png = build / "{}.png".format(fmt)
                if not png.is_file():
                    print(
                        "brand-media-kit: {} missing - run python bmk/derive.py first".format(png),
                        file=sys.stderr,
                    )
                    return 1
                webp = build / "{}.webp".format(fmt)
                to_webp(png, webp, budget)
                fan_out(webp, targets, output_name(slug, fmt))
                count += 1
        print("deployed {} file(s) to {} target(s)".format(count, len(targets)))
        return 0
    except (project.ProjectError, ConfigError, BudgetError) as exc:
        print("brand-media-kit: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
