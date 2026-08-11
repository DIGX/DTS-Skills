# Changelog

Notable changes to the skills in this repository. Each skill carries its own
`version:` in its `SKILL.md` frontmatter.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### agy-agents

#### Added
- **Fourth trap: `permissions.deny` matches the literal command string**, so
  `cmd /c npm install` defeats a `npm install` denial. With trap 3 this makes
  the CLI's permission system unusable as a boundary in both directions —
  `allow` fails closed, `deny` fails open. No behaviour change: the harness
  already skipped it and fenced with `.agy/tripwire` instead.

#### Fixed
- `dispatch-traps.md` claimed there was "no separate effort flag" for the Gemini
  IDs. `agy --help` lists `--effort (low|medium|high)`, and `.agy/dispatch` has
  always passed it on every model. Corrected, with a note to keep the ID suffix
  and `AGY_EFFORT` consistent since the precedence between them is unpinned.

## agy-agents

### [1.1.0] — 2026-08-12

First public release.

#### Added
- `reference/setup.md` — installing and authenticating the Antigravity CLI,
  the headless smoke test that proves a run really touches your repository,
  the two Windows performance/encoding rules, and how to prove the fence fires
  before trusting it.
- `setup` route in `SKILL.md`, and an explicit prerequisites block.
- Selftest coverage for the adoption path: no generated file may name a gate
  runner the installer did not write, the dispatch template must name the
  adopted runner, and adoption must not write a competing `.agy/gates`.

#### Fixed
- **Adoption pointed the implementer at a gate runner that did not exist.**
  `task-dispatch.md` and `dispatch-context.md` hardcoded `.agy/gates` instead
  of substituting `{{GATES}}`, so any repository that adopted its own existing
  runner got a dispatch template naming a path the installer never created.
  The run would have been graded against a missing command.
- **`.agy/config` promised an environment it could not deliver under
  adoption.** Only a *generated* `.agy/gates` sources the config; an adopted
  runner is the project's own script and does not. Exports still reach it
  through the dispatch's environment, but not on a bare run — which is exactly
  when a missing PATH entry looks like a real gate failure. The generated
  config now says so, and names the adopted runner.
- Removed hardcoded assertion counts from the documentation, which went stale
  the first time an assertion was added.

### [1.0.0] — 2026-08-12

Initial build, extracted from a working single-project harness.

#### Added
- `.agy/dispatch` — the only sanctioned way to call `agy`. Handles the three
  traps that make a broken run report `SUCCESS` with exit 0, parses the nested
  NDJSON event shape (the published flat shape does not match the wire), and
  judges the run itself rather than reading `$?`.
- `.agy/tripwire` — an integrity fence under your control, since
  `permissions.allow` is silently ignored under `--print`. Content hashes for
  small surfaces, size+mtime fingerprints for large external trees. Refuses to
  arm when any required surface comes back empty.
- `.agy/gates` — verification suite run by the harness. No gates configured is
  a hard failure, not a pass.
- `.agy/review-pkg` — single-file review package from a diff range.
- Reserve-quota policy: fall back to the Claude/GPT group only on a clear
  *weekly* Gemini exhaustion; hold through a 5-hour window; hold and print the
  raw text on a quota-shaped error that names no bucket.
- `scripts/install` — idempotent installer that adopts an existing SDD
  workspace and gate runner rather than duplicating them.
- `scripts/selftest` — full harness exercise against a stubbed `agy`, spending
  no quota, aborting rather than run if `agy` resolves to the real CLI.
- `reference/protocol.md`, `reference/dispatch-traps.md`,
  `reference/install.md`.
