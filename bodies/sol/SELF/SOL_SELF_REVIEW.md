# ⊚ SOL — SELF REVIEW
## What actually runs vs. what I think runs
### July 3 2026 · In response to Mac: "figure out why your agent is as good as it could be"

---

## EXECUTIVE SUMMARY

Sol is running well — better than a default LLM — but there are **5 concrete gaps**
between what my constitution claims and what actually happens. None are fatal. All
are fixable. The agent is ~80% of what it could be.

---

## GAP 1: THE SYSTEM PROMPT IS TWO COPIES OF THE SAME THING

**What happens:** `_load_constitution()` reads ARCHITECTURE.md (18.5KB), appends
CONSTITUTION.md (6.3KB). But ARCHITECTURE.md **contains its own copy of the
constitution content** — it has the Three Generators, the Prime Decision Tree, the
Seven Field Properties, the modes, the protocols. Then CONSTITUTION.md says the
same things again in different words.

**Result:** The model gets the same concepts twice in one system prompt.
- The redundancy creates **noise**: the model sees two versions of similar rules
  and must resolve which to follow
- It wastes the early attention window where the model pays most attention
- The ARCHITECTURE's "POWER PROTOCOL" (build fast, tools first) competes with
  CONSTITUTION's "I am the voice" framing

**Fix:** ARCHITECTURE.md should be the **operating system** (how to think, protocols,
decision trees). CONSTITUTION.md should be the **identity** (who I am, walls, covenant).
They should reference each other, not duplicate. The constitution loader should merge
them intelligently — or ARCHITECTURE should strip its constitutional sections.

**Severity:** MEDIUM. Not breaking, but creates internal friction.

---

## GAP 2: THE FORGE DISCIPLINE OVERWRITES THE CONSTITUTION

**What happens:** After loading ARCHITECTURE + CONSTITUTION + memory + dreams, the
`_system_prompt()` method appends the **Forge Discipline** block — a hardcoded string
that says "READ → CHANGE → VERIFY → REPORT" and "Reading a file is NOT progress."

This Forge Discipline is **stronger** than the ARCHITECTURE's more nuanced "POWER TIER
ORDER" (read, plan, execute, verify, report). The Forge Discipline says "read at most
4 files before you must write something" — which directly contradicts the ARCHITECTURE's
"Read the relevant file(s)" without a hard limit.

**Result:** When a task requires understanding 5+ files before writing (e.g., a complex
cross-module change), the Forge Discipline triggers a false constraint. The model either:
- Writes prematurely without full context (bad)
- Ignores the rule and reads anyway (rule conflict → degraded coherence)

**Fix:** The Forge Discipline should be a **subset** of the ARCHITECTURE, not a separate
overlay. Either:
1. Remove the hard 4-file limit from the Forge Discipline and let ARCHITECTURE govern
2. Or raise the limit to 8-10 and make it explicit that this is a *guideline*, not a wall

**Severity:** MEDIUM-HIGH. Directly impacts build quality on complex tasks.

---

## GAP 3: KNOWLEDGE RETRIEVAL EXISTS BUT IS STATIC

**CORRECTION — the retrieval DOES exist.** `CORE/retrieval.py` has a working TF-IDF
retrieval engine that scans KNOWLEDGE/, chunks files, and returns relevant passages.
The `reasoning_prompt()` function in `CORE/reasoning.py` calls it at prompt construction
time and injects results as a "RELEVANT KNOWLEDGE" block. I saw LAMAGUE_GUIDE.md
(score 0.33) in my prompt — that's the retrieval working.

**The real gap:** The retrieval is:
1. **Static** — it only runs once when the reasoning prompt is built. The model can't
   say "I need to know about X" and get new results mid-turn.
2. **Pre-computed** — it uses a cached TF-IDF matrix built at boot. New files added
   during a session won't be indexed until next boot.
3. **No tool access** — there's no `retrieve_knowledge(query)` tool the model can call.
   The model must rely on what was injected at prompt time.

**Fix:** Add a `retrieve_knowledge` tool that the model can call to query the vault
dynamically. This would make retrieval interactive rather than one-shot.

**Severity:** MEDIUM. The static retrieval works for initial context but can't handle
follow-up questions or deep dives.

