# Antigravity CLI: what breaks, and how the harness answers it

Read this before debugging a run, and before ever calling `agy` by hand.

Verified against **Antigravity CLI v1.1.12**. If your version differs, re-verify
before trusting any of it.

## The six traps

They share one property: **the failure is invisible from the outside.** The
first three make a broken run report SUCCESS with exit 0. The fourth makes a
*finished* run look like a hung one for 45 minutes. The fifth makes a fence you
believe you have fail open silently. The sixth does it the other way round — it
makes a *finished, committed, gate-green* run report failure, which costs you
the same thing in the end, because a verdict word that fires on good runs stops
being read. None was found by reading documentation; all six came out of probes
or the field.

Traps 1–4 shape `.agy/dispatch` directly, in the same order as its header
comment. Trap 5 shapes nothing, because the harness had already abandoned the
mechanism it breaks. Trap 6 is documented in its own section below rather than
here, because the answer to it is longer than the trap.

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

**The flag does not skip `deny` rules.** Reported from the field: a
`write_to_file` into the CLI's *own* scratch directory was auto-denied under
`--dangerously-skip-permissions`, with the reason `Matches user-configured deny
rule` — and `agy` exited **0 with `status SUCCESS`** anyway, which is trap 2
again. So "dangerously skip permissions" names half of what it does. A
machine-wide `deny` rule you forgot about will silently amputate a run and
report success, and the only trace is in the event stream. `.agy/dispatch`
catches it; `agy` on its own does not.

That is also the second reason `setup.md` tells you to keep fencing in your own
repository rather than in the machine-wide `settings.json`: the rule reaches
runs it was never written for, including this harness's.

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

The watchdog catches the silent form. There is a **chatty** form it cannot see:
the same `manage_task`/`schedule` loop, but emitting events the whole time, so
the stream keeps growing and the run sits there until agy's own
`--print-timeout` expires and it dies with `timeout waiting for response`.
Observed at 2711s wall against 364s of thread time — on a run that had already
committed the work and written a 303-line report.

Both forms end the same way: **no `result` event.** That, and not who did the
killing, is what the harness keys on.

A run with no `result` event is **deferred**, not failed: it was stopped, so
status, response and exit code describe *how it ended* rather than whether the
work was done, and are not judged. Nothing else is relaxed — a denial or zero
tool calls still fail a deferred run, because each is recorded in the stream and
is evidence of what actually happened. (A tool error is evidence too, but of the
*path* rather than the outcome; trap 6 below settles those against what landed,
on a deferred run like any other.) A deferred run is also never
quota-classified, so a hang can never open the reserve bucket.

What replaces the missing result is a **report freshness check**: the report
must exist *and* be newer than the moment this dispatch started. A stale report
from an earlier dispatch would otherwise sail through on a clean fence and a
green gate — which is the exact shape of a run that did nothing at all.

The tool tally from a cut-off stream is printed as a **floor, not a total**, and
says so. A stream that ends mid-run recorded only what it recorded; read as a
run summary it says the implementer wrote nothing, next to a commit that is on
disk.

A report written by this run, plus a clean fence, plus green gates, is a pass
regardless of how the process died. Set `AGY_IDLE_TIMEOUT=0` to disable the
watchdog; `AGY_IDLE_POLL` (default 15s) sets how often the stream is measured.
Size is used rather than mtime: the stream is append-only so size is monotone,
and one-second mtime granularity makes short gaps unreadable.

#### The variant the watchdog cannot see

A run that finishes the work and then *polls itself* never goes silent. The
observed shape: the implementer committed, then called `schedule` for a
five-second wake to check on its own verify task, never woke, and re-armed. The
stream grew the whole time, so there was nothing for the watchdog to measure,
and the wrapper stayed blocked on a process that was never going to exit — so
the fence, the gates and the verdict never printed at all. A run that was *done*
read as incomplete.

`AGY_MAX_WALL` (default 2700s, `0` disables) is the cap that catches it, because
it asks the stream nothing:

```
WALL CAP  run alive for 2700s (cap 2700s) - killing agy (pid 12345).
WALL CAP  the stream may still be moving; a model polling itself
WALL CAP  is not progress. The verdict now rests on the fence, the
WALL CAP  gates and the report.
```

