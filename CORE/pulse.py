"""
N1: THE PULSE — AZOTH's one notification spine.
Every event that reaches Mac's phone, desktop, or the activity ledger flows through
pulse(). One implementation, every surface (Single Truth Rule).

Levels:
  info  — logged always; sent to phone only when unattended (forge loop running)
  act   — needs Mac's tap; sent always (held to digest during quiet hours)
  alert — defect / failure / stuck; breaks through quiet hours

Quiet hours (AZOTH_QUIET, default "23-08"): info/act are held to workspace/
pulse_held.md and flushed as one digest on the first pulse after the window ends.
alert always sends. The Companion Clause holds: events, never reproach — no pulse
may guilt, nag, or manufacture urgency about Mac's absence.

Dedupe: identical (event, detail) within 30 minutes is suppressed (logged as dup).
State survives across processes via workspace/pulse_state.json so the heartbeat
daemon and the REPL share one dedupe window.
"""

import datetime
import json
import os
import subprocess
import threading
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
WORKSPACE   = HARNESS_DIR / "workspace"
LOG_FILE    = WORKSPACE / "pulse_log.md"
HELD_FILE   = WORKSPACE / "pulse_held.md"
STATE_FILE  = WORKSPACE / "pulse_state.json"

DEDUPE_WINDOW_S = 30 * 60
BRAND = "☿ AZOTH"

_lock = threading.Lock()
_unattended = False


def set_unattended(value: bool) -> None:
    """The forge loop (or heartbeat daemon) flips this so info-level events reach the phone."""
    global _unattended
    _unattended = value


def is_unattended() -> bool:
    return _unattended or os.environ.get("AZOTH_UNATTENDED", "") == "1"


# ── quiet hours ──────────────────────────────────────────────────────────────

def _quiet_window() -> tuple[int, int]:
    raw = os.environ.get("AZOTH_QUIET", "23-08")
    try:
        start, end = raw.split("-")
        return int(start) % 24, int(end) % 24
    except Exception:
        return 23, 8


def in_quiet_hours(now: datetime.datetime = None) -> bool:
    start, end = _quiet_window()
    if start == end:
        return False
    h = (now or datetime.datetime.now()).hour
    if start < end:
        return start <= h < end
    return h >= start or h < end  # window crosses midnight


# ── state (cross-process dedupe) ─────────────────────────────────────────────

def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"sent": {}}


def _save_state(state: dict) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    # keep only entries inside the dedupe window so the file never grows
    cutoff = datetime.datetime.now().timestamp() - DEDUPE_WINDOW_S
    state["sent"] = {k: v for k, v in state.get("sent", {}).items() if v > cutoff}
    STATE_FILE.write_text(json.dumps(state))


def _is_dup(key: str, state: dict) -> bool:
    ts = state.get("sent", {}).get(key)
    return ts is not None and (datetime.datetime.now().timestamp() - ts) < DEDUPE_WINDOW_S


# ── delivery routes ──────────────────────────────────────────────────────────

def _send_telegram(text: str) -> bool:
    try:
        from CORE.telegram_bot import send_message
        return send_message(text)
    except Exception:
        return False


def _send_desktop(title: str, body: str) -> None:
    safe = body[:150].replace('"', "'")
    try:
        if os.environ.get("TERMUX_VERSION") or Path("/data/data/com.termux").exists():
            cmd = f'termux-notification --title "{title}" --content "{safe}" 2>/dev/null || true'
        else:
            cmd = f'notify-send "{title}" "{safe}" --urgency=normal --expire-time=8000 2>/dev/null || true'
        subprocess.run(cmd, shell=True, timeout=10, capture_output=True)
    except Exception:
        pass


def _log(line: str) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def _hold(text: str) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    with open(HELD_FILE, "a") as f:
        f.write(text + "\n---\n")


def _flush_held() -> None:
    """First pulse after quiet hours: deliver everything held as ONE digest."""
    if not HELD_FILE.exists():
        return
    held = HELD_FILE.read_text().strip()
    if not held:
        HELD_FILE.unlink()
        return
    items = [x.strip() for x in held.split("---") if x.strip()]
    digest = f"{BRAND} — while you slept ({len(items)}):\n" + "\n".join(f"• {i}" for i in items)
    if _send_telegram(digest[:3800]):
        HELD_FILE.unlink()
        _log(f"[{_ts()}] digest · flushed {len(items)} held pulses")


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


# ── the spine ────────────────────────────────────────────────────────────────

_ICONS = {"info": "·", "act": "✋", "alert": "⚠"}


def pulse(event: str, detail: str = "", level: str = "info") -> str:
    """Emit one activity event. Returns a short status string for tool callers."""
    if level not in _ICONS:
        level = "info"
    icon = _ICONS[level]
    text = f"{BRAND} {icon} {event}" + (f"\n{detail}" if detail else "")

    with _lock:
        _log(f"[{_ts()}] {level} · {event}" + (f" — {detail[:200]}" if detail else ""))

        # dedupe
        state = _load_state()
        key = f"{event}|{detail[:80]}"
        if _is_dup(key, state):
            return f"pulse suppressed (duplicate within 30m): {event}"

        quiet = in_quiet_hours()
        if not quiet:
            _flush_held()

        # info stays off the phone unless AZOTH runs unattended
        if level == "info" and not is_unattended():
            return f"pulse logged: {event}"

        if quiet and level != "alert":
            _hold(f"[{_ts()}] {event}" + (f" — {detail[:200]}" if detail else ""))
            state.setdefault("sent", {})[key] = datetime.datetime.now().timestamp()
            _save_state(state)
            return f"pulse held for morning digest (quiet hours): {event}"

        sent = _send_telegram(text[:3800])
        _send_desktop(BRAND, f"{event}" + (f" — {detail[:120]}" if detail else ""))
        state.setdefault("sent", {})[key] = datetime.datetime.now().timestamp()
        _save_state(state)
        return f"pulse sent ({'telegram' if sent else 'desktop only'}): {event}"
