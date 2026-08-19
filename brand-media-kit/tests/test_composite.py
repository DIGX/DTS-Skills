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


def test_the_lockup_scales_with_the_master(art_factory, fonts_root, tmp_path):
    # brand.json states margin, column and type sizes in units of the 1376px
    # reference width - the size the WordPress card CSS has always been fed.
    # The master itself is 1920 wide, because the WordPress.org banner is
    # 1544 and derive refuses to upscale. So the lockup has to be drawn at
    # master scale and land in exactly the same place once derive brings the
    # card back down to 1376. Without that, every banner's type is 28% small.
    small_art = art_factory(1376, 768, (0, 0, 0), "small.png")
    big_art = art_factory(1920, 1080, (0, 0, 0), "big.png")

    small = compose(small_art, SUBJECT, BRAND, fonts_root, tmp_path / "s.png")
    big = compose(big_art, SUBJECT, BRAND, fonts_root, tmp_path / "b.png")

    reference = Image.open(small).convert("RGB").getbbox()
    scaled = Image.open(big).convert("RGB").resize((1376, 768), Image.LANCZOS).getbbox()

    assert reference is not None and scaled is not None
    assert all(abs(a - b) <= 6 for a, b in zip(reference, scaled)), (reference, scaled)


def test_ink_stays_inside_the_left_column_on_a_full_size_master(art_factory, fonts_root, tmp_path):
    art = art_factory(1920, 1080, (0, 0, 0), "art.png")
    long_title = dict(SUBJECT, title="ABANDONED CART RECOVERY", tagline="Recover lost sales automatically for stores")
    out = compose(art, long_title, BRAND, fonts_root, tmp_path / "out.png")

    bbox = Image.open(out).convert("RGB").getbbox()
    assert bbox is not None, "compose drew nothing"
    left, _, right, _ = bbox
    scale = 1920 / 1376.0
    margin = BRAND["geometry"]["margin"] * scale
    column = BRAND["geometry"]["column"] * scale
    assert left >= margin - 6
    assert right <= margin + column + 6
