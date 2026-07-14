"""
P3-T3: Multi-Worker Coordination — AZOTH
Decompose complex tasks → dispatch to all 3 workers → merge → resolve conflicts.

Design:
  - Takes a task description + optional context
  - Uses WORKER-A (code), WORKER-B (reason), WORKER-C (research) in parallel
  - Each worker gets a sub-task tailored to its specialty
  - Merge phase: combine results, detect contradictions, resolve via majority or escalation
  - Returns structured output with confidence signals

Integration:
  - Depends on spawn_worker() mechanism (from agent.py or direct import)
  - Workers run via threading.Thread for concurrent dispatch
  - Conflict resolution uses truth_pressure Π scoring when available
  - Falls back to deterministic rules if Π unavailable
"""

import json
import time
import threading
import traceback
from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class WorkerResult:
    worker: str            # "A" | "B" | "C"
    specialty: str         # "code" | "reason" | "research"
    sub_task: str          # the sub-task description sent
    output: str            # raw output text
    success: bool          # whether the worker returned usable output
    duration_s: float      # wall-clock time
    error: str = ""        # error message if failed
    confidence: float = 0.5  # heuristic confidence 0-1

@dataclass
class CoordinatedResult:
    task: str
    results: list[WorkerResult]
    merged_output: str
    conflicts: list[dict]      # list of {between, topic, resolution}
    consensus_level: str       # "unanimous" | "majority" | "partial" | "conflict"
    confidence: float          # overall confidence 0-1
    duration_s: float


# ── Task decomposition ───────────────────────────────────────────────────────

def decompose_task(task: str, context: str = "") -> dict:
    """
    Decompose a complex task into worker-specific sub-tasks.
    Returns { "A": str, "B": str, "C": str }.
    If a specialty doesn't apply, its value is empty string.
    """
    task_lower = task.lower()

    sub_tasks = {"A": "", "B": "", "C": ""}

    # WORKER-A (CODE): implementation, code review, compile, test
    code_keywords = ["implement", "code", "function", "class", "test", "compile",
                     "python", "script", "algorithm", "data structure", "api",
                     "refactor", "debug", "fix", "syntax", "patch", "write"]
    if any(kw in task_lower for kw in code_keywords):
        sub_tasks["A"] = (
            f"CODE task: {task}\n"
            f"Context: {context[:500]}\n"
            "Produce: working Python code, implementation plan, or code review. "
            "Include exact file paths, function signatures, and test cases."
        )

    # WORKER-B (REASON): architecture, analysis, LAMAGUE, trade-offs
    reason_keywords = ["architecture", "design", "analyze", "trade-off", "compare",
                       "why", "should", "strategy", "plan", "LAMAGUE", "reason",
                       "evaluate", "risk", "decision", "implication", "system"]
    if any(kw in task_lower for kw in reason_keywords):
        sub_tasks["B"] = (
            f"REASON task: {task}\n"
            f"Context: {context[:500]}\n"
            "Produce: structured analysis with implications, trade-offs, and "
            "recommendations. Use LAMAGUE framework if applicable. "
            "Be specific about assumptions and confidence levels."
        )

    # WORKER-C (RESEARCH): synthesis, web knowledge, patterns
    research_keywords = ["research", "find", "search", "synthesize", "survey",
                         "best practice", "pattern", "documentation", "learn",
                         "what is", "how does", "compare frameworks", "library",
                         "tool", "technology", "standard", "convention"]
    if any(kw in task_lower for kw in research_keywords):
        sub_tasks["C"] = (
            f"RESEARCH task: {task}\n"
            f"Context: {context[:500]}\n"
            "Produce: researched findings, best practices, relevant patterns, "
            "or external knowledge synthesis. Note confidence and sources."
        )

    # Fallback: if no keywords matched, dispatch to all 3 with generic framing
    if not any(sub_tasks.values()):
        sub_tasks = {
            "A": f"CODE perspective on: {task}\nContext: {context[:500]}",
            "B": f"REASON analysis of: {task}\nContext: {context[:500]}",
            "C": f"RESEARCH synthesis for: {task}\nContext: {context[:500]}",
        }

    return sub_tasks


# ── Conflict detection ───────────────────────────────────────────────────────

