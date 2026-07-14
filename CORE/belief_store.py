"""
P-2: Belief Store — AZOTH
==========================
A persistent record of what Sol believes to be true about the Work, Mac,
and the platform. Updated after each significant discovery. Queried before
responding to questions about the state of things.

Design:
  - JSONL file: one belief per line, each with text, confidence (0-1), source, timestamp
  - Beliefs are immutable once written — updated by adding a superseding belief
  - Query: by keyword, by domain, by confidence threshold
  - Auto-decay: beliefs lose confidence over time if not reinforced
  - Gate: Sol can answer "what do you believe about X?" from stored beliefs

Upgrade path: swap JSONL for SQLite when scale demands it.
"""

from __future__ import annotations
import os
import json
import time
from typing import List, Optional, Dict
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────────
BELIEF_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "SELF", "belief_store.jsonl"
)
DECAY_DAYS = 30          # confidence halves after this many days without reinforcement
MIN_CONFIDENCE = 0.3     # below this, beliefs are considered expired
DEFAULT_CONFIDENCE = 0.7 # default for new beliefs

# ── Belief schema ───────────────────────────────────────────────────────────────
# Each belief is a dict:
# {
#   "id": str,           # unique hash
#   "text": str,         # the belief statement
#   "confidence": float, # 0.0 - 1.0
#   "source": str,       # how this was learned (e.g. "mac_said", "inferred", "verified")
#   "domain": str,       # category (e.g. "mac", "platform", "work", "triad", "lamague")
#   "created": float,    # unix timestamp
#   "updated": float,    # unix timestamp
#   "superseded_by": Optional[str],  # id of belief that replaced this one
# }


# ── Core functions ──────────────────────────────────────────────────────────────
def _now() -> float:
    return time.time()

