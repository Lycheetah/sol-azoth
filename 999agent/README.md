# 999agent — World-Class Coding Agent Harness

A standalone, self-contained coding agent harness. Launch from terminal, constrained to its folder, built from scratch.

## Quick Start

```bash
# Launch interactively
./launch.sh

# Or if installed globally
999agent

# One-shot task
./launch.sh --task "build a web server"
```

## Commands

| Command | Description |
|---------|-------------|
| `./launch.sh` or `999agent` | Interactive session |
| `--task "build a thing"` | One-shot task |
| `--plan` | Enter plan mode |
| `--replay <session_id>` | Replay a past session |
| `--export` | Export memory as markdown |
## Commands

| Command | Description |
|---------|-------------|
| `./launch.sh` or `999agent` | Interactive session |
| `--task "build a thing"` | One-shot task |
| `--plan` | Enter plan mode |
| `--replay <session_id>` | Replay a past session |
| `--export` | Export memory as markdown |
| `--list-sessions` | List all past sessions |
| `--version` | Show version |

## Tools (33 built-in)

| Category | Tools |
|----------|-------|
| **Core (11)** | `read`, `write`, `edit`, `exact_edit`, `bash`, `glob`, `search`, `survey`, `py_check`, `help`, `done`, `stuck` |
| **Dev (5)** | `py_compile_check`, `git_status`, `git_commit`, `self_diff`, `survey` |
```
999agent/
├── agent.py              # Main loop + tool dispatch (680+ lines)
├── CONSTITUTION.md        # Agent identity and rules
├── 999agent               # Terminal launcher (symlink to PATH)
├── launch.sh              # Self-executing launcher (bash+python)
├── tools/                 # Auto-loaded tool implementations
│   ├── __init__.py         # Tool auto-discoverer (loads all .py files)
│   ├── web_search.py       # web_search + fetch tools
│   ├── dev_tools.py        # py_compile_check, git_status, git_commit, self_diff, survey
│   └── memory_tools.py     # session_replay, session_list, export_memory, task_tree
├── memory/                # Session logs, reflections, scratchpad
│   ├── sessions/           # JSON session logs (auto-saved on exit)
│   └── reflections/        # End-of-session reflections
├── workspace/             # Briefs, research, ephemeral output
│   └── briefs/
└── AGENTS/                # Sub-agent bodies (optional)
```
│   ├── sessions/
│   └── reflections/
├── workspace/             # Briefs, research, ephemeral output
│   └── briefs/
└── AGENTS/                # Sub-agent bodies (optional)
```

## Installation

```bash
# Symlink to PATH for global use
cd 999agent
chmod +x agent.py launch.sh 999agent
## Session Persistence

Every session is **auto-saved** on exit:
- Session log → `memory/sessions/<session_id>.json`
- Reflection → `memory/reflections/<session_id>.md`
- Replay any past session: `./agent.py --replay <session_id>`
- List all sessions: `./agent.py --list-sessions`

## Design Principles

1. **Self-contained** — everything in one folder, no external dependencies
2. **Constrained** — sandboxed to its home directory
3. **Tool-first** — every action is a tool call with string I/O
4. **Plans + Tasks** — structured planning for complex work
5. **Memory** — session logging, reflections, persistent scratchpad, replay
6. **Extensible** — drop `.py` files in `tools/` with a `register()` function
7. **Dev tools** — built-in compile check, git, diff, directory survey

## Extending

Drop a `.py` file in `tools/` with a `register()` function that returns
`{name: {"fn": callable, "description": str, "category": str}}`:

```python
def register() -> dict:
    return {
        "my_tool": {
            "fn": my_tool_impl,
            "description": "Does something useful",
            "category": "custom",
        },
    }
```

Tools are auto-discovered and loaded at startup. No registration needed beyond
the file existing in `tools/`.
    @tool("my_tool", "Does something useful", "custom")
    def my_tool(param: str) -> str:
        return f"Did something with {param}"
    return {}
```

---

*999agent v1.0.0 — World-Class Coding Agent*