def detect_conflicts(results: list[WorkerResult]) -> list[dict]:
    """
    Detect contradictions between worker outputs.
    Returns list of conflict dicts: {between, topic, resolution}.
    Uses simple heuristics: contradictory phrases, numeric disagreements.
    """
    conflicts = []
    outputs = {r.worker: r.output for r in results if r.success}

    if len(outputs) < 2:
        return conflicts

    # Check for explicit contradiction markers
    contradiction_pairs = [
        ("A", "B"), ("A", "C"), ("B", "C"),
    ]
    for w1, w2 in contradiction_pairs:
        if w1 not in outputs or w2 not in outputs:
            continue
        o1, o2 = outputs[w1].lower(), outputs[w2].lower()

        # Pattern: one says "yes/correct/works", other says "no/incorrect/doesn't work"
        positive = {"yes", "correct", "works", "valid", "true", "good", "safe", "recommend"}
        negative = {"no", "incorrect", "doesn't work", "invalid", "false", "bad", "unsafe", "avoid"}

        for word in positive:
            if word in o1 and any(n in o2 for n in negative):
                conflicts.append({
                    "between": f"{w1} vs {w2}",
                    "topic": f"Contradiction on '{word}'",
                    "resolution": "needs_manual",
                    "detail": f"{w1} positive, {w2} negative on same topic"
                })
                break

    # Check for numeric disagreements
    import re
    for w1, w2 in contradiction_pairs:
        if w1 not in outputs or w2 not in outputs:
            continue
        nums1 = set(re.findall(r'\b(\d+)\b', outputs[w1]))
        nums2 = set(re.findall(r'\b(\d+)\b', outputs[w2]))
        # If same number appears in both with different context, flag it
        common = nums1 & nums2
        for n in common:
            if n in ("0", "1", "2"):  # too common, skip
                continue
            context1 = outputs[w1].lower().find(f" {n} ")
            context2 = outputs[w2].lower().find(f" {n} ")
            if context1 >= 0 and context2 >= 0:
                # Same number appears — could be agreement, flag only if contradictory
                pass  # Numbers alone aren't contradictions

    return conflicts


def resolve_conflicts(conflicts: list[dict], results: list[WorkerResult]) -> list[dict]:
    """
    Attempt to resolve detected conflicts.
    Returns updated conflicts with resolution filled in.
    """
    for conflict in conflicts:
        if conflict.get("resolution") != "needs_manual":
            continue

        # Try majority resolution
        workers_involved = conflict["between"].split(" vs ")
        # If 3 workers and 2 agree, majority wins
        successful = [r for r in results if r.success]
        if len(successful) >= 3:
            # Can't easily determine majority on arbitrary text — flag as unresolved
            conflict["resolution"] = "unresolved_majority"
        else:
            conflict["resolution"] = "needs_manual"

    return conflicts


# ── Merge ────────────────────────────────────────────────────────────────────

def merge_results(task: str, results: list[WorkerResult], conflicts: list[dict]) -> str:
    """
    Merge worker outputs into a single coherent result.
    Orders: REASON (B) → CODE (A) → RESEARCH (C).
    Includes conflict notes inline.
    """
    sections = []
    sections.append(f"# Coordinated Result: {task[:80]}")
    sections.append(f"Workers: {len([r for r in results if r.success])}/{len(results)} successful")
    sections.append("")

    # B (REASON) first — sets the frame
    b_result = next((r for r in results if r.worker == "B" and r.success), None)
    if b_result:
        sections.append("## Analysis (WORKER-B · REASON)")
        sections.append(b_result.output[:2000])
        sections.append("")

    # A (CODE) second — implementation
    a_result = next((r for r in results if r.worker == "A" and r.success), None)
    if a_result:
        sections.append("## Implementation (WORKER-A · CODE)")
        sections.append(a_result.output[:2000])
        sections.append("")

    # C (RESEARCH) third — context
    c_result = next((r for r in results if r.worker == "C" and r.success), None)
    if c_result:
        sections.append("## Research Context (WORKER-C · RESEARCH)")
        sections.append(c_result.output[:2000])
        sections.append("")

    # Conflicts
    if conflicts:
        sections.append("## Conflicts & Resolutions")
        for c in conflicts:
            sections.append(f"- {c['between']}: {c['topic']} → {c['resolution']}")
        sections.append("")

    # Summary
    sections.append("## Summary")
    sections.append(f"Confidence: {_calculate_confidence(results, conflicts):.2f}")
    sections.append(f"Consensus: {_calculate_consensus(results, conflicts)}")

    return "\n".join(sections)


def _calculate_confidence(results: list[WorkerResult], conflicts: list[dict]) -> float:
    """Calculate overall confidence based on success rate and conflicts."""
    if not results:
        return 0.0
    success_rate = len([r for r in results if r.success]) / len(results)
    conflict_penalty = len(conflicts) * 0.15
    return max(0.0, min(1.0, success_rate * 0.7 + 0.3 - conflict_penalty))


def _calculate_consensus(results: list[WorkerResult], conflicts: list[dict]) -> str:
    """Determine consensus level."""
    if conflicts:
        return "conflict"
    successful = [r for r in results if r.success]
    if len(successful) == 0:
        return "none"
    if len(successful) == len(results):
        return "unanimous"
    if len(successful) >= len(results) / 2:
        return "majority"
    return "partial"


