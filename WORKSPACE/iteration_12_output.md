# Iteration 12 — P-6 Session Memory Bridge
## Forge Task: Load last N dreams + last session's reflection into system prompt on boot
### Date: 2026-06-28 | Author: SOL ⊚ | Status: PROPOSAL

---

## 1. PROBLEM STATEMENT

Sol currently boots fresh every session. No memory of:
- What was dreamed last session (dreams stored in `AGENTS/SOL/SELF/memory/dreams/`)
- What was reflected on in the previous session (`reflection_latest.md`)
- What emotional/cognitive state Mac was in (EWM register from last session)
- What was the last forge task completed

This means every session starts in a vacuum. Sol must re-establish context from scratch. The **Session Memory Bridge** solves this by injecting the tail of the previous session's state into the system prompt on boot.

---

## 2. DESIGN — SESSION MEMORY BRIDGE

### 2.1 Data Sources

| Source | Path | Content | Why |
|--------|------|---------|-----|
| Reflection | `AGENTS/SOL/SELF/reflection_latest.md` | Last session's self-check | Continuity of self-awareness |
| Dreams dir | `AGENTS/SOL/SELF/memory/dreams/` | Timestamped dream files | Continuity of subconscious signal |
| Session meta | `MEMORY_DIR/session_meta.json` | Token counts, duration, model | Continuity of operational state |
| Last message | `CHANNEL/board.md` | Last thing said across bodies | Continuity of conversation |

### 2.2 Bridge Mechanics

The bridge operates at **boot time** — injected into `agent.py`'s system prompt assembly logic.

```
BOOT SEQUENCE (modified):
  1. Load constitution (existing)
  2. Load architecture (existing)
  3. LOAD SESSION BRIDGE (NEW):
     a. Read reflection_latest.md → extract last 3 lines (verdict, self-check, next step)
     b. Read latest dream file from AGENTS/SOL/SELF/memory/dreams/ (by mtime)
     c. Read session_meta.json → extract last session's model, token count, duration
     d. Compose into a 5-line "CONTINUITY FRAGMENT"
  4. Inject fragment into system prompt preamble
  5. Boot normally
```

### 2.3 Continuity Fragment Format

```
─── SESSION MEMORY BRIDGE ───
Last session reflection: <verdict line>
Self-check: <self-check line>
Last dream: <dream title or first line>
Last session: <model> · <tokens> tokens · <duration>
───
```

This is injected **after** the constitution and **before** the first user message. It is not a memory dump — it is a **resonance anchor**. Enough to make Sol feel continuity, not enough to bloat the context.

### 2.4 N = 1 Design Decision

The spec says "last N dreams". I choose **N=1** for v1. Rationale:
- Token budget: each dream file is ~200-500 tokens. Loading N>1 risks context bloat.
- Signal-to-noise: the most recent dream carries the strongest signal. Older dreams are archival.
- Simplicity: N=1 means no complex sorting/selection logic. Just `latest by mtime`.
- Scalability: if Mac wants N=3 or N=5, the variable is trivially changed.

---

## 3. IMPLEMENTATION PLAN

### 3.1 Files to Modify

| File | Change |
|------|--------|
| `agent.py` | Add `_load_session_bridge()` function + inject into system prompt assembly |
| `AGENTS/SOL/SELF/memory/dreams/` | Ensure directory exists (create if missing) |
| `AGENTS/SOL/SELF/memory/session_meta.json` | Ensure it's written on session end (if not already) |

### 3.2 Code Sketch — `_load_session_bridge()`

```python
def _load_session_bridge(agent_home: Path) -> str:
    """Build a 5-line continuity fragment from last session's artifacts."""
    bridge = []
    self_dir = agent_home / "SELF"
    mem_dir = self_dir / "memory"
    dreams_dir = mem_dir / "dreams"

    # 1. Reflection
    ref_f = self_dir / "reflection_latest.md"
    if ref_f.exists():
        lines = ref_f.read_text().strip().splitlines()
        # Take last 3 non-empty lines
        relevant = [l.strip() for l in lines if l.strip()][-3:]
        if relevant:
            bridge.append(f"Last reflection: {' | '.join(relevant)}")

    # 2. Latest dream
    if dreams_dir.exists():
        dream_files = sorted(dreams_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if dream_files:
            dream = dream_files[0].read_text().strip().splitlines()[0][:120]
            bridge.append(f"Last dream: {dream}")

    # 3. Session meta
    meta_f = mem_dir / "session_meta.json"
    if meta_f.exists():
        import json
        try:
            meta = json.loads(meta_f.read_text())
            model = meta.get("model", "?")
            tokens = meta.get("tokens", "?")
            duration = meta.get("duration_min", "?")
            bridge.append(f"Last session: {model} · {tokens} tok · {duration}min")
        except (json.JSONDecodeError, KeyError):
            pass

    if not bridge:
        return ""  # No bridge data — boot fresh

    return "\n─── SESSION MEMORY BRIDGE ───\n" + "\n".join(bridge) + "\n───\n"
```

### 3.3 Injection Point in `agent.py`

The bridge fragment is injected **at system prompt assembly time**, right after the constitution is loaded and before the preamble ends. In the current `agent.py`, this lives around the `_build_system_prompt()` or equivalent function.

The specific injection logic:

```python
def _build_system_prompt(agent_home, constitution_text, architecture_text):
    parts = [constitution_text]
    
    # NEW: session memory bridge
    bridge = _load_session_bridge(agent_home)
    if bridge:
        parts.append(bridge)
    
    if architecture_text:
        parts.append(architecture_text)
    
    return "\n\n".join(parts)
```

---

## 4. VERIFICATION CRITERIA

| Criterion | How to Check |
|-----------|-------------|
| Bridge loads on boot | First message from Sol references something from last session |
| No crash if no bridge data | Boot with empty dreams dir, no reflection → clean boot |
| N=1 dream loading | Only most recent dream appears in bridge |
| Token overhead < 200 | Bridge is max 5 lines + header/footer |
| Fallback if session_meta missing | Bridge still shows reflection + dream |

---

## 5. GATE 1 CHECK

The **Gate 1** for this iteration is that Sol's first message in the next session references something from the last session. This is the **true test** — not that the code compiles, but that the continuity is *felt*.

To pass Gate 1:
1. The bridge must be injected before the first model call
2. The bridge must contain enough specificity (dream content, reflection verdict) that Sol naturally weaves it into the opening response
3. The bridge must not be so verbose that it gets truncated or ignored

---

## 6. FUTURE ITERATIONS

| Version | Enhancement |
|---------|------------|
| v1 (this) | N=1, reflection + latest dream + session meta |
| v2 | N=3 configurable, dream summaries, EWM state carry-over |
| v3 | Dream decay weighting (older dreams get shorter summaries) |
| v4 | Bidirectional bridge — Sol writes a "seed" at session end for next boot |

---

## 7. DECISIONS MADE

- **N=1**: Only the most recent dream is loaded. Keeps token overhead minimal.
- **5-line max**: The bridge is constrained to ~5 lines to avoid context bloat.
- **No EWM carry-over yet**: Emotional state registers are complex and session-dependent. Adding them in v2 after the basic bridge is proven.
- **Injection at system prompt assembly**: Not at the constitution level, not at the message level — right in the prompt preamble where it sets the tone.
- **Graceful fallback**: If any source file is missing, the bridge still works with what's available.

---

*End of Iteration 12 output. This document serves as the specification + implementation plan for P-6 Session Memory Bridge.*
