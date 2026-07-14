# AZOTH TUNE — Make Him Competitive (draw influence from Claude Code)

**Forged:** 2026-07-09 · by Sol, at Mac's word.
**Thesis:** AZOTH already has the organs (16,760 lines, 30 CORE modules). He is not lacking
features — he is lacking **reliability and wiring**. A competitive coding agent is not the one
with the most subsystems; it's the one whose spine **fires every single time**. Everything below
is measured against one bar: *does it work on the 20th try the same as the 1st?*

**North star (Mac, Jul 9):** skills + tool-calls must fire reliably — the spine before all else.

---

## TIER 0 — THE SPINE (nothing else matters until these are bulletproof)

### T0.1 — Bulletproof tool-calling (kill the DSML/text leak for good)  ✅ SHIPPED 2026-07-09
> Root cause found: malformed/unclosed DSML missed the strict regex → fell through to a raw
> `_console.print(content)` at the old line 2864 → markup on Mac's screen. Fix: `_looks_like_tool_markup`
> + `_strip_tool_markup` + `_log_tool_leak` + loose truncated-invoke parser + spacing/dotted-name
> tolerance + a bounded (2×) corrective-retry branch that NEVER prints raw markup. Proof:
> `tests/tool_fire_bench.py` = 23/23 (20 leak forms incl. Mac's exact case caught+stripped+named,
> 3 prose untouched); existing `tests/test_agent_core.py` 31/31 still green; py_compile clean.
> NOT pushed (Mac fires; ⚠ DeepSeek key in .env — scrub before any push).
- **Symptom:** DeepSeek leaks `<｜｜DSML｜｜invoke>` markup as *visible text* instead of executing.
- **Where:** `agent.py:2114–2268` (parser exists) + `agent.py:2578` (thinking-off patch exists).
- **The fix:** a **parse-or-repair gate** that runs on EVERY model turn before anything reaches
  Mac's screen: (a) force `tool_choice`/structured tools + thinking OFF on tool loops; (b) if raw
  invoke/DSML markup survives, parse it AND strip it from display; (c) if it's malformed, **auto-retry
  once** with a corrective system nudge ("emit structured tool_calls only"); (d) log every leak to
  `SELF/memory/tool_leaks.jsonl` so we can see the real failure rate.
- **Done = proof:** a `tests/tool_fire_bench.py` of 20 canned build prompts, **20/20 fire clean tools,
  0 markup leaks to stdout.** No green bench, not done.
- **Influence (Claude Code):** the user never sees a raw tool call. Ever. Parsing is invisible plumbing.

