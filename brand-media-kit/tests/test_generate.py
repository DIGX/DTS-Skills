import pytest

from bmk.generate import STYLE, build_prompt, handoff, has_api_key, missing_art

BRAND = {
    "name": "DTS",
    "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
    "fonts": {"display": "D.ttf", "body": "B.ttf", "mono": "M.ttf"},
    "geometry": {"master": [1920, 1080], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
    "budget_bytes": 90000,
}

SUBJECTS = [
    {"slug": "gst", "title": "GST INVOICE", "tagline": "t", "art": "a stylised invoice document"},
    {"slug": "cart", "title": "ABANDONED CART", "tagline": "t", "art": "a shopping cart mid-motion"},
]


def test_every_prompt_shares_a_byte_identical_style_paragraph():
    # This is the whole mechanism. If the style paragraph is ever built by
    # interpolation rather than copied verbatim, thirteen products drift
    # apart again and the kit has failed at its only job.
    prompts = [build_prompt(s, BRAND) for s in SUBJECTS]
    assert all(STYLE in p for p in prompts)
    assert len(set(prompts)) == len(prompts)


def test_the_prompt_carries_the_subject_clause():
    prompt = build_prompt(SUBJECTS[0], BRAND)
    assert "a stylised invoice document" in prompt
    assert "SUBJECT:" in prompt


def test_the_prompt_forbids_text_in_the_art():
    # Model-rendered lettering is the failure this kit is built around: it
    # arrives in a different face every generation and often misspelled.
    prompt = build_prompt(SUBJECTS[0], BRAND)
    lowered = prompt.lower()
    assert "no text" in lowered
    assert "no letter" in lowered or "no lettering" in lowered


def test_the_prompt_states_the_quiet_left_and_the_subject_band():
    prompt = build_prompt(SUBJECTS[0], BRAND)
    assert "left" in prompt.lower()
    assert "28" in prompt and "72" in prompt


def test_the_prompt_states_the_master_size():
    assert "1920" in build_prompt(SUBJECTS[0], BRAND)


def test_has_api_key_reads_the_environment():
    assert has_api_key({"GEMINI_API_KEY": "x"}) is True
    assert has_api_key({"GOOGLE_API_KEY": "x"}) is True
    assert has_api_key({}) is False
    assert has_api_key({"GEMINI_API_KEY": ""}) is False


def test_handoff_writes_one_numbered_block_per_subject(tmp_path):
    out = handoff(SUBJECTS, BRAND, tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "1." in text and "2." in text
    for s in SUBJECTS:
        assert s["slug"] in text
        assert s["art"] in text


def test_missing_art_lists_only_the_slugs_without_a_file(tmp_path):
    (tmp_path / "gst.png").write_bytes(b"x")
    assert missing_art(SUBJECTS, tmp_path) == ["cart"]


def test_the_module_imports_without_the_sdk():
    # The selftest runs offline on CI with no google-genai installed. If the
    # import moves to module scope, every test in the suite fails on a
    # machine that has no SDK - which is every CI runner.
    import importlib

    import bmk.generate

    importlib.reload(bmk.generate)


def test_generate_via_api_is_never_reached_without_a_key(monkeypatch, tmp_path):
    from bmk import generate

    def explode(*_a, **_k):
        raise AssertionError("the API path must not run in the offline suite")

    monkeypatch.setattr(generate, "generate_via_api", explode)
    assert has_api_key({}) is False


def test_the_quiet_left_zone_covers_the_whole_lockup_column():
    # The prompt reserves a quiet strip on the left; composite.py draws the
    # lockup from `margin` to `margin + column`. If the strip is narrower than
    # the lockup, the model is free to put detail exactly where the tagline
    # lands, and the two only meet on the finished banner.
    import re

    from bmk.composite import REFERENCE_WIDTH

    stated = re.search(r"left (\d+) percent", STYLE)
    assert stated, "STYLE no longer states a quiet-left percentage"

    lockup_pct = 100.0 * (BRAND["geometry"]["margin"] + BRAND["geometry"]["column"]) / REFERENCE_WIDTH
    assert int(stated.group(1)) >= lockup_pct
