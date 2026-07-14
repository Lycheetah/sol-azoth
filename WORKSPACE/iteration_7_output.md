# P2-T3 — Memory Summarization
## Iteration 7 · June 27 2026

## What Was Built

**CORE/memory_summarizer.py** — Episode compression engine.

Core functions:
- `episode_count(eng)` — current live count
- `summarize(eng, ...)` — main entry: checks threshold, compresses batch, returns result dict
- `maybe_summarize(eng, ...)` — lightweight wrapper for post-forge auto-call
- `recall_summaries(eng)` — retrieve all stored summaries
- `status(eng)` — quick dict for /status display

Compression modes:
- **Rule-based** (default): deterministic, zero cost. Timespan, session count, failure rate, top-8 actions by frequency, first 5 failures with results.
- **LLM-compressed** (opt-in via `use_llm=True`): WORKER-B (REASON/free) produces dense bullet-point summary. Falls back to rule mode on any error.

Storage: summaries stored as high-confidence learnings (confidence=0.95) under topic `EPISODE_SUMMARY_YYYYMMDD`. Recallable via `recall_summaries()` or `recall_learnings(topic="EPISODE_SUMMARY")`.

**CORE/tests/test_memory_summarizer.py** — 7 tests:
- under-threshold no-op
- over-threshold compress (110 → 60)
- summary stored as learning with correct insight
- summary content quality (Top actions + Failures present)
- status() report structure
- double-compress (160 → 110 → 60, 2 summaries)

**agent.py** — post-forge hook: `maybe_summarize()` runs after every forge task. If compression occurs, prints count to terminal. Silent otherwise.

## Test Run Result

```
34 tests, 0 failures (7 new P2-T3 tests, all green)
```

## Self-Review

**Gate 1:** CORE/memory_summarizer.py on disk (3.9KB). Test file on disk.
All 34 tests pass. ✓

**Gate 2 (Π):** Read memory_engine schema fully before writing any compression
logic. Delete uses parameterized placeholders (no SQL injection risk). LLM path
has try/except fallback — no path where a worker failure breaks the forge loop.
Double-compress test verifies idempotent correctness. ✓

**Design honesty:**
- LLM compression caps at 30 episodes to avoid token overflow — stated in code.
- Timestamps can collide in fast test loops (all same second) — affects "Timespan"
  display only, not correctness.
- The post-forge hook creates a fresh MemoryEngine() — this is a separate
  connection from any agent session. Acceptable; SQLite handles it.

## VERDICT: PASS
