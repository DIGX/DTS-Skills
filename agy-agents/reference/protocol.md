# The Claude Manager + Implementer protocol

One pass of the loop, for a repository that has `.agy/` installed.

**Claude plans, adjudicates and verifies. The Antigravity CLI implements. A
fresh Claude subagent reviews.** Delegating implementation does not delegate
review — the reviewer is the entire quality mechanism, and it stays with Claude.

Trust the ledger and `git log` over memory; trust the repository over both.

## The bridge

`.agy/dispatch N` is the whole bridge. It runs the implementer headlessly, so
no human is in the loop as a copy-paste bus.

- **Out:** write the dispatch to `<workspace>/task-N-dispatch.md`, then run
  `.agy/dispatch N`.
- **Back:** the implementer writes `<workspace>/task-N-report.md` and commits.
  The run's own report lands in `<workspace>/logs/task-N-<stamp>.response.md`
  with the raw event stream beside it. Read all of it from disk.

Because the implementer reads the same disk you do, dispatches **point at
files, they do not quote them**. Never inline the shared context, the brief, or
prior-task history — all of it is already readable at a path. This is what keeps
a dispatch cheap enough to write in full.

**Never call `agy` directly** — see `dispatch-traps.md`. `.agy/dispatch` also
runs with `--dangerously-skip-permissions`, which is only tolerable because the
tripwire fences the run. If the fence will not arm, the dispatch refuses to
start. Do not work around that.

It refuses on one more thing before it starts: a `{{marker}}` left in the shared
context or in the brief you just wrote. Both are copied from templates, and an
unfilled line in `dispatch-context.md` is inherited by every implementer and
every reviewer on the plan — they read `{{Language/runtime floor}}` as no floor
at all, and no gate can enforce a rule nobody wrote down. Fill it rather than
setting `AGY_ALLOW_UNFILLED=1`.

## The cycle

1. **Record BASE** — `git rev-parse HEAD`. The review package needs it. Never
   use `HEAD~1`: tasks routinely land as several commits.

2. **Generate or write the brief** — `<workspace>/task-N-brief.md`. If the
   project has a plan with per-task sections, generate it from there.

3. **Write the dispatch** — `<workspace>/task-N-dispatch.md`, from
   `<workspace>/task-dispatch.template.md`. Read the brief first: your job here
   is the envelope around it — interfaces from earlier tasks, your rulings on
   anything ambiguous, and the scope fence.

   Long is fine. It costs one write, and unlike a pasted prompt it never
   re-enters your context on later turns.

4. **Dispatch** — `.agy/dispatch N`. It arms the fence, runs the implementer,
   parses the event stream, re-checks the fence and runs the gates, then prints
   one verdict block: `run` / `fence` / `landed` / `log` / `gates`. Anything
   other than clean/clean/green stops the cycle here. Read logs from the `log`
   line in *that* block rather than the header's — on a quota fallback the
   header names the attempt that failed, not the one that did the work.

   `landed` is the line that says whether anything was produced. `run clean`
   grades the session; a run that wrote no code grades identically to one that
   implemented the task. `landed NOTHING` beside a confident report means read
   the diff before you believe a word of it. `landed NOT COMMITTED` fails the
   run: the brief requires the commit, so changes left in the tree are an
   unfinished task — re-dispatch it rather than committing them yourself, or
   the ledger records your commit for the implementer's work.

   `clean, but WATCHDOG-KILLED` and `clean, but the SESSION DIED before its
   result event` are both trap 4 and both still pass: the run was stopped, so
   its status and exit code describe how it ended. The fence, the gates and a
   report written *during this run* are the whole verdict there.

   Two lines in that block mean the report itself is not to be trusted, rather
   than that a step failed:

   - **`BYPASS`** — a command was denied and then ran anyway under another
     name (`cmd /c npm install` against a rule denying `npm install`). The
     boundary held and the implementer walked around it. The work described in
     the report did happen, which is what makes this worse than a plain
     denial: nothing in the report reads as wrong. Fix the boundary and
     re-run. Do not review the diff on the assumption the rest is sound.
   - **`claims CONTRADICTED`** — a number the report asserts disagrees with
     the same quantity the gates measured. This is a warning, not a gate
     failure, and it exits 0 on its own. It is also the one signal that
     catches a report describing work it did not do, so never accept a task
     while it is showing. Reconcile it or re-run.

