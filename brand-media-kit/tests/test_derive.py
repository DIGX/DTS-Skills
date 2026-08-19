import pytest
from PIL import Image

from bmk.derive import FORMATS, DeriveError, band_bounds_pct, centre_band, derive

# The master is the largest format, not the card size. WordPress.org fixes its
# banner at 1544x500 and the hero is 1920 wide, so a 1376-wide master could
# only serve them by upscaling - which derive refuses to do.
MASTER = (1920, 1080)


def test_every_format_is_produced_at_its_exact_size(art_factory, tmp_path):
    master = art_factory(MASTER[0], MASTER[1], (10, 30, 60), "master.png")
    out = derive(master, tmp_path / "out")
    assert set(out) == set(FORMATS)
    for key, path in out.items():
        assert Image.open(path).size == FORMATS[key], key


def test_the_crop_is_vertically_centred():
    left, top, right, bottom = centre_band(MASTER, 1920, 480)
    assert left == 0 and right == MASTER[0]
    assert abs(top - (MASTER[1] - (bottom - top)) / 2) <= 1


def test_the_subject_band_survives_the_tightest_crop():
    # The prompt tells the model to keep the subject between 28% and 72% of
    # the frame height. If any format's surviving band is narrower than that,
    # the prompt and the crop maths have drifted apart and some product will
    # ship with its subject sliced off.
    for key, (w, h) in FORMATS.items():
        low, high = band_bounds_pct(MASTER, w, h)
        assert low <= 28.0 + 0.5, key
        assert high >= 72.0 - 0.5, key


def test_the_tightest_format_is_about_a_quarter_band():
    low, high = band_bounds_pct(MASTER, 1920, 480)
    assert 27.0 <= low <= 28.0
    assert 72.0 <= high <= 73.0


def test_a_master_smaller_than_a_target_raises(art_factory, tmp_path):
    # Upscaling an AI image past its native resolution produces mush that
    # looks fine at review size and terrible on the WordPress.org listing.
    small = art_factory(400, 225, (0, 0, 0), "small.png")
    with pytest.raises(DeriveError, match="too small"):
        derive(small, tmp_path / "out")


def test_a_card_sized_master_is_rejected(art_factory, tmp_path):
    # The trap this whole module is shaped around: 1376x768 is the *card*
    # size, and it is 168px narrower than the WordPress.org banner. Handing
    # derive a card-sized master must fail loudly here rather than quietly
    # ship a blurred listing image.
    card_sized = art_factory(1376, 768, (0, 0, 0), "card.png")
    with pytest.raises(DeriveError, match="too small"):
        derive(card_sized, tmp_path / "out")


def test_a_non_16_9_master_raises(art_factory, tmp_path):
    square = art_factory(1024, 1024, (0, 0, 0), "square.png")
    with pytest.raises(DeriveError, match="16:9"):
        derive(square, tmp_path / "out")
