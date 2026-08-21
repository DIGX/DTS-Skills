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

## Planning dispatch — optional, and it inverts who reviews what

The plan is the artifact that carries most of the defects. In one project's
ledger across eleven tasks, almost every real defect lived in the plan's own
reference code and almost none in the implementer's transcription of it. The
protocol installs an independent reviewer for the implementation and, by
default, none for the plan — the controller writes it and the controller
reviews it, which is the one arrangement this protocol elsewhere forbids.

Dispatching the *planning* fixes that from the other side. The implementer
writes the plan; you review it. You stop being its author, so your review is
finally independent, and the plan gets read adversarially before any quota is
spent on tasks.

```bash
AGY_MODEL=gemini-3.1-pro-high .agy/dispatch --file .agy/work/<m>/plan-prompt.md
```

Copy `plan-dispatch.template.md` to `plan-prompt.md`, fill `{{SPEC}}` and
`{{MILESTONE}}`, and dispatch. `--file` is the right entry point: the label is
not `task-N`, so the report contract and the claims comparison correctly do not
apply to a run that produces a plan rather than code. The unfilled-marker
refusal still applies, so an unfilled `{{SPEC}}` cannot reach the planner.

Use a reasoning model, not a fast one. Planning is the one job in this protocol
where the model is choosing rather than transcribing, and it is also the job
whose defects are cheapest to catch and most expensive to miss.

**The plan is interfaces and prose, not implementation bodies.** This is what
makes the arrangement work at all. A plan carrying complete code *is* the
implementation, so reviewing it coarsely is rubber-stamping and reviewing it
properly costs what writing it would have — and the task dispatch that follows
degrades into transcription, which is where the delegation stops earning
anything. Interfaces and prose keep your review cheap and give the implementer
real work to do.

### Reviewing the plan

Four things, in this order. They are where plan defects actually live, and all
four are checkable without reading an implementation.

1. **Spec coverage** — walk the spec, point at the task that implements each
   requirement. List the gaps. This is the failure mode that survives to the end
   of a milestone.
2. **Interface consistency** — a name produced in Task 3 spelled identically in
   Task 7; nothing consumed before it is produced. Implementers see only their
   own task, so a rename between tasks is a build break nobody can see locally.
3. **Task independence** — each task separately testable and separately
   rejectable. A task with no independent deliverable will take its neighbour
   down with it in the fix loop.
4. **Exact values present** — no requirement reaching an implementer as a
   paraphrase. Every literal the spec fixes appears in the task that needs it.

Read Open Questions first and rule on every entry before dispatching Task 1. An
ambiguity the planner surfaced and you left unresolved is inherited by every
implementer on the plan, exactly like an unfilled marker.

What you are **not** doing is grading prose quality or rewriting to taste. If
you find yourself editing sentences, you have stopped reviewing.

## The cycle

1. **Record BASE** — `git rev-parse HEAD`. The review package needs it. Never
   use `HEAD~1`: tasks routinely land as several commits.

2. **Generate or write the brief** — `<workspace>/task-N-brief.md`. If the
   project has a plan with per-task sections, generate it from there.

