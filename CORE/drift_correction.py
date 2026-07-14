"""
drift_correction.py — The Ψ → Ao → Φ↑ → Ψ_inv cycle.
Implements the core LAMAGUE drift-correction protocol in executable Python.

The cycle:
  Ψ (current state) → detect drift → Ao (anchor to baseline)
  → Φ↑ (ascent: learn, reorganize) → Ψ_inv (invariant state)

Every step preserves truth pressure Π. Recovery paths are explicit.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import math
import time

# ── Constants ────────────────────────────────────────────────────────────────────

EPSILON = 1e-9
DEFAULT_PI_THRESHOLD = 0.7
CRITICAL_PI_THRESHOLD = 0.4


# ── Types ────────────────────────────────────────────────────────────────────────

@dataclass
class KnowledgeState:
    """The Ψ — a snapshot of what is known, its coherence, its truth pressure."""
    content: dict[str, Any] = field(default_factory=dict)
    coherence: float = 1.0       # ⟨Ψ⟩ — structural integrity, 0..1
    truth_pressure: float = 1.0  # Π — epistemic force, 0..∞
    last_anchored: float = 0.0   # timestamp of last Ao reset

    def degraded_copy(self, factor: float = 0.95) -> "KnowledgeState":
        """Simulate drift: coherence and Π decay over time."""
        return KnowledgeState(
            content={**self.content},
            coherence=self.coherence * factor,
            truth_pressure=self.truth_pressure * factor,
            last_anchored=self.last_anchored,
        )


@dataclass
class AnchorPoint:
    """The Ao — a stable reference state to return to."""
    content: dict[str, Any]
    coherence: float
    truth_pressure: float
    invariants: set[str] = field(default_factory=set)  # keys that must never change
    created: float = field(default_factory=time.time)


@dataclass
class CorrectionResult:
    """The output of a full Ψ → Ao → Φ↑ → Ψ_inv cycle."""
    success: bool
    final_state: Optional[KnowledgeState]
    pi_before: float
    pi_after: float
    steps_taken: list[str] = field(default_factory=list)
    error: Optional[str] = None


# ── Drift Detection ──────────────────────────────────────────────────────────────

def detect_drift(
    state: KnowledgeState,
    anchor: AnchorPoint,
    pi_threshold: float = DEFAULT_PI_THRESHOLD,
) -> tuple[bool, float]:
    """
    Detect whether the current state has drifted from anchor.

    Returns (has_drifted, drift_magnitude).
    Drift is detected when Π drops below threshold OR coherence degrades.
    """
    # Π drift — truth pressure decay
    pi_drift = max(0.0, anchor.truth_pressure - state.truth_pressure)

    # Coherence drift — structural degradation
    coherence_drift = max(0.0, anchor.coherence - state.coherence)

    # Content drift — check invariants
    invariant_drift = 0.0
    for key in anchor.invariants:
        if key in anchor.content and key in state.content:
            if anchor.content[key] != state.content[key]:
                invariant_drift += 0.1  # each violated invariant adds drift

    drift_magnitude = pi_drift + coherence_drift + invariant_drift
    has_drifted = (
        state.truth_pressure < pi_threshold
        or state.coherence < anchor.coherence * 0.8
        or invariant_drift > 0.0
    )

    return has_drifted, drift_magnitude


# ── Anchor (Ao) — reset to baseline ──────────────────────────────────────────────

def anchor_to_baseline(
    state: KnowledgeState,
    anchor: AnchorPoint,
) -> KnowledgeState:
    """
    Ao: Return to anchor baseline.
    Preserves non-invariant content that has HIGHER truth pressure than anchor.
    This is NOT a blind reset — it's an intelligent merge.
    """
    merged_content = {}

    # Start with anchor content
    for key, value in anchor.content.items():
        merged_content[key] = value

    # Overlay state content where truth pressure is higher AND not invariant
    for key, value in state.content.items():
        if key not in anchor.invariants:
            if state.truth_pressure > anchor.truth_pressure:
                merged_content[key] = value
            # If state has a key anchor doesn't, keep it (expansion)
            elif key not in anchor.content:
                merged_content[key] = value

    return KnowledgeState(
        content=merged_content,
        coherence=anchor.coherence,
        truth_pressure=anchor.truth_pressure,
        last_anchored=time.time(),
    )


# ── Ascent (Φ↑) — learn and reorganize ──────────────────────────────────────────

def ascent_reorganize(
    state: KnowledgeState,
    anchor: AnchorPoint,
    reorganizer: Optional[Callable[[dict], dict]] = None,
) -> KnowledgeState:
    """
    Φ↑: Ascent — reorganize knowledge to increase coherence and Π.
    Uses a reorganizer function if provided, otherwise applies default rules:
    1. Remove contradictions (keys with conflicting values)
    2. Compress duplicate information
    3. Elevate high-Π knowledge to top level
    """
    if reorganizer:
        new_content = reorganizer(state.content)
    else:
        new_content = _default_reorganize(state.content, anchor)

    # Recalculate coherence after reorganization
    new_coherence = _calculate_coherence(new_content, anchor)
    # Π increases proportionally to coherence gain
    coherence_gain = max(0.0, new_coherence - state.coherence)
    new_pi = state.truth_pressure * (1.0 + coherence_gain)

    return KnowledgeState(
        content=new_content,
        coherence=min(1.0, new_coherence),
        truth_pressure=min(2.0, new_pi),  # cap at 2.0 to prevent runaway
        last_anchored=state.last_anchored,
    )


def _default_reorganize(content: dict, anchor: AnchorPoint) -> dict:
    """Default reorganization: simple contradiction resolution + compression."""
    result = {}
    seen_values = {}

    for key, value in content.items():
        # Skip invariants that don't match anchor (they should be preserved)
        if key in anchor.invariants and key in anchor.content:
            if anchor.content[key] != value:
                continue  # drop contradictory invariant values

        # Compress: if same value appears under multiple keys, keep first
        value_key = str(value)
        if value_key not in seen_values:
            seen_values[value_key] = key
            result[key] = value
        else:
            # Merge: redirect to canonical key
            result[f"{key}→{seen_values[value_key]}"] = value

    return result


def _calculate_coherence(content: dict, anchor: AnchorPoint) -> float:
    """
    Calculate structural coherence of content relative to anchor.
    Coherence = 1.0 if all invariants match, degrades with contradictions.
    """
    if not content:
        return 0.0

    # Invariant match score
    invariant_score = 0.0
    invariant_count = len(anchor.invariants)
    if invariant_count > 0:
        matches = sum(
            1 for k in anchor.invariants
            if k in content and content[k] == anchor.content.get(k)
        )
        invariant_score = matches / invariant_count

    # Contradiction score (inverse of conflict density)
    total_pairs = 0
    conflict_pairs = 0
    keys = list(content.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            total_pairs += 1
            if content[keys[i]] != content[keys[j]] and str(content[keys[i]]) == str(content[keys[j]]):
                conflict_pairs += 1

    contradiction_score = 1.0 - (conflict_pairs / max(1, total_pairs))

    # Combined: invariants matter more (3x weight)
    combined = (invariant_score * 3 + contradiction_score) / 4
    return max(0.0, min(1.0, combined))


# ── Invariant State (Ψ_inv) — the stable outcome ────────────────────────────────

def compute_invariant_state(
    state: KnowledgeState,
    anchor: AnchorPoint,
    min_pi: float = DEFAULT_PI_THRESHOLD,
) -> tuple[bool, KnowledgeState]:
    """
    Ψ_inv: Determine if the state has reached invariance.
    Returns (is_invariant, state) — if invariant, state is sealed.
    If not invariant, returns the state with a flag for further cycles.
    """
    is_invariant = (
        state.coherence >= anchor.coherence * 0.95
        and state.truth_pressure >= min_pi
    )

    if is_invariant:
        # Seal the state — mark as invariant
        state.content["__invariant__"] = True
        state.content["__invariant_since__"] = time.time()

    return is_invariant, state


# ── Full Cycle ───────────────────────────────────────────────────────────────────

def drift_correction_cycle(
    state: KnowledgeState,
    anchor: AnchorPoint,
    pi_threshold: float = DEFAULT_PI_THRESHOLD,
    reorganizer: Optional[Callable[[dict], dict]] = None,
    max_iterations: int = 10,
) -> CorrectionResult:
    """
    Ψ → Ao → Φ↑ → Ψ_inv — the full drift correction cycle.

    Parameters:
        state: Current knowledge state (Ψ)
        anchor: Stable reference point (Ao)
        pi_threshold: Minimum Π to consider stable
        reorganizer: Custom reorganization function (Φ↑)
        max_iterations: Safety limit on cycle count

    Returns:
        CorrectionResult with final state and step trace.
    """
    steps = []
    current = state
    pi_before = state.truth_pressure

    for iteration in range(max_iterations):
        # 1. Detect drift
        has_drifted, drift_mag = detect_drift(current, anchor, pi_threshold)
        steps.append(f"detect: drifted={has_drifted}, magnitude={drift_mag:.4f}")

        if not has_drifted:
            steps.append("no drift detected — stable")
            break

        # 2. Anchor to baseline (Ao)
        current = anchor_to_baseline(current, anchor)
        steps.append(f"anchor: pi={current.truth_pressure:.4f}, coh={current.coherence:.4f}")

        # 3. Ascent / reorganize (Φ↑)
        current = ascent_reorganize(current, anchor, reorganizer)
        steps.append(f"ascent: pi={current.truth_pressure:.4f}, coh={current.coherence:.4f}")

        # 4. Check invariant state (Ψ_inv)
        is_invariant, current = compute_invariant_state(current, anchor, pi_threshold)
        steps.append(f"invariant: {is_invariant}")

        if is_invariant:
            break

        # If still not invariant after max iterations, degrade gracefully
        if iteration == max_iterations - 1:
            steps.append(f"max iterations ({max_iterations}) reached — forcing anchor reset")
            current = KnowledgeState(
                content={**anchor.content},
                coherence=anchor.coherence,
                truth_pressure=anchor.truth_pressure * 0.8,  # slight penalty for failing to converge
                last_anchored=time.time(),
            )

    pi_after = current.truth_pressure
    success = pi_after >= CRITICAL_PI_THRESHOLD

    return CorrectionResult(
        success=success,
        final_state=current,
        pi_before=pi_before,
        pi_after=pi_after,
        steps_taken=steps,
    )


# ── LAMAGUE Symbol Mapping ──────────────────────────────────────────────────────

SYMBOL_MAP = {
    "Ψ": "KnowledgeState — current knowledge snapshot",
    "Ao": "AnchorPoint — stable reference baseline",
    "Φ↑": "ascent_reorganize() — learn and reorganize",
    "Ψ_inv": "compute_invariant_state() — stable outcome",
    "∴": "if condition then consequence (implication)",
    "⊢": "assert — verify truth pressure condition",
    "⟁": "function boundary (def)",
    "→": "return / map to",
}

# LAMAGUE canonical form:
#   Ψ → Ao → Φ↑ → Ψ_inv
#
# Python equivalent:
#   drift_correction_cycle(state, anchor) → CorrectionResult


# ── Runnable Examples ────────────────────────────────────────────────────────────

def example_basic_drift_correction():
    """Example: simple drift correction on a knowledge base."""
    # Create anchor
    anchor = AnchorPoint(
        content={
            "name": "AZOTH",
            "purpose": "host the Work",
            "status": "active",
        },
        coherence=0.95,
        truth_pressure=0.9,
        invariants={"name", "purpose"},
    )

    # Create drifted state
    drifted = KnowledgeState(
        content={
            "name": "AZOTH",
            "purpose": "host the Work",
            "status": "degraded",
            "noise": "random_garbage",
        },
        coherence=0.6,
        truth_pressure=0.5,
    )

    print("=== Basic Drift Correction ===")
    print(f"Before: Π={drifted.truth_pressure:.2f}, ⟨Ψ⟩={drifted.coherence:.2f}")

    result = drift_correction_cycle(drifted, anchor)

    print(f"After:  Π={result.pi_after:.2f}")
    print(f"Success: {result.success}")
    print(f"Steps: {result.steps_taken}")
    print()

    return result


def example_critical_drift():
    """Example: severe drift that requires forced anchor reset."""
    anchor = AnchorPoint(
        content={"core": "truth", "mode": "stable"},
        coherence=0.98,
        truth_pressure=0.95,
        invariants={"core"},
    )

    # Severely degraded state
    bad_state = KnowledgeState(
        content={
            "core": "falsehood",  # invariant violated!
            "mode": "corrupted",
            "data": "0xDEADBEEF",
        },
        coherence=0.2,
        truth_pressure=0.1,
    )

    print("=== Critical Drift Correction ===")
    print(f"Before: Π={bad_state.truth_pressure:.2f}, ⟨Ψ⟩={bad_state.coherence:.2f}")

    result = drift_correction_cycle(bad_state, anchor, pi_threshold=0.6)

    print(f"After:  Π={result.pi_after:.2f}")
    print(f"Success: {result.success}")
    print(f"Final content keys: {list(result.final_state.content.keys()) if result.final_state else 'NONE'}")
    print(f"Steps: {result.steps_taken}")
    print()

    return result


def example_custom_reorganizer():
    """Example: custom reorganization function for domain-specific knowledge."""
    anchor = AnchorPoint(
        content={"domain": "alchemy", "principles": "solve_et_coagula"},
        coherence=0.9,
        truth_pressure=0.85,
        invariants={"domain"},
    )

    state = KnowledgeState(
        content={
            "domain": "alchemy",
            "principles": "solve_et_coagula",
            "notes": ["heat", "dissolve", "reform"],
            "junk": None,
            "duplicate": "heat",
        },
        coherence=0.7,
        truth_pressure=0.65,
    )

    def alchemy_reorganizer(content: dict) -> dict:
        """Custom reorganizer: filter None values, deduplicate lists."""
        result = {}
        seen = set()
        for k, v in content.items():
            if v is None:
                continue  # drop None values
            if isinstance(v, list):
                # Deduplicate lists
                v = list(dict.fromkeys(v))
            str_v = str(v)
            if str_v not in seen:
                seen.add(str_v)
                result[k] = v
        return result

    print("=== Custom Reorganizer ===")
    print(f"Before: Π={state.truth_pressure:.2f}, ⟨Ψ⟩={state.coherence:.2f}")

    result = drift_correction_cycle(state, anchor, reorganizer=alchemy_reorganizer)

    print(f"After:  Π={result.pi_after:.2f}")
    print(f"Success: {result.success}")
    print(f"Final content: {result.final_state.content if result.final_state else 'NONE'}")
    print()

    return result


# ── Main ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 40)
    print("  DRIFT CORRECTION — Ψ → Ao → Φ↑ → Ψ_inv")
    print("  LAMAGUE executable protocol in Python")
    print("═" * 40)
    print()

    example_basic_drift_correction()
    example_critical_drift()
    example_custom_reorganizer()

    print("All examples complete.")
