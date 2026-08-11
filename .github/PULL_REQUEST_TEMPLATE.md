<!--
One logical change per PR, please. See CONTRIBUTING.md.
-->

## What this changes

<!-- One or two sentences. -->

## The failing test

<!--
This repo's one firm rule: no change to a skill without a failing test first.
Name the assertion you added to agy-agents/scripts/selftest and say what it
proved. If it passed before your change, it is not testing what you think.

If this genuinely cannot be tested (a typo, a README wording change), say so
here instead — that is a fine answer, it just needs saying out loud.
-->

- Assertion added:
- It failed before the change because:

## Checklist

- [ ] `bash agy-agents/scripts/selftest` is green locally
- [ ] Comments explain *why*, not what — especially any non-obvious constraint
- [ ] Any `.ps1` touched is still ASCII-only
- [ ] No `description:` field summarises a skill's workflow (triggers only)
