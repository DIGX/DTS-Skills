"""Encode to WebP under a byte budget, then copy into every target directory.

Pillow's WebP encoder has no "hit this size" mode, so the budget is met by
descending quality until the file fits. Failing loudly when it never fits is
the point: an over-budget banner is invisible in review and obvious to anyone
loading the WordPress admin over a slow link.
"""

import pathlib
import shutil

from PIL import Image


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
