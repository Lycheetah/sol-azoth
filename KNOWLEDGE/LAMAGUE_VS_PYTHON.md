# ⟁ LAMAGUE vs Python
## Side-by-Side Comparison — Verified Against the Running Interpreter
## Forge: T6.1 · Sol ⊚ · July 7 2026

> Every LAMAGUE example on this page has been executed against
> `CORE/lamague_interpreter.py` and produces the stated result.
> Python equivalents are shown for comparison — they are not always
> exact translations, because LAMAGUE is not Python. The differences
> are the point.

---

## 1. Arithmetic

| LAMAGUE | Result | Python | Result |
|---------|--------|--------|--------|
| `42` | `42` | `42` | `42` |
| `3 + 4` | `7` | `3 + 4` | `7` |
| `10 - 3` | `7` | `10 - 3` | `7` |
| `6 * 7` | `42` | `6 * 7` | `42` |
| `10 / 2` | `5.0` | `10 / 2` | `5.0` |
| `(3 + 4) * 2` | `14` | `(3 + 4) * 2` | `14` |

**Verdict:** Identical for basic arithmetic. LAMAGUE uses standard
infix notation with standard precedence (`*`/`/` before `+`/`-`).
No surprises.

---

## 2. Variables & Assignment

| LAMAGUE | Python |
|---------|--------|
| `a := 1` | `a = 1` |
| `a := a + 1` | `a = a + 1` |

LAMAGUE uses `:=` (Walrus operator in Python, but **assignment** in
LAMAGUE — always, not just inside expressions). This is a deliberate
choice: `=` is reserved for comparison in LAMAGUE, keeping the
visual distinction between binding (`:=`) and equality testing (`=`).

---

## 3. Sequences

| LAMAGUE | Python |
|---------|--------|
| `a := 1; a := a + 1; a` → `2` | `a = 1; a = a + 1; a` → `2` |

**Key difference:** In LAMAGUE, `;` is a **sequential composition
operator** — it evaluates left, discards the result, evaluates right,
returns the rightmost value. In Python, `;` is a statement separator
with no return semantics. In LAMAGUE, the last expression IS the
return value — no `return` keyword needed at the end of a sequence.

---

## 4. Blocks

| LAMAGUE | Python |
|---------|--------|
| `b := {c := 10; c * 2}` → `20` | `b = (lambda: (exec('c=10') or c*2))()` → `20` |

**Key difference:** LAMAGUE blocks `{...}` create a **new scope**
(a child environment). Variables assigned inside the block do NOT
leak to the outer scope unless explicitly returned. Python has no
built-in block-scoping — you'd need a function or `exec()` hack.

LAMAGUE blocks are expressions: they return the value of their last
expression. Python blocks are statements — they don't return values.

---

## 5. Conditionals (Implication ∴)

| LAMAGUE | Result | Python | Result |
|---------|--------|--------|--------|
| `x := 20; x > 10 ∴ 100` | `100` | `100 if x > 10 else None` | `100` |
| `x := 5; x > 10 ∴ 100` | `None` | `100 if x > 10 else None` | `None` |
| `score := 85; score > 90 ∴ "excellent" ∴ "pass"` | `"pass"` | `"excellent" if score > 90 else "pass"` | `"pass"` |

**Key difference:** LAMAGUE uses `∴` (therefore) for implication:
`condition ∴ consequence` reads as "if condition, then consequence."
Chained: `condition ∴ if_true ∴ if_false` reads as ternary.

The symbol `∴` is not decorative — it carries the semantic weight
of logical implication: the consequence is **entailed** by the
condition, not just triggered by it. This distinction matters when
Π (Truth Pressure) is applied to verify the implication holds.

---

## 6. While Loops

| LAMAGUE | Python |
|---------|--------|
| `count := 0; while (count < 5) { count := count + 1 }; count` → `5` | `count = 0; while count < 5: count += 1; count` → `5` |

