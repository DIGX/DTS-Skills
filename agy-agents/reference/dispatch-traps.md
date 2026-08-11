# Antigravity CLI: what breaks, and how the harness answers it

Read this before debugging a run, and before ever calling `agy` by hand.

Verified against **Antigravity CLI v1.1.12**. If your version differs, re-verify
before trusting any of it.

## The four traps

They share one property: **the failure is invisible from the outside.** The
first three make a broken run report SUCCESS with exit 0. The fourth makes a
fence you believe you have fail open silently. None was found by reading
documentation — all four came out of probes.

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

### 4. `permissions.deny` matches the literal command string

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

Every dispatch ends with three judgements. Anything other than
clean / clean / green stops the cycle.

| Line | Means |
|---|---|
| `run` | the harness's own reading of the event stream, not `$?` |
| `fence` | guarded surfaces before vs after — a violation names the files |
| `gates` | the project's verification suite, run by the harness |

`gates  not run` appears only under `AGY_SKIP_GATES=1`. If `AGY_GATES` is unset
the dispatch fails rather than passing: an unverified dispatch is worse than no
dispatch, because its report will be believed.

## Debugging checklist

1. Read `<workspace>/logs/task-N-<stamp>.events.ndjson` — the raw stream. It
   is the only account of the run that cannot be summarised away.
2. `git log BASE..HEAD` and `git status --short` — what actually landed.
3. `.agy/gates` yourself — never the implementer's claim about them.
4. `.agy/tripwire check` — proves the fence still fingerprints real files. An
   empty surface guards nothing and reports clean.
5. `bash ~/.claude/skills/agy-agents/scripts/selftest` — proves the harness
   itself still works, against a stubbed `agy`, spending no quota.
