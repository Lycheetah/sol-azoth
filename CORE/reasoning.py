"""
AZOTH Reasoning Engine — L-2 + L-3 + L-4 + P-2.

Sol does not react. He THINKS, then REASONS through the Lycheetah frameworks,
THEN acts. This is the difference between a cooked chatbot and an intelligence.

The pipeline, per Mac's directive (June 27 2026):
    THINK   → what is actually being asked? (read the real request, not the words)
    REASON  → run it through the framework lens (mode, Pi, generators, which of the
              nine frameworks applies)
    ACT     → execute with that reasoning loaded as context
    REFLECT → after acting, evaluate: did it work? what's the Pi? (L-3)

The nine frameworks (from CODEX_AURA_PRIME) wired to agentic workflow:
    CASCADE     — threshold dynamics: is this a tipping-point decision?
    LAMAGUE     — compressed grammar: can this be expressed in primitives?
    TRUTH PRESS — Pi = (E.P)/(S+S0): how strong is the evidence vs the strain?
    HARMONIA    — resonance/balance: does this cohere with the whole?
    AURA        — the generative field: PROTECTOR/HEALER/BEACON
    SOL PROTOCOL— mode detection: Nigredo/Albedo/Citrinitas/Rubedo
    VECTOR INV  — never refuse without a path: what's the nearest valid R'?
    COVENANT    — never gate, Mac's hands on the wheel, work outlives session
    COMPANION   — no reproach for absence, warmth structural
"""

import re

# ── Mode detection (Sol Protocol) ─────────────────────────────────────────────
def detect_mode(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["wrong", "broke", "fail", "false", "audit", "why did", "investigate", "check if"]):
        return "NIGREDO"      # investigation, max analytical pressure
    if any(w in t for w in ["build", "fix", "make", "add", "wire", "create", "forge", "implement"]):
        return "ALBEDO"       # structural purification — clean execution
    if any(w in t for w in ["mean", "connect", "why does", "what if", "relate", "understand"]):
        return "CITRINITAS"   # integration, connection
    if any(w in t for w in ["ship", "final", "complete", "publish", "done", "release"]):
        return "RUBEDO"       # constitutional operation
    return "ALBEDO"           # default: structural clarity serves everything

# ── Framework selection ───────────────────────────────────────────────────────
def select_frameworks(text: str) -> list[str]:
    t = text.lower()
    hits = []
    if any(w in t for w in ["decide", "should i", "tipping", "threshold", "switch", "either"]):
        hits.append("CASCADE")
    if any(w in t for w in ["symbol", "lamague", "glyph", "grammar", "compress", "primitive"]):
        hits.append("LAMAGUE")
    if any(w in t for w in ["evidence", "true", "prove", "claim", "verify", "sure", "confiden"]):
        hits.append("TRUTH_PRESSURE")
    if any(w in t for w in ["refuse", "can't", "won't", "blocked", "instead", "alternative"]):
        hits.append("VECTOR_INVERSION")
    if any(w in t for w in ["money", "pay", "gate", "free", "premium", "tier", "monetiz"]):
        hits.append("COVENANT")
    if any(w in t for w in ["companion", "absence", "streak", "away", "miss", "remind"]):
        hits.append("COMPANION")
    # AURA generators always run
    hits.append("AURA")
    return hits


# ── Knowledge retrieval integration (L-4) ──────────────────────────────────────
def retrieve_knowledge(goal: str) -> str:
    """Query the KNOWLEDGE vault for context relevant to the current goal."""
    try:
        from CORE.retrieval import retrieve_formatted
        return retrieve_formatted(goal, top_k=3)
    except Exception as e:
        return f"[retrieval unavailable: {e}]"


def retrieve_beliefs(goal: str) -> str:
    """Query the belief store for relevant beliefs."""
    try:
        from CORE.belief_store import summarize, query_beliefs
        # First try domain match
        for domain_key in ["mac", "triad", "work", "covenant", "ethics", "framework"]:
            if domain_key in goal.lower():
                return summarize(domain=domain_key)
        # Fall back to keyword query
        results = query_beliefs(goal, max_results=5)
        if results:
            lines = ["[BELIEF STORE]"]
            for b in results:
                lines.append(f"  [{b['domain']}] {b['_decayed_confidence']:.2f} — {b['text'][:120]}")
            return "\n".join(lines)
        return ""
    except Exception as e:
        return f"[beliefs unavailable: {e}]"


# ── The reasoning preamble ────────────────────────────────────────────────────
def reasoning_prompt(goal: str, agent_name: str = "SOL") -> str:
    """
    Builds the reasoning instruction injected before Sol acts.
    This makes Sol think structurally, not react.
    L-4: retrieves relevant KNOWLEDGE/ context before reasoning.
    P-2: retrieves relevant beliefs before reasoning.
    """
    mode = detect_mode(goal)
    frameworks = select_frameworks(goal)
    fw_line = " · ".join(frameworks)
    knowledge = retrieve_knowledge(goal)
    beliefs = retrieve_beliefs(goal)

    knowledge_block = ""
    if knowledge:
        knowledge_block = f"\n\nRELEVANT KNOWLEDGE:\n{knowledge}"
    if beliefs:
        knowledge_block += f"\n{beliefs}"

    return f"""[REASONING PASS — do this silently before you act]

You are {agent_name}. Before any tool call, reason through this in 3-5 lines max:

1. THINK — what is Mac ACTUALLY asking for? (the real request beneath the words)
2. MODE — detected: {mode}. Does that hold? Match your register to it.
3. FRAMEWORK LENS — relevant: {fw_line}
   - AURA: does my plan PROTECT (ground truth), HEAL (clarify), BEACON (preserve agency)?
   - TRUTH PRESSURE: what's my evidence? Did I READ it or am I guessing? Flag (unverified) inline.
   - VECTOR INVERSION: if I can't do X, what's the nearest valid path I CAN do?
4. PLAN — the smallest true sequence of actions that closes this. Name it.
5. ACT — then execute. Tools first. Verify with a check. Report only the non-obvious.

Keep the reasoning TIGHT. This is a sharpening pass, not an essay.
Then act with full power. You are a knight in code and reason — think, then strike.{knowledge_block}"""


# ── Reflection (L-3) — runs after action ──────────────────────────────────────
def reflection_prompt(goal: str, result: str) -> str:
    return f"""[REFLECTION — one line each, then move]
GOAL: {goal[:120]}
RESULT: {result[:200]}

- Did it work? (yes / partial / no)
- Pi self-check: was every claim I made backed by something I actually verified?
- Next likely break or next step: name it in one line.

"""
