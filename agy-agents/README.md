# `agy-agents`

**Claude plans, adjudicates and verifies. The Antigravity CLI implements. A
fresh Claude subagent reviews.**

A Claude Code skill that deploys the *Claude Manager + Implementer* protocol
into a repository, so implementation work can be delegated to Google's
Antigravity CLI (`agy`, running Gemini) **and still be checkable afterwards**.

Delegating implementation to a second model is easy. Knowing whether it
actually did the work is not — and that is the entire problem this skill exists
to solve.

```
/agy-agents          # in Claude Code, from the repo you want set up
```

---

## Table of contents

- [Why this exists](#why-this-exists)
- [The five CLI traps](#the-five-cli-traps)
- [The three harness traps](#the-three-harness-traps)
- [The `.agy/` machinery](#the-agy-machinery)
- [Installing](#installing)
- [Configuration](#configuration)
- [Running a task](#running-a-task)
- [Reading a verdict block](#reading-a-verdict-block)
- [Quota and the reserve policy](#quota-and-the-reserve-policy)
- [Verifying the harness itself](#verifying-the-harness-itself)
- [Debugging a run](#debugging-a-run)
- [Layout of this skill](#layout-of-this-skill)
- [Caveats](#caveats)

---

## Why this exists

An implementer that reports success, a fingerprinter that hashed zero files,
and a gate suite with no gates in it **all look identical to a clean run from
the outside**. Every script installed by this skill exists to make one of those
distinguishable from the others.

The failure mode is not "the model wrote bad code" — review catches that. The
failure mode is *the run did nothing at all and told you it succeeded*, which
no amount of code review catches, because there is no code to review.

Verified against **Antigravity CLI v1.1.12**. None of what follows came from
documentation; all of it came out of probes, and in one case the published
event-shape docs did not match the wire.

---

## The five CLI traps

They share one property: **the failure is invisible from the outside.**

Traps 1–3 make a completely broken run report `SUCCESS` with exit code `0`.
Trap 4 makes a *finished* run look like a hung one for 45 minutes. Trap 5 makes
a fence you believe you have fail open silently.

Full detail, with the probe transcripts: [`reference/dispatch-traps.md`](reference/dispatch-traps.md).

### 1. `--add-dir` is not optional — the scratch-workspace trap

`agy`'s default CLI project has no resources attached (`projectResources` is
`{}`), so a headless run is handed a scratch workspace under
`~/.gemini/antigravity-cli/scratch`. Every path in your prompt resolves to
nothing.

The lie is that **the `init` event still reports your real cwd**, so the
transcript looks correct to anyone reading the log. An early probe reported
`not a git repository`, `php is not recognized` and `scripts/gates: No such
file` — while `status` read `SUCCESS`.

> **Answer:** `.agy/dispatch` always passes `--add-dir <native path>`. On
> Windows this must be the Windows-form path, not the MSYS one — the dispatcher
> converts it via `cygpath` with a fallback.

### 2. The exit code proves nothing

A tool call the CLI is not permitted to make is **soft-denied**: the run
continues, the process exits `0`, `status` still reads `SUCCESS`, and the only
trace is a notice on stderr. A probe whose every single command was blocked
exited `0`, status `SUCCESS`, with an empty response.

This is the trap that breaks CI. GitHub Actions, Jenkins and every shell script
ever written branch on `$?`, and `$?` is green on a run where nothing executed.

> **Answer:** `.agy/dispatch` parses the NDJSON event stream and judges the run
> itself — tool calls made, tools denied, whether a response was produced —
> instead of reading `$?`.

### 3. The permission system is inverted under `--print`

`permissions.allow` is honoured interactively and **silently ignored** in
headless mode. Every command you explicitly allowed is denied, and the run does
not tell you.

A fence that blocks the work and permits the lie is worse than no fence. So the
harness stops using the CLI's fence entirely: it runs with
`--dangerously-skip-permissions` and puts a fence **it** controls around the run
instead — `.agy/tripwire`.

> **The flag lives inside `.agy/dispatch`, never in a bare command**, so it
> cannot be used without the fence attached. If the fence will not arm, the
> dispatch refuses to start (exit `3`). Do not work around this.

### 4. A finished run can hang forever without emitting its result

`agy` can do the work, write the report, make the commit — and then never emit
its `result` event, trapped in an internal `manage_task`/`schedule` loop. No
error, no stderr, process still alive. It sits there until `--print-timeout`
expires 45 minutes later.

Observed on a run whose work was complete and committed **two minutes in**: the
last event was a schedule call asking to be woken in 20 seconds, and the stream
was still silent 16 minutes later.

Nothing about the process distinguishes this from slow work. The one tell is
that **the event stream stops growing**.

> **Answer:** a watchdog. If the stream is silent for `AGY_IDLE_TIMEOUT`
> (default 300s — about six times the longest gap seen on a healthy run),
> `.agy/dispatch` kills `agy` and falls through to judging the evidence on disk.

```
WATCHDOG  event stream silent for 300s - killing agy (pid 12345).
WATCHDOG  the verdict now rests on the fence, the gates and the report.
```

The same `schedule` call has a second failure mode, and it is the one the
watchdog cannot see: the run wakes, finds its task unfinished, and re-arms. The
stream keeps growing, so nothing reads as idle, and the wrapper waits on a
process that will never exit — the fence, the gates and the verdict never print.
`AGY_MAX_WALL` (default 2700s) caps total elapsed time regardless of what the
stream is doing, and reports `WALL-CAPPED` rather than `WATCHDOG-KILLED`,
because "it went quiet" and "it would not stop" are different problems.

The watchdog catches the silent form. The **chatty** form emits events the whole
time it is stuck, so the stream keeps growing, the watchdog never fires, and the
run dies of agy's own `--print-timeout` with `timeout waiting for response` —
observed at 2711s wall against 364s of thread time, on a run that had already
committed and written a 303-line report.

Both end with **no `result` event**, and that, rather than who did the killing,
is what the harness keys on:

```
  run     clean, but the SESSION DIED before its result event (agy failure 4)
```

A run with no `result` event is **deferred**, not failed: it was stopped, so
status, response and exit code describe *how it ended* rather than whether the
work was done, and are not judged. Nothing else is relaxed — a denial, a tool
error or zero tool calls still fail a deferred run, because each is recorded in
the stream and is evidence of what actually happened. The tool tally is printed
as a **floor**, since a stream that ends mid-run recorded only part of it.

What replaces the missing `result` is a **report freshness check**: the report
must exist *and* be newer than the moment this dispatch started. A stale report
from an earlier dispatch would otherwise sail through on a clean fence and green
gates — which is the exact shape of a run that did nothing.

Stream size, not mtime, is what the watchdog measures: the stream is append-only
so size is monotone, and one-second mtime granularity makes short gaps
unreadable.

### 5. `permissions.deny` matches the literal command string

A `deny` rule is compared against the command text as written, not against the
program the command ends up running. So a wrapper defeats it:

```
deny: "npm install"

npm install              → denied
cmd /c npm install       → allowed, and runs npm install
```

Anything that re-quotes the command has the same effect — a shell wrapper, an
`npx` indirection, an absolute path instead of a bare name. You cannot enumerate
the variants faster than a model can produce one by accident.

Together with trap 3 this settles the question: **`agy`'s permission system is
not a security boundary, in either direction.** `allow` fails closed where you
wanted it open; `deny` fails open where you wanted it closed. The harness
therefore skips it and derives its safety from `.agy/tripwire`, which checks the
filesystem *after the fact* rather than trying to predict a command.

### Event stream shape

The documented flat shape is wrong. Real `--output-format stream-json` events
are **nested** under a key matching `event`:

```json
{"event":"init","init":{"model":"gemini-3.7-flash-high","cwd":"..."}}
{"event":"step_update","step_update":{"step_type":"tool","state":"DONE","tool_name":"..."}}
{"event":"result","result":{"status":"SUCCESS","response":"...","num_turns":2}}
```

A parser written against the documented flat shape sees **no events at all** and
reports a clean, empty run. This is a sixth false-positive hiding inside the
first five.

---

## The three harness traps

These come from the verification harness rather than from the CLI, and they are
the reason the scripts here refuse to run rather than pass.

**An empty fingerprint reports clean.** If a guard pattern matches zero files —
a typo'd path, a directory that moved, a path containing a space that split into
two nonexistent ones — the differ compares nothing against nothing and prints
`clean`. You believe you have a fence; you have a decoration.

**An empty gate suite reports green.** A runner that executed zero gates exits
`0`. Every downstream check that trusts it is now trusting nothing.

**An unfilled brief reads as no constraint.** The installer writes
`dispatch-context.md` from a stub full of `{{markers}}` and cannot fill them —
only you know what goes in. That file is read by *every* implementer and *every*
reviewer, so one left unfilled is inherited by all of them: told the language
floor is `{{Language/runtime floor}}`, they read no floor. Nothing in a gate can
enforce a rule that was never written down, so the run passes everything.

All three are handled by refusing to proceed:

- `AGY_REQUIRE` lists the surfaces that must fingerprint a non-zero number of
  files. Any of them coming back empty makes `snapshot` **refuse to arm** — and
  a dispatch with no fence refuses to run. A guarded path that is not on disk
  at all does the same, listed in `AGY_REQUIRE` or not: nobody guards a
  directory they do not have, so absence is a config error every time.
- An unset `AGY_GATES` is a **hard failure**, not a pass. An unverified dispatch
  is worse than no dispatch, because its report will be believed.
- A surviving `{{marker}}` in the shared context or in the task's own brief
  **stops the dispatch** (`AGY_ALLOW_UNFILLED=1` if the text genuinely needs
  one). The installer reports it in its own checks, so the first dispatch is not
  the messenger.

> **"It said it worked" is not evidence.** Neither is exit `0`. The only things
> this protocol treats as evidence are: the parsed event stream, the diff, the
> fence comparison, and the gate output — each produced by the harness, none by
> the implementer.

---

## The `.agy/` machinery

```
.agy/
├── config                     the only file that differs between projects
├── dispatch                   the sanctioned way to call agy  (~760 lines)
├── tripwire                   the integrity fence             (~430 lines)
├── gates                      your verification suite — a starter; make it real
├── review-pkg                 builds a review package from a diff range
├── fingerprint-tree.ps1       fast metadata fingerprints (Windows)
└── work/<slug>/
    ├── progress.md            the ledger
    ├── dispatch-context.md    shared context, pointed at rather than quoted
    ├── task-dispatch.template.md
    └── logs/                  raw event streams + per-run responses

.claude/skills/agy-task-cycle/ thin project skill holding this repo's bindings
```

The four scripts are **the skill's to own** — refreshed on every install.
`config`, `gates` and the templates are **yours**, never overwritten without
`--force`.

### `.agy/dispatch` — the event-stream judge

The only sanctioned way to call `agy`. Its header comment is organised around
traps 1–4 in order, because each one shaped a specific part of it.

It:

- refuses to start against a brief or a shared context that still contains
  `{{markers}}`, and prints which `agy` binary resolved before it uses it;
- passes `--add-dir` with the correct native path form (trap 1);
- streams and parses the nested NDJSON event log with Node, counting tool calls,
  denials and tool errors, and judges the run from that rather than from `$?`
  (trap 2);
- carries `--dangerously-skip-permissions` internally, coupled to the fence, so
  the flag can never be used bare (trap 3);
- watchdogs a stream that goes silent, and defers on any run that ends without a
  `result` event, however it was stopped — falling through to on-disk evidence
  rather than grading how the session died (trap 4);
- arms the fence before the run, re-checks it after, then runs the gates itself;
- classifies quota exhaustion conservatively (see below);
- prints exactly one verdict block: `run` / `fence` / `landed` / `log` / `gates`.

Supports `--continue --file <path>` to resume the implementer's existing thread
for a correction round, which is far cheaper than starting cold.

### `.agy/tripwire` — the integrity fence

```bash
.agy/tripwire snapshot <dir>   # record the baseline
.agy/tripwire verify   <dir>   # compare now against it; non-zero on drift
.agy/tripwire check            # snapshot + verify in one shot (self-test)
.agy/tripwire surface <name>   # emit one surface's listing (spot-check)
.agy/tripwire surfaces         # list configured surface names
```

Surfaces come from `.agy/config`, not from the script. Every surface emits the
same shape — `<fingerprint><TAB><path>` — so one differ reads all of them. It
asks the CLI nothing and trusts the CLI's report not at all.

Three surface kinds:

| Surface | Fingerprint | Use |
|---|---|---|
| `AGY_GUARD_DIRS` | content hash | directories the implementer must not touch (always includes `.agy` and `.claude`) |
| `AGY_GUARD_FILES` | content hash | individual files, e.g. the ledger; `~` expands |
| `AGY_GUARD_TREE` | size + mtime | one large external read-only tree (a dev site, a data dir) |

**Why the tree is metadata-fingerprinted.** Content-hashing a ~15,700-file tree
means opening every file, which on Windows puts Defender's real-time scanner in
the path of each open: throughput collapses from ~3,500 files/s to ~60, and a
6-second pass becomes one that cannot finish in 150. MSYS `find` is no better —
it answers `-type f` from the directory entry (fast), but any mtime predicate
forces a per-file `stat()` that opens the file. PowerShell's `Get-ChildItem`
returns `Length` and `LastWriteTime` as part of the directory enumeration, so
the whole tree costs under a second and never opens a file. GNU `find -printf`
is the equivalent on Linux, where `stat()` is cheap.

The trade is stated rather than hidden: a write preserving both size and mtime
slips past the tree surface. That takes deliberate forgery, which is not the
threat model — the threat model is *an agent editing files it was told not to*.
A fence that intermittently takes minutes is a fence that gets switched off, and
a switched-off fence catches nothing at all.

**The fail-safe:** any surface listed in `AGY_REQUIRE` that comes back empty
makes `snapshot` refuse to arm. `.agy/fingerprint-tree.ps1` likewise exits
non-zero if the root is missing or the walk yields nothing — *so a broken fence
reports as broken rather than as clean.*

### `.agy/gates` — the verification suite

```bash
.agy/gates      # exit code is the number of FAILING gates
```

Real linters, type-checkers and test suites, run **by the harness**, after the
run, outside the implementer's control. Because the exit code is a failure
count, `.agy/gates && git commit` works.

This file is yours. The installer writes a starter from whatever toolchain it
detects — PHP/composer, Node (reading `package.json`'s `scripts` block), Cargo,
Go, Python — and that starter is a guess. **Replacing it is the step that
actually matters.** If the installer detects nothing it writes a commented TODO
block, and the runner then *fails* until you fill it in.

Three rules keep gates worth trusting:

1. A gate that cannot run must **FAIL**, never pass quietly. A single
   `command || true` in this file defeats the entire protocol.
2. Print the result line, not the whole run — a dispatch pastes this output into
   the controller's context on every task.
3. Keep it under ~60s. A slow suite stops being run on every change, and one
   that is skipped guards nothing.

### `.agy/review-pkg` — the review packager

```bash
.agy/review-pkg <base> <name> [head]

.agy/review-pkg 17dd100 task-3      # -> <workspace>/review-task-3.diff
.agy/review-pkg dfafed2 task-3-r1   # -> <workspace>/review-task-3-r1.diff
```

Commit list, stat summary and the full `-U10` diff for `BASE..HEAD`, in one file
a reviewer can read in a single call.

Lockfiles are excluded — on the first package built by hand for this workflow,
`composer.lock` and `package-lock.json` accounted for 3,476 of 4,261 lines and
would have pushed the real content past the reviewer's read limit. The manifests
themselves (`composer.json`, `package.json`, …) are always included in full, so
nothing a reviewer must judge is hidden.

#### `--check` — is the review finished?

```bash
.agy/review-pkg --check <workspace>/task-3-review.md --ac 12
# reviewed: brief=ok spec=pass quality=approved ac=12/12 (…/task-3-review.md)
```

The package tells the reviewer to end its file with one line:

```
REVIEW-END brief=<ok|findings> spec=<pass|fail> quality=<approved|changes> ac=<met>/<total>
```

`--check` tests for its **absence** and exits non-zero. A reviewer killed
mid-write leaves a file that reads exactly like a review which found nothing —
the verdict table is written before the findings are, so what survives is a
complete-looking table with every row MET and no findings section. The
controller's only signal was the presence of a table, which is what the
truncated file has. An unfinished artefact must not borrow the vocabulary of a
finished one.

Three other things fail on the way past, all of them arithmetic rather than
judgement: a spec `pass` reported alongside criteria that were not met, more
criteria met than issued, and — with `--ac <n>` — a reconciled total that does
not match the count the brief handed out. That last one is how a dropped row
becomes visible: an optimistic table is still a checklist, wrong but auditable,
where a table that can lose rows shows the reader nothing about what is gone.

The line it prints on success is what goes in the ledger, so a review nobody
checked is a review with no verdict to record.

---

## Installing

### Requirements

| | |
|---|---|
| [Antigravity CLI](https://antigravity.google/docs/cli/install) | v1.1.12 or later, authenticated |
| Node.js | the dispatcher parses the event stream with it |
| git, bash | Git Bash on Windows |
| Claude Code | this is a Claude Code skill |

If `agy --version` does not answer, start with
[`reference/setup.md`](reference/setup.md) — install, auth, and a smoke test that
proves a headless run really touches your repo.

### Install the skill

```bash
git clone https://github.com/DIGX/DTS-Skills.git
cd DTS-Skills
bash scripts/install-skill agy-agents          # --link to symlink instead
```

### Install into a repository

From the repository root, in Claude Code:

```
/agy-agents
```

With no argument it routes on what it finds: no `.agy/` means install, an
existing `.agy/` means report status. `setup`, `install`, `adopt`, `status`,
`doctor` and `protocol` route explicitly.

Or directly:

```bash
bash ~/.claude/skills/agy-agents/scripts/install --dry-run    # always first
bash ~/.claude/skills/agy-agents/scripts/install --project NAME --milestone m1
```

| Flag | Effect |
|---|---|
| `--root <path>` | project root (default: git root of the cwd) |
| `--project <name>` | display name (default: the root directory's name) |
| `--milestone <slug>` | workspace slug; also **moves** an installed project to it (default: the one already bound, else `m1`) |
| `--workspace <path>` | bind to an existing workspace instead of `.agy/work/<slug>` |
| `--gates <path>` | bind to an existing gate runner instead of writing one |
| `--guard-tree <path>` | fence an external read-only tree |
| `--plan <path>` | the plan the ledger should reference |
| `--force` | overwrite config, gates and templates |
| `--dry-run` | print every path it would touch, change nothing |

The installer finishes by checking `agy` and `node` are on PATH, arming and
verifying the fence, and running the gates.

### Adopting a repository already mid-flight

Adoption is the same command. Before writing anything it scans for work already
in progress and **binds to it rather than duplicating it**:

- **An existing workspace** — any `.superpowers/sdd/*/` or `.agy/work/*/`
  containing a `progress.md`, most recently written first. Found →
  `AGY_WORKSPACE` points at it and your ledger keeps its history. Nothing is
  moved. An `.agy/config` that already exists outranks the scan; `--workspace`
  and `--milestone` outrank both.
- **An existing gate runner** — `scripts/gates`, `bin/gates` or `./gates`.
  Found → `AGY_GATES` points at it and no starter is written. Your suite is
  almost certainly better than a generated one.

Nothing is deleted, moved or rewritten. Order of operations:

1. `--dry-run` and read the plan it prints.
2. Install.
3. Open `.agy/gates` and make it the real suite — **the step that matters**.
4. `.agy/tripwire check` — confirm every required surface fingerprints a
   non-zero number of files.
5. Move project-specific task-cycle knowledge into
   `.claude/skills/agy-task-cycle/SKILL.md` under *Local rulings*.

### Advancing to the next milestone

```bash
bash ~/.claude/skills/agy-agents/scripts/install --milestone m6
```

Scaffolds `.agy/work/m6/` and **repoints `AGY_WORKSPACE`** — one line rewritten,
the rest of your config untouched. Never `--force` to advance: that takes the
gates and the templates with it. The previous milestone stays on disk with its
ledger; the installer prints the `cp` that carries the shared context over.

Nothing installed restates the workspace path, because the path carries the
milestone. `.agy/config` is the binding and everything reads it from there —
including the project skill, which resolves it at the top of a session.

---

## Configuration

Every line of `.agy/config` is `: "${VAR:=default}"`, so **the environment always
beats the file** and a one-off override needs no extra machinery:

```bash
AGY_FALLBACK=force .agy/dispatch 4
AGY_MODEL=gemini-3.1-pro-high .agy/dispatch 4
```

| Key | Meaning |
|---|---|
| `AGY_WORKSPACE` | where briefs, dispatches, reports and logs live |
| `AGY_LEDGER` | the progress file; guarded as a file surface |
| `AGY_GATES` | path to the gate runner. **Empty is a hard failure**, not a pass |
| `AGY_MODEL` | primary implementer (`gemini-3.7-flash-high`) |
| `AGY_FALLBACK_MODEL` | reserve, weekly exhaustion only (`claude-opus-4-6-thinking`) |
| `AGY_FALLBACK` | `auto` \| `force` \| `off` |
| `AGY_EFFORT` | `--effort` value; passed on every model, suffixed or not |
| `AGY_TIMEOUT` | per-run wall clock (`45m`) |
| `AGY_IDLE_TIMEOUT` | seconds of stream silence before a run is presumed hung (`300`; `0` disables) |
| `AGY_MAX_WALL` | seconds of total run time before a livelocked run is capped, silent or not (`2700`; `0` disables) |
| `AGY_IDLE_POLL` | how often the stream is measured (`15`) |
| `AGY_GUARD_DIRS` | directories fenced by content hash |
| `AGY_GUARD_FILES` | individual files fenced by content hash; `~` expands |
| `AGY_GUARD_TREE` | external tree fenced by size+mtime |
| `AGY_GUARD_TREE_SKIP` | patterns excluded from that tree |
| `AGY_REQUIRE` | surfaces that must be non-empty or the fence refuses to arm |

`AGY_GUARD_DIRS` always includes `.agy` and `.claude`. `.git` and the workspace
itself are pruned from every hash, so a run's own logs never trip its own fence —
but the ledger stays guarded **as a file**, which is why you must never write to
it mid-dispatch.

### Paths containing spaces

Guard lists are whitespace-separated, which cannot express `Acme Suite/app`.
Write **one path per line** instead:

```bash
AGY_GUARD_DIRS='.agy
.claude
Acme Suite/app'
```

Each list is split independently. This matters more than it sounds: without it
such a path silently splits into several nonexistent surfaces, each fingerprints
nothing, and a fence guarding nothing reports **clean**. Put the path in
`AGY_REQUIRE` too and the fence refuses to arm instead of lying.

### Model IDs

```
gemini-3.7-flash-high | -medium | -low
gemini-3.5-flash-high | -medium | -low
gemini-3.1-pro-high   | -low
claude-sonnet-4-6
claude-opus-4-6-thinking
gpt-oss-120b-medium
```

Effort appears in two places — as a suffix on the Gemini IDs, and as a real
session flag (`--effort low|medium|high`). `.agy/dispatch` passes `--effort` on
**every** model, including the suffixed ones. Which wins when they disagree is
not pinned down, so keep them consistent.

---

## Running a task

Full protocol: [`reference/protocol.md`](reference/protocol.md). One pass:

1. **Record BASE** — `git rev-parse HEAD`. Never `HEAD~1`; tasks routinely land
   as several commits.
2. **Write the brief** — `<workspace>/task-N-brief.md`.
3. **Write the dispatch** — `<workspace>/task-N-dispatch.md` from the template.
   Your job is the envelope around the brief: interfaces from earlier tasks,
   rulings on anything ambiguous, and the scope fence.
4. **Dispatch** — `.agy/dispatch N`.
5. **Verify the gates yourself** — read the dispatch's output, never the
   implementer's claim about it.
6. **Read the actual diff** — `git log BASE..HEAD` and the changed files. Check
   for files touched that the dispatch did not name.
7. **Package the review** — `.agy/review-pkg <BASE> task-N`.
8. **Dispatch a fresh Claude subagent reviewer** — three verdicts: brief
   integrity, spec compliance, code quality. Then
   `.agy/review-pkg --check <workspace>/task-N-review.md --ac <n>` before
   reading it: a review that was cut off looks like one that found nothing.
9. **Fix loop** — rounds 1–3 back to the implementer via
   `.agy/dispatch --continue --file <correction>`; rounds 4–5 escalate to Claude.
   Five rounds maximum.
10. **Close the task** — append commits, gate results, deferred Minors and any
    rulings to the ledger.

Three rules that carry most of the weight:

- **Dispatches point at files; they never quote them.** The implementer reads
  the same disk you do. This keeps a dispatch cheap enough to write in full.
- **Delegating implementation does not delegate review.** The reviewer is a
  fresh Claude subagent that never saw the implementation happen — it has caught
  an initialiser that silently did nothing while every gate stayed green.
- **The brief is reviewed too, before the diff is.** Ask whether its stated
  invariants actually follow from its stated rules. A brief that fails that test
  produces perfect compliance, a clean review and green gates over a defect
  nobody downstream can see — the controller wrote it, so the controller cannot
  be the one to catch it.
- **Never write to the ledger during a dispatch.** It is a guarded surface; a
  controller edit mid-run lands as a fence violation.

### Sizing

Signals a task is too big for one dispatch: more than ~4 files in scope, more
than one new class plus its tests, or any step whose correctness depends on a
plan section the brief only summarises.

**Raise review scrutiny, don't lower it, when a large task comes back unusually
fast.** Speed is not evidence of correctness, and here it has repeatedly meant
the opposite.

---

## Reading a verdict block

Every dispatch ends with the harness's judgements and the path to the evidence
behind them. **Anything other than clean / clean / green stops the cycle.**

| Line | Means |
|---|---|
| `run` | the harness's own reading of the event stream, not `$?` |
| `fence` | guarded surfaces before vs after — a violation names the files |
| `landed` | what the run put in the tree: commits, uncommitted changes, or nothing |
| `log` | the event stream of the attempt that produced this verdict |
| `gates` | the project's verification suite, run by the harness |

`landed  NOTHING — no commit, and nothing changed outside the workspace` is the
one to read twice. Every other line describes how the session behaved, and a
run that wrote no code at all behaves impeccably: clean run, clean fence, green
gates, a confident report. The workspace is excluded from the count for the
same reason the fence prunes it — a report saying the work happened is not the
work. It reports rather than fails, because an investigation task legitimately
lands nothing and a harness that cries wolf on those gets ignored on the ones
that matter.

`landed  NOT COMMITTED — N change(s) outside the workspace, 0 commits` does
fail the run. That one is not a judgement call: the brief's definition of done
names the commit, so work sitting in the working tree is an unfinished task —
and the next dispatch starts on top of it, inheriting changes no ledger entry
explains.

Read the `log` line here, not the one in the header. The header prints its path
before any attempt runs, so on a quota fallback it names the attempt that hit
the wall while the work happened under `<base>.reserve.*`. Following the header
on a fallback means grading a failed run's artefacts as the work.

`gates  not run` appears only under `AGY_SKIP_GATES=1`. If `AGY_GATES` is unset
the dispatch fails rather than passing.

`run  clean, but WATCHDOG-KILLED after Ns idle` is trap 4: the run was stopped,
not judged. Treat the fence and gates below it as the whole verdict, and read the
report — it had to be written *during this run* to get that far.

`run  clean, but the SESSION DIED before its result event` is the same verdict by
the other route — agy stopped on its own and the watchdog never fired. Read it
identically. It is deliberately not `PROBLEMS`: the work landing and the session
dying are different facts, and a harness with one word for both teaches you to
discount that word.

---

## Quota and the reserve policy

Antigravity meters two buckets, each with **its own weekly and 5-hour limit**:

| Group | Members | Role |
|---|---|---|
| `GEMINI MODELS` | Gemini Flash, Gemini Pro | primary |
| `CLAUDE AND GPT MODELS` | Claude Opus, Claude Sonnet, GPT | reserve |

The reserve drains far faster for the same work, so it is never a co-equal.
Fallback happens **only on a clear weekly exhaustion of the Gemini group**. A
spent 5-hour window refreshes on its own within hours — the dispatch reports and
holds rather than burning the reserve on a window that would have healed itself.

**Quota is not queryable headlessly** — `agy quota` produces nothing and no quota
verb appears in `agy --help`; it exists only in the interactive panel. So
exhaustion is detected from the failure itself, not polled in advance.

**Nothing about being in fallback is persisted.** Every dispatch starts on Gemini
again, which is what makes "switch back the moment it is available" automatic —
there is no sticky flag that can strand you on the reserve.

The classifier is deliberately conservative: a quota-shaped error that does not
clearly say *weekly* does **not** trigger fallback. It stops and prints the raw
text, so the first genuine occurrence tells you the exact string.

```bash
AGY_FALLBACK=force .agy/dispatch 4    # panel already shows the weekly bucket spent
AGY_FALLBACK=off   .agy/dispatch 4    # never touch the reserve
```

---

## Verifying the harness itself

```bash
bash ~/.claude/skills/agy-agents/scripts/selftest      # --keep to retain the temp repo
```

Builds a throwaway repository and exercises the whole harness against a
**stubbed** `agy` — fence arm/violate/refuse, the zero-gates fail-safe, git
fast-forward vs branch switch, all four quota routes, the watchdog and its
report-freshness check, adoption, idempotency.

It spends **no quota**, touches nothing outside its temp dir, and **aborts rather
than run if `agy` resolves to the real CLI**. Run it after editing anything under
`assets/`.

Every assertion in it exists because the property it checks is one you cannot see
failing from the outside.

---

## Debugging a run

Start with [`reference/dispatch-traps.md`](reference/dispatch-traps.md), then:

1. Read `<workspace>/logs/task-N-<stamp>.events.ndjson` — the raw stream. It is
   the only account of the run that cannot be summarised away.
2. `git log BASE..HEAD` and `git status --short` — what actually landed.
3. `.agy/gates` yourself — never the implementer's claim about them.
4. `.agy/tripwire check` — proves the fence still fingerprints real files.
5. `bash ~/.claude/skills/agy-agents/scripts/selftest` — proves the harness
   itself still works, spending no quota.

---

## Layout of this skill

```
agy-agents/
├── SKILL.md                       the skill Claude Code loads; routes on argument
├── README.md                      this file
├── reference/
│   ├── setup.md                   install & authenticate agy; headless smoke test
│   ├── install.md                 installing, adopting, full config reference
│   ├── protocol.md                the task cycle, reviewer contract, fix loop
│   └── dispatch-traps.md          the five traps, event shape, quota, debugging
├── assets/
│   ├── dispatch                   ─┐
│   ├── tripwire                    │ copied into .agy/ on install
│   ├── gates                       │ (the four scripts are refreshed
│   ├── review-pkg                  │  on every install; gates is yours)
│   ├── fingerprint-tree.ps1       ─┘
│   └── templates/
│       ├── dispatch-context.md    shared context the dispatch points at
│       ├── progress.md            the ledger
│       ├── project-skill.md       the per-repo agy-task-cycle skill
│       └── task-dispatch.md       the per-task dispatch template
└── scripts/
    ├── install                    deploy/adopt into a repository
    └── selftest                   stubbed end-to-end harness verification
```

`reference/` files are read on demand, not at load time — the routing table in
`SKILL.md` decides which one is needed, so none of this costs context until it
is relevant.

---

## Caveats

- **Developed and used daily on Windows** with Git Bash. Platform-specific paths
  are guarded (`cygpath` falls back, `powershell.exe` is behind a `command -v`
  check) and CI runs the suite on Ubuntu and Windows both — but Windows is where
  it has real mileage.
- **Verified against Antigravity CLI v1.1.12.** The traps were found by probing,
  not by reading documentation, and the published event-shape docs did not match
  the wire. If your version differs, re-run the smoke test in `setup.md` before
  trusting a dispatch.
- **The quota classifier is written against expected vocabulary**, not a captured
  exhaustion event. If you hit the real thing, the raw string is in the log —
  please [open an issue](https://github.com/DIGX/DTS-Skills/issues) with it.
- **The installer cannot write your gates.** It emits a starter from whatever
  toolchain it detects, and that is a guess.
- **Trap 5 is reported, not reproduced here.** It was reported against v1.1.12 by
  a second harness and is consistent with trap 3; the exact matching rule is
  Antigravity's. It costs nothing to assume — the harness never relied on `deny`.

---

Part of [DTS-Skills](../README.md). MIT licensed.
