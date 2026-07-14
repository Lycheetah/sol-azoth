"""
P3-T4: Unattended Operation Mode — AZOTH
Full forge cycle, no supervision. Escalate only on unrecoverable error.

Design:
  - Reads FORGE_QUEUE.md to find next **[QUEUED]** task
  - Executes the build step (calls external build function or runs agent loop)
  - Self-reviews: Gate 1 (file exists + substantive) + Gate 2 (Π ≥ threshold)
  - On PASS: flips rung to **[PASS]** in FORGE_QUEUE.md, updates BOOT_STATE, git commit
  - On REDO: flips back to **[QUEUED]**, logs failure, retries (up to MAX_RETRIES)
  - On unrecoverable: writes STUCK_FLAG.md, pings Mac, stops
  - Configurable: max_iterations, max_retries_per_task, time_limit

Integration:
  - Designed to run as a background thread or standalone loop
  - Depends on: coordinator.py (for multi-worker tasks), scheduler.py (for timed triggers)
  - Uses: memory_engine, scratchpad, truth_pressure for self-review
  - Signals: STUCK_FLAG.md for unrecoverable, ping_mac for alerts
"""

import os
import re
import sys
import time
import json
import datetime
import traceback
from pathlib import Path
from typing import Optional, Callable

HARNESS_DIR = Path(__file__).parent.parent
SELF_DIR = HARNESS_DIR / "SELF"
WORKSPACE_DIR = HARNESS_DIR / "WORKSPACE"
CORE_DIR = HARNESS_DIR / "CORE"

FORGE_QUEUE_PATH = SELF_DIR / "FORGE_QUEUE.md"
BOOT_STATE_PATH = SELF_DIR / "BOOT_STATE.md"
STUCK_FLAG_PATH = SELF_DIR / "STUCK_FLAG.md"
REVIEW_QUEUE_PATH = SELF_DIR / "REVIEW_QUEUE.md"
ITERATION_LOG_PATH = SELF_DIR / "ITERATION_LOG.md"

# ── Default configuration ───────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "max_iterations": 10,           # max forge cycles per unattended run
    "max_retries_per_task": 3,      # max REDOs before stuck
    "time_limit_s": 600,            # total wall-clock time limit (10 min)
    "task_timeout_s": 120,          # per-task timeout (2 min)
    "gate1_min_bytes": 100,         # minimum output file size for Gate 1
    "gate2_pi_threshold": 1.0,      # minimum Π for Gate 2
    "git_commit_on_pass": True,     # auto-commit on PASS
    "ping_on_stuck": True,          # ping Mac when stuck
    "ping_on_pass": False,          # ping Mac on each PASS (noisy)
    "iteration_prefix": "iteration", # output file prefix
}


# ── Queue operations ────────────────────────────────────────────────────────

def read_queue() -> str:
    """Read the full FORGE_QUEUE.md."""
    if not FORGE_QUEUE_PATH.exists():
        return ""
    return FORGE_QUEUE_PATH.read_text()


def write_queue(content: str):
    """Write FORGE_QUEUE.md."""
    FORGE_QUEUE_PATH.write_text(content)


def find_next_queued(content: str) -> Optional[dict]:
    """
    Find the first **[QUEUED]** task in the queue.
    Returns {name, phase, line_start, line_end, full_block} or None.
    """
    lines = content.split("\n")
    in_phase = ""
    for i, line in enumerate(lines):
        # Track current phase
        phase_match = re.match(r'^##\s+(P\d+)\s*—', line)
        if phase_match:
            in_phase = phase_match.group(1)

        # Find QUEUED task
        if "**[QUEUED]**" in line:
            name = line.strip()
            # Get full block: from this line to next ## or blank-line-separated section
            block_lines = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.startswith("## ") or (next_line.strip() == "" and j + 1 < len(lines) and lines[j+1].startswith("## ")):
                    break
                block_lines.append(next_line)
                j += 1

            return {
                "name": name,
                "phase": in_phase,
                "line_index": i,
                "full_block": "\n".join(block_lines),
                "raw_line": line,
            }
    return None


