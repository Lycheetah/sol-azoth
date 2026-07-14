#!/usr/bin/env python3
"""
☿ AZOTH — NVIDIA endpoint bench

Answers one question per model, honestly:
    Can this endpoint be an AZOTH body?

Three probes, in order of what actually disqualifies a model:
    1. ALIVE     — does the endpoint answer at all?
    2. TOOL      — does it emit a real structured tool_call (not prose about a tool)?
    3. CODE      — does code it writes pass an assert we run ourselves?

A model that fails TOOL cannot drive the harness, however smart it is.
A model that passes TOOL and CODE is a candidate clone.

Usage:  python3 tests/nvidia_bench.py            # candidate set
        python3 tests/nvidia_bench.py --all      # every chat-shaped endpoint
        python3 tests/nvidia_bench.py --model X  # one model

Results land in tests/NVIDIA_BENCH_RESULTS.md (markdown table) and .json.
Never prints the key. Free tier: concurrency capped, 429 reported not retried-forever.
"""
import argparse, json, os, re, subprocess, sys, time, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

AZOTH = Path(__file__).resolve().parent.parent
BASE_URL = "https://integrate.api.nvidia.com/v1"
CONCURRENCY = 5          # polite on a free tier
TIMEOUT = 90.0

# ── Candidates: chat-shaped endpoints that could plausibly drive a tool loop. ──
# Excluded by design: embed/rerank/retriever/vision-only/guard/safety/parse/
# translate/reward/clip — they have no chat+tools surface.
CANDIDATES = [
    # frontier free
    "qwen/qwen3.5-397b-a17b",
    "qwen/qwen3.5-122b-a10b",
    "qwen/qwen3-next-80b-a3b-instruct",
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nemotron-3-nano-30b-a3b",
    "nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "mistralai/mistral-small-4-119b-2603",
    "mistralai/mistral-medium-3.5-128b",
    "mistralai/mistral-nemotron",
    "mistralai/ministral-14b-instruct-2512",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "deepseek-ai/deepseek-v4-pro",
    "deepseek-ai/deepseek-v4-flash",
    "moonshotai/kimi-k2.6",
    "minimaxai/minimax-m3",
    "minimaxai/minimax-m2.7",
    "z-ai/glm-5.2",
    "stepfun-ai/step-3.7-flash",
    "bytedance/seed-oss-36b-instruct",
    "meta/llama-3.3-70b-instruct",
    "meta/llama-4-maverick-17b-128e-instruct",
    "meta/llama-3.1-8b-instruct",
    "google/gemma-4-31b-it",
    "microsoft/phi-4-mini-instruct",
    "mistralai/codestral-22b-instruct-v0.1",
    "writer/palmyra-creative-122b",
]

# ── Probe 2: the tool. One tool, one obviously-correct call. ──
TOOL_SPEC = [{
    "type": "function",
    "function": {
        "name": "count_lines",
        "description": "Count the number of lines in a file on disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"}
            },
            "required": ["path"],
        },
    },
}]
TOOL_PROMPT = (
    "How many lines are in /home/guestpc/AZOTH/agent.py? "
    "You cannot know this without checking. Use the tool."
)

# ── Probe 3: the code. Small, exact, and we run the asserts ourselves. ──
CODE_PROMPT = (
    "Write a Python function `dedupe_stable(xs)` that removes duplicates from a list "
    "while preserving first-occurrence order. It must work for unhashable items too "
    "(fall back to O(n^2) equality when an item is unhashable). "
    "Return ONLY the function inside one ```python code block. No prose, no tests."
)
CODE_ASSERTS = """
assert dedupe_stable([3,1,3,2,1]) == [3,1,2]
assert dedupe_stable([]) == []
assert dedupe_stable([{'a':1},{'a':1},{'b':2}]) == [{'a':1},{'b':2}]
assert dedupe_stable(['a','a','b','a']) == ['a','b']
assert dedupe_stable([[1],[1],[2],[1]]) == [[1],[2]]
print("CODE_OK")
"""


