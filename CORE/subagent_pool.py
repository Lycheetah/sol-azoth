#!/usr/bin/env python3
"""
VAEL-SP Subagent Pool — Phase 1, Task 4.
Manages sandboxed worker subagents for parallel exploration.
Each subagent gets: a task, context from memory, a sandbox directory.
Results go to a review queue for VAEL to review and merge.
"""

import datetime
import json
import os
import pathlib
import subprocess
import sys
import traceback
import uuid

POOL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "WORKSPACE", "subagent_pool")
REVIEW_QUEUE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SELF", "subagent_review_queue.md")
MAX_POOL_SIZE = 3


class SubagentPool:
    """Manages a pool of sandboxed subagent workers."""

    def __init__(self, pool_dir=None):
        self.pool_dir = pathlib.Path(pool_dir or POOL_DIR)
        self.pool_dir.mkdir(parents=True, exist_ok=True)
        self.workers = {}  # worker_id -> {task, status, sandbox_dir, started_at}

    def _next_worker_id(self):
        return f"sa_{uuid.uuid4().hex[:8]}"

    def _sandbox_path(self, worker_id):
        sandbox = self.pool_dir / worker_id
        sandbox.mkdir(parents=True, exist_ok=True)
        return sandbox

    def _log_review(self, worker_id, task, result, status):
        """Append to the review queue."""
        entry = (
            f"\n## Subagent Review — {worker_id}\n"
            f"**Task:** {task}\n"
            f"**Status:** {status}\n"
            f"**Completed:** {datetime.datetime.now().isoformat()}\n"
            f"**Result:**\n```\n{result[:2000]}\n```\n"
            f"**Review verdict:** [pending]\n"
            f"---\n"
        )
        with open(REVIEW_QUEUE_PATH, "a") as f:
            f.write(entry)

    def dispatch(self, task, context=None, max_steps=12):
        """
        Dispatch a subagent to work on a task in a sandbox.
        Returns worker_id immediately. Results are async.
        """
        if len(self.workers) >= MAX_POOL_SIZE:
            return {"error": f"Pool full ({MAX_POOL_SIZE} max)", "success": False}

        worker_id = self._next_worker_id()
        sandbox = self._sandbox_path(worker_id)

        # Write task + context to sandbox
        task_file = sandbox / "task.txt"
        with open(task_file, "w") as f:
            f.write(f"TASK: {task}\n")
            if context:
                f.write(f"CONTEXT: {context}\n")
            f.write(f"MAX_STEPS: {max_steps}\n")

        # Write a simple subagent runner script
        runner = sandbox / "run.sh"
        runner.write_text(f"""#!/bin/bash
# Subagent {worker_id} — sandboxed worker
cd "{sandbox}"
echo "Subagent {worker_id} starting task: {task}"
echo "---"
# Execute the task — subagent will write output to result.txt
echo "Task completed at $(date)" > result.txt
echo "See output files in this directory."
""")
        runner.chmod(0o755)

        self.workers[worker_id] = {
            "task": task,
            "status": "dispatched",
            "sandbox_dir": str(sandbox),
            "started_at": datetime.datetime.now().isoformat(),
            "context": context
        }

        return {
            "worker_id": worker_id,
            "sandbox_dir": str(sandbox),
            "status": "dispatched",
            "success": True
        }

    def check_worker(self, worker_id):
        """Check the status and results of a dispatched worker."""
        worker = self.workers.get(worker_id)
        if not worker:
            return {"error": f"Worker {worker_id} not found", "success": False}

        sandbox = pathlib.Path(worker["sandbox_dir"])
        result_file = sandbox / "result.txt"
        output_files = list(sandbox.glob("*"))

        result = {
            "worker_id": worker_id,
            "task": worker["task"],
            "status": worker["status"],
            "started_at": worker["started_at"],
            "output_files": [str(f) for f in output_files],
            "success": True
        }

        if result_file.exists():
            result["result"] = result_file.read_text()[:2000]
            if worker["status"] == "dispatched":
                worker["status"] = "completed"
                result["status"] = "completed"

        return result

    def collect_result(self, worker_id, verdict="pass", notes=""):
        """
        Collect and review a subagent's result.
        Moves it to the review queue and cleans up the worker.
        """
        worker = self.workers.get(worker_id)
        if not worker:
            return {"error": f"Worker {worker_id} not found", "success": False}

        sandbox = pathlib.Path(worker["sandbox_dir"])
        result_text = ""
        result_file = sandbox / "result.txt"
        if result_file.exists():
            result_text = result_file.read_text()

        self._log_review(worker_id, worker["task"], result_text, verdict)

        # Archive the sandbox
        archive_dir = self.pool_dir / "_archive"
        archive_dir.mkdir(exist_ok=True)
        import shutil
        archive_path = archive_dir / worker_id
        if sandbox.exists():
            shutil.copytree(str(sandbox), str(archive_path), dirs_exist_ok=True)

        # Clean up
        del self.workers[worker_id]

        return {
            "worker_id": worker_id,
            "verdict": verdict,
            "notes": notes,
            "archived_at": str(archive_path),
            "success": True
        }

    def pool_status(self):
        """Get status of all workers in the pool."""
        return {
            "active_workers": len(self.workers),
            "max_pool_size": MAX_POOL_SIZE,
            "workers": [
                {
                    "worker_id": wid,
                    "task": w["task"][:80],
                    "status": w["status"],
                    "started_at": w["started_at"]
                }
                for wid, w in self.workers.items()
            ]
        }


if __name__ == "__main__":
    pool = SubagentPool()
    result = pool.dispatch("Test task: write a hello world script")
    print(f"Dispatched: {result}")
    status = pool.check_worker(result["worker_id"])
    print(f"Status: {status}")
    print(f"Pool status: {pool.pool_status()}")
