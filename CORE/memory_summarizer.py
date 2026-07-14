"""
P2-T3: Memory Summarization — AZOTH
When episode count exceeds threshold, compress oldest N into one summary entry.
Two modes: rule-based (free, always works) + LLM-compressed (via WORKER-B, on demand).
"""

import json, datetime
from pathlib import Path

THRESHOLD   = 100   # compress when episode count exceeds this
BATCH_SIZE  = 50    # episodes to compress per run
HARNESS_DIR = Path(__file__).parent.parent


def episode_count(eng) -> int:
    """Return total episode count in the DB."""
    cur = eng.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM episodes")
    return cur.fetchone()[0]


def _fetch_oldest(eng, n: int) -> list:
    """Return the oldest N episodes in ascending order."""
    cur = eng.conn.cursor()
    cur.execute(
        "SELECT * FROM episodes ORDER BY timestamp ASC LIMIT ?", (n,)
    )
    return [dict(row) for row in cur.fetchall()]


def _delete_episodes(eng, ids: list[int]) -> int:
    """Delete episodes by id list. Returns count deleted."""
    if not ids:
        return 0
    placeholders = ",".join("?" * len(ids))
    cur = eng.conn.cursor()
    cur.execute(f"DELETE FROM episodes WHERE id IN ({placeholders})", ids)
    eng.conn.commit()
    return cur.rowcount


def _rule_compress(episodes: list) -> str:
    """
    Deterministic, zero-cost compression.
    Produces a structured summary: timespan, counts, action digest, failures.
    """
    if not episodes:
        return "(empty batch)"

    first_ts = episodes[0].get("timestamp", "?")
    last_ts  = episodes[-1].get("timestamp", "?")
    total    = len(episodes)
    failures = [e for e in episodes if not e.get("success", True)]

    # Action frequency
    from collections import Counter
    action_counts = Counter(e.get("action", "?") for e in episodes)
    top_actions   = action_counts.most_common(8)

    # Unique sessions
    sessions = {e.get("session_id") for e in episodes if e.get("session_id")}

    lines = [
        f"COMPRESSED EPISODE BATCH — {total} episodes",
        f"Timespan: {first_ts} → {last_ts}",
        f"Sessions: {len(sessions)}",
        f"Failures: {len(failures)}/{total}",
        "",
        "Top actions:",
    ]
    for action, count in top_actions:
        lines.append(f"  {count:3d}× {action[:80]}")

    if failures:
        lines.append("")
        lines.append("Notable failures:")
        for f in failures[:5]:
            lines.append(f"  [{f.get('timestamp','?')}] {str(f.get('action','?'))[:60]}")
            if f.get("result"):
                lines.append(f"    → {str(f['result'])[:80]}")

    return "\n".join(lines)


def _llm_compress(episodes: list, spawn_worker_fn) -> str:
    """
    LLM compression via WORKER-B (REASON/free).
    Falls back to rule compression if worker fails.
    """
    if spawn_worker_fn is None:
        return _rule_compress(episodes)

    episode_text = "\n".join(
        f"[{e.get('timestamp','?')}] {e.get('action','?')}: {str(e.get('result',''))[:120]}"
        for e in episodes[:30]  # cap to 30 to avoid token overflow
    )
    task = (
        "Compress this batch of agent episodes into a dense summary. "
        "Preserve: key patterns, important outcomes, failures with root cause, "
        "capability signals. Format: 5-10 bullet points. Dense, not narrative."
    )
    try:
        result = spawn_worker_fn("B", task, context=episode_text)
        if result and "ERROR" not in result[:20]:
            return f"COMPRESSED EPISODE BATCH — {len(episodes)} episodes\n\n" + result
    except Exception:
        pass
    return _rule_compress(episodes)


def summarize(eng, use_llm: bool = False, spawn_worker_fn=None,
              threshold: int = THRESHOLD, batch_size: int = BATCH_SIZE) -> dict:
    """
    Main entry point. Checks count, compresses if needed.

    Returns:
        {"compressed": bool, "before": int, "after": int,
         "batch": int, "summary_id": int|None, "reason": str}
    """
    before = episode_count(eng)

    if before <= threshold:
        return {
            "compressed": False, "before": before, "after": before,
            "batch": 0, "summary_id": None,
            "reason": f"count={before} ≤ threshold={threshold}, no action needed",
        }

    oldest = _fetch_oldest(eng, batch_size)
    if not oldest:
        return {
            "compressed": False, "before": before, "after": before,
            "batch": 0, "summary_id": None, "reason": "no episodes returned",
        }

    if use_llm and spawn_worker_fn:
        summary_text = _llm_compress(oldest, spawn_worker_fn)
    else:
        summary_text = _rule_compress(oldest)

    # Store summary as a high-confidence learning, tagged for recall
    first_ts = oldest[0].get("timestamp", "?")
    last_ts  = oldest[-1].get("timestamp", "?")
    topic    = f"EPISODE_SUMMARY_{first_ts[:10].replace('-', '')}"

    summary_id = eng.learn(
        topic=topic,
        insight=summary_text,
        evidence=f"{len(oldest)} episodes compressed ({first_ts} → {last_ts})",
        confidence=0.95,
    )

    # Delete the originals
    ids = [e["id"] for e in oldest]
    deleted = _delete_episodes(eng, ids)

    after = episode_count(eng)
    return {
        "compressed": True,
        "before": before,
        "after": after,
        "batch": deleted,
        "summary_id": summary_id,
        "reason": f"compressed {deleted} episodes into learning id={summary_id}",
    }


def maybe_summarize(eng, use_llm: bool = False, spawn_worker_fn=None) -> dict:
    """Lightweight wrapper — call after any forge run. No-ops if under threshold."""
    return summarize(eng, use_llm=use_llm, spawn_worker_fn=spawn_worker_fn)


def recall_summaries(eng, limit: int = 10) -> list:
    """Retrieve all stored episode summaries."""
    return eng.recall_learnings(topic="EPISODE_SUMMARY", limit=limit)


def status(eng) -> dict:
    """Quick status for /status display."""
    count = episode_count(eng)
    sums  = recall_summaries(eng, limit=100)
    return {
        "episodes_live": count,
        "summaries_stored": len(sums),
        "threshold": THRESHOLD,
        "pressure": f"{count}/{THRESHOLD} ({100*count//THRESHOLD}%)",
        "needs_compress": count > THRESHOLD,
    }
