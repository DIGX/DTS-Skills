"""Where an adopting project keeps its brand kit.

Five commands run in a row need the same four answers - which config, which
fonts, where the art landed, where the build goes - and an operator should not
have to repeat them five times. `scripts/install` scaffolds the `.brandkit`
directory this module then finds.

Layout, all of it under the project root:

    .brandkit/brand.json     palette, fonts, geometry, byte budget
    .brandkit/assets.json    subjects and target directories
    .brandkit/fonts/         the font files brand.json names
    .brandkit/art/           one <slug>.png master per subject, from the model
    .brandkit/build/<slug>/  master.png plus one PNG per derived format

Only `art/` is precious: everything under `build/` is reproducible from it, and
everything in the targets is reproducible from `build/`.
"""

import argparse
import pathlib

from bmk.config import load_assets, load_brand

DIRNAME = ".brandkit"


class ProjectError(Exception):
    pass


class Project:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        self.kit = self.root / DIRNAME
        self.brand = load_brand(self.kit / "brand.json")
        self.assets = load_assets(self.kit / "assets.json")

    @property
    def subjects(self):
        return self.assets["subjects"]

    @property
    def fonts_dir(self):
        return self.kit / "fonts"

    @property
    def art_dir(self):
        return self.kit / "art"

    @property
    def build_dir(self):
        return self.kit / "build"

    @property
    def targets(self):
        # Relative to the project root, not the caller's cwd: the same command
        # must mean the same thing from anywhere in the tree.
        return [self.root / t for t in self.assets["targets"]]

    def art(self, slug):
        return self.art_dir / "{}.png".format(slug)

    def build(self, slug):
        return self.build_dir / slug

    def select(self, slugs):
        """The named subjects, in config order, or all of them if none named."""
        if not slugs:
            return list(self.subjects)
        known = {s["slug"]: s for s in self.subjects}
        unknown = [s for s in slugs if s not in known]
        if unknown:
            raise ProjectError(
                "no such subject in assets.json: {}".format(", ".join(unknown))
            )
        return [known[s] for s in slugs]


def find(start=None):
    """Walk up from `start` for the nearest .brandkit, the way git finds .git."""
    start = pathlib.Path(start or pathlib.Path.cwd()).resolve()
    for candidate in [start] + list(start.parents):
        if (candidate / DIRNAME / "brand.json").is_file():
            return candidate
    raise ProjectError(
        "no {}/brand.json at or above {} - run scripts/install first".format(DIRNAME, start)
    )


def load(root=None):
    """Open the project at `root`, or the nearest one above the cwd.

    An explicit root is taken literally rather than walked up from: a typo in
    --project must fail here, not silently pick up the kit two levels above and
    write media into somebody else's plugin.
    """
    if root is None:
        root = find()
    else:
        root = pathlib.Path(root).resolve()
        if not (root / DIRNAME / "brand.json").is_file():
            raise ProjectError("no {}/brand.json under {}".format(DIRNAME, root))
    return Project(root)


def parser(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument(
        "--project",
        default=None,
        metavar="DIR",
        help="project root holding {}/ (default: nearest above the cwd)".format(DIRNAME),
    )
    return p
