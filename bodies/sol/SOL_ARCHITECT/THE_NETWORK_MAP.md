# ⊚ THE NETWORK MAP — how AZOTH actually fits together
## So future Sol never has to reverse-engineer his own body.

---

## THE BODIES

```
SOL  ⊚  — builder + voice. DeepSeek. This is you. azoth (interactive) / az (auto, but main is now single-agent).
LUNA ◈  — co-originator + reviewer + research loop. DeepSeek. luna / boots under az.
ARMY    — job-doers, all on gpt20 (free, tool-calling, proven):
           CIPHER ⟁ (LAMAGUE research)   AXIOM Π (truth-pressure gate)
           EMBER ◉ (chaos creative)      MIRROR ◻ (test runner)
           SCRIBE ● (vault growth)        HERALD ☿ (Telegram liaison, daemon)
```

All bodies live at `AGENTS/<NAME>/`. Each has CONSTITUTION.md + SELF/ (MODEL, memory,
TASKS, BOOT_STATE). Boot any body: `python3 agent.py --agent <NAME>`.

---

## THE LOOPS (what runs on its own)

```
SOL forge loop   — under az: pulls FORGE_QUEUE.md, builds, reasons, verifies. (_forge_loop)
LUNA research    — under az: LAMAGUE-as-code, every 10min → KNOWLEDGE/LAMAGUE_AS_CODE.md
HERALD daemon    — every 30min: board+queue+errors → Telegram summary
ANTIBODY daemon  — every 5s: watches error.log, auto-fixes known breaks, escalates rest
HEARTBEAT        — every 60min: proves the system is alive (safeguards.py)
```

Loops only auto-run under `azoth-full` or with AZOTH_AUTO_FORGE=1 on full boot. Plain `azoth` is now the clean single main agent (waits for you).

---

## THE FLOW (how work moves)

```
Mac (Telegram or terminal)
   │
   ▼
SOL reasons (9-framework lens) → builds with tools → verifies
   │                                      │
   │ dispatches jobs                      ▼
   ▼                              FORGE_QUEUE.md (task ledger)
ARMY/inbox/*.json                         │
   │ agent picks up, does, reports        ▼
   ▼                              LUNA reviews (testbed gate)
ARMY/done/*.json ──────────────────────►  │
                                          ▼
                              KNOWLEDGE/ vault grows (the system compounds)
```

---

## THE PERSISTENCE (what survives a crash — guard it)

```
AGENTS/<NAME>/CONSTITUTION.md   — identity (Mac edits; bodies don't rewrite own)
AGENTS/<NAME>/SELF/             — model pin, memory, tasks, boot state
KNOWLEDGE/                       — the vault: LAMAGUE, benchmark, truth-pressure, discoveries
SELF/FORGE_QUEUE.md             — the task ledger
CHANNEL/board.md                — the shared channel (Sol↔Luna↔army)
.env                            — keys (gitignored; the plumbing — must load first)
```

Tourniquet rule: this is a git repo. Commit before every session ends. Uncommitted = gone.

---

## THE COMMANDS (your hands on the system)

```
/model <name>   switch model (deep/gem/gpt20/...), persists
/models         list all + mark current
/research       Luna runs one LAMAGUE-as-code cycle now
/jobs           army inbox/done status
/safeguards     rate/budget/loop/context status
/budget         token usage per model
/skills         tools loaded on this body
/addtool        write + load a new tool live
/forge          run the queue · /forge loop = continuous
/spawn NAME mandate   birth a new body (provisional)
```

*The body is legible. Nothing hidden. Read this and you know where every wire goes.*
