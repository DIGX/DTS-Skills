from PIL import Image, ImageFont

import bmk


def test_package_imports():
    assert bmk is not None


def test_font_fixture_loads_at_a_real_size(font_path):
    font = ImageFont.truetype(str(font_path), 64)
    assert font.getlength("DTS") > 0


def test_art_factory_makes_the_size_asked_for(art_factory):
    path = art_factory(1376, 768, (10, 30, 60), "art.png")
    assert Image.open(path).size == (1376, 768)
