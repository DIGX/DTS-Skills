# Installing and adopting

```bash
cd <repo root>
bash ~/.claude/skills/agy-agents/scripts/install --dry-run
bash ~/.claude/skills/agy-agents/scripts/install --project NAME --milestone m1
```

Always `--dry-run` first. It prints every path it would write and changes
nothing.

## What lands

```
.agy/config                     the only file that differs between projects
.agy/dispatch                   the sanctioned way to call agy
.agy/tripwire                   the integrity fence
.agy/review-pkg                 builds a review workspace from a diff range
.agy/gates                      verification suite — a starter; make it real
.agy/fingerprint-tree.ps1       fast metadata fingerprints (Windows)
.agy/work/<slug>/progress.md    the ledger
.agy/work/<slug>/dispatch-context.md
.agy/work/<slug>/task-dispatch.template.md
.agy/work/<slug>/plan-dispatch.template.md   optional — see protocol.md
.claude/skills/agy-task-cycle/  thin project skill holding this repo's bindings
```

The four scripts are **the skill's to own** — they are refreshed on every
install. `config`, `gates` and the templates are **yours**, and are never
overwritten without `--force`.

## Fill the context before the first dispatch

`dispatch-context.md` and `task-dispatch.template.md` land full of
`{{markers}}`, because only you know what belongs in them. `dispatch-context.md`
is read by **every** implementer and **every** reviewer on the plan, so anything
left unfilled there is inherited by all of them — an agent told the language
floor is `{{Language/runtime floor}}` reads that as no constraint at all, and
the gates cannot enforce what was never written down. The run then passes every
check the harness has.

So `.agy/dispatch` **refuses to run** while any `{{marker}}` — or the "delete
this quote block" note at the top — survives in the shared context or in the
task's own brief. The installer's final checks report it too, rather than
letting the first dispatch be the messenger.

If a brief genuinely needs literal `{{...}}` in its text, `AGY_ALLOW_UNFILLED=1`
overrides the refusal for that run.

## Options

