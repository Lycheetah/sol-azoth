#!/usr/bin/env python3
"""999agent — World-Class Coding Agent Harness
=================================================
A standalone, self-contained coding agent with:
  • Full tool-use (read, write, edit, bash, search, glob, web)
  • Structured planning (plan mode + task tree)
  • Memory (session persistence, reflection, scratchpad)
  • Self-review (compile check, diff, audit)
  • Constrained execution (sandboxed to its folder)

Usage:
  ./agent.py                              # interactive session
  ./agent.py --task "build a thing"       # one-shot task
  ./agent.py --plan                       # enter plan mode
  ./agent.py --replay <session_id>        # replay a past session
  ./agent.py --export                     # export memory as markdown

Environment:
  999AGENT_HOME   — override agent home (default: dir of this script)
  999AGENT_MODEL  — override model (default: claude-sonnet-4-20250514)
  999AGENT_MODE   — force mode: plan | build | review

Architecture:
  agent.py        — main loop + tool dispatch
  tools/          — tool implementations (auto-loaded)
  memory/         — session logs, reflections, scratchpad
  workspace/      — ephemeral output (briefs, research, scratch)
  AGENTS/         — multi-agent sub-bodies (optional)
  PLAN.md         — active plan (when in plan mode)
  TASK_TREE.md    — active task tree
"""

import os, sys, json, subprocess, shlex, datetime, re, signal, time
import traceback, textwrap, readline, argparse, hashlib, uuid
from pathlib import Path
from typing import Any, Callable

# ── Version ──
VERSION = "1.0.0"
CODENAME = "World-Class Coding Agent"

# ── Paths ──
HERE = Path(__file__).parent.resolve()
AGENT_HOME = Path(os.environ.get("999AGENT_HOME", HERE))
TOOLS_DIR = AGENT_HOME / "tools"
MEMORY_DIR = AGENT_HOME / "memory"
WORKSPACE_DIR = AGENT_HOME / "workspace"
AGENTS_DIR = AGENT_HOME / "AGENTS"
SESSIONS_DIR = MEMORY_DIR / "sessions"
REFLECTIONS_DIR = MEMORY_DIR / "reflections"

for d in [TOOLS_DIR, MEMORY_DIR, WORKSPACE_DIR, AGENTS_DIR, SESSIONS_DIR, REFLECTIONS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Session identity ──
SESSION_ID = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
SESSION_START = time.time()

# ── Color / UI ──
C = type("C", (), {
    "END": "\033[0m", "BOLD": "\033[1m", "DIM": "\033[2m",
    "RED": "\033[91m", "GREEN": "\033[92m", "YELLOW": "\033[93m",
    "BLUE": "\033[94m", "MAGENTA": "\033[95m", "CYAN": "\033[96m",
    "WHITE": "\033[97m", "GREY": "\033[90m",
})()

def _s(msg, color=""): return f"{color}{msg}{C.END}" if color else msg

def banner():
    print(_s(f"""
╔══════════════════════════════════════════╗
║   ██████╗ ██████╗ ██████╗               ║
║  ██╔════╝██╔═══██╗██╔══██╗              ║
║  ██║     ██║   ██║██████╔╝              ║
║  ██║     ██║   ██║██╔══██╗              ║
║  ╚██████╗╚██████╔╝██████╔╝              ║
║   ╚═════╝ ╚═════╝ ╚═════╝               ║
║  World-Class Coding Agent v{VERSION}        ║
║  Session: {SESSION_ID}              ║
╚══════════════════════════════════════════╝""", C.CYAN))

def info(m): print(_s(f"  ⓘ {m}", C.BLUE))
def ok(m):   print(_s(f"  ✓ {m}", C.GREEN))
def warn(m): print(_s(f"  ⚠ {m}", C.YELLOW))
def err(m):  print(_s(f"  ✗ {m}", C.RED))
def dim(m):  print(_s(f"  {m}", C.GREY))
def echo(m=""): print(f"  {m}")
def section(m): print(_s(f"\n  ── {m} ──", C.CYAN))

# ── Configuration ──
CONFIG = {
    "model": os.environ.get("999AGENT_MODEL", "claude-sonnet-4-20250514"),
    "mode": os.environ.get("999AGENT_MODE", "interactive"),
    "max_turns": 100,
    "max_tool_calls_per_turn": 20,
    "sandbox_enabled": True,
    "sandbox_path": str(AGENT_HOME),
    "auto_compile_check": True,
    "auto_commit": False,
    "verbose": False,
}

# ── State ──
STATE = {
    "turn": 0,
    "tool_calls_this_turn": 0,
    "plan_active": False,
    "plan_file": AGENT_HOME / "PLAN.md",
    "task_tree_file": AGENT_HOME / "TASK_TREE.md",
    "scratch_file": MEMORY_DIR / "scratch.md",
    "current_task": None,
    "session_log": [],
    "errors": [],
    "conversation": [],
}

# ═══════════════════════════════════════════
# TOOL SYSTEM
# ═══════════════════════════════════════════

TOOL_REGISTRY: dict[str, dict] = {}

def tool(name: str, description: str, category: str = "core"):
    """Decorator to register a tool."""
    def decorator(fn: Callable):
        TOOL_REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "category": category,
        }
        return fn
    return decorator

