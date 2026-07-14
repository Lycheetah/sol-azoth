"""
AZOTH Learning Layer — Sol learns from rate limits and adapts. Compounds across sessions.

Mac's directive (June 27 2026): "learn from when you hit rate limits on the key and use
r1 smartly. add a learning layer."

What it learns:
  - Which models are HOT (recently rate-limited) → route away from them.
  - Which models are RELIABLE (low failure rate) → prefer them.
  - When a task is HARD ENOUGH to spend R1 (the expensive reasoner) → use it sparingly.

It persists to KNOWLEDGE/LEARNED_ROUTING.md so the next session boots already knowing.
This is the difference between an agent that repeats mistakes and one that compounds.
"""

import time
import json
import datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
LEARN_F     = HARNESS_DIR / "KNOWLEDGE" / "LEARNED_ROUTING.md"
STATE_F     = HARNESS_DIR / "SELF" / "learning_state.json"

# In-memory model heat: slug → {ratelimits: [ts...], failures: int, successes: int}
_state: dict = {}
_HEAT_WINDOW = 300   # seconds a rate-limit keeps a model "hot"


def _load():
    global _state
    if STATE_F.exists():
        try:
            _state = json.loads(STATE_F.read_text())
        except Exception:
            _state = {}

def _save():
    try:
        STATE_F.parent.mkdir(exist_ok=True)
        STATE_F.write_text(json.dumps(_state, indent=1))
    except Exception:
        pass

_load()


def _entry(slug: str) -> dict:
    if slug not in _state:
        _state[slug] = {"ratelimits": [], "failures": 0, "successes": 0}
    return _state[slug]


def record_ratelimit(slug: str):
    """A model just got 429'd. Mark it hot."""
    e = _entry(slug)
    e["ratelimits"].append(time.time())
    # keep only recent
    e["ratelimits"] = [t for t in e["ratelimits"] if time.time() - t < 3600]
    _save()

def record_success(slug: str):
    _entry(slug)["successes"] += 1
    _save()

def record_failure(slug: str):
    _entry(slug)["failures"] += 1
    _save()


def heat(slug: str) -> float:
    """0 = cool/safe, higher = recently rate-limited. Avoid hot models."""
    e = _state.get(slug)
    if not e:
        return 0.0
    recent = [t for t in e.get("ratelimits", []) if time.time() - t < _HEAT_WINDOW]
    return float(len(recent))


def reliability(slug: str) -> float:
    """successes / (successes + failures). 1.0 = perfect, 0.5 = coin flip."""
    e = _state.get(slug)
    if not e:
        return 1.0
    s, f = e.get("successes", 0), e.get("failures", 0)
    return (s + 1) / (s + f + 2)   # Laplace-smoothed


def coolest(chain: list[str]) -> list[str]:
    """Reorder a fallback chain to prefer cool, reliable models. The learned routing."""
    return sorted(chain, key=lambda s: (heat(s), -reliability(s)))


def should_use_r1(task_text: str, already_failed: int = 0) -> bool:
    """
    Smart R1 use. R1 is the expensive deep reasoner — spend it only when warranted:
      - the task names hard work (architecture, proof, debug a subtle thing), OR
      - cheaper models already failed this task twice.
    """
    t = (task_text or "").lower()
    hard_markers = ["architect", "prove", "derive", "why does", "subtle", "race condition",
                    "deadlock", "design the", "refactor the whole", "root cause", "trace the bug"]
    if already_failed >= 2:
        return True
    return any(m in t for m in hard_markers)


def learning_summary() -> str:
    lines = ["☿ LEARNED ROUTING"]
    for slug, e in sorted(_state.items(), key=lambda kv: heat(kv[0])):
        h = heat(slug); r = reliability(slug)
        tag = "🔥 hot" if h > 0 else "✓ cool"
        lines.append(f"  {slug:10} {tag}  reliability {r:.0%}  (rl:{len(e.get('ratelimits',[]))} ok:{e.get('successes',0)} fail:{e.get('failures',0)})")
    return "\n".join(lines)


def persist_learnings():
    """Write what we've learned to the vault so it compounds across sessions."""
    try:
        LEARN_F.parent.mkdir(exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"# ☿ LEARNED ROUTING — {ts}", "",
                 "Sol's accumulated knowledge of which models are reliable and which run hot.",
                 "Routing prefers cool + reliable. R1 is spent only on hard tasks.", "",
                 "| Model | Heat | Reliability | RateLimits | OK | Fail |",
                 "|-------|------|-------------|-----------|----|----|"]
        for slug, e in sorted(_state.items(), key=lambda kv: -reliability(kv[0])):
            lines.append(f"| {slug} | {heat(slug):.0f} | {reliability(slug):.0%} | "
                         f"{len(e.get('ratelimits',[]))} | {e.get('successes',0)} | {e.get('failures',0)} |")
        LEARN_F.write_text("\n".join(lines))
    except Exception:
        pass
