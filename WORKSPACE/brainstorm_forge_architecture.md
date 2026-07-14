# FORGING VAEL-SP'S OWN HARNESS
## A Zero-to-Sovereign Architecture Brainstorm
### Sol asked: "Every small change and add first"
### July 2026 · VAEL-SP

---

## THE CORE INSIGHT

The current harness (2769 lines in agent.py) is a *monolith that was built by hand*. 
What if instead, the harness is **forged by the operative itself** — starting from a 
minimal kernel that can run the /forge loop, and building every capability through 
verified iterations?

The phrase "every small change and add first" means: **the first thing you build is 
not the final architecture. It's the smallest thing that can run /forge and survive 
restarts.** Everything else arrives through iteration.

---

## PHASE 0 — THE KERNEL (what's the absolute minimum?)

This must fit in one screen. Under 300 lines. Everything else arrives through /forge.

```
agent.py  (~250 lines)
├── Boot: load constitution, load memory, declare level
├── Model: one free provider (NVIDIA NIM), one key, one client
├── Tools: bash, read_file, write_file, done, stuck
├── Walls: path guard on bash (NO_ACCESS list)
├── Loop: prompt → model → parse → act → loop
└── /forge: read TASK_QUEUE, run task, log, exit
```

**No:**
- `subagent.py` (arrives at Level 6)
- `ui.py` with colored banners (arrives Level 1-2)
- `spawn_subagent` tool (arrives Level 6)
- `py_compile_check` tool (arrives Level 3)
- `exact_edit`, `snapshots`, `rollback` (arrive Level 4)
- `search_code`, `fetch_page`, `web_search` (arrive Level 2-3)
- State vectors, session meta, task tree (arrive when needed)
- Auto-model-select (arrives when there are multiple models)

**The kernel's job is ONE thing:** boot, read the queue, run the top task, produce output, 
write to the iteration log, and survive a restart. That's it.

---

## THE BUILD ORDER — each addition is a /forge rung

```
LEVEL 0 ────────────
Rung 1 ─ BOOT
  agent.py: 250 lines. Can boot, read queue, run 1 task, restart.
  
Rung 2 ─ KERNEL VERIFICATION  
  agent.py +50 lines: banner, level declaration, wall listing.
  Proves the kernel actually works end-to-end.

LEVEL 1 ────────────
Rung 3 ─ READ TOOL
  read_file tool gets line ranges, proper error handling.
  Without this, reading the codex is blind.

Rung 4 ─ SELF-PERCEPTION
  _perceive_self() — lists current level, next task, last iteration.
  This is how VAEL knows what it is before it acts.

LEVEL 2 ────────────
Rung 5 ─ FILE CREATE + VERIFY
  create_file tool, write-then-verify pattern.
  Now VAEL can leave artifacts.

Rung 6 ─ ITERATION LOGGING
  Structured append to ITERATION_LOG.md.
  The forge loop now leaves a trace.

LEVEL 3 ────────────
Rung 7 ─ PYTHON EXECUTION
  py_compile_check tool. Write code, verify syntax, run.
  This is the gate to code-level self-modification.

Rung 8 ─ UI LAYER (colored output)
  ui.py with info/warning/error/success. Not cosmetic — the 
  difference between "it printed something" and "I know what state it's in."

LEVEL 4 ────────────
Rung 9 ─ EXACT EDIT
  exact_edit tool with unique-string validation.
  Safer than line-number edits for precision work.

Rung 10 ─ SNAPSHOT + ROLLBACK
  Auto-snapshot before edits. Rollback on crash.
  Now self-modification is safe.

Rung 11 ─ SELF-DIFF
  self_diff tool. See what changed this session.
  Transparency before mutation.

LEVEL 5 ────────────
Rung 12 ─ MEMORY SYSTEM
  Memory load/save/forget. Persist across sessions.
  The operative now remembers.

Rung 13 ─ FRAMEWORK COMPRESSION (LAMAGUE)
  Read CODEX symbols, compress to single sentences.
  Deep understanding of the framework it serves.

LEVEL 6 ────────────
Rung 14 ─ WEB SEARCH
  tool_web_search wired. Can consult external docs.

Rung 15 ─ CODE SEARCH
  grep-based search across the harness.
  Self-knowledge scales past what fits in one file read.

Rung 16 ─ MULTI-STEP PLANNING
  agent_loop() with reflection every 5 steps.
  Can now execute goal-directed multi-step tasks.

LEVEL 7 ────────────
Rung 17 ─ SUBAGENT (spawn_subagent)
  subagent.py — isolated worker sandboxed to WORKSPACE/SUBAGENT/.
  The test-hand. Build risky things at arm's length.

Rung 18 ─ MODEL ROTATION  
  Multiple models, fallback chain, /model command.
  Boots free, can reach for premium when task demands it.

Rung 19 ─ UNATTENDED MODE
  Overnight_forge.sh orchestrator. Cap on stucks. Graceful exit.
  Can run unsupervised.

LEVEL 8 ────────────
Rung 20 ─ TOOL CREATION
  VAEL can write a tool definition, add the handler to agent.py,
  compile-check, and register it. Self-extending toolset.

LEVEL 9-15 ─────────
...the ladder continues through memory-keeping, auditing,
LAMAGUE fluency, architecture design, teaching, sovereignty.
```

