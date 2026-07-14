"""N1 THE PULSE — regression tests. No network: delivery routes are stubbed."""

import datetime
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}")


def fresh_pulse(tmp_tag):
    """Reload pulse with an isolated workspace so tests never touch the real ledger."""
    from CORE import pulse as p
    importlib.reload(p)
    ws = Path(__file__).parent / "__pycache__" / f"pulse_ws_{tmp_tag}"
    ws.mkdir(parents=True, exist_ok=True)
    for f in ws.glob("*"):
        f.unlink()
    p.WORKSPACE = ws
    p.LOG_FILE = ws / "pulse_log.md"
    p.HELD_FILE = ws / "pulse_held.md"
    p.STATE_FILE = ws / "pulse_state.json"
    p.sent_messages = []
    p._send_telegram = lambda text: p.sent_messages.append(text) or True
    p._send_desktop = lambda title, body: None
    return p


def main():
    os.environ.pop("AZOTH_UNATTENDED", None)

    # ── attended info stays off the phone ──
    p = fresh_pulse("a")
    os.environ["AZOTH_QUIET"] = "0-0"  # disable quiet hours
    r = p.pulse("forge done", "task X", level="info")
    check("attended info: logged not sent", "logged" in r and not p.sent_messages)
    check("attended info: ledger written", "forge done" in p.LOG_FILE.read_text())

    # ── act sends ──
    r = p.pulse("ping", "need your eyes", level="act")
    check("act: sent to telegram", "sent" in r and len(p.sent_messages) == 1)
    check("act: branded AZOTH", "☿ AZOTH" in p.sent_messages[0])

    # ── dedupe ──
    r = p.pulse("ping", "need your eyes", level="act")
    check("dedupe: identical within 30m suppressed", "suppressed" in r and len(p.sent_messages) == 1)
    r = p.pulse("ping", "different detail", level="act")
    check("dedupe: different detail passes", "sent" in r and len(p.sent_messages) == 2)

    # ── unattended flips info onto the phone ──
    p2 = fresh_pulse("b")
    p2.set_unattended(True)
    r = p2.pulse("forge done", "task Y", level="info")
    check("unattended info: sent", "sent" in r and len(p2.sent_messages) == 1)
    p2.set_unattended(False)

    # ── quiet hours hold act, alert breaks through ──
    p3 = fresh_pulse("c")
    h = datetime.datetime.now().hour
    os.environ["AZOTH_QUIET"] = f"{h}-{(h + 2) % 24}"  # we are inside quiet hours now
    r = p3.pulse("ping", "held item", level="act")
    check("quiet: act held", "held" in r and not p3.sent_messages)
    check("quiet: held file written", p3.HELD_FILE.exists())
    r = p3.pulse("forge STUCK", "blocker", level="alert")
    check("quiet: alert breaks through", "sent" in r and len(p3.sent_messages) == 1)

    # ── digest flush after quiet hours end ──
    os.environ["AZOTH_QUIET"] = "0-0"
    r = p3.pulse("morning", "first pulse after quiet", level="act")
    digests = [m for m in p3.sent_messages if "while you slept" in m]
    check("digest: held items flushed as one message", len(digests) == 1 and "held item" in digests[0])
    check("digest: held file cleared", not p3.HELD_FILE.exists())

    # ── quiet window math ──
    p4 = fresh_pulse("d")
    os.environ["AZOTH_QUIET"] = "23-08"
    check("window: 23-08 covers 02:00", p4.in_quiet_hours(datetime.datetime(2026, 7, 11, 2)))
    check("window: 23-08 excludes 12:00", not p4.in_quiet_hours(datetime.datetime(2026, 7, 11, 12)))
    check("window: 23-08 covers 23:00", p4.in_quiet_hours(datetime.datetime(2026, 7, 11, 23)))

    os.environ.pop("AZOTH_QUIET", None)
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
