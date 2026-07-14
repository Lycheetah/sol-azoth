"""999agent tool loader — auto-discovers tools in this directory.

Usage:
    from tools import load_tools, TOOL_REGISTRY
    load_tools()
    result = TOOL_REGISTRY["web_search"]["fn"](query="hello")
"""

import sys
import importlib
from pathlib import Path

TOOL_REGISTRY: dict = {}
TOOLS_DIR = Path(__file__).parent.resolve()


def load_tools(verbose: bool = True) -> dict:
    """Auto-discover and load all tools from this directory.
    
    Each .py file (except __init__.py) should expose a register() function
    returning {name: {"fn": callable, "description": str, "category": str}}.
    
    Returns the populated TOOL_REGISTRY.
    """
    sys.path.insert(0, str(TOOLS_DIR))
    
    for f in sorted(TOOLS_DIR.glob("*.py")):
        if f.name == "__init__.py":
            continue
        try:
            mod_name = f.stem
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "register"):
                tools = mod.register()
                for name, t in tools.items():
                    TOOL_REGISTRY[name] = t
                if verbose:
                    print(f"  ✓ Loaded {len(tools)} tool(s) from {f.name}")
        except Exception as e:
            if verbose:
                print(f"  ⚠ Failed to load {f.name}: {e}")
    
    return TOOL_REGISTRY


def get_tool(name: str):
    """Get a tool function by name."""
    if name not in TOOL_REGISTRY:
        return None
    return TOOL_REGISTRY[name]["fn"]


def list_tools(category: str = None) -> list:
    """List all registered tools, optionally filtered by category."""
    if category:
        return [(n, t) for n, t in TOOL_REGISTRY.items() if t.get("category") == category]
    return list(TOOL_REGISTRY.items())
