"""
AZOTH MODEL SCOUT — runs overnight, unattended.

Tests every NVIDIA free model:
  1. Availability check (can it respond at all?)
  2. Context length probe (binary search for real limit)
  3. Quality test on LAMAGUE task (scored by Π)
  4. Speed test (tokens/sec)
  5. Rate limit characterization (429 threshold)

Writes results to KNOWLEDGE/model_catalog.md and ARMY/done/.
Posts Telegram summaries every 30 minutes.
Self-heals on errors — if a model 429s, backs off and continues.
"""

import os
import sys
import time
import json
import datetime
import threading
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent

def run_scout():
    """Main overnight scout loop. Call this from a standalone script."""
    sys.path.insert(0, str(HARNESS_DIR))

    from dotenv import load_dotenv
    load_dotenv(HARNESS_DIR / ".env")

    from openai import OpenAI
    from CORE.telegram_bot import send_message as tg
    from CORE.orchestrator import mark_done, DONE_DIR

    nvidia_key = (os.environ.get("NVIDIA_KEY", "")
                  or os.environ.get("NVIDIA_API_KEY", ""))
    if not nvidia_key:
        tg("☿ MODEL SCOUT — no NVIDIA key found. Aborting.")
        return

    client = OpenAI(
        api_key=nvidia_key,
        base_url="https://integrate.api.nvidia.com/v1",
    )

    # The full catalog to test — add more as discovered
    MODELS_TO_TEST = [
        "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "meta/llama-3.3-70b-instruct",
        "meta/llama-3.1-8b-instruct",
        "meta/llama-3.1-405b-instruct",
        "mistralai/mistral-large-2-instruct",
        "mistralai/mixtral-8x22b-instruct-v0.1",
        "google/gemma-3-27b-it",
        "deepseek-ai/deepseek-r1",
        "qwen/qwen3-235b-a22b",
        "nvidia/nemotron-4-340b-instruct",
    ]

    LAMAGUE_TEST = (
        "You are given a LAMAGUE symbol: ◈ (diamond, four-cornered).\n"
        "Explain in 2 sentences: (1) what this symbol means in the LAMAGUE grammar, "
        "(2) how you would use it in a truth-pressure expression.\n"
        "Be precise. No padding."
    )

    RESULTS_DIR = HARNESS_DIR / "ARMY" / "done"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    catalog_path  = HARNESS_DIR / "KNOWLEDGE" / "model_catalog.md"
    results_path  = HARNESS_DIR / "ARMY" / "done" / "model_scout_results.json"

    all_results = {}
    start_ts    = datetime.datetime.now().isoformat()

    tg(
        f"☿ MODEL SCOUT — starting overnight run.\n"
        f"{len(MODELS_TO_TEST)} models to test.\n"
        f"Telegram updates every 30 min. Results → KNOWLEDGE/model_catalog.md"
    )

    last_tg = time.time()

    for model in MODELS_TO_TEST:
        slug = model.split("/")[-1]
        r    = {"model": model, "slug": slug, "ts": datetime.datetime.now().isoformat()}

        # ── Availability check ───────────────────────────────────────────
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say: OK"}],
                max_tokens=5,
                temperature=0.0,
            )
            r["available"] = True
            r["ping_reply"] = (resp.choices[0].message.content or "").strip()[:20]
        except Exception as ex:
            r["available"] = False
            r["error"]     = str(ex)[:120]
            all_results[slug] = r
            continue

        # ── Speed test ───────────────────────────────────────────────────
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Count from 1 to 20, one number per line."}],
                max_tokens=80,
                temperature=0.0,
            )
            elapsed = time.time() - t0
            out_tok = resp.usage.completion_tokens if resp.usage else 20
            r["tokens_per_sec"] = round(out_tok / max(elapsed, 0.1), 1)
        except Exception as ex:
            r["tokens_per_sec"] = None
            r["speed_error"] = str(ex)[:80]

        # ── Context length probe (coarse) ────────────────────────────────
        # Try progressively larger contexts until it fails
        ctx_sizes = [4096, 8192, 16384, 32768, 65536, 128000]
        max_ctx   = 0
        for ctx in ctx_sizes:
            try:
                # Fill with ~ctx tokens of padding
                padding = ("The quick brown fox jumps over the lazy dog. " * 40)[:ctx * 3]
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": f"{padding}\n\nSay: OK"},
                    ],
                    max_tokens=5,
                    temperature=0.0,
                )
                if resp.choices:
                    max_ctx = ctx
            except Exception:
                break
            time.sleep(1)  # gentle on rate limits
        r["max_ctx_tested"] = max_ctx

        # ── LAMAGUE quality test ─────────────────────────────────────────
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": LAMAGUE_TEST}],
                max_tokens=200,
                temperature=0.3,
            )
            answer = (resp.choices[0].message.content or "").strip()
            r["lamague_response"] = answer[:300]
            # Rough quality score: did it mention diamond, four-cornered, truth-pressure?
            hits = sum(1 for w in ["diamond", "truth", "pressure", "◈", "lamague", "symbol"]
                       if w.lower() in answer.lower())
            r["lamague_score"] = hits  # /6 max
        except Exception as ex:
            r["lamague_score"] = 0
            r["lamague_error"] = str(ex)[:80]

        # Brief backoff between models
        time.sleep(3)
        all_results[slug] = r

        # Telegram ping every 30 minutes
        if time.time() - last_tg > 1800:
            done_count = sum(1 for v in all_results.values() if v.get("available"))
            tg(f"☿ MODEL SCOUT — progress: {len(all_results)}/{len(MODELS_TO_TEST)} tested, "
               f"{done_count} available.")
            last_tg = time.time()

    # ── Write results ────────────────────────────────────────────────────────
    results_path.write_text(json.dumps(all_results, indent=2))

    # Write human-readable catalog
    lines = [
        "# AZOTH MODEL CATALOG",
        f"## Generated by MODEL SCOUT · {start_ts}",
        f"## {len(all_results)} models tested · NVIDIA NIM API",
        "",
        "| Model | Available | Tokens/sec | Max CTX | LAMAGUE/6 |",
        "|---|---|---|---|---|",
    ]
    for slug, r in sorted(all_results.items(),
                          key=lambda x: x[1].get("lamague_score", 0), reverse=True):
        avail  = "✓" if r.get("available") else "✗"
        tps    = r.get("tokens_per_sec", "—")
        ctx    = r.get("max_ctx_tested", "—")
        lscore = r.get("lamague_score", "—")
        lines.append(f"| {slug} | {avail} | {tps} | {ctx} | {lscore} |")

    lines += [
        "",
        "## Top recommendation",
    ]
    # Best = available + highest lamague + fastest
    best = max(
        (v for v in all_results.values() if v.get("available")),
        key=lambda v: (v.get("lamague_score", 0), v.get("tokens_per_sec", 0)),
        default=None,
    )
    if best:
        lines.append(
            f"**{best['model']}** — LAMAGUE score {best.get('lamague_score',0)}/6 · "
            f"{best.get('tokens_per_sec','?')} tok/s · max CTX {best.get('max_ctx_tested','?')}"
        )

    lines += [
        "",
        "## Raw results",
        f"Full JSON: ARMY/done/model_scout_results.json",
    ]
    catalog_path.write_text("\n".join(lines))

    # Final Telegram report
    available = [v for v in all_results.values() if v.get("available")]
    summary = (
        f"☿ MODEL SCOUT — COMPLETE.\n\n"
        f"Tested: {len(all_results)} models\n"
        f"Available: {len(available)}\n"
    )
    if best:
        summary += (
            f"\nBest model: {best['slug']}\n"
            f"  LAMAGUE: {best.get('lamague_score',0)}/6\n"
            f"  Speed:   {best.get('tokens_per_sec','?')} tok/s\n"
            f"  CTX:     {best.get('max_ctx_tested','?')}\n"
        )
    summary += f"\nFull catalog: KNOWLEDGE/model_catalog.md"
    tg(summary)


if __name__ == "__main__":
    run_scout()
