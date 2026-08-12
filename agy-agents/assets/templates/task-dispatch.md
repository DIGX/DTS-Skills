# IMPLEMENTER TASK — {{PROJECT}}, Task {{N}}

**Objective:** {{one sentence: the exact outcome required}}

**Read these first, in order — both are binding:**
1. `{{WORKSPACE}}/dispatch-context.md`
   Global constraints, environment, commands, the definition of done, the
   report contract. Where a brief step and a global constraint disagree, the
   global constraint wins.
2. `{{WORKSPACE}}/task-{{N}}-brief.md`
   Your requirements. Exact values are exact; a near-miss is a miss.

**Context:** {{one or two sentences: where this task sits, what the last task
left behind. No history beyond that.}}

**Interfaces you need from earlier tasks:** {{file paths and signatures only —
not explanations. Omit the section if there are none.}}

**Rulings:** {{the controller's resolution of anything ambiguous in the brief.
Omit if none.}}

**Scope — you may modify:**
- {{path}}
- {{path}}

**Do NOT:**
- Touch any file not listed above. If the task genuinely requires one, stop and
  say so instead of doing it.
- Modify anything under {{generated/vendored/external paths}}.
- Change the plan, the spec, or another task's code.
- Refactor, upgrade dependencies, or fix unrelated bugs you notice — report
  them at the end instead, under "Observations".
- Move on to Task {{N+1}}.
- Report completion without running every gate.

**Required actions:**
1. {{numbered, concrete}}
2. …

**Acceptance criteria:**
- {{specific, checkable}}
- …

**Verification — run this and paste the real output into your report:**
```
{{GATES}}
```

**Report:** write `{{WORKSPACE}}/task-{{N}}-report.md` **incrementally** —
append a section as you finish each step, not all at once at the end. Include
the verbatim gate output, not a summary of it. Any other command you run as
proof: name its exact command line above the output, and paste the output
whole. It will be re-run. End the report with an `## Observations` heading —
`None.` if you noticed nothing.

**Definition of done:** every acceptance criterion satisfied, all gates green,
committed as `{{feat: task N — <what>}}`. If a blocker or a genuine ambiguity
stops you, STOP and write it to the report rather than guessing.
