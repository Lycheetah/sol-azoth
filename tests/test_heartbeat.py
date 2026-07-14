"""N2 THE HEARTBEAT — regression tests. No API: clone engine and pulse stubbed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import clones
from CORE import heartbeat as H
from CORE import pulse as P


def _quiet_off(monkeypatch):
    monkeypatch.setattr(P, "in_quiet_hours", lambda now=None: False)


def _no_busy(monkeypatch):
    monkeypatch.setattr(H, "forge_is_live", lambda: False)


def test_ok_is_silent(monkeypatch):
    _quiet_off(monkeypatch)
    _no_busy(monkeypatch)
    sent = []
    monkeypatch.setattr(P, "pulse", lambda *a, **k: sent.append(a))
    monkeypatch.setattr(clones, "run_clone",
                        lambda *a, **k: clones.CloneResult("large", "m", True, "HEARTBEAT_OK", 1, 0.1))
    out = H.beat()
    assert out.startswith("ok") and not sent


def test_ok_with_short_trailing_note_still_silent(monkeypatch):
    _quiet_off(monkeypatch)
    _no_busy(monkeypatch)
    sent = []
    monkeypatch.setattr(P, "pulse", lambda *a, **k: sent.append(a))
    monkeypatch.setattr(clones, "run_clone",
                        lambda *a, **k: clones.CloneResult("large", "m", True,
                                                           "HEARTBEAT_OK — all four checks clean", 1, 0.1))
    assert H.beat().startswith("ok") and not sent


def test_ok_wrapped_in_clone_answer_format_still_silent(monkeypatch):
    # live-caught 2026-07-11: clones answer in a mandatory ANSWER:/BASIS: format,
    # so a clean OK arrived as "ANSWER: HEARTBEAT_OK\nBASIS: ..." and false-alerted
    _quiet_off(monkeypatch)
    _no_busy(monkeypatch)
    sent = []
    monkeypatch.setattr(P, "pulse", lambda *a, **k: sent.append(a))
    monkeypatch.setattr(clones, "run_clone",
                        lambda *a, **k: clones.CloneResult("large", "m", True,
                                                           "ANSWER: HEARTBEAT_OK\nBASIS:\n1. checks clean\nUNSURE: nothing", 3, 5.0))
    assert H.beat().startswith("ok") and not sent


def test_alert_pulses(monkeypatch):
    _quiet_off(monkeypatch)
    _no_busy(monkeypatch)
    sent = []
    monkeypatch.setattr(P, "pulse", lambda event, detail="", level="info": sent.append((event, level)))
    monkeypatch.setattr(clones, "run_clone",
                        lambda *a, **k: clones.CloneResult("large", "m", True,
                                                           "Check 2 fired: FORGE_QUEUE.md has 3 QUEUED tasks and no forge is running.", 2, 0.2))
    out = H.beat()
    assert out.startswith("alert") and sent == [("heartbeat", "act")]


def test_quiet_hours_skip(monkeypatch):
    monkeypatch.setattr(P, "in_quiet_hours", lambda now=None: True)
    called = []
    monkeypatch.setattr(clones, "run_clone", lambda *a, **k: called.append(1))
    assert "quiet" in H.beat() and not called


def test_busy_defers(monkeypatch):
    _quiet_off(monkeypatch)
    monkeypatch.setattr(H, "forge_is_live", lambda: True)
    called = []
    monkeypatch.setattr(clones, "run_clone", lambda *a, **k: called.append(1))
    assert "deferred" in H.beat() and not called


def test_failed_seat_never_raises(monkeypatch):
    _quiet_off(monkeypatch)
    _no_busy(monkeypatch)
    monkeypatch.setattr(clones, "run_clone",
                        lambda *a, **k: clones.CloneResult("large", "m", False, "", 0, 0.1, "endpoint dead"))
    out = H.beat()
    assert "failed" in out and "endpoint dead" in out
