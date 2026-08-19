import pytest
from PIL import ImageFont

from bmk.fonts import FontError, load_font


def test_loads_a_real_font(font_path):
    font = load_font(font_path, 72)
    assert font.getlength("DTS") > 0


def test_a_missing_font_raises(tmp_path):
    with pytest.raises(FontError, match="font not found"):
        load_font(tmp_path / "nope.ttf", 72)


def test_a_corrupt_font_raises(tmp_path):
    bad = tmp_path / "bad.ttf"
    bad.write_bytes(b"this is not a font")
    with pytest.raises(FontError, match="could not be loaded"):
        load_font(bad, 72)


def test_it_never_falls_back_to_the_default_face(tmp_path, monkeypatch):
    # The whole point of the module. If a future edit adds a try/except that
    # reaches for load_default, this test detonates rather than shipping one
    # product rendered in a bitmap face nobody notices until print.
    def explode(*_args, **_kwargs):
        raise AssertionError("load_default must never be reached")

    monkeypatch.setattr(ImageFont, "load_default", explode)

    bad = tmp_path / "bad.ttf"
    bad.write_bytes(b"nope")
    with pytest.raises(FontError):
        load_font(bad, 72)


def test_a_nonpositive_size_raises(font_path):
    with pytest.raises(FontError, match="size"):
        load_font(font_path, 0)