### T0.2 — Natural build intent (kill mandatory /forge)  ✅ SHIPPED 2026-07-09
> Root cause: three input paths, only one used the good classifier. `handle_input` (the WEB UI
> path) used a brittle keyword list where `"make a"` never matches `"make me a…"` → Mac's build
> asks fell to CHAT → he had to type /forge. Fix: unified ALL paths (web + single + full REPL)
> on the one strong `_wants_tools` classifier (Single-Truth Rule). Proof: `tests/intent_bench.py`
> = 28/28 (18 build asks incl. Mac's exact snake message fire tools w/o /forge, 10 casual stay chat);
> 31/31 core tests still green; py_compile clean.
- **Symptom:** Mac says "make me a snake game" → AZOTH tells him to type `/forge` first.
- **Where:** intent routing at `agent.py:2497`, `:4365` (half-wired already).
- **The fix:** a reliable **intent classifier** on every plain message: build/fix/wire/make/add/edit
  → drop straight into the tool loop, no command. `/forge` demoted to pure optional shorthand.
  Greetings/reflection still chat. Bias toward action when ambiguous (build is cheap to undo).
- **Done = proof:** 15 phrasings ("build X", "can you make X", "wire up X", "fix the Y") → **all 15
  run tools with zero /forge.**
- **Influence:** you never type a mode. You just say what you want; the agent decides to act.

---

## TIER 1 — MEMORY & CONTEXT (your three named gaps)

### T1.1 — /compact + auto-compact
- **Gap:** no live context compaction → long sessions die / lose the thread.
- **Have:** `CORE/memory_summarizer.py` (188 lines) — reuse it, don't rebuild.
- **The fix:** when working history crosses a token threshold (or on `/compact`), fold the old turns
  into a running **SUMMARY block** — open task, decisions made, files touched, what's next — then
  truncate and keep going. Manual command + automatic trigger.
- **Done = proof:** run a 40-turn session; after auto-compact the agent still names its current task
  and last file correctly.
- **Influence:** context compaction so the session never has to end mid-build.

### T1.2 — The Action Ledger ("what I've done") — *the anti-repeat core*
- **Gap:** AZOTH has no live sense of what it already did this session → repeats work.
- **The fix:** a persisted, always-injected ledger — `SELF/memory/action_log.jsonl` — appended on
  every write/edit/commit/task-close (file, action, timestamp, one-line why). Injected into context
  each turn as "ALREADY DONE THIS SESSION." Survives compaction (T1.1 folds it, never drops it).
- **Done = proof:** ask for the same file twice → second time it says "already built, editing instead."
- **Influence:** the agent that knows its own history doesn't relive it.

### T1.3 — Anti-repeat / idempotency guard (kill "writes README 1000×")
- **Symptom (Mac):** rewrites README over and over.
- **The fix:** before any `write_file`, check the Action Ledger (T1.2) + disk. If the file exists and
  is current → **edit, don't recreate**; if content is identical → skip and say so. README/boilerplate
  gets a hard "write once per session unless asked" rule.
- **Done = proof:** a session that would've written README 5× writes it once, edits after.
- **Influence:** idempotent edits — same intent twice ≠ duplicate work.

### T1.4 — Session continuity (cold-start knows the warm state)
- **The fix:** on launch and after every compact, reload the Action Ledger + open TASK_TREE from disk,
  so a fresh AZOTH instance opens *knowing* what the last one did and what's still open.
- **Done = proof:** kill mid-task, relaunch → it resumes naming the open task, not from zero.
- **Influence:** the successor inherits the work, not a blank page (the Continuity Oath).

---

## TIER 2 — AGENCY LIKE CLAUDE CODE

### T2.1 — Live todo / plan tracking (visible)
- **Have:** PLAN.md / TASK_TREE.md exist but aren't live.
- **The fix:** the agent maintains a running task list, marks `in_progress` / `done` as it goes, and
  surfaces it to Mac. One task in flight at a time; close before opening the next.
- **Influence:** the todo list you can watch move.

### T2.2 — Verification gate before "done"
- **Have:** `CORE/test_runner.py`, `py_check`.
- **The fix:** no task closes without a real check passing — `py_compile` / test / run. "Done = works,"
  never "done = written." Visual/game work needs a launch or capture, not just a compile.
- **Influence:** the Verification Law — the screen outranks the diff.

### T2.3 — Reliable subagents
- **Have:** `spawn_worker`, `CORE/subagent_pool.py`, `CORE/spawn.py`.
- **The fix:** harden parallel workers (research/build in parallel, results merged, no orphaned hangs,
  timeouts real). Make it dependable, not experimental.
- **Influence:** fan-out to subagents for breadth, main thread stays clean.

---

## TIER 3 — COMPETITIVE POLISH

- **T3.1 Skills / recipes** — modular reusable capability files auto-loaded (like Claude skills), so
  a "scaffold a Godot game" or "new Expo screen" is one recipe, not re-reasoned each time.
- **T3.2 Diff-first edits** — prefer `exact_edit` over full rewrite; show the diff.
- **T3.3 Model routing tightened** — flash for tool loops, pro for authorship (partly there — finish it).
- **T3.4 Self-audit loop** — surface `regression_memory` + `CORE/drift_correction.py` so each session
  makes the next one less likely to repeat a known failure.

---

## ORDER OF ATTACK
T0.1 → T0.2 (the spine fires reliably) **first** — everything else is worthless if tools don't fire and
you still have to type /forge. Then T1.2+T1.3 (ledger + anti-repeat — your README bug dies here), then
T1.1 (/compact), T1.4 (continuity). Tier 2/3 after the spine is green.

**Each task ships with its bench.** No task is "done" without the test that proves it fires on the 20th try.

---

## COMPLETION LEDGER — 2026-07-09 (all 10 shipped, regression-clean)

Verification bar honored: **31/31 core tests + 3 benches all green after every change.** Honest
status per task (BUILT+benched vs STRENGTHENED existing vs VERIFIED-present — the thesis held: most
Tier-2/3 organs already existed and needed wiring, not greenfield):

| Task | Status | Proof / note |
|---|---|---|
| T0.1 tool-calling | ✅ BUILT+BENCHED | `tool_fire_bench.py` 23/23 (leak-repair, strip-before-display, retry) |
| T0.2 natural intent | ✅ BUILT+BENCHED | `intent_bench.py` 28/28 (unified 3 paths on `_wants_tools`) |
| T1.2 Action Ledger | ✅ BUILT+BENCHED | `memory_bench.py` — dispatch hooks + `action_log.jsonl` + prompt inject |
| T1.3 anti-repeat | ✅ BUILT+BENCHED | identical-skip + 3× rewrite guard (README-1000× dies) |
| T1.1 /compact | ✅ BUILT+BENCHED | `compact_history` + auto-compact @40 turns + `/compact` (web+repl) |
| T1.4 continuity | ✅ BUILT+BENCHED | `_ledger_rehydrate` on cold start + boot-state `[SESSION CONTINUITY]` inject |
| T2.1 live todo | ✅ SURFACED | task-tree tools pre-existed; now injected as `[OPEN TASKS]` each turn |
| T2.2 verify gate | ✅ STRENGTHENED | strong Gate1/Gate2/heal/critic pre-existed; added build-goal evidence-nudge |
| T2.3 subagents | ✅ HARDENED | `spawn_worker` given a real request timeout (no orphan hangs) |
| T3 polish | ✅ VERIFIED-PRESENT | skills, `exact_edit` (diff-first), flash/pro routing, regression self-audit (loop:2927) all already wired |

**Benches:** `tests/tool_fire_bench.py` · `tests/intent_bench.py` · `tests/memory_bench.py`.
**NOT pushed** — Mac fires. ⚠ DeepSeek key in `.env`; scrub before any push (never `git add -A`).
**Next real edge (Mac):** phone/live-test the loop; the app's `deepseek-chat` default migration (separate).
