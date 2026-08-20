# PLANNER TASK — {{PROJECT}}, {{MILESTONE}}

**Objective:** turn the spec named below into an implementation plan that a
different agent can execute one task at a time, without ever reading the spec.

**Read these first, in order — both are binding:**
1. `{{WORKSPACE}}/dispatch-context.md`
   Global constraints, environment, commands, the definition of done. Every
   task you write inherits this file; do not restate it per task, and do not
   contradict it.
2. `{{SPEC}}`
   What is being built. Where the spec and a global constraint disagree, stop
   and say so in the plan's Open Questions — do not silently pick one.

**Write exactly one file:** `{{WORKSPACE}}/plan.md`. Touch nothing else. You are
not implementing anything, and a plan that arrives alongside modified source is
rejected on sight.

## What a task looks like

Interfaces and prose, **not implementation bodies**. The implementer that
receives your task is a capable engineer who does not know this codebase; your
job is to remove every ambiguity about *what* and leave *how* to them.

Each task gets:

- **Files** — exact paths, marked Create / Modify / Test.
- **Interfaces** — what it consumes from earlier tasks and what later tasks may
  rely on, as exact signatures: names, parameter and return types, error cases.
  This is the section that makes tasks independent. An implementer sees only
  its own task, so a name that appears in two tasks must be spelled identically
  in both, and every name a later task uses must be *produced* by an earlier one.
- **Behaviour** — what the code must do, in prose, including the edge cases that
  matter and the ones that do not.
- **Exact values** — every literal the implementation must match: magic strings,
  numbers, formats, file names, exit codes, error text. Copy them verbatim from
  the spec. A near-miss is a miss, and this is the only place they appear.
- **Tests** — what must be proven, and what a passing test would have to do to
  be lying. Name the cases; do not write the test bodies.
- **Acceptance criteria** — numbered, each one checkable by reading the diff or
  running a command. "Works correctly" is not a criterion.

Do **not** include:

- implementation bodies, or code blocks longer than a signature or a literal
- restatements of `dispatch-context.md`
- history, rationale for the plan itself, or notes to the reader
- any task that cannot be tested on its own

## Sizing

A task is the smallest unit worth a fresh reviewer's gate. Fold setup, config
and docs into the task whose deliverable needs them. Split only where a reviewer
could sensibly reject one task while approving the one beside it. If a task has
no independently testable deliverable, it is not a task — merge it.

## Required structure

```
# {{PROJECT}} — {{MILESTONE}} implementation plan

## Goal            one sentence
## Architecture    2-3 sentences: the approach, and what it rejects
## File structure  every file the plan creates or modifies, one line each on
                   what it is responsible for
## Global constraints
                   only what the spec adds beyond dispatch-context.md
## Task 1: <name>  ... the sections above
## Task 2: <name>
...
## Open questions  anything the spec left genuinely ambiguous, each with the
                   two readings and which one you would pick. Do not resolve
                   them silently; this section is read before any dispatch.
```

## How this is graded

The controller reviews this plan before a single task is dispatched, and reviews
it for four things:

1. **Spec coverage** — every requirement in the spec maps to a task.
2. **Interface consistency** — a name produced in Task 3 is spelled the same in
   Task 7, and nothing is consumed before it is produced.
3. **Task independence** — each task is separately testable and separately
   rejectable.
4. **Exact values present** — no requirement reaches an implementer as a
   paraphrase.

Those four are where defects in plans actually live. An Open Questions section
that honestly names a hard ambiguity is worth more than a plan that guessed.

## Report

Write your summary to `{{WORKSPACE}}/plan-report.md`: the task count, anything
in the spec you could not place in a task, and every assumption you made that
the spec did not license. Return only a one-line status.
