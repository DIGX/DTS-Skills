"""Shared fixtures.

The font is vendored rather than resolved from the system: CI runners disagree
about what is installed, and Pillow silently substitutes a bitmap default when
a truetype load fails, which would make every layout assertion measure a font
that is not the one we ship.
"""

import pathlib
import sys

import pytest
from PIL import Image

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


@pytest.fixture
def font_path():
    path = FIXTURES / "BebasNeue-Regular.ttf"
    assert path.is_file(), "test font missing; see Task 1 of the plan"
    return path


@pytest.fixture
def art_factory(tmp_path):
    """Make a flat-colour PNG standing in for generated art."""

    def _make(w, h, colour, name):
        out = tmp_path / name
        Image.new("RGB", (w, h), colour).save(out)
        return out

    return _make
