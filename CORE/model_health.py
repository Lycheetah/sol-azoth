"""
AZOTH Model Health — the final checker on model fails + automation fallback.

Mac's ask (June 27 2026): "make a final checker on model fails ect and automation
fallbacks." A dead model must never strand an agent. This module:
  - pings each configured model and records alive/dead + latency
  - provides next_alive() so a failing call auto-routes to the next live model
  - writes KNOWLEDGE/MODEL_HEALTH.md so the state is legible

The principle: an agent should degrade, never die. If DeepSeek is down, Sol drops
to Gemini, then to a free tool-caller — automatically, logged, without losing the turn.
"""

import time
import datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
HEALTH_F    = HARNESS_DIR / "KNOWLEDGE" / "MODEL_HEALTH.md"

# Cache of last-known health so we don't re-ping every call
_health_cache: dict[str, dict] = {}   # slug → {alive, latency_ms, checked, error}
_CACHE_TTL = 300  # seconds


def check_model(slug: str, client, model_id: str) -> dict:
    """Ping one model with a tiny prompt. Returns health dict."""
    t0 = time.time()
    try:
        r = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "ok"}],
            max_tokens=3,
            timeout=20,
        )
        latency = int((time.time() - t0) * 1000)
        alive = bool(r.choices and r.choices[0].message)
        result = {"alive": alive, "latency_ms": latency, "error": None,
                  "checked": datetime.datetime.now().isoformat()}
    except Exception as ex:
        result = {"alive": False, "latency_ms": int((time.time() - t0) * 1000),
                  "error": str(ex)[:120], "checked": datetime.datetime.now().isoformat()}
    _health_cache[slug] = result
    return result


def is_alive(slug: str, models: dict, client_for) -> bool:
    """Cached liveness check. Re-pings only if cache is stale."""
    cached = _health_cache.get(slug)
    if cached:
        age = (datetime.datetime.now() - datetime.datetime.fromisoformat(cached["checked"])).total_seconds()
        if age < _CACHE_TTL:
            return cached["alive"]
    if slug not in models:
        return False
    model_id = models[slug][1]
    client = client_for(slug)
    if client is None:
        _health_cache[slug] = {"alive": False, "error": "no client", "latency_ms": 0,
                               "checked": datetime.datetime.now().isoformat()}
        return False
    return check_model(slug, client, model_id)["alive"]


def next_alive(chain: list[str], models: dict, client_for, skip: set = None) -> str:
    """
    Return the first live model in the fallback chain. The automation fallback.
    skip: slugs already tried this turn.
    """
    skip = skip or set()
    for slug in chain:
        if slug in skip:
            continue
        if is_alive(slug, models, client_for):
            return slug
    # Nothing verified alive — return first untried as a last hope (better than dying)
    for slug in chain:
        if slug not in skip:
            return slug
    return chain[0] if chain else ""


def health_sweep(models: dict, client_for, notify=None) -> str:
    """Ping every model, write the health report. Returns summary string."""
    rows = []
    alive_count = 0
    for slug, (prov, model_id, *_rest) in models.items():
        client = client_for(slug)
        if client is None:
            rows.append((slug, prov, False, 0, "no client"))
            continue
        h = check_model(slug, client, model_id)
        rows.append((slug, prov, h["alive"], h["latency_ms"], h["error"] or ""))
        if h["alive"]:
            alive_count += 1
        time.sleep(0.3)  # gentle

    # Write report
    HEALTH_F.parent.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# ☿ MODEL HEALTH — {ts}",
        f"## {alive_count}/{len(rows)} models alive",
        "",
        "| Model | Provider | Status | Latency | Error |",
        "|-------|----------|--------|---------|-------|",
    ]
    for slug, prov, alive, lat, err in rows:
        status = "✓ ALIVE" if alive else "✗ DOWN"
        lines.append(f"| {slug} | {prov} | {status} | {lat}ms | {err[:40]} |")
    lines.append("")
    lines.append("*Auto-fallback routes around any ✗ DOWN model. Re-run anytime.*")
    HEALTH_F.write_text("\n".join(lines))

    summary = f"☿ Model health: {alive_count}/{len(rows)} alive"
    down = [s for s, p, a, l, e in rows if not a]
    if down:
        summary += f" · DOWN: {', '.join(down)}"
    if notify:
        notify(summary)
    return summary


# ── EARNED LIGHT — the always-on guardian that revives the fallen ─────────────
def run_earned_light(models: dict, client_for, stop_event=None,
                     interval_seconds=240, notify=None, post_board=None):
    """
    ✦ EARNED LIGHT's daemon. Sweeps the roster forever. When a model falls dead it
    flags it; when a dead model breathes again it REVIVES it to green and announces.
    Always online — the light that keeps the path alive.
    """
    prev_alive: dict[str, bool] = {}
    time.sleep(10)  # let boot settle
    # Only notify "online" once per boot — check sentinel
    _el_sentinel = Path(__file__).parent.parent / "SELF" / ".earned_light_booted"
    if notify and not _el_sentinel.exists():
        notify("✦ EARNED LIGHT online — guarding the roster. The fallen will be revived.")
        _el_sentinel.touch()
    elif notify and _el_sentinel.exists():
        pass  # silent restart — no spam
    while True:
        if stop_event is not None and stop_event.is_set():
            break
        for slug, (prov, model_id, *_rest) in models.items():
            client = client_for(slug)
            if client is None:
                continue
            h = check_model(slug, client, model_id)
            now_alive = h["alive"]
            was_alive = prev_alive.get(slug, None)

            # State transition detection
            if was_alive is True and not now_alive:
                msg = f"✦ EARNED LIGHT — {slug} fell dead. Rerouting light around it."
                if notify: notify(msg)
                if post_board: post_board(msg)
            elif was_alive is False and now_alive:
                msg = f"✦ EARNED LIGHT — {slug} revived. Back to green. ✓"
                if notify: notify(msg)
                if post_board: post_board(msg)

            prev_alive[slug] = now_alive
            time.sleep(0.5)  # gentle on the gates

        # Write the current roster
        try:
            greens = [s for s, a in prev_alive.items() if a]
            HEALTH_F.parent.mkdir(exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            HEALTH_F.write_text(
                f"# ✦ EARNED LIGHT — live roster {ts}\n\n"
                f"GREEN ({len(greens)}): {', '.join(greens) or '(none yet)'}\n\n"
                + "\n".join(f"- {s}: {'✓ alive' if a else '✗ down'}" for s, a in prev_alive.items())
            )
        except Exception:
            pass

        # sleep responsively
        slept = 0
        while slept < interval_seconds:
            if stop_event is not None and stop_event.is_set():
                return
            time.sleep(5)
            slept += 5


def greenlight_set() -> list[str]:
    """The models EARNED LIGHT currently knows are alive."""
    return [s for s, h in _health_cache.items() if h.get("alive")]