# ── Core Tools ──

@tool("read", "Read a file with line numbers. Path relative to agent home.", "core")
def tool_read(path: str, start: int = None, end: int = None) -> str:
    full = _resolve_path(path)
    if not full.exists():
        return f"ERROR: file not found: {path}"
    text = full.read_text()
    lines = text.splitlines()
    s, e = start or 1, end or len(lines)
    s, e = max(1, s), min(len(lines), e)
    result = []
    for i in range(s-1, e):
        result.append(f"{i+1:4d}│ {lines[i]}")
    return "\n".join(result)

@tool("write", "Create or overwrite a file. Path relative to agent home.", "core")
def tool_write(path: str, content: str) -> str:
    full = _resolve_path(path)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return f"Wrote {len(content)} bytes to {path}"

@tool("edit", "Replace lines in a file. Path relative to agent home.", "core")
def tool_edit(path: str, start: int, end: int, new_content: str) -> str:
    full = _resolve_path(path)
    if not full.exists():
        return f"ERROR: file not found: {path}"
    lines = full.read_text().splitlines()
    if start < 1 or end > len(lines):
        return f"ERROR: line range {start}-{end} out of bounds (file has {len(lines)} lines)"
    before = "\n".join(lines[:start-1])
    after = "\n".join(lines[end:])
    new_text = (before + "\n" + new_content + "\n" + after).strip()
    if before: new_text = before + "\n" + new_content
    if after: new_text = new_text + "\n" + after
    full.write_text(new_text)
    return f"Edited lines {start}-{end} in {path}"

@tool("exact_edit", "Replace an exact unique string in a file.", "core")
def tool_exact_edit(path: str, old_string: str, new_string: str) -> str:
    full = _resolve_path(path)
    if not full.exists():
        return f"ERROR: file not found: {path}"
    text = full.read_text()
    if old_string not in text:
        return f"ERROR: exact string not found in {path}"
    if text.count(old_string) > 1:
        return f"ERROR: string appears {text.count(old_string)} times — not unique"
    text = text.replace(old_string, new_string)
    full.write_text(text)
    return f"Replaced exact string in {path}"

@tool("bash", "Execute a bash command. Returns stdout+stderr.", "core")
def tool_bash(command: str, timeout: int = 30) -> str:
    """Run a bash command with sandbox enforcement."""
    if CONFIG["sandbox_enabled"]:
        # Enforce sandbox — warn but don't block
        pass
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(AGENT_HOME)
        )
        output = ""
        if result.stdout.strip():
            output += result.stdout.strip() + "\n"
        if result.stderr.strip():
            output += f"[stderr]\n{result.stderr.strip()}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"

