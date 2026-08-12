# Changelog

Notable changes to the skills in this repository. Each skill carries its own
`version:` in its `SKILL.md` frontmatter.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## agy-agents

### [1.2.0] — 2026-08-12

Merges harness work done in a second project with documentation fixes made
here. Neither side was a superset of the other, which is the whole argument for
this repository existing.

#### Added
- **Trap 4: a finished run can hang forever without emitting its `result`.**
  `agy` can do the work, write the report, commit — then sit in an internal
  `manage_task`/`schedule` loop until `--print-timeout` expires 45 minutes
  later, with no error and the process alive. The only tell is that the event
  stream stops growing. `.agy/dispatch` now watchdogs the stream
  (`AGY_IDLE_TIMEOUT`, default 300s) and, on a kill with no result event,
  *defers* rather than fails: status, response and exit code are not judged,
  but a denial, a tool error or zero tool calls still fail the run, and the
  report must be newer than the dispatch that asked for it. A deferred run is
  never quota-classified, so a hang cannot open the reserve bucket.
- **Trap 5: `permissions.deny` matches the literal command string**, so
  `cmd /c npm install` defeats a `npm install` denial. With trap 3 this makes
  the CLI's permission system unusable as a boundary in both directions —
  `allow` fails closed, `deny` fails open. No behaviour change: the harness
  already skipped it and fenced with `.agy/tripwire` instead.
- **`.agy/tripwire` handles guard paths containing spaces.** A list written one
  path per line is split on newlines instead of whitespace, and each list is
  split independently. Previously `Acme Suite/app` fractured into several
  nonexistent surfaces, each hashing to nothing — a fence guarding nothing,
  reporting clean.
- Selftest coverage for the watchdog: that a hung run is killed rather than
  waited out, that its empty response and exit code are *not* held against it,
  that a missing report fails it, that a report left by an earlier dispatch
  fails it, and that a hang never burns the reserve group. Verified by
  disabling the watchdog and watching them go red.

- `agy-agents/README.md` — full documentation of the five CLI traps, the two
  harness traps, the `.agy/` machinery, installation, adoption, configuration
  and the task cycle.

#### Changed
- The selftest exports `AGY_IDLE_POLL=1`. The shipped 15s default cannot notice
  a stubbed run has exited any sooner, which added ~15s to every dispatch in the
  suite. Runtime went from ~3m to ~1m36s while gaining 11 assertions.

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
