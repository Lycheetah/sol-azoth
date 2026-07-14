"""S1 THE SWARM — regression tests. No API: clone engine is stubbed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import agent as A
import clones


def _names():
    return {t["function"]["name"] for t in A.TOOL_DEFINITIONS}


def test_spawn_clone_registered():
    assert "spawn_clone" in _names()


def test_dispatch_requires_task():
    assert "ERROR" in A.dispatch_tool("spawn_clone", {})


def test_dispatch_rejects_bad_mode():
    out = A.dispatch_tool("spawn_clone", {"task": "x", "mode": "swarm-of-doom"})
    assert "ERROR" in out and "mode" in out


def test_dispatch_rejects_bad_mandate():
    out = A.dispatch_tool("spawn_clone", {"task": "x", "mandate": "root"})
    assert "ERROR" in out and "mandate" in out


def test_dispatch_rejects_unknown_seat():
    out = A.dispatch_tool("spawn_clone", {"task": "x", "seats": "nonexistent_seat"})
    assert "ERROR" in out and "unknown seat" in out


def test_clones_cannot_spawn_clones():
    # structural depth cap: the swarm tool must never be inside a clone's mandate
    assert "spawn_clone" not in clones.READONLY_TOOLS
    assert "spawn_clone" not in clones.BUILD_TOOLS
    assert "delegate_read" not in clones.BUILD_TOOLS


def test_solo_routes_to_run_clone(monkeypatch):
    calls = {}

    def fake_run(seat, task, context="", mandate="readonly", max_hops=8, max_tokens=1200):
        calls.update(seat=seat, task=task, mandate=mandate)
        return clones.CloneResult(seat, "stub-model", True, "STUB ANSWER", 2, 0.1)

    monkeypatch.setattr(clones, "run_clone", fake_run)
    out = A.tool_spawn_clone("check x", mode="solo", seats="flash")
    assert "STUB ANSWER" in out and calls["seat"] == "flash"


def test_race_reports_winner(monkeypatch):
    def fake_spawn(task, seats=None, mode="race", context="", mandate="readonly", max_hops=8):
        return {"mode": "race", "winner": "THE ANSWER", "seat": "nano",
                "results": [{"seat": "nano", "ok": True}, {"seat": "large", "ok": False}]}

    monkeypatch.setattr(clones, "spawn_clones", fake_spawn)
    out = A.tool_spawn_clone("q", mode="race")
    assert "THE ANSWER" in out and "race winner: nano" in out


def test_convene_surfaces_judgment(monkeypatch):
    def fake_spawn(task, seats=None, mode="convene", context="", mandate="readonly", max_hops=8):
        return {"mode": "convene", "answers": {"large": "A1", "super": "A2"},
                "judgment": "VERDICT: act on A1",
                "results": [{"seat": "large", "ok": True}, {"seat": "super", "ok": True}]}

    monkeypatch.setattr(clones, "spawn_clones", fake_spawn)
    out = A.tool_spawn_clone("q", mode="convene")
    assert "JUDGMENT" in out and "VERDICT: act on A1" in out


def test_spawn_worker_folded_into_clones(monkeypatch):
    seen = {}

    def fake_run(seat, task, context="", mandate="readonly", max_hops=8, max_tokens=1200):
        seen.update(seat=seat, mandate=mandate, context=context)
        return clones.CloneResult(seat, "stub-model", True, "WORKER VIA CLONE", 1, 0.1)

    monkeypatch.setattr(clones, "run_clone", fake_run)
    out = A.spawn_worker("A", "analyze this")
    assert "WORKER VIA CLONE" in out
    assert seen["seat"] == A.WORKER_SEATS["A"]
    assert seen["mandate"] == "readonly"
    # the worker's persona instructions ride in as context
    assert "code analysis" in seen["context"].lower()


def test_spawn_worker_failure_is_honest(monkeypatch):
    def fake_run(seat, task, context="", mandate="readonly", max_hops=8, max_tokens=1200):
        return clones.CloneResult(seat, "stub-model", False, "", 8, 9.9, "hop ceiling reached")

    monkeypatch.setattr(clones, "run_clone", fake_run)
    out = A.spawn_worker("B", "hard question")
    assert "ERROR" in out and "hop ceiling" in out


def test_build_mandate_gets_room_to_write(monkeypatch):
    # 2026-07-11: build clones write whole files through output — floor 4096
    seen = {}

    class FakeMsg:
        content = "ANSWER: ok"
        tool_calls = None

    class FakeChoice:
        message = FakeMsg()

    class FakeResp:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kw):
            seen.update(kw)
            return FakeResp()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(clones, "_client", lambda: FakeClient())
    clones.run_clone("flash", "write a file", mandate="build")
    assert seen["max_tokens"] == 4096
    clones.run_clone("flash", "read a thing", mandate="readonly")
    assert seen["max_tokens"] == 1200
