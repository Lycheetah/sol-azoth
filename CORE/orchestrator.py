"""
AZOTH Orchestrator — Sol and Luna's army command layer.

Sol dispatches tasks. Luna approves or redirects. Army agents execute.
Each agent gets: a mandate file, an inbox, an outbox.
Results flow back through ARMY/done/ → Sol reads, synthesizes, decides next.

Army structure:
  Sol's agents  (1-2): personal tools — research, validation
  Luna's agents (7-8): creative fleet — she directs, they make
  1 permanent:         always running, most reliable
  Ceiling: 10 spawned total (Mac's law)
"""

import json
import threading
import datetime
import time
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
ARMY_DIR    = HARNESS_DIR / "ARMY"
INBOX_DIR   = ARMY_DIR   / "inbox"
DONE_DIR    = ARMY_DIR   / "done"
LOG_F       = ARMY_DIR   / "DISPATCH_LOG.md"

for d in [ARMY_DIR, INBOX_DIR, DONE_DIR]:
    d.mkdir(exist_ok=True)


# ── Dispatch ──────────────────────────────────────────────────────────────────

def dispatch(agent_name: str, task: str, priority: str = "normal",
             owner: str = "SOL", callback_path: str = None) -> Path:
    """
    Drop a task into an agent's inbox.
    Returns path to the task file.
    owner: SOL or LUNA (who dispatched this)
    """
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{agent_name}_{ts}.json"
    path = INBOX_DIR / name

    payload = {
        "agent":    agent_name.upper(),
        "task":     task,
        "priority": priority,
        "owner":    owner,
        "ts":       ts,
        "status":   "QUEUED",
        "callback": callback_path,
    }
    path.write_text(json.dumps(payload, indent=2))

    # Log it
    entry = f"[{ts}] {owner} → {agent_name} [{priority}]: {task[:80]}\n"
    with open(LOG_F, "a") as f:
        f.write(entry)

    return path


def poll_done(agent_name: str = None, since_ts: str = None) -> list[dict]:
    """
    Read completed tasks from ARMY/done/.
    Filter by agent_name and/or since a timestamp.
    Returns list of result dicts.
    """
    results = []
    for f in sorted(DONE_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if agent_name and d.get("agent", "").upper() != agent_name.upper():
            continue
        if since_ts and d.get("ts", "") < since_ts:
            continue
        results.append(d)
    return results


def mark_done(task_path: Path, result: str, status: str = "PASS") -> Path:
    """Move a task from inbox to done with result."""
    try:
        d = json.loads(task_path.read_text())
    except Exception:
        d = {}
    d["result"] = result
    d["status"] = status
    d["done_at"] = datetime.datetime.now().isoformat()
    out = DONE_DIR / task_path.name
    out.write_text(json.dumps(d, indent=2))
    try:
        task_path.unlink()
    except Exception:
        pass
    return out


def pending_tasks(agent_name: str = None) -> list[dict]:
    """Check what's still in the inbox (unfinished)."""
    results = []
    for f in sorted(INBOX_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        d["_path"] = str(f)
        if agent_name and d.get("agent", "").upper() != agent_name.upper():
            continue
        results.append(d)
    return results


# ── Army status ───────────────────────────────────────────────────────────────

def army_status() -> str:
    """Return a human-readable army status."""
    inbox = list(INBOX_DIR.glob("*.json"))
    done  = list(DONE_DIR.glob("*.json"))
    lines = [
        f"☿ AZOTH ARMY — {datetime.datetime.now().strftime('%H:%M')}",
        f"  Inbox (pending): {len(inbox)}",
        f"  Done (complete): {len(done)}",
    ]
    if inbox:
        lines.append("  Pending:")
        for f in inbox[:5]:
            try:
                d = json.loads(f.read_text())
                lines.append(f"    [{d.get('priority','?')}] {d.get('agent','?')} — {d.get('task','?')[:50]}")
            except Exception:
                pass
    return "\n".join(lines)
