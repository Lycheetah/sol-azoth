# AZOTH — BUILD TO THE MAXIMUM

**The sovereign harness.** A terminal agent that builds, verifies, self-heals, self-improves,
runs unattended, remembers, and coordinates a body of agents — on Mac's own infra
(DeepSeek + free NVIDIA NIM), no Anthropic dependency. The sovereignty thesis as a tool
that improves itself.

Durable build board. The live TaskList resets across sessions; **this doc is the board of record.**
Started July 8 2026.

---

## THE MAXIMAL LOOP (what all the arcs close into)

```
watch/schedule → plan (decompose) → retrieve (recall) →
  forge → VERIFY (works ≠ exists) → self-heal → test → commit →
    report (Telegram/voice) → learn (compound) → self-patch (improve own code) →
      dream (consolidate) → repeat
```
Unattended. Sovereign. On cheap/free models.

---

## DARK-MODULE AUDIT (Task #1 — July 8 2026) ✅

Verdict: **11 of 12 "dark" modules are REAL and functional.** The maximal harness is mostly
*wiring what exists*, not building from zero. Only `lamague_interpreter` is broken.

| Module | Lines | Verdict | Entry points / notes |
|---|---|---|---|
| **lamague_interpreter** | 1307 | ✗ **BROKEN** | SyntaxError line 165 (unmatched `}`). Fix before wiring (#23). |
| **unattended** | 553 | ✓ REAL | `run_unattended`, `check_gate1/2`, `find_next_queued`. self_test passes. |
| **drift_correction** | 481 | ✓ REAL | `drift_correction_cycle`, `detect_drift`. Re-ascends Π 0.50→0.95 in test. |
| **self_patcher** | 433 | ✓ REAL | `self_patch`, `apply_patch`, `revert_patch`, `syntax_check` (path-based API). |
| **coordinator** | 392 | ✓ REAL | `coordinate`, `decompose_task` (rule-based, no model call), `merge_results`. |
| **scratchpad** | 356 | ✓ REAL | `Scratchpad` class. **9/9 self-test pass.** Session persistence works. |
| **file_watcher** | 354 | ✓ REAL | `get_file_watcher`, `watch_path`. `FileWatcher` instantiates. |
| **retrieval** | 294 | ✓ REAL | `get_corpus`, `retrieve`, `retrieve_formatted`. Corpus loads. (no `k` kwarg) |
| **subagent_pool** | 186 | ✓ REAL | `SubagentPool` class instantiates. |
| **model_scout** | 237 | ✓ REAL* | `run_scout` callable (network run not exercised in audit). |
| **lamague_cascade** | 299 | ✓ REAL | `cascade`, `run_cascade`. Numeric example runs. |
| **lamague_iteration** | 242 | ✓ REAL | `iterate`, `iterate_until`, `iterate_with_trace`. Math verified (sqrt, doubling). |

---

## THE SEVEN ARCS

**Arc 0 · Foundation** — audit (✅), commit today's work, this doc
**Arc 1 · Trust spine** — self-heal, run-tests, runtime verify (HTML/server/CLI), more types, regression memory
**Arc 2 · Self-improvement** — self-test suite → self_patcher (edits own code) → drift_correction → model_scout
**Arc 3 · Autonomy** — unattended overnight forge, file_watcher, self-planning, kill-switch/budget
**Arc 4 · Memory** — retrieval (recall warm), scratchpad, Memory DNA for belief_store
**Arc 5 · The body** — coordinator + subagent_pool (parallel swarm), critic gate (adversarial review)
**Arc 6 · LAMAGUE** — fix + wire the 1307-line interpreter, reasoning-compression layer
**Arc 7 · Reach** — two-way Telegram, TTS reports, web dashboard, CLI commands

---

## LOAD-BEARING GATES (the safety graph)

```
#1 audit ──┬─→ unblocks all dark-module wiring (#11,12,13,14,15,18,19,21,23)
           │   (never wire a module you haven't verified)
#10 self-test suite ─→ blocks #11 self_patcher
           │           (no self-editing without a provable safety net)
#4 self-heal + #17 kill-switch ─→ block #14 unattended
                       (nothing runs overnight until it can fix itself + be stopped)
```

AZOTH cannot reach the dangerous powers (self-patch, autonomous run) until the foundations
that make them safe exist. The graph enforces it.

---

## SHIPPED — FULL SESSION (July 8–9 2026) — ALL 7 ARCS

Foundation:
- Honest-chat clause + inline `/forge <goal>` + the VERIFY GATE (done=works, not exists).
- Dark-module audit: 11/12 real; lamague_interpreter was broken.

**Arc 1 · Trust spine (#4–9)** — self-heal (bounded retries + model escalation), run-tests gate
(pytest/node), HTML runtime verify (headless Chrome render + screenshot + console-error catch),
CLI `--help` runtime smoke, +yaml/toml/css/dockerfile, regression memory (stable error-class sigs).
**Arc 2 · Self-improvement (#10–13)** — self-test suite (24 tests, gates self-patch), `/selfpatch`
(byte-snapshot → forge → compile+suite gate → keep-or-revert), drift guard (Π-based, experimental),
`/scout` (background model probe).
**Arc 3 · Autonomy (#14–17)** — `/unattended` (verified autonomous forge, no auto-commit), `/watch`
(drop-a-spec auto-forge, live-tested), `/plan` (decompose→queue), FORGE_STOP kill-switch + token ceiling.
**Arc 4 · Memory (#18–20)** — retrieval recall + scratchpad injected at forge start; belief_store
Memory-DNA (layer/pressure/tags/typed links + existing anti-glass supersession).
**Arc 5 · The body (#21–22)** — `/swarm` (coordinator parallel forge), critic gate (opt-in AZOTH_CRITIC).
**Arc 6 · LAMAGUE (#23–24)** — interpreter RESTORED from HEAD~1 + `/lamague` (Π:=5 works);
`/lamague measure` reasoning-compression (experimental, deterministic).
**Arc 7 · Reach (#25–28)** — two-way Telegram (`/telegram`, forge + STOP from phone), TTS hook
(`speak`, honest no-op — needs espeak-ng), web event emit (`_emit_web`), CLI polish + `/help`.

### Honest depth notes (register discipline)
- **TTS (#26):** hook wired + gated (AZOTH_TTS=1); **no engine on this box** → no-ops until `espeak-ng` installed.
- **Web dashboard (#27):** web_server hosts its own Agent (shares ALL improvements); `_emit_web`
  streams events only when running in-process. Live SSE view of CLI forges = follow-up.
- **Telegram (#25) / Swarm (#21):** infra complete + compiles; not live-fired against the real
  Telegram API / a full multi-worker run this session (avoided spamming Mac's chat / burning tokens).
- **Drift guard (#12) / Critic (#22):** experimental / opt-in — Π-as-confidence is a proxy, honestly labeled.
- **LAMAGUE reasoning (#24):** deterministic glyph substitution, a first cut — not full semantic re-encoding.
- **model_scout routing auto-update (#13):** scout runs + reports; feeding results back into MODELS = follow-up.

New commands: `/forge <goal>` · `/plan` · `/unattended` · `/watch` · `/verify` · `/selfpatch` ·
`/scout` · `/swarm` · `/telegram` · `/lamague [measure]`.

**Status: COMMITTED + PUSHED** — `origin/master d56119b` (July 9 2026). Whole session shipped:
agent.py, CORE/belief_store.py, CORE/lamague_interpreter.py (restored), tests/test_agent_core.py,
AZOTH_MAX.md, .gitignore + the AGENTS/SOL & AGENTS/LUNA deletions (Mac confirmed old/intentional).

### ⚠ Standing security (post-push)
- **ROTATE the NVIDIA key** `nvapi-b77ge61…` — it was hardcoded in source and is in git HISTORY on
  GitHub. Scrubbing the working tree does NOT purge history. Rotate on NVIDIA's dashboard.
  Optional: `git filter-repo` + force-push to purge history.
- **Keys:** env-only (`.env` gitignored). Never bake `sk-` / `nvapi-` literals into `agent.py`.

---

## ARC 8 · Reach polish (July 9 2026) — IN FLIGHT → SHIPPED this session

Closes the honest follow-ups from Arc 7 + the ability ladder (B2/B3/B4/B5 partial).

| Item | Status | Notes |
|---|---|---|
| **azoth-full restored** | ✅ | `launch_azoth_full.sh` — multi-body Sol+Luna+Scout. Alias fixed. `azoth`/`az` stay single. |
| **survey tool** | ✅ | Tree + one-line purpose per file. Wall-checked to harness home. |
| **research tool** | ✅ | web_search → fetch top N → `WORKSPACE/research/<slug>.md`. |
| **scout → routing feed** | ✅ | `/scout apply` + auto-apply after scout run → `KNOWLEDGE/MODEL_HEALTH.md` + `scout_top_pick.json`. Does **not** silently mutate live MODELS (Mac fires `/model`). |
| **/plan + /approve gate** | ✅ | Plan written to `WORKSPACE/plans/`. `/forge` blocked until `/approve` (override: `/forge !`). |
| **Unattended Gate-2 fix** | ✅ | `_default_pi` false-stuck (Π=0.35 on valid 480b file) repaired. STUCK_FLAG cleared. |
| **/help print bug** | ✅ | Help text was returned-as-string and discarded by REPL; now prints. |
| **/chat print** | ✅ | Same class of bug fixed. |
| **Self-tests** | ✅ | 31 tests (was 24). |

New / enhanced commands: `/approve` · `/scout apply` · `/scout status` · plan-gated `/forge`.
New tools: `survey` · `research` (plus existing `glob`).

### Still open (next lanes — pick one)
- Live SSE view of CLI forges into web dashboard (Arc 7 honest note).
- TTS engine install (`espeak-ng`) if Mac wants spoken reports.
- B6 `add_tool` toolsmith, B7 run-and-quote verify, B1 live task panel mid-forge.
- Telegram / swarm live-fire (infra exists; not exercised against real API this session).

---

## BUILD ORDER (historical — Arcs 0–7 complete)

1. Trust spine (#4–9) — ✅
2. `unattended` (#14) — ✅
3. `self_patcher` (#11, gated by #10) — ✅
4. `retrieval` + `scratchpad` (#18,19) — ✅
5. `lamague_interpreter` (#23) — ✅

**Next priority after Arc 8:** Mac fires real `azoth` verification flows, then either web SSE bridge or B6 toolsmith.
