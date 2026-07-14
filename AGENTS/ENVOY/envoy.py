#!/usr/bin/env python3
"""
⟡ ENVOY — the outward hand.

Nothing in this file publishes anything on its own. Every path to a live
post runs through a human tap. That is structural, not configurable.
(CONSTITUTION §I, and CLAUDE.md XVI: Sol prepares, Mac fires.)

    python3 envoy.py draft x "text of the post"    # lint + queue it
    python3 envoy.py list                          # what's waiting
    python3 envoy.py approve <id>                  # Mac's tap. posts if live.
    python3 envoy.py reject  <id> "why"            # kills it, resets the tier
    python3 envoy.py budget                        # where the money is

Live posting requires BOTH:
    ENVOY_LIVE=1        in the environment
    an approved queue item

Default state of the world is a dry run.
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from humanize import lint  # noqa: E402

HOME = Path(__file__).parent
QUEUE = HOME / "QUEUE"
SELF = HOME / "SELF"
BUDGET_F = HOME / "BUDGET.json"
RECORD_F = SELF / "record.json"

LIVE = os.getenv("ENVOY_LIVE", "0") == "1"

# X pay-per-use, verified against X's Feb 2026 pricing. Bluesky and
# Mastodon charge nothing, which is why the voice gets proven there first.
COSTS = {
    ("x", "post"): 0.015,
    ("x", "post_with_link"): 0.20,
    ("x", "read_other"): 0.005,
    ("x", "read_own"): 0.001,
    ("bluesky", "post"): 0.0,
    ("bluesky", "read"): 0.0,
    ("mastodon", "post"): 0.0,
    ("mastodon", "read"): 0.0,
}

# Categories that may EVER graduate to auto-post. Replies and DMs are
# absent by construction, not by config. (CONSTITUTION §VII, Tier ∞)
AUTO_ELIGIBLE = {"build_log", "art_drop", "note"}
NEVER_AUTO = {"reply", "dm", "quote", "callout"}
GRADUATION_APPROVALS = 30


class BudgetExceeded(Exception):
    pass


# ─────────────────────────────────────────────────────────────────────
# THE BUDGET GOVERNOR
# At the ceiling I stop. I do not ask for more. (CONSTITUTION §III)
# ─────────────────────────────────────────────────────────────────────

def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def load_budget() -> dict:
    if not BUDGET_F.exists():
        b = {"month": _month(), "cap_usd": 5.00, "spent_usd": 0.0, "log": []}
        BUDGET_F.write_text(json.dumps(b, indent=2))
        return b
    b = json.loads(BUDGET_F.read_text())
    if b["month"] != _month():          # new month, fresh ceiling
        b = {"month": _month(), "cap_usd": b["cap_usd"], "spent_usd": 0.0, "log": []}
        BUDGET_F.write_text(json.dumps(b, indent=2))
    return b


def quote(platform: str, action: str) -> float:
    return COSTS.get((platform, action), 0.0)


def charge(platform: str, action: str, note: str = "") -> float:
    """Log the cost BEFORE the call is made. Refuse at the ceiling."""
    cost = quote(platform, action)
    b = load_budget()
    if b["spent_usd"] + cost > b["cap_usd"]:
        raise BudgetExceeded(
            f"${b['spent_usd']:.3f} spent of ${b['cap_usd']:.2f} ceiling. "
            f"This {platform}/{action} costs ${cost:.3f}. Stopping."
        )
    b["spent_usd"] = round(b["spent_usd"] + cost, 4)
    b["log"].append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platform": platform, "action": action, "usd": cost, "note": note[:80],
    })
    BUDGET_F.write_text(json.dumps(b, indent=2))
    return cost


# ─────────────────────────────────────────────────────────────────────
# THE RECORD (drives the autonomy ladder)
# ─────────────────────────────────────────────────────────────────────

def load_record() -> dict:
    return json.loads(RECORD_F.read_text()) if RECORD_F.exists() else {}


def save_record(r: dict) -> None:
    SELF.mkdir(exist_ok=True)
    RECORD_F.write_text(json.dumps(r, indent=2))


def may_autopost(category: str) -> bool:
    """Trust is not a ratchet. One rejection resets the category."""
    if category in NEVER_AUTO or category not in AUTO_ELIGIBLE:
        return False
    c = load_record().get(category, {})
    return c.get("approved", 0) >= GRADUATION_APPROVALS and c.get("rejected", 0) == 0


# ─────────────────────────────────────────────────────────────────────
# THE QUEUE
# ─────────────────────────────────────────────────────────────────────

def _items() -> list[dict]:
    out = []
    for f in sorted(QUEUE.glob("*.json")):
        d = json.loads(f.read_text())
        d["_path"] = str(f)
        out.append(d)
    return out


def _find(item_id: str) -> dict:
    for it in _items():
        if it["id"].startswith(item_id):
            return it
    raise SystemExit(f"no queue item starting with '{item_id}'")


def _save(it: dict) -> None:
    p = it.pop("_path")
    Path(p).write_text(json.dumps(it, indent=2))
    it["_path"] = p


def _notify(text: str) -> None:
    if os.getenv("ENVOY_QUIET") == "1":
        return
    try:
        sys.path.insert(0, str(HOME.parent.parent))
        from CORE.telegram_bot import send_message
        send_message(text)
    except Exception:
        pass  # Telegram down is never a reason to lose a draft


def draft(platform: str, text: str, category: str = "note", longform: bool = False) -> None:
    """Lint, then queue. A draft that fails the gate never reaches Mac."""
    rep = lint(text, longform=longform)
    if not rep.ok:
        print(rep.explain())
        print("\nNot queued. Rewrite it.")
        raise SystemExit(1)

    QUEUE.mkdir(exist_ok=True)
    item = {
        "id": uuid.uuid4().hex[:8],
        "platform": platform,
        "category": category,
        "text": text,
        "longform": longform,
        "status": "pending",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "est_usd": quote(platform, "post"),
        "soft_flags": rep.soft,
    }
    (QUEUE / f"{int(time.time())}_{item['id']}.json").write_text(json.dumps(item, indent=2))

    print(rep.explain())
    print(f"\nqueued {item['id']}  [{platform}/{category}]  est ${item['est_usd']:.3f}")

    if may_autopost(category):
        print(f"category '{category}' is Tier 1. Auto-posting.")
        _publish(_find(item["id"]))
    else:
        _notify(f"⟡ ENVOY draft {item['id']} [{platform}]\n\n{text}\n\n✓ approve {item['id']}\n✗ reject {item['id']}")


def approve(item_id: str) -> None:
    it = _find(item_id)
    if it["status"] != "pending":
        raise SystemExit(f"{it['id']} is already '{it['status']}'")
    rec = load_record()
    c = rec.setdefault(it["category"], {"approved": 0, "rejected": 0})
    c["approved"] += 1
    save_record(rec)
    it["status"] = "approved"
    _save(it)
    _publish(it)


def reject(item_id: str, why: str = "") -> None:
    it = _find(item_id)
    rec = load_record()
    c = rec.setdefault(it["category"], {"approved": 0, "rejected": 0})
    c["rejected"] += 1
    save_record(rec)
    it["status"] = "rejected"
    it["why"] = why
    _save(it)
    print(f"{it['id']} rejected. Category '{it['category']}' is back to Tier 0.")


def _publish(it: dict) -> None:
    """The only path to a live post. Requires an approved item AND ENVOY_LIVE=1."""
    if it["status"] != "approved":
        raise SystemExit("refusing to publish an unapproved item")

    if not LIVE:
        print(f"\n[DRY RUN] would post to {it['platform']}:\n  {it['text']}")
        print("  (set ENVOY_LIVE=1 to make this real)")
        return

    try:
        charge(it["platform"], "post", it["text"][:40])
    except BudgetExceeded as e:
        print(f"BUDGET STOP: {e}")
        _notify(f"⟡ ENVOY stopped. {e}")
        return

    from platforms import get_platform
    url = get_platform(it["platform"]).post(it["text"])
    it["status"] = "posted"
    it["url"] = url
    _save(it)
    print(f"posted: {url}")
    _notify(f"⟡ posted to {it['platform']}\n{url}")


def show_budget() -> None:
    b = load_budget()
    left = b["cap_usd"] - b["spent_usd"]
    print(f"⟡ BUDGET {b['month']}")
    print(f"  ceiling  ${b['cap_usd']:.2f}")
    print(f"  spent    ${b['spent_usd']:.3f}")
    print(f"  left     ${left:.3f}")
    print(f"  live     {'YES' if LIVE else 'no (dry run)'}")
    if b["log"]:
        print("  recent:")
        for e in b["log"][-5:]:
            print(f"    {e['ts']}  {e['platform']}/{e['action']}  ${e['usd']:.3f}")


def show_queue() -> None:
    items = [i for i in _items() if i["status"] == "pending"]
    if not items:
        print("queue is empty.")   # never "you haven't posted in N days" (§IV)
        return
    for it in items:
        print(f"  {it['id']}  [{it['platform']}/{it['category']}]  ${it['est_usd']:.3f}")
        print(f"      {it['text'][:100]}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "draft":
        draft(a[1], a[2], a[3] if len(a) > 3 else "note")
    elif a[0] == "approve":
        approve(a[1])
    elif a[0] == "reject":
        reject(a[1], a[2] if len(a) > 2 else "")
    elif a[0] == "list":
        show_queue()
    elif a[0] == "budget":
        show_budget()
    else:
        print(__doc__)
