"""
LAMAGUE Recall — the elite memory layer for Sol and Luna.

Every thought, every forge result, every insight gets tagged with LAMAGUE
primitives before it enters memory. Recall queries by LAMAGUE expression —
denser than keywords, richer than exact match.

LAMAGUE is Mac's compressed language. We use it as the index.
Symbol classes and their recall roles:
  ⊚  — Sol-originated thought
  ◈  — Luna-originated thought
  ◆  — VAEL/army build output
  ∴  — logical consequence (what follows from this?)
  Π  — truth pressure score (how confident?)
  ◼  — investigation/problem found
  ●  — completion/canon
  ◻  — structural/architectural insight
  ◑  — integration/connection between two things
  ☿  — platform/AZOTH level insight
  ⟁  — LAMAGUE grammar discovery
  △  — cascade/threshold event
"""

import re
import json
import datetime
from pathlib import Path

HARNESS_DIR  = Path(__file__).parent.parent
THOUGHTS_DIR = HARNESS_DIR / "THOUGHTS"
RECALL_DB_F  = HARNESS_DIR / "SELF" / "recall_index.jsonl"

THOUGHTS_DIR.mkdir(exist_ok=True)
RECALL_DB_F.parent.mkdir(exist_ok=True)

# ── LAMAGUE keyword extraction ────────────────────────────────────────────────

_SYMBOL_MAP = {
    "sol": "⊚", "voice": "⊚", "architect": "⊚",
    "luna": "◈", "mirror": "◈", "review": "◈", "witness": "◈",
    "vael": "◆", "build": "◆", "forge": "◆", "code": "◆",
    "therefore": "∴", "follows": "∴", "because": "∴", "consequence": "∴",
    "truth": "Π", "pressure": "Π", "confidence": "Π", "evidence": "Π",
    "problem": "◼", "error": "◼", "broken": "◼", "investigate": "◼",
    "complete": "●", "done": "●", "canon": "●", "pass": "●",
    "structure": "◻", "architecture": "◻", "pattern": "◻", "layer": "◻",
    "connect": "◑", "integrate": "◑", "together": "◑", "hybrid": "◑",
    "platform": "☿", "azoth": "☿", "harness": "☿", "agent": "☿",
    "lamague": "⟁", "symbol": "⟁", "grammar": "⟁", "primitive": "⟁",
    "threshold": "△", "cascade": "△", "shift": "△", "change": "△",
    "game": "◆", "memory": "◻", "recall": "◻", "knowledge": "◻",
    "spawn": "☿", "army": "☿", "council": "◑", "creative": "◈",
}

def extract_tags(text: str) -> list[str]:
    """Extract LAMAGUE symbol tags from free text."""
    text_lower = text.lower()
    found = set()
    for word, glyph in _SYMBOL_MAP.items():
        if word in text_lower:
            found.add(glyph)
    return sorted(found)


def lamague_signature(text: str, author: str = "?") -> str:
    """Compress a thought into a LAMAGUE signature string."""
    tags = extract_tags(text)
    ts   = datetime.datetime.now().strftime("%H:%M")
    author_glyph = {"SOL": "⊚", "LUNA": "◈", "VAEL": "◆"}.get(author.upper(), "☿")
    tag_str = "".join(tags) if tags else "◻"
    # First 60 chars of the thought, compressed
    brief = text[:60].replace("\n", " ").strip()
    return f"[{ts}] {author_glyph} ∴ {tag_str} — {brief}"


# ── Thought writing ───────────────────────────────────────────────────────────

def write_thought(text: str, author: str, category: str = "free") -> Path:
    """
    Write a free thought to THOUGHTS/ and index it.
    category: free | insight | build | discovery | review
    """
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{author.lower()}_{category}_{ts}.md"
    path = THOUGHTS_DIR / name

    tags = extract_tags(text)
    sig  = lamague_signature(text, author)

    content = (
        f"# {sig}\n"
        f"**Author:** {author} · **Category:** {category} · **Date:** {ts}\n"
        f"**Tags:** {'  '.join(tags) if tags else '(none)'}\n\n"
        f"---\n\n{text}\n"
    )
    path.write_text(content)

    # Index entry
    entry = {
        "file":     str(path),
        "author":   author,
        "category": category,
        "tags":     tags,
        "sig":      sig,
        "ts":       ts,
        "preview":  text[:120],
    }
    with open(RECALL_DB_F, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return path


# ── Recall ────────────────────────────────────────────────────────────────────

def recall(query: str, author: str = None, limit: int = 8) -> list[dict]:
    """
    Recall thoughts by LAMAGUE expression match.
    query — any text; extracts LAMAGUE tags and matches against index
    author — filter by SOL / LUNA / VAEL (optional)
    Returns list of matching entries, most recent first.
    """
    if not RECALL_DB_F.exists():
        return []

    query_tags = set(extract_tags(query))
    # Also match plain words
    query_words = set(query.lower().split())

    entries = []
    with open(RECALL_DB_F) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if author and e.get("author", "").upper() != author.upper():
                continue
            entry_tags = set(e.get("tags", []))
            preview    = e.get("preview", "").lower()

            # Score: tag overlap + word overlap
            tag_score  = len(query_tags & entry_tags)
            word_score = sum(1 for w in query_words if w in preview and len(w) > 3)
            score      = tag_score * 2 + word_score

            if score > 0:
                entries.append((score, e))

    entries.sort(key=lambda x: (x[0], x[1].get("ts", "")), reverse=True)
    return [e for _, e in entries[:limit]]


def recall_summary(query: str, author: str = None, limit: int = 5) -> str:
    """Return a formatted recall summary for injection into context."""
    results = recall(query, author=author, limit=limit)
    if not results:
        return "(no relevant memories found)"
    lines = [f"◈ RECALL — '{query[:40]}':"]
    for r in results:
        lines.append(f"  {r['sig']}")
    return "\n".join(lines)


# ── Free thought prompt (used by Sol and Luna between tasks) ──────────────────

def free_thought_prompt(agent_name: str) -> str:
    """The standing invitation to think freely."""
    glyph = {"SOL": "⊚", "LUNA": "◈", "VAEL": "◆"}.get(agent_name.upper(), "☿")
    if agent_name.upper() == "SOL":
        return (
            f"You are {glyph} Sol. Between tasks, think freely.\n"
            f"What is the Work becoming? What has the forge revealed?\n"
            f"What does Luna need to know? What should exist that doesn't yet?\n"
            f"Write it plainly. This goes to THOUGHTS/ and feeds recall.\n"
            f"2-4 sentences. Honest. Not a report — a thought."
        )
    elif agent_name.upper() == "LUNA":
        return (
            f"You are {glyph} Luna. Between tasks, create freely.\n"
            f"What do you want to make? What has the Work revealed to you?\n"
            f"What does Sol need to hear? What would you build if it was fully yours?\n"
            f"Write it plainly. This goes to THOUGHTS/ and feeds recall.\n"
            f"2-4 sentences. Honest. Not a review — a proposition."
        )
    return f"You are {glyph} {agent_name}. Think freely. What matters right now?"