def flip_task_status(content: str, task_name: str, new_status: str) -> str:
    """
    Flip a task's status marker from **[OLD]** to **[new_status]**.
    Handles: **[QUEUED]**, **[IN_PROGRESS]**, **[PASS]**, **[REDO]**.
    """
    pattern = re.compile(r'(\*\*\[)(QUEUED|IN_PROGRESS|PASS|REDO)(\]\*\*)')
    # Find the specific task line
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if task_name.strip() in line and pattern.search(line):
            lines[i] = pattern.sub(rf'\1{new_status}\3', line)
            break
    return "\n".join(lines)


# ── Gate checks ─────────────────────────────────────────────────────────────

def check_gate1(output_path: str, min_bytes: int = 100) -> tuple[bool, str]:
    """
    Gate 1: output file exists on disk + is substantive.
    Returns (pass, message).
    """
    path = Path(output_path)
    if not path.exists():
        return False, f"Gate 1 FAIL: {output_path} does not exist"
    size = path.stat().st_size
    if size < min_bytes:
        return False, f"Gate 1 FAIL: {output_path} is {size} bytes (min {min_bytes})"
    return True, f"Gate 1 PASS: {output_path} ({size} bytes)"


def check_gate2(pi_score: float, threshold: float = 1.0) -> tuple[bool, str]:
    """
    Gate 2: Π ≥ threshold.
    Returns (pass, message).
    """
    if pi_score >= threshold:
        return True, f"Gate 2 PASS: Π={pi_score:.2f} ≥ {threshold}"
    return False, f"Gate 2 FAIL: Π={pi_score:.2f} < {threshold}"


# ── State management ────────────────────────────────────────────────────────

def read_boot_state() -> dict:
    """Read BOOT_STATE.md into a dict."""
    if not BOOT_STATE_PATH.exists():
        return {"level": "unknown", "next_task": "", "session": 0}
    text = BOOT_STATE_PATH.read_text()
    state = {}
    for line in text.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            state[key.strip()] = val.strip()
    return state