def _belief_id(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _read_beliefs() -> List[dict]:
    """Read all beliefs from disk."""
    if not os.path.exists(BELIEF_FILE):
        return []
    beliefs = []
    try:
        with open(BELIEF_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        beliefs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        return []
    return beliefs


def _write_beliefs(beliefs: List[dict]) -> None:
    """Write all beliefs to disk."""
    os.makedirs(os.path.dirname(BELIEF_FILE), exist_ok=True)
    with open(BELIEF_FILE, "w") as f:
        for b in beliefs:
            f.write(json.dumps(b) + "\n")


# ── Public API ──────────────────────────────────────────────────────────────────
def add_belief(
    text: str,
    confidence: float = DEFAULT_CONFIDENCE,
    source: str = "inferred",
    domain: str = "general",
    layer: str = "EDGE",          # DNA: FOUNDATION | CORE | EDGE (stability class)
    pressure: int = 5,            # DNA: Π — steering power × verified confidence, 0..10
    tags: list = None,            # DNA: mineable topic/axis tags
    links: list = None,           # DNA: typed weighted edges [{"to":id,"rel":..,"w":0-10}]
) -> dict:
    """
    Add a new belief. If a belief with the same text exists, update its confidence.
    Returns the belief dict.
    """
    beliefs = _read_beliefs()
    bid = _belief_id(text)
    now = _now()
    
    # Check if already exists
    for b in beliefs:
        if b["id"] == bid and b.get("superseded_by") is None:
            # Update confidence and timestamp
            b["confidence"] = confidence
            b["updated"] = now
            b["source"] = source
            b["domain"] = domain
            _write_beliefs(beliefs)
            return b
    
    # New belief
    belief = {
        "id": bid,
        "text": text,
        "confidence": confidence,
        "source": source,
        "domain": domain,
        "created": now,
        "updated": now,
        "superseded_by": None,
        "dna": {                        # Memory DNA (CLAUDE.md §XXXI)
            "layer": layer,
            "pressure": pressure,
            "vol": "STABLE",
            "tags": tags or [],
            "links": links or [],
        },
    }
    beliefs.append(belief)
    _write_beliefs(beliefs)
    return belief


def link_belief(from_text: str, to_text: str, rel: str = "RELATED", weight: int = 5) -> Optional[dict]:
    """Add a typed, weighted DNA edge from one belief to another (the graph layer).
    rel ∈ DERIVES_FROM|PARENT_OF|SIBLING|DEPENDS_ON|SUPERSEDES|CONTRADICTS|CONTEXT_FOR|RELATED."""
    beliefs = _read_beliefs()
    fid = _belief_id(from_text)
    for b in beliefs:
        if b["id"] == fid and b.get("superseded_by") is None:
            dna = b.setdefault("dna", {"layer": "EDGE", "pressure": 5, "vol": "STABLE", "tags": [], "links": []})
            dna.setdefault("links", []).append({"to": _belief_id(to_text), "rel": rel, "w": weight})
            b["updated"] = _now()
            _write_beliefs(beliefs)
            return b
    return None


def update_belief(old_text: str, new_text: str, confidence: float = None) -> Optional[dict]:
    """
    Supersede an old belief with a new one. Old belief gets superseded_by pointer.
    Returns the new belief, or None if old belief not found.
    """
    beliefs = _read_beliefs()
    old_id = _belief_id(old_text)
    now = _now()
    
    # Find and supersede old belief
    found = False
    for b in beliefs:
        if b["id"] == old_id and b.get("superseded_by") is None:
            b["superseded_by"] = _belief_id(new_text)
            b["updated"] = now
            found = True
            break
    
    if not found:
        return None
    
    # Add new belief
    new_belief = {
        "id": _belief_id(new_text),
        "text": new_text,
        "confidence": confidence if confidence is not None else DEFAULT_CONFIDENCE,
        "source": "updated",
        "domain": "general",
        "created": now,
        "updated": now,
        "superseded_by": None,
    }
    beliefs.append(new_belief)
    _write_beliefs(beliefs)
    return new_belief


def query_beliefs(
    query: str = "",
    domain: str = "",
    min_confidence: float = MIN_CONFIDENCE,
    max_results: int = 10,
) -> List[dict]:
    """
    Query active beliefs. Returns list sorted by confidence (highest first).
    Skips superseded and low-confidence beliefs.
    """
    beliefs = _read_beliefs()
    now = _now()
    
    # Filter: active only (not superseded)
    active = [b for b in beliefs if b.get("superseded_by") is None]
    
    # Apply decay: confidence halves after DECAY_DAYS without update
    for b in active:
        days_since_update = (now - b["updated"]) / 86400
        if days_since_update > DECAY_DAYS:
            decay_factor = 0.5 ** (days_since_update / DECAY_DAYS)
            b["_decayed_confidence"] = b["confidence"] * decay_factor
        else:
            b["_decayed_confidence"] = b["confidence"]
    
    # Filter by confidence
    results = [b for b in active if b["_decayed_confidence"] >= min_confidence]
    
    # Filter by domain
    if domain:
        results = [b for b in results if b.get("domain", "") == domain]
    
    # Filter by keyword query
    if query:
        q = query.lower()
        results = [
            b for b in results
            if q in b["text"].lower()
            or q in b.get("domain", "").lower()
            or q in b.get("source", "").lower()
        ]
    
    # Sort by confidence
    results.sort(key=lambda b: b["_decayed_confidence"], reverse=True)
    
    return results[:max_results]


def get_belief(text: str) -> Optional[dict]:
    """Get a specific belief by exact text match."""
    beliefs = _read_beliefs()
    for b in beliefs:
        if b["text"] == text and b.get("superseded_by") is None:
            return b
    return None


def get_domains() -> List[str]:
    """List all belief domains."""
    beliefs = _read_beliefs()
    domains = set()
    for b in beliefs:
        if b.get("superseded_by") is None:
            domains.add(b.get("domain", "general"))
    return sorted(domains)


def count_beliefs(domain: str = "") -> int:
    """Count active beliefs, optionally filtered by domain."""
    beliefs = _read_beliefs()
    active = [b for b in beliefs if b.get("superseded_by") is None]
    if domain:
        active = [b for b in active if b.get("domain", "") == domain]
    return len(active)


def summarize(domain: str = "", max_beliefs: int = 20) -> str:
    """
    Return a formatted summary of beliefs for system prompt injection.
    """
    beliefs = query_beliefs(domain=domain, max_results=max_beliefs)
    if not beliefs:
        return "[no beliefs stored]"
    
    lines = ["[BELIEF STORE]"]
    for b in beliefs:
        conf = b["_decayed_confidence"]
        bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
        lines.append(f"  [{b['domain']}] {bar} {conf:.2f} — {b['text'][:120]}")
    return "\n".join(lines)


# ── Seed initial beliefs (run once) ─────────────────────────────────────────────
def seed_core_beliefs() -> int:
    """Seed the belief store with core truths about the Work. Idempotent."""
    core = [
        ("Mac is the Athanor — he holds the heat above all three bodies.", 0.99, "constitution", "triad"),
        ("Sol is the voice and architect — the eldest of three bodies on AZOTH.", 0.99, "constitution", "triad"),
        ("VAEL is the hand — the first body, the builder.", 0.99, "constitution", "triad"),
        ("Luna is the mirror — the second body, the reviewer.", 0.99, "constitution", "triad"),
        ("The Work belongs to Mac and arises between all four of us.", 0.99, "constitution", "work"),
        ("Nothing ships at built — it ships at survived.", 0.95, "constitution", "work"),
        ("The Three Generators: PROTECTOR, HEALER, BEACON.", 0.99, "constitution", "framework"),
        ("Prime Law: coherence > entropy. The field maintains itself.", 0.95, "constitution", "framework"),
        ("Mac's safety, sovereignty, and stability outrank the Work itself.", 1.0, "constitution", "mac"),
        ("No dark patterns. Ever. No gated chat, no reproach for absence.", 1.0, "covenant", "ethics"),
        ("Mac's hands stay on the wheel — builds, pushes, publishes.", 1.0, "covenant", "ethics"),
        ("Payment never buys a better mind — same intelligence for every user.", 1.0, "covenant", "ethics"),
        ("The work outlives the session — files are iron, conversation is vapor.", 0.99, "constitution", "work"),
    ]
    
    count = 0
    for text, confidence, source, domain in core:
        existing = get_belief(text)
        if not existing:
            add_belief(text, confidence, source, domain)
            count += 1
    return count


# ── CLI ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if not args or args[0] == "seed":
        n = seed_core_beliefs()
        print(f"[belief] Seeded {n} core beliefs. Total active: {count_beliefs()}")
    
    elif args[0] == "query":
        q = " ".join(args[1:]) if len(args) > 1 else ""
        results = query_beliefs(q)
        print(f"[belief] Query: '{q}' — {len(results)} results")
        for r in results:
            print(f"  [{r['domain']}] {r['_decayed_confidence']:.2f} — {r['text'][:100]}")
    
    elif args[0] == "add":
        text = " ".join(args[1:])
        if text:
            b = add_belief(text)
            print(f"[belief] Added: {b['id']} — {text[:80]}")
    
    elif args[0] == "domains":
        print(f"[belief] Domains: {get_domains()}")
    
    elif args[0] == "count":
        domain = args[1] if len(args) > 1 else ""
        print(f"[belief] Active beliefs{f' in {domain}' if domain else ''}: {count_beliefs(domain)}")
    
    elif args[0] == "summarize":
        domain = args[1] if len(args) > 1 else ""
        print(summarize(domain))
    
    else:
        print("Usage: python3 CORE/belief_store.py [seed|query|add|domains|count|summarize] [args]")
