"""
VAEL-SP Dynamic Tool Loader
───────────────────────────
Auto-discovers all .py files in tools/ (except __init__.py),
calls their register() function, and returns the merged tool registry.

Each tool module must expose:
    def register() -> dict
        Returns: {
            "name": str,           # unique tool name
            "description": str,    # what it does
            "safety_level": str,   # "safe" | "filesystem" | "network" | "dangerous"
            "params": [            # list of parameter dicts
                {
                    "name": str,
                    "type": str,       # "string" | "integer" | "boolean"
                    "description": str,
                    "required": bool,
                    "default": any     # optional
                }
            ],
            "handler": callable    # the function that handles the tool call
        }

The loader validates:
    - name is unique (no duplicates across modules)
    - handler is callable
    - params have required fields
"""

import importlib.util
import inspect
import os
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent


def discover_tool_modules():
    """Find all .py files in tools/ that aren't __init__.py."""
    modules = []
    for f in sorted(TOOLS_DIR.glob("*.py")):
        if f.name == "__init__.py":
            continue
        if f.name.startswith("_"):
            continue
        modules.append(f)
    return modules


def load_tool_module(filepath):
    """Dynamically import a single tool module from its file path."""
    module_name = filepath.stem
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        return None, f"Could not create spec for {filepath}"
    
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        return None, f"Import error in {module_name}: {e}"
    
    return module, None


def validate_tool_registration(reg: dict, source: str) -> list:
    """Validate a tool registration dict. Returns list of error strings (empty = valid)."""
    errors = []
    
    required_keys = ["name", "description", "safety_level", "params", "handler"]
    for key in required_keys:
        if key not in reg:
            errors.append(f"Missing required key '{key}' in {source}")
    
    if "name" in reg:
        if not isinstance(reg["name"], str) or not reg["name"].strip():
            errors.append(f"Tool name must be a non-empty string in {source}")
    
    if "description" in reg:
        if not isinstance(reg["description"], str) or not reg["description"].strip():
            errors.append(f"Tool description must be a non-empty string in {source}")
    
    if "safety_level" in reg:
        valid_levels = ["safe", "filesystem", "network", "dangerous"]
        if reg["safety_level"] not in valid_levels:
            errors.append(f"Invalid safety_level '{reg['safety_level']}' in {source}. Must be one of {valid_levels}")
    
    if "handler" in reg:
        if not callable(reg["handler"]):
            errors.append(f"Handler must be callable in {source}")
    
    if "params" in reg:
        if not isinstance(reg["params"], list):
            errors.append(f"Params must be a list in {source}")
        else:
            for i, p in enumerate(reg["params"]):
                if not isinstance(p, dict):
                    errors.append(f"Param {i} must be a dict in {source}")
                    continue
                if "name" not in p:
                    errors.append(f"Param {i} missing 'name' in {source}")
                if "type" not in p:
                    errors.append(f"Param {i} missing 'type' in {source}")
    
    return errors


def load_all_tools():
    """
    Scan tools/, load every module, call register(), validate.
    Returns:
        registry: dict of {name: registration_dict}
        definitions: list of OpenAI-style tool definitions (for TOOL_DEFINITIONS)
        errors: list of error strings
    """
    registry = {}
    definitions = []
    errors = []
    
    modules = discover_tool_modules()
    
    for filepath in modules:
        module, err = load_tool_module(filepath)
        if err:
            errors.append(err)
            continue
        
        if not hasattr(module, "register"):
            errors.append(f"{filepath.name} has no register() function — skipping")
            continue
        
        try:
            reg = module.register()
        except Exception as e:
            errors.append(f"register() failed in {filepath.name}: {e}")
            continue
        
        # Validate
        validation_errors = validate_tool_registration(reg, filepath.name)
        if validation_errors:
            errors.extend(validation_errors)
            continue
        
        # Check uniqueness
        name = reg["name"]
        if name in registry:
            errors.append(f"Duplicate tool name '{name}' in {filepath.name} (already from {registry[name]['_source']})")
            continue
        
        # Build OpenAI-style definition
        properties = {}
        required_params = []
        for p in reg["params"]:
            param_name = p["name"]
            param_type = p.get("type", "string")
            
            # Map our types to JSON schema types
            type_map = {
                "string": "string",
                "integer": "number",
                "boolean": "boolean",
                "number": "number",
                "array": "array",
                "object": "object",
            }
            json_type = type_map.get(param_type, "string")
            
            param_schema = {
                "type": json_type,
                "description": p.get("description", ""),
            }
            
            if "default" in p:
                param_schema["default"] = p["default"]
            
            properties[param_name] = param_schema
            
            if p.get("required", False):
                required_params.append(param_name)
        
        definition = {
            "type": "function",
            "function": {
                "name": name,
                "description": reg["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                },
            },
        }
        
        if required_params:
            definition["function"]["parameters"]["required"] = required_params
        
        # Store
        reg["_source"] = filepath.name
        reg["_definition"] = definition
        registry[name] = reg
        definitions.append(definition)
    
    return registry, definitions, errors