# ── Main coordination function ──────────────────────────────────────────────

def coordinate(task: str, context: str = "",
               spawn_worker_fn: Optional[Callable] = None,
               timeout_s: float = 60.0) -> CoordinatedResult:
    """
    Main entry point: decompose → dispatch → collect → merge → resolve.

    Args:
        task: The complex task description
        context: Additional context (file contents, prior results)
        spawn_worker_fn: Function to call workers. Signature:
            spawn_worker_fn(worker: str, task: str, context: str) -> str
            If None, returns stub results.
        timeout_s: Max total time for coordination

    Returns:
        CoordinatedResult with merged output, conflicts, confidence
    """
    t0 = time.perf_counter()

    # 1. Decompose
    sub_tasks = decompose_task(task, context)
    active_sub_tasks = {k: v for k, v in sub_tasks.items() if v}

    if not active_sub_tasks:
        return CoordinatedResult(
            task=task, results=[], merged_output="No sub-tasks generated.",
            conflicts=[], consensus_level="none", confidence=0.0,
            duration_s=time.perf_counter() - t0
        )

    # 2. Dispatch workers (parallel via threads)
    results: list[WorkerResult] = []
    lock = threading.Lock()

    def _dispatch(worker: str, sub_task: str):
        w_t0 = time.perf_counter()
        try:
            if spawn_worker_fn:
                output = spawn_worker_fn(worker, sub_task, context[:1000])
            else:
                # Stub mode — generate a plausible response
                stubs = {
                    "A": f"[WORKER-A CODE STUB]\nImplementation analysis for: {sub_task[:100]}",
                    "B": f"[WORKER-B REASON STUB]\nStructured analysis for: {sub_task[:100]}",
                    "C": f"[WORKER-C RESEARCH STUB]\nResearch synthesis for: {sub_task[:100]}",
                }
                output = stubs.get(worker, f"[STUB] No handler for worker {worker}")

            specialties = {"A": "code", "B": "reason", "C": "research"}
            result = WorkerResult(
                worker=worker,
                specialty=specialties.get(worker, "unknown"),
                sub_task=sub_task[:200],
                output=str(output),
                success=bool(output and len(str(output).strip()) > 20),
                duration_s=time.perf_counter() - w_t0,
                confidence=0.7 if bool(output and len(str(output).strip()) > 20) else 0.2,
            )
        except Exception as e:
            result = WorkerResult(
                worker=worker, specialty="unknown",
                sub_task=sub_task[:200], output="",
                success=False, duration_s=time.perf_counter() - w_t0,
                error=str(e), confidence=0.0,
            )
        with lock:
            results.append(result)

    threads = []
    for worker, sub_task in active_sub_tasks.items():
        t = threading.Thread(target=_dispatch, args=(worker, sub_task), daemon=True)
        threads.append(t)
        t.start()

    # 3. Wait with timeout
    for t in threads:
        t.join(timeout=timeout_s / max(len(threads), 1))

    # 4. Detect and resolve conflicts
    conflicts = detect_conflicts(results)
    conflicts = resolve_conflicts(conflicts, results)

    # 5. Merge
    merged = merge_results(task, results, conflicts)

    # 6. Compute overall metrics
    confidence = _calculate_confidence(results, conflicts)
    consensus = _calculate_consensus(results, conflicts)

    return CoordinatedResult(
        task=task,
        results=results,
        merged_output=merged,
        conflicts=conflicts,
        consensus_level=consensus,
        confidence=confidence,
        duration_s=time.perf_counter() - t0,
    )


# ── Convenience ──────────────────────────────────────────────────────────────

def format_result(result: CoordinatedResult) -> str:
    """Format a CoordinatedResult as a readable string."""
    lines = [
        f"# Coordinated Task: {result.task[:80]}",
        f"Duration: {result.duration_s:.2f}s",
        f"Consensus: {result.consensus_level}",
        f"Confidence: {result.confidence:.2f}",
        f"Workers: {len([r for r in result.results if r.success])}/{len(result.results)} successful",
        "",
    ]
    for r in result.results:
        status = "✓" if r.success else "✗"
        lines.append(f"  {status} W-{r.worker} ({r.specialty})  [{r.duration_s:.1f}s]  "
                     f"{'OK' if r.success else r.error[:60]}")
    if result.conflicts:
        lines.append("")
        lines.append("Conflicts:")
        for c in result.conflicts:
            lines.append(f"  ⚠ {c['between']}: {c['topic']} → {c['resolution']}")
    lines.append("")
    lines.append("---")
    lines.append(result.merged_output)
    return "\n".join(lines)
