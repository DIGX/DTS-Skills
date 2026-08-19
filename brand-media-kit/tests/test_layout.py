import pytest
from PIL import Image, ImageDraw

from bmk.fonts import load_font
from bmk.layout import LayoutError, fit, measure, wrap


@pytest.fixture
def draw():
    return ImageDraw.Draw(Image.new("RGB", (1376, 768)))


def test_measure_grows_with_the_string(draw, font_path):
    font = load_font(font_path, 64)
    assert measure(draw, "DTS", font) < measure(draw, "DTS INVOICE", font)


def test_wrap_keeps_one_line_when_it_fits(draw, font_path):
    font = load_font(font_path, 48)
    assert wrap(draw, "GST INVOICE", font, 10000) == ["GST INVOICE"]


def test_wrap_breaks_on_words_not_characters(draw, font_path):
    font = load_font(font_path, 96)
    lines = wrap(draw, "ABANDONED CART RECOVERY", font, 400)
    assert len(lines) > 1
    assert " ".join(lines) == "ABANDONED CART RECOVERY"
    assert all(line == line.strip() for line in lines)


def test_a_single_word_wider_than_the_column_still_returns_it(draw, font_path):
    # Better to overflow visibly on one word than to hyphenate a product name.
    # fit() is what turns this into a shrink; wrap() must not lose characters.
    font = load_font(font_path, 200)
    assert wrap(draw, "SUPERCALIFRAGILISTIC", font, 50) == ["SUPERCALIFRAGILISTIC"]


def test_fit_shrinks_until_it_fits(draw, font_path):
    lines, font = fit(draw, "ABANDONED CART RECOVERY", font_path, 517, 2, 120, 40)
    assert len(lines) <= 2
    assert all(measure(draw, line, font) <= 517 for line in lines)
    assert font.size <= 120


def test_fit_never_grows_a_short_title(draw, font_path):
    _, small = fit(draw, "GST", font_path, 517, 2, 96, 40)
    _, big = fit(draw, "ABANDONED CART RECOVERY", font_path, 517, 2, 96, 40)
    assert small.size == 96
    assert big.size <= small.size


def test_fit_raises_when_nothing_fits(draw, font_path):
    with pytest.raises(LayoutError, match="does not fit"):
        fit(draw, "ABANDONED CART RECOVERY", font_path, 40, 1, 120, 100)


def test_fit_rejects_a_backwards_size_range(draw, font_path):
    with pytest.raises(LayoutError, match="size_hi"):
        fit(draw, "X", font_path, 517, 2, 40, 120)


def test_measure_counts_the_tracking_between_glyphs(draw, font_path):
    from bmk.fonts import load_font

    font = load_font(font_path, 40)
    plain = measure(draw, "SHIPPING", font)
    tracked = measure(draw, "SHIPPING", font, tracking=3)
    # Seven gaps in an eight-glyph word: tracking sits between glyphs, not
    # after the last one, which is what draw_tracked actually paints.
    assert tracked == plain + 3 * 7


def test_fit_honours_tracking_when_it_shrinks(draw, font_path):
    # Same text, same column: with tracking asked for, the type has to come
    # down a size or wrap, because the tracked run is genuinely wider.
    lines_plain, font_plain = fit(draw, "WOOCOMMERCE SHIPMENT TRACKING", font_path, 600, 2, 96, 40)
    lines_tracked, font_tracked = fit(
        draw, "WOOCOMMERCE SHIPMENT TRACKING", font_path, 600, 2, 96, 40, tracking=6
    )
    assert font_tracked.size <= font_plain.size
    for line in lines_tracked:
        assert measure(draw, line, font_tracked, tracking=6) <= 600
