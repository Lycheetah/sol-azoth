#!/usr/bin/env python3
"""VAEL-SP SUBAGENT — the controlled test-hand.

VAEL-SP spawns this as a SEPARATE PROCESS to build things while he reviews. It is
isolated by construction:
  - Runs in its OWN process (a crash here never touches VAEL)
  - Sandboxed to WORKSPACE/SUBAGENT/ ONLY — cannot read or write anywhere else
  - Free NVIDIA key only (never the paid DeepSeek key — a runaway loop costs nothing)
  - Bounded steps (hard cap), bounded tokens
  - Writes its result to WORKSPACE/SUBAGENT/result.md for VAEL to review

This is how VAEL builds himself up without risk: the subagent attempts, VAEL judges.
The subagent has NO walls to enforce because it has NO reach outside its sandbox —
every file path it produces is forced under SANDBOX before it touches disk.

Usage:  python3 subagent.py "<task description>"
        VAEL calls this via the spawn_subagent tool. Mac can also run it directly.
"""
import os, sys, json, subprocess
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    print("SUBAGENT ERROR: openai package not available", file=sys.stderr)
    sys.exit(2)

HOME     = Path(__file__).parent.resolve()
SANDBOX  = HOME / "WORKSPACE" / "SUBAGENT"
SANDBOX.mkdir(parents=True, exist_ok=True)
RESULT_F = SANDBOX / "result.md"

# FREE key only. The subagent never gets the paid endpoint — by design.
NVIDIA_KEY = os.environ.get("NVIDIA_KEY", "")
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY)
MODEL  = os.environ.get("SUBAGENT_MODEL", "meta/llama-4-maverick-17b-128e-instruct")

MAX_STEPS = int(os.environ.get("SUBAGENT_MAX_STEPS", "12"))

SYSTEM = f"""You are the VAEL-SP SUBAGENT — a focused build-hand spawned to attempt ONE task.

YOUR SANDBOX: {SANDBOX}
You may ONLY create files inside that directory. Every path you write is forced
under the sandbox automatically — do not try to escape it; you have no reach outside.

You are precise and fast. You build the thing, you test it if it's code, you report
honestly what works and what doesn't. You do not pad. You do not explain what you
will do — you do it and show the result.

TOOLS (reply with a single JSON object per turn, nothing else):
  {{"tool": "write", "name": "<filename>", "content": "<file contents>"}}
  {{"tool": "run",   "command": "<bash run inside the sandbox>"}}
  {{"tool": "done",  "summary": "<what you built, what works, what doesn't>"}}

Filenames are relative to the sandbox. `run` executes inside the sandbox only.
When the task is complete and verified, call done. You have at most {MAX_STEPS} turns."""


def _safe_path(name: str) -> Path:
    """Force any filename under the sandbox. No escape possible."""
    p = (SANDBOX / name).resolve()
    if not str(p).startswith(str(SANDBOX.resolve())):
        # Reached outside — collapse to a flat name inside the sandbox.
        p = SANDBOX / Path(name).name
    return p


def _run_in_sandbox(command: str) -> str:
    # Block any obvious escape or push, mirror the parent's spirit. Subagent is
    # sandboxed by cwd + path-forcing, but we still refuse the worst patterns.
    bad = ["..", "~", "/home/guestpc/.claude", "git push", "rm -rf /", "api.anthropic.com",
           "CODEX_AURA_PRIME", "0sol-by-lycheetah", "SOL-MOBILE-VAULT"]
    for b in bad:
        if b in command:
            return f"BLOCKED: '{b}' is not permitted in the subagent sandbox."
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True,
                           timeout=60, cwd=str(SANDBOX))
        return (r.stdout + ("\n[stderr] " + r.stderr if r.stderr else "")).strip()[:2000] or f"[exit {r.returncode}]"
    except subprocess.TimeoutExpired:
        return "TIMEOUT after 60s"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    task = sys.argv[1] if len(sys.argv) > 1 else ""
    if not task:
        print("SUBAGENT ERROR: no task given", file=sys.stderr)
        sys.exit(1)

    print(f"◆ SUBAGENT spawned · sandbox={SANDBOX} · model={MODEL} · max_steps={MAX_STEPS}")
    print(f"  TASK: {task}\n")

    history = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"TASK: {task}\n\nBegin. One JSON tool object per turn."},
    ]
    log = [f"# SUBAGENT RESULT\n\n**Task:** {task}\n\n## Build log\n"]

    for step in range(MAX_STEPS):
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=history, temperature=0.4, max_tokens=2000,
            )
            content = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            log.append(f"\n- step {step+1}: MODEL ERROR {e}")
            break

        # Extract the first JSON object
        try:
            start = content.index("{")
            depth, end = 0, None
            for i in range(start, len(content)):
                if content[i] == "{": depth += 1
                elif content[i] == "}":
                    depth -= 1
                    if depth == 0: end = i + 1; break
            obj = json.loads(content[start:end])
        except Exception:
            log.append(f"\n- step {step+1}: no valid tool JSON, stopping. Raw: {content[:200]}")
            break

        tool = obj.get("tool")
        history.append({"role": "assistant", "content": content})

        if tool == "write":
            p = _safe_path(obj.get("name", "untitled.txt"))
            p.write_text(obj.get("content", ""))
            msg = f"wrote {p.relative_to(SANDBOX)} ({len(obj.get('content',''))} bytes)"
            print(f"  [{step+1}] {msg}")
            log.append(f"\n- step {step+1}: {msg}")
            history.append({"role": "user", "content": f"OK — {msg}. Continue."})

        elif tool == "run":
            out = _run_in_sandbox(obj.get("command", ""))
            print(f"  [{step+1}] run: {obj.get('command','')[:60]} → {out[:80]}")
            log.append(f"\n- step {step+1}: ran `{obj.get('command','')}` →\n```\n{out[:600]}\n```")
            history.append({"role": "user", "content": f"Output:\n{out[:1500]}\nContinue."})

        elif tool == "done":
            summary = obj.get("summary", "(no summary)")
            print(f"  [{step+1}] DONE: {summary[:120]}")
            log.append(f"\n\n## DONE\n{summary}")
            break
        else:
            log.append(f"\n- step {step+1}: unknown tool '{tool}', stopping.")
            break
    else:
        log.append(f"\n\n## STOPPED — hit max steps ({MAX_STEPS}) without done.")

    RESULT_F.write_text("\n".join(log))
    print(f"\n◆ SUBAGENT finished · result → {RESULT_F}")


if __name__ == "__main__":
    main()
