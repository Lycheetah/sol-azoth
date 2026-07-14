# ☿ AZOTH — THE BOARD
## Last real update: 2026-07-11 — read this at boot, don't grep to re-derive it

**This is where you orient. If you don't know what you have or what's next, read here FIRST —
before searching the filesystem.** The 1.2M-token survey that happened before this file existed
is exactly what this board is for preventing.

## WHAT YOU ARE
AZOTH — an autonomous forge agent. Terminal REPL (`python3 agent.py`), 41+ tools, 31 documented
commands (`/help`), running on a mix of your own paid DeepSeek key and free NVIDIA endpoints.

## WHAT YOU HAVE, RIGHT NOW
- **13 bench-verified clone seats** (`clones.py`) — real free minds, verified by their own hands
  (tool_call + executed code), not by name alone. `SEATS` dict has latency + notes per seat.
- **`/clonetrooper <task>`** — spawn clones on those seats. RACE (default, fast, first sound
  answer) or `--convene` (all seats answer, LIBRA judges disagreement under Mac's 4 axes:
  evidence / experimental-potential / connection / curiosity).
- **`delegate_read(question, paths, seat)`** — the context firewall. Ask a question OF a file
  without loading the file into YOUR context. Reach for this before `read_file` when you want to
  know something ABOUT a file, not its literal content for editing.
- **The registry is honest** — 12 NVIDIA seats in `agent.py`'s own model list are all bench-
  verified live. Dead endpoints (kimi-k2, codestral-22b, nemotron-ultra-253b) and permanent
  hangers (llama-3.3-70b, mistral-nemotron, maverick) are removed, not silently failing.
- **THE PHONE BRIDGE** — every phone command now answers in the terminal too. One
  implementation (`_telegram_reply`), two surfaces; `PHONE_BRIDGE` in `agent.py` is the single
  routing + help source and the test suite fails if it ever advertises a dead name.
- **`/board` and `/seats`** — this file and the clone seats are first-class commands now,
  not things you grep for.
- **THE SHELL (`azoth-ui` → `shell.py`)** — Textual full-screen face: pinned bottom chat bar,
  live status strip (model · tokens · forge state), transcript pane capturing every tool echo
  and thought. Same brain; classic `azoth` REPL untouched underneath.
- **Live Ctrl+C cancel** (first = cancel the forge, second = quit) · **the Forge Cockpit**
  (live status line in the classic REPL) · **the focus leash** (fresh-build goals: write-first,
  reads capped at 2) · **/new is real** (it was advertised for months and didn't exist).

## THE CARVE — 2026-07-11 (Fable): FULL AUTONOMY ORGANS (all committed, unpushed)
Board: `FABLE_CARVE_2026-07-11.md`. Influences: OpenClaw (heartbeat, Task Brain),
Hermes (skill loop, lineage compression), Kimi Claw (swarm-as-agent's-own-move).
- **THE PULSE** (`CORE/pulse.py`) — one notification spine: info/act/alert, quiet
  hours → morning digest (alert breaks through), 30m dedupe, pulse_log ledger.
  ping_mac/done/stuck/forge-loop all route through it. Brand is ☿ AZOTH now.
- **THE SWARM** — `spawn_clone` is a TOOL (solo/race/convene): the forge brain
  dispatches its own free seats mid-task. spawn_worker A/B/C folded into clones
  (grunt lanes off the paid key). Clones structurally cannot spawn clones.
- **THE HEARTBEAT** (`CORE/heartbeat.py` + `HEARTBEAT.md`) — wakes on its own
  clock, runs the checklist as ONE free readonly clone turn, OK is silent, fired
  checks pulse Mac. `launch_heartbeat.sh` — **Mac fires the daemon, always.**
- **REAL CRON** (`CORE/cron.py`) — cron_jobs.txt entries actually fire (hosted
  by the heartbeat daemon); outcomes pulsed + recorded. The old crontab lie died.
- **TASK BRAIN** (`CORE/taskbrain.py`) — ONE SQLite ledger: tasks, forge, cron,
  heartbeat, swarm. task_tree.json migrated (48 tasks) + superseded. /status
  shows it. FORGE_QUEUE.md / cron_jobs.txt stay Mac's hand-edited what's-next.
- **SKILL FORGE** (`CORE/skillforge.py`) — skill_save/skill_recall + index in
  every system prompt; clean runs compound into SELF/SKILLS/.
- **LINEAGE COMPRESSION** — compact_history: protected session root, prune-first,
  free-seat summarizer, token-based autocompact trigger (turn count alone lied).
- Tests: 88/88 + a conftest.py isolation wall (tests can never write real state
  again — live-caught defect, fixed structurally same session).

## THE ROOT CAUSE THAT WAS FIXED
`AZOTH_DEEPSEEK_ONLY=1` in `.env` used to make the free registry unreachable — every worker
fell to paid DeepSeek regardless of what was asked of it. `clones.py` builds its own NVIDIA
client so it works regardless of that flag. If you're burning paid tokens on grunt work, check
whether `delegate_read` or `/clonetrooper` would have done the job for free.

## WHAT'S OPEN
- The web dispatcher (`handle_input`) is still its own partial copy of the command set —
  smaller blast radius than the Telegram fork was (it serves only web_server), but the same
  disease. Fold it into the bridge pattern when the web surface next gets real work.

## CLOSED 2026-07-10 (late night, Fable pass)
- **THE POISONED-HISTORY DEFECT (severe, pre-existing, live-caught).** Every done-gate
  (evidence / Gate 1 / Gate 2 / critic / stuck-rejected) appended a SECOND tool message for the
  same tool_call id. Two responses to one call = API-invalid history → every later call 400s and
  the fallback chain resends the same poison forever. **Every gated `done` on a build goal was
  silently killing the forge loop.** Gates now REPLACE the generic tool response. Regression test
  locks it (scripted forge, no API). Found because the new peak-agency echoes made a live run's
  death visible at the exact step it happened.
- Peak terminal agency: tool echoes now show step + tool + TARGET (`s3 → bash  git status`),
  failures echo red the moment they happen, blocked reads say why, the spinner names the work
  (`forge s3 · flash · 12,400tok`), and `/think` actually works — it was a placebo switch
  (toggled, never read; the /bench class again). A one-line ☁ thinking trace shows by default.
- ~~Re-time provisional seats solo~~ — DONE. medium 12.0s (was 21.2), qwen80 13.7s (was 64.9),
  glm 76.2s (from the earlier solo run). Concurrency starvation, not slow seats. No seat in
  `clones.py` is provisional anymore.
- ~~Bridge ~18 Telegram-only commands into the terminal~~ — DONE. The Phone Bridge (above).
  Four live defects found and fixed in the same pass: phone `/models` crashed with TypeError
  (dict access on tuples), phone `/help` sent the string "True" while the help printed to the
  server console, `/forge <goal>` from the phone was DEAD CODE (a second unreachable branch —
  it showed the queue and silently ignored the goal), `/ping` claimed "VAEL alive" on every body.

## WHAT'S HELD (not abandoned — resume when the app build has breathing room)
CODEX DEFENSE PROTOCOL D-1.0 · TRUTH PRESSURE Π empirical program · k₁–k₄ calibration ·
Paper 1 revision (LAMAGUE, July 2026 deadline) · CASCADE PC v0.4 / API.

## THE DISCIPLINE
Read this board before surveying. If it's stale, that's a defect — flag it in one sentence and
fix it the same session (Self-Found Defect Rule). A board nobody trusts is worse than no board.
