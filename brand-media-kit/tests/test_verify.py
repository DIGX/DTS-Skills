import pytest
from PIL import Image

from bmk.verify import verify

EXPECTED = {"card.webp": (1376, 768), "header.webp": (1376, 400)}


def put(root, name, size, colour=(34, 113, 177)):
    root.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, colour).save(root / name, "WEBP", quality=80)
    return root / name


@pytest.fixture
def clean(tmp_path):
    roots = [tmp_path / "a", tmp_path / "b"]
    for i, name in enumerate(EXPECTED):
        img = Image.new("RGB", EXPECTED[name], (34, 113 + i * 40, 177))
        for root in roots:
            root.mkdir(parents=True, exist_ok=True)
            img.save(root / name, "WEBP", quality=80)
    return roots


def test_a_clean_tree_reports_nothing(clean):
    assert verify(EXPECTED, clean, 90000) == []


def test_an_empty_expected_set_is_itself_a_failure(clean):
    # A fence given nothing to check must not report clean. This repo has
    # shipped that bug before; it is why this test is first.
    problems = verify({}, clean, 90000)
    assert problems
    assert any("nothing to verify" in p for p in problems)


def test_no_roots_is_itself_a_failure():
    problems = verify(EXPECTED, [], 90000)
    assert problems
    assert any("no target" in p for p in problems)


def test_a_missing_file_is_reported(clean):
    (clean[1] / "header.webp").unlink()
    problems = verify(EXPECTED, clean, 90000)
    assert any("header.webp" in p and "missing" in p for p in problems)


def test_a_missing_root_is_reported(tmp_path, clean):
    problems = verify(EXPECTED, clean + [tmp_path / "ghost"], 90000)
    assert any("ghost" in p for p in problems)


def test_two_products_with_identical_bytes_are_reported(tmp_path):
    # The exact defect in the current DTS set: dts-banner-default.webp and
    # dts-shipment-tracking.webp are the same 78792 bytes, so one product is
    # wearing another's picture.
    root = tmp_path / "a"
    img = Image.new("RGB", (1376, 768), (34, 113, 177))
    root.mkdir(parents=True)
    img.save(root / "card.webp", "WEBP", quality=80)
    img.save(root / "header.webp", "WEBP", quality=80)
    problems = verify({"card.webp": (1376, 768), "header.webp": (1376, 768)}, [root], 90000)
    assert any("identical" in p for p in problems)


def test_copies_that_differ_between_roots_are_reported(clean):
    # Same name, different bytes across plugin directories is how the set
    # silently drifts out of sync one deploy at a time.
    Image.new("RGB", (1376, 768), (200, 10, 10)).save(clean[1] / "card.webp", "WEBP", quality=80)
    problems = verify(EXPECTED, clean, 90000)
    assert any("card.webp" in p and "differ" in p for p in problems)


def test_a_wrong_size_is_reported(clean):
    put(clean[0], "card.webp", (800, 600))
    problems = verify(EXPECTED, clean, 90000)
    assert any("card.webp" in p and "1376x768" in p for p in problems)


def test_an_over_budget_file_is_reported(clean):
    problems = verify(EXPECTED, clean, 100)
    assert any("budget" in p for p in problems)
