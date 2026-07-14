#!/usr/bin/env python3
"""
VAEL-SP Memory Engine — SQLite-backed persistent memory store.
Phase 1, Task 1 of the Architecture Forge.

Tables:
  - episodes:   timestamped records of actions taken and results
  - learnings:  conclusions drawn, lessons learned, patterns observed
  - capabilities: what VAEL can do, with verification status
  - tasks:      task queue with status, priority, dependencies

Usage:
  from memory_engine import MemoryEngine
  mem = MemoryEngine()
  mem.store_episode("read file X", "found 42 lines")
  results = mem.recall("file X")
"""

import sqlite3
import json
import hashlib
import datetime
import os
import pathlib

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.db")


class MemoryEngine:
    """Persistent memory store for VAEL-SP using SQLite."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._ensure_db_dir()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._migrate_if_needed()

    def _ensure_db_dir(self):
        pathlib.Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)

    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                action TEXT NOT NULL,
                context TEXT,
                result TEXT,
                tags TEXT DEFAULT '[]',
                session_id TEXT,
                success INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                topic TEXT NOT NULL,
                insight TEXT NOT NULL,
                evidence TEXT,
                confidence REAL DEFAULT 0.5,
                source_episode_id INTEGER,
                verified INTEGER DEFAULT 0,
                FOREIGN KEY (source_episode_id) REFERENCES episodes(id)
            );

            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                level INTEGER DEFAULT 0,
                description TEXT,
                verified INTEGER DEFAULT 0,
                verified_at TEXT,
                test_script TEXT,
                depends_on TEXT DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                name TEXT NOT NULL,
                phase TEXT,
                status TEXT DEFAULT 'QUEUED',
                priority INTEGER DEFAULT 0,
                description TEXT,
                output_path TEXT,
                error_log TEXT,
                depends_on TEXT DEFAULT '[]'
            );

            CREATE INDEX IF NOT EXISTS idx_episodes_timestamp ON episodes(timestamp);
            CREATE INDEX IF NOT EXISTS idx_episodes_tags ON episodes(tags);
            CREATE INDEX IF NOT EXISTS idx_learnings_topic ON learnings(topic);
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        """)
        self.conn.commit()

    def _migrate_if_needed(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        current_version = row[0] if row[0] else 0

        if current_version < 1:
            cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
            self.conn.commit()

    # ─── EPISODES ────────────────────────────────────────────────

    def store_episode(self, action, context=None, result=None, tags=None, session_id=None, success=True):
        """Record an action and its result."""
        cursor = self.conn.cursor()
        # Serialize dict/list types to JSON strings for SQLite
        ctx = json.dumps(context) if isinstance(context, (dict, list)) else context
        res = json.dumps(result) if isinstance(result, (dict, list)) else result
        cursor.execute(
            """INSERT INTO episodes (action, context, result, tags, session_id, success)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (action, ctx, res, json.dumps(tags or []), session_id, int(success))
        )
        self.conn.commit()
        return cursor.lastrowid

    def recall(self, query, limit=10, tags=None):
        """Search episodes by text match in action, context, or result."""
        cursor = self.conn.cursor()
        like = f"%{query}%"
        if tags:
            cursor.execute(
                """SELECT * FROM episodes
                   WHERE (action LIKE ? OR context LIKE ? OR result LIKE ?)
                   AND tags LIKE ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (like, like, like, f"%{tags}%", limit)
            )
        else:
            cursor.execute(
                """SELECT * FROM episodes
                   WHERE action LIKE ? OR context LIKE ? OR result LIKE ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (like, like, like, limit)
            )
        return [dict(row) for row in cursor.fetchall()]

    def recent_episodes(self, limit=10):
        """Get most recent episodes."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # ─── LEARNINGS ───────────────────────────────────────────────

    def learn(self, topic, insight, evidence=None, confidence=0.5, source_episode_id=None):
        """Store a learning/conclusion."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO learnings (topic, insight, evidence, confidence, source_episode_id)
               VALUES (?, ?, ?, ?, ?)""",
            (topic, insight, evidence, confidence, source_episode_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def recall_learnings(self, topic=None, min_confidence=0.0, limit=10):
        """Retrieve learnings, optionally filtered by topic."""
        cursor = self.conn.cursor()
        if topic:
            cursor.execute(
                """SELECT * FROM learnings
                   WHERE topic LIKE ? AND confidence >= ?
                   ORDER BY confidence DESC, timestamp DESC LIMIT ?""",
                (f"%{topic}%", min_confidence, limit)
            )
        else:
            cursor.execute(
                """SELECT * FROM learnings
                   WHERE confidence >= ?
                   ORDER BY confidence DESC, timestamp DESC LIMIT ?""",
                (min_confidence, limit)
            )
        return [dict(row) for row in cursor.fetchall()]

    # ─── CAPABILITIES ────────────────────────────────────────────

    def register_capability(self, name, level, description, test_script=None, depends_on=None):
        """Register a new capability."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO capabilities (name, level, description, test_script, depends_on)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, level, description, test_script, json.dumps(depends_on or []))
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # already exists

    def verify_capability(self, name):
        """Mark a capability as verified."""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE capabilities
               SET verified = 1, verified_at = datetime('now')
               WHERE name = ?""",
            (name,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def list_capabilities(self, verified_only=False):
        """List all capabilities."""
        cursor = self.conn.cursor()
        if verified_only:
            cursor.execute("SELECT * FROM capabilities WHERE verified = 1 ORDER BY level, name")
        else:
            cursor.execute("SELECT * FROM capabilities ORDER BY level, name")
        return [dict(row) for row in cursor.fetchall()]

    # ─── TASKS ───────────────────────────────────────────────────

    def add_task(self, name, phase=None, priority=0, description="", depends_on=None):
        """Add a task to the queue."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO tasks (name, phase, priority, description, depends_on)
               VALUES (?, ?, ?, ?, ?)""",
            (name, phase, priority, description, json.dumps(depends_on or []))
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_task_status(self, task_id, status, output_path=None, error_log=None):
        """Update a task's status."""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE tasks
               SET status = ?, updated_at = datetime('now'),
                   output_path = COALESCE(?, output_path),
                   error_log = COALESCE(?, error_log)
               WHERE id = ?""",
            (status, output_path, error_log, task_id)
        )
        self.conn.commit()

    def next_task(self):
        """Get the highest-priority QUEUED task whose dependencies are met."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT * FROM tasks
               WHERE status = 'QUEUED'
               ORDER BY priority DESC, created_at ASC
               LIMIT 1"""
        )
        row = cursor.fetchone()
        if row is None:
            return None
        task = dict(row)
        # Check dependencies
        deps = json.loads(task.get("depends_on", "[]"))
        if deps:
            placeholders = ",".join("?" for _ in deps)
            cursor.execute(
                f"SELECT status FROM tasks WHERE name IN ({placeholders})",
                deps
            )
            dep_statuses = [r[0] for r in cursor.fetchall()]
            if any(s != "PASS" for s in dep_statuses):
                return None  # dependencies not met
        return task

    def list_tasks(self, status=None):
        """List tasks, optionally filtered by status."""
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at", (status,))
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at")
        return [dict(row) for row in cursor.fetchall()]

    # ─── UTILITY ─────────────────────────────────────────────────

    def get_stats(self):
        """Get memory store statistics."""
        cursor = self.conn.cursor()
        stats = {}
        for table in ["episodes", "learnings", "capabilities", "tasks"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM episodes WHERE success = 1")
        stats["successful_episodes"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM capabilities WHERE verified = 1")
        stats["verified_capabilities"] = cursor.fetchone()[0]
        return stats

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ─── SELF-TEST ───────────────────────────────────────────────────

def self_test():
    """Run the memory engine through its paces. Called on /forge verification."""
    import tempfile
    import os

    test_db = os.path.join(tempfile.gettempdir(), "vael_memory_test.db")
    if os.path.exists(test_db):
        os.remove(test_db)

    mem = MemoryEngine(test_db)
    results = []

    # Test 1: Store and recall an episode
    ep_id = mem.store_episode(
        action="read_file /test/path",
        context="testing memory engine",
        result="found 42 lines of code",
        tags=["test", "read"],
        session_id="test-session-1"
    )
    assert ep_id is not None, "store_episode returned None"
    results.append(("PASS", "store_episode returns valid id"))

    # Test 2: Recall by query
    recalled = mem.recall("test/path")
    assert len(recalled) >= 1, f"recall returned {len(recalled)} results"
    assert recalled[0]["action"] == "read_file /test/path"
    results.append(("PASS", "recall finds stored episode"))

    # Test 3: Store and recall a learning
    learn_id = mem.learn(
        topic="memory engine",
        insight="SQLite works well for persistent structured memory",
        evidence="self-test passed all assertions",
        confidence=0.9,
        source_episode_id=ep_id
    )
    assert learn_id is not None
    learnings = mem.recall_learnings(topic="memory")
    assert len(learnings) >= 1
    results.append(("PASS", "learn/recall_learnings works"))

    # Test 4: Register and verify a capability
    registered = mem.register_capability(
        name="memory_engine",
        level=1,
        description="SQLite-backed persistent memory store",
        test_script="CORE/memory_engine.py::self_test"
    )
    assert registered, "register_capability failed"
    verified = mem.verify_capability("memory_engine")
    assert verified, "verify_capability failed"
    caps = mem.list_capabilities(verified_only=True)
    assert len(caps) >= 1
    results.append(("PASS", "capability registration and verification works"))

    # Test 5: Task queue operations
    task_id = mem.add_task(
        name="test_task",
        phase="TEST",
        priority=10,
        description="A test task"
    )
    assert task_id is not None
    mem.update_task_status(task_id, "PASS", output_path="/dev/null")
    tasks = mem.list_tasks(status="PASS")
    assert len(tasks) >= 1
    results.append(("PASS", "task queue operations work"))

    # Test 6: Stats
    stats = mem.get_stats()
    assert stats["episodes"] >= 1
    assert stats["learnings"] >= 1
    assert stats["capabilities"] >= 1
    assert stats["tasks"] >= 1
    results.append(("PASS", "get_stats returns coherent counts"))

    mem.close()
    os.remove(test_db)

    print("=== MEMORY ENGINE SELF-TEST RESULTS ===")
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
        mem = MemoryEngine()
        print(f"Memory Engine initialized at: {mem.db_path}")
        print(f"Stats: {mem.get_stats()}")
