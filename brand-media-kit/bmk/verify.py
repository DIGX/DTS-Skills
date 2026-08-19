"""The fence.

Imports no other bmk module on purpose. Every other stage reports what it
believes it did; this one re-reads what is actually on disk. A checker that
shares code with the thing it checks inherits its bugs.

The refusal to pass on an empty input set is the whole design. A fence that
reports clean because it was handed nothing is worse than no fence, because
it is trusted.
"""

# `python bmk/<stage>.py` - the form SKILL.md documents - puts bmk/ on sys.path
# rather than the skill root, so `import bmk` would fail on the next line, long
# before main() is reached. This has to sit above the package imports for that
# reason.
if __name__ == "__main__" and __package__ in (None, ""):
    import pathlib as _pathlib
    import sys as _sys

    _sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))

import hashlib
import pathlib
import sys

from PIL import Image


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(expected, roots, budget_bytes):
    problems = []

    if not expected:
        problems.append("nothing to verify: the expected file set is empty")
    if not roots:
        problems.append("no target directories given")
    if problems:
        return problems

    digests = {}

    for root in roots:
        root = pathlib.Path(root)
        if not root.is_dir():
            problems.append("target directory is missing: {}".format(root))
            continue

        for name, size in expected.items():
            path = root / name
            if not path.is_file():
                problems.append("missing: {}".format(path))
                continue

            actual = path.stat().st_size
            if actual > budget_bytes:
                problems.append(
                    "over budget: {} is {} bytes, limit {}".format(path, actual, budget_bytes)
                )

            try:
                with Image.open(path) as img:
                    got = img.size
            except OSError as exc:
                problems.append("unreadable: {} ({})".format(path, exc))
                continue

            if got != tuple(size):
                problems.append(
                    "wrong size: {} is {}x{}, expected {}x{}".format(
                        path, got[0], got[1], size[0], size[1]
                    )
                )

            digests.setdefault(name, {})[str(root)] = _digest(path)

    # Same name, different bytes across roots: the set has drifted out of sync.
    for name, by_root in digests.items():
        if len(set(by_root.values())) > 1:
            problems.append(
                "copies differ between targets: {} ({})".format(name, ", ".join(sorted(by_root)))
            )

    # Different names, same bytes: one product is wearing another's picture.
    first_seen = {}
    for name, by_root in sorted(digests.items()):
        for root, digest in sorted(by_root.items()):
            if digest in first_seen and first_seen[digest] != name:
                problems.append(
                    "identical images for different assets: {} and {}".format(first_seen[digest], name)
                )
            first_seen.setdefault(digest, name)

    return problems


def main(argv=None):
    # Imported here rather than at module scope, and asserted by
    # tests/test_cli.py: verify() itself must stay clear of the code it checks.
    # The CLI still has to learn the expected set from somewhere, and the honest
    # source is what the operator declared - assets.json - crossed with the
    # published format table.
    from bmk import project
    from bmk.config import ConfigError
    from bmk.deploy import output_name
    from bmk.derive import FORMATS

    p = project.parser("Re-read what is on disk and report anything wrong with it.")
    args = p.parse_args(argv)

    try:
        proj = project.load(args.project)
        expected = {
            output_name(subject["slug"], fmt): size
            for subject in proj.subjects
            for fmt, size in FORMATS.items()
        }
        problems = verify(expected, proj.targets, proj.brand["budget_bytes"])
    except (project.ProjectError, ConfigError) as exc:
        print("brand-media-kit: {}".format(exc), file=sys.stderr)
        return 1

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print("verify: {} problem(s)".format(len(problems)), file=sys.stderr)
        return 1

    print("verify: {} file(s) x {} target(s), all clean".format(len(expected), len(proj.targets)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
