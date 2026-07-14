"""P1-T3: Dynamic tool loader tests."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_tool_loader_importable():
    from CORE.tool_loader import discover_tools, list_tools, call_tool
    return True, "discover_tools + list_tools + call_tool importable"

def test_tool_loader_discovers_tools():
    from CORE.tool_loader import discover_tools, list_tools
    discover_tools()
    tools = list_tools()  # returns list of dicts with 'name', 'description', etc.
    assert len(tools) >= 1, f"Expected >=1 tool, found: {tools}"
    names = [t["name"] for t in tools]
    return True, f"discovered {len(tools)} tool(s): {names}"

def test_tool_hello_exists():
    from CORE.tool_loader import discover_tools, list_tools
    discover_tools()
    tools = list_tools()
    names = [t["name"] for t in tools]
    hello_names = [n for n in names if "hello" in n.lower()]
    assert hello_names, f"No hello tool found. Available: {names}"
    return True, f"hello tool present: {hello_names}"

def test_tool_call_hello():
    from CORE.tool_loader import discover_tools, call_tool, list_tools
    discover_tools()
    tools = list_tools()
    names = [t["name"] for t in tools]
    hello_names = [n for n in names if "hello" in n.lower()]
    if not hello_names:
        return None, "SKIP — no hello tool to call"
    result = call_tool(hello_names[0])
    assert result is not None, "call_tool returned None"
    return True, f"call_tool('{hello_names[0]}') returned: {str(result)[:60]}"

def test_custom_tool_roundtrip():
    """Load a custom tool from a temp dir by temporarily pointing TOOLS_DIR there."""
    from CORE import tool_loader
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        tool_file = os.path.join(d, "custom_roundtrip.py")
        with open(tool_file, "w") as f:
            f.write(
                'def register():\n'
                '    return {\n'
                '        "name": "custom_roundtrip",\n'
                '        "description": "temp test tool",\n'
                '        "parameters": {},\n'
                '        "handler": lambda **kw: "roundtrip_ok"\n'
                '    }\n'
            )
        original_dir = getattr(tool_loader, "TOOLS_DIR", None)
        tool_loader.TOOLS_DIR = Path(d)
        try:
            tool_loader.reload_tools()
            tools = tool_loader.list_tools()
            names = [t["name"] for t in tools]
            assert "custom_roundtrip" in names, f"custom_roundtrip not in: {names}"
            result = tool_loader.call_tool("custom_roundtrip")
            inner = result.get("result") if isinstance(result, dict) else result
            assert inner == "roundtrip_ok", f"Expected 'roundtrip_ok', got: {result}"
        finally:
            if original_dir is not None:
                tool_loader.TOOLS_DIR = original_dir
            tool_loader.reload_tools()
    return True, "custom tool registered + called successfully"
