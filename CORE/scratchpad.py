#!/usr/bin/env python3
"""
VAEL-SP Structured Scratchpad — persistent reasoning state between turns.
Phase 1, Task 2 of the Architecture Forge.

Replaces flat scratch.md with structured sections:
  - current_task: what I'm working on right now
  - plan_steps: ordered list of steps to complete the task
  - step_results: what each step produced
  - blockers: anything blocking progress
  - next_action: what to do on the next turn
  - context: relevant files, paths, data loaded this session

Auto-saves after every write. Loads on boot.
"""

import json
import datetime
import os
import pathlib

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scratchpad_state.json")

DEFAULT_STATE = {
    "session_id": None,
    "started_at": None,
    "last_updated": None,
    "current_task": {
        "name": None,
        "phase": None,
        "status": "idle",  # idle, planning, executing, verifying, blocked, done
        "started_at": None
    },
    "plan_steps": [],
    "step_results": {},
    "blockers": [],
    "next_action": None,
    "context": {
        "loaded_files": [],
        "active_paths": [],
        "session_notes": []
    },
    "reasoning_log": []
}


class Scratchpad:
    """Persistent structured reasoning state."""

    def __init__(self, state_path=None):
        self.state_path = state_path or STATE_PATH
        self.state = self._load()

    def _load(self):
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r") as f:
                    data = json.load(f)
                    # Merge with defaults to handle schema evolution
                    merged = DEFAULT_STATE.copy()
                    merged.update(data)
                    return merged
            except (json.JSONDecodeError, IOError):
                return DEFAULT_STATE.copy()
        return DEFAULT_STATE.copy()

    def _save(self):
        self.state["last_updated"] = datetime.datetime.now().isoformat()
        pathlib.Path(os.path.dirname(self.state_path)).mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2)

    # ─── SESSION ─────────────────────────────────────────────────

    def start_session(self, session_id=None):
        """Initialize a new session."""
        self.state["session_id"] = session_id or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.state["started_at"] = datetime.datetime.now().isoformat()
        self.state["reasoning_log"] = []
        self._save()

    def get_session_id(self):
        return self.state.get("session_id")

    # ─── TASK MANAGEMENT ─────────────────────────────────────────

    def set_task(self, name, phase=None):
        """Set the current task being worked on."""
        self.state["current_task"] = {
            "name": name,
            "phase": phase,
            "status": "planning",
            "started_at": datetime.datetime.now().isoformat()
        }
        self.state["plan_steps"] = []
        self.state["step_results"] = {}
        self.state["blockers"] = []
        self._save()

    def set_task_status(self, status):
        """Update current task status: planning, executing, verifying, blocked, done."""
        self.state["current_task"]["status"] = status
        self._save()

    def get_task(self):
        return self.state.get("current_task", {})

    # ─── PLANNING ────────────────────────────────────────────────

    def set_plan(self, steps):
        """Set the ordered list of steps for the current task.
        steps: list of dicts with 'step' (number), 'action' (string), 'expected' (string)
        """
        self.state["plan_steps"] = steps
        self.state["current_task"]["status"] = "planning"
        self._save()

    def get_plan(self):
        return self.state.get("plan_steps", [])

    def next_step(self):
        """Get the first uncompleted step."""
        for step in self.state.get("plan_steps", []):
            if step.get("status") in (None, "pending"):
                return step
        return None

    # ─── EXECUTION TRACKING ──────────────────────────────────────

    def record_step_result(self, step_number, result, status="done", output_path=None):
        """Record what a step produced."""
        self.state["step_results"][str(step_number)] = {
            "result": result,
            "status": status,
            "output_path": output_path,
            "timestamp": datetime.datetime.now().isoformat()
        }
        # Update the step in the plan
        for step in self.state.get("plan_steps", []):
            if step.get("step") == step_number:
                step["status"] = status
                break
        self._save()

    def get_step_results(self):
        return self.state.get("step_results", {})

    # ─── BLOCKERS ────────────────────────────────────────────────

    def add_blocker(self, description, severity="medium"):
        """Log something blocking progress."""
        blocker = {
            "description": description,
            "severity": severity,
            "raised_at": datetime.datetime.now().isoformat()
        }
        self.state["blockers"].append(blocker)
        self.state["current_task"]["status"] = "blocked"
        self._save()
        return blocker

    def resolve_blocker(self, description):
        """Mark a blocker as resolved."""
        for blocker in self.state.get("blockers", []):
            if blocker["description"] == description and "resolved_at" not in blocker:
                blocker["resolved_at"] = datetime.datetime.now().isoformat()
                break
        # If no blockers remain, revert to previous status
        active = [b for b in self.state.get("blockers", []) if "resolved_at" not in b]
        if not active:
            self.state["current_task"]["status"] = "executing"
        self._save()

    def get_blockers(self):
        return [b for b in self.state.get("blockers", []) if "resolved_at" not in b]

    # ─── NEXT ACTION ─────────────────────────────────────────────

    def set_next_action(self, action):
        """What to do on the next turn."""
        self.state["next_action"] = action
        self._save()

    def get_next_action(self):
        return self.state.get("next_action")

    def clear_next_action(self):
        self.state["next_action"] = None
        self._save()

    # ─── CONTEXT ─────────────────────────────────────────────────

    def note_file_loaded(self, path):
        """Record that a file was loaded into context."""
        if path not in self.state["context"]["loaded_files"]:
            self.state["context"]["loaded_files"].append(path)
            self._save()

    def note_path_active(self, path):
        """Record an active working path."""
        if path not in self.state["context"]["active_paths"]:
            self.state["context"]["active_paths"].append(path)
            self._save()

    def add_session_note(self, note):
        """Add a freeform session note."""
        self.state["context"]["session_notes"].append({
            "note": note,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._save()

    def get_context(self):
        return self.state.get("context", {})

    # ─── REASONING LOG ───────────────────────────────────────────

    def log_reasoning(self, entry):
        """Log a reasoning step for audit trail."""
        self.state["reasoning_log"].append({
            "entry": entry,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._save()

    def get_reasoning_log(self, limit=None):
        log = self.state.get("reasoning_log", [])
        if limit:
            return log[-limit:]
        return log

    # ─── SUMMARY ─────────────────────────────────────────────────

    def summarize(self):
        """Return a concise summary of current state for the prompt."""
        task = self.get_task()
        blockers = self.get_blockers()
        next_action = self.get_next_action()

        lines = []
        if task.get("name"):
            lines.append(f"Current task: {task['name']} ({task['status']})")
        if next_action:
            lines.append(f"Next action: {next_action}")
        if blockers:
            lines.append(f"Blockers: {len(blockers)} active")
            for b in blockers[:3]:
                lines.append(f"  - {b['description']}")
        plan = self.get_plan()
        done_steps = [s for s in plan if s.get("status") == "done"]
        if plan:
            lines.append(f"Plan: {len(done_steps)}/{len(plan)} steps complete")
        return "\n".join(lines)

    def reset(self):
        """Reset to default state (start fresh)."""
        self.state = DEFAULT_STATE.copy()
        self._save()

    def __repr__(self):
        return f"<Scratchpad task={self.state['current_task']['name']} status={self.state['current_task']['status']}>"


# ─── SELF-TEST ───────────────────────────────────────────────────

def self_test():
    """Run the scratchpad through its paces."""
    import tempfile
    import os

    test_path = os.path.join(tempfile.gettempdir(), "vael_scratchpad_test.json")
    if os.path.exists(test_path):
        os.remove(test_path)

    sp = Scratchpad(test_path)
    results = []

    # Test 1: Start session
    sp.start_session("test-session")
    assert sp.get_session_id() == "test-session"
    results.append(("PASS", "start_session sets session_id"))

    # Test 2: Set task and plan
    sp.set_task("Build memory engine", phase="P1")
    assert sp.get_task()["name"] == "Build memory engine"
    sp.set_plan([
        {"step": 1, "action": "Write code", "expected": "file created", "status": "pending"},
        {"step": 2, "action": "Test it", "expected": "tests pass", "status": "pending"}
    ])
    assert len(sp.get_plan()) == 2
    results.append(("PASS", "set_task and set_plan work"))

    # Test 3: Record step results
    sp.record_step_result(1, "code written", "done", "/tmp/test.py")
    sp.record_step_result(2, "all tests pass", "done")
    assert len(sp.get_step_results()) == 2
    results.append(("PASS", "record_step_result works"))

    # Test 4: Blockers
    sp.add_blocker("Missing dependency", "high")
    assert len(sp.get_blockers()) == 1
    sp.resolve_blocker("Missing dependency")
    assert len(sp.get_blockers()) == 0
    results.append(("PASS", "blocker add/resolve works"))

    # Test 5: Next action
    sp.set_next_action("Run the tests")
    assert sp.get_next_action() == "Run the tests"
    sp.clear_next_action()
    assert sp.get_next_action() is None
    results.append(("PASS", "next_action set/clear works"))

    # Test 6: Context tracking
    sp.note_file_loaded("/path/to/file.py")
    sp.note_path_active("/workspace")
    ctx = sp.get_context()
    assert "/path/to/file.py" in ctx["loaded_files"]
    assert "/workspace" in ctx["active_paths"]
    results.append(("PASS", "context tracking works"))

    # Test 7: Reasoning log
    sp.log_reasoning("Decided to use SQLite over flat files for performance")
    log = sp.get_reasoning_log()
    assert len(log) == 1
    results.append(("PASS", "reasoning log works"))

    # Test 8: Summarize
    summary = sp.summarize()
    assert "Build memory engine" in summary
    assert "2/2 steps complete" in summary
    results.append(("PASS", "summarize produces coherent output"))

    # Test 9: Persistence (reload)
    sp2 = Scratchpad(test_path)
    assert sp2.get_task()["name"] == "Build memory engine"
    assert len(sp2.get_plan()) == 2
    results.append(("PASS", "state persists across reloads"))

    os.remove(test_path)

    print("=== SCRATCHPAD SELF-TEST RESULTS ===")
    for status, msg in results:
        print(f"  [{status}] {msg}")
    print(f"  Total: {len(results)}/{len(results)} passed")
    return all(s == "PASS" for s, _ in results)


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        success = self_test()
        sys.exit(0 if success else 1)
    else:
        sp = Scratchpad()
        print(f"Scratchpad state at: {sp.state_path}")
        print(sp.summarize() if sp.get_task().get("name") else "No active task")
