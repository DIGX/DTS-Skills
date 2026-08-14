# Setting up the Antigravity CLI

Do this once per machine, before installing the harness into any repository.
`.agy/dispatch` will not run without it, and the installer's final check fails
loudly rather than writing a setup that cannot dispatch.

Everything here was verified against **Antigravity CLI v1.1.12** on Windows. If
your version differs, re-verify §"Prove it works" before trusting a run —
`dispatch-traps.md` explains why version drift matters more here than it
usually does.

## 1. Prerequisites

| Need | Why | Check |
|---|---|---|
| `agy` | the implementer | `agy --version` |
| `node` | `.agy/dispatch` parses the NDJSON event stream with it | `node --version` |
| `git` | the harness judges every run by what landed in the tree | `git --version` |
| `bash` | all five scripts are bash | `bash --version` |
| A Google account with Antigravity access | quota | see §3 |

On Windows, `bash` means **Git Bash** (bundled with Git for Windows). The
scripts are written for it specifically: they call `cygpath` where a Windows
path is required, and fall back cleanly where it is absent. PowerShell is used
for one job only — fingerprinting large external trees — and only when
`powershell.exe` is on PATH.

## 2. Install `agy`

Antigravity CLI is the successor to Gemini CLI, which Google retired on
18 June 2026. **Any instruction you find that says `gemini -p …` is stale.**
It ships as a single compiled binary — no Node or Python runtime to manage.

**macOS / Linux**

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Installs to `~/.local/bin/agy`. If `agy` is not found afterwards, that
directory is not on your PATH. The installer writes the PATH line to
`~/.bashrc`; **macOS defaults to zsh, which never reads it** — add
`export PATH="$HOME/.local/bin:$PATH"` to `~/.zshrc` instead.

**Windows (PowerShell)**

```powershell
irm https://antigravity.google/cli/install.ps1 | iex
```

Installs to `%LOCALAPPDATA%\agy\bin`. `.agy/dispatch` falls back to that
location if `agy` is not on PATH, so a Git Bash session that hasn't picked up
the PATH change still works.

Both installers accept `--skip-aliases` (leaves existing `agy`/`antigravity`
shell aliases alone) and `--skip-path` (does not touch your shell profile).

## 3. Authenticate

Run `agy` once, interactively:

```bash
agy
```

The first run starts a Google Sign-In flow and opens your browser. Over SSH it
detects the remote session and prints an authorization URL instead. Credentials
go to the system keyring; `/logout` clears them.

**Do this before your first headless run.** An unauthenticated `--print` run is
exactly the kind of failure this harness exists to catch — and while the
harness *will* catch it, discovering it during a real dispatch wastes a task.

## 4. Prove it works

Version and a real headless round-trip, in a throwaway directory:

```bash
agy --version                       # expect 1.1.12 or later
mkdir -p /tmp/agy-smoke && cd /tmp/agy-smoke && git init -q .
agy --print "Create a file called hello.txt containing the word ok." \
    --add-dir "$PWD" \
    --output-format stream-json \
    --model gemini-3.7-flash-high \
    --mode accept-edits \
    --print-timeout 5m | tail -3
cat hello.txt
```

**Judge it by `hello.txt`, not by the exit code.** If the file is missing, the
run failed no matter what the last event said — that is trap 3, and it is the
single most important thing to internalise before delegating real work. On
Windows, `--add-dir` needs the Windows-form path: `--add-dir "$(cygpath -w "$PWD")"`.

Then verify the harness itself, which needs no quota at all:

```bash
bash ~/.claude/skills/agy-agents/scripts/selftest
```

### On MSYS, a Windows-form `PATH` entry is ignored in silence

Git Bash searches `PATH` in POSIX form. A `C:\...` or `C:/...` entry is accepted
by `export` without complaint and then **never searched** — so the directory you
just put first is skipped, and the next match answers instead.

This is not theoretical. During a watchdog drill a stub `agy` was exported that
way; `command -v agy` walked straight past it, resolved the **real** CLI, and
re-dispatched an already-completed brief against live quota.

```bash
export PATH="$(cygpath -u '/c/tools/bin'):$PATH"   # convert, always
command -v agy                                     # then assert what answered
```

Two things now make it visible rather than silent: `.agy/dispatch` prints
`binary <path>` in its header on every run, and the installer's checks flag a
Windows-form entry on `PATH`. The selftest refuses to run at all if `agy`
resolves to anything but its stub.

## 5. Where things live

| Path | What |
|---|---|
| `~/.gemini/antigravity-cli/settings.json` | global CLI settings |
| `~/.gemini/antigravity-cli/scratch/` | where a run lands when `--add-dir` is missing (trap 1) |
| `~/.local/bin/agy` · `%LOCALAPPDATA%\agy\bin` | the binary |

`settings.json` is **shared by every project on the machine.** A `deny` rule
you add there changes other people's runs. Keep project-specific fencing in
your own repo — which is what `.agy/tripwire` is for. It is also why the
harness guards that file rather than editing it.

## 6. Quota

Antigravity meters two independent groups, each with its own weekly **and**
5-hour limit: `GEMINI MODELS` (primary) and `CLAUDE AND GPT MODELS` (reserve,
which drains far faster for the same work).

Quota is **not queryable headlessly** — `agy quota` produces nothing and no
quota verb appears in `agy --help`. It exists only in the interactive panel. So
`.agy/dispatch` detects exhaustion from the failure itself and is deliberately
conservative about spending the reserve. See `dispatch-traps.md`.

## 7. Two Windows rules that cost an hour each

**Never content-hash a large tree.** Hashing ~15,700 files means *opening*
every one, which wakes Defender's real-time scanner and collapses throughput
from ~3,500 files/s to ~60. MSYS `find` is not an escape: it answers `-type f`
from the directory entry cheaply, but **any mtime predicate** (`-newer`,
`-printf '%T@'`) forces a per-file `stat()` that opens the file — a `find
-newer` walk hung for 3m20s where PowerShell's `Get-ChildItem` returned the
same data in 917ms, because `Length` and `LastWriteTime` come out of the
directory enumeration with no file opens at all. This is why `AGY_GUARD_TREE`
fingerprints by `size:mtime` via `fingerprint-tree.ps1` and only
`AGY_GUARD_DIRS` gets content hashes.

**Keep every `.ps1` ASCII-only.** Windows PowerShell 5.1 reads a `.ps1` in the
system codepage unless it carries a UTF-8 BOM. One em dash in an error string
arrived as mojibake and took the parser down with `Missing ')' in method call`
— an error pointing nowhere near the real fault. Check with:

```bash
LC_ALL=C grep -n '[^ -~\t]' .agy/*.ps1
```

## 8. Before you trust the fence

Prove it fires. A fence that has never fired is not known to work:

```bash
.agy/tripwire snapshot /tmp/fence-proof
echo x >> docs/README.md          # any file in a guarded dir
.agy/tripwire verify /tmp/fence-proof     # must name that file and exit non-zero
git checkout docs/README.md
```

The same discipline the protocol demands of your gates: **a gate you have never
seen go red is not yet a gate.**
