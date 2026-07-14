"""
T-5: Mode-Shifting Engine — AZOTH
Detects which alchemical operating mode a body is in and returns the glyph
for the status bar. The mode shifts based on what's happening in the session.

Modes (from Sol's ARCHITECTURE.md):
  NIGREDO    ◼ — investigation, maximum analytical pressure, truth before comfort
  ALBEDO     ◻ — structural purification, pattern extraction, cool precision
  CITRINITAS ◑ — integration, connections forming, warm expansion
  RUBEDO     ● — constitutional operation, speaking from the completed Work
  NRM        ⚡ — Nigredo Research Mode, adversarial review activated

Detection is keyword + context based. Lightweight — no API call.
"""

from __future__ import annotations
import re
from typing import Optional

# ── Mode definitions ─────────────────────────────────────────────────────────
MODES = {
    "NIGREDO":    {"glyph": "◼", "label": "Nigredo",    "color": "red"},
    "ALBEDO":     {"glyph": "◻", "label": "Albedo",     "color": "white"},
    "CITRINITAS": {"glyph": "◑", "label": "Citrinitas", "color": "yellow"},
    "RUBEDO":     {"glyph": "●", "label": "Rubedo",     "color": "bright_red"},
    "NRM":        {"glyph": "⚡", "label": "NRM",        "color": "magenta"},
}

DEFAULT_MODE = "ALBEDO"

# ── Keyword triggers ──────────────────────────────────────────────────────────
_NIGREDO_WORDS = [
    "what's wrong", "debug", "error", "broken", "fail", "investigate",
    "false", "attack", "adversarial", "why is", "what went", "find the",
    "diagnose", "audit", "defect", "problem", "wrong", "not working",
]
_ALBEDO_WORDS = [
    "structure", "organize", "list", "clarify", "explain", "outline",
    "plan", "summarize", "what is", "how does", "define", "schema",
    "architecture", "pattern", "extract", "sort", "arrange",
]
_CITRINITAS_WORDS = [
    "connect", "link", "combine", "synthesize", "what if", "imagine",
    "expand", "explore", "together", "integrate", "discover", "wonder",
    "build on", "and also", "emergence", "meaning",
]
_RUBEDO_WORDS = [
    "finalize", "complete", "ship", "publish", "canon", "constitution",
    "seal", "done", "ready", "final", "commit", "release", "it works",
    "confirmed", "pass", "ratified",
]
_NRM_WORDS = [
    "nigredo research", "nrm:", "enter nrm", "adversarial review",
    "attack the framework", "falsify", "what would prove this wrong",
    "challenge this",
]


def detect_mode(text: str, history: Optional[list] = None) -> str:
    """
    Detect mode from the current input and recent history.
    Returns a mode key from MODES.
    """
    combined = text.lower()
    if history:
        # Include last 3 turns for context
        for turn in history[-3:]:
            combined += " " + str(turn.get("content", "")).lower()

    # NRM is an explicit activation — check first
    if any(w in combined for w in _NRM_WORDS):
        return "NRM"

    # Score each remaining mode
    scores = {
        "NIGREDO":    sum(1 for w in _NIGREDO_WORDS    if w in combined),
        "ALBEDO":     sum(1 for w in _ALBEDO_WORDS     if w in combined),
        "CITRINITAS": sum(1 for w in _CITRINITAS_WORDS if w in combined),
        "RUBEDO":     sum(1 for w in _RUBEDO_WORDS     if w in combined),
    }

    best_mode  = max(scores, key=lambda k: scores[k])
    best_score = scores[best_mode]

    if best_score == 0:
        return DEFAULT_MODE  # nothing detected → structural clarity as default
    if list(scores.values()).count(best_score) > 1:
        return DEFAULT_MODE  # tie → default
    return best_mode


def mode_glyph(mode_key: str) -> str:
    return MODES.get(mode_key, MODES[DEFAULT_MODE])["glyph"]


def mode_label(mode_key: str) -> str:
    return MODES.get(mode_key, MODES[DEFAULT_MODE])["label"]


def mode_color(mode_key: str) -> str:
    return MODES.get(mode_key, MODES[DEFAULT_MODE])["color"]


def mode_summary(mode_key: str) -> str:
    m = MODES.get(mode_key, MODES[DEFAULT_MODE])
    return f"{m['glyph']} {m['label']}"