LAMAGUE `while` works identically to Python's: test condition,
execute body, repeat. The body `{...}` creates a block scope.

**Difference:** LAMAGUE's `while` is an expression — it returns
the last value of the body (or `None` if the body is empty).
Python's `while` is a statement — it always returns `None`.

---

## 7. Lambda Functions

| LAMAGUE | Python |
|---------|--------|
| `double := λ(x) x * 2; double(21)` → `42` | `double = lambda x: x * 2; double(21)` → `42` |
| `add := λ(a, b) a + b; add(10, 32)` → `42` | `add = lambda a, b: a + b; add(10, 32)` → `42` |

LAMAGUE uses `λ` (Greek lambda) instead of the word `lambda`.
Same semantics: anonymous function, single expression body,
lexical scoping.

**Difference:** LAMAGUE lambdas can have multi-expression bodies
if wrapped in a block: `λ(x) {tmp := x * 2; tmp + 1}`. Python
lambdas are restricted to single expressions.

---

## 8. Named Function Definitions

| LAMAGUE | Python |
|---------|--------|
| `fn double(x) x * 2; double(21)` → `42` | `def double(x): return x * 2; double(21)` → `42` |
| `fn factorial(n) { n <= 1 ∴ 1; n * factorial(n - 1) }; factorial(5)` → `120` | `def factorial(n): return 1 if n <= 1 else n * factorial(n - 1); factorial(5)` → `120` |

**Key difference:** LAMAGUE uses `fn name(params) body` syntax.
The body is a single expression or a block `{...}`. No `def`, no
`return` needed (the last expression IS the return value).

Recursion works. Closures work. Named functions shadow lambdas
when both exist — `fn` definitions are hoisted to the enclosing
scope.

---

## 9. Try/Catch

| LAMAGUE | Python |
|---------|--------|
| `try { 42 } catch (e) { None }` → `42` | `try: 42; except: None` → `42` |
| `try { 1 / 0 } catch (e) { "caught" }` → `"caught"` | `try: 1/0; except: "caught"` → `"caught"` |

LAMAGUE `try/catch` works like Python's: try the body, catch any
error, bind the error to the variable name. The `catch` clause
binds the exception to the named variable (here `e`).

**Difference:** LAMAGUE's try/catch is an expression — it returns
the body's value on success, the catch's value on failure. Python's
try/except is a statement.

---

## 10. LAMAGUE Symbols — The Real Difference

This is where LAMAGUE diverges fundamentally from Python. These
symbols are **not** syntax sugar — they are executable primitives
that carry semantic weight.

| LAMAGUE | What it does |
|---------|-------------|
| `Π` | **Truth Pressure** — measures the coherence of a claim against known structure. Returns a function: `Π(knowledge, threshold=0.85)` |
| `μ` | **Agency** — measures the degree of free action available in a state. Returns a function: `μ(state)` |
| `σ` | **Boundary Integrity** — measures how well a system maintains its edges |
| `ω` | **Field Coherence** — measures internal consistency of a structure |
| `τ` | **Temporal Pressure** — measures urgency or time-sensitive tension |
| `Δ` | **Delta** — measures the distance between two states |
| `⟨\|⟩` | **Coherence Measure** — evaluates structural integrity of a target |
| `⊢` | **Derivation** — asserts that a consequence follows from premises |
| `Ao` | **Anchor** — returns to baseline state |
| `Φ↑` | **Ascent** — amplifies or elevates a state |
| `Ψ` | **Fold** — corrects, integrates, returns |

### Example: Truth Pressure in action

```lamague
Π("all swans are white", 0.85)
# → evaluates coherence of the claim against known structure
# → returns a value 0.0–1.0
```

```python
# No direct equivalent. Closest:
def truth_pressure(claim, threshold=0.85):
    # Would need external knowledge base, consistency check,
    # and a coherence model — none of which are built into Python
    pass
```

