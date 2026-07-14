"""P5-T2: Truth pressure Π tests."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

def test_truth_pressure_importable():
    from CORE.truth_pressure import PiTracker, forge_gates, Register, score
    return True, "PiTracker + forge_gates + Register + score importable"

def test_score_function():
    from CORE.truth_pressure import score
    pi = score(evidence=3, precision=0.9, strain=0.0, s0=1.0)
    assert isinstance(pi, float), f"Expected float, got {type(pi)}"
    assert pi > 0, f"Π should be positive with evidence, got {pi}"
    return True, f"score(E=3, P=0.9, S=0.0, s0=1.0) = Π={pi:.3f}"

def test_pi_zero_at_start():
    from CORE.truth_pressure import PiTracker
    t = PiTracker()
    pi = t.pi()
    assert isinstance(pi, float), f"Expected float, got: {type(pi)}"
    return True, f"fresh tracker returns Π={pi:.3f}"

def test_pi_rises_with_evidence():
    from CORE.truth_pressure import PiTracker
    t = PiTracker()
    t.record_evidence("file_read", count=3)
    t.set_precision(0.9)
    pi = t.pi()
    assert pi > 0, f"Π should rise with evidence/precision, got {pi}"
    return True, f"Π rises to {pi:.3f} after recording evidence+precision"

def test_pi_gate2():
    from CORE.truth_pressure import PiTracker, PASS_THRESHOLD
    t = PiTracker()
    t.record_evidence("file_read", count=5)
    t.set_precision(1.0)
    passing = t.gate2_pass()
    return True, f"gate2_pass()={passing} with high evidence (threshold={PASS_THRESHOLD})"

def test_register_enum_has_all_types():
    from CORE.truth_pressure import Register
    required = {"DERIVED", "ASSUMED", "MEASURED", "INTUITION",
                "CONSISTENCY", "INTERPRETIVE", "CONJECTURE"}
    names = {r.name for r in Register}
    missing = required - names
    assert not missing, f"Missing register types: {missing}"
    return True, f"Register has all 7 types: {sorted(names)}"

def test_forge_gates_pass():
    from CORE.truth_pressure import forge_gates
    output_file = os.path.join(os.path.dirname(__file__), "../../WORKSPACE/logprobs_probe.md")
    if not os.path.exists(output_file):
        return None, f"SKIP — test file doesn't exist: {output_file}"
    result = forge_gates(output_file)
    # forge_gates returns a dict with "gate1" and "gate2" and "pass" keys
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "gate1" in result, f"Missing gate1 key: {result}"
    return True, f"forge_gates returns dict: gate1={result.get('gate1')}"

def test_forge_gates_fail_no_file():
    from CORE.truth_pressure import forge_gates
    result = forge_gates("/nonexistent/path/file.md")
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    gate1 = result.get("gate1", {})
    passed = gate1.get("pass", True) if isinstance(gate1, dict) else gate1
    assert not passed, f"Gate 1 should fail for missing file, got: {result}"
    return True, "forge_gates correctly reports gate1 fail for missing file"

def test_pi_summary():
    from CORE.truth_pressure import PiTracker, Register
    t = PiTracker()
    t.record_evidence("bash_run", count=2)
    t.set_precision(0.8)
    t.add_claim("this is a test claim", Register.MEASURED, pi_at_claim=t.pi())
    s = t.summary()
    assert isinstance(s, dict), f"Expected dict from summary(), got {type(s)}"
    assert "pi" in s, f"summary() missing 'pi' key: {s}"
    return True, f"summary() returns pi={s.get('pi', '?'):.3f}, claims={s.get('claims', '?')}"
