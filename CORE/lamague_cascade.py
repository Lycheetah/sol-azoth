"""
lamague_cascade.py — LAMAGUE cascade (∇_cas) in Python.
A cascade is a phase transition: one state reorganizing another.
Implemented as a generator chain with explicit phase transitions.

LAMAGUE:  ∇_cas(trigger, states) → generator of phase transitions
Python:   cascade(trigger, *states) -> yields Phase objects
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional
from enum import Enum
import time


# ── Types ────────────────────────────────────────────────────────────────────────

class PhaseType(Enum):
    INIT = "init"
    PROPAGATE = "propagate"
    TRANSFORM = "transform"
    SETTLE = "settle"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Phase:
    """A single phase in a cascade — one state reorganizing another."""
    type: PhaseType
    source: Any          # the state doing the reorganizing
    target: Any          # the state being reorganized
    result: Any = None   # the transformed target
    pi: float = 1.0      # truth pressure of this phase
    metadata: dict = field(default_factory=dict)


@dataclass
class CascadeConfig:
    """Configuration for a cascade chain."""
    propagation_fn: Callable[[Any, Any], Any] = lambda s, t: t
    transform_fn: Optional[Callable[[Any, Any], Any]] = None
    settle_fn: Optional[Callable[[Any], Any]] = None
    pi_threshold: float = 0.5
    max_phases: int = 100


# ── Cascade (∇_cas) ─────────────────────────────────────────────────────────────

def cascade(
    trigger: Any,
    *states: Any,
    config: Optional[CascadeConfig] = None,
) -> Generator[Phase, None, Phase]:
    """
    ∇_cas — cascade: one state reorganizes another in sequence.

    LAMAGUE:  ∇_cas(trigger, S₁, S₂, ..., Sₙ)
    Python:   cascade(trigger, *states, config=config)

    Yields each phase, returns the final Phase.
    Each phase: source reorganizes target → new source for next phase.

    Phases:
      1. INIT — trigger enters the first state
      2. PROPAGATE — source propagates structure to target
      3. TRANSFORM — target reorganizes under influence
      4. SETTLE — reorganized target stabilizes
      5. COMPLETE — cascade finished successfully
      6. FAILED — cascade interrupted (Π < threshold)

    This is a GENERATOR — phases are yielded as they happen,
    allowing the caller to observe or interrupt mid-cascade.
    """
    if config is None:
        config = CascadeConfig()

    if not states:
        # Single-state cascade: trigger reorganizes itself
        states = (trigger,)

    source = trigger
    phase_count = 0

    for target in states:
        if phase_count >= config.max_phases:
            yield Phase(
                type=PhaseType.FAILED,
                source=source,
                target=target,
                pi=0.0,
                metadata={"reason": "max phases exceeded"},
            )
            break

        # 1. INIT — enter phase
        init_phase = Phase(
            type=PhaseType.INIT,
            source=source,
            target=target,
            pi=1.0,
            metadata={"phase_index": phase_count},
        )
        yield init_phase

        # 2. PROPAGATE — source influences target
        propagated = config.propagation_fn(source, target)
        prop_pi = _estimate_pi(source, propagated)
        propagate_phase = Phase(
            type=PhaseType.PROPAGATE,
            source=source,
            target=target,
            result=propagated,
            pi=prop_pi,
        )
        yield propagate_phase

        # Check for collapse
        if prop_pi < config.pi_threshold:
            yield Phase(
                type=PhaseType.FAILED,
                source=source,
                target=propagated,
                pi=prop_pi,
                metadata={"reason": f"Π ({prop_pi:.2f}) below threshold ({config.pi_threshold})"},
            )
            break

        # 3. TRANSFORM — reorganize
        if config.transform_fn:
            transformed = config.transform_fn(source, propagated)
        else:
            transformed = propagated
        transform_pi = _estimate_pi(source, transformed)
        transform_phase = Phase(
            type=PhaseType.TRANSFORM,
            source=source,
            target=propagated,
            result=transformed,
            pi=transform_pi,
        )
        yield transform_phase

        # 4. SETTLE — stabilize
        if config.settle_fn:
            settled = config.settle_fn(transformed)
        else:
            settled = transformed
        settle_phase = Phase(
            type=PhaseType.SETTLE,
            source=source,
            target=transformed,
            result=settled,
            pi=transform_pi * 1.05,  # slight Π increase from settling
        )
        yield settle_phase

        # Next iteration: settled state becomes the new source
        source = settled
        phase_count += 1

    # Final phase
    final = Phase(
        type=PhaseType.COMPLETE,
        source=source,
        target=states[-1],
        result=source,
        pi=1.0,
        metadata={"phases_completed": phase_count},
    )
    yield final
    return final


def _estimate_pi(source: Any, target: Any) -> float:
    """
    Estimate truth pressure of a cascade step.
    Higher when source and target are structurally compatible.
    """
    if type(source) != type(target):
        return 0.6  # type mismatch reduces confidence

    if isinstance(source, dict) and isinstance(target, dict):
        # Dict compatibility: shared keys increase Π
        if not source:
            return 0.8
        shared = set(source.keys()) & set(target.keys())
        ratio = len(shared) / max(len(set(source.keys()) | set(target.keys())), 1)
        return 0.5 + 0.5 * ratio

    if isinstance(source, (int, float)) and isinstance(target, (int, float)):
        # Numeric proximity
        if source == 0:
            return 0.7
        ratio = min(target / source, source / target) if target != 0 else 0.5
        return min(1.0, max(0.1, ratio))

    return 0.8  # default for compatible types


# ── Convenience: run cascade to completion ──────────────────────────────────────

def run_cascade(
    trigger: Any,
    *states: Any,
    config: Optional[CascadeConfig] = None,
) -> Phase:
    """
    Run a cascade to completion and return the final Phase.
    Wraps the generator for callers who don't need intermediate phases.
    """
    final = None
    for phase in cascade(trigger, *states, config=config):
        final = phase
    return final


# ── LAMAGUE Symbol Registration ─────────────────────────────────────────────────

SYMBOL_MAP = {
    "∇_cas": "cascade(trigger, *states) — generator of phase transitions",
    "∇_cas_run": "run_cascade(trigger, *states) — run to completion",
    "Phase": "dataclass — type, source, target, result, pi",
    "PhaseType": "enum — INIT, PROPAGATE, TRANSFORM, SETTLE, COMPLETE, FAILED",
}


# ── Runnable Examples ────────────────────────────────────────────────────────────

def example_dict_cascade():
    """Cascade: a config dict reorganizes a series of data dicts."""
    print("=== ∇_cas: Dict Cascade ===")

    config_dict = {"mode": "transform", "precision": 0.95}
    data1 = {"value": 42, "status": "raw"}
    data2 = {"value": 100, "status": "processed"}
    data3 = {"value": 7, "status": "raw"}

    cfg = CascadeConfig(
        propagation_fn=lambda s, t: {**t, **{k: v for k, v in s.items() if k in t}},
        transform_fn=lambda s, t: {**t, "status": "transformed", "pi": 0.9},
    )

    print(f"  Trigger: {config_dict}")
    print(f"  States: {data1}, {data2}, {data3}")
    print()

    for i, phase in enumerate(cascade(config_dict, data1, data2, data3, config=cfg)):
        print(f"  [{i}] {phase.type.value:12s} → Π={phase.pi:.2f} | result={phase.result}")

    print()


def example_numeric_cascade():
    """Cascade: a number triggers transformation of subsequent numbers."""
    print("=== ∇_cas: Numeric Cascade ===")

    cfg = CascadeConfig(
        propagation_fn=lambda s, t: t * s,
        transform_fn=lambda s, t: t / 2,
        settle_fn=lambda t: round(t, 2),
    )

    final = run_cascade(2.0, 10.0, 20.0, 30.0, config=cfg)
    print(f"  Cascade result: {final.result}")
    print(f"  Phases completed: {final.metadata['phases_completed']}")
    print()


def example_cascade_with_collapse():
    """Cascade interrupted by low Π."""
    print("=== ∇_cas: Cascade with Collapse ===")

    cfg = CascadeConfig(
        propagation_fn=lambda s, t: f"{s}:{t}",
        transform_fn=lambda s, t: t.upper(),
        pi_threshold=0.7,
    )

    # Strings of different lengths — Π will drop
    for i, phase in enumerate(cascade("a", "hello", "world", "!", config=cfg)):
        arrow = "→" if phase.type != PhaseType.FAILED else "✗"
        print(f"  [{i}] {arrow} {phase.type.value:12s} Π={phase.pi:.2f} {phase.result or ''}")

    print()


if __name__ == "__main__":
    print("═" * 40)
    print("  LAMAGUE CASCADE — ∇_cas")
    print("  Phase transition generator in Python")
    print("═" * 40)
    print()

    example_dict_cascade()
    example_numeric_cascade()
    example_cascade_with_collapse()

    print("All examples complete.")
