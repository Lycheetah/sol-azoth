"""P1-T2: Structured scratchpad tests."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_scratchpad_importable():
    from CORE.scratchpad import Scratchpad
    return True, "Scratchpad class importable"

def test_scratchpad_session():
    from CORE.scratchpad import Scratchpad
    with tempfile.TemporaryDirectory() as d:
        sp = Scratchpad(state_path=os.path.join(d, "scratch.json"))
        sid = sp.start_session(session_id="test_session")
        assert sp.get_session_id() is not None, "session_id should not be None"
    return True, "start_session + get_session_id"

def test_scratchpad_task():
    from CORE.scratchpad import Scratchpad
    with tempfile.TemporaryDirectory() as d:
        sp = Scratchpad(state_path=os.path.join(d, "scratch.json"))
        sp.start_session()
        sp.set_task("P2-T1 test run", phase="P2")
        task = sp.get_task()
        assert task.get("name") == "P2-T1 test run", f"Got task: {task}"
    return True, "set_task + get_task roundtrip"

def test_scratchpad_plan():
    from CORE.scratchpad import Scratchpad
    with tempfile.TemporaryDirectory() as d:
        sp = Scratchpad(state_path=os.path.join(d, "scratch.json"))
        sp.start_session()
        sp.set_plan(["step 1", "step 2", "step 3"])
        plan = sp.get_plan()
        assert plan == ["step 1", "step 2", "step 3"], f"Got plan: {plan}"
    return True, "set_plan + get_plan roundtrip"

def test_scratchpad_next_step():
    from CORE.scratchpad import Scratchpad
    with tempfile.TemporaryDirectory() as d:
        sp = Scratchpad(state_path=os.path.join(d, "scratch.json"))
        sp.start_session()
        # steps are dicts with 'step', 'action', 'expected'
        sp.set_plan([
            {"step": 1, "action": "alpha", "expected": "done", "status": "pending"},
            {"step": 2, "action": "beta", "expected": "done", "status": "pending"},
        ])
        step = sp.next_step()
        assert step is not None, "next_step returned None"
        assert step.get("action") == "alpha", f"Expected first step 'alpha', got: {step}"
    return True, f"next_step returns first pending step: action={step.get('action')!r}"

def test_scratchpad_persists():
    from CORE.scratchpad import Scratchpad
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "scratch.json")
        sp1 = Scratchpad(state_path=path)
        sp1.start_session()
        sp1.set_task("persist_task", phase="P2")
        sp2 = Scratchpad(state_path=path)
        task = sp2.get_task()
        assert task.get("name") == "persist_task", f"Persisted task not found: {task}"
    return True, "task survives across Scratchpad instances (file-backed)"

def test_scratchpad_blocker():
    from CORE.scratchpad import Scratchpad
    with tempfile.TemporaryDirectory() as d:
        sp = Scratchpad(state_path=os.path.join(d, "scratch.json"))
        sp.start_session()
        sp.add_blocker("test blocker description", severity="high")
        blockers = sp.get_blockers()
        assert any("test blocker" in b.get("description", "") for b in blockers), \
            f"Blocker not found: {blockers}"
    return True, "add_blocker + get_blockers"