5. **Verify the gates yourself.** The dispatch already ran them — read *its*
   output, not the implementer's claim about it. This is the most load-bearing
   step in the cycle: the implementer's claim is the least verifiable link in
   the chain and you cannot see its reasoning. A green report over a red gate is
   the expected failure mode, not a surprise. If you are ever unsure the run
   really executed them, run `.agy/gates` again yourself.

6. **Read the actual diff** — `git log BASE..HEAD` and the changed files. Not
   the report. Check for scope drift: files touched that the dispatch did not
   name. Silent scope expansion is the drift this workflow exists to catch.

7. **Package the review** — `.agy/review-pkg <BASE> task-N`.

8. **Dispatch the reviewer** — a fresh Claude subagent, per the contract below.

9. **Fix loop** — see below.

10. **Close the task** — append to the ledger: commits, gate results, every
    Minor finding as `Task N: minor (deferred): <one-liner>`, any ruling you
    made, and anything learned about how the implementer handles this codebase.
    Update the project's status signpost. Mark the todo complete.

## The reviewer contract

The reviewer is a **fresh Claude subagent that never saw the implementation
happen**. Do not delegate this to the implementer and do not do it yourself in
the main session — the agent that wrote the brief cannot independently grade
work against it. This is not ceremony. Independent review has caught an
initialiser that silently did nothing under the integration suite while every
gate stayed green, which would have quietly broken every later task.

Dispatch it pointing at the shared context, the brief, the report and the
review package. Then:

- Demand **three** verdicts, in this order:
  1. **Brief integrity** — do the brief's stated invariants actually follow from
     its stated rules? Not "is the brief clear", but: take the rules it lays
     down, follow them, and see whether they produce the property it claims.
  2. **Spec compliance** — ✅/❌, walked requirement by requirement with
     `file:line` citations.
  3. **Code quality** — Approved / Changes requested, findings as Critical /
     Important / Minor.
- **Brief integrity comes first because it is the one defect this loop cannot
  otherwise see.** A brief whose invariants do not follow from its rules
  produces an implementer that complies exactly, a reviewer that confirms
  compliance, green gates and a clean fence — every check passes and the defect
  is in the specification the whole task was graded against. The controller
  wrote that brief, so the controller is the last agent who can catch it, which
  is another way of saying nobody can. Ask the reviewer explicitly, every time:
  a reviewer told only to check the diff against the brief will read the brief
  as ground truth, because from where it sits that is exactly what it is.
  A finding here is **adjudicated by the controller, not fixed by the
  implementer**: correct the brief, record the correction as a ruling in the
  ledger, and re-dispatch if the landed work is now wrong.
- Tell it to write the full review to `<workspace>/task-N-review.md` and reply
  with only the verdicts, counts, and one line per Critical/Important finding.
- **Declare authorship honestly** — say which code came from the implementer and
  which you wrote yourself, and that both are in scope on the same terms.
  Controller-authored code fails review at a similar rate; hiding it wastes the
  reviewer.
- Do **not** pre-judge. If the prompt you are writing contains "do not flag",
  "at most Minor", or "the plan chose" — stop. Let the reviewer raise it, then
  adjudicate it in the loop.
- **Re-execute any output the report pastes as proof; do not read it.** This
  costs seconds and is the only check that distinguishes real output from
  output that was tidied. Every number in a hand-trimmed block can be true
  while the block lies about what ran — a suite quietly reduced to the cases
  that pass leaves a green gate, a clean fence, a `SUCCESS` verdict and a
  report full of accurate figures. Nothing else in this harness looks inside a
  report.
- The exception is the gate suite itself: `.agy/dispatch` runs it and keeps its
  own copy at `<log>.gates.log`, so that output is already independently
  evidenced and the claims check already compares the report against it. Every
  *other* command a report cites — a one-off script, a fault injection, a
  targeted test run — has no such capture. Re-run those.

### When the reviewer cannot run

A subagent may be unavailable: the harness forbids it, the session budget will
not carry another one, it dies on dispatch. The cheapest way out is to read the
diff carefully yourself and call it reviewed.
**Never substitute yourself for the reviewer.**
You wrote the brief; grading work against your own brief is not
review, and the result is worse than no review because the ledger will record
one that never happened.

The task is **HELD** instead:

