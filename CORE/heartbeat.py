"""
N2: THE HEARTBEAT — AZOTH wakes on its own clock.

On each beat: read HEARTBEAT.md (the checklist — that file IS the behavior),
gather light context (BOARD.md, TASKS.md), run ONE bounded readonly clone turn
on a paid seat, and either log HEARTBEAT_OK silently or pulse Mac with what
needs attention. The heartbeat detects and reports; it never builds, never
forges, never commits — Mac fires (Covenant).

Cost: one paid DeepSeek call per beat, metered by CORE/swarm_budget.py's
monthly ceiling (2026-07-11: the free NVIDIA tier was too slow/unreliable for
the harness — Mac's call — so nothing here runs on it anymore).
Quiet hours: no beats inside AZOTH_QUIET (pulse.in_quiet_hours) — the morning
digest already covers the gap. Busy: beats defer while a forge loop is live
(workspace/forge_live.flag).

Run:
  python3 -m CORE.heartbeat --once      # single beat, prints the outcome
  python3 -m CORE.heartbeat --daemon    # loop forever (Mac fires this, never Sol)
Interval: AZOTH_HEARTBEAT_MIN (default 30).
"""

import argparse
import datetime
import time
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
WORKSPACE   = HARNESS_DIR / "workspace"
BUSY_FLAG   = WORKSPACE / "forge_live.flag"
BEAT_LOG    = WORKSPACE / "heartbeat_log.md"

OK_TOKEN = "HEARTBEAT_OK"
OK_SLACK = 300  # chars allowed after OK before we treat the reply as an alert
SEAT = "flash"  # paid DeepSeek — free tier retired 2026-07-11 (too slow/unreliable)


def _read(path: Path, cap: int = 4000) -> str:
    try:
        return path.read_text()[:cap]
    except Exception:
        return ""


def _log(line: str) -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(BEAT_LOG, "a") as f:
        f.write(f"[{ts}] {line}\n")


def forge_is_live() -> bool:
    return BUSY_FLAG.exists()


def beat() -> str:
    """One heartbeat turn. Returns a one-line outcome for the caller/log."""
    import sys
    sys.path.insert(0, str(HARNESS_DIR))
    from CORE.pulse import pulse, in_quiet_hours

    if in_quiet_hours():
        _log("skipped — quiet hours")
        return "skipped: quiet hours"
    if forge_is_live():
        _log("deferred — forge loop live")
        return "deferred: forge is live"

    checklist = _read(HARNESS_DIR / "HEARTBEAT.md", 6000)
    if not checklist.strip():
        _log("skipped — no HEARTBEAT.md")
        return "skipped: no HEARTBEAT.md"

    context = (
        f"[BOARD.md]\n{_read(HARNESS_DIR / 'BOARD.md')}\n\n"
        f"[TASKS.md]\n{_read(HARNESS_DIR / 'TASKS.md')}\n\n"
        f"Repo root for any git/file checks: {HARNESS_DIR}"
    )
    task = (
        "Follow this heartbeat checklist strictly. Do not infer old tasks from the "
        "context beyond what the checklist asks you to check.\n\n" + checklist
    )

    import clones
    r = clones.run_clone(SEAT, task, context=context, mandate="readonly", max_hops=6)

    if not r.ok:
        _log(f"beat FAILED on seat {r.seat}: {r.error}")
        return f"beat failed: {r.error}"

    from CORE.taskbrain import record
    answer = r.answer.strip()
    # Clones answer in a mandatory ANSWER:/BASIS: format, so the OK token may be
    # wrapped (live-caught on the first real beat). OK = the token appears in the
    # first line; an alert names a fired check there instead.
    first_line = answer.splitlines()[0].upper() if answer else ""
    if OK_TOKEN in first_line:
        _log(f"OK ({r.seconds}s, {r.hops} hops)")
        record("heartbeat", "beat", status="ok", detail=f"{r.seconds}s, {r.hops} hops")
        return "ok: nothing needs attention"

    _log(f"ALERT: {answer[:200]}")
    record("heartbeat", "beat", status="alert", detail=answer[:600])
    pulse("heartbeat", answer[:600], level="act")
    return f"alert pulsed: {answer[:120]}"


def daemon() -> None:
    import os
    interval = int(os.environ.get("AZOTH_HEARTBEAT_MIN", "30")) * 60
    _log(f"daemon started — every {interval // 60}m")
    # C1: the daemon also hosts the cron clock (workspace/cron_jobs.txt, real now)
    from CORE.cron import start_thread
    start_thread()
    while True:
        try:
            print(beat(), flush=True)
        except Exception as e:  # a bad beat must never kill the heart
            _log(f"beat crashed: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--daemon", action="store_true")
    a = ap.parse_args()
    if a.daemon:
        daemon()
    else:
        print(beat())
