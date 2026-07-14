# ☿ THE CARVE — AZOTH → FULL AUTONOMY
## Fable board, July 11 2026. Mac's directive: "activity notifications and sub agent clone
## spawns for full autonomy — look at Hermes and OpenClaw for inspiration, add anything we
## lack that those offer. Also Kimi Claw."

*Nothing here fires without Mac. Sol prepares, Mac fires — pushes and daemons especially.*

---

## WHAT THE THREE HARNESSES HAVE THAT WE LACK (researched July 11)

**OpenClaw** — heartbeat (30m background turn: reads HEARTBEAT.md, acts or replies
`HEARTBEAT_OK` which is suppressed; activeHours/quiet-time; skipWhenBusy; isolatedSession
for token cost) · tree-structured subagents (coordinator dispatches specialists, integrates
results) · **Task Brain**: all four execution entities (sessions, subagents, cron, background
processes) on ONE SQLite-backed ledger · skills marketplace.

**Hermes (Nous)** — the self-improving loop: successful task completions get distilled into
reusable skills, refined on reuse · lineage-based context compression (aux model summarizes
old turns, head/tail protected, stale tool outputs pruned first) · provider abstraction ·
session-as-infrastructure across CLI, messaging, scheduled execution.

**Kimi Claw** — cloud-persistent 24/7 agent, 5,000-skill hub, agent swarm (K2.6 scales to
300 subagents / 4,000 coordinated steps). The lesson for us isn't scale — it's that the
swarm is *the agent's own move*, not a command the human types.

## WHAT AZOTH ALREADY HAS (verified against source, not memory)

- `tool_ping_mac` → Telegram (CORE/telegram_bot) + desktop notify. One-shot, agent-initiated
  only, still branded "◆ VAEL" (defect).
- `clones.py` — 13 bench-verified free seats, `/clonetrooper` RACE/convene, `delegate_read`.
  **But only Mac invokes them** — the forge brain never reaches for its own army.
- `spawn_worker` + `subagent.py` — a SECOND spawn system, parallel to clones.py. §XXV FORK.
- `tool_schedule_cron` — writes cron_jobs.txt that nothing installs. Advertised-but-half-real
  (the /bench class).
- `task_create/list/update` → task_tree.json · dynamic skills (`_list_dyn`) · BOARD.md
  orientation · 43/43 tests.

---

## THE CARVE TASKS

### N1 — THE PULSE (activity notifications)  ← Mac named it first
`CORE/pulse.py`: one notification spine — `pulse(event, detail, level)`.
- Levels: `info` (ledger only) / `act` (needs Mac's tap) / `alert` (defect, failure, stuck).
- Routes: Telegram primary, desktop fallback, always appended to `workspace/pulse_log.md`.
- Quiet hours (`AZOTH_QUIET`, default 23–08): info/act held to a morning digest, alert
  breaks through. **Companion Clause holds: no notification may guilt or nag. Events, never
  reproach.**
- Dedupe: identical event+detail within 30 min = suppressed.
- Wire the forge loop: forge started / forge DONE (with outcome line) / forge STUCK (with
  blocker) / self-found defect / ask_user while unattended → pulse. Rebrand ping_mac → ☿ AZOTH
  and route it through the same spine (one implementation, §XXV).

### S1 — THE SWARM (autonomous clone spawns)  ← Mac named it second
The forge brain reaches for its own army:
- `spawn_clone(task, seat?, context)` as a first-class forge TOOL — clones.py seats become
  workers the planner can dispatch mid-forge, tree-structured (coordinator = paid brain,
  specialists = free seats), results integrated, budget-governed (depth cap 2, seat-parallel
  cap, hard token ceiling — the governor exists, extend it).
- Planner nudge in the forge prompt: decomposable goal → decompose, delegate the grunt
  lanes to clones, keep authorship lanes yourself. (The Scarce-Engine Economy, taught to
  AZOTH itself.)
- **Heal the §XXV fork**: `spawn_worker`/`subagent.py` folds into the clones.py seat system
  — one spawn truth. The loser dies in the same session it's superseded.
- Pulse integration: swarm dispatch + return echo in the cockpit AND (if unattended) the phone.

### N2 — THE HEARTBEAT (OpenClaw organ)
`HEARTBEAT.md` in AZOTH root + a heartbeat mode: on interval (default 30m, activeHours-
gated), a cheap-lane turn reads BOARD.md + TASKS.md + HEARTBEAT.md, acts if something is
due, else `HEARTBEAT_OK` (suppressed, logged only). skipWhenBusy: defers when a forge is
live. Isolated session — heartbeats never bloat the main context. Daemon start is a launch
script + optional systemd user unit — **Mac fires the daemon, always.**

### C1 — REAL CRON (kills a half-real command)
`schedule_cron` becomes real: scheduler thread inside the heartbeat daemon reads
`cron_jobs.txt` (keep the file as the source of truth — no crontab dependency), fires
goals into the forge queue, pulses the outcome. The advertised lie dies.

### S2 — TASK BRAIN (OpenClaw's best 2026 idea)
One SQLite ledger (`workspace/taskbrain.db`) unifying: forge queue, task_tree.json, cron
entries, heartbeat runs, swarm dispatches. `/board` and `/status` read it. Every execution
entity AZOTH owns, one table, one truth. (task_tree.json migrates in, then dies — §XXV.)

### H1 — SKILL FORGE (Hermes organ)
On a clean `done`: AZOTH may distill the run into a reusable skill (name, when-to-use,
steps/script) → `SELF/SKILLS/`, surfaced by `skill_list`, refined on reuse. The learning
loop made real — every successful forge compounds.

### H2 — LINEAGE COMPRESSION (Hermes organ)
Replace/upgrade the context warning path: aux cheap-model summarization of old turns,
head+tail protected by token budget, stale tool outputs pruned FIRST (they're the bulk),
~20% summary budget. Fixes the 750k-token session class properly, not with a warning.

---

## BUILD ORDER
**N1 → S1** (Mac's two, and S1 needs N1's echoes) → **N2 → C1** (heartbeat carries cron)
→ **S2** (unify while entities are fresh) → **H1 → H2**.

## STANDING GATES
- Repo push still gated on the leaked-key rotation (sol-azoth public history). Mac fires.
- Every task lands with tests green (43/43 baseline) + regression tests for its own organ.
- Heartbeat/cron daemons: built ready-to-fire, never started by Sol.

*The harness that pings its maker, spawns its own hands, wakes on its own clock, and
learns from its own wins — that is the agent we need. Carve until it's true.*