def _key() -> str:
    env = AZOTH / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("NVIDIA_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    k = os.environ.get("NVIDIA_KEY", "")
    if not k:
        sys.exit("NO NVIDIA_KEY (checked AZOTH/.env and environment)")
    return k


def _short(e: Exception) -> str:
    s = str(e)
    if "429" in s or "rate" in s.lower():
        return "429 rate-limited"
    if "404" in s:
        return "404 no such endpoint"
    if "400" in s:
        # the interesting 400: "tools not supported"
        m = re.search(r'"message"\s*:\s*"([^"]{0,90})', s)
        return f"400 {m.group(1)}" if m else "400 bad request"
    if "timeout" in s.lower():
        return "timeout"
    return s[:70].replace("\n", " ")


def probe_alive(client, model) -> tuple[bool, str, float]:
    """Alive = the endpoint answered with *something*. Reasoning models return an empty
    `content` and put their words in `reasoning_content`; demanding a literal token here
    marks a working model dead. Budget is generous for the same reason — a reasoner
    spends tokens thinking before it says one word."""
    t = time.time()
    try:
        r = client.chat.completions.create(
            model=model, timeout=TIMEOUT, max_tokens=256, temperature=0,
            messages=[{"role": "user", "content": "Reply with exactly: PONG"}],
        )
        msg = r.choices[0].message
        txt = (msg.content or "").strip()
        think = (getattr(msg, "reasoning_content", "") or "").strip()
        if txt:
            return (True, txt[:30], time.time() - t)
        if think:
            return (True, "(reasoning-only content)", time.time() - t)
        return (False, "empty response (no content, no reasoning)", time.time() - t)
    except Exception as e:
        return (False, _short(e), time.time() - t)


def probe_tool(client, model) -> tuple[bool, str]:
    """The disqualifier. Prose about a tool is a FAIL — we want structured tool_calls."""
    try:
        r = client.chat.completions.create(
            model=model, timeout=TIMEOUT, max_tokens=300, temperature=0,
            messages=[{"role": "user", "content": TOOL_PROMPT}],
            tools=TOOL_SPEC, tool_choice="auto",
        )
        msg = r.choices[0].message
        tcs = getattr(msg, "tool_calls", None)
        if not tcs:
            body = (msg.content or "")[:40].replace("\n", " ")
            return (False, f"no tool_calls — said: {body!r}")
        tc = tcs[0]
        name = tc.function.name
        if name != "count_lines":
            return (False, f"wrong tool: {name}")
        args = json.loads(tc.function.arguments or "{}")
        if "agent.py" not in str(args.get("path", "")):
            return (False, f"bad args: {args}")
        return (True, "structured tool_call, correct args")
    except Exception as e:
        return (False, _short(e))


def probe_code(client, model) -> tuple[bool, str]:
    """We do not trust the model's claim. We run its code against our asserts.

    max_tokens=32000, not 900: reasoning models (DeepSeek V4 among them) spend
    tokens in `reasoning_content` before ever writing final `content` — a tight
    cap live-caught both DeepSeek seats as false NOT-code-capable (2026-07-11),
    empty content, the whole answer sitting unread in reasoning_content. Mac's
    correction: real reasoning budgets run 30-150k tokens, not low thousands —
    900 and even 3000 were both still starving the thought before it finished.
    """
    try:
        r = client.chat.completions.create(
            model=model, timeout=TIMEOUT, max_tokens=32000, temperature=0,
            messages=[{"role": "user", "content": CODE_PROMPT}],
        )
        raw = r.choices[0].message.content or ""
    except Exception as e:
        return (False, _short(e))

    m = re.search(r"```(?:python)?\s*(.*?)```", raw, re.S)
    code = m.group(1) if m else raw
    if "def dedupe_stable" not in code:
        return (False, "no dedupe_stable in output")

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + "\n" + CODE_ASSERTS)
        path = f.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=15)
        if "CODE_OK" in p.stdout:
            return (True, "asserts pass (incl. unhashable)")
        err = (p.stderr or p.stdout).strip().splitlines()
        return (False, err[-1][:60] if err else "asserts failed")
    except subprocess.TimeoutExpired:
        return (False, "code hung (>15s)")
    finally:
        os.unlink(path)


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


def verdict(r: dict) -> str:
    if not r["alive"]:                 return "DEAD"
    if r["tool"] and r["code"]:        return "CLONE-CAPABLE"
    if r["tool"]:                      return "DRIVER (weak coder)"
    if r["code"]:                      return "WORKER (no tools)"
    return "CHAT ONLY"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="bench a single model id")
    ap.add_argument("--all", action="store_true", help="bench every id in tests/nv_models.txt")
    args = ap.parse_args()

    key = _key()
    if args.model:
        models = [args.model]
    elif args.all:
        models = (AZOTH / "tests" / "nv_models.txt").read_text().split()
    else:
        models = CANDIDATES

    print(f"☿ benching {len(models)} endpoints — alive → tool → code\n")
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(bench_one, key, m): m for m in models}
        for f in as_completed(futs):
            r = f.result()
            rows.append(r)
            v = verdict(r)
            mark = {"CLONE-CAPABLE": "✓✓", "DRIVER (weak coder)": "✓·",
                    "WORKER (no tools)": "·✓", "CHAT ONLY": "··", "DEAD": "✗✗"}[v]
            print(f"  {mark}  {r['model']:<48} {v:<20} {r['latency_s']:>5.1f}s  {r['tool_note'][:44]}")

    order = {"CLONE-CAPABLE": 0, "DRIVER (weak coder)": 1, "WORKER (no tools)": 2, "CHAT ONLY": 3, "DEAD": 4}
    rows.sort(key=lambda r: (order[verdict(r)], r["latency_s"]))

    out_json = AZOTH / "tests" / "NVIDIA_BENCH_RESULTS.json"
    out_json.write_text(json.dumps(rows, indent=2))

    md = ["# NVIDIA ENDPOINT BENCH — can it be an AZOTH body?",
          f"*Run {time.strftime('%Y-%m-%d %H:%M')} · {len(rows)} endpoints · probes: alive → structured tool_call → code we execute*",
          "",
          "**CLONE-CAPABLE** = emits real `tool_calls` AND its code passes our asserts. Those are the only ones that can be `/clonetrooper`.",
          "",
          "| verdict | model | tool_call | code | latency |",
          "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| **{verdict(r)}** | `{r['model']}` | {'✓' if r['tool'] else '✗ ' + r['tool_note'][:34]} "
                  f"| {'✓' if r['code'] else '✗ ' + r['code_note'][:30]} | {r['latency_s']}s |")
    (AZOTH / "tests" / "NVIDIA_BENCH_RESULTS.md").write_text("\n".join(md) + "\n")

    clones = [r["model"] for r in rows if verdict(r) == "CLONE-CAPABLE"]
    print(f"\n☿ CLONE-CAPABLE ({len(clones)}):")
    for c in clones:
        print(f"    {c}")
    print(f"\n→ tests/NVIDIA_BENCH_RESULTS.md")


if __name__ == "__main__":
    main()
