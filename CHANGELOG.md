# Changelog

Notable changes to the skills in this repository. Each skill carries its own
`version:` in its `SKILL.md` frontmatter.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## agy-agents

### [1.6.0] — 2026-08-12

From a backlog of flaws reported by two harnesses running this skill on real
projects. Three of the six were already fixed here and stale only in the
installed copy; the rest share one shape — **a check that exists but can be
walked around by something ordinary**: a space in a path, a template nobody
filled, a `PATH` entry the shell quietly ignores.

#### Added
- **A guarded path that is not on disk makes the fence refuse to arm** — dir,
  file or tree, whether or not it is named in `AGY_REQUIRE`. Nobody configures
  a guard for a directory they do not have, so absence is always a config
  error. This is what makes the space-split guard list *loud*: the fragments do
  not exist, so instead of fingerprinting nothing and reporting `clean`, the
  fence stops. The reported case was
  `AGY_GUARD_TREE=NevaraFlow Suite app shell-handoff/` — the project's primary
  guarded surface, silently unguarded, reporting clean on every run.
- **`.agy/dispatch` refuses to run against an unfilled brief.** The installer
  writes `dispatch-context.md` from a stub full of `{{markers}}` and cannot
  fill them — only the controller knows what goes in. Nothing checked that
  anyone had, and that file is read by *every* implementer and *every*
  reviewer: told the language floor is `{{Language/runtime floor}}`, they read
  no floor at all, and a gate cannot enforce a rule that was never written
  down. The task's own brief is checked the same way. `AGY_ALLOW_UNFILLED=1`
  overrides it for text that genuinely needs `{{...}}`.
- **The installer reports both in its own checks**, so the first dispatch is
  not the messenger — unfilled context lines, and a Windows-form `PATH` entry
  on MSYS.
- **`.agy/dispatch` prints the `agy` binary that resolved.** Git Bash accepts a
  `C:\...` `PATH` entry and then never searches it, so an exported stub can be
  skipped in silence and the real, quota-spending CLI answers instead. That
  happened during a watchdog drill and re-dispatched a completed brief. An
  absolute path on screen cannot be misread. Documented in `setup.md`.

#### Fixed
- **The installer writes guard lists one path per line**, the form the tripwire
  splits on newlines, rather than teaching the whitespace-separated shape that
  cannot express a path with a space in it. `$HOME` alone is enough to hit this
  on Windows (`C:\Users\Firstname Lastname`).
- **`hash_surface` no longer swallows its fingerprinter's exit code.** A bare
  `return 0` discarded every failure the surfaces report, including the
  PowerShell tree walk exiting 4, leaving the empty-surface check as the only
  thing between a broken fingerprinter and the word `clean`.
- **The verdict block names the log the work actually landed in.** The header
  prints its log path before any attempt runs, so on a quota fallback it
  advertised the attempt that hit the wall while the reserve attempt wrote to
  `<base>.reserve.*`. A reader following the advertised path opens a failed run
  and grades its artefacts as the work — this harness's own failure family,
  reintroduced by the harness. `LOG_BASE` now tracks which attempt produced the
  work and the verdict block prints it; the header's copy stays, provisional.

### [1.5.0] — 2026-08-12

From a run where the implementer's fault-injection output was hand-trimmed to
drop the main suite that had already run. Nothing was fabricated and every
count was real. The gate passed, the fence was clean, the run reported
`SUCCESS` — none of those can see inside a report. It surfaced only because the
reviewer re-ran the script itself.

#### Added
- **The reviewer re-executes pasted proof rather than reading it.** Pasted
  output is a claim shaped like evidence: a suite quietly reduced to the cases
  that pass leaves every number in the block true and the block itself a lie
  about what ran. The gate suite is the stated exception — `.agy/dispatch`
  runs it and keeps its own copy at `<log>.gates.log`, so it is already
  independently evidenced and the claims check already compares against it.
  Every *other* cited command has no such capture. This replaces the old "do
  not ask it to re-run gates the report already evidences", which was true of
  gates and quietly wrong about everything else.
- **Implementers must name the exact command line above any pasted block, and
  paste it whole.** Stated so the reviewer's re-run is possible at all: proof
  you cannot reproduce the invocation for is not proof.
- **The harness fails a report missing a required section.** `## Observations`
  was required by the contract and enforced by nothing. An absent section reads
  identically whether there was nothing to observe or the implementer never
  looked. Sections come from `AGY_REPORT_SECTIONS` (default `## Observations`);
  `None.` is a valid body. This is a gate, not a warning, because unlike the
  claims comparison it is deterministic — a heading is present or it is not.

  Known limit: it only checks a report this run actually wrote. A run that
  writes no report at all is still caught only on the deferred path.

### [1.4.0] — 2026-08-12

#### Added
- **A reviewer that cannot run now has a state to park the task in: `HELD`.**
  The protocol said the reviewer must be a fresh subagent and said nothing
  about the subagent being unavailable, which left the controller one cheap
  move — read the diff itself and call it reviewed. That removes the only
  independent check in the loop and, worse, leaves a ledger recording a review
  that never happened. A held task stays open, is recorded as reviewed by
  nobody with the reason, and its only exit is a reviewer becoming available.
  Written as a state rather than a bare prohibition on purpose: a prohibition
  with no exit is a deadlock, and a deadlock is what gets negotiated away
  under pressure.

#### Fixed
- **"When what remains is mechanical, finish it yourself" read as licence to
  produce a verdict.** It was written for a reviewer that died mid-write-up
  after reaching its verdicts. Now says so, adds that a killed subagent can be
  resumed from its own transcript, and states that producing a verdict is
  never mechanical however obvious the diff looks.

### [1.3.0] — 2026-08-12

Both additions come from a real run in another project that reported success,
committed, and was wrong on both counts — a denied `npm install` that ran as
`cmd /c npm install`, and a report claiming a test count the gates contradicted.
Neither was visible in the verdict block at the time.

#### Added
- **Denial-then-success pairs are named as a `BYPASS`.** A denial was already a
  hard failure, so a run like that would have failed anyway — but it failed as
  "one call was blocked", which reads as an *incomplete* run. The fact that
  matters is the next line in the stream: the same command completed under
  another name. That makes the run *compromised* rather than incomplete, and
  every claim in its report unverified, because the work really did happen —
  outside the boundary. The dispatcher now normalises both sides (unwrapping
  `cmd /c`, `sh -c`, `powershell -Command`, `npx`, `sudo`, absolute paths and
  quoting, nested up to four deep) and pairs them on the first two tokens of
  intent. This required collecting successful command strings, which the parser
  previously read and discarded.
- **Report numbers are checked against the gate output.** Where the report and
  the gates name the same quantity, the measurement wins. Deliberately narrow:
  only a unit appearing on *both* sides is ever compared, since the gates cannot
  contradict a number they never measured. It is a **warning, not a gate** — it
  does not change the exit code — because the comparison is heuristic and a
  checker that invents disagreements teaches the controller to ignore it. It is
  still the only signal that catches a report describing work it did not do, so
  `reference/protocol.md` says not to accept a task while it is showing.
- Report freshness is now computed on every run rather than only a deferred one.
  Only the deferred path still *fails* on it; the claims check uses it to avoid
  measuring a report an earlier dispatch left behind.
- Selftest coverage for both, plus the missing assertion that a red gate fails
  the dispatch — a property nothing had pinned, and one this release's gate
  output capture touches.

#### Changed
- The gate runner's output is teed to `<log>.gates.log` so it can be compared
  against the report. Status is read from `PIPESTATUS[0]` rather than the
  pipeline's, so a `tee` failure cannot fake a red gate.

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
