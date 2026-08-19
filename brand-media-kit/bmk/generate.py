"""Build the image prompt and get art back, by API or by hand.

The style paragraph below is a constant, not a template. Every product's
prompt embeds these exact bytes and differs only in one SUBJECT clause. That
is the entire consistency mechanism on the art side - the moment the style
text is assembled per product, the products drift apart again.

Two paths exist because a consumer Gemini Pro subscription does not include
API access; AI Studio keys are billed separately. Both paths call
build_prompt, so the manual route cannot drift from the automated one.
"""

import os
import pathlib

STYLE = (
    "Dark technical illustration, deep navy-to-black gradient background, "
    "thin luminous cyan and azure line-work, subtle circuit-like geometry, "
    "soft volumetric glow, shallow depth of field, high contrast, no grain, "
    "flat vector-adjacent rendering with a faint glass reflection. "
    "Composition: the left 45 percent of the frame is quiet - background "
    "gradient only, no detail, nothing that competes with overlaid type. "
    "The subject sits right of centre. "
    "Absolutely no text, no letters, no lettering, no numerals, no logos, "
    "no watermarks, no UI chrome anywhere in the image."
)

CONSTRAINTS = (
    "Output a single image, {w} x {h} pixels, 16:9. "
    "Keep the subject entirely between {low} percent and {high} percent of the "
    "frame height, because every derived crop keeps only that vertical band."
)


class GenerateError(Exception):
    pass


def has_api_key(env=None):
    env = os.environ if env is None else env
    return bool(env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY"))


def build_prompt(subject, brand):
    w, h = brand["geometry"]["master"]
    low, high = brand["geometry"]["subject_band_pct"]
    return "{}\n\nSUBJECT: {}\n\n{}".format(
        STYLE,
        subject["art"],
        CONSTRAINTS.format(w=w, h=h, low=low, high=high),
    )


def handoff(subjects, brand, out_dir):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "PROMPTS.md"

    blocks = ["# Image prompts", "", "Paste each block into the Gemini app, then save the returned",
              "image as `<slug>.png` in this directory. See reference/manual-handoff.md.", ""]
    for i, subject in enumerate(subjects, 1):
        blocks.append("## {}. {}".format(i, subject["slug"]))
        blocks.append("")
        blocks.append("```")
        blocks.append(build_prompt(subject, brand))
        blocks.append("```")
        blocks.append("")

    out.write_text("\n".join(blocks), encoding="utf-8")
    return out


def missing_art(subjects, art_dir):
    art_dir = pathlib.Path(art_dir)
    return [s["slug"] for s in subjects if not (art_dir / "{}.png".format(s["slug"])).is_file()]


def generate_via_api(subject, brand, out_path, model="gemini-3-pro-image"):
    # Imported here, not at module scope: the offline selftest runs on CI
    # runners with no SDK installed, and a top-level import would fail the
    # entire suite on every one of them.
    try:
        from google import genai
    except ImportError:
        raise GenerateError("google-genai is not installed; use the manual handoff path instead")

    if not has_api_key():
        raise GenerateError("no GEMINI_API_KEY or GOOGLE_API_KEY in the environment")

    client = genai.Client()
    response = client.models.generate_content(
        model=model, contents=build_prompt(subject, brand)
    )

    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline is not None and inline.data:
            out_path.write_bytes(inline.data)
            return out_path

    raise GenerateError("the model returned no image for {}".format(subject["slug"]))