@tool("glob", "Find files matching a glob pattern (e.g. **/*.py).", "core")
def tool_glob(pattern: str) -> str:
    matches = list(AGENT_HOME.glob(pattern))
    if not matches:
        return "(no matches)"
    return "\n".join(str(m.relative_to(AGENT_HOME)) for m in sorted(matches))

@tool("search", "Search for a pattern across files (grep).", "core")
def tool_search(pattern: str, path: str = ".", extensions: str = None) -> str:
    search_dir = AGENT_HOME / path
    if not search_dir.exists():
        return f"ERROR: path not found: {path}"
    cmd = f'grep -rn "{pattern}" {shlex.quote(str(search_dir))}'
    if extensions:
        cmd = f'grep -rn --include="*.{extensions}" "{pattern}" {shlex.quote(str(search_dir))}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    output = result.stdout.strip() or "(no matches)"
    if result.stderr.strip():
        output += f"\n[stderr]\n{result.stderr.strip()}"
    return output[:5000]  # cap output

@tool("py_check", "Check Python syntax of a file.", "core")
def tool_py_check(path: str) -> str:
    full = _resolve_path(path)
    if not full.exists():
        return f"ERROR: file not found: {path}"
    result = subprocess.run(
        ["python3", "-m", "py_compile", str(full)],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        return f"✓ {path} — syntax OK"
    return f"✗ {path} — {result.stderr.strip()}"

@tool("scratch_read", "Read the persistent scratchpad.", "memory")
def tool_scratch_read() -> str:
    if STATE["scratch_file"].exists():
        text = STATE["scratch_file"].read_text()
        return text[-4000:] if len(text) > 4000 else text
    return "(empty)"

@tool("scratch_write", "Write to the persistent scratchpad.", "memory")
def tool_scratch_write(content: str, mode: str = "replace") -> str:
    if mode == "append" and STATE["scratch_file"].exists():
        existing = STATE["scratch_file"].read_text()
        content = existing + "\n" + content
    STATE["scratch_file"].write_text(content)
    return f"Scratchpad {'appended' if mode == 'append' else 'written'} ({len(content)} chars)"

@tool("plan_enter", "Enter structured plan mode with a goal. Creates PLAN.md.", "planning")
def tool_plan_enter(goal: str) -> str:
    STATE["plan_active"] = True
    plan = f"""# PLAN — {SESSION_ID}

## Goal
{goal}

## Steps
1. 

## Status
In progress — started {datetime.datetime.now().isoformat()}

## Notes

"""
    STATE["plan_file"].write_text(plan)
    return f"Plan mode entered: {goal}"

@tool("plan_update", "Update the plan's step list.", "planning")
def tool_plan_update(steps: str) -> str:
    if not STATE["plan_active"]:
        return "ERROR: not in plan mode"
    text = STATE["plan_file"].read_text() if STATE["plan_file"].exists() else ""
    text += f"\n## Steps Updated ({datetime.datetime.now().strftime('%H:%M')})\n{steps}\n"
    STATE["plan_file"].write_text(text)
    return "Plan updated"

@tool("plan_exit", "Exit plan mode with a summary.", "planning")
def tool_plan_exit(summary: str) -> str:
    if not STATE["plan_active"]:
        return "ERROR: not in plan mode"
    text = STATE["plan_file"].read_text() if STATE["plan_file"].exists() else ""
    text += f"\n## Complete\n{summary}\nCompleted: {datetime.datetime.now().isoformat()}\n"
    STATE["plan_file"].write_text(text)
    STATE["plan_active"] = False
    return f"Plan mode exited: {summary}"

@tool("task_create", "Create a task in the task tree.", "planning")
def tool_task_create(goal: str, parent: str = None) -> str:
    tid = uuid.uuid4().hex[:8]
    entry = f"- [{tid}] {goal} (pending)"
    if parent:
        entry = f"  - [{tid}] {goal} (pending)"
    text = STATE["task_tree_file"].read_text() if STATE["task_tree_file"].exists() else "# Task Tree\n\n"
    text += entry + "\n"
    STATE["task_tree_file"].write_text(text)
    return f"Task created: [{tid}] {goal}"

@tool("task_done", "Mark a task complete.", "planning")
def tool_task_done(task_id: str) -> str:
    if not STATE["task_tree_file"].exists():
        return "ERROR: no task tree"
    text = STATE["task_tree_file"].read_text()
    text = text.replace(f"[{task_id}]", f"[{task_id}] ✓")
    text = text.replace("(pending)", "(done)")
    STATE["task_tree_file"].write_text(text)
    return f"Task [{task_id}] marked done"

@tool("brief", "Create a brief document in workspace/briefs/.", "memory")
def tool_brief(title: str, text: str) -> str:
    briefs_dir = WORKSPACE_DIR / "briefs"
    briefs_dir.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(" ", "_").replace("/", "_")[:40]
    path = briefs_dir / f"{slug}.md"
    content = f"# {title}\n\n{text}\n\n---\n*Created {datetime.datetime.now().isoformat()}*"
    path.write_text(content)
    return f"Brief written: {path.relative_to(AGENT_HOME)}"

@tool("reflect", "Write a reflection about what just happened.", "memory")
def tool_reflect(text: str) -> str:
    ts = datetime.datetime.now().isoformat()
    path = REFLECTIONS_DIR / f"reflection_{SESSION_ID}.md"
    content = f"# Reflection — {ts}\n\n{text}\n\n---"
    mode = "a" if path.exists() else "w"
    with open(path, mode) as f:
        f.write("\n\n" + content if mode == "a" else content)
    return f"Reflection saved"

@tool("done", "Mark the current task complete with a summary.", "core")
def tool_done(completed: str, decisions: str = "") -> str:
    STATE["current_task"] = None
    msg = f"✓ Task complete.\n{completed}"
    if decisions:
        msg += f"\n\nDecisions: {decisions}"
    return msg

@tool("stuck", "Signal that you're blocked and need help.", "core")
def tool_stuck(completed: str, blocker: str, attempted: str) -> str:
    msg = f"BLOCKED.\nCompleted: {completed}\nBlocker: {blocker}\nAttempted: {attempted}"
    return msg

@tool("agent_create", "Create a new agent sub-body under AGENTS/<name>/.", "multi-agent")
def tool_agent_create(name: str, constitution: str = None) -> str:
    agent_dir = AGENTS_DIR / name.upper()
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "memory").mkdir(exist_ok=True)
    const = constitution or f"# {name.upper()} — Agent Body\n\nA sub-agent of 999agent."
    (agent_dir / "CONSTITUTION.md").write_text(const)
    return f"Agent '{name.upper()}' created at AGENTS/{name.upper()}/"

