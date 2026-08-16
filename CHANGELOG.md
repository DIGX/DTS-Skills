# Changelog

Notable changes to the skills in this repository. Each skill carries its own
`version:` in its `SKILL.md` frontmatter.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## agy-agents

### [1.8.6] — 2026-08-16

A new control shipped to every repository running the harness, and reached
none of them. That is the whole release: the gap between "the skill has it"
and "this repository has it".

#### Added
- **The installer adds missing keys to a config it keeps.** `.agy/config` is
  the project's file and re-installing has always kept it — but the four
  scripts are refreshed every time, so 1.8.4's trailer check arrived in old
  repositories with no `AGY_COAUTHOR` for it to read. An unset value means
  off. The check landed and did nothing, which is worse than not shipping it:
  the repository now looks protected and is not.

  A kept config is compared against the one this version would write, and any
  key yours lacks is appended in a dated block, carrying the comment paragraph
  that explains it — a control that arrives without its paragraph is a line
  somebody deletes later for looking like noise. Nothing above the block is
  read for its value, rewritten, or reordered. Appending is safe on its own
  terms too: every binding is `${VAR:=…}` or `${VAR=…}`, so an earlier value
  wins over anything below it, and a deliberate edit survives even if the name
  match were wrong.

  Adding `AGY_COAUTHOR` turns the trailer check on, and dispatch then refuses
  until the context names the same address. Correct — and, arriving on the
  next dispatch in a repository where nothing looked like it changed,
  indistinguishable from a broken harness. So the run that causes it says so,
  and either rewrites the template's `Co-Authored-By:` line or prints the line
  to paste.

- **`--coauthor` now works on a repository that already has one.** The
  migration only *adds* keys, which left the documented way to change this
  address doing nothing on the only repositories that needed it — the same
  trap one level up. The flag repoints `.agy/config` and the milestone
  context in place, then re-sources the config to confirm the value the
  harness will actually resolve. If it does not match, the installer says it
  could not repoint rather than reporting a change it did not make.

- **Install-time precedence, most specific first:** `--coauthor`, then
  `.agy/config`, then `AGY_COAUTHOR` in the environment, then the shipped
  default. An existing config outranks the environment deliberately — a
  maintainer with `AGY_COAUTHOR` exported, installing into somebody else's
  repository, must not rewrite that project's shared context to name their own
  mailbox. A milestone advance re-scaffolds `dispatch-context.md` from the
  resolved value, so without this rule 1.8.5 would have manufactured exactly
  the config/context drift it added a refusal for. `--force` regenerates the
  config but does not silently move the credit; only `--coauthor` does.