3. **Write the dispatch** — `<workspace>/task-N-dispatch.md`, from
   `<workspace>/task-dispatch.template.md`. Read the brief first: your job here
   is the envelope around it — interfaces from earlier tasks, your rulings on
   anything ambiguous, and the scope fence.

   Read the brief **beside `dispatch-context.md`**, never on its own. The
   implementer reads both and treats both as binding, so a rule the context
   states and the brief contradicts is a task carrying two specifications with
   nothing to say which governs. The implementer does not stop on that: it
   picks one, silently, and the run comes back clean — the contradiction is
   invisible to every check in the loop, because each of them reads one
   document and finds it self-consistent. One such pair, disagreeing about
   whether proof scripts are committed, survived four dispatches. Your standing
   contradiction pass compares the brief against the *code*; this is the pass
   against the *context*, and it is the only one that catches this class.

   Resolve any disagreement before dispatching, by fixing a document rather
   than by ruling around it. If the brief is wrong, correct the brief. If the
   **context** is wrong, correct the context and note it in the ledger: it is
   inherited by every later task, so a contradiction resolved as a one-task
   ruling is one you meet again on N+1 — which is exactly how the same pair
   contradicted four briefs in a row.

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
   really executed them, run them again yourself:

   ```sh
   ( . .agy/config && bash $AGY_GATES )
   ```

   Not `.agy/gates` — that file exists only when the installer wrote a starter
   suite. In an adopted repo it bound `AGY_GATES` to the runner you already had
   and deliberately wrote no competing one, so the literal path is a `No such
   file or directory`. Sourcing the config is what makes the command work in
   both kinds of repo, and it is exactly what the wrapper does before its own
   gate run. `$AGY_GATES` is left unquoted for the same reason it is unquoted
   in `dispatch` — a runner may carry arguments.

   **Order this against step 8.** Steps 5 and 6 spend the controller's budget
   and step 8 spends it on the reviewer — the same pool, with the reviewer
   drawing from it last, when it is thinnest. So the harder the controller
   works, the less likely its own review can run. Nothing in step 7 needs step
   5 or 6: the package is built from `BASE..HEAD` alone. Read the gate result
   the dispatch already captured — free, already on disk, and enough to stop
   you spending a reviewer on a red gate — then package, dispatch the reviewer,
   and do the rest of this step and step 6 while it runs. Background dispatch
   makes that literal where the harness offers it; where it does not, dispatch
   first anyway, because the point is the reviewer's position in the budget and
   not the wall clock.

   What moves after the dispatch is the open-ended half: your own gate re-run,
   and the contract's rule about re-executing every command the report pastes
   as proof. Reported from the field after three consecutive reviewer losses in
   one session. Three is not proof the structure caused them — an account near
   its weekly cap produces the same pattern — but the structure is real and the
   reordering costs nothing either way.

6. **Read the actual diff** — `git log BASE..HEAD` and the changed files. Not
   the report. Check for scope drift: files touched that the dispatch did not
   name. Silent scope expansion is the drift this workflow exists to catch.

7. **Package the review** — `.agy/review-pkg <BASE> task-N`.

8. **Dispatch the reviewer** — a fresh Claude subagent, per the contract below.
   Do this before the open-ended half of steps 5 and 6, not after them; step 5
   says why. When it returns, check the file it wrote before reading a word of
   it:
   `.agy/review-pkg --check <workspace>/task-N-review.md --ac <criteria the
   brief issued>`. Non-zero means there is no review here yet, whatever is on
   disk. The line it prints on success is the one that goes in the ledger.

   If the reviewer cannot be dispatched at all — quota exhausted, model outage,
   the harness refuses — that is **not** this step failing open. Go to *When the
   reviewer cannot run*, below, and hold the task. Reported from the field as a
   missing path, by a controller that had already handled it correctly: the
   clause existed and it still was not found from here, which is why this
   pointer exists.

9. **Fix loop** — see below. It comes back here: the loop is a detour inside
   this step, and a task that leaves it still has step 10 to do.

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
     Then read it against `dispatch-context.md`: anything the two documents
     say differently is a finding here, whichever one turns out to be right.
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
  ledger, and re-dispatch if the landed work is now wrong. The same holds for
  a brief that contradicts the context, with one addition — fix the document
  that is actually wrong. Correcting the brief when the context was the faulty
  one leaves every later task inheriting the fault.
- **Grade the acceptance criteria as claims to falsify, not as work to
  summarise.** Left to itself an implementer fills that table in as a report of
  what it did: every row restates the action it took, so a row reads ✅ because
  the work happened, not because the criterion holds. The reviewer must take
  each criterion and try to break it — name the input or state under which it
  would fail, then check whether the code survives that. A criterion nobody
  attempted to falsify is not satisfied, it is **unverified**, and it is
  reported ❌ with what a test of it would take. This is the same rule the rest
  of the harness runs on: an absent measurement is never a pass.
