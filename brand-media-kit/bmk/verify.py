"""The fence.

Imports no other bmk module on purpose. Every other stage reports what it
believes it did; this one re-reads what is actually on disk. A checker that
shares code with the thing it checks inherits its bugs.

The refusal to pass on an empty input set is the whole design. A fence that
reports clean because it was handed nothing is worse than no fence, because
it is trusted.
"""

import hashlib
import pathlib

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
