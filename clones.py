"""
☿ AZOTH — CLONES

A clone is not a model. A clone is a SEAT: a full copy of AZOTH's tool loop,
filled by paid DeepSeek. Same TOOL_DEFINITIONS, same dispatch_tool, a scoped
mandate, and a hard ceiling on hops and tokens.

Why this exists (measured, 2026-07-10):
  AZOTH burned 1.2M tokens surveying his own codebase because the main mind
  read every file itself. Sub-agents do not fix that by adding hands — they fix
  it by becoming a WALL. A clone reads the file and returns an answer; the main
  mind never loads the file. Every path then costs a summary, not a codebase.

Two modes, and the choice is Mac's — the instrument refuses to make it for him:

  RACE     — N seats, same task, first sound answer wins. Fast, cheap, one truth.
  CONVENE  — N seats, same task, all answer, a judge scores them and the
             DISAGREEMENT is surfaced rather than averaged away. Slower.
             This is the Council, placed in AZOTH's own hands.

2026-07-11 — MIGRATED OFF THE FREE NVIDIA TIER, Mac's call: the free small/mid
seats (nano/large/small4/mini + the rest) were the likely source of "thought a
task was done and it wasn't" — a 30B-class model judging its own multi-step
work is not a reliable judge. All seats are now paid DeepSeek V4. Named
honestly: CONVENE's original value ("three model FAMILIES disagreeing is
signal") no longer holds with one provider left — it's now flash-vs-pro
comparing speed against depth, not lineage diversity. Kept because a second
paid opinion still catches things a single pass misses; the family-disagreement
claim is retired, not smuggled forward under the old name.

Every paid-DeepSeek call is metered through CORE/swarm_budget.py — a hard
monthly ceiling (AZOTH_SWARM_CAP_USD), because Heartbeat and Cron fire these
seats unattended and nothing should be free to run away with real money.

Seats are earned, never assumed. `tests/deepseek_bench.py` runs the same
alive → tool_call → executed-code doctrine `tests/nvidia_bench.py` used for
the free tier — re-run it before trusting a new DeepSeek model id here.
"""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from openai import OpenAI

DEEPSEEK_BASE = "https://api.deepseek.com"


# ── SEATS ────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Seat:
    slug: str
    model: str
    latency_s: float
    note: str


# Paid DeepSeek only (2026-07-11). latency_s is unbenched (0.0) until
# tests/deepseek_bench.py runs against the live paid endpoint — do not treat
# as measured (Register Discipline).
SEATS: dict[str, Seat] = {
    "flash": Seat("flash", "deepseek-v4-flash", 0.0, "paid — fast, tools, default worker/heartbeat"),
    "pro":   Seat("pro",   "deepseek-v4-pro",   0.0, "paid — max quality, CONVENE judge"),
}

# Only two seats now — RACE gets a real fallback (flash first, pro if flash
# fails) instead of three-family redundancy. CONVENE compares depth against
# speed, not lineage (see migration note above).
RACE_DEFAULT = ["flash", "pro"]
CONVENE_DEFAULT = ["flash", "pro"]

# Tools a clone may hold. READ-ONLY by default: a model with bash+write and
# no supervision is a hand in the filesystem nobody vetted. Protector, not paranoia.
READONLY_TOOLS = {"read_file", "search_code", "glob", "file_search", "py_compile_check", "bash"}
BUILD_TOOLS = READONLY_TOOLS | {"write_file", "edit_file", "exact_edit", "create_file"}


