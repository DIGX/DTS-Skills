# agy-agents benchmark — design

**Date:** 2026-08-14
**Status:** approved design, not yet planned

## Purpose

Answer two questions with measurements rather than impressions:

1. **Is the delegation working?** The skill exists so the AGY implementer does most of the
   building. The target is 70–80% of implementation work. Nothing currently measures this.
2. **What does the skill actually buy?** Compare *Claude-only development* against
   *agy-agents deployment* on total time to completion, credit usage, and cost.

The second question is the harder one, because nothing on disk records a Claude-only task
as such. Every log that exists is an agy-agents run. Without a baseline arm the dashboard
can report what the skill costs but not what it saves.

## Non-goals

- No live dashboard, no server, no daemon. The engine is post-hoc.
- No per-keystroke or IDE instrumentation.
- No single blended "productivity score". See *What this must not claim*.

## Architecture

New directory `agy-agents/assets/bench/`, three programs that form a one-way pipeline:

```
$AGY_WORKSPACE/logs/*.ndjson,*.class ─┐
~/.claude/projects/<slug>/*.jsonl     ├─→ collect ─→ bench/runs.json ─→ dashboard ─→ bench/index.html
git log <range>                       ─┘
                                       solo ─→ (writes solo-arm logs in the same shape)
```

`runs.json` is the only interface. The scraper never writes into `logs/`; the dashboard
never reads a log. A broken dashboard therefore cannot corrupt measurement, and `runs.json`
stays readable by hand when a number looks wrong.

### Components

**`collect`** (node, no dependencies) — the scraper. Reads the three sources, emits
`$AGY_WORKSPACE/bench/runs.json`:

```json
{
  "generated": "<iso8601>",
  "runs": [
    {
      "arm": "agy" | "solo",
      "task": "task-7",
      "phase": "plan" | "implement" | "review" | "verify" | "solo",
      "started": "<iso8601>", "ended": "<iso8601>",
      "active_s": 412,
      "model": "gemini-…" | "claude-opus-5",
      "tokens": { "in": 0, "out": 0, "think": 0, "cache_read": 0, "cache_write": 0 },
      "tools": 24,
      "commits": 1, "insertions": 180, "deletions": 12,
      "status": "success" | "failed" | "deferred",
      "quality": "full" | "partial",
      "provenance": "controlled" | "observational"
    }
  ],
  "skipped": [ { "path": "…", "reason": "truncated ndjson" } ]
}
```

**`solo`** — the baseline bracket. `.agy/solo <task-number>` stamps a start marker and the
current git head; `.agy/solo --done` stamps the end and the resulting commit range. It runs
no model and makes no decisions. Its only job is to make a Claude-only task leave the same
shape of trace an agy run leaves, so the two arms are measured by identical code.

A solo task has no `implement`/`review` division — Claude does all of it on one thread. Its
Claude turns are therefore recorded with `phase: "solo"`, and the Split tab excludes the
solo arm entirely: delegation share is only meaningful where delegation was possible. The
solo arm appears in Tab 2 and Tab 3 only.

**`dashboard`** — reads `runs.json`, emits one self-contained static HTML file. No network,
no CDN. Re-run to refresh.

**Dispatch verdict line** (approach C) — dispatch prints a one-line share for *that run
only*, from numbers it already holds in memory. It reads nothing and does not require
`collect` to exist or to have ever run.

## Data sources