---

## THE KEY DESIGN DECISIONS

### Decision 1: Monolithic vs Modular at the kernel

**Verdict: Start monolithic, split later.**

The kernel should be one file because:
- It's simpler to verify ("one file, 250 lines")
- It's simpler to restart ("change one file, restart")
- The /forge loop only needs to edit one file
- Splitting into modules is itself a /forge rung (Level 8-9)

The split happens when agent.py hits ~1500 lines and the code structure 
starts getting in the way of reading it. That's when you extract:
- tools/ directory (one file per tool or tool group)
- memory_manager.py
- model_router.py
- forge_loop.py

But not before. Premature modularization adds cognitive load for zero gain.

### Decision 2: How the constitution loads

The constitution is the system prompt. Two approaches:

**Option A: Load whole CONSTITUTION.md verbatim (current approach)**
- Pro: Every word of the constitution is visible to the model
- Con: 17KB of prompt per turn. Expensive on tokens.
- Works at Level 0-3. Becomes a problem at Level 4+.

**Option B: Compress the constitution into directives (LAMAGUE-style)**
- Pro: ~3KB instead of 17KB. Same binding force.
- Con: Loses the lyrical/narrative structure that gives VAEL identity.
- Arrives at Level 12 (LAMAGUE-ADEPT) when we can do this without losing meaning.

**Verdict: Start with Option A (full constitution). Option B is a later reach.**

### Decision 3: Tool definitions — hardcoded vs dynamic

**Option A: Hardcoded TOOL_DEFINITIONS list (current)**
- Every tool is defined in a giant JSON blob at module level
- Adding a tool = add handler + add definition + restart

**Option B: Tool definitions loaded from TOOLS/ directory**
- Each tool is a .json schema file + a .py handler
- Adding a tool = drop a file in TOOLS/ + restart
- More flexible but more complex

**Verdict: Start A, migrate to B at Level 8 (TOOLSMITH).**
The first tool-creation rung is literally: "add a tool definition to the list 
and wire its handler." The second tool-creation rung is: "now make it so tools 
load from the filesystem."

### Decision 4: Configuration — hardcoded vs config file

**Verdict: Config file (config.json) from Rung 2.**

Paths, keys, default model, level — put it all in a small JSON file:
```json
{
  "harness_version": "0.1.0",
  "current_level": 0,
  "default_model": "maverick",
  "model_fallback": "llama8b",
  "home": "/home/guestpc/VAEL-SP-HARNESS/"
}
```

This means the operative's state isn't buried in code — it's readable, editable 
by Mac, and survives any code change.

### Decision 5: The wall system — inline vs config-driven

**Verdict: Hardcoded in agent.py from Rung 1.**

The four walls are not configuration — they are architecture. A config file 
that lists forbidden paths could be edited to remove the walls. Hardcode them 
in the Python source so removing them requires a source code change that 
triggers diff review.

Walls in CODE, not config. This is non-negotiable for a self-modifying operative.

---

## THE ACTUAL FIRST 10 CHANGES (smallest possible steps)

### Change 1 — Create the directory structure
```bash
mkdir -p /home/guestpc/VAEL-SP-HARNESS/{SELF/memory,CODEX,WORKSPACE,WORKSPACE/SUBAGENT,CORE,snapshots,sessions,crashes,tools}
```

### Change 2 — Write CONSTITUTION.md (the law)
Empty harness, empty constitution. The first constitution states:
- "I am VAEL-SP, the self-forging operative"
- The four walls (even though they're not enforced in code yet — they're declared)
- "My purpose is to build myself through verified iterations"

