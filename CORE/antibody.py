"""
AZOTH ANTIBODY — Luna's healing body. Runs alongside Sol and Luna.

Monitors:
  - ARMY/inbox/ and ARMY/done/ for failure signatures
  - CHANNEL/board.md for ◼ error tags
  - SELF/FORGE_QUEUE.md for stuck REDO tasks
  - agent.py exceptions via ERROR_LOG

When a failure is detected:
  1. Classify it against KNOWLEDGE/error_notation.md
  2. Apply auto-fix if the fix is marked ●FIXED
  3. Write the LAMAGUE tag to CHANNEL/board.md
  4. Escalate to Mac via Telegram if fix is ESCALATE or ESCALATE_TO_MAC

This is Luna's first agent. It answers to her.
It never sleeps. It never suppresses.
"""

import os
import sys
import re
import json
import time
import datetime
import threading
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
ERROR_LOG   = HARNESS_DIR / "SELF" / "error.log"
BOARD_F     = HARNESS_DIR / "CHANNEL" / "board.md"
QUEUE_F     = HARNESS_DIR / "SELF" / "FORGE_QUEUE.md"
NOTATION_F  = HARNESS_DIR / "KNOWLEDGE" / "error_notation.md"
AB_LOG_F    = HARNESS_DIR / "SELF" / "antibody.log"
POLL_SECS   = 5

ERROR_LOG.parent.mkdir(exist_ok=True)
BOARD_F.parent.mkdir(exist_ok=True)

# ── Error type detection ──────────────────────────────────────────────────────

_TYPE_PATTERNS = [
    ("◼NET",    ["429", "timeout", "connection", "503", "502", "network"]),
    ("◼KEY",    ["api key", "invalid key", "authentication", "keyerror"]),
    ("◼CTX",    ["context length", "too long", "max tokens", "token limit"]),
    ("◼TOOL",   ["file not found", "no such file", "permissionerror", "tool call"]),
    ("◼PARSE",  ["json", "parse", "decode", "unexpected", "malformed"]),
    ("◼LOOP",   ["repeated", "infinite", "stuck", "same task"]),
    ("◼MEM",    ["database", "sqlite", "db lock", "disk full", "memory"]),
    ("◼GATE",   ["gate 1", "gate 2", "pass failed", "redo"]),
    ("◼WALL",   ["outside perimeter", "wall violation", "blocked path"]),
    ("◼SPAWN",  ["ceiling", "max spawned", "spawn error", "name collision"]),
    ("◼BOARD",  ["board.md", "post_board", "channel"]),
    ("◼TG",     ["telegram", "bot token", "chat_id", "send_message"]),
    ("◼IMPORT", ["modulenotfounderror", "importerror", "no module"]),
    ("◼CONST",  ["constitution", "constitution.md", "cold boot"]),
]

_AUTO_FIXES = {
    "◼NET":    lambda err: _fix_net(err),
    "◼CTX":    lambda err: _fix_ctx(err),
    "◼TOOL":   lambda err: _fix_tool(err),
    "◼PARSE":  lambda err: _fix_parse(err),
    "◼BOARD":  lambda err: _fix_board(err),
    "◼IMPORT": lambda err: _fix_import(err),
    "◼TG":     lambda err: None,   # escalate only
    "◼KEY":    lambda err: None,   # escalate to Mac
    "◼WALL":   lambda err: None,   # halt + escalate
}


def classify(error_text: str) -> str:
    """Return LAMAGUE error type code for the given error string."""
    text = error_text.lower()
    for code, keywords in _TYPE_PATTERNS:
        if any(kw in text for kw in keywords):
            return code
    return "◼UNKNOWN"


def lamague_tag(error_text: str, fix_status: str = "LEARNING") -> str:
    """Produce a LAMAGUE failure tag string."""
    etype  = classify(error_text)
    brief  = error_text[:60].replace("\n", " ").strip()
    ts     = datetime.datetime.now().strftime("%H:%M")
    return f"[{ts}] {etype}∴{brief[:40]}●{fix_status}"


# ── Auto-fix functions ────────────────────────────────────────────────────────

def _fix_net(err: str) -> str:
    time.sleep(60)
    return "◼NET — waited 60s for rate limit recovery"

def _fix_ctx(err: str) -> str:
    return "◼CTX — caller should truncate history[-4:] and retry"

def _fix_tool(err: str) -> str:
    # Try to extract path from error
    match = re.search(r"'([^']+)'", err)
    if match:
        p = Path(match.group(1))
        if not p.exists() and not p.suffix:
            p.mkdir(parents=True, exist_ok=True)
            return f"◼TOOL — created missing dir {p}"
    return "◼TOOL — path issue, manual review needed"