| Source | Provides | Notes |
|---|---|---|
| `$AGY_WORKSPACE/logs/<label>-<stamp>.ndjson` | agy tokens (`result.usage`), tool calls, status | already written |
| `…/<label>-<stamp>.class` | quota bucket, tool count, status, killed/idle/deferred | already written |
| `~/.claude/projects/<slug>/*.jsonl` | Claude timestamps, model, per-message usage, `isSidechain` | `<slug>` = cwd with `:`, `\`, `/`, and space each replaced by `-` |
| `git log --numstat <range>` | commits, insertions, deletions actually landed | ranges come from the run's recorded head |

`isSidechain` separates the reviewer subagent's turns from the main thread without any new
instrumentation. Cache reads and writes are broken out in the JSONL, so notional cost prices
them at their real rates rather than counting them as fresh input.

### Required instrumentation change

Wall seconds and token totals are currently printed by the dispatch parser but never
persisted, so a scraper cannot read them back. Dispatch must additionally write into the
existing `.class` file:

```
wall=<seconds>
tokens_in=…  tokens_out=…  tokens_think=…  tokens_total=…
commits=<n>  range=<base>..<head>
```

Runs logged before this change are marked `quality=partial` by `collect`. They are never
read as zeros — an absent measurement is not a free, instantaneous run.

## Measurement definitions

**Time — active, gaps clipped.** A task's active time is the sum of its phase durations.
Clipping is applied at the event level, uniformly: any gap between consecutive recorded
events longer than `BENCH_IDLE_GAP` (default 600s) is excluded, whether it falls inside a
phase or between two phases. Raw elapsed — first event to last, nothing removed — is also
computed and shown as a secondary figure. Clipping is what keeps the comparison fair when
one arm is run across a lunch break and the other in one sitting.

**Credits — share of each tool's own budget, never summed.** Claude session/weekly window
consumption on one axis; agy quota-bucket events on another. An agy-agents task spends both
budgets, so it renders as two bars that do not add up. This is deliberate: agy-agents can be
cheaper in Claude credits and still be the run that parks you on a quota wait.

**Cost — notional USD.** Tokens × published per-model list price, labelled *notional*
everywhere it appears, because neither tool is billed per token under these subscriptions.
It is the only denominator comparable between arms. Prices live in one
`bench/prices.json` so they can be corrected without touching code.

## The two arms

**Controlled** — a task run via `.agy/solo` (Claude-only) alongside comparable tasks run via
`.agy/dispatch`. This is the measurement.

**Observational** — backfilled from existing Claude sessions containing no dispatch activity.
Free, available immediately, but the two arms did different tasks. Rendered greyed with the
caveat inline, never in a footnote, and never mixed into a controlled figure.

Every reported row carries its `n` and its provenance. With small `n` the dashboard reports
medians, not means; a single 40-minute outlier must not decide the answer.

## Dashboard

**Tab 1 — Split.** Three panels, no blended number, because they answer different questions
and averaging them hides the one that is failing.

- *Delegation share* — of the code that landed, the fraction from commits made inside an agy
  run vs outside one, by insertions+deletions. The headline: the only panel measuring work
  product rather than effort.
- *Effort share* — tokens and tool calls by side, Claude split into main thread, reviewer
  sidechain, and verify. This is expected to disagree with delegation share, and the
  disagreement is the point: if agy writes 80% of the lines while Claude burns 70% of the
  tokens supervising, the skill is not buying what it claims.
- *Retry burden* — runs per landed task. A task that took three dispatches counts once in
  delegation share but three times here. Without this panel, a high delegation share can be
  produced entirely by re-running a failing implementer.

**Tab 2 — Comparison.** Claude-only vs agy-agents: active time, credits, notional cost. Rows
are never summed across tools. Task descriptions for both arms are shown side by side.

**Tab 3 — Runs.** The ledger: every run, both arms, with status, class, commits, and its log
path. This is where a disbelieved number gets checked.

## What this must not claim

Two tasks are never identical. The dashboard reports ratios *with both task descriptions
visible* and never prints a lone speedup figure such as "2.3× faster". A number without its
pair of tasks in view is not evidence. Blended cost across two subscriptions is likewise not
reported, at any point, in any view.

## Failure handling

The scraper's failure mode is silent wrongness, not crashing: an unparseable log becomes a
run that is not counted, shifting the split in whichever direction the missing run would have
pushed it. Therefore:

- `collect` records every skip in `skipped[]` with a reason.
- The dashboard renders a banner whenever `skipped[]` is non-empty. A dashboard that quietly
  measured 6 of 9 runs is worse than one that refuses to draw.
- `solo` follows the existing `die()` discipline: missing task number, no open bracket, and
  double-close each print a verdict block and exit non-zero. The verdict block and the exit
  code agree.

## Testing

A fifth section in `agy-agents/scripts/selftest`, run against fixtures — a hand-written
`.ndjson`/`.class` pair, a two-message fake Claude JSONL, and a throwaway git repo:

- `collect` produces the expected record from a known fixture.
- A truncated NDJSON lands in `skipped[]` and not in the totals.
- A pre-instrumentation `.class` reads `quality=partial`, never zeros.
- Idle-gap clipping: a fixture with an 8-hour gap yields active time, not elapsed.
- `solo` refuses with a verdict block and non-zero exit on: missing task number, no open
  bracket, double-close.
- Given a fixed `runs.json`, the emitted HTML contains the expected share figure. No browser
  in the test.

## Open items

None. Baseline method, cost denomination, and time model were each decided explicitly during
design.