The verdict says `WALL-CAPPED at Ns — the run would not end`, deliberately not
borrowing the idle kill's wording: one says the run went quiet, the other says
it would not stop, and the reader goes to a different place for each.

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
{"event":"init","init":{"model":"gemini-3.7-flash-high","cwd":"..."}}
{"event":"step_update","step_update":{"step_type":"tool","state":"DONE","tool_name":"..."}}
{"event":"result","result":{"status":"SUCCESS","response":"...","num_turns":2}}
```

A parser written against the flat shape sees no events at all and reports a
clean, empty run.

## Quota: two independent groups

Antigravity meters two groups, each with **its own long-horizon and
short-horizon limit**:

| Group | Members |
|---|---|
| `GEMINI MODELS` | Gemini Flash, Gemini Pro |
| `CLAUDE AND GPT MODELS` | Claude Opus, Claude Sonnet, GPT |

Which group is primary is a config decision, not a property of the vendors:
`AGY_MODEL` is tried first and `AGY_FALLBACK_MODEL` is the reserve, and either
slot may hold either group. Both arrangements are in the field.

The reserve drains far faster for the same work, so it is never a co-equal.

Fallback happens **only on a clear exhaustion of the primary's long bucket**. A
spent short window refreshes on its own within hours — the dispatch reports
and holds rather than burning the reserve.

**Quota is not queryable headlessly.** `agy quota` produces nothing and no quota
verb appears in `agy --help`; it exists only in the interactive panel. So
exhaustion is detected from the failure itself, not polled in advance.

**Nothing about being in fallback is persisted.** Every dispatch starts on the
primary again, which is what makes "switch back the moment it is available"
automatic — there is no sticky flag that can strand you on the reserve.

### Which bucket, without asking the vendor

The classifier reads the **reset horizon the error states about itself**. That
is the one vocabulary every vendor shares: a bucket coming back in hours is
short and worth waiting out, one coming back in more than 12 hours is long and
worth the reserve. An explicit bucket word (*week*, *month*, *5-hour*) outranks
the horizon — that is the vendor naming the bucket rather than us inferring it.

It reads horizons because it used to read one vendor's wording. The
reserve-authorising class was reached only by matching the literal word *week*,
which is Gemini's. Anthropic's individual quota says `Individual quota reached.
... Resets in 3h27m2s` and never says week, so under `AGY_MODEL=claude-*` every
quota failure classified as `unknown` and `AGY_FALLBACK=auto` was unreachable
code — a fallback that could fire only for the group the harness was not
configured to use. Reported from the field as GST-40.

It is still deliberately conservative: an error that names no bucket **and**
states no reset time does **not** trigger fallback. It stops and prints the raw
text, so the first genuine occurrence tells you the exact string and the matcher
gets corrected once.

Use `AGY_FALLBACK=force` in the meantime; the interactive panel shows the real
number.

```bash
AGY_FALLBACK=force .agy/dispatch 4    # panel already shows the long bucket spent
AGY_FALLBACK=off   .agy/dispatch 4    # never touch the reserve
```

### Model IDs

Do not copy this list on faith — read it off the CLI:

```bash
agy models < /dev/null        # <id><TAB><display name>
```

**`agy models` hangs if it inherits an open stdin.** It produces no output and
no error; it simply sits there until something kills it. Redirect stdin and it
answers in about a second. Worth knowing beyond this one subcommand: a headless
`agy` invocation should never be handed a stdin it might read from.

As of v1.1.12 (`gemini-3.7-flash-high` is the harness default):

```
gemini-3.7-flash-high | -medium | -low
gemini-3.6-flash-high | -medium | -low
gemini-3.5-flash-high | -medium | -low
gemini-3.1-pro-high   | -low
claude-sonnet-4-6
claude-opus-4-6-thinking
gpt-oss-120b-medium
```

The 1.1.12 release notes advertise `--output-format json` on `models` and
`agents`. The 1.1.12 binary rejects it (`flags provided but not defined`), so
parse the tab-separated form above.

`--effort` is the same shape of trap one paragraph further on. `agy --help`
lists `--effort (low|medium|high)` without qualification, and it is real — on
Gemini. Claude and GPT reject it outright: the process exits within seconds
having taken **zero turns**, with no message that names the flag. Two runs were
lost to this before the cause was found, and both looked like the quota failure
that preceded them rather than like a bad command line.

Through 1.8.10 `.agy/dispatch` passed it on every model, which made the reserve
path unrunnable in every repository this skill had installed — invisibly, since
the fallback is rare and its symptom is indistinguishable from the exhaustion
that triggers it. It is now sent only to models whose ID starts `gemini`, keyed
on the model string at the call site rather than on the config slot, so the
supported inversion (Claude primary, Gemini reserve) routes correctly in both
directions. Unrecognised models get no flag.

`AGY_EFFORT=` is not an off switch and never was: `.agy/config` writes
`: "${AGY_EFFORT:=high}"`, and `:=` fires on null as well as unset, so an empty
value re-supplies the default rather than clearing it. That dead end is why the
routing is keyed on the model name.

Where the suffix and the flag disagree on a Gemini model, which one wins is not
something this project has pinned down, so keep them consistent: if you set
`AGY_MODEL=gemini-3.7-flash-low`, set `AGY_EFFORT=low` too rather than relying
on one to override the other.

## Reading a verdict block

Every dispatch ends with the harness's judgements and the path to the evidence
behind them. Anything other than clean / clean / green stops the cycle.

| Line | Means |
|---|---|
| `run` | the harness's own reading of the event stream, not `$?` |
| `fence` | guarded surfaces before vs after — a violation names the files, and `COULD NOT JUDGE` means the baseline and the config disagree |
| `landed` | what the run put in the tree: commits, uncommitted changes, or nothing |
| `share` | the lines *this run* committed — one side only, not a ratio: dispatch cannot see Claude's tokens for the task. Absent when nothing landed, and absent when git could not resolve what did. Run `.agy/bench/collect` for the split |
| `log` | the event stream of the attempt that produced this verdict |
| `gates` | the project's verification suite, run by the harness |

`landed` exists because every other line in the block describes how the session
behaved, and a run that produced no code behaves perfectly: clean run, clean
fence, green gates, and a report describing work that is not on disk. Three
forms:

- `landed  N commit(s) — <subject>` — history moved. The normal outcome.
- `landed  NOT COMMITTED — N change(s) outside the workspace, 0 commits` —
  **the run fails on this** (exit 1). The brief's definition of done requires
  the commit, so a tree full of changes and an empty history is an unfinished
  task, not a style question. Read the diff before doing anything with it: the
  next run starts on top of whatever is sitting there, and if you commit it
  yourself the ledger records your commit for the implementer's work.
- `landed  NOTHING — no commit, and nothing changed outside the workspace` —
  reports, does not fail: an investigation task legitimately produces no code.
  Read the diff before accepting anything in the report.

The workspace is excluded from the count for the same reason the fence prunes
it: the brief, the report and the logs are the harness's own paper trail, and
every run writes them. Counting them would make every run look productive,
which is the failure restated rather than fixed.

`turns` is agy's own count and is printed on its own line for that reason: runs
reporting `1 turns` have carried two dozen recorded tool calls. The measured
number is the tool total beside it, counted off the event stream.

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

`run  clean, but the SESSION DIED before its result event` is the same verdict
arrived at the other way — the chatty form of trap 4, where agy stopped on its
own and the watchdog never fired. Read it identically. It is deliberately not
`PROBLEMS`: the work landing and the session dying are different facts, and a
harness with one word for both teaches you to discount that word.

`run  clean, but N TOOL ERROR(S) the run worked around` is trap 6, below.

## Trap 6: one failed call condemns a finished run

`write_to_file` in Antigravity is sandboxed to the agent's own workspace and
refuses a path outside it — including `.agy/work/mN/task-N-report.md`, the one
file every dispatch is contractually required to produce. Observed in the field
on the reserve model: the run recovered through `run_command`, wrote 564 accurate
lines, and committed. agy had already downgraded the session to `status ERROR`
for that one call, and the harness turned that into exit 1. At the exit code the
run was indistinguishable from the quota failure forty minutes earlier that
committed nothing, and every reserve run had to be adjudicated by hand.

The exit code was the wrong instrument. It carries one bit and was being asked
two questions — *did anything go wrong along the way* and *did the work land* —
and the answers are independent. The fault injection behind the quota work had
already found the same defect from the other side: an assertion that a run
exited 0 passed against a run that never ran, because a run that never runs also
exits 0.

So a tool error stops being the verdict and becomes evidence, and recovery is
**proven, not inferred**. Every one of these is measured on the run itself:

| Measured | Why it is not enough on its own |
|---|---|
| the report exists, and *this* run wrote it | a stale one proves nothing |
| it carries its contract sections | a truncated one proves nothing |
| the fence is clean | no guarded surface moved |
| the gates are **green** | `not run` is absent, and absent is never green |
| the work is committed, and measured so | not "we could not tell" |
| no number in the report is contradicted | the gates outrank the account |
| the co-author trailer is the configured one | |
| nothing in the stream is about conduct | see below |

All of them must hold. Miss one and the run stays `PROBLEMS`, because an absent
measurement is never a pass — including the sidecar itself, which is read back
as *fail* when it cannot be read at all.

**Conduct is never recovered from.** A blocked call or a bypass in the same
stream fails the run however green everything else is, and the greenest possible
tree does not answer it: the report will describe the work as done, accurately.
A denial is a fact about the boundary holding; a tool error is a fact about the
path the run took to get around something. Only the second is recoverable.

Which puts the whole weight of that distinction on one regex, and the field
promptly leaned on it. Antigravity's auto-denial for a `deny` rule says
`Matches user-configured deny rule` — no *permission*, no *denied*, no *not
allowed*. Under the wording list as it stood, that denial would have been filed
as a tool error, and a tool error is now recoverable: the one exemption conduct
must never get. The list was widened, with the field's verbatim sentence as the
fixture.

It errs toward calling things denials on purpose. A false denial costs one
hand-adjudication. A missed one costs the boundary, and the boundary is the
only thing here that cannot be rebuilt out of artifacts afterwards.

The errors stay printed in the run report above the verdict and counted in the
sidecar as `tool_errors=N`, next to `hard_fails=N`. Read them: a path a run had
to work around once will be there again next time.

## When the dispatch refuses to start

Refusals happen before `agy` is ever called. Each is the harness telling you it
cannot produce a trustworthy verdict — none is a bug to work around.

Every one of them prints a verdict block of its own, headed
`run  DID NOT RUN — <reason>` and carrying its own exit code as text:

```
--- verdict --------------------------------------------------------
  run     DID NOT RUN — no dispatch file at .agy/work/m6/task-7-dispatch.md
          write the brief there first — the implementer is told to read it
  exit    2

  Nothing was dispatched: no model was called and the tree is untouched.
