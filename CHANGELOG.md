# Changelog

Notable changes to the skills in this repository. Each skill carries its own
`version:` in its `SKILL.md` frontmatter.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## brand-media-kit

### [1.0.0] — 2026-08-19

First release. A banner set for a family of products, where the consistency is
structural rather than a matter of care.

#### Added
- **One art master per product**, 16:9, from a locked style prompt. `STYLE` in
  `bmk/generate.py` is a constant, not a template: every prompt is those exact
  bytes plus one subject clause, because a style assembled per product drifts
  per product. Two routes to the same prompt — the API when a key is present,
  and a generated `PROMPTS.md` when it is not, since a consumer Gemini
  subscription does not include API access and should not mean a different
  prompt.
- **All typography composited in code.** The model is asked for a quiet left
  45%; `bmk/composite.py` draws the title and tagline into it at fixed sizes,
  tracking and position. Fitting shrinks and never grows — a two-word product
  name set larger than a five-word one to fill the space is the exact drift this
  kit removes. Pillow has no letterspacing, so `draw_tracked` paints glyph by
  glyph, and `layout.measure` counts those n-1 gaps so a line that measures as
  fitting also draws as fitting.
- **Geometry in 1376-unit reference space**, scaled to whatever master it is
  handed. The master is 1920 x 1080 because `hero` is 1920 wide and nothing is
  ever upscaled; the card-sized master everyone reaches for first is rejected
  with the format that could not be cut from it.
- **Five formats, all centred crops of the one master**: `card` 1376x768,
  `header` 1376x400, `hero` 1920x480, `wporg-banner` 1544x500,
  `wporg-banner-sm` 772x250. `subject_band_pct` `[28, 72]` is derived from the
  widest of them — the slice every crop is guaranteed to keep.
- **WebP under a byte budget**, quality descending until it fits, then copied
  into every target as `<slug>-<format>.webp`. Every target holds every
  product's media, because the card grid on any one product's screen shows the
  whole range — which is why the slug is in the filename rather than only in
  the directory.
- **Five stages that are commands, not just modules.** `python bmk/<stage>.py`,
  each taking optional slugs and `--project DIR`; without it they find the
  nearest `.brandkit/` above the working directory, the way git finds `.git`.
  `bmk/project.py` holds the paths all five need, so an operator states them
  once rather than five times.
- **`bmk/verify.py`, which imports no other module in the kit.** Missing files,
  missing target directories, wrong dimensions, over budget, unreadable, copies
  that differ between targets, two different assets that are byte-identical. It
  fails when handed an empty expected set or no roots: a fence that reports
  clean because it was given nothing is worse than no fence, because it is
  trusted.
- `scripts/install` — scaffolds `.brandkit/` from the example configs, refuses
  to clobber without `--force`, `--dry-run` to see what it would write.
- `scripts/selftest` — the full suite, offline, against a vendored test font.
  It picks the first interpreter on PATH that can import both Pillow and pytest
  rather than the first named `python3`, which on Windows is often a Store stub
  with neither.
- `reference/config-schema.md`, `reference/layout-grid.md`,
  `reference/prompt-recipe.md`, `reference/manual-handoff.md`.

#### Known limitations
- **Adopting an existing set means agreeing on filenames.** The kit deploys
  `<slug>-<format>.webp`. A project that already loads `<slug>.webp` has to
  either update those references or narrow the format list — decide before
  generating, not after, because the choice is cheap up front and a rename
  across a dozen repositories is not.
- **Every format is a wide crop of a 16:9 master.** A square or portrait format
  cannot come from this pipeline: cropping 1:1 out of 16:9 keeps only the middle
  56% of the width, and the lockup lives in the left 45%, so the type would be
  cut in half. A square asset needs its own layout, not another entry in the
  format table.
- **Fonts are not shipped.** `brand.json` names files that must exist in
  `.brandkit/fonts/`, and `bmk/fonts.py` raises rather than substituting
  Pillow's bitmap default — a silent fallback measures the wrong thing and the
  whole set comes out subtly wrong.
- **The no-lettering check is human.** Before saving a master, look at it and
  reject it if it contains any lettering. OCR was the obvious automation and was
  rejected twice over: a cloud vision call breaks the rule that the selftest is
  offline and spends no quota, and a local Tesseract would skip itself on every
  machine without the binary — a check that disables itself quietly is worse
  than a documented one that does not. `verify` checks bytes and sizes; it
  cannot read.

## agy-agents

### [1.8.1] — 2026-08-14

Three reports from one day of field use. The first is the mirror of the flaw
fixed in 1.7.x, where a guard path that was not on disk fingerprinted nothing
and the fence reported clean: this time the control does not silently pass, it
confidently fails — against the wrong target. The other two are both the
reviewer being told, in one way or another, what to conclude before it looked.

