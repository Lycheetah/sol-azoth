#!/usr/bin/env python3
"""Run all LAMAGUE examples against the interpreter. Exit 0 = all pass."""
import sys
sys.path.insert(0, '/home/guestpc/AZOTH')
from CORE.lamague_interpreter import LAMAGUE

lam = LAMAGUE()
tests = []

def test(name, code, expected):
    tests.append((name, code, expected))

# 1. Arithmetic
test("literal int", "42", 42)
test("literal float", "3.14", 3.14)
test("addition", "3 + 4", 7)
test("subtraction", "10 - 3", 7)
test("multiplication", "6 * 7", 42)
test("division", "10 / 2", 5.0)
test("parens", "(3 + 4) * 2", 14)

# 2. Variables
test("assign + read", "a := 1; a", 1)
test("assign + increment", "a := 1; a := a + 1; a", 2)

# 3. Sequences
test("sequence", "a := 1; a := a + 1; a", 2)

# 4. Blocks
test("block", "b := {c := 10; c * 2}", 20)

# 5. Conditionals
test("implication true", "x := 20; x > 10 ∴ 100", 100)
test("implication false", "x := 5; x > 10 ∴ 100", None)

# 6. While loops
lam.set_variable("count", 0)
test("while loop", "count := 0; while (count < 5) { count := count + 1 }; count", 5)

# 7. Lambda
test("lambda", "double := λ(x) x * 2; double(21)", 42)
test("lambda multi-arg", "add := λ(a, b) a + b; add(10, 32)", 42)

# 8. Try/catch
test("try/catch no error", "try { 42 } catch (e) { None }", 42)

# 9. Nested
lam.set_variable("score", 85)
test("nested if-in-block", '{grade := "pass"; score > 90 ∴ grade := "excellent"; grade}', "pass")

# 10. LAMAGUE symbols (use actual symbol characters — return callables when bare)
# These are symbol lookups that return functions; skip None check
# Just verify they don't crash
test("truth pressure Π", "Π", "skip")
test("agency μ", "μ", "skip")

# Run
failed = 0
for name, code, expected in tests:
    try:
        result = lam.eval(code)
        if expected == "skip":
            print(f"  ✓ {name} (no assert)")
        elif result == expected or (expected is None and result is None):
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}: expected {expected!r}, got {result!r}")
            failed += 1
    except Exception as e:
        print(f"  ✗ {name}: ERROR {e}")
        failed += 1

print(f"\n{'ALL PASS' if failed == 0 else f'{failed} FAILURES'}")
sys.exit(failed)
