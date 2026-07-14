"""
CORE/swarm_budget.py — spend governor for paid clone seats.

2026-07-11: clones.py moved off the free NVIDIA tier onto paid DeepSeek (too
slow/unreliable for the harness — Mac's call). Heartbeat and Cron fire clone
seats unattended; nothing should be free to run away with real money while
Mac isn't watching. Mirrors AGENTS/ENVOY/envoy.py's budget pattern: charge
BEFORE the call, hard monthly ceiling, refuse past it.

Per-call costs below are ASSUMED, not MEASURED (Register Discipline) — a
placeholder until a month of real DeepSeek billing exists. Tighten
AZOTH_SWARM_CAP_USD or the estimates once real numbers land.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
BUDGET_F = HARNESS_DIR / "workspace" / "swarm_budget.json"

DEFAULT_CAP_USD = float(os.environ.get("AZOTH_SWARM_CAP_USD", "10.00"))

# ASSUMED per-call estimate (flash cheaper/faster, pro pricier/deeper).
EST_COST_USD = {"flash": 0.01, "pro": 0.03}
DEFAULT_EST_COST_USD = 0.02


class SwarmBudgetExceeded(Exception):
    pass


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def load_budget() -> dict:
    BUDGET_F.parent.mkdir(parents=True, exist_ok=True)
    if not BUDGET_F.exists():
        b = {"month": _month(), "cap_usd": DEFAULT_CAP_USD, "spent_usd": 0.0, "log": []}
        BUDGET_F.write_text(json.dumps(b, indent=2))
        return b
    b = json.loads(BUDGET_F.read_text())
    if b["month"] != _month():  # new month, fresh ceiling (keeps whatever cap Mac set)
        b = {"month": _month(), "cap_usd": b.get("cap_usd", DEFAULT_CAP_USD), "spent_usd": 0.0, "log": []}
        BUDGET_F.write_text(json.dumps(b, indent=2))
    return b


def charge(seat: str, note: str = "") -> float:
    """Log the estimated cost BEFORE the call fires. Refuse at the ceiling."""
    cost = EST_COST_USD.get(seat, DEFAULT_EST_COST_USD)
    b = load_budget()
    if b["spent_usd"] + cost > b["cap_usd"]:
        raise SwarmBudgetExceeded(
            f"${b['spent_usd']:.3f} spent of ${b['cap_usd']:.2f} swarm ceiling this month. "
            f"Stopping before the {seat!r} call. Raise AZOTH_SWARM_CAP_USD to continue."
        )
    b["spent_usd"] = round(b["spent_usd"] + cost, 4)
    b["log"].append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seat": seat, "usd": cost, "note": note[:80],
    })
    # Cap the log so this file can't grow forever under a busy daemon.
    b["log"] = b["log"][-500:]
    BUDGET_F.write_text(json.dumps(b, indent=2))
    return cost


def status() -> str:
    b = load_budget()
    return (f"swarm budget {b['month']}: ${b['spent_usd']:.3f} / ${b['cap_usd']:.2f} "
            f"({len(b['log'])} calls logged)")


if __name__ == "__main__":
    print(status())