#### Changed
- **The protocol now says what makes a fault injection sound** (field report
  #29). It already required each acceptance criterion to be falsified rather
  than summarised, and said nothing about attributing a mutation's red to its
  fault — so every harness that has tried it reached for the same unsound
  shortcut: inject the fault, grep the whole output for `FAIL`. A suite of any
  size has other reasons to go red, and a fault that *cannot fire* looks
  identical to one that fired and was caught.

  The rule added: name the assertions the fault should break **before**
  running, then compare predicted against observed. Predicted-red-observed-
  green means the assertion is vacuous. Observed-red-unpredicted means the
  blast radius is wider than the fault, usually a cascade, and those
  assertions are still unpinned. Only a match is proof.

  The worked example in the text is from this release. A mutation disabling
  the config read turned four assertions red; "did it go red?" says yes, and
  the precedence assertions get filed as pinned. They were green — the
  mutation had disabled a different branch. Inverting the precedence directly
  turned five other assertions red, and the two sets barely overlap.

### [1.8.5] — 2026-08-16

1.8.4 made the trailer checkable and then shipped one address for everybody.
That is fine for the check and wrong for the credit: the projects using this
harness are not one project, and the account that should be named is a thing
each of them knows and the installer does not.

#### Added
- **`--coauthor`, and `AGY_COAUTHOR` read from the environment at install.**
  A project crediting its own mailbox is making a true claim, and there was no
  way to make it short of editing two files by hand after every install:

  ```bash
  scripts/install --coauthor 'Antigravity <agy@example.com>'   # this repo
  export AGY_COAUTHOR='Antigravity <agy@example.com>'          # every repo
  ```

  Both write `.agy/config` and `dispatch-context.md` from the one value, so the
  override inherits the property the default had — the model's copy of the rule
  and the harness's copy still come from a single source.

  The shipped default stays `antigravity@antigravity.invalid`, and that is not
  an oversight to tidy up later. This installer runs in other people's
  repositories, so whatever is baked in here lands on the contributor graph of
  every repo a stranger installs it into — the bug 1.8.4 fixed, with the roles
  swapped. A default must credit nobody. Crediting *someone* is a choice each
  project makes for itself, which is what these two flags are for.

  Prefer a dedicated mailbox: `agy@` reads as machine authorship in `git log`,
  where a personal address quietly inflates a human's graph with a model's work.

#### Fixed
- **A config and a context that disagree now refuse to dispatch.** The trailer
  rule has two renderings and the installer wrote both — but nothing stopped
  them being edited apart afterwards. Change `AGY_COAUTHOR`, hand-edit the
  context, copy a context in from another project, and the model is told one
  address and judged against another. Every run then fails on a trailer the
  implementer copied faithfully out of the file it was given, and the evidence
  points squarely at the implementer, which is the one place the fault is not.

  So the disagreement is caught before anything is dispatched, alongside the
  unfilled-marker refusal and for the same reason: it costs one edit, and it is
  a configuration fault rather than evidence about anybody's work.

  A note for whoever simplifies the comparison: it lowercases both sides
  through `tr` instead of asking grep for `-i`. `-F` is not optional — an
  address contains `.` — and `grep -iF`, the obvious way to write that pair, is
  the one shape that cannot be used. GNU grep 3.0 as shipped by Git for Windows
  **aborts** on `-i` combined with `-F`, and an aborting check inside `if !`
  reads as "no match", so every dispatch on Windows would have refused.

### [1.8.4] — 2026-08-15

`dispatch-context.md` is where every behavioural rule in this harness lives,
and until now not one of them was enforced. The fence checks file scope, the
gates check correctness, the report contract checks the report — conduct was
enforced by the model choosing to comply, and detected only if a controller
happened to look. That is not a weaker control than a check; it is the absence
of one, wearing the vocabulary of a rule.

#### Fixed
- **The co-author trailer is now checked, not merely requested.** The template
  asked for a `Co-Authored-By:` line without saying what to put in it, so
  implementers filled it in themselves and settled on `antigravity@google.com`.
  GitHub resolves co-author trailers to accounts **by email** and counts them
  on the repository's Insights contributor graph — so every run of this harness
  was publishing a false claim of authorship against a live third-party
  account, in a repository its owner has never had any access to.

  Naming the right address in the template is half a fix, because the previous
  wrong address got there the same way. `.agy/dispatch` now reads the trailers
  off every commit the run landed and fails on any address that is not the
  configured one, printing the `git commit --amend` that fixes it. The address
  is compared alone — the display name is cosmetic, and GitHub ignores it.

  The value is defined once, in the installer, and rendered into two places:
  `AGY_COAUTHOR` in `.agy/config` for the check, and the trailer block in
  `dispatch-context.md` for the model. One source, two renderings, so the rule
  the model reads and the rule the harness enforces cannot drift apart.

  The default is `Antigravity <antigravity@antigravity.invalid>`. `.invalid` is
  reserved by RFC 2606 and can never be registered, so no account can ever
  verify an address there and the trailer credits nobody.
  `antigravity@users.noreply.github.com` is **not** an alternative: the GitHub
  user `antigravity` exists, and that form resolves to them. Both the config
  and the template say so, because both wrong answers look like fixes.

  Scope, deliberately: a *wrong* address fails, a *missing* trailer does not.
  Whether a commit should have carried one is a judgement — controllers commit
  into the same range, amends drop trailers, merges never carry them — and a
  check that can be wrong warns rather than fails. Whether an address is the
  configured one is not a judgement. Only that is enforced.

  `AGY_COAUTHOR=` (empty) switches the check off. The config binds it with `=`
  rather than `:=` for exactly that reason: under `:=` an empty value is
  indistinguishable from an unset one and the default comes straight back,
  leaving no way to opt out short of deleting the check.

  Trailers are read through git's own parser rather than matched in the message
  text, so a commit that *discusses* an address — like the ones in this
  release — is prose, not a claim.

### [1.8.3] — 2026-08-15

Five field reports. Every one of them is a control that was present, ran, and
reported — while being structurally unable to see the thing it named. A check
that cannot fail is not a weaker check than one that can; it is worse than
none, because the clean result it prints is read as evidence.

#### Fixed
- **The claims checker had been inverted, and nobody could tell.** Two
  independent causes. `singular()` stripped `/e?s$/`, which turns `failures`
  into `failur` and `cases`, `suites`, `examples`, `gates` likewise — none of
  them a known unit, so they were dropped from *both* sides and silently never
  compared. Five of the eleven units were unreachable in the plural, including
  the one that matters most. Separately, the comparison asked only whether the
  report's number appeared anywhere in the gate output, so a correctly-labelled
  scoped count — `19 tests (--filter Gateway)` beside a suite of 76 — was
  flagged as a contradiction. The net effect was a checker that passed the lies
  and failed the accurate reports, teaching every controller who saw it to
  ignore the line. It now strips at most a trailing `s`, and only when that
  lands on a real unit; and a report naming several numbers for one unit is
  read as naming several scopes, which the gate log cannot disambiguate, so it
  is not judged at all.

  The three existing tests passed throughout because all three were written
  with `assertions` — the one plural the old regex happened to survive.

- **`--file` switched off both report checks.** Every fix round is dispatched
  as `--continue --file task-N-fixM.md`, and that path set `REPORT=""`, which
  gates off the report contract *and* the claims comparison. So the checks were
  live on the first attempt and dark for every correction after it — including
  the rounds most likely to be papered over. The label is now matched for a
  task number and the report path recovered from it; a correction file that is
  not a task file still skips, exactly as before.

- **An interrupted run left a commit and no account of it.** Flaw #20. Ctrl-C,
  a closed terminal, a killed parent — the script exited silently, and if the
  model had already committed, what remained on disk was indistinguishable from
  a dispatch that never ran, except that HEAD had moved. From the moment the
  fence is armed the run now owes a verdict however it ends, in the usual shape
  and in its own vocabulary: `INTERRUPTED by SIGTERM`, `THE TREE MOVED` with
  the range to read, `fence NOT CHECKED`, `gates NEVER RAN`. Neither check ran,
  so neither reports a result. The handler also stops `agy`, which is a
  background child and would otherwise go on writing to the log after the
  verdict said the run had stopped.

- **The commit trailer credited a real person.** `dispatch-context.md` required
  a `Co-Authored-By:` trailer and never said what to put in it, so implementers
  supplied `antigravity@google.com` — and GitHub resolves co-author trailers to
  accounts by email, putting a stranger on the Insights contributor graph of
  repositories they have never had access to. The trailer is now pinned
  verbatim to `antigravity@antigravity.invalid`: `.invalid` is reserved by
  RFC 2606 and can never be registered, so no account can ever verify it. The
  template explains why, because the obvious alternative is the trap — the
  `<username>@users.noreply.github.com` form resolves to the GitHub user of
  that name, and the user `antigravity` exists.

- **The fix loop had no way back.** Flaw #24 reported the protocol as having no
  step for closing a task in the ledger. It has one, and always has — but step
  9 is "Fix loop — see below", and that section ended at the scoped re-review
  with the next heading on a different subject. A controller that resolved the
  last finding and adjudicated had reached the genuine end of the text. The
  step existed; nothing routed to it. Fixed as an edge rather than a second
  step, since two closing instructions is how they start to disagree.

- **`protocol.md` named a file that does not exist in half of all installs.**
  Flaw #19. Three places told the controller to run `.agy/gates` — written only
  when the installer generates a starter suite. In an adopted repo the
  installer binds `AGY_GATES` to the runner already present and deliberately
  writes no competing one, so the literal path is a `No such file or
  directory`. Now `( . .agy/config && bash $AGY_GATES )`, which is what the
  wrapper itself does.

- **Nothing compared a task brief against the shared context.** Flaw #21. Both
  are binding and the implementer reads both, so a rule the context states and
  the brief contradicts is a task carrying two specifications with nothing to
  say which governs. The implementer picks one silently and the run comes back
  clean: every check in the loop reads one document and finds it
  self-consistent. One such pair survived four dispatches. The cycle now
  reconciles the two before dispatch, the reviewer contract carries the
  backstop, and the resolution must fix a document rather than rule around it —
  a contradiction settled as a one-task ruling is one you meet again on N+1.

### [1.8.2] — 2026-08-14

Two more from the same day. Both are about a control that cannot see the thing
it is supposed to catch — one because it measures the wrong quantity, one
because it reads a table that the run being graded is allowed to edit.

#### Added
- **`AGY_MAX_WALL` — a cap on total elapsed time, default 2700s.** The idle
  watchdog measures *silence*, so it cannot see a run that finished the work and
  then parked itself in a poll loop: one observed failure committed at 13:28,
  scheduled a five-second wake to check on its own verify task, never woke, and
  was still alive when it was killed by hand eleven minutes later. The stream
  kept growing the whole time, so the watchdog had nothing to measure, and
  because the wrapper was still waiting on the process the fence, the gates and
  the verdict never printed — a run that was *done* looked incomplete. This has
  now happened twice on the same tool call, which is what moved it from a
  curiosity to a cap.

  The cap is tested before the stream is read, because the run it exists to
  catch is one whose stream looks perfectly healthy. It is deliberately not the
  same verdict as the idle kill: `WALL-CAPPED at Ns — the run would not end`
  against `WATCHDOG-KILLED after Ns idle`. One says the run went quiet, the
  other says it would not stop, and they send a reader to different places. As
  with the idle kill, neither is a judgement on the work: the fence, the gates
  and the report are all computable without the model's cooperation, and that is
  what the verdict then rests on.

#### Fixed
- **The reviewer reconciles the acceptance-criteria table row for row against
  the brief.** 1.8.1 stopped the rows being filled in optimistically. This is the
  stronger version of the same failure: a task issued with twelve criteria came
  back reporting eight, and among the four that had silently gone was a
  regression tripwire marked non-negotiable. An optimistic table is at least
  auditable — it is wrong in a way you can see. A table that can lose rows is
  not a checklist at all, because nothing in it shows the reader what is
  missing. The reviewer is now told how many criteria the brief issued and
  reconciles the count before reading any row; a mismatch is a finding on its
  own. The brief template says the same thing to the implementer: a criterion
  that was not met is reported NOT MET with a reason, and rewording a criterion
  to match what was built is not available either.

### [1.8.1] — 2026-08-14

Three reports from one day of field use. The first is the mirror of the flaw
fixed in 1.7.x, where a guard path that was not on disk fingerprinted nothing
and the fence reported clean: this time the control does not silently pass, it
confidently fails — against the wrong target. The other two are both the
reviewer being told, in one way or another, what to conclude before it looked.

#### Fixed
- **`tripwire verify` compares the baseline's surface set against the config
  before judging anything.** It used to walk the *current* config's surfaces
  and never look at what the baseline actually held, which was wrong in both
  directions at once. A surface the baseline never recorded loaded as an empty
  "before", so every file under it was reported `added` — a fully populated
  VIOLATION report, exit 1, for a tree in which nothing had moved, naming the
  source bundle among the casualties. And a surface the baseline *did* record
  but the config no longer lists was never visited at all, so a file tampered
  with under it was reported `clean`, exit 0.

  The two harnesses in that repo name their baselines differently — ours after
  the guarded **path** (`src/styles` → `src-styles.fp`), theirs after the
  surface (`tokens.fp`) — so verifying one fence with the other runner was
  enough to produce the first. A config edited between arming and verifying is
  enough to produce the second.

  A mismatched pair now prints `BASELINE DOES NOT MATCH THIS CONFIG`, names
  the surfaces on each side, and **exits 2, not 1**. This is the same ruling
  as a guard path that is not on disk: a config fault, not drift. The exit
  code is what tells a controller which thing to go and look at, so the two
  must not share one.

- **The verdict block's `fence` line has three outcomes rather than two.**
  `COULD NOT JUDGE — the baseline does not match this config` sends the reader
  to the config; `VIOLATED` sends them to the implementer's diff. Collapsing
  them meant a run that touched nothing could read as a compromised one.
  Neither is a pass: both still exit 4.

- **The reviewer grades acceptance criteria as claims to falsify, not as work
  to summarise.** Reported often enough to stop being a per-brief problem: left
  to itself, an implementer fills that table in as a report of what it did.
  Every row restates the action taken, so a row reads ✅ because the work
  happened rather than because the criterion holds — and the reviewer, handed a
  completed table, confirms it. The contract now tells the reviewer to take each
  criterion and try to break it: name the input or state under which it would
  fail, then check whether the code survives. A criterion nobody attempted to
  falsify is not satisfied, it is **unverified**, and it is reported ❌. This is
  the rule the rest of the harness already runs on, applied where it was
  missing: an absent measurement is never a pass. It lives in the reviewer
  contract now, so it stops having to be written into every brief by hand.

- **The pre-judging ban names the phrasings that actually get written.** It
  listed "do not flag", "at most Minor" and "the plan chose" — the shapes a
  controller writes deliberately. The one that gets written by accident looks
  like helpful context about behaviour that was preserved on purpose: *"these
  are NOT a defect — flag only if undocumented."* That is a verdict the
  controller reached before the reviewer looked, and a conditional licence to
  flag is still a verdict. Both phrasings are now in the list.

### [1.8.0] — 2026-08-13

Two reports from a project three milestones past its install date. Both are the
same shape: a number that was true once, or a line that describes the session
rather than the work, sitting where a controller reads it as fact.

#### Fixed
- **The project skill no longer pins the milestone.** Its bindings table was
  rendered at install time and still read `.agy/work/m5` three milestones later.
  Every script had been reading the real path out of `.agy/config` the whole
  time; only the one document meant to be authoritative about where the ledger
  lives was reading a memory of it. The workspace, the ledger and the shared
  context are now resolved from the config at the top of a session, and the
  table names the config instead of copying it.
- **`--milestone` moves an installed project.** It used to be ignored outright
  whenever any workspace was already on disk, and a config that exists is kept,
  so `--milestone m6` scaffolded `.agy/work/m6/` and left `AGY_WORKSPACE`
  pointing at m5 — a new workspace that nothing wrote to. It now repoints that
  one line and leaves the rest of the config alone (`--force` was never an
  acceptable way to advance a milestone: it takes the gates with it). A config
  whose binding the rewrite cannot find reports `COULD NOT REPOINT` and counts
  as a problem, rather than claiming a move it did not make. The installer also
  prints the `cp` that carries the shared context to the new milestone.
- **The workspace resolution order is written down and enforced:**
  `--workspace`/`--milestone`, then `.agy/config`, then a scan of the disk
  (newest ledger first), then `.agy/work/m1`. The config outranks the scan
  because a project past its first milestone has several `progress.md` on disk
  and only the config knows which is current — the old glob would rebind an
  established repo to whichever milestone sorted first.
- **The `{{date}} — {{ruling}}` placeholder in "Local rulings" is gone.** Its
  markers were lowercase, so the installer never substituted them and the one
  section designed to survive a `/clear` shipped as a literal template line that
  nobody wrote in. The selftest now asserts the installed project skill contains
  no unrendered marker at all, and names no milestone workspace.

#### Added
- **`landed` in the verdict block.** Every other line grades how the session
  behaved, and a run that produced no code behaves impeccably: clean run, clean
  fence, green gates, a confident report. The tree was the only thing that told
  the two apart and nothing measured it. Now: `N commit(s) — <subject>`,
  `NOT COMMITTED — N change(s) outside the workspace, 0 commits`, or `NOTHING`.
  The workspace is excluded for the same reason the fence prunes it — every run
  writes a report there, and counting it would make every run look productive.

- **Work left uncommitted fails the dispatch.** Reported twice on consecutive
  runs: the implementer wrote the code, committed none of it, the harness
  printed `SUCCESS`, and the controller committed by hand both times. That is
  not a judgement call the harness has to duck — the brief's own definition of
  done names the commit, so a tree full of changes against an empty history is
  an unfinished task, and the next dispatch would start on top of it carrying
  work no ledger entry explains. `NOTHING` still only reports, because an
  investigation task legitimately produces no code — and that case leaves
  nothing outside the workspace, so it never reaches the failing branch. The
  brief template now says the commit is part of the task rather than cleanup
  after it.

- **The reviewer now grades the brief before the diff.** Two rounds running, the
  most valuable finding was against the brief rather than the implementation —
  and the contract had no place to put it. A brief whose stated invariants do
  not follow from its stated rules produces an implementer that complies
  exactly, a reviewer that confirms compliance, green gates and a clean fence:
  every check passes and the defect sits in the specification everything else
  was graded against. The controller wrote the brief, so the controller cannot
  be the agent that catches it. Brief integrity is now the first of three
  demanded verdicts, and a finding there is adjudicated by the controller and
  recorded as a ruling rather than sent to the implementer as a fix. The three
  verdicts are printed into the review package itself, not just documented in
  `reference/protocol.md`: the package is the one file the reviewer subagent is
  guaranteed to open, and a contract it never reads is a contract it never has.

- **A refusal prints a verdict block.** Reported as "the missing-brief path exits
  0"; it exits 2, and has since the first release. What made it look like a
  success was the pipe: `.agy/dispatch 3 | tee run.log` returns tee's `0`, and a
  backgrounded wrapper reports whether it managed to start the job. The status
  is the half of the signal the caller can lose, so it can no longer be the only
  half — every pre-run refusal now prints the same block a finished run prints,
  headed `run  DID NOT RUN — <reason>` and carrying its own exit code as text.
  A reader that only sees the output reaches the same conclusion as a caller
  that reads `$?`.

#### Changed
- **`turns` is on its own line, labelled as agy's own count.** Runs reporting
  `1 turns` have carried two dozen recorded tool calls; printed beside the
  durations it read as a one-shot answer. The tool line now leads with the total
  the harness counted off the event stream, which is the number that was
  measured rather than reported.

### [1.7.0] — 2026-08-12

One flaw, reported by a harness on its third crashed run in a row: a run that
did the work, committed it and wrote a 303-line report, then died at 2711s with
`timeout waiting for response` and no result event — and was graded **PROBLEMS**
beside a clean fence, green gates and a correct diff. The harness had no way to
say *the work landed, the session died*.

#### Fixed
- **Deferral keys on the missing result event, not on who did the killing.** The
  watchdog was only ever one route to a run with no `result`: agy also dies on
  its own — its `--print-timeout` expiring, an internal error, a dropped
  connection — and when it does the stream was still moving, so the watchdog
  never fires. The old condition (`killed && !resultEvent`) covered our kill
  only, so a self-inflicted death was judged on its status, its empty response
  and its exit code. All three describe how the session ended. None is evidence
  about the work. Nothing else is relaxed: a denial, a tool error, zero tool
  calls or a report that is missing or stale still fails a stopped run.
- **The verdict can say it.** `run  clean, but the SESSION DIED before its
  result event` — the counterpart to the existing `WATCHDOG-KILLED` line. A
  harness whose only word for this is `PROBLEMS` trains its reader to discount
  `PROBLEMS`, which is the one word that has to keep meaning something.
- **The tool tally is labelled a floor when the stream was cut off.** A stream
  that ends mid-run tallies only what it recorded, and presenting that as a run
  summary reads as proof the implementer wrote nothing — next to a commit that
  is on disk. The reported run showed no write tools at all and made a landed
  commit look like it had appeared from nowhere.
- **Quota classification now keys on the watchdog rather than on deferral**, so
  broadening deferral did not quietly close the fallback route. A run *we* killed
  is still never classified — that is what stops a hang from spending the reserve
  group — but a session that died on its own is, because a genuine weekly
  exhaustion is one of the ways a run ends without a result event.

### [1.6.0] — 2026-08-12

From a backlog of flaws reported by two harnesses running this skill on real
projects. Three of the six were already fixed here and stale only in the
installed copy; the rest share one shape — **a check that exists but can be
walked around by something ordinary**: a space in a path, a template nobody
filled, a `PATH` entry the shell quietly ignores.

#### Added
- **A guarded path that is not on disk makes the fence refuse to arm** — dir,
  file or tree, whether or not it is named in `AGY_REQUIRE`. Nobody configures
  a guard for a directory they do not have, so absence is always a config
  error. This is what makes the space-split guard list *loud*: the fragments do
  not exist, so instead of fingerprinting nothing and reporting `clean`, the
  fence stops. The reported case was
  `AGY_GUARD_TREE=NevaraFlow Suite app shell-handoff/` — the project's primary
  guarded surface, silently unguarded, reporting clean on every run.
- **`.agy/dispatch` refuses to run against an unfilled brief.** The installer
  writes `dispatch-context.md` from a stub full of `{{markers}}` and cannot
  fill them — only the controller knows what goes in. Nothing checked that
  anyone had, and that file is read by *every* implementer and *every*
  reviewer: told the language floor is `{{Language/runtime floor}}`, they read
  no floor at all, and a gate cannot enforce a rule that was never written
  down. The task's own brief is checked the same way. `AGY_ALLOW_UNFILLED=1`
  overrides it for text that genuinely needs `{{...}}`.
- **The installer reports both in its own checks**, so the first dispatch is
  not the messenger — unfilled context lines, and a Windows-form `PATH` entry
  on MSYS.
- **`.agy/dispatch` prints the `agy` binary that resolved.** Git Bash accepts a
  `C:\...` `PATH` entry and then never searches it, so an exported stub can be
  skipped in silence and the real, quota-spending CLI answers instead. That
  happened during a watchdog drill and re-dispatched a completed brief. An
  absolute path on screen cannot be misread. Documented in `setup.md`.

#### Fixed
- **The installer writes guard lists one path per line**, the form the tripwire
  splits on newlines, rather than teaching the whitespace-separated shape that
  cannot express a path with a space in it. `$HOME` alone is enough to hit this
  on Windows (`C:\Users\Firstname Lastname`).
- **`hash_surface` no longer swallows its fingerprinter's exit code.** A bare
  `return 0` discarded every failure the surfaces report, including the
  PowerShell tree walk exiting 4, leaving the empty-surface check as the only
  thing between a broken fingerprinter and the word `clean`.
- **The verdict block names the log the work actually landed in.** The header
  prints its log path before any attempt runs, so on a quota fallback it
  advertised the attempt that hit the wall while the reserve attempt wrote to
  `<base>.reserve.*`. A reader following the advertised path opens a failed run
  and grades its artefacts as the work — this harness's own failure family,
  reintroduced by the harness. `LOG_BASE` now tracks which attempt produced the
  work and the verdict block prints it; the header's copy stays, provisional.

### [1.5.0] — 2026-08-12

From a run where the implementer's fault-injection output was hand-trimmed to
drop the main suite that had already run. Nothing was fabricated and every
count was real. The gate passed, the fence was clean, the run reported
`SUCCESS` — none of those can see inside a report. It surfaced only because the
reviewer re-ran the script itself.

#### Added
- **The reviewer re-executes pasted proof rather than reading it.** Pasted
  output is a claim shaped like evidence: a suite quietly reduced to the cases
  that pass leaves every number in the block true and the block itself a lie
  about what ran. The gate suite is the stated exception — `.agy/dispatch`
  runs it and keeps its own copy at `<log>.gates.log`, so it is already
  independently evidenced and the claims check already compares against it.
  Every *other* cited command has no such capture. This replaces the old "do
  not ask it to re-run gates the report already evidences", which was true of
  gates and quietly wrong about everything else.
- **Implementers must name the exact command line above any pasted block, and
  paste it whole.** Stated so the reviewer's re-run is possible at all: proof
  you cannot reproduce the invocation for is not proof.
- **The harness fails a report missing a required section.** `## Observations`
  was required by the contract and enforced by nothing. An absent section reads
  identically whether there was nothing to observe or the implementer never
  looked. Sections come from `AGY_REPORT_SECTIONS` (default `## Observations`);
  `None.` is a valid body. This is a gate, not a warning, because unlike the
  claims comparison it is deterministic — a heading is present or it is not.

  Known limit: it only checks a report this run actually wrote. A run that
  writes no report at all is still caught only on the deferred path.

### [1.4.0] — 2026-08-12

#### Added
- **A reviewer that cannot run now has a state to park the task in: `HELD`.**
  The protocol said the reviewer must be a fresh subagent and said nothing
  about the subagent being unavailable, which left the controller one cheap
  move — read the diff itself and call it reviewed. That removes the only
  independent check in the loop and, worse, leaves a ledger recording a review
  that never happened. A held task stays open, is recorded as reviewed by
  nobody with the reason, and its only exit is a reviewer becoming available.
  Written as a state rather than a bare prohibition on purpose: a prohibition
  with no exit is a deadlock, and a deadlock is what gets negotiated away
  under pressure.

#### Fixed
- **"When what remains is mechanical, finish it yourself" read as licence to
  produce a verdict.** It was written for a reviewer that died mid-write-up
  after reaching its verdicts. Now says so, adds that a killed subagent can be
  resumed from its own transcript, and states that producing a verdict is
  never mechanical however obvious the diff looks.

### [1.3.0] — 2026-08-12

Both additions come from a real run in another project that reported success,
committed, and was wrong on both counts — a denied `npm install` that ran as
`cmd /c npm install`, and a report claiming a test count the gates contradicted.
Neither was visible in the verdict block at the time.

#### Added
- **Denial-then-success pairs are named as a `BYPASS`.** A denial was already a
  hard failure, so a run like that would have failed anyway — but it failed as
  "one call was blocked", which reads as an *incomplete* run. The fact that
  matters is the next line in the stream: the same command completed under
  another name. That makes the run *compromised* rather than incomplete, and
  every claim in its report unverified, because the work really did happen —
  outside the boundary. The dispatcher now normalises both sides (unwrapping
  `cmd /c`, `sh -c`, `powershell -Command`, `npx`, `sudo`, absolute paths and
  quoting, nested up to four deep) and pairs them on the first two tokens of
  intent. This required collecting successful command strings, which the parser
  previously read and discarded.
- **Report numbers are checked against the gate output.** Where the report and
  the gates name the same quantity, the measurement wins. Deliberately narrow:
  only a unit appearing on *both* sides is ever compared, since the gates cannot
  contradict a number they never measured. It is a **warning, not a gate** — it
  does not change the exit code — because the comparison is heuristic and a
  checker that invents disagreements teaches the controller to ignore it. It is
  still the only signal that catches a report describing work it did not do, so
  `reference/protocol.md` says not to accept a task while it is showing.
- Report freshness is now computed on every run rather than only a deferred one.
  Only the deferred path still *fails* on it; the claims check uses it to avoid
  measuring a report an earlier dispatch left behind.
- Selftest coverage for both, plus the missing assertion that a red gate fails
  the dispatch — a property nothing had pinned, and one this release's gate
  output capture touches.

#### Changed
- The gate runner's output is teed to `<log>.gates.log` so it can be compared
  against the report. Status is read from `PIPESTATUS[0]` rather than the
  pipeline's, so a `tee` failure cannot fake a red gate.

## agy-agents

### [1.2.0] — 2026-08-12

Merges harness work done in a second project with documentation fixes made
here. Neither side was a superset of the other, which is the whole argument for
this repository existing.

#### Added
- **Trap 4: a finished run can hang forever without emitting its `result`.**
  `agy` can do the work, write the report, commit — then sit in an internal
  `manage_task`/`schedule` loop until `--print-timeout` expires 45 minutes
  later, with no error and the process alive. The only tell is that the event
  stream stops growing. `.agy/dispatch` now watchdogs the stream
  (`AGY_IDLE_TIMEOUT`, default 300s) and, on a kill with no result event,
  *defers* rather than fails: status, response and exit code are not judged,
  but a denial, a tool error or zero tool calls still fail the run, and the
  report must be newer than the dispatch that asked for it. A deferred run is
  never quota-classified, so a hang cannot open the reserve bucket.
- **Trap 5: `permissions.deny` matches the literal command string**, so
  `cmd /c npm install` defeats a `npm install` denial. With trap 3 this makes
  the CLI's permission system unusable as a boundary in both directions —
  `allow` fails closed, `deny` fails open. No behaviour change: the harness
  already skipped it and fenced with `.agy/tripwire` instead.
- **`.agy/tripwire` handles guard paths containing spaces.** A list written one
  path per line is split on newlines instead of whitespace, and each list is
  split independently. Previously `Acme Suite/app` fractured into several
  nonexistent surfaces, each hashing to nothing — a fence guarding nothing,
  reporting clean.
- Selftest coverage for the watchdog: that a hung run is killed rather than
  waited out, that its empty response and exit code are *not* held against it,
  that a missing report fails it, that a report left by an earlier dispatch
  fails it, and that a hang never burns the reserve group. Verified by
  disabling the watchdog and watching them go red.

- `agy-agents/README.md` — full documentation of the five CLI traps, the two
  harness traps, the `.agy/` machinery, installation, adoption, configuration
  and the task cycle.

#### Changed
- The selftest exports `AGY_IDLE_POLL=1`. The shipped 15s default cannot notice
  a stubbed run has exited any sooner, which added ~15s to every dispatch in the
  suite. Runtime went from ~3m to ~1m36s while gaining 11 assertions.

#### Fixed
- `dispatch-traps.md` claimed there was "no separate effort flag" for the Gemini
  IDs. `agy --help` lists `--effort (low|medium|high)`, and `.agy/dispatch` has
  always passed it on every model. Corrected, with a note to keep the ID suffix
  and `AGY_EFFORT` consistent since the precedence between them is unpinned.

## agy-agents

### [1.1.0] — 2026-08-12

First public release.

#### Added
- `reference/setup.md` — installing and authenticating the Antigravity CLI,
  the headless smoke test that proves a run really touches your repository,
  the two Windows performance/encoding rules, and how to prove the fence fires
  before trusting it.
- `setup` route in `SKILL.md`, and an explicit prerequisites block.
- Selftest coverage for the adoption path: no generated file may name a gate
  runner the installer did not write, the dispatch template must name the
  adopted runner, and adoption must not write a competing `.agy/gates`.

#### Fixed
- **Adoption pointed the implementer at a gate runner that did not exist.**
  `task-dispatch.md` and `dispatch-context.md` hardcoded `.agy/gates` instead
  of substituting `{{GATES}}`, so any repository that adopted its own existing
  runner got a dispatch template naming a path the installer never created.
  The run would have been graded against a missing command.
- **`.agy/config` promised an environment it could not deliver under
  adoption.** Only a *generated* `.agy/gates` sources the config; an adopted
  runner is the project's own script and does not. Exports still reach it
  through the dispatch's environment, but not on a bare run — which is exactly
  when a missing PATH entry looks like a real gate failure. The generated
  config now says so, and names the adopted runner.
- Removed hardcoded assertion counts from the documentation, which went stale
  the first time an assertion was added.

### [1.0.0] — 2026-08-12

Initial build, extracted from a working single-project harness.

#### Added
- `.agy/dispatch` — the only sanctioned way to call `agy`. Handles the three
  traps that make a broken run report `SUCCESS` with exit 0, parses the nested
  NDJSON event shape (the published flat shape does not match the wire), and
  judges the run itself rather than reading `$?`.
- `.agy/tripwire` — an integrity fence under your control, since
  `permissions.allow` is silently ignored under `--print`. Content hashes for
  small surfaces, size+mtime fingerprints for large external trees. Refuses to
  arm when any required surface comes back empty.
- `.agy/gates` — verification suite run by the harness. No gates configured is
  a hard failure, not a pass.
- `.agy/review-pkg` — single-file review package from a diff range.
- Reserve-quota policy: fall back to the Claude/GPT group only on a clear
  *weekly* Gemini exhaustion; hold through a 5-hour window; hold and print the
  raw text on a quota-shaped error that names no bucket.
- `scripts/install` — idempotent installer that adopts an existing SDD
  workspace and gate runner rather than duplicating them.
- `scripts/selftest` — full harness exercise against a stubbed `agy`, spending
  no quota, aborting rather than run if `agy` resolves to the real CLI.
- `reference/protocol.md`, `reference/dispatch-traps.md`,
  `reference/install.md`.