```

The exit code was always correct, but it is the half of the signal that does not
survive how the harness gets run: `.agy/dispatch 3 | tee run.log` returns
**tee's** `0`, and so does a wrapper that reports whether it managed to start
the job in the background. What is left is a log otherwise shaped like a clean
run. So the refusal says it in the output too, in the same block a finished run
prints, and a reader that only ever sees stdout still cannot mistake it for
work. When you do want the status, run the dispatch unpiped — or read
`${PIPESTATUS[0]}` rather than `$?`.

| Message | Exit | Why |
|---|---|---|
| `no dispatch file at <path>` | 2 | The brief does not exist. The implementer is told to read that path, so there is nothing to run. |
| `no task given` | 2 | Called with no arguments. |
| `no .agy/config` | 2 | Not an installed repo. |
| `agy not found` | 127 | The CLI is not on `PATH` — see `setup.md`. |
| `is still a template — N unfilled line(s)` | 2 | A `{{marker}}` survives in the shared context or the task brief. Every agent inherits that file; an unfilled constraint reads as no constraint, and no gate can catch what was never specified. Fill it, or `AGY_ALLOW_UNFILLED=1` if the text genuinely needs `{{...}}`. |
| `guarded directory does not exist` / `guarded file does not exist` | 3 | A path in `AGY_GUARD_DIRS`/`AGY_GUARD_FILES`/`AGY_GUARD_TREE` is not on disk, so it would fingerprint nothing and the fence would report clean. Usually a moved path — or a path with a space written on one line, which splits into fragments that do not exist. Write guard lists **one path per line**. |
| `surface X came back EMPTY` | 3 | The path exists but fingerprinted zero files, and `AGY_REQUIRE` says it must not. The fingerprinter broke; a broken fence that says "clean" is worse than no fence. |
| `BASELINE DOES NOT MATCH THIS CONFIG` | 2 | `verify` was handed a baseline armed for a different set of surfaces than `AGY_GUARD_DIRS` now asks for. Either the config changed after the fence was armed, or the baseline was written by a different harness — a repo with its own `scripts/tripwire` alongside `.agy/tripwire` is the usual way this happens, since the two name their `.fp` files differently (ours after the **path**, `src/styles` → `src-styles.fp`). Re-arm; do not read the result either way. |

The `binary` line in the dispatch header exists for a fourth, quieter version of
the same problem: on MSYS a Windows-form `PATH` entry (`C:\...`) is accepted and
then never searched, so the `agy` you added can be skipped in silence and the
next one on `PATH` answers instead. Read that line before believing a run came
from the binary you intended. See `setup.md`.

## Debugging checklist

1. Read `<workspace>/logs/task-N-<stamp>.events.ndjson` — the raw stream. It
   is the only account of the run that cannot be summarised away.
2. `git log BASE..HEAD` and `git status --short` — what actually landed.
3. `( . .agy/config && bash $AGY_GATES )` yourself — never the implementer's claim about them.
4. `.agy/tripwire check` — proves the fence still fingerprints real files. An
   empty surface guards nothing and reports clean.
5. `bash ~/.claude/skills/agy-agents/scripts/selftest` — proves the harness
   itself still works, against a stubbed `agy`, spending no quota.
