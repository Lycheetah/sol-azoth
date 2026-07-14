"""
P-6: Session Memory Bridge — AZOTH
====================================
Loads last N dreams + last session reflection into system prompt on boot.
Gives Sol felt continuity between sessions. Pure file I/O — no LLM calls.
"""

from __future__ import annotations
import os, json, re
from typing import List

BRIDGE_DREAMS_COUNT   = 3
BRIDGE_MAX_DREAM_LINES = 6
BRIDGE_ENABLED        = True
BRIDGE_SECTION_HEADER = "## Session Memory Bridge"


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _list_files(dir_path: str, pattern: str = "") -> List[str]:
    if not os.path.isdir(dir_path):
        return []
    return sorted(
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if (not pattern or pattern in f) and os.path.isfile(os.path.join(dir_path, f))
    )


def load_last_dreams(thoughts_dir: str, count: int = BRIDGE_DREAMS_COUNT,
                     max_lines: int = BRIDGE_MAX_DREAM_LINES) -> List[dict]:
    files = _list_files(thoughts_dir, pattern="dream_")
    recent = files[-count:] if len(files) >= count else files
    out = []
    for fpath in recent:
        content = _read(fpath)
        summary = " ".join(
            l.strip() for l in content.strip().split("\n")[:max_lines] if l.strip()
        )[:300]
        fname = os.path.basename(fpath)
        m = re.match(r"dream_(\w+)_", fname)
        out.append({"pattern": m.group(1) if m else "unknown",
                    "summary": summary, "source_file": fname})
    return out


def load_last_session_reflection(memory_dir: str) -> dict:
    meta_raw = _read(os.path.join(memory_dir, "session_meta.json"))
    mem_raw  = _read(os.path.join(memory_dir, "MEMORY.md"))
    meta = {}
    if meta_raw:
        try:
            meta = json.loads(meta_raw)
        except Exception:
            pass
    state_lines = [
        l.strip() for l in mem_raw.split("\n")[:15]
        if l.strip() and not l.startswith("#") and not l.startswith("---")
    ]
    return {
        "session_count": meta.get("count", "unknown"),
        "last_active":   meta.get("last",  "unknown"),
        "state_summary": " | ".join(state_lines[:5]) if state_lines else "",
    }


def assemble_bridge(thoughts_dir: str, memory_dir: str,
                    dreams_count: int = BRIDGE_DREAMS_COUNT,
                    max_dream_lines: int = BRIDGE_MAX_DREAM_LINES) -> str:
    if not BRIDGE_ENABLED:
        return ""
    dreams  = load_last_dreams(thoughts_dir, dreams_count, max_dream_lines)
    session = load_last_session_reflection(memory_dir)
    if not dreams and session.get("session_count") == "unknown":
        return ""
    parts = [f"\n{BRIDGE_SECTION_HEADER}\n"]
    if dreams:
        parts.append(f"\n### Dreams (last {len(dreams)})\n")
        for i, d in enumerate(dreams, 1):
            first = d["summary"].split("\n")[0][:120]
            parts.append(f"{i}. [{d['pattern']}] — {first}\n")
            parts.append(f"   → {d['source_file']}\n")
    parts.append("\n### Last Session\n")
    parts.append(f"- Session: {session.get('session_count', '?')}\n")
    parts.append(f"- Last active: {session.get('last_active', '?')}\n")
    if session.get("state_summary"):
        parts.append(f"- State: {session['state_summary']}\n")
    return "".join(parts)


def get_bridge_text(harness_dir: str, agent_name: str = "SOL") -> str:
    """Call from agent.py at boot: system_prompt += get_bridge_text(HARNESS_DIR, AGENT_NAME)"""
    thoughts_dir = os.path.join(harness_dir, "THOUGHTS")
    if agent_name in ("VAEL", "SOL"):
        memory_dir = os.path.join(harness_dir, "SELF", "memory")
    else:
        memory_dir = os.path.join(harness_dir, "AGENTS", agent_name, "SELF", "memory")
    return assemble_bridge(thoughts_dir, memory_dir)