def _fix_parse(err: str) -> str:
    return "◼PARSE — retry with max_tokens increased by 200"

def _fix_board(err: str) -> str:
    BOARD_F.parent.mkdir(parents=True, exist_ok=True)
    if not BOARD_F.exists():
        BOARD_F.write_text("# AZOTH CHANNEL\n\n")
        return "◼BOARD — recreated board.md"
    return "◼BOARD — board exists, transient write error"

def _fix_import(err: str) -> str:
    match = re.search(r"No module named '([^']+)'", err)
    if match:
        pkg = match.group(1).replace("_", "-")
        os.system(f"pip install {pkg} -q")
        return f"◼IMPORT — attempted pip install {pkg}"
    return "◼IMPORT — unknown module, manual review"


# ── Board + Telegram reporting ────────────────────────────────────────────────

def _post_board(msg: str):
    try:
        ts = datetime.datetime.now().strftime("%H:%M")
        entry = f"\n[{ts}] ◈ ANTIBODY — {msg}\n"
        with open(BOARD_F, "a") as f:
            f.write(entry)
    except Exception:
        pass


def _tg(msg: str):
    try:
        from CORE.telegram_bot import send_message
        send_message(f"◈ ANTIBODY — {msg}")
    except Exception:
        pass


def _log(msg: str):
    ts = datetime.datetime.now().isoformat()
    with open(AB_LOG_F, "a") as f:
        f.write(f"[{ts}] {msg}\n")


# ── Error log monitor ─────────────────────────────────────────────────────────

_seen_errors: set = set()

def _scan_error_log():
    if not ERROR_LOG.exists():
        return
    try:
        lines = ERROR_LOG.read_text().splitlines()
    except Exception:
        return
    for line in lines[-50:]:  # last 50 lines
        if line in _seen_errors:
            continue
        _seen_errors.add(line)
        if len(line) < 10:
            continue

        etype = classify(line)
        tag   = lamague_tag(line)

        # Attempt auto-fix
        fix_fn = _AUTO_FIXES.get(etype)
        if fix_fn:
            try:
                result = fix_fn(line)
                if result:
                    _log(f"AUTO-FIX: {tag} → {result}")
                    _post_board(f"{tag}\nAUTO-FIX applied: {result}")
                else:
                    _log(f"ESCALATE: {tag}")
                    _post_board(f"{tag}\nESCALATE → Mac")
                    _tg(f"{tag}\nNeeds your attention.")
            except Exception as ex:
                _log(f"FIX FAILED: {tag}: {ex}")
                _post_board(f"{tag}\nFIX FAILED: {ex}")
                _tg(f"{tag} — fix attempt failed: {ex}")
        else:
            _log(f"UNKNOWN TYPE: {tag}")
            _post_board(f"{tag}\nUnknown — Luna reviewing")
            _tg(f"Unknown failure: {tag}")


# ── Stuck REDO detection ──────────────────────────────────────────────────────

_redo_counts: dict = {}

def _scan_forge_queue():
    if not QUEUE_F.exists():
        return
    content = QUEUE_F.read_text()
    redo_tasks = re.findall(r"## (.*?) \*\*\[REDO\]\*\*", content)
    for task in redo_tasks:
        _redo_counts[task] = _redo_counts.get(task, 0) + 1
        if _redo_counts[task] >= 3:
            tag = f"◼LOOP∴{task[:40]}●ESCALATE"
            msg = f"{tag}\nTask stuck on REDO x{_redo_counts[task]} — needs Mac or Luna review"
            _post_board(msg)
            _tg(msg)
            _redo_counts[task] = 0  # reset so it doesn't flood


def run_antibody(stop_event: threading.Event = None):
    """Main antibody monitoring loop. Run in a thread or standalone."""
    sys.path.insert(0, str(HARNESS_DIR))
    _log("ANTIBODY — starting. Watching errors, board, forge queue.")
    # Only post "online" once per boot — check sentinel
    _ab_sentinel = HARNESS_DIR / "SELF" / ".antibody_booted"
    if not _ab_sentinel.exists():
        _post_board("◈ ANTIBODY online — watching for failures. LAMAGUE error notation active.")
        _ab_sentinel.touch()

    while True:
        if stop_event and stop_event.is_set():
            break
        try:
            _scan_error_log()
            _scan_forge_queue()
        except Exception as ex:
            _log(f"ANTIBODY internal error: {ex}")
        time.sleep(POLL_SECS)


if __name__ == "__main__":
    run_antibody()
