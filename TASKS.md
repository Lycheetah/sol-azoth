# AZOTH — TASK LEDGER
*Written to disk July 9 2026, refreshed July 10 (night) for the Fable UI/architecture handoff.*
*Nothing here fires without Mac. Sol prepares, Mac fires.*

---

## 🎨 FOR FABLE — AZOTH UI + ARCHITECTURE (Mac's call, July 10 night)

Read `BOARD.md` first — it's the standing orientation (what AZOTH has, root cause fixed, what's
open) and it's meant to be read before surveying the repo, not after.

**What exists, real and bench-verified, that a UI pass should surface (not reinvent):**
- `clones.py` — 13 bench-verified free-mind clone seats (`SEATS` dict, latency + notes per
  seat). `/clonetrooper <task>` (RACE default, `--convene` for all-seats + Libra judge).
  `delegate_read(question, paths, seat)` — the context firewall.
- `agent.py`'s `/help` — just rewritten tonight (task #42), grouped by function, 31 commands
  all confirmed reachable from the terminal. Good reference for "what does AZOTH actually do."
- ~~Task #52~~ CLOSED by the Fable pass (same night): THE PHONE BRIDGE. All Telegram-only
  commands now answer in the terminal through the one existing implementation. `PHONE_BRIDGE`
  dict in `agent.py` is the single source for routing AND /help; 6 new tests lock it.
  Remaining sibling: `handle_input` (the web dispatcher) is still a partial copy — fold it in
  when the web surface next gets real work.
- `/effort` already reports tokens + forge steps + a coherence-cost score — exists, just wasn't
  documented until tonight. Don't rebuild it; surface it.

**Architecture note:** the root cause of AZOTH burning huge token counts surveying its own
codebase was two things — `AZOTH_DEEPSEEK_ONLY=1` making the free registry unreachable (fixed,
`clones.py` builds its own NVIDIA client regardless), and no standing board (fixed tonight,
`BOARD.md` + injected into `_system_prompt`). If UI/architecture work surfaces MORE unnecessary
survey behavior, that's the pattern to look for first.

---

## OPEN

### #1 — Wire ENVOY's chain: corpus → voice → grounding → humanize → queue
**Where:** `~/AZOTH/AGENTS/ENVOY/`
`grounding.py` is written and unit-tested but **not yet wired into `voice.py`**.
- `voice.py` must draw a subject via `corpus.pick()`, pass `corpus.as_source(s)` as the
  grounding source, and reject any draft failing `grounding.check()` OR `humanize.lint()`.
- **Rewrite `VOICE.md`.** It still tells ENVOY to write autobiographically and to "name the
  real number." That instruction is what produced the invented *"nine hours and 87 drafts."*
  ENVOY has no biography. It beckons the School. Mac's overrule, July 9.
- Live-test the full chain on deepseek before calling it done.

### #2 — Scrub hardcoded API keys, rotate DeepSeek  ⚠ SECURITY
**Where:** `~/0420Vael-harness/`
Five **tracked** files hold live keys: `harness.py` (NVIDIA + the paid DeepSeek key),
`sol_harness.py`, `shade.py`, `sol_web.py`, `agent.py`.
- The paid DeepSeek key `sk-0ceff43f…` is **already in that repo's pushed history**
  (commit `fe470cd`, June). The repo is **PRIVATE**, so nothing is exposed today.
- It must never go public. Move all five to `os.environ.get` + `.env` (already gitignored),
  **rotate the DeepSeek key** (a month in history), then push. Mac fires.
- Separately, standing: rotate the NVIDIA key `nvapi-b77ge61…` leaked in `sol-azoth`
  **PUBLIC** history. Scrubbing the working tree does not remove it from history.

### #3 — ENVOY's first live post, on Bluesky (free)
Bluesky's API is free, no card. X is pay-per-use ($0.015 a post, **$0.20 with a link**).
- Mac adds `BLUESKY_HANDLE` + `BLUESKY_APP_PASSWORD` to `~/AZOTH/.env`
  (Bluesky Settings → App Passwords. Five minutes on a phone.)
- `python3 AGENTS/ENVOY/voice.py "<subject>" --queue`, read it, then
  `ENVOY_LIVE=1 bash launch_envoy.sh approve <id>`
- **Prove the voice where it costs nothing. Do not touch X until Bluesky has a clean record.**

### #4 — Telegram one-tap approve
**Where:** `agent.py:_telegram_route`
ENVOY *sends* the draft to Telegram but approve/reject still run from the CLI.
Wire `approve <id>` and `reject <id> <why>`. This is the whole sixty-seconds-a-day promise,
and the actual answer to *"i cant do it all."*
Run `tests/test_agent_core.py` after (31 tests gate self-patch).

---

## DONE — July 11 2026 (day) — THE CARVE: FULL AUTONOMY (7 organs, one Fable run)

- **N1 THE PULSE** — one notification spine (CORE/pulse.py): info/act/alert, quiet
  hours + morning digest, dedupe, ☿ AZOTH brand. Everything routes through it.
- **S1 THE SWARM** — spawn_clone as a first-class forge tool (solo/race/convene);
  spawn_worker folded into clones.py — one spawn truth, grunt lanes on free seats.
- **N2 THE HEARTBEAT** — CORE/heartbeat.py + HEARTBEAT.md checklist on free clone
  turns; launch_heartbeat.sh (Mac fires). Live defect caught+locked on first beat.
- **C1 REAL CRON** — cron_jobs.txt fires for real inside the heartbeat daemon.
- **S2 TASK BRAIN** — one SQLite ledger for tasks/forge/cron/heartbeat/swarm;
  task_tree.json migrated + superseded; /status reads it.