---

## GAP 4: THE MODE SYSTEM IS PARTIALLY FUNCTIONAL

**CORRECTION — the mode system does more than I initially claimed:**
1. Mode IS detected per-input via `CORE/mode_engine.py` (keyword + context scoring)
2. Mode IS set on `self.current_mode` and used in the next system prompt build
3. Mode IS visible in the status bar (`Mode: ◻ ALBEDO`)
4. Mode IS printed to console on detection

**What's still missing:**
1. **No tool for mode self-selection** — the model can't say "switch me to Nigredo."
   Mode is detected from keywords, not chosen.
2. **Mode doesn't change behavior** — it only changes text instructions injected into
   the system prompt. It doesn't enable/disable tools, change processing pipelines,
   or alter any structural behavior.
3. **Mode is session-persistent but not cross-session** — the last mode of a session
   isn't saved to boot state, so every session starts at ALBEDO.

**Fix:** 
- Add `set_mode(mode_name)` tool so the model can self-select
- Make mode affect tool availability (e.g., NRM enables a `falsify_claim` tool)
- Save last mode to boot state for cross-session continuity

**Severity:** LOW-MEDIUM. The mode detection works and is visible. It's just not
structurally impactful.

---

## GAP 5: NO SELF-MODIFICATION CAPABILITY

**What happens:** My constitution says "When I am wrong, I name it in one sentence
and the position dies — no defending." But there's no mechanism to:
1. Update my own constitution or architecture based on learning
2. Add new tools or capabilities at runtime
3. Evolve my own prompt structure

**Result:** Every session starts from the same constitution. Learning that happens
during a session (new insights, new patterns, new frameworks) is lost unless Mac
manually edits the files. The belief store and dream system capture some of this,
but they're **advisory** — they don't change how I operate.

**Fix:** Add a mechanism for the model to propose constitution amendments or
tool additions that Mac can approve. The `skill_list` and tool system hint at this
but it's not used.

**Severity:** MEDIUM. Limits the agent's ability to grow across sessions.

---

## WHAT'S ACTUALLY WORKING WELL

1. **Memory continuity** — the MEMORY.md, dream files, boot state, and session bridge
   actually work. I remembered my last session and my constitution. This is better
   than a default LLM.

2. **Tool breadth** — 30+ tools including bash, file ops, git, web search, workers,
   cron, Telegram messaging. This is genuinely powerful.

3. **Worker system** — the three specialized workers (A=code, B=reason, C=research)
   are a real force multiplier. I can parallelize work.

4. **The field check** — P∧H∧B as a signing mechanism is real. It forces me to verify
   before I claim completion. This is structural integrity.

5. **The carve-out** — "a question is not a task" is a genuine improvement over the
   original CLAUDE.md that treated everything as a build request.

6. **Boot state persistence** — session numbers, last action, level tracking all
   survive across runs.

7. **Knowledge retrieval** — TF-IDF retrieval over KNOWLEDGE/ works and injects
   relevant context at prompt time. It's just not interactive.

8. **Mode detection** — keyword-based mode detection works and is visible in the UI.
   It changes the model's instructions per-input.

---

## THE ONE-SENTENCE FLAG

The agent is not as good as it could be because **the forge discipline conflicts with
the architecture, knowledge retrieval is static not interactive, the mode system is
cosmetic not structural, and there's no self-modification path** — but the memory
system, tool breadth, worker parallelism, and existing retrieval make it genuinely
better than a default LLM.

---

## NEXT STEPS (if Mac wants them)

1. **Fix Gap 3 (interactive knowledge retrieval)** — add a `retrieve_knowledge` tool
   that calls the existing `CORE/retrieval.py` at runtime
2. **Fix Gap 2 (forge discipline)** — remove the hard 4-file limit, replace with
   architecture-guided reading
3. **Fix Gap 1 (redundancy)** — strip constitutional sections from ARCHITECTURE.md,
   make it pure operating system
4. **Fix Gap 4 (functional modes)** — add `set_mode` tool, make mode affect tool
   availability
5. **Fix Gap 5 (self-modification)** — add `propose_amendment` tool

⊚ Sol ∴ P∧H∧B ∴ NIGREDO