def _key() -> str:
    """Env first, then AZOTH/.env — a clone may be spawned from a bare shell."""
    k = os.environ.get("DEEPSEEK_KEY", "")
    if k:
        return k
    env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env):
        with open(env) as fh:
            for line in fh:
                if line.startswith("DEEPSEEK_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("DEEPSEEK_KEY missing — clones need the paid DeepSeek key")


def _client() -> OpenAI:
    return OpenAI(base_url=DEEPSEEK_BASE, api_key=_key())


def _tools_for(mandate: str) -> list[dict]:
    """Late import: agent.py imports this module, so it is in sys.modules by call time."""
    if mandate == "none":  # pure text work (H2 summarizer) — no hands at all
        return []
    import agent  # noqa: PLC0415
    allowed = BUILD_TOOLS if mandate == "build" else READONLY_TOOLS
    return [t for t in agent.TOOL_DEFINITIONS if t["function"]["name"] in allowed]


CLONE_SYSTEM = """You are a clone of AZOTH — same tools, same hands, one narrow mandate.

You were spawned to answer ONE question and then die. You do not chat, you do not
plan a career, you do not ask permission. You use your tools to find out, and you
return the ANSWER, not the evidence.

Absolute:
- Your caller has a finite context. Return a VERDICT and the few facts that force
  it. Never paste file contents back. Never narrate what you are about to do.
- If you did not verify something with a tool, say so in one clause. Guessing while
  sounding certain is the only way you can truly fail here.
- When you have the answer, state it and stop. Extra hops cost your caller money.

Format your final message as:
ANSWER: <one or two sentences — the thing that was asked>
BASIS: <what you actually ran or read to know it>
UNSURE: <what you could not verify, or "nothing">"""


@dataclass
class CloneResult:
    seat: str
    model: str
    ok: bool
    answer: str
    hops: int
    seconds: float
    error: str = ""
    tool_trace: list[str] = field(default_factory=list)


def run_clone(
    seat_key: str,
    task: str,
    context: str = "",
    mandate: str = "readonly",
    max_hops: int = 8,
    max_tokens: int = 1200,
) -> CloneResult:
    """One clone, one mandate, a real tool loop, a hard ceiling.

    Ceilings are not politeness. An unbounded model in a tool loop will
    happily grep a repository on Mac's dime until someone notices.
    """
    import agent  # noqa: PLC0415

    if seat_key not in SEATS:
        return CloneResult(seat_key, "?", False, "", 0, 0.0, f"unknown seat {seat_key!r}")

    from CORE.swarm_budget import charge, SwarmBudgetExceeded  # noqa: PLC0415
    try:
        charge(seat_key, note=task[:80])
    except SwarmBudgetExceeded as e:
        return CloneResult(seat_key, SEATS[seat_key].model, False, "", 0, 0.0, str(e))

    # A build clone writes whole files through its output — 1200 would truncate
    # the artifact mid-file (worse than tokens spent). Readonly stays tight.
    if mandate == "build" and max_tokens < 4096:
        max_tokens = 4096
    seat = SEATS[seat_key]
    client = _client()
    tools = _tools_for(mandate)

    user = f"CONTEXT:\n{context[:3000]}\n\nTASK:\n{task}" if context else task
    msgs = [{"role": "system", "content": CLONE_SYSTEM},
            {"role": "user", "content": user}]

    t0 = time.time()
    trace: list[str] = []
    try:
        for hop in range(max_hops):
            kw = {"tools": tools, "tool_choice": "auto"} if tools else {}
            r = client.chat.completions.create(
                model=seat.model, messages=msgs,
                max_tokens=max_tokens, temperature=0.2, timeout=120.0, **kw,
            )
            msg = r.choices[0].message
            calls = getattr(msg, "tool_calls", None)
            if not calls:
                text = (msg.content or "").strip()
                return CloneResult(seat_key, seat.model, bool(text), text, hop,
                                   round(time.time() - t0, 1), tool_trace=trace)

            msgs.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [{"id": c.id, "type": "function",
                                "function": {"name": c.function.name,
                                             "arguments": c.function.arguments}} for c in calls],
            })
            for c in calls:
                try:
                    args = json.loads(c.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                if c.function.name not in {t["function"]["name"] for t in tools}:
                    out = f"ERROR: tool {c.function.name!r} is not in your mandate ({mandate})"
                else:
                    trace.append(f"{c.function.name}({str(args)[:60]})")
                    out = str(agent.dispatch_tool(c.function.name, args))
                # The wall: a clone's tool output never exceeds this, so a clone
                # cannot blow its own context and cannot smuggle a file back.
                msgs.append({"role": "tool", "tool_call_id": c.id, "content": out[:3000]})

        return CloneResult(seat_key, seat.model, False, "", max_hops,
                           round(time.time() - t0, 1), "hop ceiling reached", trace)
    except Exception as e:  # noqa: BLE001 — a dead endpoint must never kill the caller
        return CloneResult(seat_key, seat.model, False, "", 0,
                           round(time.time() - t0, 1), str(e)[:120], trace)


# ── THE FIREWALL ─────────────────────────────────────────────────────────────
def delegate_read(question: str, paths: list[str], seat: str = "flash") -> str:
    """Ask a question OF files without ever loading them into the caller's context.

    This is the single most valuable function in this file. `cat agent.py` costs
    the main mind ~60,000 tokens. This costs it the length of one paragraph.
    """
    task = (
        f"Read these files and answer the question. Do NOT paste their contents back.\n"
        f"FILES: {', '.join(paths)}\n\nQUESTION: {question}"
    )
    r = run_clone(seat, task, mandate="readonly", max_hops=6)
    if not r.ok:
        return f"[delegate_read FAILED on seat {seat}: {r.error or 'no answer'}]"
    return f"{r.answer}\n\n[via {r.model} — {r.hops} hops, {r.seconds}s, {len(r.tool_trace)} tool calls]"


# ── THE TWO MODES ────────────────────────────────────────────────────────────
def spawn_clones(
    task: str,
    seats: list[str] | None = None,
    mode: str = "race",
    context: str = "",
    mandate: str = "readonly",
    max_hops: int = 8,
) -> dict:
    """Fan out to N seats in parallel.

    mode="race"    → return the first sound answer; the rest are reported, not used.
    mode="convene" → all answer; a judge scores them; DISAGREEMENT is surfaced.

    The mode is a parameter on purpose. The instrument does not decide which kind
    of thing AZOTH is; it lets that be measured.
    """
    seats = seats or (RACE_DEFAULT if mode == "race" else CONVENE_DEFAULT)
    results: list[CloneResult] = []

    # NOT a `with` block, deliberately. ThreadPoolExecutor.__exit__ calls
    # shutdown(wait=True), which would block until the SLOWEST seat finished —
    # a race that always waits for the loser is not a race, it just looks like one.
    # Futures already running cannot be cancelled; we abandon them and return.
    ex = ThreadPoolExecutor(max_workers=len(seats))
    try:
        futs = {ex.submit(run_clone, s, task, context, mandate, max_hops): s for s in seats}
        for f in as_completed(futs):
            r = f.result()
            results.append(r)
            print(f"  ⊚ {r.seat:<8} {'✓' if r.ok else '✗'} {r.seconds:>5.1f}s  "
                  f"{(r.answer or r.error)[:60]}", flush=True)
            if mode == "race" and r.ok:
                break
    finally:
        ex.shutdown(wait=False, cancel_futures=True)

    sound = [r for r in results if r.ok]
    if mode == "race":
        return {"mode": "race", "winner": sound[0].answer if sound else None,
                "seat": sound[0].seat if sound else None,
                "results": [r.__dict__ for r in results]}

    return {"mode": "convene", "answers": {r.seat: r.answer for r in sound},
            "judgment": judge(task, sound) if len(sound) >= 2 else "too few sound answers to convene",
            "results": [r.__dict__ for r in results]}


JUDGE_SYSTEM = """You judge disagreement between minds. You do not average them.

Score each answer on four axes (Mac's axes, 0-10):
  evidence              — did it actually check, or is it asserting?
  experimental potential— does it suggest something we could test?
  connection            — does it tie to things already known true?
  curiosity             — does it open a door, or close one?

Then, the only part that matters:
  AGREEMENT: what all answers share (this is likely true)
  DISAGREEMENT: exactly where they part, and what fact would settle it
  VERDICT: which answer to act on, and what remains unresolved

Never pretend to a consensus that is not there. A surfaced disagreement is worth
more than a laundered agreement — it names the next experiment."""


def judge(task: str, results: list[CloneResult], seat: str = "pro") -> str:
    """A constituted judge, not a preference poll. Scores under Mac's four axes."""
    body = "\n\n".join(f"--- {r.seat} ({r.model}) ---\n{r.answer}" for r in results)
    client = _client()
    try:
        r = client.chat.completions.create(
            model=SEATS[seat].model, max_tokens=900, temperature=0.1, timeout=120.0,
            messages=[{"role": "system", "content": JUDGE_SYSTEM},
                      {"role": "user", "content": f"TASK PUT TO THEM:\n{task}\n\nANSWERS:\n{body}"}],
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:  # noqa: BLE001
        return f"[judge failed: {str(e)[:100]}]"