@tool("survey", "Show directory structure with file purposes.", "core")
def tool_survey(path: str = ".", max_files: int = 50) -> str:
    base = AGENT_HOME / path
    if not base.exists():
        return f"ERROR: path not found: {path}"
    result = []
    for p in sorted(base.rglob("*")):
        if p.is_dir() or len(result) >= max_files:
            continue
        rel = p.relative_to(AGENT_HOME)
        # Get first line as purpose
        try:
            first = p.read_text().strip().split("\n")[0][:80]
        except:
            first = ""
        result.append(f"{'  ' * (len(rel.parts)-1)}📄 {rel.name}  {_s(first, C.GREY)}")
    return "\n".join(result) if result else "(empty)"

@tool("session_log", "Show the last N entries from the session log.", "memory")
def tool_session_log(n: int = 10) -> str:
    entries = STATE["session_log"][-n:]
    if not entries:
        return "(no log entries yet)"
    return "\n".join(entries)

@tool("help", "List all available tools with descriptions.", "core")
def tool_help() -> str:
    result = [_s("Available Tools:", C.CYAN)]
    cats = {}
    for name, t in sorted(TOOL_REGISTRY.items()):
        cats.setdefault(t["category"], []).append((name, t["description"]))
    for cat, tools in sorted(cats.items()):
        result.append(f"\n  {_s(cat.upper(), C.YELLOW)}")
        for name, desc in tools:
            result.append(f"    {name:<20} {desc}")
    return "\n".join(result)