- **A fault injection proves something only if you predicted what it would
  break.** The bullet above says to try to break the criterion. This one is
  about how to read the result, and it is where the technique quietly stops
  working. Injecting a fault and then searching the output for `FAIL` — or for
  a marker string anywhere in it — certifies nothing: a suite of any size has
  other reasons to go red, so a fault that *cannot fire* looks exactly like one
  that fired and was caught. Reaching for an output-wide grep is the default
  move, and it has been the default move of every harness that has tried this
  here.

  So name the targets first. Before running the mutated suite, write down the
  exact assertion labels the fault should turn red. Run it. Compare the two
  sets, and read each mismatch as its own answer:

  - **predicted red, observed green** — the assertion is vacuous. It does not
    test what its label claims. That is a defect in the test, not a detail.
  - **observed red, not predicted** — the blast radius is wider than the fault.
    Usually a cascade: one fixture feeding later assertions, which then fail
    for a missing precondition rather than for the fault. Those assertions are
    still unpinned. Pin them with a second, narrower mutation.
  - **the two sets match** — and only then — the assertions are falsified.

  Worked example, from this repo's own 1.8.6 work. A mutation that stopped the
  installer reading the co-author out of an existing config turned four
  assertions red. "Did it go red?" says yes, and the precedence assertions get
  filed as pinned — but they were green, and they were green because the
  mutation had disabled a *different* branch that happened to leave the config
  untouched. Inverting the precedence directly turned five other assertions
  red. The two sets barely overlap, and only the second mutation said anything
  about the rule that was supposedly under test.
- **Reconcile the acceptance-criteria rows against the brief, and say the
  count.** The failure above is an optimistic row; this one is a row that is not
  there at all. A task issued with twelve criteria came back reporting eight,
  and among the four that had quietly gone was the one marked non-negotiable.
  An optimistic table is still a checklist — wrong, but auditable. A table that
  can lose rows is not a checklist at all, because nothing in it shows the
  reader what is missing. So tell the reviewer how many criteria the brief
  issued, and have it reconcile row for row before reading any of them: a count
  that does not match the brief is a finding on its own. Dropping a row is not
  an available move. A criterion that was not met is reported **NOT MET, with a
  reason** — which is information, where a deleted row is the absence of it.
- Tell it to write the full review to `<workspace>/task-N-review.md` and reply
  with only the verdicts, counts, and one line per Critical/Important finding.
- **Have it write each finding to that file as it finds it, and the verdict
  table last.** A reviewer that composes the whole review in its head and
  writes it at the end loses all of it when it is killed — and the reviewer is
  the likeliest agent in the cycle to be killed, because it runs last on the
  thinnest budget. The natural order is also the worst one: the verdict table
  is the cheapest section to produce and the findings are the dearest, so
  writing top to bottom guarantees that the part which survives is the part
  with no information in it. Invert it. A file holding four findings and no
  terminator is still rejected by `--check`, exactly as before — but the fix
  loop can start from those four, and a re-dispatched reviewer can be told what
  is already covered instead of buying the whole review a second time.
- **Demand a terminator, and check for it mechanically.** The review's last
  line, nothing after it:

  ```
  REVIEW-END brief=<ok|findings> spec=<pass|fail> quality=<approved|changes> ac=<met>/<total>
  ```

  A reviewer killed mid-write — session limit, dispatch failure — leaves a file
  that reads exactly like a review which found nothing. Left to itself a
  reviewer writes the verdict table before the findings, so what survives is a
  complete-looking table with every row MET and no findings section, and the
  controller's only signal was the presence of a table. That is precisely what
  the truncated file has. The bullet above asks for the opposite order; this
  one is what catches a reviewer that did not comply, which is the half of the
  pair a machine can check.
  This is flaw #20's shape one level up: **an unfinished artefact must not
  borrow the vocabulary of a finished one.**

  So the finished state has a mark that a partial file cannot accidentally
  carry, and `.agy/review-pkg --check <file> --ac <n>` tests for its absence and
  exits non-zero. Run it before reading the review. Three more failures fall out
  of the same line on the way past, all arithmetic rather than judgement: a spec
  `pass` reported alongside criteria that were not met — there is no third
  verdict for a criterion, so those cannot both be true; more criteria met than
  issued; and a reconciled total that does not match the count the brief handed
  out. Take its output as the ledger's verdict line — a review you did not check
  is one you have no line to record.
- **Declare authorship honestly** — say which code came from the implementer and
  which you wrote yourself, and that both are in scope on the same terms.
  Controller-authored code fails review at a similar rate; hiding it wastes the
  reviewer.