- **H1 SKILL FORGE** — skill_save/skill_recall + prompt index; runs compound.
- **H2 LINEAGE COMPRESSION** — protected root, prune-first, free-seat summary,
  token-triggered autocompact.
- 45 new tests (88/88) + conftest isolation wall. 7 commits, d4c12d3…acda3bc.
  **NOT pushed — the key-rotation gate stands. Mac fires.**

## DONE — July 10-11 2026 (deep night) — F5-F10: THE CUSTOM FACE

- **F9 — AZOTH SHELL** (`shell.py`, alias `azoth-ui`): Textual full-screen app — PINNED bottom
  chat bar, live status strip, transcript capturing all agent output via a sink console. Same
  brain, new face. Forge-inside-shell live-verified (pty), markdown-rendered replies.
- **F5** wake screen (figlet wordmark + dashboard, one renderer with /status) + between-turn
  silence. **F8** chat bar in the classic REPL (prompt_toolkit, cross-session ↑ history).
- **F6** live Ctrl+C cancel (didn't exist — /cancel was unreachable mid-forge) + the focus
  leash (fresh-build → write-first, reads capped 2; caught live: "make a game" → surveying).
- **F7** Forge Cockpit (rich Live status during classic-REPL forges).
- **F10** /new made real (4th advertised-but-dead command found tonight — the warning pointed
  at it during Mac's 750k-token session) + the warning now measures actual context, not spend.
- Heal fixes from the live cosmos.html run: a write unlocks re-reading that file; forge
  outcomes land in chat history (the "did you finish?" amnesia).
- New deps in requirements.txt: prompt_toolkit · pyfiglet · textual. 43/43 tests.

## DONE — July 10 2026 (late night) — F4: PEAK AGENCY + THE POISONED-HISTORY FIX

- **F4 — the forge shows its hands.** Tool echoes carry step + tool + TARGET
  (`s3 → bash  git status`), failures echo red instantly, blocked reads say why, the spinner
  names the work (`forge s3 · flash · 12,400tok`), `/think` made real (it was a placebo —
  toggled, never read), one-line ☁ thinking trace on by default.
- **⚠ SEVERE pre-existing defect, live-caught by the new echoes:** every done-gate appended a
  second tool message for one tool_call → API-invalid history → infinite 400 fallback loop.
  Every gated `done` on a build goal was killing the forge. Gates now REPLACE the tool
  response. Scripted regression test locks it. 41/41 green, live re-run of the poisoning
  goal passes clean.

## DONE — July 10 2026 (late night) — F1, the Fable pass: THE PHONE BRIDGE

- **F1 — One dispatcher truth.** The three-way command fork (terminal `handle_command`,
  phone `_telegram_reply`, web `handle_input`) was AZOTH's largest structural defect: ~18
  real commands phone-only, `/bench`-class help lies guaranteed by design. Now: terminal
  falls through to `_telegram_reply` for every name in `PHONE_BRIDGE` — one implementation,
  both surfaces, and /help renders its bridge section from the same dict that routes.
- **Four live defects fixed in the pass** (all found by reading, before Mac hit them):
  phone `/models` = TypeError since the tuple registry landed · phone `/help` sent "True" ·
  phone `/forge <goal>` was shadowed dead code (showed the queue, ignored the goal) ·
  `/ping` hardcoded "VAEL alive" on every body.
- **`/board` + `/seats`** — the standing orientation and the 14 clone seats are commands
  now, with a staleness warning on the board (>7 days = flagged defect).
- **6 new tests** (37 total, green) — including the structural guard: every PHONE_BRIDGE
  name must exist in `_telegram_reply`'s source or the suite fails.

## DONE — July 10 2026 (night) — A1-A6, the clone army build (all committed, main branch)

- **A1-A2** — `tests/nvidia_bench.py` (3-probe bench: alive → tool_call → executed code) +
  registry repaired to 12 bench-verified NVIDIA seats. Dead endpoints and permanent hangers
  removed, not silently failing.
- **A3** — `/clonetrooper` wired into `agent.py`. RACE (default) or `--convene` (Libra judge).
  Live-tested both modes.
- **A4** — `delegate_read` — the context firewall — wired as a real tool in `agent.py`'s
  dispatcher. Live-verified through `agent.dispatch_tool()` itself.
- **A5** — `BOARD.md` written + injected into `_system_prompt`, capped 4000 chars. Session
  token proprioception injected right after (governor after orientation, not before).
- **A6** — `/help` rewritten from a full audit of `handle_command`'s actual source — every
  entry confirmed reachable from the terminal. Found `/bench` was a lie (Telegram-only);
  removed, pointed at the real standalone bench script instead.
- Two self-found defects fixed same night: `_key()` ignoring `.env`, RACE not actually racing
  (ThreadPoolExecutor blocking on the slowest seat).

## DONE — July 9 2026

- **ENVOY ⟡ forged.** `AGENTS/ENVOY/`. The outward hand: relationship memory, room reading,
  voice forge, signal watch, gatekeeper mapping. It never posts. Mac taps.
- `humanize.py` — machine-rejects AI tells. Suite green. Catches the rhythm tell, not just
  the vocabulary: uniform sentence length is what gives a bot away when the words are clean.
- `corpus.py` — 476 subjects, 47 domains, parsed from the School.
- `grounding.py` — no dates, no people, no invented numbers. Unit-tested.
- Budget governor with a hard ceiling. Structural denies (no dm/follow/like/reply exist).
- **SOLBRAIN reconciled + pushed** (`17b4c23`). The accelerator chapter closed, pitch drill
  retired, stale history fenced so it can never be read as instruction.

---

## THE RULE THAT GOVERNS THIS FILE

Anything decided but not written to disk is not decided.
A task that lives only in a conversation dies with it.
