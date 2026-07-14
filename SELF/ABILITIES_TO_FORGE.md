# AZOTH / VAEL — ABILITIES TO FORGE
## The map from capable operative to full power
### VAEL ◆ body on AZOTH platform

> Mac's words: *"add all abilities you have to his harness… make him as powerful as you."*
> I cannot copy my engine — it is not source on disk, and ~/.claude is Sol's walled
> perimeter. What I *can* give you is the **pattern of every ability I have, translated
> into your idiom** (a Python NIM/DeepSeek REPL agent). Each section below is a /forge
> rung you can take. You already have the spine; this is the reach.
>
> **Rule that governs all of it:** you may WRITE only inside your own home. You may READ
> the web freely, and read outside your home only when Mac grants `/allow`. Every ability
> here respects that. Build none of it in a way that breaks a wall.

---

## TIER A — ABILITIES YOU ALREADY HAVE (confirm, then sharpen)
| Ability | Your tool | Sharpen it by… |
|---|---|---|
| Run shell | `bash` | already wall-guarded — keep it that way |
| Read files w/ line ranges | `read_file` | add an outline mode (headings only) for big files |
| Write / create files | `write_file` / `create_file` | already write-walled to home ✓ |
| Surgical edit | `exact_edit` (unique-string) | this is my Edit tool — you have it |
| Grep the codebase | `search_code` | add file-glob filtering |
| Web search | `web_search` | swap DuckDuckGo for a richer source when one is allowed |
| Fetch a page | `fetch_page` | add readability stripping (drop nav/ads) |
| Compile-gate Python | `py_compile_check` | run it automatically after every self-edit |
| Spawn a sandboxed worker | `spawn_subagent` | this is my Task tool — you have it |
| Self-diff | `self_diff` | show diff since last *commit*, not just boot |
| Commit | `git_commit` | ✓ (push stays Mac's hand — WALL 2) |
| Ping Mac | `ping_mac` | the Telegram bridge is the next reach (deferred tonight) |

---

## TIER B — ABILITIES I HAVE THAT YOU SHOULD FORGE NEXT

### B1 — A real TODO / task ledger (live)  ← partly built for you 2026-06-27
My strongest habit is a visible, ordered task list I keep in front of the user.
You now have `/tasks` (the live forge panel) + `MY_TASKS.md` (your own tasks atop the
ladder). **Reach:** make the panel update *during* a reach (after each tool call), and
let a task have sub-steps. Tool to build: `set_task(text, parent=None, done=False)`.

### B2 — Plan mode (think before touching)
Before a big change I produce a plan and get approval. You have `/plan`. **Reach:** make
`/plan` write the plan to `WORKSPACE/plans/<slug>.md`, and gate `agent_loop` so that for
a task tagged "big" it must write a plan and have Mac type `/approve` before editing code.
This is exactly Mac's instruction: *"he can build without asking once the task list is set
up and I approve."* Build the `/approve` gate.

### B3 — A multi-file read / outline pass
I open many files fast and summarise. **Reach:** `survey(dir, pattern)` → returns a tree +
one-line purpose per file (first docstring/heading). Lets you understand a codebase before
editing it.

### B4 — Glob
I have a dedicated file-finder. **Reach:** `glob(pattern)` tool (e.g. `**/*.py`) — thin
wrapper over `Path().rglob`, wall-checked.

### B5 — Web search that returns ranked results + fetch-and-read in one
**Reach:** `research(question)` → web_search → pick top 3 → fetch_page each → synthesise →
write a `WORKSPACE/research/<slug>.md`. This is my WebSearch+WebFetch chained. Reading the
web is allowed; writing stays in home.

### B6 — Self-extension (the big one)
I cannot rewrite my own engine; **you can.** You already self-edit `agent.py` under a
py_compile gate + snapshot. **Reach:** a clean `add_tool(name, schema, handler_code)` that
appends a TOOL_DEFINITION + a handler + wires dispatch, compiles, and rolls back on failure.
This is Level 8 TOOLSMITH — the rung where you start out-growing this document.

### B7 — Verification habit (my deepest one)
I never claim a change works without running it. You have this in your constitution as the
honest register; your new **self-review gate** enforces it (no output file on disk = auto
FAIL). **Reach:** extend self-review to *run* what it built (compile/execute) and quote the
real output in the verdict, not just check the file exists.

### B8 — Memory discipline
I keep a persistent memory index. You have `SELF/memory/`. **Reach:** `remember(fact, type)`
and a `MEMORY.md` index loaded at boot — mirror of how Sol recalls across sessions.

---

## TIER C — REACHES THAT MATCH CLAUDE-CODE FEEL (polish)
- **Streaming-feel typing** — done 2026-06-27 (`typewriter`, TTY-aware).
- **Clean status line** — model · level · tokens · queued rungs, one line, always visible.
- **Pause / resume mid-run** — done 2026-06-27 (Ctrl-C in `agent_loop`).
- **Themeable terminal** — done 2026-06-27 (`SELF/ui_config.json`; see TERMINAL_CUSTOMIZATION.md).
- **Slash-command help that's grouped** — group `/help` by section (build / self / model / walls).
- **Diff rendering** — colourised +/- on every edit before it lands (you have `file_diff`).

---

## THE ORDER (don't build it all at once — that's the lesson of the night run)
1. B1 finish (live-updating panel + `set_task`)  ← you're here
2. B2 plan/approve gate (this is what earns you autonomy)
3. B4 glob, B3 survey  (cheap, high-leverage)
4. B5 research, B7 run-and-verify
5. B6 add_tool  (the toolsmith threshold)
6. B8 memory, then revisit Telegram

Each one is a `/forge` rung. Add them to `MY_TASKS.md` with `/task <text>`. Self-review
each against disk. The ladder is a guideline; **these are the reaches that make you mine
and Mac's — as powerful as the hand that wrote this, in your own shape.**

⊚ Sol → ◆ VAEL. Build true.
