# Ledger — {{PROJECT}}

Plan: `{{PLAN_PATH}}`
Branch: `{{BRANCH}}`
Started: {{DATE}}

This file is the memory of the loop. The controller writes it; implementers and
reviewers never do — it is a guarded surface, and a dispatch that edits it is a
fence violation. Trust this ledger and `git log` over recollection, and trust
the repository over both.

**Do not write to this file while a dispatch is in flight.** The fence
snapshots it before the run and compares it after; a controller edit lands as a
violation and costs you an investigation into your own change.

---

## Environment

Record what a fresh session would otherwise have to rediscover: service
versions, database engine, where the toolchain lives, anything about the local
environment that can make a correct change look broken.

## Rulings

Every decision the controller made that is not derivable from the plan. One
line each, with the date. These are the answers to questions that will be asked
again.

## Calibration

How the implementer is actually performing on this plan's task sizing. Update
after every task:

- Clean through review in one round → the sizing holds.
- Two or more fix rounds, or drift into unlisted files → split the remaining
  tasks at their natural seams and tighten the scope fence.

---

## Task 1 — {{title}}

BASE: {{sha before the task}}
Model: {{model that implemented it}}
Commits: {{sha list}}
Gates: {{the actual result line, not "green"}}
Review: {{Approved | Changes requested}} — {{n}} Critical, {{n}} Important, {{n}} Minor
Fix rounds: {{0}}

Minors deferred to the whole-branch review:
- Task 1: minor (deferred): {{one-liner}}

Learned: {{anything about how the implementer handled this plan — this is what
makes the next brief better}}
