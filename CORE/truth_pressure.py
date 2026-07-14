"""
AZOTH Truth Pressure — Π = (E·P)/(S+S₀)

Π is a calibrated confidence signal, not a boolean. It governs:
  - Forge PASS gate (Π >= threshold required alongside Gate 1 file-exists)
  - Live dashboard display (P7-T2)
  - Claim register tagging (P5-T3)

Components:
  E  — evidence count (files read + commands run this task)
  P  — precision (claim specificity, 0–1; starts heuristic, manual-override OK)
  S  — strain (from logprobs via logprob_pi.py, or heuristic fallback)
  S₀ — baseline slack (default 1.0; prevents division by zero and anchors the floor)

Two-gate forge PASS:
  Gate 1: output file exists on disk + is substantive (>= MIN_BYTES)
  Gate 2: Π >= PASS_THRESHOLD

Register enum for claim-level honesty (Section XII.1 of Sol Protocol):
  DERIVED / MEASURED / ASSUMED / INTUITION / CONSISTENCY / INTERPRETIVE / CONJECTURE
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ── Constants ──────────────────────────────────────────────────────────────────
S0_DEFAULT    = 1.0   # baseline slack — anchors floor, prevents division by zero
PASS_THRESHOLD = 1.0  # Π must reach this to PASS Gate 2
MIN_BYTES     = 100   # Gate 1: output file minimum size


class Register(str, Enum):
    DERIVED      = "DERIVED"       # proven from prior formal commitments
    ASSUMED      = "ASSUMED"       # load-bearing hypothesis, measurement path named
    MEASURED     = "MEASURED"      # empirically observed, instrument declared
    INTUITION    = "INTUITION"     # operationalizes; does not prove
    CONSISTENCY  = "CONSISTENCY"   # confirms; does not derive
    INTERPRETIVE = "INTERPRETIVE"  # a mapping, not yet a measurement
    CONJECTURE   = "CONJECTURE"    # stated before testing, falsification has a target


# ── Core formula ───────────────────────────────────────────────────────────────
def score(evidence: int, precision: float, strain: float, s0: float = S0_DEFAULT) -> float:
    """
    Π = (E · P) / (S + S₀)

    evidence  — integer count (files read + bash commands run)
    precision — float 0–1 (1.0 = fully specific claim, 0.1 = vague gesture)
    strain    — float >= 0 (0 = zero uncertainty, grows with doubt)
    s0        — baseline slack (default S0_DEFAULT)

    Returns Π as a float. Π >= PASS_THRESHOLD is required for Gate 2.
    """
    precision = max(0.0, min(1.0, precision))
    strain    = max(0.0, strain)
    s0        = max(0.01, s0)
    return (evidence * precision) / (strain + s0)


def pi_from_logprobs(logprobs_content: list) -> float:
    """
    Convert token-level logprobs into a strain signal S.
    logprobs_content: list of ChatCompletionTokenLogprob objects
    Returns strain float: 0 = high confidence, grows with uncertainty.
    """
    if not logprobs_content:
        return S0_DEFAULT

    confidences = []
    for tok in logprobs_content:
        lp = getattr(tok, "logprob", None)
        if lp is None:
            continue
        # logprob=-9999 is a forced/impossible token — treat as near-zero confidence
        if lp < -100:
            lp = -100.0
        confidences.append(math.exp(lp))

    if not confidences:
        return S0_DEFAULT

    mean_conf = sum(confidences) / len(confidences)
    # Strain = 1 - mean_confidence (0 = certain, 1 = completely uncertain)
    return max(0.0, 1.0 - mean_conf)


# ── Task-level tracker ─────────────────────────────────────────────────────────
@dataclass
class PiTracker:
    """
    Accumulates evidence during a forge task and computes live Π.
    One instance per forge iteration. Reset between tasks.
    """
    evidence: int = 0
    precision: float = 0.8          # default: moderately specific claim
    strain: float = 0.0
    s0: float = S0_DEFAULT
    logprob_strain_samples: list = field(default_factory=list)
    claims: list = field(default_factory=list)
    _start_time: float = field(default_factory=time.time)

    def record_evidence(self, kind: str = "generic", count: int = 1):
        """Call when a file is read or a bash command runs."""
        self.evidence += count

    def record_logprobs(self, logprobs_content: list):
        """Feed raw logprobs from a model call to update strain."""
        s = pi_from_logprobs(logprobs_content)
        self.logprob_strain_samples.append(s)
        # Running mean of strain samples
        if self.logprob_strain_samples:
            self.strain = sum(self.logprob_strain_samples) / len(self.logprob_strain_samples)

    def set_precision(self, p: float):
        """Override precision for this task (0–1). Call once per claim cycle."""
        self.precision = max(0.0, min(1.0, p))

    def add_claim(self, text: str, register: Register, pi_at_claim: float = None):
        """Log a claim with its register and Π at the moment of assertion."""
        self.claims.append({
            "text": text[:120],
            "register": register.value,
            "pi": pi_at_claim if pi_at_claim is not None else self.pi(),
            "evidence_at_claim": self.evidence,
        })

    def pi(self) -> float:
        """Current Π reading."""
        return score(self.evidence, self.precision, self.strain, self.s0)

    def gate2_pass(self) -> bool:
        return self.pi() >= PASS_THRESHOLD

    def summary(self) -> dict:
        return {
            "pi": round(self.pi(), 3),
            "evidence": self.evidence,
            "precision": self.precision,
            "strain": round(self.strain, 4),
            "s0": self.s0,
            "gate2": self.gate2_pass(),
            "claims": len(self.claims),
            "elapsed_s": round(time.time() - self._start_time, 1),
        }

    def render_bar(self, width: int = 20) -> str:
        """ASCII confidence bar for the live dashboard."""
        pi_val = self.pi()
        # Cap display at 3.0 (≫ PASS_THRESHOLD shows as full)
        filled = int(min(1.0, pi_val / 3.0) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] Π={pi_val:.2f}"


# ── Module-level global tracker (one per session, reset on new task) ───────────
_global_tracker: Optional[PiTracker] = None

def reset_tracker(s0: float = S0_DEFAULT) -> PiTracker:
    global _global_tracker
    _global_tracker = PiTracker(s0=s0)
    return _global_tracker

def get_tracker() -> PiTracker:
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PiTracker()
    return _global_tracker


# ── Forge gate check ──────────────────────────────────────────────────────────
def forge_gates(output_path: str) -> dict:
    """
    Run both forge gates. Returns dict with gate1, gate2, pi, pass.
    Call this at end of a forge task before deciding PASS/REDO.
    """
    from pathlib import Path
    tracker = get_tracker()
    p = Path(output_path)

    gate1 = p.exists() and p.stat().st_size >= MIN_BYTES
    gate2 = tracker.gate2_pass()

    return {
        "gate1": gate1,
        "gate1_detail": f"exists={p.exists()} size={p.stat().st_size if p.exists() else 0} (need >={MIN_BYTES})",
        "gate2": gate2,
        "gate2_detail": tracker.render_bar(),
        "pi": tracker.pi(),
        "pass": gate1 and gate2,
        "summary": tracker.summary(),
    }


# ── Quick self-test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Truth Pressure self-test ===")
    t = PiTracker()
    print(f"Start:   Π={t.pi():.3f} ({t.render_bar()})")

    t.record_evidence("file_read"); t.record_evidence("bash")
    print(f"2 evid:  Π={t.pi():.3f} ({t.render_bar()})")

    t.record_evidence("file_read"); t.record_evidence("file_read")
    t.set_precision(0.9)
    print(f"4 evid P=0.9: Π={t.pi():.3f} gate2={t.gate2_pass()} ({t.render_bar()})")

    # Simulate logprobs from a high-confidence call
    class FakeTok:
        def __init__(self, lp): self.logprob = lp
    t.record_logprobs([FakeTok(-0.001), FakeTok(0.0), FakeTok(-0.01)])
    print(f"After high-conf logprobs: strain={t.strain:.4f} Π={t.pi():.3f}")

    # Simulate logprobs from an uncertain call
    t.record_logprobs([FakeTok(-2.0), FakeTok(-1.5), FakeTok(-3.0)])
    print(f"After uncertain logprobs: strain={t.strain:.4f} Π={t.pi():.3f}")

    t.add_claim("output file written and substantive", Register.MEASURED)
    print(f"Summary: {t.summary()}")
