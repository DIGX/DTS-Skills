import pytest
from PIL import Image, ImageDraw

from bmk.composite import compose, draw_tracked
from bmk.fonts import load_font

BRAND = {
    "name": "DTS",
    "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
    "fonts": {"display": "BebasNeue-Regular.ttf", "body": "BebasNeue-Regular.ttf", "mono": "BebasNeue-Regular.ttf"},
    "geometry": {"master": [1376, 768], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
    "budget_bytes": 90000,
}

SUBJECT = {"slug": "gst", "title": "GST INVOICE", "tagline": "Compliant invoicing", "art": "an invoice"}


@pytest.fixture
def fonts_root(tmp_path, font_path):
    # compose() resolves brand["fonts"] names against a directory, so the test
    # supplies one holding the vendored face under the three brand names.
    root = tmp_path / "fonts"
    root.mkdir()
    (root / "BebasNeue-Regular.ttf").write_bytes(font_path.read_bytes())
    return root


def test_tracking_widens_the_line(font_path):
    draw = ImageDraw.Draw(Image.new("RGB", (1376, 768)))
    font = load_font(font_path, 64)
    tight = draw_tracked(draw, (0, 0), "DTS", font, (255, 255, 255), 0)
    loose = draw_tracked(draw, (0, 0), "DTS", font, (255, 255, 255), 6)
    assert loose > tight


def test_compose_writes_an_image_the_size_of_the_art(art_factory, fonts_root, tmp_path):
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    out = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "out.png")
    assert Image.open(out).size == (1376, 768)


def test_compose_is_deterministic(art_factory, fonts_root, tmp_path):
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    a = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "a.png")
    b = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "b.png")
    assert a.read_bytes() == b.read_bytes()


def test_different_subjects_produce_different_pixels(art_factory, fonts_root, tmp_path):
    # Guards the failure where every product gets the same banner because the
    # subject was read from the wrong variable. deploy.py's duplicate check
    # catches this too, but by then the operator has already generated 13
    # images and paid for them.
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    other = dict(SUBJECT, slug="cart", title="ABANDONED CART", tagline="Recover lost sales")
    a = compose(art, SUBJECT, BRAND, fonts_root, tmp_path / "a.png")
    b = compose(art, other, BRAND, fonts_root, tmp_path / "b.png")
    assert a.read_bytes() != b.read_bytes()


def test_ink_stays_inside_the_left_column(art_factory, fonts_root, tmp_path):
    # Solid black art, so every non-black pixel is text this module drew. If
    # the lockup runs past the column it collides with the art's subject on
    # the right, and on the plugin home header it collides with the live HTML
    # h1 that WordPress renders on top.
    art = art_factory(1376, 768, (0, 0, 0), "art.png")
    long_title = dict(SUBJECT, title="ABANDONED CART RECOVERY", tagline="Recover lost sales automatically for stores")
    out = compose(art, long_title, BRAND, fonts_root, tmp_path / "out.png")

    img = Image.open(out).convert("RGB")
    bbox = Image.eval(img, lambda v: v).getbbox()  # non-black extent
    assert bbox is not None, "compose drew nothing"
    left, _, right, _ = bbox
    margin = BRAND["geometry"]["margin"]
    column = BRAND["geometry"]["column"]
    assert left >= margin - 4          # a few px of glyph bearing is fine
    assert right <= margin + column + 4
