"""
S2: TASK BRAIN — one SQLite ledger for every execution entity.

Before this, AZOTH's execution state lived in five places that could not see
each other: task_tree.json, FORGE_QUEUE.md, cron_jobs.txt, heartbeat_log.md,
and the swarm's stdout. The brain is the one ledger they all write to.

Ownership boundaries (deliberate):
- FORGE_QUEUE.md stays authoritative for WHAT'S NEXT — it is Mac's hand-edited
  surface and the brain never rewrites it. The brain records what RAN.
- cron_jobs.txt stays the cron source of truth (same reason). Fires are recorded.
- task_tree.json is SUPERSEDED: tasks live here now. agent.py's task helpers
  route through record_task/update_task; existing trees migrate on first open.

Schema — one table, `entries`:
  id INTEGER PK · kind TEXT (task|forge|cron|heartbeat|swarm) · subject TEXT ·
  status TEXT (pending|running|done|fail|ok|alert) · detail TEXT ·
  parent INTEGER · created TEXT · updated TEXT
"""

import datetime
import json
import sqlite3
import threading
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
WORKSPACE   = HARNESS_DIR / "workspace"
DB_FILE     = WORKSPACE / "taskbrain.db"
LEGACY_TREE = HARNESS_DIR / "task_tree.json"

_lock = threading.Lock()


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _conn() -> sqlite3.Connection:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_FILE, timeout=10)
    c.execute("""CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,
        subject TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        detail TEXT DEFAULT '',
        parent INTEGER,
        created TEXT NOT NULL,
        updated TEXT NOT NULL)""")
    _migrate_legacy(c)
    return c


def _migrate_legacy(c: sqlite3.Connection) -> None:
    """task_tree.json folds in exactly once, then is renamed .superseded (§XXV)."""
    if not LEGACY_TREE.exists():
        return
    try:
        tree = json.loads(LEGACY_TREE.read_text())
        idmap = {}
        for tid, node in tree.get("nodes", {}).items():
            status = {"pending": "pending", "in_progress": "running",
                      "done": "done", "completed": "done"}.get(node.get("status", "pending"), node.get("status", "pending"))
            cur = c.execute(
                "INSERT INTO entries (kind, subject, status, detail, created, updated) VALUES (?,?,?,?,?,?)",
                ("task", node.get("goal", "?"), status, node.get("result") or "",
                 node.get("created", _now()), _now()))
            idmap[tid] = cur.lastrowid
        for tid, node in tree.get("nodes", {}).items():
            p = node.get("parent")
            if p in idmap:
                c.execute("UPDATE entries SET parent=? WHERE id=?", (idmap[p], idmap[tid]))
        c.commit()
    except Exception:
        pass  # a corrupt legacy tree must not block the brain
    LEGACY_TREE.rename(LEGACY_TREE.with_suffix(".json.superseded"))


# ── writers ──────────────────────────────────────────────────────────────────

def record(kind: str, subject: str, status: str = "pending",
           detail: str = "", parent: int = None) -> int:
    with _lock, _conn() as c:
        cur = c.execute(
            "INSERT INTO entries (kind, subject, status, detail, parent, created, updated) VALUES (?,?,?,?,?,?,?)",
            (kind, subject[:500], status, detail[:2000], parent, _now(), _now()))
        return cur.lastrowid


def update(entry_id: int, status: str = None, detail: str = None) -> bool:
    with _lock, _conn() as c:
        sets, vals = ["updated=?"], [_now()]
        if status is not None:
            sets.append("status=?"); vals.append(status)
        if detail is not None:
            sets.append("detail=?"); vals.append(detail[:2000])
        vals.append(entry_id)
        cur = c.execute(f"UPDATE entries SET {', '.join(sets)} WHERE id=?", vals)
        return cur.rowcount > 0


# ── readers ──────────────────────────────────────────────────────────────────

def rows(kind: str = None, status: str = None, limit: int = 50) -> list[dict]:
    q, vals = "SELECT * FROM entries", []
    conds = []
    if kind:
        conds.append("kind=?"); vals.append(kind)
    if status:
        conds.append("status=?"); vals.append(status)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY id DESC LIMIT ?"
    vals.append(limit)
    with _lock, _conn() as c:
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute(q, vals).fetchall()]


def summary() -> str:
    """One block for /status and /board — the whole execution surface at a glance."""
    with _lock, _conn() as c:
        counts = {f"{k}/{s}": n for k, s, n in
                  c.execute("SELECT kind, status, COUNT(*) FROM entries GROUP BY kind, status")}
        last = {k: (sub, st, up) for k, sub, st, up in
                c.execute("""SELECT kind, subject, status, updated FROM entries
                             WHERE id IN (SELECT MAX(id) FROM entries GROUP BY kind)""")}
    open_tasks = counts.get("task/pending", 0) + counts.get("task/running", 0)
    lines = [f"TASK BRAIN — {open_tasks} open task(s)"]
    for kind in ("task", "forge", "swarm", "cron", "heartbeat"):
        if kind in last:
            sub, st, up = last[kind]
            lines.append(f"  {kind:<9} last: [{st}] {sub[:60]}  ({up[:16]})")
    return "\n".join(lines)
