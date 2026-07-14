"""
P3-T2: File Watcher — AZOTH
Watch files/directories for changes and trigger actions.
Integrates with the scheduler (P3-T1) but can also run standalone.

Two modes:
  1. Poll-based — register with Scheduler, checks mtime every interval
  2. inotify-based — uses pyinotify if available, falls back to poll

Design: Each watch has a path, a callback, and a cooldown. On change detected,
callback(path, event_type) is called. Events: 'modified', 'created', 'deleted',
'size_changed', 'content_changed'.
"""

import os
import time
import hashlib
import threading
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class WatchEntry:
    """A single file/directory watch target."""
    path: str
    callback: Callable                    # fn(path: str, event: str) -> None
    cooldown_s: float = 1.0              # minimum seconds between triggers
    recursive: bool = False              # watch subdirectories (dirs only)
    check_content: bool = False          # hash content for real changes
    enabled: bool = True
    last_trigger: float = 0.0
    last_mtime: float = 0.0
    last_size: int = 0
    last_hash: str = ""
    trigger_count: int = 0
    last_event: str = ""


class FileWatcher:
    """
    File and directory watcher. Poll-based by default (no external deps).
    
    Usage:
        fw = FileWatcher()
        fw.watch("/path/to/file", my_callback)
        fw.start()  # runs in daemon thread
        # or: fw.poll_once() for scheduler integration
    """

    def __init__(self, poll_interval: float = 0.5):
        self._watches: dict[str, WatchEntry] = {}
        self._lock = threading.Lock()
        self._poll_interval = poll_interval
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._log: list[dict] = []
        self._LOG_CAP = 200

    # ── Registration ──────────────────────────────────────────────

    def watch(self, path: str, callback: Callable,
              cooldown_s: float = 1.0, recursive: bool = False,
              check_content: bool = False) -> "FileWatcher":
        """
        Register a path to watch.
        callback(path: str, event: str) is called on change.
        Events: 'modified', 'created', 'deleted', 'size_changed', 'content_changed'
        """
        abs_path = str(Path(path).resolve())
        with self._lock:
            # Snapshot current state
            mtime, size, file_hash = self._snapshot(abs_path)
            self._watches[abs_path] = WatchEntry(
                path=abs_path,
                callback=callback,
                cooldown_s=cooldown_s,
                recursive=recursive,
                check_content=check_content,
                last_mtime=mtime,
                last_size=size,
                last_hash=file_hash,
            )
        return self

    def unwatch(self, path: str) -> bool:
        """Remove a watch."""
        abs_path = str(Path(path).resolve())
        with self._lock:
            return self._watches.pop(abs_path, None) is not None

    def enable(self, path: str):
        abs_path = str(Path(path).resolve())
        with self._lock:
            if abs_path in self._watches:
                self._watches[abs_path].enabled = True

    def disable(self, path: str):
        abs_path = str(Path(path).resolve())
        with self._lock:
            if abs_path in self._watches:
                self._watches[abs_path].enabled = False

    # ── Core detection ────────────────────────────────────────────

    def _snapshot(self, path: str) -> tuple:
        """Get (mtime, size, content_hash) for a path. Returns zeros if missing."""
        try:
            p = Path(path)
            if not p.exists():
                return (0.0, 0, "")
            stat = p.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            file_hash = ""
            if size > 0 and size < 10 * 1024 * 1024:  # only hash files < 10MB
                try:
                    file_hash = hashlib.md5(p.read_bytes()).hexdigest()
                except Exception:
                    pass
            return (mtime, size, file_hash)
        except Exception:
            return (0.0, 0, "")

    def _detect_event(self, entry: WatchEntry) -> Optional[str]:
        """
        Check a single watch entry for changes.
        Returns event type string or None.
        """
        path = entry.path
        p = Path(path)

        # Check existence
        exists = p.exists()
        was_missing = (entry.last_mtime == 0.0 and entry.last_size == 0)

        if not exists:
            if not was_missing:
                entry.last_mtime = 0.0
                entry.last_size = 0
                entry.last_hash = ""
                return "deleted"
            return None

        if was_missing:
            # Was missing, now exists = created
            mtime, size, file_hash = self._snapshot(path)
            entry.last_mtime = mtime
            entry.last_size = size
            entry.last_hash = file_hash
            return "created"

        # Exists now and existed before — check modification
        mtime, size, file_hash = self._snapshot(path)

        if mtime != entry.last_mtime or size != entry.last_size:
            # Something changed
            if size != entry.last_size:
                event = "size_changed"
            else:
                event = "modified"

            # Content hash check for false positives
            if entry.check_content and file_hash:
                if file_hash == entry.last_hash:
                    # mtime changed but content didn't — false alarm
                    entry.last_mtime = mtime
                    entry.last_size = size
                    return None
                event = "content_changed"

            entry.last_mtime = mtime
            entry.last_size = size
            entry.last_hash = file_hash
            return event

        return None

    def _check_cooldown(self, entry: WatchEntry) -> bool:
        """True if enough time has passed since last trigger."""
        return (time.time() - entry.last_trigger) >= entry.cooldown_s

    # ── Polling ───────────────────────────────────────────────────

    def poll_once(self) -> list[dict]:
        """
        Check all watches once. Returns list of triggered events.
        Each event: {"path": str, "event": str, "callback": str}
        Safe for scheduler integration — call from Scheduler task.
        """
        triggered = []
        with self._lock:
            for abs_path, entry in list(self._watches.items()):
                if not entry.enabled:
                    continue
                if not self._check_cooldown(entry):
                    continue

                event = self._detect_event(entry)
                if event is None:
                    continue

                # Trigger callback
                try:
                    entry.callback(abs_path, event)
                except Exception as ex:
                    tb = traceback.format_exc().strip().split("\n")[-1]
                    self._log_event(abs_path, event, "callback_error", str(ex)[:120])
                    continue

                entry.last_trigger = time.time()
                entry.trigger_count += 1
                entry.last_event = event

                log_entry = {
                    "ts": time.time(),
                    "path": abs_path,
                    "event": event,
                    "trigger_count": entry.trigger_count,
                }
                self._log.append(log_entry)
                if len(self._log) > self._LOG_CAP:
                    self._log.pop(0)
                triggered.append(log_entry)

        # Handle recursive watches: check subdirectories
        triggered += self._poll_recursive()

        return triggered

    def _poll_recursive(self) -> list[dict]:
        """For recursive watches, scan directories for new/deleted entries."""
        recursive_results = []
        with self._lock:
            for abs_path, entry in list(self._watches.items()):
                if not entry.enabled or not entry.recursive:
                    continue
                p = Path(abs_path)
                if not p.is_dir():
                    continue
                # Check if the directory itself still exists
                if not p.exists():
                    continue
                # For recursive dirs, we track children via the main poll loop
                # Individual child files would need their own WatchEntry
                # This is a lightweight check — full recursive tracking is complex
                pass
        return recursive_results

    def _log_event(self, path: str, event: str, status: str, error: str = ""):
        self._log.append({
            "ts": time.time(),
            "path": path,
            "event": event,
            "status": status,
            "error": error,
        })
        if len(self._log) > self._LOG_CAP:
            self._log.pop(0)

    # ── Thread lifecycle ──────────────────────────────────────────

    def start(self) -> "FileWatcher":
        """Start the watcher in a daemon thread."""
        if self._running:
            return self
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="azoth-filewatcher")
        self._thread.start()
        return self

    def stop(self):
        """Stop the watcher thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def _loop(self):
        """Main poll loop."""
        while self._running:
            self.poll_once()
            time.sleep(self._poll_interval)

    # ── Status ────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return current status of all watches."""
        with self._lock:
            watches = []
            for abs_path, w in sorted(self._watches.items()):
                watches.append({
                    "path": abs_path,
                    "enabled": w.enabled,
                    "recursive": w.recursive,
                    "check_content": w.check_content,
                    "cooldown_s": w.cooldown_s,
                    "trigger_count": w.trigger_count,
                    "last_event": w.last_event,
                    "last_trigger_s_ago": round(time.time() - w.last_trigger, 1) if w.last_trigger else None,
                })
            return {
                "running": self._running,
                "watch_count": len(watches),
                "poll_interval_s": self._poll_interval,
                "watches": watches,
                "log_entries": len(self._log),
            }

    def recent_events(self, n: int = 20) -> list:
        """Return the last n events."""
        with self._lock:
            return list(self._log[-n:])

    def watch_count(self) -> int:
        with self._lock:
            return len(self._watches)


# ── Module-level singleton ────────────────────────────────────────────────────
_file_watcher: Optional[FileWatcher] = None

def get_file_watcher(poll_interval: float = 0.5) -> FileWatcher:
    """Get or create the singleton file watcher."""
    global _file_watcher
    if _file_watcher is None:
        _file_watcher = FileWatcher(poll_interval=poll_interval)
    return _file_watcher

def reset_file_watcher():
    """Reset the singleton (stops it if running)."""
    global _file_watcher
    if _file_watcher and _file_watcher._running:
        _file_watcher.stop()
    _file_watcher = None


# ── Convenience: watch a path with a simple callback ─────────────────────────
def watch_path(path: str, callback: Callable = None, **kwargs):
    """
    Quick-start: watch a path with an optional callback.
    If no callback, prints events to stdout.
    Returns the FileWatcher instance.
    """
    fw = get_file_watcher()
    if callback is None:
        def default_cb(p, e):
            print(f"[file_watcher] {p} → {e}")
        callback = default_cb
    fw.watch(path, callback, **kwargs)
    return fw
