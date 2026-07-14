"""
AZOTH Self-Patching Loop — P2-T2.
Test fails → WORKER-A analyzes → patch → re-test. 3 fails → stuck().

Design:
  - Takes a test file path + its failure output
  - Dispatches to WORKER-A (code) to propose a patch
  - Applies the patch as an edit to the source-under-test
  - Re-runs the test to verify
  - Retries up to MAX_RETRIES (3) total
  - After 3 consecutive failures, signals stuck via file flag

Integration:
  - Called from agent.py cmd_forge() or cmd_test() after a test failure
  - Depends on: spawn_worker() for analysis, py_compile_check() for syntax gate
  - Signals stuck by writing SELF/STUCK_FLAG.md (read by agent loop)
"""

import os
import sys
import time
import traceback
import re
from pathlib import Path
from typing import Optional, Tuple

HARNESS_DIR = Path(__file__).parent.parent
SELF_DIR = HARNESS_DIR / "SELF"
WORKSPACE = HARNESS_DIR / "WORKSPACE"
STUCK_FLAG = SELF_DIR / "STUCK_FLAG.md"
PATCH_LOG = WORKSPACE / "patch_log.md"

MAX_RETRIES = 3


# ── Patch application ──────────────────────────────────────────────────────

def apply_patch(file_path: str, original: str, patched: str) -> Tuple[bool, str]:
    """
    Apply a patch to a file. The patched content replaces the file.
    Returns (success, message).
    Fails if file doesn't exist or patched content is empty.
    """
    p = Path(file_path)
    if not p.exists():
        return False, f"File not found: {file_path}"
    if not patched or len(patched.strip()) < 10:
        return False, "Patched content is empty or too short"
    
    # Safety: don't overwrite with something that lost all structure
    if len(patched) < len(original) * 0.3:
        return False, f"Patched content ({len(patched)} chars) is <30% of original ({len(original)} chars) — likely corruption, aborting"
    
    try:
        p.write_text(patched)
        return True, f"Patch applied to {file_path} ({len(patched)} bytes written)"
    except Exception as e:
        return False, f"Write error: {e}"


def revert_patch(file_path: str, original: str) -> Tuple[bool, str]:
    """Revert a file to its original content."""
    try:
        Path(file_path).write_text(original)
        return True, f"Reverted {file_path}"
    except Exception as e:
        return False, f"Revert error: {e}"


# ── Syntax gate ────────────────────────────────────────────────────────────

def syntax_check(file_path: str) -> Tuple[bool, str]:
    """
    Python syntax check via compile(). Returns (pass, message).
    """
    try:
        source = Path(file_path).read_text()
        compile(source, file_path, 'exec')
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Compile error: {e}"


# ── Worker-A dispatch ─────────────────────────────────────────────────────

def _call_worker_a(task: str, context: str = "") -> str:
    """
    Call WORKER-A (deepseek-chat, code specialist) to analyze a failure
    and propose a patch. Uses the spawn_worker mechanism if available,
    otherwise falls back to a local heuristic.
    
    This function is designed to be called from agent.py which has
    spawn_worker in scope. When called standalone, it imports it.
    """
    try:
        # Try importing from the running agent context
        from agent import spawn_worker
        result = spawn_worker("A", task, context)
        return result
    except (ImportError, ModuleNotFoundError):
        # Standalone mode — construct a simple heuristic response
        return _local_analyze_failure(task, context)
    except Exception as e:
        return f"WORKER-A dispatch error: {e}"


def _local_analyze_failure(task: str, context: str) -> str:
    """
    Fallback analysis when spawn_worker is not available.
    Attempts to extract error lines and suggest fixes.
    This is a minimal heuristic — the real analysis comes from WORKER-A.
    """
    lines = context.split("\n")
    error_lines = [l for l in lines if any(kw in l.lower() for kw in 
                   ["error", "traceback", "assert", "failed", "exception", "syntaxerror"])]
    
    if not error_lines:
        return ("ANALYSIS: Could not identify specific errors. "
                "Suggested patch: review test assertions and verify function signatures match.")
    
    result = "ANALYSIS (local fallback):\n"
    result += "\n".join(error_lines[:5])
    result += "\n\nSUGGESTION: Review the error lines above. Check function signatures, "
    result += "import paths, and return value contracts."
    return result


# ── Extract patch from WORKER-A response ──────────────────────────────────

def _extract_patch(analysis: str) -> Optional[str]:
    """
    Extract a code patch from WORKER-A's response.
    Looks for Python code blocks marked with ```python ... ```
    Returns the first substantial code block found, or None.
    """
    # Match ```python ... ``` blocks
    blocks = re.findall(r'```(?:python)?\n(.*?)```', analysis, re.DOTALL)
    if not blocks:
        # Try ``` (unlabeled) blocks
        blocks = re.findall(r'```\n(.*?)```', analysis, re.DOTALL)
    
    for block in blocks:
        stripped = block.strip()
        # Must be substantial and look like Python
        if len(stripped) > 50 and ('def ' in stripped or 'import ' in stripped or 'class ' in stripped or 'return ' in stripped):
            return stripped
    
    return None


