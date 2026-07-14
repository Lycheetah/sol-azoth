"""
lamague_iteration.py — LAMAGUE iteration (↻) and collapse (↯) in Python.
Part of: Topic 3 — LAMAGUE as a coding language.
"""

from typing import Any, Callable, TypeVar, Optional
import functools

T = TypeVar("T")


# ── ↻ (Iteration) ───────────────────────────────────────────────────────────────

def iterate(f: Callable[[T], T], n: int, x: T) -> T:
    """
    ↻(f, n, x) — apply f to x, n times.

    LAMAGUE:  ↻(f, n, x) → y
    Python:   iterate(f, n, x) -> result

    This is NOT functools.reduce — reduce takes an iterable.
    ↻ is pure iteration: apply f, take result, apply f again.
    """
    if n < 0:
        raise ValueError(f"↻ requires n >= 0, got {n}")
    if n == 0:
        return x
    result = x
    for _ in range(n):
        result = f(result)
    return result


def iterate_with_trace(f: Callable[[T], T], n: int, x: T) -> list[T]:
    """
    ↻ with trace — returns all intermediate states.
    Useful for debugging and observing convergence.
    """
    if n < 0:
        raise ValueError(f"↻ requires n >= 0, got {n}")
    states = [x]
    result = x
    for _ in range(n):
        result = f(result)
        states.append(result)
    return states


# ── ↻ with convergence check ────────────────────────────────────────────────────

def iterate_until(
    f: Callable[[T], T],
    x: T,
    condition: Callable[[T], bool],
    max_iterations: int = 100,
) -> tuple[T, int]:
    """
    ↻ with early termination — iterate until condition is met.

    LAMAGUE:  ↻(f, x, condition) → (result, iterations)
    Python:   iterate_until(f, x, condition, max_iterations)

    Returns (final_state, iterations_taken).
    """
    result = x
    for i in range(max_iterations):
        if condition(result):
            return result, i
        result = f(result)
    return result, max_iterations


# ── ↯ (Collapse) ────────────────────────────────────────────────────────────────

class Collapse(Exception):
    """
    ↯ — LAMAGUE collapse exception.
    Raised when a computation cannot continue coherently.
    Carries the last valid state and the reason for collapse.
    """
    def __init__(self, state: Any, reason: str, pi: float = 0.0):
        self.state = state
        self.reason = reason
        self.pi = pi
        super().__init__(f"↯ Collapse: {reason} (Π={pi:.2f})")


def collapse_detect(
    state: Any,
    pi: float,
    threshold: float = 0.4,
    reason: str = "truth pressure below critical threshold",
) -> None:
    """
    Detect collapse condition and raise if triggered.

    LAMAGUE:  ⊢ Π(state) > threshold  →  ↯ if not
    Python:   collapse_detect(state, pi, threshold)

    This is the LAMAGUE equivalent of an assertion that can
    carry structured recovery information.
    """
    if pi < threshold:
        raise Collapse(state=state, reason=reason, pi=pi)


def collapse_recover(
    operation: Callable[[], T],
    anchor: T,
    fallback: Optional[Callable[[Collapse], T]] = None,
) -> T:
    """
    ↯ recovery — run operation, catch Collapse, recover via Ao (anchor).

    LAMAGUE:  ⟐(operation, anchor) → result
    Python:   collapse_recover(operation, anchor, fallback)

    This is the LAMAGUE try/except:
      try: operation()
      except Collapse: anchor_to_baseline()
    """
    try:
        return operation()
    except Collapse as c:
        if fallback:
            return fallback(c)
        # Default: return anchor (Ao)
        return anchor


# ── LAMAGUE Symbol Registration ─────────────────────────────────────────────────

SYMBOL_MAP = {
    "↻": "iterate(f, n, x) — apply f n times",
    "↻_trace": "iterate_with_trace(f, n, x) — all intermediate states",
    "↻_until": "iterate_until(f, x, condition) — iterate until condition",
    "↯": "Collapse — exception carrying state + reason + Π",
    "↯_detect": "collapse_detect(state, pi, threshold) — raise if below threshold",
    "↯_recover": "collapse_recover(op, anchor) — try/except with Ao fallback",
    "⟐": "collapse_recover (silent fail wrapper)",
}


# ── Runnable Examples ────────────────────────────────────────────────────────────

def example_iteration():
    """Basic ↻: apply a transformation n times."""
    print("=== ↻ (Iteration) ===")

    # Double a number 5 times
    double = lambda x: x * 2
    result = iterate(double, 5, 1)
    print(f"  ↻(double, 5, 1) = {result}")  # 32

    # With trace
    trace = iterate_with_trace(double, 5, 1)
    print(f"  ↻_trace(double, 5, 1) = {trace}")

    # Convergence check
    def converge(x: float) -> float:
        return (x + 5 / x) / 2  # Newton's method for sqrt(5)

    result, iters = iterate_until(converge, 1.0, lambda x: abs(x * x - 5) < 0.0001)
    print(f"  sqrt(5) ≈ {result:.6f} in {iters} iterations")
    print()


def example_collapse():
    """↯ (Collapse) with recovery."""
    print("=== ↯ (Collapse) ===")

    # Simulate a computation that might collapse
    anchor = {"value": 0, "status": "safe"}

    def risky_operation():
        state = {"value": 100, "status": "computed"}
        pi = 0.3  # Below threshold!
        collapse_detect(state, pi, threshold=0.5, reason="low confidence")
        return state

    try:
        result = risky_operation()
        print(f"  Success: {result}")
    except Collapse as c:
        print(f"  ↯ caught: {c}")

    # With recovery
    result = collapse_recover(risky_operation, anchor)
    print(f"  Recovered: {result}")

    # With custom fallback
    def fallback(c: Collapse):
        return {"value": c.state["value"], "status": "recovered", "pi": c.pi}

    result = collapse_recover(risky_operation, anchor, fallback)
    print(f"  Custom recovery: {result}")
    print()


def example_combined():
    """↻ + ↯ together — iterate with collapse detection."""
    print("=== Combined: ↻ with ↯ detection ===")

    anchor = 0
    pi_threshold = 0.5

    def safe_double(x: int) -> int:
        """Double, but collapse if result exceeds 100."""
        result = x * 2
        # Simulate Π decreasing as values grow
        pi = max(0.0, 1.0 - result / 200)
        collapse_detect(result, pi, pi_threshold, f"value {result} too large")
        return result

    # This will iterate until collapse
    try:
        result = iterate(safe_double, 20, 1)
        print(f"  ↻ completed: {result}")
    except Collapse as c:
        print(f"  ↻ interrupted by ↯ at state={c.state}: {c.reason}")

    # With recovery — iterate until collapse, then anchor
    def guarded_iterate():
        return iterate(safe_double, 20, 1)

    recovered = collapse_recover(guarded_iterate, anchor)
    print(f"  After ↯ recovery: {recovered}")
    print()


if __name__ == "__main__":
    print("═" * 40)
    print("  LAMAGUE ITERATION + COLLAPSE")
    print("  ↻ and ↯ in executable Python")
    print("═" * 40)
    print()

    example_iteration()
    example_collapse()
    example_combined()

    print("All examples complete.")
