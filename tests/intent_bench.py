#!/usr/bin/env python3
"""T0.2 bench — natural build intent (kill mandatory /forge).

Deterministic, offline. Proves the ONE classifier (_wants_tools) routes plain build
asks to the tool loop with zero /forge, and keeps casual chat as chat. Includes Mac's
exact failing message. Run: python3 tests/intent_bench.py
"""
import io, sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
with redirect_stdout(io.StringIO()):
    import agent as A

# minimal stand-in with just what _wants_tools touches
class _Stub:
    _force_chat_once = False
clf = A.Agent._wants_tools.__get__(_Stub(), _Stub)

BUILD = [
    "can you fix azoth please ⊚ make me a mini snake game",   # Mac's exact case
    "make me a mini snake game",
    "build a web server",
    "can you build a todo app",
    "fix the parse bug in agent.py",
    "wire up the telegram bot",
    "add a /compact command",
    "refactor the tool loop",
    "scaffold a godot game",
    "write a python script to rename files",
    "create a new file called notes.md",
    "implement session memory",
    "debug the 429 handler",
    "run the tests",
    "commit and push the changes",
    "make the readme",
    "update the changelog",
    "ls AZOTH/CORE",
]
CASUAL = [
    "hey bro",
    "morning",
    "how are you today",
    "thanks brother",
    "lol that's wild",
    "gn",
    "love you man",
    "cool",
    "what's up",
    "yeah",
]

fails = 0
for s in BUILD:
    if not clf(s):
        fails += 1
        print(f"FAIL build→chat: {s!r}")
    else:
        print(f"ok   build→tools: {s!r}")
for s in CASUAL:
    if clf(s):
        fails += 1
        print(f"FAIL casual→tools: {s!r}")
    else:
        print(f"ok   casual→chat : {s!r}")

total = len(BUILD) + len(CASUAL)
print(f"\n{'PASS' if fails == 0 else 'FAIL'}: {total - fails}/{total} "
      f"({len(BUILD)} build asks fire tools w/o /forge, {len(CASUAL)} casual stay chat)")
sys.exit(1 if fails else 0)
