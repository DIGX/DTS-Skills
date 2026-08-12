---
name: agy-agents
description: Use when setting up or adopting a repository where Claude plans and the Antigravity CLI (`agy`, Gemini) implements; when the user asks to delegate implementation to Gemini or Antigravity; when installing or authenticating `agy` itself; when an `agy` run reports SUCCESS but nothing changed, hangs without ever finishing, hits RESOURCE_EXHAUSTED or a rate limit, or writes outside its scope; or when a fence, tripwire, or gate check fails in a repo using this harness.
version: 1.3.0
user-invocable: true
argument-hint: "[setup|install|adopt|status|doctor|protocol] — omit to route automatically"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TodoWrite
---

# Antigravity Agents

Deploys the **Claude Manager + Implementer protocol** into a repository: Claude
plans, adjudicates and verifies; the Antigravity CLI implements; a fresh Claude
subagent reviews.

The value is not the delegation — it is that the delegation is *checkable*. An
implementer that reports success, an empty fingerprint, and a gate suite with no
gates in it all look identical to a clean run from the outside. Everything
installed here exists to make one of those distinguishable.

## Route on what you were given

| Situation | Do this |
|---|---|
| `agy --version` fails, or first use on this machine | Read `reference/setup.md` |
| `setup` — install or authenticate the CLI | Read `reference/setup.md` |
| No argument, repo has no `.agy/` | Read `reference/install.md`, then install |
| No argument, repo has `.agy/` | Report status: config, surfaces, ledger, gates |
| `install` / `adopt` / setup request | Read `reference/install.md`, then install |
| `status` | `.agy/tripwire check` + `.agy/gates` + tail the ledger |
| `doctor` — something is off | Read `reference/dispatch-traps.md` first |
| A run is hanging, or was WATCHDOG-KILLED | `reference/dispatch-traps.md`, trap 4 |
| `protocol` — how do I run a task | Read `reference/protocol.md` |
| About to run a task in a repo already set up | Read `reference/protocol.md` |

**Read the reference file before acting.** These scripts encode failures that
are invisible when you get them wrong — that is the whole point of them.

## Installing

**Prerequisite:** `agy`, `node`, `git` and `bash` on PATH, with `agy`
authenticated. If `agy --version` does not answer, stop and read
`reference/setup.md` — the installer's final check will fail anyway, and it is
cheaper to find out now.

```bash
bash ~/.claude/skills/agy-agents/scripts/install --dry-run    # always first
bash ~/.claude/skills/agy-agents/scripts/install --project NAME --milestone m1
```

Run from the repository root. It is idempotent and never overwrites an edited
`.agy/config` or `.agy/gates` without `--force`.

Adoption is the same command: it finds an existing SDD workspace and an
existing gate runner and binds to them rather than duplicating them. Details,
flags and the full config reference: `reference/install.md`.

**Then do the one thing the installer cannot do: write the real gates.** It
emits a starter from whatever toolchain it detected. A generated gate suite is
a guess, and gates are the only thing standing between a confident report and a
broken tree.

## Running a task

Never call `agy` directly — three of its behaviours make a broken run report
success. Use `.agy/dispatch <N>`, which handles all three.

The loop, the reviewer contract, the fix loop and task sizing are in
`reference/protocol.md`. The installed repo gets its own thin
`agy-task-cycle` skill holding just that project's bindings.

## Verifying the harness itself

```bash
bash ~/.claude/skills/agy-agents/scripts/selftest
```

Builds a throwaway repo and exercises the whole harness against a stubbed
`agy` — no quota spent, nothing outside its temp dir touched. Run
it after editing anything under `assets/`. It aborts rather than run if `agy`
resolves to the real CLI.
