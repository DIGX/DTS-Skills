# Contributing

Thanks for looking. Issues and pull requests are both welcome.

## The one firm rule

**No change to a skill without a failing test first.**

This is [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
applied to agent instructions, and it applies to documentation edits too — not
just code. It exists because this repo's entire subject is *failures that look
like successes*. A harness that judges other agents has to be judged the same
way, or it becomes one more thing that reports clean while guarding nothing.

The cycle:

1. **RED** — add an assertion to `agy-agents/scripts/selftest` that fails
   because of the bug or gap you are fixing. Run the suite and *watch it fail*.
   If it passes before your change, it is not testing what you think.
2. **GREEN** — make the smallest change that turns it green.
3. **REFACTOR** — tidy, re-run, keep it green.

This is not ceremony. Two real examples from this repo's own history:

- A fingerprinter piped into `xargs sha256`, where `sha256` was a *shell
  function*. `xargs` can only exec real programs, so every surface hashed
  nothing — and the fence reported **clean**. Only the "no surface may be
  empty" assertion caught it.
- A test that stripped gate *calls* with `grep -v '^gate'` also stripped the
  `gate()` *definitions*, leaving orphaned function bodies. The runner exited 1
  from a bash syntax error, so the assertion "a runner with no gates fails"
  had been **passing for entirely the wrong reason**.

Both are exactly the class of bug the project exists to prevent, and both were
found by the test suite rather than by review.

## Running the tests

```bash
bash agy-agents/scripts/selftest
```

It builds a throwaway repository in a temp directory, stubs `agy`, and
exercises the harness end to end. It **spends no quota**, touches nothing
outside its temp dir, and aborts rather than run if `agy` resolves to the real
CLI — that guard exists because getting it wrong once cost ~148k tokens of live
quota.

CI runs the same suite on Ubuntu and Windows for every push and pull request.

## Writing skill documentation

Two constraints that are easy to get wrong:

**The `description:` field states *when to use the skill*, never what it
does.** Agents read descriptions to decide what to load, and a description that
summarises the workflow becomes a shortcut they take *instead of* reading the
body. Start with "Use when…" and list triggering conditions and symptoms only.

**Match the form to the failure.** A rule someone skips under pressure needs a
prohibition and a rationalization table. Output of the wrong *shape* needs a
positive recipe — stating what the output is, in order — because prohibitions
invite negotiation and measurably backfire there. A missing element in
something already being produced needs a required slot in the template, not a
prose reminder nearby.

## Style

- Bash, POSIX-ish, `set -uo pipefail`. Tabs for indentation, matching what's
  there.
- **Comments explain why, not what** — especially the non-obvious constraint
  that made the code look the way it does. Most comments in this repo are a
  record of something that went wrong; keep that.
- Keep every `.ps1` **ASCII-only**. Windows PowerShell 5.1 reads a `.ps1` in
  the system codepage without a UTF-8 BOM, and a single em dash takes the
  parser down with an error pointing nowhere near the real fault.
- Shell scripts are pinned to LF in `.gitattributes`. Do not override it — a
  CRLF shebang fails on Linux with `bad interpreter: /usr/bin/env bash^M`.

## Reporting a quota-exhaustion string

The fallback classifier is written against the vocabulary these errors normally
use, not against a captured Antigravity exhaustion event — there was no real
sample to match when it was written. **If you hit a genuine weekly or 5-hour
wall, the raw text in your log is the most useful thing you can contribute.**
Open an issue with it and the classifier gets corrected once, for everyone,
instead of guessed at.

## Pull requests

- One logical change per PR.
- Say what failing test you added and what it proved.
- If you changed anything under `agy-agents/assets/`, confirm the selftest is
  green locally as well as in CI.