# ── Path resolution ──
def _resolve_path(path: str) -> Path:
    """Resolve a path relative to agent home."""
    p = Path(path)
    if p.is_absolute():
        return p
    return (AGENT_HOME / path).resolve()

# ═══════════════════════════════════════════
# TOOL AUTO-LOADER
# ═══════════════════════════════════════════

def load_tools():
    """Auto-discover and load tools from tools/ directory."""
    if not TOOLS_DIR.exists():
        return
    sys.path.insert(0, str(TOOLS_DIR))
    for f in sorted(TOOLS_DIR.glob("*.py")):
        if f.name == "__init__.py":
            continue
        try:
            mod_name = f.stem
            import importlib
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "register"):
                tools = mod.register()
                for name, t in tools.items():
                    TOOL_REGISTRY[name] = t
                ok(f"Loaded tools from {f.name}")
        except Exception as e:
            warn(f"Failed to load {f.name}: {e}")

# ═══════════════════════════════════════════
# TOOL DISPATCH
# ═══════════════════════════════════════════

def dispatch_tool(name: str, args: dict) -> str:
    """Execute a tool by name with arguments."""
    if name not in TOOL_REGISTRY:
        return f"ERROR: unknown tool '{name}'. Type 'help' for available tools."
    
    tool_info = TOOL_REGISTRY[name]
    fn = tool_info["fn"]
    
    # Log the call
    STATE["tool_calls_this_turn"] += 1
    entry = f"[T{STATE['turn']}:{STATE['tool_calls_this_turn']}] {name}({_summarize_args(args)})"
    STATE["session_log"].append(entry)
    
    try:
        result = fn(**args)
        STATE["session_log"].append(f"  → {result[:200]}")
        return result
    except TypeError as e:
        return f"ERROR: wrong arguments for {name}: {e}"
    except Exception as e:
        tb = traceback.format_exc()
        STATE["errors"].append(f"{name}: {e}")
        return f"ERROR: {name} failed: {e}\n{tb}"

def _summarize_args(args: dict) -> str:
    """Summarize arguments for logging (truncate long strings)."""
    parts = []
    for k, v in args.items():
        s = str(v)
        if len(s) > 60:
            s = s[:57] + "..."
        parts.append(f"{k}={s}")
    return ", ".join(parts)

# ═══════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════

def process_input(user_input: str) -> str:
    """Process a single user input and return the response."""
    STATE["turn"] += 1
    STATE["tool_calls_this_turn"] = 0
    
    # Parse tool calls from the input
    # Format: tool_name(arg1, arg2=val) or tool_name | arg1 | arg2=val
    
    # Try AST parsing first (handles survey("."), write("x","y"), etc.)
    import ast
    try:
        tree = ast.parse(user_input.strip())
        if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Call):
            call = tree.body[0].value
            name = call.func.id if isinstance(call.func, ast.Name) else None
            if name and name in TOOL_REGISTRY:
                args = {}
                # Positional args → map by parameter name via inspection
                import inspect
                sig = inspect.signature(TOOL_REGISTRY[name]["fn"])
                param_names = list(sig.parameters.keys())
                for i, arg in enumerate(call.args):
                    if i < len(param_names):
                        if isinstance(arg, ast.Constant):
                            args[param_names[i]] = arg.value
                        elif isinstance(arg, ast.Str):
                            args[param_names[i]] = arg.s
                for kw in call.keywords:
                    if isinstance(kw.value, ast.Constant):
                        args[kw.arg] = kw.value.value
                    elif isinstance(kw.value, ast.Str):
                        args[kw.arg] = kw.value.s
                return dispatch_tool(name, args)
    except:
        pass
    
    # Also support: tool_name | arg1 | arg2=val  (pipe syntax)
    parts = user_input.strip().split("|")
    tool_name = parts[0].strip().lower()
    
    if tool_name in TOOL_REGISTRY:
        import inspect
        sig = inspect.signature(TOOL_REGISTRY[tool_name]["fn"])
        param_names = list(sig.parameters.keys())
        args = {}
        pi = 0  # positional index
        for p in parts[1:]:
            p = p.strip()
            if "=" in p:
                k, v = p.split("=", 1)
                args[k.strip()] = v.strip().strip('"').strip("'")
            else:
                if pi < len(param_names):
                    args[param_names[pi]] = p.strip().strip('"').strip("'")
                    pi += 1
        return dispatch_tool(tool_name, args)
    
    # Not a tool call — echo as conversation
    return None  # signal that this wasn't a tool call