# ── Core patch loop ────────────────────────────────────────────────────────

def self_patch(test_file: str, source_file: str, failure_output: str,
               max_retries: int = MAX_RETRIES, verbose: bool = True) -> dict:
    """
    Main entry point: attempt to self-patch a failing test.
    
    Args:
        test_file: Path to the test file that failed
        source_file: Path to the source file under test (the one to patch)
        failure_output: The failure output from the test run
        max_retries: Maximum patch attempts (default 3)
        verbose: Print progress messages
    
    Returns:
        dict with keys:
            success: bool — True if all tests now pass
            attempts: int — number of patch attempts made
            final_message: str — summary of what happened
            patches_applied: list[str] — descriptions of patches applied
            stuck: bool — True if max_retries exhausted and still failing
    """
    result = {
        "success": False,
        "attempts": 0,
        "final_message": "",
        "patches_applied": [],
        "stuck": False,
    }
    
    # Read original source for revert capability
    src_path = Path(source_file)
    if not src_path.exists():
        result["final_message"] = f"Source file not found: {source_file}"
        return result
    
    original_source = src_path.read_text()
    test_path = Path(test_file)
    test_name = test_path.stem if test_path.exists() else "unknown_test"
    
    if verbose:
        print(f"  ◆ Self-Patch: {test_name} → {source_file}")
        print(f"  ◆ Max retries: {max_retries}")
    
    for attempt in range(1, max_retries + 1):
        result["attempts"] = attempt
        
        if verbose:
            print(f"  ◆ Patch attempt {attempt}/{max_retries}")
        
        # Step 1: Read current source
        try:
            current_source = src_path.read_text()
        except Exception as e:
            result["final_message"] = f"Cannot read source: {e}"
            return result
        
        # Step 2: Dispatch to WORKER-A for analysis
        task = (
            f"A test is failing. Analyze the failure and propose a fix.\n\n"
            f"TEST FILE: {test_file}\n"
            f"SOURCE FILE: {source_file}\n\n"
            f"FAILURE OUTPUT:\n{failure_output[:2000]}\n\n"
            f"CURRENT SOURCE CODE:\n```python\n{current_source[:3000]}\n```\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Identify what is wrong in the source code\n"
            f"2. Output the COMPLETE corrected source code in a ```python block\n"
            f"3. Explain the fix briefly\n"
            f"4. Do NOT modify the test file — only the source file"
        )
        
        analysis = _call_worker_a(task, context=f"Test: {test_name}, File: {source_file}")
        
        if verbose:
            print(f"  ◆ WORKER-A analysis received ({len(analysis)} chars)")
        
        # Step 3: Extract patch
        patched_code = _extract_patch(analysis)
        
        if patched_code is None:
            if verbose:
                print(f"  ◆ No code patch found in analysis — trying full response as patch")
            # Try using the whole response as a patch if it looks like code
            if 'def ' in analysis or 'class ' in analysis:
                patched_code = analysis
        
        if patched_code is None or len(patched_code.strip()) < 50:
            msg = f"Attempt {attempt}: WORKER-A did not produce a valid patch"
            if verbose:
                print(f"  ✗ {msg}")
            if attempt < max_retries:
                failure_output += f"\n\n[Patch attempt {attempt} failed: {msg}]"
            continue
        
        # Step 4: Apply patch
        success, msg = apply_patch(source_file, current_source, patched_code)
        if not success:
            if verbose:
                print(f"  ✗ Patch apply failed: {msg}")
            if attempt < max_retries:
                failure_output += f"\n\n[Patch apply failed: {msg}]"
            continue
        
        result["patches_applied"].append(f"Attempt {attempt}: {msg}")
        if verbose:
            print(f"  ✓ {msg}")
        
        # Step 5: Syntax gate
        syntax_ok, syntax_msg = syntax_check(source_file)
        if not syntax_ok:
            if verbose:
                print(f"  ✗ Syntax check failed: {syntax_msg}")
            # Revert and try again
            revert_patch(source_file, current_source)
            if attempt < max_retries:
                failure_output += f"\n\n[Syntax error after patch: {syntax_msg}]"
            continue
        
        if verbose:
            print(f"  ✓ Syntax check passed")
        
        # Step 6: Re-run the test
        test_pass, test_msg = _run_single_test(test_file)
        
        if test_pass:
            result["success"] = True
            result["final_message"] = (f"Self-patch succeeded on attempt {attempt}. "
                                       f"{test_name} now passes. Patch applied to {source_file}.")
            if verbose:
                print(f"  ✓ TEST PASSES — self-patch successful on attempt {attempt}")
            
            # Log the successful patch
            _log_patch(test_file, source_file, attempt, True, test_msg)
            return result
        else:
            if verbose:
                print(f"  ✗ Test still failing after patch: {test_msg[:200]}")
            # Revert for next attempt
            revert_patch(source_file, current_source)
            failure_output = f"[After patch attempt {attempt}] Test result: {test_msg}\n\nOriginal failure context:\n{failure_output[:1500]}"
    
    # All retries exhausted
    result["final_message"] = (f"Self-patch failed after {max_retries} attempts. "
                               f"Source reverted to original. Manual intervention required.")
    result["stuck"] = True
    
    # Write stuck flag
    _write_stuck_flag(test_file, source_file, max_retries, result["patches_applied"])
    
    if verbose:
        print(f"  ◆ STUCK — {max_retries} attempts exhausted. STUCK_FLAG written.")
    
    return result


