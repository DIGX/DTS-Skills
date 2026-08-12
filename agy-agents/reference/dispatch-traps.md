# Antigravity CLI: what breaks, and how the harness answers it

Read this before debugging a run, and before ever calling `agy` by hand.

Verified against **Antigravity CLI v1.1.12**. If your version differs, re-verify
before trusting any of it.

## The five traps

They share one property: **the failure is invisible from the outside.** The
first three make a broken run report SUCCESS with exit 0. The fourth makes a
*finished* run look like a hung one for 45 minutes. The fifth makes a fence you
believe you have fail open silently. None was found by reading documentation —
all five came out of probes.

Traps 1–4 shape `.agy/dispatch` directly, in the same order as its header
comment. Trap 5 shapes nothing, because the harness had already abandoned the
mechanism it breaks.

### 1. `--add-dir` is not optional

`agy`'s default CLI project has no resources attached (`projectResources` is
`{}`), so a headless run gets a scratch workspace under
`~/.gemini/antigravity-cli/scratch`. Every path in your prompt resolves to
nothing.

The `init` event still reports the **real** cwd, so the transcript looks
correct. An early probe reported "not a git repository", "php is not
recognized" and "scripts/gates: No such file" — while `status` read `SUCCESS`.

**Answer:** `.agy/dispatch` always passes `--add-dir <native path>`. On Windows
it must be the Windows-form path, not the MSYS one.

### 2. The exit code proves nothing

A tool call the CLI is not permitted to make is **soft-denied**: the run
continues, the process exits 0, `status` still reads `SUCCESS`, and the only
trace is a notice on stderr. A probe whose every command was blocked exited 0,
status SUCCESS, with an empty response.

**Answer:** `.agy/dispatch` parses the event stream and judges the run itself —
tool calls made, tools denied, whether a response was produced — instead of
reading `$?`.

### 3. The permission system is inverted under `--print`

`permissions.allow` is honoured interactively and **silently ignored** in
headless mode. Every allowed command is denied, and the run lies about it.

A fence that blocks the work and permits the lie is worse than no fence. So the
harness runs with `--dangerously-skip-permissions` and puts a fence *it*
controls around the run instead: `.agy/tripwire` fingerprints the surfaces the
implementer must never touch, before and after.

**The flag lives inside `.agy/dispatch`, never in a bare command**, so it cannot
be used without the fence attached. If the fence will not arm, the dispatch
refuses to start (exit 3). Do not work around this.

### 4. A finished run can hang forever without emitting its result

`agy` can do the work, write the report, make the commit — and then never emit
its `result` event, trapped in an internal `manage_task`/`schedule` loop. No
error, no stderr, the process still alive. It will sit there until
`--print-timeout` expires 45 minutes later.

Observed on a run whose work was complete and committed **two minutes in**: the
last event was a schedule call asking to be woken in 20 seconds, and the stream
was still silent 16 minutes later.

Nothing about the process distinguishes this from slow work. The one tell is
that **the event stream stops growing.** So `.agy/dispatch` runs a watchdog: if
the stream is silent for `AGY_IDLE_TIMEOUT` (default 300s — about six times the
longest gap seen on a healthy run, where the slowest single tool call, the gate,
takes ~50s), it kills `agy` and falls through to judging the evidence on disk.

```
WATCHDOG  event stream silent for 300s - killing agy (pid 12345).
WATCHDOG  the verdict now rests on the fence, the gates and the report.
```

A killed run with no `result` event is **deferred**, not failed: the process was
stopped, so status, response and exit code describe *how it ended* rather than
whether the work was done, and are not judged. Nothing else is relaxed — a
denial, a tool error or zero tool calls still fail a deferred run, because each
is recorded in the stream and is evidence of what actually happened. A deferred
run is also never quota-classified, so a hang can never open the reserve bucket.

What replaces the missing result is a **report freshness check**: the report
must exist *and* be newer than the moment this dispatch started. A stale report
from an earlier dispatch would otherwise sail through on a clean fence and a
green gate — which is the exact shape of a run that did nothing at all.

A report written by this run, plus a clean fence, plus green gates, is a pass
regardless of how the process died. Set `AGY_IDLE_TIMEOUT=0` to disable the
watchdog; `AGY_IDLE_POLL` (default 15s) sets how often the stream is measured.
Size is used rather than mtime: the stream is append-only so size is monotone,
and one-second mtime granularity makes short gaps unreadable.

### 5. `permissions.deny` matches the literal command string

A `deny` rule is compared against the command text as written, not against the
program the command will end up running. So a wrapper defeats it:

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
therefore skips it entirely and derives its safety from `.agy/tripwire`, which
checks the filesystem after the fact rather than trying to predict a command.

That is also why `setup.md` tells you to keep fencing in your own repository
instead of adding `deny` rules to the machine-wide `settings.json`: the rule is
weaker than it looks, and it changes every other project on the machine.

> Reported against v1.1.12 by a second harness, and consistent with trap 3;
> the exact matching rule is Antigravity's, not something this project can pin
> open. It costs nothing to assume — the harness never relied on `deny` anyway.

## Event stream shape

The documented flat shape is wrong. Real `--output-format stream-json` events
are **nested** under a key matching `event`:

```json
{"event":"init","init":{"model":"gemini-3.6-flash-high","cwd":"..."}}
{"event":"step_update","step_update":{"step_type":"tool","state":"DONE","tool_name":"..."}}
{"event":"result","result":{"status":"SUCCESS","response":"...","num_turns":2}}
```

