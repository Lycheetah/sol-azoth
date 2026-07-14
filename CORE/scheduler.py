"""
P3-T1: Background Scheduler — AZOTH
Cron-like task scheduler. Register tasks, run on interval, log results, ping Mac on failure.
No external dependencies. Single daemon thread polls every second.
"""

import threading, time, datetime, json, traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional

HARNESS_DIR   = Path(__file__).parent.parent
SCHEDULE_FILE = HARNESS_DIR / "SELF" / "schedule.json"


@dataclass
class ScheduledTask:
    name: str
    fn: Callable                    # zero-arg callable; raise on failure
    interval_s: float               # seconds between runs (0 = one-shot)
    enabled: bool = True
    last_run: Optional[float] = None
    last_status: str = "pending"    # pending / ok / fail
    last_error: str = ""
    run_count: int = 0
    fail_count: int = 0
    next_run: float = field(default_factory=time.time)

    def due(self) -> bool:
        return self.enabled and time.time() >= self.next_run

    def schedule_next(self):
        if self.interval_s > 0:
            self.next_run = time.time() + self.interval_s
        else:
            self.enabled = False   # one-shot — disable after first run


class Scheduler:
    """Background task scheduler. One daemon thread, one second poll loop."""

    def __init__(self, ping_fn: Callable = None):
        self._tasks: dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._ping = ping_fn   # called with (message: str) on failure
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._log: list[dict] = []   # in-memory run log, last 200 entries
        self._LOG_CAP = 200

    # ── Registration ──────────────────────────────────────────────

    def register(self, name: str, fn: Callable, interval_s: float,
                 run_immediately: bool = False, enabled: bool = True) -> "Scheduler":
        """Add or replace a scheduled task."""
        next_run = time.time() if run_immediately else time.time() + interval_s
        with self._lock:
            self._tasks[name] = ScheduledTask(
                name=name, fn=fn, interval_s=interval_s,
                enabled=enabled, next_run=next_run,
            )
        return self

    def unregister(self, name: str) -> bool:
        with self._lock:
            return self._tasks.pop(name, None) is not None

    def enable(self, name: str):
        with self._lock:
            if name in self._tasks:
                self._tasks[name].enabled = True

    def disable(self, name: str):
        with self._lock:
            if name in self._tasks:
                self._tasks[name].enabled = False

    # ── Execution ─────────────────────────────────────────────────

    def _run_task(self, task: ScheduledTask):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        t0 = time.perf_counter()
        try:
            task.fn()
            duration = time.perf_counter() - t0
            task.last_status = "ok"
            task.last_error  = ""
            task.run_count  += 1
            entry = {"ts": ts, "task": task.name, "status": "ok",
                     "duration_ms": int(duration * 1000)}
        except Exception as ex:
            duration = time.perf_counter() - t0
            tb = traceback.format_exc().strip().split("\n")[-1]
            task.last_status = "fail"
            task.last_error  = tb
            task.run_count  += 1
            task.fail_count += 1
            entry = {"ts": ts, "task": task.name, "status": "fail",
                     "error": tb, "duration_ms": int(duration * 1000)}
            if self._ping:
                try:
                    self._ping(f"◆ scheduler: {task.name} FAILED — {tb[:120]}")
                except Exception:
                    pass

        task.last_run = time.time()
        task.schedule_next()

        with self._lock:
            self._log.append(entry)
            if len(self._log) > self._LOG_CAP:
                del self._log[: len(self._log) - self._LOG_CAP]

    def _loop(self):
        while self._running:
            with self._lock:
                due = [t for t in self._tasks.values() if t.due()]
            for task in due:
                threading.Thread(target=self._run_task, args=(task,), daemon=True).start()
            time.sleep(0.1)   # 100ms poll — responsive without burning CPU

    # ── Lifecycle ─────────────────────────────────────────────────

    def start(self) -> "Scheduler":
        if self._running:
            return self
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="azoth-scheduler")
        self._thread.start()
        return self

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    @property
    def running(self) -> bool:
        return self._running

    # ── Status ────────────────────────────────────────────────────

    def status(self) -> dict:
        with self._lock:
            tasks = []
            for t in self._tasks.values():
                next_in = max(0.0, t.next_run - time.time()) if t.enabled else None
                tasks.append({
                    "name":        t.name,
                    "enabled":     t.enabled,
                    "interval_s":  t.interval_s,
                    "last_status": t.last_status,
                    "last_error":  t.last_error[:80] if t.last_error else "",
                    "run_count":   t.run_count,
                    "fail_count":  t.fail_count,
                    "next_in_s":   round(next_in, 1) if next_in is not None else None,
                })
            return {
                "running":     self._running,
                "task_count":  len(tasks),
                "tasks":       tasks,
                "log_entries": len(self._log),
            }

    def recent_log(self, n: int = 20) -> list:
        with self._lock:
            return list(self._log[-n:])

    def task_names(self) -> list:
        with self._lock:
            return list(self._tasks.keys())


# ── Module-level singleton ────────────────────────────────────────────────────
_scheduler: Optional[Scheduler] = None

def get_scheduler(ping_fn: Callable = None) -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(ping_fn=ping_fn)
    return _scheduler

def reset_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.stop()
    _scheduler = None
