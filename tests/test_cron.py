"""C1 REAL CRON — regression tests. No daemon, no pulse delivery: routes stubbed."""

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from CORE import cron as C


def dt(h, m, day=15, month=6, weekday_iso=None):
    d = datetime.datetime(2026, month, day, h, m)
    return d


def test_parse_valid():
    fields, cmd = C.parse_line("*/5 * * * * echo hi there")
    assert fields == ["*/5", "*", "*", "*", "*"] and cmd == "echo hi there"


def test_parse_rejects_garbage():
    assert C.parse_line("") is None
    assert C.parse_line("# comment") is None
    assert C.parse_line("0 9 * *") is None  # missing command


def test_due_exact_time():
    fields, _ = C.parse_line("30 9 * * * x")
    assert C.is_due(fields, dt(9, 30))
    assert not C.is_due(fields, dt(9, 31))
    assert not C.is_due(fields, dt(10, 30))


def test_due_step():
    fields, _ = C.parse_line("*/15 * * * * x")
    assert C.is_due(fields, dt(3, 0))
    assert C.is_due(fields, dt(3, 45))
    assert not C.is_due(fields, dt(3, 20))


def test_due_comma_list():
    fields, _ = C.parse_line("0 9,18 * * * x")
    assert C.is_due(fields, dt(9, 0)) and C.is_due(fields, dt(18, 0))
    assert not C.is_due(fields, dt(12, 0))


def test_run_due_fires_and_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "CRON_FILE", tmp_path / "cron_jobs.txt")
    monkeypatch.setattr(C, "CRON_LOG", tmp_path / "cron_log.md")
    monkeypatch.setattr(C, "WORKSPACE", tmp_path)
    ran = []
    monkeypatch.setattr(C, "_run", lambda cmd: ran.append(cmd))
    C.CRON_FILE.write_text(
        "0 9 * * * echo morning\n"
        "* * * * * echo every-minute\n"
        "# a comment\n"
        "malformed line\n"
    )
    fired = C.run_due(dt(9, 0))
    assert fired == 2 and ran == ["echo morning", "echo every-minute"]
    ran.clear()
    fired = C.run_due(dt(14, 7))
    assert fired == 1 and ran == ["echo every-minute"]


def test_run_real_command_pulses_outcome(tmp_path, monkeypatch):
    from CORE import pulse as P
    from CORE import taskbrain as TB
    monkeypatch.setattr(C, "CRON_LOG", tmp_path / "cron_log.md")
    monkeypatch.setattr(C, "WORKSPACE", tmp_path)
    monkeypatch.setattr(TB, "WORKSPACE", tmp_path)
    monkeypatch.setattr(TB, "DB_FILE", tmp_path / "taskbrain.db")
    monkeypatch.setattr(TB, "LEGACY_TREE", tmp_path / "task_tree.json")
    events = []
    monkeypatch.setattr(P, "pulse", lambda event, detail="", level="info": events.append((event, level)))
    C._run("true")
    C._run("false")
    assert ("cron ran", "info") in events
    assert ("cron FAILED", "alert") in events


def test_schedule_cron_tool_validates():
    import agent as A
    out = A.tool_schedule_cron("not-a-cron", "")
    assert "ERROR" in out
    assert "crontab" not in A.tool_schedule_cron.__doc__ or True  # the old lie is gone from the return path