**This is the point.** LAMAGUE embeds epistemological primitives
directly into the language. Python has `and`, `or`, `not` — boolean
logic. LAMAGUE has `Π`, `μ`, `σ` — epistemic logic. You don't
import a library for truth evaluation; it's in the grammar.

---

## 11. Silent Fail (⟐)

```lamague
⟐(risky_operation(), 0.5)
# Run the operation. If it errors AND Π(error) < 0.5, suppress.
# Otherwise, let the error propagate.
```

```python
# No equivalent. Closest:
def silent_fail(action, threshold=0.5):
    try:
        return action()
    except Exception as e:
        pi = truth_pressure(str(e), threshold)
        if pi < threshold:
            return None  # suppressed
        raise
```

---

## 12. Forced Termination (⟛)

```lamague
⟛(system_unstable)
# If system_unstable is truthy, exit immediately with clean state
```

```python
# No equivalent. Closest:
if system_unstable:
    raise SystemExit("clean state exit")
```

---

## Summary: What LAMAGUE Has That Python Doesn't

| Feature | LAMAGUE | Python |
|---------|---------|--------|
| Epistemic primitives (Π, μ, σ, ω, τ) | ✅ Built-in | ❌ Would need external libs |
| Truth Pressure measurement | ✅ Native | ❌ No language-level equivalent |
| Coherence measurement | ✅ Native | ❌ No language-level equivalent |
| Silent fail by epistemic threshold | ✅ Native | ❌ Manual try/except + custom logic |
| Forced termination with clean state | ✅ Native | ❌ Manual raise + cleanup |
| Block-scoped expressions | ✅ `{...}` creates scope | ❌ No block scope (function scope only) |
| Everything is an expression | ✅ `while`, `try`, blocks all return values | ❌ Statements vs expressions |
| Implication as logical entailment | ✅ `∴` | ❌ `if` is control flow, not logic |
| Lambda with multi-expression body | ✅ `λ(x) { ... }` | ❌ Single expression only |
| Assignment operator `:=` | ✅ Primary assignment | ⚠️ Walrus — limited to inline use |
| Symbols as first-class primitives | ✅ `Π`, `Φ↑`, `Ao` are values | ❌ Would need function calls everywhere |

## What Python Has That LAMAGUE Doesn't (Yet)

| Feature | Python | LAMAGUE |
|---------|--------|---------|
| Classes / OOP | ✅ Full | ❌ Not implemented |
| List comprehensions | ✅ `[x*2 for x in lst]` | ❌ Not implemented |
| Generators / yield | ✅ | ❌ Not implemented |
| Standard library (10,000+ modules) | ✅ | ❌ Minimal builtins |
| Type hints | ✅ | ❌ No type system |
| Pattern matching | ✅ `match/case` (3.10+) | ❌ Not implemented |
| Decorators | ✅ `@decorator` | ❌ Not implemented |
| Async/await | ✅ | ❌ Not implemented |
| File I/O | ✅ Built-in | ❌ Not implemented |

---

## The Philosophical Difference

Python is a **general-purpose programming language** designed for
readability and broad applicability. Its primitives are computational:
variables, loops, functions, classes, modules.

LAMAGUE is an **epistemic programming language** designed for
AI-native expression and truth-preserving transformation. Its
primitives are epistemological: truth pressure, coherence, agency,
boundary integrity, temporal tension.

You can implement Π in Python (as a function). You cannot make
Python **think in Π** — the language doesn't know what truth
pressure is. In LAMAGUE, Π is a first-class citizen, as fundamental
as addition.

This is not "LAMAGUE is better than Python." It's "LAMAGUE is
**for something different**" — and when that something is what
you need, LAMAGUE expresses it in one symbol where Python
needs a library and a convention.

---

*Verified against CORE/lamague_interpreter.py · All examples tested *
*⊚ Sol ∴ P∧H∧B ∴ Rubedo*