| Flag | Effect |
|---|---|
| `--root <path>` | project root (default: git root of the cwd) |
| `--project <name>` | display name (default: the root directory's name) |
| `--milestone <slug>` | workspace slug; also **moves** an installed project to it (default: the one already bound, else `m1`) |
| `--workspace <path>` | bind to an existing workspace instead of `.agy/work/<slug>` |
| `--gates <path>` | bind to an existing gate runner instead of writing one |
| `--guard-tree <path>` | fence an external read-only tree (a dev site, a data dir) |
| `--plan <path>` | the plan the ledger should reference |
| `--coauthor <trailer>` | the one `Co-Authored-By:` value landed commits may carry (see below) |
| `--force` | overwrite config, gates and templates |
| `--dry-run` | print, change nothing |

## The co-author trailer

Every commit an implementer lands carries a `Co-Authored-By:` trailer, and
`.agy/dispatch` **fails the run** on any address that is not the configured
one. GitHub resolves those trailers to accounts by email — the display name is
ignored — and counts them on the repository's contributor graph, so the address
is a public claim that a specific account helped write the code.

The default credits nobody: `Antigravity <antigravity@antigravity.invalid>`.
`.invalid` is reserved by RFC 2606 and can never be registered. This is the
default precisely because the installer runs in other people's repositories,
and a default that credits somebody credits the wrong somebody.

To credit your own account or organisation instead:

```bash
# this repository only
scripts/install --coauthor 'Antigravity <agy@example.com>'

# every repository you install into, from now on
export AGY_COAUTHOR='Antigravity <agy@example.com>'
```

Prefer a dedicated mailbox over a personal or general one — `agy@` reads as
machine authorship in `git log`, where `you@` quietly inflates a human's
contribution graph with work a model did.

Both the value in `.agy/config` and the trailer block in `dispatch-context.md`
are written from this one setting. Change one without the other and dispatch
refuses to run: the implementer would be judged against a rule it was never
given. Fix both, or re-install.

Already installed? `--coauthor` changes it in place — the `AGY_COAUTHOR` line
in `.agy/config` and the `Co-Authored-By:` line in the current milestone's
`dispatch-context.md`, both, in one run. Nothing else in either file is
touched, and the installer re-reads the config afterwards to confirm the new
value is what the harness will actually resolve. If it cannot, it says so and
tells you to edit by hand rather than reporting a change it did not make.

`AGY_COAUTHOR=` (empty) switches the check off. Opt out that way, never by
widening it to a value that matches anything.

### Which value wins

Four sources, most specific first:

| | source | when it applies |
|---|---|---|
| 1 | `--coauthor` on this run | always — this is how you change a decided project |
| 2 | `AGY_COAUTHOR` in `.agy/config` | the project already chose; `--force` does not override it |
| 3 | `AGY_COAUTHOR` in the environment | first install into this repository |
| 4 | the shipped default | nothing else was said |

An existing config outranks your environment on purpose. Exporting
`AGY_COAUTHOR` and then installing into somebody else's repository must not
rewrite their shared context to name your mailbox — and a milestone advance
re-scaffolds `dispatch-context.md`, so without that rule it would.

## Re-installing an existing repository

The four scripts (`dispatch`, `tripwire`, `review-pkg`, the gate runner) are
refreshed on every install. `.agy/config`, the gate file and the templates are
kept unless you pass `--force`.

Keeping the config wholesale used to mean a key introduced by a later version
never reached a repository installed before it existed — while the *code* that
reads that key arrived anyway. `AGY_COAUTHOR` is how that surfaced: 1.8.4
shipped the trailer check into repositories with no value for it to check
against, and an unset `AGY_COAUTHOR` means off. The check landed and did
nothing.

So a kept config is now compared against the one this version would write, and
any key missing from yours is **appended** in a dated block at the end, with
the comment paragraph that explains it. Nothing above that block is read for
its value, rewritten, or reordered — it stays yours. Appending is safe on its
own terms too: every binding is `${VAR:=…}` or `${VAR=…}`, so a value set
earlier in the file wins over anything below it. The installer names each key
it adds.

One of those additions has a consequence worth stating: adding `AGY_COAUTHOR`
to a config that never carried it turns the trailer check **on**, and dispatch
then refuses to run until the milestone context names the same address. That
refusal is correct, but meeting it on your next dispatch — in a repository
where nothing looked like it changed the rules — reads as a broken harness. So
the install that causes it says so, and either rewrites the template's
`Co-Authored-By:` line for you or prints the exact line to paste.

## Advancing to the next milestone

Same command, new slug:

```bash
bash ~/.claude/skills/agy-agents/scripts/install --milestone m6 --dry-run
bash ~/.claude/skills/agy-agents/scripts/install --milestone m6
```

It scaffolds `.agy/work/m6/` and **repoints `AGY_WORKSPACE` at it**, rewriting
that one line and leaving the rest of your config — gates, models, guard lists,
project environment — exactly as it is. Never use `--force` to advance a
milestone: it regenerates the gates and the templates too.

The ledger and the shared context do not travel on their own. The old
milestone's directory is left where it is, with its history intact, and the new
one starts from the templates — so the installer's final checks flag the fresh
`dispatch-context.md` as unfilled and print the `cp` that carries the previous
one over. The context describes the project, not the milestone; it is almost
always the file you want.

Because the workspace path carries the slug, **nothing installed restates it**.
`.agy/config` holds the binding and every script reads it from there, including
the project skill, which resolves it at the top of a session:

```bash
( . .agy/config; printf '%s\n' "$AGY_WORKSPACE" )
```

If a hand-edited config holds the binding in a shape the rewrite cannot find,
the installer says `COULD NOT REPOINT` and counts it as a problem rather than
reporting a move it did not make.

## Adopting an existing project

Adoption is the same command. Before writing anything it scans for work already
in progress and binds to it rather than duplicating it:

- **An existing workspace** — any `.superpowers/sdd/*/` or `.agy/work/*/`
  containing a `progress.md`, most recently written first. Found →
  `AGY_WORKSPACE` points at it, and your ledger keeps its history. Nothing is
  moved.
- **An existing gate runner** — `scripts/gates`, `bin/gates`, or `./gates`.
  Found → `AGY_GATES` points at it and no starter is written. Your suite is
  almost certainly better than the generated one.
- **Toolchain** — for a fresh install it detects PHP/composer, Node (reading
  the `scripts` block of `package.json`), Cargo, Go and Python, and writes a
  starter suite from what it finds. If it detects nothing it writes a commented
  TODO block, and the gate runner then **fails** until you fill it in.

An `.agy/config` that already exists outranks that scan: a project past its
first milestone has several `progress.md` on disk and only the config knows
which one is current. `--workspace` and `--milestone` outrank both — they are
you saying so on this run.

Order of operations when adopting a repo mid-flight:

1. `--dry-run` and read the plan it prints.
2. Install.
3. Open the runner `.agy/config` now points at — `.agy/gates` on a fresh
   install, your own on adoption — and confirm it is the real suite. This is
   the step that matters.
4. `.agy/tripwire check` — confirm every required surface fingerprints a
   non-zero number of files.
5. Move the project's task-cycle knowledge into
   `.claude/skills/agy-task-cycle/SKILL.md` under "Local rulings".

Nothing is deleted, moved, or rewritten in your existing tree. If you already
had a `scripts/gemini-dispatch`-style bridge, it is left exactly where it is;
delete it yourself once `.agy/dispatch` has proven itself on a real task.

## `.agy/config`

Every line is `: "${VAR:=default}"`, so **the environment always beats the
file** and a one-off override needs no extra machinery:

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
| `AGY_FALLBACK_MODEL` | reserve, long-bucket exhaustion only (`claude-opus-4-6-thinking`) |
| `AGY_FALLBACK` | `auto` \| `force` \| `off` |
| `AGY_EFFORT` | `--effort` value. Sent to Gemini models only — see below |
| `AGY_TIMEOUT` | per-run wall clock (`45m`) |
| `AGY_IDLE_TIMEOUT` | seconds of event-stream silence before a run is presumed hung (`300`; `0` disables) |
| `AGY_MAX_WALL` | seconds of total run time before a livelocked run is capped, silent or not (`2700`; `0` disables) |
| `AGY_IDLE_POLL` | how often the stream is measured (`15`) |
| `AGY_GUARD_DIRS` | directories fenced by content hash |
| `AGY_GUARD_FILES` | individual files fenced by content hash; `~` expands |
| `AGY_GUARD_TREE` | external tree fenced by size+mtime, not content |
| `AGY_GUARD_TREE_SKIP` | patterns excluded from that tree |
| `AGY_REQUIRE` | surfaces that must be non-empty or the fence refuses to arm |
| `AGY_CONTEXT` | the shared context every agent reads (`$AGY_WORKSPACE/dispatch-context.md`) |

Environment-only, never written to the config:

| Key | Meaning |
|---|---|
| `AGY_SKIP_GATES=1` | report only; do not run the gates |
| `AGY_ALLOW_UNFILLED=1` | dispatch against a brief that still contains `{{...}}` |

`AGY_GUARD_DIRS` always includes `.agy` and `.claude`. `.git` and the workspace
itself are pruned from every hash, so a run's own logs never trip its own fence
— but the ledger stays guarded as a *file*, which is why you must not write to
it mid-dispatch.

### Paths containing spaces

A whitespace-separated list cannot express `Acme Suite/app`. Write **one path
per line** instead and the list is split on newlines — which is the form the
installer now writes, so an edited config inherits the right shape by example:

```bash
AGY_GUARD_DIRS='.agy
.claude
Acme Suite/app'
```

Each list is split independently, so a newline in one does not change how the
others are read.

This matters more than it sounds: written on one line, such a path splits into
several nonexistent surfaces, each hashes to nothing, and a fence guarding
nothing reports **clean**. So the second half of the fix is that **a guarded
path that is not on disk makes the fence refuse to arm** — dir, file or tree,
whether or not it is named in `AGY_REQUIRE`. Nobody configures a guard for a
directory they do not have, so absence is always a config error, and the split
fragments above are exactly that error. `$HOME` alone is enough to hit this on
Windows: `C:\Users\Firstname Lastname`.

### Why a tree is fingerprinted by metadata

Content-hashing a large external tree means opening every file, and on Windows
that puts Defender in the path of each open: throughput collapses from roughly
3,500 files/s to about 60. `Get-ChildItem` returns `Length` and
`LastWriteTime` straight out of the directory enumeration without opening
anything, so a size+mtime fingerprint over a big tree stays in seconds. It
catches every write the implementer could plausibly make; it would not catch a
deliberate same-size, same-mtime forgery, which is not the threat model.

### `AGY_REQUIRE` is the fence's own alarm

A fingerprinter that returns nothing reports **clean**. That is the failure the
whole harness exists to prevent, so any surface listed here that comes back
empty makes `snapshot` refuse to arm — and a dispatch with no fence refuses to
run.

## After installing

The installer checks that `agy` and `node` are on PATH, arms and verifies the
fence, and runs the gates. Then:

```bash
bash ~/.claude/skills/agy-agents/scripts/selftest    # stubbed agy, no quota
```

Read `protocol.md` before running the first task.
