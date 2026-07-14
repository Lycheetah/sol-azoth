#!/usr/bin/env python3
"""
VAEL-SP Dynamic Tool Loader — Phase 1, Task 3.
Scans tools/ directory for Python files with register() functions.
Each tool declares: name, description, parameters, handler, safety_level.
Tools become available as /tool_name commands in the agent loop.
"""

import importlib.util
import inspect
import os
import sys
import pathlib
import traceback

TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
REGISTRY = {}  # name -> {name, desc, params, handler, safety_level, file}


def discover_tools():
    """Scan tools/ directory and load all registered tools."""
    global REGISTRY
    REGISTRY = {}
    tools_dir = pathlib.Path(TOOLS_DIR)
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Ensure tools dir is in path
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))

    loaded = []
    errors = []

    for f in sorted(tools_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        if f.name == "council_loop.sh":
            continue

        try:
            spec = importlib.util.spec_from_file_location(f.stem, str(f))
            if spec is None or spec.loader is None:
                errors.append(f"{f.name}: could not load spec")
                continue

            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not hasattr(mod, "register"):
                errors.append(f"{f.name}: no register() function")
                continue

            tool_def = mod.register()
            if not isinstance(tool_def, dict) or "name" not in tool_def:
                errors.append(f"{f.name}: register() must return dict with 'name'")
                continue

            tool_def["file"] = str(f)
            REGISTRY[tool_def["name"]] = tool_def
            loaded.append(tool_def["name"])

        except Exception as e:
            errors.append(f"{f.name}: {e}\n{traceback.format_exc()}")

    return {
        "loaded": loaded,
        "errors": errors,
        "count": len(loaded)
    }


def get_tool(name):
    """Get a tool definition by name."""
    return REGISTRY.get(name)


def list_tools():
    """List all loaded tools with their descriptions."""
    result = []
    for name, tool in sorted(REGISTRY.items()):
        result.append({
            "name": name,
            "description": tool.get("description", ""),
            "safety_level": tool.get("safety_level", "normal"),
            "params": tool.get("params", [])
        })
    return result


def call_tool(tool_name, **kwargs):
    """Call a tool by name with given parameters."""
    tool = REGISTRY.get(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found", "success": False}
    if not tool:
        return {"error": f"Tool '{name}' not found", "success": False}

    handler = tool.get("handler")
    if not handler:
        return {"error": f"Tool '{name}' has no handler", "success": False}

    try:
        result = handler(**kwargs)
        return {"result": result, "success": True}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc(), "success": False}


def reload_tools():
    """Force reload all tools (clear import cache for tool modules)."""
    for name in list(REGISTRY.keys()):
        # Remove from sys.modules if loaded
        mod_name = f"tools.{name}"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    return discover_tools()


if __name__ == "__main__":
    result = discover_tools()
    print(f"Loaded {result['count']} tools:")
    for name in result["loaded"]:
        print(f"  ✓ {name}")
    for err in result["errors"]:
        print(f"  ✗ {err}")