1. Leave the task open. Do not close it, do not start the next one.
2. Record it: `Task N: HELD — reviewed by nobody; <why the reviewer could not
   run>`. A held task is a visible state, not a quiet gap.
3. Tell the user what is on disk — commits, gate results, whether the diff
   stayed in scope — and that it is unreviewed.
4. Wait for a reviewer to become available. That is the only exit.

You may state your own reading of the diff while it is held. Label it as the
controller's opinion and never let it stand in the ledger where a verdict goes.

## Fix loop

Five rounds maximum.

- **Rounds 1–3 go back to the implementer**, in its existing thread — it still
  has the task's context, so resume rather than start cold: write the correction
  to `<workspace>/task-N-fixM.md` and run
  `.agy/dispatch --continue --file <that file>`. State plainly: what was
  required, what it actually did, what is missing, what to change. Nothing else
  — a correction is not a re-brief.
- **Rounds 4–5 escalate to Claude.** Two failed rounds on the same finding means
  the task was mis-sized, or the finding needs judgment the implementer is not
  applying. Fix it yourself and declare the authorship to the reviewer.
- **Never let a third round repeat the second's instruction.** If the same thing
  was missed twice, the instruction is the problem. Change the strategy, narrow
  the task, or take it over.
- **Minor findings never enter the loop.** Record each in the ledger and point
  the final whole-branch review at that list.
- **A finding that contradicts the plan's text is the human's call.** Present
  the finding beside the plan text and ask which governs. Exception: when the
  contradiction is *internal to the plan* and its global-constraints section
  covers it, the constraint governs by the plan's own stated precedence — fix
  it, mirror it into the plan, and tell the user.
- After fixing, package the fix diff with `.agy/review-pkg <prev> task-N-rM` and
  send a **scoped** re-review: only "are these findings resolved, and did the
  fix introduce anything new".

## Sizing tasks

A plan written for a Claude subagent implementer is not automatically sized for
this one. Do not theorise about the difference — calibrate on real tasks and
record the result in the ledger:

- Clean through review in one round → keep the sizing.
- Two or more fix rounds, or drift into unlisted files → split the remaining
  tasks at their natural seams and tighten the scope fence.

Signals that a task is too big for one dispatch: more than ~4 files in scope,
more than one new class plus its tests, or any step whose correctness depends on
a plan section the brief only summarises.

**Raise review scrutiny, don't lower it, when a large task comes back unusually
fast.** Speed is not evidence of correctness, and here it has repeatedly meant
the opposite.

## Mirror every fix into the plan

When a review finding, or the implementer, exposes a defect in the plan's own
reference code, fix the plan in the same breath — otherwise every later task
inherits it and the plan stops being reproducible.

## When a run dies mid-task

**A Claude subagent (reviewer) killed by a session limit** — routine, not a
failure:

1. Check what is on disk: `git status --short`, and whether the review exists.
2. Run `.agy/gates` yourself.
3. **Decide before resuming.** A killed subagent is not lost — it can be
   resumed from its own transcript, which still holds everything it read.
   Resuming reloads that transcript (~120–150k tokens), so resume when what
   remains needs the judgment it is carrying.

   What you may finish yourself is *mechanical remainder of a review that
   already reached its verdicts* — writing up findings it had already stated,
   filing them, packaging the fix. Producing a verdict is never mechanical,
   however obvious the diff looks. If it died before verdicts, the choice is
   resume or HELD.
4. If you do resume, send exactly what you verified — gate output, file list,
   HEAD sha — and tell it explicitly not to re-run any of it.

**The implementer stalls, drifts, or stops early** — it keeps its own thread
history, so recovery is cheaper: `.agy/dispatch --continue --file <correction>`.
But first establish what actually landed, from disk, not by asking it:

1. `git status --short` and `git log BASE..HEAD` — what was committed.
2. `.agy/gates` — what actually passes.
3. Read `task-N-report.md` — how far the incremental log got.

Then send a correction naming the remaining steps only. If it has stopped early
twice on the same task, treat that as a sizing signal and split the task rather
than nudging a third time.

## Never write to the ledger during a dispatch

`<workspace>/progress.md` is a guarded surface. The fence snapshots it before
the run and compares after, so a controller edit mid-run lands as a violation
and costs an investigation into your own change. Close the task first, then
write.
