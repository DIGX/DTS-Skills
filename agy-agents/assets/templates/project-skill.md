---
name: agy-task-cycle
description: Use when implementing, reviewing, or closing any planned task in {{PROJECT}} — this project delegates implementation to the Antigravity CLI and keeps review with a fresh Claude subagent. Covers writing the dispatch, running the fence and gates, packaging the review, the fix loop, and closing the task in the ledger.
---

# {{PROJECT}} task cycle

This project runs the **Claude Manager + Implementer protocol**. Claude plans,
adjudicates and verifies; the Antigravity CLI implements; a fresh Claude
subagent reviews. Adopted {{DATE}}.

**Read the protocol before your first cycle in a session:**
`{{PROTOCOL}}`

That file is the loop, the fix-loop rules, the reviewer contract and the
sizing rules. This file is only what is specific to this project.

## Project bindings

| | |
|---|---|
| Config | `.agy/config` — where the work lives, and the authority on it |
| Workspace | `$AGY_WORKSPACE` — `.agy/work/<milestone>/`; **it moves** |
| Ledger | `$AGY_LEDGER` — `$AGY_WORKSPACE/progress.md` |
| Shared context | `$AGY_WORKSPACE/dispatch-context.md` |
| Gates | `{{GATES}}` |
| Dispatch | `.agy/dispatch <N>` |
| Review package | `.agy/review-pkg <BASE> task-<N>` |
| Implementer | `{{MODEL}}` |
| Reserve | `{{FALLBACK_MODEL}}` — weekly exhaustion only |

The workspace is the one binding this file deliberately does **not** spell out.
It carries the milestone slug, so it moves — and a copy of it written here at
install time keeps looking authoritative long after it stops being true. Every
script reads `.agy/config`; only this file would be reading a memory of it. So
resolve it from the config once per session, before you touch the ledger:

```bash
( . .agy/config; printf 'workspace  %s\nledger     %s\ngates      %s\n' \
	"$AGY_WORKSPACE" "$AGY_LEDGER" "$AGY_GATES" )
```

Advancing a milestone is one command from the repo root, and it repoints the
config as well as scaffolding the new workspace:

```bash
bash ~/.claude/skills/agy-agents/scripts/install --milestone m2 --dry-run
```

## The bridge

- **Out:** write the dispatch to `$AGY_WORKSPACE/task-N-dispatch.md`, then run
  `.agy/dispatch N`.
- **Back:** the implementer writes `$AGY_WORKSPACE/task-N-report.md` and commits.
  The run's own report lands in `$AGY_WORKSPACE/logs/task-N-<stamp>.response.md`
  with the raw event stream beside it. Read all of it from disk.

Because the implementer reads the same disk you do, dispatches **point at
files, they do not quote them**. Never inline the shared context, the brief, or
prior-task history — all of it is already readable at a path.

**Never call `agy` directly.** Three of its behaviours make a broken run look
like a clean one. `.agy/dispatch` handles all three; its header documents each.

## Never write to the ledger during a dispatch

`$AGY_LEDGER` is a guarded surface. The fence snapshots it before the run and
compares it after, so a controller edit mid-run lands as a violation and costs
an investigation into your own change. Close the task first, then write.

## Local rulings

Decisions made in this project, recorded as they are made so they survive a
`/clear`. One line each, newest last, in the form `2026-01-31 — the ruling`:

- (none yet — replace this line with the first one)
