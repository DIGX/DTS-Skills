# DTS Skills

Agent skills for [Claude Code](https://claude.com/claude-code), built and
maintained by [DIGX](https://github.com/DIGX).

A *skill* is a folder Claude Code loads on demand — instructions, reference
material and scripts that turn a workflow you had to explain every time into
one Claude already knows.

| Skill | What it is |
|---|---|
| [`agy-agents`](agy-agents/) | Delegate implementation to Google's Antigravity CLI (Gemini) while keeping planning and review with Claude — with a fence, gates and a self-test that make the delegation *checkable*. |
| [`brand-media-kit`](brand-media-kit/) | Generate a consistent banner set for a family of products — one art master each, all type drawn in code, every delivery size cut from that one file, and a checker that re-reads the disk. |

---

## `agy-agents`

**Claude plans, adjudicates and verifies. The Antigravity CLI implements. A
fresh Claude subagent reviews.**

Delegating implementation to a second model is easy. Knowing whether it
actually did the work is not — and that is the whole problem this skill exists
to solve.

Three behaviours of the Antigravity CLI make a **completely broken run report
`SUCCESS` with exit code 0**:

1. Without `--add-dir`, a headless run executes in a scratch workspace instead
   of your repository — while the `init` event still reports your real working
   directory.
2. `permissions.allow` is honoured interactively and **silently ignored** under
   `--print`. Every allowed command is soft-denied; the run continues, does
   nothing, and exits 0.
3. The exit code is not evidence of anything. A run where every tool call was
   blocked still exits 0 with `status: SUCCESS`.

Add the ones that come from the harness rather than the CLI — a fingerprinter
that returns zero files reports *clean*; a gate suite with no gates in it
reports *green* — and "it said it worked" stops being information.

`/agy-agents` installs the machinery that makes those states distinguishable:

- **`.agy/dispatch`** — the only sanctioned way to call `agy`. Handles the four
  traps that can wreck a run, parses the NDJSON event stream and judges the run
  itself rather than reading `$?`, watchdogs a stream that goes silent, tells a
  session that died apart from work that failed, and prints one verdict block:
  `run` / `fence` / `log` / `gates`.
- **`.agy/tripwire`** — an integrity fence you control, since the CLI's own
  permission system cannot be trusted headlessly. Fingerprints the surfaces the
  implementer must never touch, before and after every run. **Refuses to arm if
  any required surface comes back empty**, because a broken fence reporting
  "clean" is worse than no fence.
- **`.agy/gates`** — your verification suite, run by the harness, never taken on
  the implementer's word. **No gates configured is a hard failure, not a pass.**
- **`.agy/review-pkg`** — builds a single-file review package from a diff range.
- **A reserve-quota policy** that will not burn your expensive model bucket on a
  five-hour window that refreshes by itself.
- **A per-project `agy-task-cycle` skill** holding just that repo's bindings, so
  the protocol stays in one maintained place.

### Requirements

| | |
|---|---|
| [Antigravity CLI](https://antigravity.google/docs/cli/install) | v1.1.12 or later, authenticated |
| Node.js | the dispatcher parses the event stream with it |
| git, bash | Git Bash on Windows |
| Claude Code | this is a Claude Code skill |

Setup instructions for the CLI itself — install, auth, and a smoke test that
proves a headless run really touches your repo — are in
[`agy-agents/reference/setup.md`](agy-agents/reference/setup.md).

### Install

```bash
git clone https://github.com/DIGX/DTS-Skills.git
cd DTS-Skills
bash scripts/install-skill agy-agents
```

That copies the skill to `~/.claude/skills/agy-agents/`. Pass `--link` instead
to symlink it, so `git pull` updates the installed skill in place — the right
choice if you intend to contribute. On Windows a real symlink needs Developer
Mode or an elevated shell; without either, the installer says so and falls back
to a copy rather than leave you believing edits are live.

Then, in Claude Code:

```
/agy-agents
```

With no argument it routes on what it finds: no `.agy/` in the repo means
install, an existing `.agy/` means report status. `setup`, `install`, `adopt`,
`status`, `doctor` and `protocol` route explicitly.

### Adopting a repository already mid-flight

Adoption is the same command. Before writing anything it scans for work already
in progress and **binds to it rather than duplicating it**: an existing
`.superpowers/sdd/*/` workspace keeps its ledger history, and an existing
`scripts/gates` is adopted as-is — your suite is almost certainly better than a
generated one. Nothing is deleted, moved or rewritten. Always `--dry-run` first;
it prints every path it would touch and changes nothing.

### Verify

```bash
bash ~/.claude/skills/agy-agents/scripts/selftest
```

Builds a throwaway repository and exercises the whole harness against a stubbed
`agy` — fence arm/violate/refuse, the zero-gates fail-safe, git fast-forward vs
branch switch, all four quota routes, adoption, idempotency. **It spends no
quota**, and it aborts rather than run if `agy` resolves to the real CLI.

---

## `brand-media-kit`

**One art master per product. All type drawn in code. Every size cut from that
one file.**

Thirteen plugins, each with a banner made when that plugin shipped. Every one
reasonable on its own; together, thirteen unrelated products. Consistency by
discipline does not survive the fourteenth product, or the second person, or the
six-month gap — so none of the consistency here depends on discipline:

- **The style prompt is one constant string.** Every product's prompt is those
  exact bytes plus a single subject clause. Assemble the style per product and
  the products drift apart again.
- **Type is never in the art.** The model is asked to leave the left 45% of the
  frame quiet; the title and tagline are drawn there afterwards by one function
  at fixed sizes, tracking and position. Long titles shrink to fit; short ones
  never grow to fill.
- **Every format is a centred crop of the same master** — product card, page
  header, hero strip, and both WordPress.org listing sizes. Nothing is drawn
  twice, and nothing is ever upscaled: a master too small for a format is a hard
  error, because upscaled art looks fine at review size and soft in the listing.
- **Deployed files are encoded down to a byte budget** and copied into every
  target directory.
- **`verify` imports nothing else in the kit.** Every other stage reports what it
  believes it did; this one re-reads the files — sizes, budgets, and whether the
  copies in each target are still byte-identical. It refuses to pass when handed
  an empty expected set, because a fence that reports clean on nothing is worse
  than no fence.

Art comes from Gemini, by API key if you have one and by a generated
`PROMPTS.md` to paste into the app if you do not — both routes build the same
prompt, since a consumer subscription not including API access should not mean a
different prompt.

**One step is deliberately human**: before saving a master, look at it and
reject it if it contains lettering. Image models produce letterforms unprompted,
and OCR was rejected as the automation — a cloud vision call would break the
rule that the selftest runs offline and spends no quota, and a local Tesseract
would silently stop enforcing on every machine lacking the binary.

### Requirements

| | |
|---|---|
| Python | 3.9+ with Pillow (`pip install -r brand-media-kit/requirements.txt`) |
| Fonts | your own, licensed; the suite vendors Bebas Neue (SIL OFL) for tests only |
| A Gemini key | optional — without one, the manual handoff path does the same work |
| Claude Code | this is a Claude Code skill |

### Install

```bash
bash scripts/install-skill brand-media-kit
```

Then, in Claude Code, from the project you want set up:

```
/brand-media-kit
```

With no argument it routes on what it finds: no `.brandkit/` means scaffold one,
configs but no art means generate, art in place means composite and onward.

### Adopting a product set that already has images

Two things to settle before generating anything, because both are cheap to
decide and expensive to redo:

- **Filenames.** The kit deploys `<slug>-<format>.webp` into every target, since
  each target holds the whole range rather than just its own product. A project
  already loading `<slug>.webp` either updates those references or narrows the
  format list.
- **Fonts.** `brand.json` names font files that must exist in `.brandkit/fonts/`.
  Nothing is shipped and nothing is substituted — a missing face is an error,
  not a fallback.

### Verify

```bash
bash ~/.claude/skills/brand-media-kit/scripts/selftest
```

Runs the whole suite offline against a vendored test font. It never calls a
model and spends no quota.

---

## Honest caveats

- **Developed and used daily on Windows** with Git Bash. The scripts guard their
  platform-specific paths (`cygpath` falls back, `powershell.exe` is behind a
  `command -v` check) and CI runs the suite on Ubuntu and Windows both — but
  Windows is where it has real mileage.
- **Verified against Antigravity CLI v1.1.12.** The traps above were found by
  probing, not by reading documentation, and the published event-shape docs did
  not match the wire. If your version differs, re-run the smoke test in
  `setup.md` before trusting a dispatch.
- **The quota classifier is deliberately conservative.** It is written against
  the vocabulary these errors normally use, not against a captured exhaustion
  event. A quota-shaped error that does not clearly say *weekly* stops and
  prints its raw text rather than spending your reserve on a guess. If you hit
  the real thing, the raw string is in the log — please
  [open an issue](https://github.com/DIGX/DTS-Skills/issues) with it.
- **The installer cannot write your gates.** It emits a starter from whatever
  toolchain it detects, and that is a guess. Replacing it is step 3 of adoption
  and the step that actually matters.

## Contributing

Issues and pull requests are welcome. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) first — this repo has one firm rule about
changing a skill, and it is not the usual one.

## License

[MIT](LICENSE).
