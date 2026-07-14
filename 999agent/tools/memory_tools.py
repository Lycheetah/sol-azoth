"""Memory and persistence tools for 999agent — session replay, task tree, export.

Registers:
  - session_replay(session_id)  — replay a past session log
  - task_tree()                 — show the current task tree
  - export_memory()             — export all memory as markdown
  - session_list()              — list all past sessions
"""

import json
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent.parent.resolve()
MEMORY_DIR = HERE / "memory"
SESSIONS_DIR = MEMORY_DIR / "sessions"
REFLECTIONS_DIR = MEMORY_DIR / "reflections"


def session_replay_impl(session_id: str) -> str:
    """Replay a past session log by ID."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        # Try with .txt extension
        session_file = SESSIONS_DIR / f"{session_id}.txt"
    if not session_file.exists():
        # Search for partial match
        matches = list(SESSIONS_DIR.glob(f"{session_id}*"))
        if not matches:
            return f"ERROR: no session found matching '{session_id}'"
        session_file = matches[0]
    
    try:
        if session_file.suffix == ".json":
            data = json.loads(session_file.read_text())
            lines = [f"Session: {data.get('session_id', session_id)}"]
            if "start" in data:
                lines.append(f"Started: {data['start']}")
            if "turn_count" in data:
                lines.append(f"Turns: {data['turn_count']}")
            lines.append("")
            for entry in data.get("log", []):
                lines.append(f"  {entry[:200]}")
            return "\n".join(lines)
        else:
            text = session_file.read_text()
            if len(text) > 8000:
                text = text[:8000] + "\n... (truncated)"
            return text
    except Exception as e:
        return f"ERROR reading session: {e}"


def session_list_impl() -> str:
    """List all past sessions."""
    if not SESSIONS_DIR.exists():
        return "No sessions directory."
    
    sessions = sorted(SESSIONS_DIR.glob("*"))
    if not sessions:
        return "No past sessions found."
    
    lines = ["Past sessions:"]
    for s in sessions:
        size = s.stat().st_size
        mtime = datetime.fromtimestamp(s.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(f"  • {s.stem}  ({size}b, {mtime})")
    
    return "\n".join(lines)


def task_tree_impl() -> str:
    """Show the current task tree."""
    task_file = HERE / "TASK_TREE.md"
    if not task_file.exists():
        return "No task tree. Create tasks with task_create()."
    content = task_file.read_text()
    if len(content) > 4000:
        content = content[:4000] + "\n... (truncated)"
    return content


def export_memory_impl() -> str:
    """Export all memory as markdown."""
    export_path = HERE / f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    parts = ["# 999agent Memory Export\n"]
    
    # Reflections
    if REFLECTIONS_DIR.exists():
        parts.append("## Reflections\n")
        for f in sorted(REFLECTIONS_DIR.glob("*.md")):
            parts.append(f.read_text())
            parts.append("\n---\n")
    
    # Scratchpad
    scratch = HERE / "workspace" / "scratch.md"
    if scratch.exists():
        parts.append("## Scratchpad\n\n")
        parts.append(scratch.read_text())
        parts.append("\n---\n")
    
    # Session count
    if SESSIONS_DIR.exists():
        count = len(list(SESSIONS_DIR.glob("*")))
        parts.append(f"\n## Sessions\n\n{count} session(s) available.\n")
    
    content = "\n".join(parts)
    export_path.write_text(content)
    return f"✓ Exported to {export_path.relative_to(HERE)} ({len(content)} bytes)"


def register() -> dict:
    """Register memory tools."""
    return {
        "session_replay": {
            "fn": session_replay_impl,
            "description": "Replay a past session log by session ID",
            "category": "memory",
        },
        "session_list": {
            "fn": session_list_impl,
            "description": "List all past sessions",
            "category": "memory",
        },
        "task_tree": {
            "fn": task_tree_impl,
            "description": "Show the current task tree",
            "category": "memory",
        },
        "export_memory": {
            "fn": export_memory_impl,
            "description": "Export all memory (reflections, scratchpad) as markdown",
            "category": "memory",
        },
    }