A parser written against the flat shape sees no events at all and reports a
clean, empty run.

## Quota: two independent groups

Antigravity meters two buckets, each with **its own weekly and 5-hour limit**:

| Group | Members | Role |
|---|---|---|
| `GEMINI MODELS` | Gemini Flash, Gemini Pro | primary |
| `CLAUDE AND GPT MODELS` | Claude Opus, Claude Sonnet, GPT | reserve |

The reserve drains far faster for the same work, so it is never a co-equal.
Fallback happens **only on a clear weekly exhaustion of the Gemini group**. A
spent 5-hour window refreshes on its own within hours — the dispatch reports
and holds rather than burning the reserve.

**Quota is not queryable headlessly.** `agy quota` produces nothing and no quota
verb appears in `agy --help`; it exists only in the interactive panel. So
exhaustion is detected from the failure itself, not polled in advance.

**Nothing about being in fallback is persisted.** Every dispatch starts on
Gemini again, which is what makes "switch back the moment it is available"
automatic — there is no sticky flag that can strand you on the reserve.

### The classifier is deliberately conservative

It is written against the vocabulary these errors normally use, not against a
captured Antigravity exhaustion event. So a quota-shaped error that does not
clearly say *weekly* does **not** trigger fallback — it stops and prints the raw
text, so the first genuine occurrence tells you the exact string and the matcher
gets corrected once.

Use `AGY_FALLBACK=force` in the meantime; the interactive panel shows the real
number.

```bash
AGY_FALLBACK=force .agy/dispatch 4    # panel already shows the weekly bucket spent
AGY_FALLBACK=off   .agy/dispatch 4    # never touch the reserve
```

### Model IDs

```
gemini-3.6-flash-high | -medium | -low
gemini-3.5-flash-high | -medium | -low
gemini-3.1-pro-high   | -low
claude-sonnet-4-6
claude-opus-4-6-thinking
gpt-oss-120b-medium
```

Effort appears in two places: as a suffix on the Gemini IDs, and as a real
session flag — `agy --help` lists `--effort (low|medium|high)`. `.agy/dispatch`
passes `--effort "$AGY_EFFORT"` on **every** model, including the suffixed ones.

Which one wins when they disagree is not something this project has pinned down,
so keep them consistent: if you set `AGY_MODEL=gemini-3.6-flash-low`, set
`AGY_EFFORT=low` too rather than relying on one to override the other.

## Reading a verdict block

Every dispatch ends with three judgements and the path to the evidence behind
them. Anything other than clean / clean / green stops the cycle.

| Line | Means |
|---|---|
| `run` | the harness's own reading of the event stream, not `$?` |
| `fence` | guarded surfaces before vs after — a violation names the files |
| `log` | the event stream of the attempt that produced this verdict |
| `gates` | the project's verification suite, run by the harness |

The header prints a `log` line too, but it does so before any attempt runs, so
it is provisional. On a quota fallback the reserve attempt writes to
`<base>.reserve.*` and the header's path now points at the attempt that hit the
wall — open it and you are grading a failed run's artefacts as the work. The
verdict block's copy is the one to act on.

`gates  not run` appears only under `AGY_SKIP_GATES=1`. If `AGY_GATES` is unset
the dispatch fails rather than passing: an unverified dispatch is worse than no
dispatch, because its report will be believed.

`run  clean, but WATCHDOG-KILLED after Ns idle` is trap 4: the run was stopped,
not judged. Treat the fence and the gates below it as the whole verdict, and
read the report — it had to be written during this run to get that far.

## When the dispatch refuses to start

Three refusals happen before `agy` is ever called. All three are the harness
telling you it cannot produce a trustworthy verdict — none is a bug to work
around.

| Message | Exit | Why |
|---|---|---|
| `is still a template — N unfilled line(s)` | 2 | A `{{marker}}` survives in the shared context or the task brief. Every agent inherits that file; an unfilled constraint reads as no constraint, and no gate can catch what was never specified. Fill it, or `AGY_ALLOW_UNFILLED=1` if the text genuinely needs `{{...}}`. |
| `guarded directory does not exist` / `guarded file does not exist` | 3 | A path in `AGY_GUARD_DIRS`/`AGY_GUARD_FILES`/`AGY_GUARD_TREE` is not on disk, so it would fingerprint nothing and the fence would report clean. Usually a moved path — or a path with a space written on one line, which splits into fragments that do not exist. Write guard lists **one path per line**. |
| `surface X came back EMPTY` | 3 | The path exists but fingerprinted zero files, and `AGY_REQUIRE` says it must not. The fingerprinter broke; a broken fence that says "clean" is worse than no fence. |

The `binary` line in the dispatch header exists for a fourth, quieter version of
the same problem: on MSYS a Windows-form `PATH` entry (`C:\...`) is accepted and
then never searched, so the `agy` you added can be skipped in silence and the
next one on `PATH` answers instead. Read that line before believing a run came
from the binary you intended. See `setup.md`.

## Debugging checklist

1. Read `<workspace>/logs/task-N-<stamp>.events.ndjson` — the raw stream. It
   is the only account of the run that cannot be summarised away.
2. `git log BASE..HEAD` and `git status --short` — what actually landed.
3. `.agy/gates` yourself — never the implementer's claim about them.
4. `.agy/tripwire check` — proves the fence still fingerprints real files. An
   empty surface guards nothing and reports clean.
5. `bash ~/.claude/skills/agy-agents/scripts/selftest` — proves the harness
   itself still works, against a stubbed `agy`, spending no quota.
