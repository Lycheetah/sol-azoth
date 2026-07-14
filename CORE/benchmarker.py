"""
NVIDIA / model benchmarker — AZOTH
Fires a standard prompt at every available model, measures latency + throughput,
scores quality, writes a comparison table to WORKSPACE/bench_results.md.
"""

import time, json, datetime, threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

HARNESS_DIR  = Path(__file__).parent.parent
RESULTS_FILE = HARNESS_DIR / "WORKSPACE" / "bench_results.md"

# Standard benchmark prompt — tests reasoning, instruction-following, concision
BENCH_PROMPT = (
    "You are being benchmarked. Answer in exactly 3 sentences. "
    "Question: What is the most important property of a good reasoning system, "
    "and why does it matter more than raw speed or raw accuracy alone?"
)

QUALITY_KEYWORDS = [
    "calibrat", "uncertain", "honest", "truth", "evidence",
    "verify", "reason", "confiden", "reliab", "consistent"
]


@dataclass
class BenchResult:
    model_id:    str
    slug:        str
    provider:    str
    latency_s:   float = 0.0     # time to first token (approx — full call)
    total_s:     float = 0.0     # wall-clock for full response
    out_tokens:  int   = 0
    tokens_per_s: float = 0.0
    quality:     int   = 0       # 0-5: keyword hits in response
    response:    str   = ""
    error:       str   = ""
    ok:          bool  = False


def _score_quality(text: str) -> int:
    t = text.lower()
    return sum(1 for kw in QUALITY_KEYWORDS if kw in t)


def bench_model(slug: str, model_id: str, client, max_tokens: int = 200) -> BenchResult:
    r = BenchResult(model_id=model_id, slug=slug,
                    provider="nvidia" if "nvidia" in str(client.base_url) else slug.split("-")[0])
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": BENCH_PROMPT}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        r.total_s    = time.perf_counter() - t0
        r.latency_s  = r.total_s   # non-streaming — best we can do without SSE
        r.response   = resp.choices[0].message.content or ""
        usage        = getattr(resp, "usage", None)
        r.out_tokens = usage.completion_tokens if usage else len(r.response.split())
        r.tokens_per_s = round(r.out_tokens / r.total_s, 1) if r.total_s > 0 else 0
        r.quality    = _score_quality(r.response)
        r.ok         = True
    except Exception as ex:
        r.total_s = time.perf_counter() - t0
        r.error   = str(ex)[:120]
    return r


def run_benchmark(models_dict: dict, clients_map: dict,
                  progress_fn=None) -> list[BenchResult]:
    """
    models_dict: {slug: (provider, model_id, tier, desc)}
    clients_map: {"deepseek": client, "nvidia": client, "gemini": client}
    progress_fn: optional callable(slug, status_str) for live updates
    """
    results = []
    for slug, spec in models_dict.items():
        provider, model_id = spec[0], spec[1]
        client = clients_map.get(provider)
        if client is None:
            continue
        if progress_fn:
            progress_fn(slug, "running…")
        r = bench_model(slug, model_id, client)
        results.append(r)
        if progress_fn:
            if r.ok:
                progress_fn(slug, f"✓ {r.total_s:.1f}s · {r.tokens_per_s} tok/s · Q{r.quality}")
            else:
                progress_fn(slug, f"✗ {r.error[:50]}")
    return results


def write_report(results: list[BenchResult]) -> str:
    ts  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ok  = [r for r in results if r.ok]
    fail= [r for r in results if not r.ok]

    lines = [
        f"# AZOTH Model Benchmark",
        f"*{ts}*\n",
        f"Prompt: standardised 3-sentence reasoning question.",
        f"Quality score: keyword hits (0–{len(QUALITY_KEYWORDS)}) from reasoning vocabulary.\n",
        "## Results\n",
        f"| Slug | Total(s) | Tok/s | Quality | Status |",
        f"|------|----------|-------|---------|--------|",
    ]
    # Sort by quality desc, then speed
    for r in sorted(ok, key=lambda x: (-x.quality, x.total_s)):
        lines.append(
            f"| {r.slug} | {r.total_s:.2f} | {r.tokens_per_s} | {r.quality}/{len(QUALITY_KEYWORDS)} | ✓ |"
        )
    for r in fail:
        lines.append(f"| {r.slug} | — | — | — | ✗ {r.error[:40]} |")

    if ok:
        fastest = min(ok, key=lambda x: x.total_s)
        highest = max(ok, key=lambda x: x.quality)
        lines += [
            "\n## Verdict",
            f"- **Fastest:** {fastest.slug} ({fastest.total_s:.2f}s)",
            f"- **Highest quality:** {highest.slug} (Q{highest.quality})",
        ]
        if fastest.slug != highest.slug:
            lines.append(f"- **Best balance:** pick {highest.slug} for reasoning, {fastest.slug} for speed")

    if ok:
        lines += ["\n## Sample responses\n"]
        for r in sorted(ok, key=lambda x: -x.quality)[:3]:
            lines.append(f"### {r.slug}")
            lines.append(f"> {r.response[:300].strip()}\n")

    report = "\n".join(lines)
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(report)
    return report


def summary_table(results: list[BenchResult]) -> str:
    """Short Telegram-friendly table."""
    ok   = [r for r in results if r.ok]
    fail = [r for r in results if not r.ok]
    lines = [f"◆ Benchmark — {len(ok)} pass · {len(fail)} fail\n"]
    for r in sorted(ok, key=lambda x: (-x.quality, x.total_s)):
        lines.append(f"  {r.slug:<14} {r.total_s:>5.1f}s  {r.tokens_per_s:>5} tok/s  Q{r.quality}")
    for r in fail:
        lines.append(f"  {r.slug:<14} ✗ {r.error[:35]}")
    if ok:
        fastest = min(ok, key=lambda x: x.total_s)
        best    = max(ok, key=lambda x: x.quality)
        lines.append(f"\nFastest: {fastest.slug} · Best Q: {best.slug}")
        lines.append(f"Full report: WORKSPACE/bench_results.md")
    return "\n".join(lines)