- Do **not** pre-judge. If the prompt you are writing contains "do not flag",
  "at most Minor", "the plan chose", "is NOT a defect", or "flag only if" —
  stop. Let the reviewer raise it, then adjudicate it in the loop. The last two
  are the ones that get written by accident: they arrive dressed as helpful
  context about deliberately preserved behaviour, and a conditional licence to
  flag ("only if undocumented") is still a verdict the controller reached before
  the reviewer looked.
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

### Size the review to a session, not to the task

Reported from the field, twice on the same project: a milestone lost three
consecutive tasks because each reviewer hit its session limit mid-review. The
section below accounts for that correctly but treats it as an accident. It is
not. It is arithmetic.

Count what this contract asks a reviewer to do: read the diff, the brief, the
report, `dispatch-context.md` and the review package; **re-execute** every
command the report pastes as proof; then produce three verdicts with `file:line`
citations and a reconciled criteria table. On a task with a two-thousand-line
diff that is most of a session's budget by itself, and three of them back to
back is reliably over it. Nothing above is safe to cut, either — re-execution is
the only check in the whole harness that looks inside a report, so the expensive
half is the load-bearing half.

So the review is a unit of work with a budget, and the budget is what sizes it.

- **One full review per reviewer session.** Do not queue three and expect the
  third to survive. A reviewer killed at eighty percent has spent everything it
  read and returns a file the `REVIEW-END` check will reject — the worst trade
  available.
- **Size the task by its review, not by its implementation.** *Sizing tasks*
  below asks whether a task has one independently testable deliverable. Add a
  second question: can one reviewer read the resulting diff and re-run its
  proofs inside a single session? A task that will produce well over a thousand
  diff lines needs splitting for that reason alone, however clean its
  deliverable is. `.agy/review-pkg` prints the package's diff size and says so
  when it crosses the line, because a controller that has to estimate this by
  eye will estimate it optimistically every time.
- **Scope the package when the task's risk is narrow, and say that you did.**
  Not every task earns the full contract. One that touches only infrastructure —
  no product source, no interface a later task consumes, no surface the user
  sees — can be reviewed from a shortened package: diff, brief, and acceptance
  criteria. Brief integrity and spec compliance are still demanded; what drops
  is the whole-file quality sweep over code the task did not touch. State the
  scoping in the dispatch and record it in the ledger as `reviewed (scoped:
  <why>)`. An unannounced short review is indistinguishable from a lazy one, and
  the ledger is where that distinction has to survive.
- **Never scope by shortening the verdicts.** All three still come back, the
  criteria table still reconciles against the brief, and the `REVIEW-END` line
  still terminates the file. What shrinks is what the reviewer *reads* — never
  what it is asked to conclude. A review with two verdicts is not a cheaper
  review, it is an incomplete one, and the check will reject it.

