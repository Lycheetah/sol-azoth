"""S2 TASK BRAIN — regression tests. Isolated DB per test, no API."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from CORE import taskbrain as TB


@pytest.fixture
def brain(tmp_path, monkeypatch):
    monkeypatch.setattr(TB, "WORKSPACE", tmp_path)
    monkeypatch.setattr(TB, "DB_FILE", tmp_path / "taskbrain.db")
    monkeypatch.setattr(TB, "LEGACY_TREE", tmp_path / "task_tree.json")
    return TB


def test_record_and_rows(brain):
    tid = brain.record("task", "build the thing")
    assert tid >= 1
    items = brain.rows(kind="task")
    assert len(items) == 1 and items[0]["subject"] == "build the thing"
    assert items[0]["status"] == "pending"


def test_update(brain):
    tid = brain.record("task", "x")
    assert brain.update(tid, status="done", detail="finished")
    r = brain.rows(kind="task")[0]
    assert r["status"] == "done" and r["detail"] == "finished"
    assert not brain.update(99999, status="done")


def test_kind_isolation(brain):
    brain.record("task", "a task")
    brain.record("cron", "echo hi", status="done")
    brain.record("heartbeat", "beat", status="ok")
    brain.record("swarm", "race: q", status="done")
    assert len(brain.rows(kind="task")) == 1
    assert len(brain.rows(kind="cron")) == 1
    assert len(brain.rows()) == 4


def test_summary_names_every_kind(brain):
    brain.record("task", "open one")
    brain.record("forge", "goal", status="done")
    brain.record("swarm", "solo/nano: q", status="done")
    s = brain.summary()
    assert "1 open task" in s and "forge" in s and "swarm" in s


def test_legacy_migration_once(brain, tmp_path):
    legacy = tmp_path / "task_tree.json"
    legacy.write_text(json.dumps({
        "root_ids": ["t001"],
        "nodes": {
            "t001": {"id": "t001", "goal": "parent goal", "status": "pending",
                     "parent": None, "children": ["t002"], "result": None,
                     "created": "2026-07-01T10:00:00"},
            "t002": {"id": "t002", "goal": "child goal", "status": "done",
                     "parent": "t001", "children": [], "result": "shipped",
                     "created": "2026-07-02T10:00:00"},
        }}))
    items = brain.rows(kind="task", limit=10)
    assert len(items) == 2
    by_subject = {r["subject"]: r for r in items}
    assert by_subject["child goal"]["status"] == "done"
    assert by_subject["child goal"]["parent"] == by_subject["parent goal"]["id"]
    assert not legacy.exists()
    assert (tmp_path / "task_tree.json.superseded").exists()
    # opening again must not double-migrate
    assert len(brain.rows(kind="task", limit=10)) == 2


def test_agent_tools_run_on_brain(brain):
    import agent as A
    out = A.tool_task_create("brain-backed task")
    assert "Task created: #" in out
    tid = out.split("#")[1].split(" ")[0]
    assert "brain-backed task" in A.tool_task_list()
    assert f"#{tid} → [done]" in A.tool_task_update(tid, "done")
    assert "ERROR" in A.tool_task_update("not-a-number", "done")
    assert "Todo added" in A.tool_todo_write("a todo", "pending")