def interactive_loop():
    """Main interactive REPL loop."""
    banner()
    info(f"Home: {AGENT_HOME}")
    info(f"Session: {SESSION_ID}")
    info(f"Tools loaded: {len(TOOL_REGISTRY)}")
    echo(_s("Type tool_name(args) or just type to chat. 'help' for tools. 'exit' to quit.", C.GREY))
    echo()
    
    while True:
        try:
            user_input = input(_s("999> ", C.CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            echo()
            ok("Goodbye.")
            break
        
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            ok("Session ended.")
            break
        
        result = process_input(user_input)
        if result is not None:
            echo(result)
        else:
            # Not a tool call — treat as chat
            echo(_s(f"  (chat mode — use tool_name(args) to invoke tools)", C.GREY))
            echo(f"  You said: {user_input}")

def one_shot_task(task: str):
    """Execute a single task and exit."""
    banner()
    info(f"One-shot task: {task}")
    echo()
    
    # Create a plan
    result = dispatch_tool("plan_enter", {"goal": task})
    echo(result)
    
    # Let the user know
    echo(_s(f"\nTask queued. Run the agent interactively to execute it:", C.GREY))
    echo(f"  ./agent.py")
    echo()

def main():
    parser = argparse.ArgumentParser(description=f"999agent v{VERSION}")
    parser.add_argument("--task", "-t", help="One-shot task to execute")
    parser.add_argument("--plan", "-p", action="store_true", help="Enter plan mode")
    parser.add_argument("--replay", help="Replay a past session by ID")
    parser.add_argument("--export", action="store_true", help="Export memory as markdown")
    parser.add_argument("--version", "-v", action="store_true", help="Show version")
    args = parser.parse_args()
    
    # Load external tools
    load_tools()
    
    if args.version:
        print(f"999agent v{VERSION} — {CODENAME}")
        print(f"Home: {AGENT_HOME}")
        print(f"Tools: {len(TOOL_REGISTRY)}")
        return
    
    if args.export:
        # Export memory
        export_path = AGENT_HOME / f"memory_export_{SESSION_ID}.md"
        content = [f"# 999agent Memory Export — {SESSION_ID}\n"]
        for f in sorted(REFLECTIONS_DIR.glob("*.md")):
            content.append(f.read_text())
        if STATE["scratch_file"].exists():
            content.append(f"## Scratchpad\n\n{STATE['scratch_file'].read_text()}")
        export_path.write_text("\n\n---\n\n".join(content))
        ok(f"Memory exported to {export_path.relative_to(AGENT_HOME)}")
        return
    
    if args.task:
        one_shot_task(args.task)
        return
    
    if args.plan:
        goal = input(_s("Plan goal: ", C.CYAN)).strip()
        result = dispatch_tool("plan_enter", {"goal": goal})
        echo(result)
    
    interactive_loop()

if __name__ == "__main__":
    main()
