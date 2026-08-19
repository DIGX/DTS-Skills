import pytest
from PIL import Image

from bmk.deploy import BudgetError, fan_out, to_webp


def test_it_writes_a_webp(art_factory, tmp_path):
    src = art_factory(1376, 768, (34, 113, 177), "a.png")
    out = to_webp(src, tmp_path / "a.webp", 90000)
    assert out.is_file()
    assert Image.open(out).format == "WEBP"


def test_it_stays_under_budget(art_factory, tmp_path):
    src = art_factory(1376, 768, (34, 113, 177), "a.png")
    out = to_webp(src, tmp_path / "a.webp", 90000)
    assert out.stat().st_size <= 90000


def test_it_preserves_the_pixel_dimensions(art_factory, tmp_path):
    src = art_factory(1544, 500, (34, 113, 177), "a.png")
    out = to_webp(src, tmp_path / "a.webp", 90000)
    assert Image.open(out).size == (1544, 500)


def test_an_unmeetable_budget_raises(art_factory, tmp_path):
    # Silently shipping an over-budget file is the failure mode that matters:
    # nobody reads the byte count, they just notice the admin page got slow.
    src = art_factory(1920, 480, (34, 113, 177), "a.png")
    with pytest.raises(BudgetError, match="budget"):
        to_webp(src, tmp_path / "a.webp", 50)


def test_fan_out_writes_one_copy_per_target(art_factory, tmp_path):
    src = art_factory(64, 36, (0, 0, 0), "a.png")
    targets = [tmp_path / "one", tmp_path / "two", tmp_path / "three"]
    written = fan_out(src, targets, "banner.png")
    assert len(written) == 3
    assert all(p.is_file() for p in written)
    assert all(p.name == "banner.png" for p in written)


def test_fan_out_copies_are_byte_identical(art_factory, tmp_path):
    src = art_factory(64, 36, (0, 0, 0), "a.png")
    written = fan_out(src, [tmp_path / "one", tmp_path / "two"], "banner.png")
    assert written[0].read_bytes() == written[1].read_bytes() == src.read_bytes()


def test_fan_out_creates_missing_directories(art_factory, tmp_path):
    src = art_factory(64, 36, (0, 0, 0), "a.png")
    deep = tmp_path / "plugins" / "new-plugin" / "assets" / "images"
    written = fan_out(src, [deep], "banner.png")
    assert written[0].is_file()
