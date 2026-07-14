"""P3-T1: Background scheduler tests."""
import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_scheduler_importable():
    from CORE.scheduler import Scheduler, get_scheduler, reset_scheduler
    return True, "Scheduler + get/reset importable"

def test_register_and_list():
    from CORE.scheduler import Scheduler
    s = Scheduler()
    s.register("task_a", lambda: None, interval_s=60)
    s.register("task_b", lambda: None, interval_s=30)
    assert "task_a" in s.task_names()
    assert "task_b" in s.task_names()
    return True, f"registered 2 tasks: {s.task_names()}"

def test_task_runs():
    from CORE.scheduler import Scheduler
    ran = threading.Event()
    s = Scheduler()
    s.register("quick", lambda: ran.set(), interval_s=0.1, run_immediately=True)
    s.start()
    try:
        fired = ran.wait(timeout=2.0)
        assert fired, "task did not run within 2s"
        st = s.status()
        task = next(t for t in st["tasks"] if t["name"] == "quick")
        assert task["run_count"] >= 1, f"run_count={task['run_count']}"
        assert task["last_status"] == "ok"
    finally:
        s.stop()
    return True, f"task ran, status=ok, run_count={task['run_count']}"

def test_failure_captured():
    from CORE.scheduler import Scheduler
    pinged = []
    s = Scheduler(ping_fn=lambda msg: pinged.append(msg))
    s.register("bad_task", lambda: (_ for _ in ()).throw(ValueError("boom")),
               interval_s=0.1, run_immediately=True)
    s.start()
    try:
        time.sleep(0.5)
        st = s.status()
        task = next(t for t in st["tasks"] if t["name"] == "bad_task")
        assert task["last_status"] == "fail", f"Expected fail, got: {task['last_status']}"
        assert task["fail_count"] >= 1
        assert len(pinged) >= 1, "ping_fn was not called on failure"
        assert "bad_task" in pinged[0]
    finally:
        s.stop()
    return True, f"failure captured, ping sent: {pinged[0][:60]!r}"

def test_enable_disable():
    from CORE.scheduler import Scheduler
    count = [0]
    s = Scheduler()
    s.register("toggle", lambda: count.__setitem__(0, count[0]+1), interval_s=0.05)
    s.disable("toggle")
    s.start()
    try:
        time.sleep(0.3)
        assert count[0] == 0, f"disabled task ran {count[0]} times"
        s.enable("toggle")
        time.sleep(0.3)
        assert count[0] >= 1, "enabled task didn't run"
    finally:
        s.stop()
    return True, f"disable blocked runs, enable allowed them (count={count[0]})"

def test_unregister():
    from CORE.scheduler import Scheduler
    s = Scheduler()
    s.register("remove_me", lambda: None, interval_s=60)
    assert "remove_me" in s.task_names()
    removed = s.unregister("remove_me")
    assert removed, "unregister returned False"
    assert "remove_me" not in s.task_names()
    return True, "unregister removes task"

def test_log_populated():
    from CORE.scheduler import Scheduler
    s = Scheduler()
    s.register("logged", lambda: None, interval_s=0.05, run_immediately=True)
    s.start()
    try:
        time.sleep(0.4)
        log = s.recent_log(10)
        assert len(log) >= 1, f"Expected log entries, got: {log}"
        assert log[-1]["task"] == "logged"
        assert log[-1]["status"] == "ok"
    finally:
        s.stop()
    return True, f"log has {len(log)} entries, last={log[-1]['status']}"

def test_one_shot():
    from CORE.scheduler import Scheduler
    fired = [0]
    s = Scheduler()
    s.register("once", lambda: fired.__setitem__(0, fired[0]+1),
               interval_s=0, run_immediately=True)
    s.start()
    try:
        time.sleep(0.5)
        st = s.status()
        task = next((t for t in st["tasks"] if t["name"] == "once"), None)
        # one-shot tasks disable themselves
        assert task is None or not task["enabled"], "one-shot task should be disabled"
        assert fired[0] >= 1, f"one-shot task didn't fire: {fired[0]}"
    finally:
        s.stop()
    return True, f"one-shot fired {fired[0]} time(s) then disabled"

def test_status_shape():
    from CORE.scheduler import Scheduler
    s = Scheduler()
    s.register("t1", lambda: None, interval_s=30)
    st = s.status()
    assert "running" in st
    assert "task_count" in st
    assert "tasks" in st
    assert st["task_count"] == 1
    task = st["tasks"][0]
    required = {"name","enabled","interval_s","last_status","run_count","fail_count"}
    assert required.issubset(task.keys()), f"missing keys: {required - task.keys()}"
    return True, f"status() has correct shape: {sorted(st.keys())}"