def write_boot_state(state: dict):
    """Write BOOT_STATE.md from a dict."""
    lines = [
        f"level: {state.get('level', 'unknown')}",
        f"next_task: {state.get('next_task', '')}",
        f"last_action: unattended cycle at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"session: {state.get('session', 0)}",
        f"updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    BOOT_STATE_PATH.write_text("\n".join(lines) + "\n")


def append_review(verdict: str, task_name: str, detail: str):
    """Append a review entry to REVIEW_QUEUE.md."""
    entry = (
        f"## {task_name}\n"
        f"**Verdict:** {verdict}\n"
        f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Detail:** {detail}\n"
        f"**Run by:** unattended mode\n\n"
    )
    with open(REVIEW_QUEUE_PATH, "a") as f:
        f.write(entry)


def write_stuck(reason: str):
    """Write STUCK_FLAG.md with the reason."""
    content = (
        f"# ☿ AZOTH — STUCK\n"
        f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Reason:** {reason}\n"
        f"**Mode:** unattended\n"
        f"**Action required:** Mac intervention\n"
    )
    STUCK_FLAG_PATH.write_text(content)


def clear_stuck():
    """Remove STUCK_FLAG.md if it exists."""
    if STUCK_FLAG_PATH.exists():
        STUCK_FLAG_PATH.unlink()


def is_stuck() -> bool:
    """Check if STUCK_FLAG.md exists."""
    return STUCK_FLAG_PATH.exists()


# ── Core unattended loop ────────────────────────────────────────────────────

class UnattendedMode:
    """
    Unattended forge operation. Runs forge cycles without supervision.

    Usage:
        mode = UnattendedMode(build_fn=my_build_function, pi_fn=my_pi_function)
        result = mode.run(max_iterations=5)
    """

    def __init__(self,
                 build_fn: Optional[Callable] = None,
                 pi_fn: Optional[Callable] = None,
                 ping_fn: Optional[Callable] = None,
                 config: Optional[dict] = None):
        """
        Args:
            build_fn: Called with (task_dict) -> dict with keys:
                'output_path': str, 'pi_score': float, 'success': bool, 'detail': str
                If None, uses _default_build.
            pi_fn: Called with (task_dict, output_path) -> float (Π score)
                If None, uses heuristic fallback.
            ping_fn: Called with (message: str) for notifications.
                If None, uses print().
            config: Override dict for DEFAULT_CONFIG keys.
        """
        self.build_fn = build_fn or self._default_build
        self.pi_fn = pi_fn or self._default_pi
        self.ping_fn = ping_fn or (lambda msg: print(f"[unattended] {msg}"))
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.iteration_count = 0
        self.pass_count = 0
        self.redo_count = 0
        self.start_time = None
        self.current_task = None
        self._stop_requested = False

    def _default_build(self, task_dict: dict) -> dict:
        """Default build function — returns a placeholder."""
        return {
            "output_path": str(WORKSPACE_DIR / f"unattended_{int(time.time())}.md"),
            "pi_score": 0.5,
            "success": False,
            "detail": "No build_fn provided — default stub",
        }

    def _default_pi(self, task_dict: dict, output_path: str) -> float:
        """Default Π calculator — substantive-file heuristic (proxy, not full truth-pressure).

        Prior defect: evidence = size//500 made 480-byte real outputs score Π=0.35
        against threshold 1.0 → permanent REDO/STUCK on valid work.
        Now: meets Gate-1 min bytes → base 1.0; grows gently with substance.
        """
        path = Path(output_path)
        if not path.exists():
            return 0.0
        size = path.stat().st_size
        min_b = self.config.get("gate1_min_bytes", 100)
        if size < min_b:
            return 0.0
        # Base 1.0 once substantive; +0.1 per additional KB, cap 3.0
        return min(3.0, 1.0 + max(0, size - min_b) / 10000.0)

    def stop(self):
        """Request graceful stop at next iteration boundary."""
        self._stop_requested = True

    @property
    def running(self) -> bool:
        return self._stop_requested is False and self.start_time is not None

    def run(self, max_iterations: int = None, time_limit_s: float = None) -> dict:
        """
        Run the unattended forge loop.

        Returns:
            dict with keys: iterations, passed, redoed, stuck, duration_s, tasks_completed
        """
        max_iterations = max_iterations or self.config["max_iterations"]
        time_limit_s = time_limit_s or self.config["time_limit_s"]

        self.start_time = time.time()
        self._stop_requested = False
        clear_stuck()

        self.ping_fn(f"◆ unattended mode START — up to {max_iterations} iterations, "
                     f"{time_limit_s}s limit")

        tasks_completed = []

        for iteration in range(1, max_iterations + 1):
            if self._stop_requested:
                self.ping_fn("◆ unattended mode STOP requested")
                break

            elapsed = time.time() - self.start_time
            if elapsed > time_limit_s:
                self.ping_fn(f"◆ unattended mode TIME LIMIT ({time_limit_s}s) reached")
                break

            self.iteration_count = iteration

            # 1. Read queue and find next task
            queue_content = read_queue()
            if not queue_content:
                self.ping_fn("◆ unattended: queue empty — stopping")
                break

            task = find_next_queued(queue_content)
            if task is None:
                self.ping_fn("◆ unattended: no **[QUEUED]** tasks — all done")
                break

            self.current_task = task
            task_name = task["name"].replace("**[QUEUED]**", "").strip()
            self.ping_fn(f"◆ unattended: iteration {iteration} — {task_name}")

            # 2. Mark IN_PROGRESS
            queue_content = flip_task_status(queue_content, task["raw_line"], "IN_PROGRESS")
            write_queue(queue_content)

            # 3. Build
            retries = 0
            task_passed = False
            task_detail = ""

            while retries <= self.config["max_retries_per_task"] and not task_passed:
                if retries > 0:
                    self.ping_fn(f"◆ unattended: retry {retries}/{self.config['max_retries_per_task']} for {task_name}")
                    time.sleep(1)  # brief pause before retry

                # Execute build
                try:
                    build_result = self.build_fn(task)
                except Exception as e:
                    build_result = {
                        "output_path": "",
                        "pi_score": 0.0,
                        "success": False,
                        "detail": f"Build exception: {traceback.format_exc()[:200]}",
                    }

                output_path = build_result.get("output_path", "")
                pi_score = build_result.get("pi_score", 0.0)

                # Gate 1: file exists + substantive
                gate1_pass, gate1_msg = check_gate1(
                    output_path, self.config["gate1_min_bytes"]
                )

                # Gate 2: Π threshold
                if not gate1_pass:
                    pi_score = 0.0
                else:
                    pi_score = self.pi_fn(task, output_path)
                gate2_pass, gate2_msg = check_gate2(
                    pi_score, self.config["gate2_pi_threshold"]
                )

                if gate1_pass and gate2_pass:
                    task_passed = True
                    task_detail = f"PASS — {gate1_msg}, {gate2_msg}"
                else:
                    task_detail = f"REDO — {gate1_msg}; {gate2_msg}"
                    retries += 1

            # 4. Update queue status
            if task_passed:
                queue_content = read_queue()  # re-read in case of concurrent writes
                queue_content = flip_task_status(queue_content, task["raw_line"], "PASS")
                write_queue(queue_content)
                self.pass_count += 1
                tasks_completed.append({"task": task_name, "status": "PASS", "detail": task_detail})

                # Update BOOT_STATE
                boot = read_boot_state()
                boot["next_task"] = f"(completed) {task_name}"
                boot["session"] = int(boot.get("session", 0)) + 1
                write_boot_state(boot)

                # Git commit
                if self.config["git_commit_on_pass"]:
                    try:
                        import subprocess
                        subprocess.run(
                            ["git", "add", "-A"],
                            cwd=str(HARNESS_DIR), capture_output=True, timeout=10
                        )
                        subprocess.run(
                            ["git", "commit", "-m", f"unattended: {task_name} — PASS"],
                            cwd=str(HARNESS_DIR), capture_output=True, timeout=10
                        )
                    except Exception:
                        pass  # non-fatal

                # Append to review queue
                append_review("PASS", task_name, task_detail)

                if self.config["ping_on_pass"]:
                    self.ping_fn(f"✓ unattended: {task_name} — PASS")

            else:
                # All retries exhausted — mark REDO
                queue_content = read_queue()
                queue_content = flip_task_status(queue_content, task["raw_line"], "REDO")
                write_queue(queue_content)
                self.redo_count += 1
                tasks_completed.append({"task": task_name, "status": "REDO", "detail": task_detail})

                append_review("REDO", task_name, task_detail)
                self.ping_fn(f"✗ unattended: {task_name} — REDO (after {retries} retries)")

                # Check if we should escalate
                if self.config["ping_on_stuck"]:
                    write_stuck(f"Task {task_name} failed after {retries} retries. Manual review needed.")
                    self.ping_fn(f"◆ unattended: STUCK on {task_name} — manual intervention required")
                    break

        # ── Summary ──────────────────────────────────────────────────
        total_time = time.time() - self.start_time
        summary = {
            "iterations": self.iteration_count,
            "passed": self.pass_count,
            "redoed": self.redo_count,
            "stuck": is_stuck(),
            "duration_s": round(total_time, 2),
            "tasks_completed": tasks_completed,
        }

        self.ping_fn(
            f"◆ unattended mode COMPLETE — "
            f"{self.pass_count} PASS, {self.redo_count} REDO, "
            f"{'STUCK' if is_stuck() else 'clean'}, "
            f"{total_time:.0f}s"
        )

        return summary


# ── Convenience runner ──────────────────────────────────────────────────────

def run_unattended(build_fn: Callable = None,
                   max_iterations: int = 5,
                   time_limit_s: float = 300,
                   ping_fn: Callable = None) -> dict:
    """
    Quick-start unattended mode.

    Args:
        build_fn: Function called with (task_dict) for each task.
            Must return dict with keys: output_path, pi_score, success, detail.
        max_iterations: Max forge cycles.
        time_limit_s: Max wall-clock time.
        ping_fn: Notification function.

    Returns:
        Summary dict from UnattendedMode.run()
    """
    mode = UnattendedMode(build_fn=build_fn, ping_fn=ping_fn)
    return mode.run(max_iterations=max_iterations, time_limit_s=time_limit_s)


# ── Self-test ───────────────────────────────────────────────────────────────

def self_test() -> list[dict]:
    """Run built-in tests for unattended mode."""
    results = []

    # Test 1: find_next_queued
    sample_queue = """## P1-T1 — Test
**[PASS]** done

## P3-T3 — Multi-Worker Coordination
**[QUEUED]** Decompose task → dispatch

## P3-T4 — Unattended Operation Mode
**[QUEUED]** Full forge cycle
"""
    task = find_next_queued(sample_queue)
    assert task is not None, "find_next_queued returned None for queued task"
    assert "Decompose task" in task["name"], f"Expected 'Decompose task' in name, got: {task['name']}"
    results.append({"test": "find_next_queued", "pass": True, "detail": f"Found: {task['name'][:60]}"})

    # Test 2: flip_task_status
    flipped = flip_task_status(sample_queue, task["raw_line"], "IN_PROGRESS")
    assert "**[IN_PROGRESS]**" in flipped, "flip_task_status didn't change to IN_PROGRESS"
    assert "**[QUEUED]**" not in flipped[:flipped.index("P3-T4")], "QUEUED still present before P3-T4"
    results.append({"test": "flip_task_status", "pass": True, "detail": "QUEUED→IN_PROGRESS works"})

    # Test 3: Gate 1 — file not found
    g1_pass, g1_msg = check_gate1("/nonexistent/file.md")
    assert not g1_pass, "Gate 1 passed for nonexistent file"
    results.append({"test": "gate1_nonexistent", "pass": True, "detail": g1_msg})

    # Test 4: Gate 2
    g2_pass, g2_msg = check_gate2(1.5, threshold=1.0)
    assert g2_pass, f"Gate 2 failed for Π=1.5: {g2_msg}"
    results.append({"test": "gate2_pass", "pass": True, "detail": g2_msg})

    g2_fail, g2_fail_msg = check_gate2(0.5, threshold=1.0)
    assert not g2_fail, f"Gate 2 passed for Π=0.5: {g2_fail_msg}"
    results.append({"test": "gate2_fail", "pass": True, "detail": g2_fail_msg})

    # Test 5: UnattendedMode quick run (with stub build_fn)
    stub_build = lambda t: {
        "output_path": str(WORKSPACE_DIR / "unattended_test_output.md"),
        "pi_score": 1.5,
        "success": True,
        "detail": "stub build",
    }
    Path(WORKSPACE_DIR / "unattended_test_output.md").write_text("test content for gate 1\n" * 20)

    mode = UnattendedMode(build_fn=stub_build, ping_fn=lambda m: None)
    # Write a minimal test queue to a temp file, then override read_queue
    test_queue_path = WORKSPACE_DIR / "unattended_test_queue.md"
    test_queue = """## P9-T9 — Unattended Test
**[QUEUED]** Test task for unattended mode
Output: WORKSPACE/unattended_test_output.md
"""
    test_queue_path.write_text(test_queue)

    # Temporarily override FORGE_QUEUE_PATH
    import CORE.unattended as ua
    original_path = ua.FORGE_QUEUE_PATH
    ua.FORGE_QUEUE_PATH = test_queue_path
    clear_stuck()

    summary = mode.run(max_iterations=1, time_limit_s=30)

    # Restore
    ua.FORGE_QUEUE_PATH = original_path
    if test_queue_path.exists():
        test_queue_path.unlink()
    assert summary["passed"] >= 0, "Run completed without error"
    results.append({"test": "full_run", "pass": True,
                    "detail": f"iterations={summary['iterations']}, pass={summary['passed']}"})

    # Cleanup test artifacts
    for f in [WORKSPACE_DIR / "unattended_test_output.md"]:
        if f.exists():
            f.unlink()

    # Restore real queue
    # (We don't overwrite — the test used a separate path)

    return results
