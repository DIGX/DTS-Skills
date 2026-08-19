# Manual handoff

The path for when there is no API key — and the human check that every path
depends on.

## Why this path exists at all

A consumer Gemini Pro subscription does not include API access; AI Studio keys
are billed separately. Plenty of people who can generate these images in a
browser cannot generate them from a script. Both routes call the same
`build_prompt`, so the manual route cannot drift from the automated one — the
prompt you paste is byte-for-byte the prompt the API would have sent.

## The steps

1. **Write the prompts.**

   ```
   python bmk/generate.py --handoff
   ```

   This writes `.brandkit/art/PROMPTS.md`, one numbered block per product that
   is still missing art. It writes nothing else and never touches the network.

2. **Generate each image.** Paste one block into the Gemini app, ask for a
   single image, and read what comes back before you do anything else.

3. **Check it. See below — this is the step that matters.**

4. **Save it** as `.brandkit/art/<slug>.png`, using the slug from the block
   heading. The filename is how every later stage finds it; a typo shows up as
   "no art for: …" at the composite step.

5. **Confirm the set is complete.**

   ```
   python bmk/generate.py --check
   ```

   Exits non-zero and names any product still missing art. Then carry on with
   `python bmk/composite.py`.

## The check

**Before saving, look at the image and reject it if it contains any lettering.**

Not "fix it", not "crop it out" — reject it and generate again. Letterforms in
generated art are usually near-words: plausible glyph shapes that read as text
until someone looks closely, at which point they read as a mistake nobody
proofread. On a WordPress.org listing, that is the first impression.

Reject on any of these:

- Letters, numerals, or word-like glyph clusters, anywhere, at any size.
- Logos, wordmarks, or watermarks.
- UI chrome — buttons, tabs, menus, address bars — since it almost always
  carries labels.
- Detail in the left 45% of the frame. The lockup is drawn there and needs the
  space empty; art that fills it will have type sitting on top of it.
- A subject that strays outside the top and bottom band named in the prompt.
  Everything outside it is cropped away in four of the five formats.

The prompt asks for no text in six different ways and models still produce it.
That is why the check is here rather than trusted to the prompt.

### Why a person does this and not the code

The obvious automation is OCR — run Tesseract or a cloud vision API over each
master and fail on any detected glyph. Both were rejected:

- The selftest must run **offline** and spend **no quota**. A cloud vision call
  breaks both. Tesseract breaks neither, but adds a system binary that the
  selftest would have to detect, skip around, and quietly stop enforcing on
  every machine that lacks it — a check that silently disables itself is worse
  than a documented one that does not.
- OCR is unreliable on exactly this input: low-contrast luminous line-work over
  a dark gradient, which is where it both misses real lettering and invents it
  from circuit traces.

So this is a **human gate**, deliberately, and it is the one gate in the kit
with no automated backstop. If you skip it, nothing downstream will catch it:
`bmk/verify.py` checks sizes, budgets, and byte identity, and it cannot read.

## Using the API instead

If `GEMINI_API_KEY` or `GOOGLE_API_KEY` is in the environment, plain
`python bmk/generate.py` calls the model directly and writes the masters itself.
It also needs the `google-genai` package, which is deliberately not in
`requirements.txt` — the selftest must install nothing that could reach the
network.

The check above still applies. Open every generated master and look at it before
you composite. The API path removes the pasting, not the judgement.