def _run_single_test(test_file: str) -> Tuple[bool, str]:
    """
    Run a single test file and return (pass, message).
    Uses importlib to load and run the test module.
    """
    test_path = Path(test_file)
    if not test_path.exists():
        return False, f"Test file not found: {test_file}"
    
    try:
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(test_path.stem, str(test_path))
        if spec is None or spec.loader is None:
            return False, f"Could not load spec for {test_file}"
        
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        failures = []
        for name in dir(mod):
            if not name.startswith("test_"):
                continue
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            try:
                ret = fn()
                if ret is None:
                    failures.append(f"{name}: no return value (expected True/False or tuple)")
                elif isinstance(ret, tuple):
                    if not ret[0]:
                        failures.append(f"{name}: {ret[1]}")
                elif not ret:
                    failures.append(f"{name}: returned False")
            except Exception as e:
                failures.append(f"{name}: {e}")
        
        if failures:
            return False, "; ".join(failures[:5])
        return True, "All tests passed"
    
    except Exception as e:
        return False, f"Module import error: {e}"


def _write_stuck_flag(test_file: str, source_file: str, attempts: int, patches: list):
    """Write a stuck flag file that the agent loop can detect."""
    SELF_DIR.mkdir(parents=True, exist_ok=True)
    content = [
        "# STUCK FLAG — Self-Patching Loop Exhausted",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Test file: {test_file}",
        f"Source file: {source_file}",
        f"Attempts made: {attempts}",
        f"Patches attempted: {len(patches)}",
        "",
        "Patches applied and reverted:",
    ]
    for p in patches:
        content.append(f"  - {p}")
    content.append("")
    content.append("Manual intervention required. Remove this file after fixing.")
    
    STUCK_FLAG.write_text("\n".join(content))


def _log_patch(test_file: str, source_file: str, attempt: int, success: bool, message: str):
    """Log a patch attempt to the patch log."""
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    entry = (
        f"## Patch Attempt — {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Test: {test_file}\n"
        f"Source: {source_file}\n"
        f"Attempt: {attempt}\n"
        f"Status: {'✓ PASS' if success else '✗ FAIL'}\n"
        f"Message: {message}\n\n"
    )
    
    if PATCH_LOG.exists():
        existing = PATCH_LOG.read_text()
        PATCH_LOG.write_text(entry + existing)
    else:
        PATCH_LOG.write_text("# AZOTH Patch Log\n\n" + entry)


def check_stuck_flag() -> bool:
    """Returns True if a stuck flag exists (indicating manual intervention needed)."""
    return STUCK_FLAG.exists()


def clear_stuck_flag():
    """Remove the stuck flag after manual intervention."""
    if STUCK_FLAG.exists():
        STUCK_FLAG.unlink()
        return True
    return False


# ── CLI entry point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AZOTH Self-Patching Loop")
    parser.add_argument("test_file", help="Path to the failing test file")
    parser.add_argument("source_file", help="Path to the source file to patch")
    parser.add_argument("--failure", "-f", default="", help="Failure output text (or read from stdin)")
    parser.add_argument("--retries", "-r", type=int, default=MAX_RETRIES, help="Max retry attempts")
    
    args = parser.parse_args()
    
    failure_text = args.failure
    if not failure_text and not sys.stdin.isatty():
        failure_text = sys.stdin.read()
    if not failure_text:
        failure_text = "(no failure output provided)"
    
    result = self_patch(args.test_file, args.source_file, failure_text, 
                        max_retries=args.retries, verbose=True)
    
    print(f"\n{'='*50}")
    print(f"Result: {'✓ PASS' if result['success'] else '✗ FAIL'}")
    print(f"Attempts: {result['attempts']}")
    print(f"Stuck: {result['stuck']}")
    print(f"Message: {result['final_message']}")
    sys.exit(0 if result['success'] else 1)