Sequencing follows from the same budget. Reviews are the tail of every task, so
a milestone that dispatches implementers as fast as they finish will stack
unreviewed tasks behind a reviewer that cannot keep up — which is the state the
field report describes, and which the protocol elsewhere forbids outright. When
the reviewer is the scarce resource, it sets the pace of the milestone: hold the
next task rather than run ahead of the last review.

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
   run>; retry after <time, or the condition that clears it>`. A held task is a
   visible state, not a quiet gap.

   The retry field is not decoration. A session that resumes tomorrow reads the
   ledger, not this session's transcript, and `quota` tells it only that
   something was wrong once — where `retry after 8:10am (Asia/Kolkata)` tells it
   what to do and when. Write the wall-clock time with its zone when you have
   one, and the condition when you do not: *retry after the weekly window
   resets*, *retry once the harness allows subagents again*. Without it, HELD
   and "review found nothing" are the same entry to whoever arrives next.
3. Tell the user what is on disk — commits, gate results, whether the diff
   stayed in scope — and that it is unreviewed.
4. Wait for a reviewer to become available. That is the only exit.

You may state your own reading of the diff while it is held. Label it as the
controller's opinion and never let it stand in the ledger where a verdict goes.

**A reviewer that was killed is not a reviewer that cannot run.** Check this
before holding anything. A budget-killed subagent can be resumed from its own
transcript, which still holds everything it read — see *When a run dies
mid-task* for when resuming is worth its cost. And check the disk first: a
reviewer told to write each finding as it finds it leaves those findings in
`<workspace>/task-N-review.md` and loses only the verdict table, so what looks
like a dead review is often a review missing its last section. Dispatching a
fresh reviewer there pays the whole read cost again to produce something that
already exists, and HELD records a gap where there is a file. Hold only when
there is no reviewer to resume and nothing on disk to finish.

**Whether the next task may dispatch while this one is held.** It may — the
fence guards surfaces, not agents, so the only question is where each one
writes. The workspace is pruned from every guarded directory, so a reviewer
writing `<workspace>/task-N-review.md` during someone else's dispatch is clean.
Two things are not. The ledger is guarded as a *file*, so being inside the
workspace does not exempt it — that is the same rule as *Never write to the
ledger during a dispatch*, and it binds the held task's bookkeeping too. And
anything under `docs/`, `.claude/`, or the rest of `.agy/` is a guarded
directory in full. So: let the held reviewer write only into the workspace, and
leave the ledger alone until both tasks close. If it needs to put a note
anywhere else, wait for the dispatch to finish instead. A violation here is
expensive out of proportion to the note — it lands on the *implementer's*
verdict, and you spend the investigation proving your own bookkeeping caused
it.

## Fix loop

Five rounds maximum.

- **Rounds 1–3 go back to the implementer**, in its existing thread — it still
  has the task's context, so resume rather than start cold: write the correction
  to `<workspace>/task-N-fixM.md` and run
  `.agy/dispatch --continue --file <that file>`. State plainly: what was
  required, what it actually did, what is missing, what to change. Nothing else
  — a correction is not a re-brief.
- **That thread only exists until the next task dispatches.** `agy --continue`
  resumes the last conversation *globally*; the flag is passed through verbatim
  and there is no per-task selector. So run the fix rounds before the next task
  goes out. Once one has, the thread you want is unreachable: drop `--continue`
  and re-brief cold. `.agy/dispatch` records the last label it sent and refuses
  a mismatched `--continue` rather than dropping your correction into a
  conversation that believes it just finished something else — a warm
  implementer holding the wrong context is worse than a cold one holding none.
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
  fix introduce anything new". It ends with the same `REVIEW-END` line and is
  checked the same way, with one substitution: on a scoped re-review `ac` counts
  the **findings sent back**, not the brief's acceptance criteria, so `--ac`
  takes the number of findings you handed it. The field means "of the things
  this review was asked to reconcile, how many came back met" either way, and a
  re-review that answers three of five findings is the same defect as a table
  that lost rows.

**When the loop closes — clean re-review, or findings adjudicated at round
five — go back to step 10 and close the task.** The loop is a detour inside
step 9, not the end of the cycle. Say so out loud, because the text does not
carry you there: the section ends here, and the next heading is a different
subject entirely. A controller that resolves the last finding and stops has
finished the work and written down nothing about it — no commits, no gate
results, no deferred Minors, no rulings. That is the most expensive way to
finish a task, because it is invisible: the code is right, the review passed,
and the next controller has no record that any of it happened.

Adjudication is the last thing you decide. It is never the last thing you do.

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

**And size it by the review it will need, not only by the work it contains.**
A task can have exactly one independently testable deliverable and still be too
large for anyone to grade — see *Size the review to a session, not to the task*
above. `.agy/review-pkg` prints the number and warns when it crosses the line,
but by then the task is written; the cheap moment to catch it is here.

## Mirror every fix into the plan

When a review finding, or the implementer, exposes a defect in the plan's own
reference code, fix the plan in the same breath — otherwise every later task
inherits it and the plan stops being reproducible.

## When a run dies mid-task

**A Claude subagent (reviewer) killed by a session limit** — routine, not a
failure:

1. Check what is on disk: `git status --short`, and whether the review exists.
2. Run the gates yourself: `( . .agy/config && bash $AGY_GATES )`.
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
2. `( . .agy/config && bash $AGY_GATES )` — what actually passes.
3. Read `task-N-report.md` — how far the incremental log got.

Then send a correction naming the remaining steps only. If it has stopped early
twice on the same task, treat that as a sizing signal and split the task rather
than nudging a third time.

## Never write to the ledger during a dispatch

`<workspace>/progress.md` is a guarded surface. The fence snapshots it before
the run and compares after, so a controller edit mid-run lands as a violation
and costs an investigation into your own change. Close the task first, then
write.
