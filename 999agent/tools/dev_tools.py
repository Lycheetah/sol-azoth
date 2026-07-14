"""Development tools for 999agent — compile check, git, diff, survey.

Registers:
  - py_compile_check(path)  — verify Python syntax
  - git_status()            — show git status and recent log
  - git_commit(message)     — stage all and commit
  - self_diff()             — show what changed in agent.py
  - survey(path, max_files) — outline a directory
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent.resolve()


def py_compile_check_impl(path: str) -> str:
    """Verify Python syntax of a file."""
    target = HERE / path if not os.path.isabs(path) else Path(path)
    if not target.exists():
        return f"ERROR: file not found: {path}"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(target)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return f"✓ Syntax OK: {path}"
        else:
            return f"✗ Syntax error in {path}:\n{result.stderr.strip()}"
    except Exception as e:
        return f"ERROR: py_compile failed: {e}"


def git_status_impl() -> str:
    """Show git status and recent log."""
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, cwd=HERE
        )
        if result.returncode != 0:
            return "Not a git repository (or git not available)."
        
        repo_root = result.stdout.strip()
        
        # Status
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5, cwd=HERE
        )
        
        # Recent log
        log = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            capture_output=True, text=True, timeout=5, cwd=HERE
        )
        
        parts = [f"Repository: {repo_root}"]
        if status.stdout.strip():
            parts.append(f"\nChanges:\n{status.stdout.rstrip()}")
        else:
            parts.append("\nNo changes (clean).")
        parts.append(f"\nRecent commits:\n{log.stdout.rstrip()}")
        
        return "\n".join(parts)
    except Exception as e:
        return f"ERROR: git_status failed: {e}"


def git_commit_impl(message: str) -> str:
    """Stage all changes and commit."""
    try:
        # Check git repo
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, cwd=HERE
        )
        if result.returncode != 0:
            return "Not a git repository."
        
        # Stage all
        add = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, timeout=10, cwd=HERE
        )
        if add.returncode != 0:
            return f"ERROR: git add failed: {add.stderr.strip()}"
        
        # Check if anything to commit
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5, cwd=HERE
        )
        if not status.stdout.strip():
            return "Nothing to commit (clean tree)."
        
        # Commit
        commit = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, text=True, timeout=10, cwd=HERE
        )
        if commit.returncode == 0:
            return f"✓ Committed: {commit.stdout.strip()}"
        else:
            return f"✗ Commit failed: {commit.stderr.strip()}"
    except Exception as e:
        return f"ERROR: git_commit failed: {e}"


def self_diff_impl() -> str:
    """Show what changed in agent.py since last startup snapshot."""
    snapshot = HERE / "memory" / "agent_snapshot.py"
    agent_py = HERE / "agent.py"
    
    if not snapshot.exists():
        # Create initial snapshot
        if agent_py.exists():
            snapshot.write_text(agent_py.read_text())
            return "No previous snapshot. Created baseline snapshot of agent.py."
        return "ERROR: agent.py not found."
    
    if not agent_py.exists():
        return "ERROR: agent.py not found."
    
    current = agent_py.read_text()
    prev = snapshot.read_text()
    
    if current == prev:
        return "No changes to agent.py since last snapshot."
    
    # Simple line-based diff
    cur_lines = current.split("\n")
    prev_lines = prev.split("\n")
    
    import difflib
    diff = difflib.unified_diff(
        prev_lines, cur_lines,
        fromfile="agent.py (snapshot)",
        tofile="agent.py (current)",
        lineterm=""
    )
    
    diff_lines = list(diff)
    if len(diff_lines) > 80:
        diff_lines = diff_lines[:80] + ["... (truncated)"]
    
    return "\n".join(diff_lines)


def survey_impl(path: str = ".", max_files: int = 50) -> str:
    """Outline a directory: show tree and one-line purpose per file."""
    base = HERE / path if path != "." else HERE
    if not base.exists() or not base.is_dir():
        # Try as a file
        if base.exists() and base.is_file():
            return f"File: {base.relative_to(HERE)}\nSize: {base.stat().st_size} bytes"
        return f"ERROR: path not found: {path}"
    
    lines = []
    lines.append(f"Survey of {base.relative_to(HERE) if base != HERE else '.'}/")
    lines.append("")
    
    count = 0
    for f in sorted(base.rglob("*")):
        if count >= max_files:
            lines.append(f"... ({max_files} files shown)")
            break
        if f.is_dir():
            continue
        
        rel = f.relative_to(HERE)
        size = f.stat().st_size
        
        # Get first line or heading
        try:
            content = f.read_text(errors="replace")[:200]
            first_line = content.split("\n")[0].strip()
            if first_line.startswith("#"):
                purpose = first_line
            elif first_line.startswith("#!/"):
                purpose = first_line
            elif content.strip():
                purpose = content[:80].strip().replace("\n", " ")
            else:
                purpose = "(empty)"
        except:
            purpose = "(binary or unreadable)"
        
        lines.append(f"  {rel}  ({size}b)  — {purpose}")
        count += 1
    
    return "\n".join(lines)


def dreams_impl(n: int = 5) -> str:
    """Show recent dreams from the Dream Engine."""
    try:
        import sys
        azoth_home = HERE.parent  # tools/ → 999agent/ → AZOTH/
        sys.path.insert(0, str(azoth_home))
        from CORE.dream_loop import get_recent_dreams
        dreams = get_recent_dreams(n)
        if not dreams:
            return "[dreams] No dreams recorded yet."
        lines = [f"[dreams] {len(dreams)} recent dreams:"]
        for d in dreams:
            lines.append(f"  [{d['type']}] {d['insight'][:120]}")
        return "\n".join(lines)
    except Exception as e:
        return f"[dreams] Error: {e}"

def register() -> dict:
    """Register dev tools."""
    return {
        "dreams": {
            "fn": dreams_impl,
            "description": "Show recent dreams from the Dream Engine",
            "category": "dev",
        },
        "py_compile_check": {
            "fn": py_compile_check_impl,
            "description": "Verify Python syntax of a file",
            "category": "dev",
        },
        "git_status": {
            "fn": git_status_impl,
            "description": "Show git status and recent log",
            "category": "dev",
        },
        "git_commit": {
            "fn": git_commit_impl,
            "description": "Stage all changes and commit",
            "category": "dev",
        },
        "self_diff": {
            "fn": self_diff_impl,
            "description": "Show what changed in agent.py since last snapshot",
            "category": "dev",
        },
        "survey": {
            "fn": survey_impl,
            "description": "Outline a directory with file sizes and first-line summaries",
            "category": "dev",
        },
    }