#### Fixed
- **`tripwire verify` compares the baseline's surface set against the config
  before judging anything.** It used to walk the *current* config's surfaces
  and never look at what the baseline actually held, which was wrong in both
  directions at once. A surface the baseline never recorded loaded as an empty
  "before", so every file under it was reported `added` — a fully populated
  VIOLATION report, exit 1, for a tree in which nothing had moved, naming the
  source bundle among the casualties. And a surface the baseline *did* record
  but the config no longer lists was never visited at all, so a file tampered
  with under it was reported `clean`, exit 0.

  The two harnesses in that repo name their baselines differently — ours after
  the guarded **path** (`src/styles` → `src-styles.fp`), theirs after the
  surface (`tokens.fp`) — so verifying one fence with the other runner was
  enough to produce the first. A config edited between arming and verifying is
  enough to produce the second.

  A mismatched pair now prints `BASELINE DOES NOT MATCH THIS CONFIG`, names
  the surfaces on each side, and **exits 2, not 1**. This is the same ruling
  as a guard path that is not on disk: a config fault, not drift. The exit
  code is what tells a controller which thing to go and look at, so the two
  must not share one.

- **The verdict block's `fence` line has three outcomes rather than two.**
  `COULD NOT JUDGE — the baseline does not match this config` sends the reader
  to the config; `VIOLATED` sends them to the implementer's diff. Collapsing
  them meant a run that touched nothing could read as a compromised one.
  Neither is a pass: both still exit 4.

- **The reviewer grades acceptance criteria as claims to falsify, not as work
  to summarise.** Reported often enough to stop being a per-brief problem: left
  to itself, an implementer fills that table in as a report of what it did.
  Every row restates the action taken, so a row reads ✅ because the work
  happened rather than because the criterion holds — and the reviewer, handed a
  completed table, confirms it. The contract now tells the reviewer to take each
  criterion and try to break it: name the input or state under which it would
  fail, then check whether the code survives. A criterion nobody attempted to
  falsify is not satisfied, it is **unverified**, and it is reported ❌. This is
  the rule the rest of the harness already runs on, applied where it was
  missing: an absent measurement is never a pass. It lives in the reviewer
  contract now, so it stops having to be written into every brief by hand.

- **The pre-judging ban names the phrasings that actually get written.** It
  listed "do not flag", "at most Minor" and "the plan chose" — the shapes a
  controller writes deliberately. The one that gets written by accident looks
  like helpful context about behaviour that was preserved on purpose: *"these
  are NOT a defect — flag only if undocumented."* That is a verdict the
  controller reached before the reviewer looked, and a conditional licence to
  flag is still a verdict. Both phrasings are now in the list.

### [1.8.0] — 2026-08-13

Two reports from a project three milestones past its install date. Both are the
same shape: a number that was true once, or a line that describes the session
rather than the work, sitting where a controller reads it as fact.

#### Fixed
- **The project skill no longer pins the milestone.** Its bindings table was
  rendered at install time and still read `.agy/work/m5` three milestones later.
  Every script had been reading the real path out of `.agy/config` the whole
  time; only the one document meant to be authoritative about where the ledger
  lives was reading a memory of it. The workspace, the ledger and the shared
  context are now resolved from the config at the top of a session, and the
  table names the config instead of copying it.
- **`--milestone` moves an installed project.** It used to be ignored outright
  whenever any workspace was already on disk, and a config that exists is kept,
  so `--milestone m6` scaffolded `.agy/work/m6/` and left `AGY_WORKSPACE`
  pointing at m5 — a new workspace that nothing wrote to. It now repoints that
  one line and leaves the rest of the config alone (`--force` was never an
  acceptable way to advance a milestone: it takes the gates with it). A config
  whose binding the rewrite cannot find reports `COULD NOT REPOINT` and counts
  as a problem, rather than claiming a move it did not make. The installer also
  prints the `cp` that carries the shared context to the new milestone.
- **The workspace resolution order is written down and enforced:**
  `--workspace`/`--milestone`, then `.agy/config`, then a scan of the disk
  (newest ledger first), then `.agy/work/m1`. The config outranks the scan
  because a project past its first milestone has several `progress.md` on disk
  and only the config knows which is current — the old glob would rebind an
  established repo to whichever milestone sorted first.
- **The `{{date}} — {{ruling}}` placeholder in "Local rulings" is gone.** Its
  markers were lowercase, so the installer never substituted them and the one
  section designed to survive a `/clear` shipped as a literal template line that
  nobody wrote in. The selftest now asserts the installed project skill contains
  no unrendered marker at all, and names no milestone workspace.

