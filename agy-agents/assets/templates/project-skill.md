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
| Workspace | `{{WORKSPACE}}` |
| Ledger | `{{WORKSPACE}}/progress.md` |
| Shared context | `{{WORKSPACE}}/dispatch-context.md` |
| Gates | `{{GATES}}` |
| Dispatch | `.agy/dispatch <N>` |
| Review package | `.agy/review-pkg <BASE> task-<N>` |
| Implementer | `{{MODEL}}` |
| Reserve | `{{FALLBACK_MODEL}}` — weekly exhaustion only |

## The bridge

- **Out:** write the dispatch to `{{WORKSPACE}}/task-N-dispatch.md`, then run
  `.agy/dispatch N`.
- **Back:** the implementer writes `{{WORKSPACE}}/task-N-report.md` and commits.
  The run's own report lands in `{{WORKSPACE}}/logs/task-N-<stamp>.response.md`
  with the raw event stream beside it. Read all of it from disk.

Because the implementer reads the same disk you do, dispatches **point at
files, they do not quote them**. Never inline the shared context, the brief, or
prior-task history — all of it is already readable at a path.

**Never call `agy` directly.** Three of its behaviours make a broken run look
like a clean one. `.agy/dispatch` handles all three; its header documents each.

## Never write to the ledger during a dispatch

`{{WORKSPACE}}/progress.md` is a guarded surface. The fence snapshots it before
the run and compares it after, so a controller edit mid-run lands as a
violation and costs an investigation into your own change. Close the task
first, then write.

## Local rulings

Record decisions here as they are made, so they survive a `/clear`:

- {{date}} — {{ruling}}