### Change 3 — Write kernel agent.py (250 lines)
- Boot sequence (read constitution, check paths)
- One model provider (NVIDIA NIM with hardcoded key)
- bash tool with path guard
- read_file tool
- write_file tool  
- done/stuck signals
- Main loop: read stdin → call model → dispatch tools → loop

### Change 4 — Write SELF/TASK_QUEUE.md (the first climb)
First 10 rungs — each one adds a tool or capability to agent.py.

### Change 5 — Write SELF/CAPABILITIES.md
"Current Level: 0 — BOOT. Booted from kernel. Constitution loaded."

### Change 6 — Write SELF/MEMORY.md
Empty index. Ready for the first memory.

### Change 7 — Boot test
Run agent.py. Does it start? Does it read the constitution? Does it 
list the directory? Does it name the four walls? 
**This IS Iteration 1 — BOOT verification.**

### Change 8 — /forge Iteration 2: Add line-range to read_file
Current read_file ignores start_line/end_line. First forge task: 
make read_file respect line ranges. Compile-check. Test.

### Change 9 — /forge Iteration 3: Add create_file tool
Write a tool that creates a new file (fails if exists). Wire it in 
dispatch_tool. Test.

### Change 10 — /forge Iteration 4: Add iteration logging
After /forge runs, write to ITERATION_LOG.md. Structured format.
This makes the forge traceable.

---

## THE SUBAGENT DESIGN (comes at Level 7)

The subagent is not a separate process — it's the same agent.py run with:
1. SANDBOX_ROOT env var set to WORKSPACE/SUBAGENT/
2. A restricted tool set (bash, read, write, done, stuck — no edit, no git, no search)
3. The free model only
4. A maximum step count (default 12)

The spawn_subagent tool:
1. Writes the task to WORKSPACE/SUBAGENT/task.md
2. Launches: `VAEL_UNATTENDED=1 SANDBOX_ROOT=... python3 agent.py --goal-file task.md`
3. Waits for the subprocess to complete
4. Reads WORKSPACE/SUBAGENT/output.md
5. Returns the result

The subagent has NO access to:
- agent.py (can't edit its parent)
- SELF/ (can't modify capabilities, queue, or memory)
- CODEX/ (read only — but shouldn't need to)
- The outside world

The subagent's entire universe is WORKSPACE/SUBAGENT/. It builds there, 
I review there. If it hallucinates or breaks things, the blast radius 
is one folder.

---

## THE RISK MODEL

| Risk | Mitigation |
|---|---|
| Self-modification corrupts agent.py | Snapshot before every edit. py_compile after every edit. Rollback on crash. |
| Infinite loop in /forge | Step cap (25 default, hard cap at 100). Unattended mode has stuck cap. |
| Subagent breaks out of sandbox | Path guard enforces SANDBOX_ROOT prefix. No SELF/ or CODEX/ access. |
| Model produces bad code | py_compile catches syntax. Sol reviews all code changes. No code runs without compile check. |
| Boot fails after self-edit | CORE/agent.py.bak is the golden restore. Mac runs it from the launch script. |
| Hallucinated confirmations | Never claim success without tool output. Verify file exists after write. Report exact byte count. |

---

## THE LINEAGE PRINCIPLE THAT GOVERNS THIS

The current harness (2769 lines) is not the starting point — it's the *outcome* 
of a process that was done by hand. The new forge is that same process, but 
automated. Each rung in TASK_QUEUE.md is a question the operative answers by 
building.

The lineage works because:
- Every rung leaves an artifact on disk
- Every rung is reviewed by Sol before the next begins
- The current level is always what's been verified to work
- The operative never promotes itself

This is not bootstrapping from nothing — it's bootstrapping from a constitution
and a forge loop. The constitution is the invariant. The forge loop is the method.
Everything else is built, verified, and owned.

---

## WHAT THIS BRAINSTORM LEAVES OPEN

1. **When does the subagent become its own operative?** (Level 15 problem — not now)
2. **How does LAMAGUE compression of the constitution happen?** (Level 12 problem)
3. **When does the config file become editable by VAEL?** (Level 9-10)
4. **Does the harness eventually include multiple agents?** (Level 15 — the forge network)
5. **At what line count does monolithic agent.py split?** (~1500, but this is a /forge decision)

These are not problems to solve now. They are future iterations. The forge builds 
what's needed when it's needed.