#### Added
- **`landed` in the verdict block.** Every other line grades how the session
  behaved, and a run that produced no code behaves impeccably: clean run, clean
  fence, green gates, a confident report. The tree was the only thing that told
  the two apart and nothing measured it. Now: `N commit(s) — <subject>`,
  `NOT COMMITTED — N change(s) outside the workspace, 0 commits`, or `NOTHING`.
  The workspace is excluded for the same reason the fence prunes it — every run
  writes a report there, and counting it would make every run look productive.

- **Work left uncommitted fails the dispatch.** Reported twice on consecutive
  runs: the implementer wrote the code, committed none of it, the harness
  printed `SUCCESS`, and the controller committed by hand both times. That is
  not a judgement call the harness has to duck — the brief's own definition of
  done names the commit, so a tree full of changes against an empty history is
  an unfinished task, and the next dispatch would start on top of it carrying
  work no ledger entry explains. `NOTHING` still only reports, because an
  investigation task legitimately produces no code — and that case leaves
  nothing outside the workspace, so it never reaches the failing branch. The
  brief template now says the commit is part of the task rather than cleanup
  after it.

- **The reviewer now grades the brief before the diff.** Two rounds running, the
  most valuable finding was against the brief rather than the implementation —
  and the contract had no place to put it. A brief whose stated invariants do
  not follow from its stated rules produces an implementer that complies
  exactly, a reviewer that confirms compliance, green gates and a clean fence:
  every check passes and the defect sits in the specification everything else
  was graded against. The controller wrote the brief, so the controller cannot
  be the agent that catches it. Brief integrity is now the first of three
  demanded verdicts, and a finding there is adjudicated by the controller and
  recorded as a ruling rather than sent to the implementer as a fix. The three
  verdicts are printed into the review package itself, not just documented in
  `reference/protocol.md`: the package is the one file the reviewer subagent is
  guaranteed to open, and a contract it never reads is a contract it never has.

- **A refusal prints a verdict block.** Reported as "the missing-brief path exits
  0"; it exits 2, and has since the first release. What made it look like a
  success was the pipe: `.agy/dispatch 3 | tee run.log` returns tee's `0`, and a
  backgrounded wrapper reports whether it managed to start the job. The status
  is the half of the signal the caller can lose, so it can no longer be the only
  half — every pre-run refusal now prints the same block a finished run prints,
  headed `run  DID NOT RUN — <reason>` and carrying its own exit code as text.
  A reader that only sees the output reaches the same conclusion as a caller
  that reads `$?`.

#### Changed
- **`turns` is on its own line, labelled as agy's own count.** Runs reporting
  `1 turns` have carried two dozen recorded tool calls; printed beside the
  durations it read as a one-shot answer. The tool line now leads with the total
  the harness counted off the event stream, which is the number that was
  measured rather than reported.

### [1.7.0] — 2026-08-12

One flaw, reported by a harness on its third crashed run in a row: a run that
did the work, committed it and wrote a 303-line report, then died at 2711s with
`timeout waiting for response` and no result event — and was graded **PROBLEMS**
beside a clean fence, green gates and a correct diff. The harness had no way to
say *the work landed, the session died*.

#### Fixed
- **Deferral keys on the missing result event, not on who did the killing.** The
  watchdog was only ever one route to a run with no `result`: agy also dies on
  its own — its `--print-timeout` expiring, an internal error, a dropped
  connection — and when it does the stream was still moving, so the watchdog
  never fires. The old condition (`killed && !resultEvent`) covered our kill
  only, so a self-inflicted death was judged on its status, its empty response
  and its exit code. All three describe how the session ended. None is evidence
  about the work. Nothing else is relaxed: a denial, a tool error, zero tool
  calls or a report that is missing or stale still fails a stopped run.
- **The verdict can say it.** `run  clean, but the SESSION DIED before its
  result event` — the counterpart to the existing `WATCHDOG-KILLED` line. A
  harness whose only word for this is `PROBLEMS` trains its reader to discount
  `PROBLEMS`, which is the one word that has to keep meaning something.
- **The tool tally is labelled a floor when the stream was cut off.** A stream
  that ends mid-run tallies only what it recorded, and presenting that as a run
  summary reads as proof the implementer wrote nothing — next to a commit that
  is on disk. The reported run showed no write tools at all and made a landed
  commit look like it had appeared from nowhere.
- **Quota classification now keys on the watchdog rather than on deferral**, so
  broadening deferral did not quietly close the fallback route. A run *we* killed
  is still never classified — that is what stops a hang from spending the reserve
  group — but a session that died on its own is, because a genuine weekly
  exhaustion is one of the ways a run ends without a result event.

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
