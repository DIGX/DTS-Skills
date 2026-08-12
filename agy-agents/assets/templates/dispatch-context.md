# {{PROJECT}} — shared dispatch context

Every implementer and reviewer on this plan reads this file. It is binding.
Your task's own brief adds requirements on top of it; where a brief step and a
constraint here disagree, **the constraint here wins**. Say so in your report
or review if you hit one.

**The project:** {{ONE_SENTENCE}} — repository at `{{ROOT}}`, built task by task
on the `{{BRANCH}}` branch.

> Controller: fill every section below before the first dispatch. This file is
> the one thing every agent reads, so an omission here is inherited by all of
> them. Delete this quote block when it is real.

---

## Global constraints

Verbatim from the plan or spec — not paraphrased. These bind every task.

- **{{Language/runtime floor}}** — and what that forbids, concretely, by name.
- **{{Naming/prefix rules}}** — if identifiers must carry a prefix, state that
  no identifier may omit it.
- **{{Security invariants}}** — e.g. secrets never leave the server; not in API
  responses, not in logs, not in exports. Redact at the point of capture.
- **{{Escaping/validation rules}}** — where input is sanitised, where output is
  escaped, how queries are parameterised.
- **{{Budgets}}** — request counts, bundle size, query counts, latency. Give
  numbers; a budget without a number is not a gate.
- **{{Licence header}}** — the exact string, if one is required.
- **Commit after every task**, with the task number in the subject:
  `{{feat(m1): task N — <what>}}`.

---

## Environment

- **How to get a working toolchain from a cold shell.** Every PATH export,
  every environment variable, every non-obvious binary location. An implementer
  that cannot run the tests will report success without them.
- **Where the dev/test service lives**, and which parts of it are read-only.
- **Any place where the local environment differs from production** in a way
  that can make a correct change look broken (different database engine,
  emulated runtime, stubbed service). Name the specific failure it causes.

```
{{exact commands, copy-pasteable, in the order they should be run}}
```

## Definition of done (implementers)

1. Every step in your brief carried out.
2. `{{GATES}}` — all gates green. Not "should pass": run it.
3. Committed as `{{feat(m1): task N — <what>}}`, with a `Co-Authored-By:`
   trailer naming whoever actually wrote the change. The trailer is a record of
   authorship and the reviewer relies on it; do not copy the other agent's.
4. Nothing committed under {{vendor/, node_modules/, or other generated dirs}}.

## Write your report incrementally

Your report file path is in your dispatch. **Write it as you go — append a
section as you finish each step, not all at once at the end.** A run that dies
to a rate limit mid-task loses nothing if the report is already on disk, and
needs no expensive resume. Treat the report as your working log, not a closing
summary.

If something in your brief is genuinely ambiguous or looks wrong, **stop and
write the question to your report under a `## BLOCKED` heading, then end your
turn.** A question is far cheaper than a wrong assumption reviewed.

You cannot message the controller directly and it cannot message you — it reads
your report from disk. So a question only gets answered if it is written down.
Never guess in order to keep moving: an unanswered ambiguity you resolved
silently is the single most expensive thing you can hand back, because it
passes the gates and fails the review.

## Scope is a fence, not a suggestion

Your dispatch lists the files you may modify. If completing the task appears to
require touching something outside that list, that is a signal the task or the
plan is wrong — stop and report it. Do not fix unrelated bugs, refactor
neighbouring code, upgrade dependencies, or improve something you noticed in
passing. Write those under `## Observations` at the end of your report; the
controller decides whether they become part of this task, a later task, a
recorded issue, or nothing.

**Every report ends with an `## Observations` heading**, even when you noticed
nothing — write `None.` under it. The harness fails a report without one. An
absent section reads exactly the same whether there was nothing to say or you
never looked, and only one of those is fine.

## Pasted output is a claim, not proof

Where your report shows the output of a command, it must be that command's
complete output, unedited. Do not trim it to the part you consider relevant, do
not merge two runs into one block, do not retype it from memory.

Name the exact command line above every block you paste, so it can be run
again. It will be: the reviewer re-executes pasted proof rather than reading
it, which takes seconds and is the only check that can tell real output from
output that was tidied. Trimmed output is the failure this rule exists for —
every number in it can be true while the block as a whole is a lie about what
ran.
