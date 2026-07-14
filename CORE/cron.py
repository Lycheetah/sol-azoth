"""
C1: REAL CRON — schedule_cron entries actually fire.

tool_schedule_cron has written workspace/cron_jobs.txt since it was born, and
nothing ever read it (the /bench class: advertised, half-real). Now the
heartbeat daemon hosts a cron thread that reads that same file — the file stays
the single source of truth, no crontab dependency — evaluates due-ness every
minute, runs the command via subprocess, and pulses the outcome (alert on
failure). Every run lands in workspace/cron_log.md.

Entry format (one per line, written by tool_schedule_cron):
  <min> <hour> <dom> <mon> <dow> <command...>
Fields support: * , exact numbers, comma lists, and */n steps.
"""

import datetime
import subprocess
import threading
import time
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
WORKSPACE   = HARNESS_DIR / "workspace"
CRON_FILE   = WORKSPACE / "cron_jobs.txt"
CRON_LOG    = WORKSPACE / "cron_log.md"

CMD_TIMEOUT_S = 600


def _field_matches(field: str, value: int) -> bool:
    for part in field.split(","):
        part = part.strip()
        if part == "*":
            return True
        if part.startswith("*/"):
            try:
                if int(part[2:]) > 0 and value % int(part[2:]) == 0:
                    return True
            except ValueError:
                continue
        else:
            try:
                if int(part) == value:
                    return True
            except ValueError:
                continue
    return False


def parse_line(line: str):
    """Return (fields[5], command) or None for blanks/comments/malformed lines."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split(None, 5)
    if len(parts) < 6:
        return None
    return parts[:5], parts[5]


def is_due(fields: list[str], now: datetime.datetime) -> bool:
    values = [now.minute, now.hour, now.day, now.month, now.isoweekday() % 7]
    return all(_field_matches(f, v) for f, v in zip(fields, values))


def _log(line: str) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(CRON_LOG, "a") as f:
        f.write(f"[{ts}] {line}\n")


def _run(command: str) -> None:
    from CORE.pulse import pulse
    from CORE.taskbrain import record, update
    entry_id = record("cron", command[:200], status="running")
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True,
                           timeout=CMD_TIMEOUT_S, cwd=str(HARNESS_DIR))
        tail = (r.stdout or r.stderr or "").strip()[-200:]
        if r.returncode == 0:
            _log(f"ok · {command} · {tail[:120]}")
            update(entry_id, status="done", detail=tail[:200])
            pulse("cron ran", f"{command[:100]} — ok", level="info")
        else:
            _log(f"FAIL({r.returncode}) · {command} · {tail}")
            update(entry_id, status="fail", detail=f"exit {r.returncode}: {tail[:180]}")
            pulse("cron FAILED", f"{command[:100]} — exit {r.returncode}: {tail[:150]}", level="alert")
    except subprocess.TimeoutExpired:
        _log(f"TIMEOUT · {command}")
        update(entry_id, status="fail", detail="timeout")
        pulse("cron TIMEOUT", command[:150], level="alert")
    except Exception as e:
        _log(f"ERROR · {command} · {e}")
        update(entry_id, status="fail", detail=str(e)[:200])
        pulse("cron ERROR", f"{command[:100]} — {e}", level="alert")


def run_due(now: datetime.datetime = None) -> int:
    """Run every entry due at `now`'s minute. Returns how many fired."""
    now = now or datetime.datetime.now()
    if not CRON_FILE.exists():
        return 0
    fired = 0
    for raw in CRON_FILE.read_text().splitlines():
        parsed = parse_line(raw)
        if parsed and is_due(parsed[0], now):
            fired += 1
            _run(parsed[1])
    return fired


def cron_loop(stop: threading.Event = None) -> None:
    """Poll once per minute, aligned to the minute. Hosted by the heartbeat daemon."""
    _log("cron loop started")
    last_minute = None
    while stop is None or not stop.is_set():
        now = datetime.datetime.now()
        key = (now.hour, now.minute)
        if key != last_minute:
            last_minute = key
            try:
                run_due(now)
            except Exception as e:  # one bad entry must never kill the clock
                _log(f"loop error: {e}")
        time.sleep(5)


def start_thread() -> threading.Thread:
    t = threading.Thread(target=cron_loop, daemon=True, name="azoth-cron")
    t.start()
    return t
