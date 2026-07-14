"""Test isolation wall — no test may write AZOTH's real persistence.

Live-caught 2026-07-11: cron/heartbeat/swarm tests wrote rows into the REAL
workspace/taskbrain.db because they patched their own module's paths but not the
brain's. This autouse fixture points taskbrain and pulse at a per-test tmp dir
for every test in the suite, so escape is structurally impossible.

Same day, same disease, caught before it shipped: clones.run_clone() gained a
swarm_budget.charge() call (paid-DeepSeek migration) that writes to the REAL
workspace/swarm_budget.json. Any test that exercises run_clone without fully
mocking it (test_swarm.py's seat/mandate tests, for one) would otherwise pollute
production spend. Isolated below in the same fixture, before it ever ran once.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def _isolate_persistence(tmp_path, monkeypatch):
    from CORE import taskbrain as TB
    from CORE import pulse as P
    from CORE import swarm_budget as SB
    monkeypatch.setattr(TB, "WORKSPACE", tmp_path)
    monkeypatch.setattr(TB, "DB_FILE", tmp_path / "taskbrain.db")
    monkeypatch.setattr(TB, "LEGACY_TREE", tmp_path / "task_tree.json")
    monkeypatch.setattr(P, "WORKSPACE", tmp_path)
    monkeypatch.setattr(P, "LOG_FILE", tmp_path / "pulse_log.md")
    monkeypatch.setattr(P, "HELD_FILE", tmp_path / "pulse_held.md")
    monkeypatch.setattr(P, "STATE_FILE", tmp_path / "pulse_state.json")
    monkeypatch.setattr(SB, "BUDGET_F", tmp_path / "swarm_budget.json")
