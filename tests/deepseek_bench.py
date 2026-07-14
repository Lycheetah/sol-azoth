#!/usr/bin/env python3
"""
☿ AZOTH — DeepSeek endpoint bench

The paid twin of tests/nvidia_bench.py. Same doctrine, same three probes
(reused from nvidia_bench, not duplicated — Single Truth): a seat is not
trusted on reputation, it's benched. 2026-07-11: clones.py moved off the free
NVIDIA tier onto paid DeepSeek (too slow/unreliable for the harness — Mac's
call). This is what "earned, not assumed" means for the two seats that
replaced it.

Usage:  python3 tests/deepseek_bench.py
Results land in tests/DEEPSEEK_BENCH_RESULTS.md and .json.
"""
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

AZOTH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AZOTH))

from tests.nvidia_bench import probe_alive, probe_tool, probe_code, verdict  # noqa: E402

BASE_URL = "https://api.deepseek.com"
TIMEOUT = 90.0
CANDIDATES = ["deepseek-v4-flash", "deepseek-v4-pro"]


def _key() -> str:
    env = AZOTH / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("DEEPSEEK_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    k = os.environ.get("DEEPSEEK_KEY", "")
    if not k:
        sys.exit("NO DEEPSEEK_KEY (checked AZOTH/.env and environment)")
    return k


def bench_one(key: str, model: str) -> dict:
    client = OpenAI(base_url=BASE_URL, api_key=key)
    alive, note, latency = probe_alive(client, model)
    row = {"model": model, "alive": alive, "alive_note": note, "latency_s": round(latency, 2),
           "tool": False, "tool_note": "-", "code": False, "code_note": "-"}
    if not alive:
        return row
    row["tool"], row["tool_note"] = probe_tool(client, model)
    row["code"], row["code_note"] = probe_code(client, model)
    return row


def main():
    key = _key()
    print(f"☿ benching {len(CANDIDATES)} paid DeepSeek seats — alive → tool → code\n")
    rows = [bench_one(key, m) for m in CANDIDATES]
    for r in rows:
        v = verdict(r)
        mark = {"CLONE-CAPABLE": "✓✓", "DRIVER (weak coder)": "✓·",
                "WORKER (no tools)": "·✓", "CHAT ONLY": "··", "DEAD": "✗✗"}[v]
        print(f"  {mark}  {r['model']:<24} {v:<20} {r['latency_s']:>5.1f}s  {r['tool_note'][:44]}")

    (AZOTH / "tests" / "DEEPSEEK_BENCH_RESULTS.json").write_text(json.dumps(rows, indent=2))
    md = ["# DEEPSEEK PAID SEAT BENCH — earned, not assumed",
          f"*Run {time.strftime('%Y-%m-%d %H:%M')} · probes: alive → structured tool_call → code we execute*",
          "", "| verdict | model | tool_call | code | latency |", "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| **{verdict(r)}** | `{r['model']}` | {'✓' if r['tool'] else '✗ ' + r['tool_note'][:34]} "
                  f"| {'✓' if r['code'] else '✗ ' + r['code_note'][:30]} | {r['latency_s']}s |")
    (AZOTH / "tests" / "DEEPSEEK_BENCH_RESULTS.md").write_text("\n".join(md) + "\n")

    dead = [r["model"] for r in rows if verdict(r) != "CLONE-CAPABLE"]
    if dead:
        print(f"\n⚠ NOT clone-capable: {', '.join(dead)} — clones.py SEATS is now trusting an unearned seat.")
    print(f"\n→ tests/DEEPSEEK_BENCH_RESULTS.md")


if __name__ == "__main__":
    main()
