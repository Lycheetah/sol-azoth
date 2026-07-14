"""H2 LINEAGE COMPRESSION — regression tests. Model calls stubbed."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import agent as A
import clones


class FakeAgent:
    """Just enough surface for the compaction methods, bound from the real class."""
    _history_tokens = A.AzothAgent._history_tokens if hasattr(A, "AzothAgent") else None


def _agent_cls():
    # find the class that owns compact_history without assuming its name
    for name in dir(A):
        obj = getattr(A, name)
        if isinstance(obj, type) and hasattr(obj, "compact_history"):
            return obj
    raise AssertionError("no class with compact_history found")


@pytest.fixture
def ag(monkeypatch):
    cls = _agent_cls()
    inst = object.__new__(cls)  # no __init__ — we only exercise compaction
    inst.history = []
    monkeypatch.setattr(A, "_ledger_context", lambda: "", raising=False)
    return inst


def _fill(inst, n=20, bulk_at=(3, 5)):
    inst.history = [{"role": "user", "content": "ORIGINAL GOAL: build the temple"}]
    for i in range(n):
        c = ("X" * 5000) if i in bulk_at else f"turn {i}"
        inst.history.append({"role": "assistant" if i % 2 else "user", "content": c})


def test_prune_bulk_cuts_only_oversized(ag):
    msgs = [{"role": "assistant", "content": "short"},
            {"role": "assistant", "content": "Y" * 3000}]
    out = _agent_cls()._prune_bulk(msgs)
    assert out[0]["content"] == "short"
    assert "pruned" in out[1]["content"] and len(out[1]["content"]) < 500
    assert "Y" * 3000 == msgs[1]["content"]  # original list untouched


def test_history_tokens_estimates(ag):
    ag.history = [{"role": "user", "content": "a" * 400}]
    assert ag._history_tokens() == 100


def test_compact_protects_root_and_uses_paid_seat(ag, monkeypatch):
    _fill(ag)
    called = {}

    def fake_run(seat, task, context="", mandate="readonly", max_hops=8, max_tokens=1200):
        called.update(seat=seat, mandate=mandate)
        assert "pruned" in task or "turn" in task  # bulk was pruned before the model saw it
        return clones.CloneResult(seat, "m", True, "SUMMARY LINES", 1, 0.1)

    monkeypatch.setattr(clones, "run_clone", fake_run)
    out = ag.compact_history(keep_recent=4)
    assert "Compacted" in out
    assert called["mandate"] == "none" and called["seat"] == "flash"
    heads = [m["content"] for m in ag.history if m["role"] == "system"]
    assert any("SUMMARY LINES" in c for c in heads)
    assert any("ORIGINAL GOAL: build the temple" in c for c in heads)  # root survived
    assert len(ag.history) == 2 + 4  # summary + root + recent


def test_compact_falls_back_to_main_model(ag, monkeypatch):
    _fill(ag)
    monkeypatch.setattr(clones, "run_clone",
                        lambda *a, **k: clones.CloneResult("large", "m", False, "", 0, 0.1, "dead"))
    ag.call_model = lambda msgs, stream=False: ("MAIN MODEL SUMMARY", [])
    out = ag.compact_history(keep_recent=4)
    assert "Compacted" in out
    assert any("MAIN MODEL SUMMARY" in m["content"] for m in ag.history if m["role"] == "system")


def test_nothing_to_compact(ag):
    ag.history = [{"role": "user", "content": "hi"}]
    assert "Nothing" in ag.compact_history()
