#!/usr/bin/env python3
"""T1.2/T1.3/T1.1/T1.4 bench — Action Ledger, anti-repeat, compaction, continuity.

Deterministic, offline (no API). Writes to temp dirs. Run: python3 tests/memory_bench.py
"""
import io, sys, tempfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
with redirect_stdout(io.StringIO()):
    import agent as A

def q(fn):
    with redirect_stdout(io.StringIO()):
        return fn()

fails = 0
def check(label, cond):
    global fails
    print(f"{'ok  ' if cond else 'FAIL'} {label}")
    if not cond: fails += 1

# reset live ledger
A._ACTION_LEDGER.clear(); A._SESSION_WRITES.clear(); A._WRITE_COUNTS.clear()

# T1.2 ledger + T1.3 identical-skip
note = str(Path(tempfile.mkdtemp()) / "note.md")
r1 = q(lambda: A.dispatch_tool("write_file", {"path": note, "content": "hello"}))
check("first write proceeds", "SKIPPED" not in r1)
r2 = q(lambda: A.dispatch_tool("write_file", {"path": note, "content": "hello"}))
check("identical rewrite SKIPPED (anti-repeat)", "SKIPPED (anti-repeat)" in r2)

# T1.3 rewrite guard: 3 different writes ok, 4th blocked
readme = str(Path(tempfile.mkdtemp()) / "README.md")
res = [q(lambda i=i: A.dispatch_tool("write_file", {"path": readme, "content": f"v{i}"})) for i in range(4)]
check("first 3 differing writes proceed", all("SKIPPED" not in res[k] for k in range(3)))
check("4th rewrite SKIPPED (guard)", "SKIPPED (anti-repeat guard)" in res[3])

# T1.2 ledger context surfaces the work
ctx = A._ledger_context()
check("ledger context has ALREADY DONE + both files",
      "ALREADY DONE" in ctx and "note.md" in ctx and "README.md" in ctx)

# T1.4 continuity: clear in-memory, rehydrate from today's log
A._ACTION_LEDGER.clear()
n = A._ledger_rehydrate()
check("rehydrate reloads today's actions", n > 0 and len(A._ACTION_LEDGER) > 0)

# T1.1 compaction fold (offline: stub call_model → forces rule-based summary)
class FakeAgent:
    def __init__(self):
        self.history = [{"role": "user", "content": f"msg{i}"} if i % 2 == 0
                        else {"role": "assistant", "content": f"reply{i}"} for i in range(20)]
    def call_model(self, *a, **k):
        return "", []
fa = FakeAgent()
msg = A.Agent.compact_history.__get__(fa, FakeAgent)(keep_recent=6)
check("compact folds 20→7 (1 summary + 6 recent)", "Compacted" in msg and len(fa.history) == 7)
check("compacted summary carries a system marker", fa.history[0]["role"] == "system"
      and "COMPACTED SESSION SUMMARY" in fa.history[0]["content"])

total = 9
print(f"\n{'PASS' if fails == 0 else 'FAIL'}: {total - fails}/{total}")
sys.exit(1 if fails else 0)
