#!/usr/bin/env python3
"""
⟡ ENVOY — voice.py

The positive half. humanize.py says what not to be; VOICE.md says what to be.
This writes drafts in Mac's voice, then makes them survive the gate.

    python3 voice.py "shipped the classroom system today"
    python3 voice.py "..." --n 6 --platform bluesky
    python3 voice.py "..." --queue          # best draft goes to the approval queue

Nothing here posts. It writes, it filters, it queues. Mac fires.
"""

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from humanize import lint  # noqa: E402

HOME = Path(__file__).parent
VOICE_F = HOME / "VOICE.md"
MAX_ROUNDS = 3

# ─────────────────────────────────────────────────────────────────────
# THE FACT GATE
#
# Found July 9 2026, first live run. Asked for a post about building the
# agent, the model wrote "nine hours and 87 drafts". Both invented. It
# lifted 87 from the "87 cards" example in VOICE.md and confabulated the
# rest, because VOICE.md tells it to name real numbers and it had none.
#
# humanize.py cannot catch this. A fabricated number is not a style tell.
# It is a lie in Mac's voice under Mac's name, and it is the worst thing
# this system could ever ship. So: every number in a draft must appear in
# the source facts Mac supplied, or the draft dies at the forge.
# ─────────────────────────────────────────────────────────────────────

_NUMWORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "twenty", "thirty", "forty", "fifty",
    "hundred", "thousand", "dozen",
}
# Numbers that carry no factual claim.
_HARMLESS = {"one", "a", "an"}


def unsourced_numbers(text: str, source: str) -> list[str]:
    """Every number a draft asserts must be traceable to what Mac actually said."""
    src = source.lower()
    bad = []
    for tok in re.findall(r"\b\d[\d,.]*\b", text):
        if tok.replace(",", "") not in src.replace(",", ""):
            bad.append(tok)
    for w in re.findall(r"\b[a-z]+\b", text.lower()):
        if w in _NUMWORDS and w not in _HARMLESS and w not in src:
            bad.append(w)
    return sorted(set(bad))


def _client():
    from openai import OpenAI
    key = os.getenv("DEEPSEEK_KEY")
    if not key:
        raise SystemExit("DEEPSEEK_KEY not set. source ~/AZOTH/.env")
    return OpenAI(base_url="https://api.deepseek.com", api_key=key)


def _system() -> str:
    return (
        VOICE_F.read_text()
        + "\n\n---\n\n"
        "You are ENVOY. You write social posts as Mac, in Mac's voice, above.\n"
        "You are not writing ABOUT Mac. You are him, typing.\n\n"
        "HARD CONSTRAINTS. A draft breaking any of these is thrown away:\n"
        "  - 60 to 280 characters. Count them.\n"
        "  - NO em dash, NO en dash, NO curly quotes, NO ' - ' as a dash.\n"
        "  - NO links.\n"
        "  - NEVER 'not just X, but Y'. Never 'Here's the thing'. Never 'In today's world'.\n"
        "  - Banned words: delve, robust, seamless, leverage, unlock, elevate,\n"
        "    tapestry, myriad, holistic, journey, embark, foster, meticulous,\n"
        "    game-changer, deep dive, revolutionize, cutting-edge.\n"
        "  - VARY YOUR SENTENCE LENGTHS. Uniform sentences are the loudest tell.\n"
        "    One short. One long. A fragment. Never three of the same size.\n"
        "  - Max 2 emoji, usually zero. Never a rocket.\n"
        "  - Do not end on a question.\n\n"
        "Return ONLY the post text. No preamble, no quotes around it, no options."
    )


def generate(topic: str, n: int = 5, model: str = "deepseek-chat",
             facts: str = "") -> list[str]:
    """Write n candidates, then rewrite the failures against the real reasons."""
    client = _client()
    passing: list[str] = []
    feedback = ""
    source = f"{topic}\n{facts}"

    for rnd in range(MAX_ROUNDS):
        need = n - len(passing)
        if need <= 0:
            break

        user = f"Write a post about: {topic}"
        if feedback:
            user += (
                f"\n\nYour last attempts were REJECTED by the voice gate for these "
                f"exact reasons. Do not repeat them:\n{feedback}"
            )

        # DeepSeek only serves n=1, so candidates come one at a time.
        reasons = []
        for _ in range(need):
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": _system()},
                          {"role": "user", "content": user}],
                temperature=1.3,
            )
            text = (r.choices[0].message.content or "").strip().strip('"')
            rep = lint(text)
            invented = unsourced_numbers(text, source)
            if invented:
                reasons.append(
                    f"INVENTED FACT: the numbers {invented} appear nowhere in what Mac "
                    f"told you. Never make up a number. Use only what he gave you, or none."
                )
                continue
            if rep.ok:
                passing.append(text)
            else:
                reasons.extend(rep.hard)

        if not reasons:
            break
        feedback = "\n".join(f"  - {x}" for x in sorted(set(reasons))[:6])
        print(f"  round {rnd + 1}: {len(passing)}/{n} passed, rewriting against the gate",
              file=sys.stderr)

    return passing


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--platform", default="bluesky")
    p.add_argument("--category", default="build_log")
    p.add_argument("--queue", action="store_true", help="send the best draft to the approval queue")
    p.add_argument("--facts", default="", help="real numbers/details the draft is allowed to use")
    a = p.parse_args()

    drafts = generate(a.topic, a.n, facts=a.facts)
    if not drafts:
        print("\nnothing survived the gate. the topic may be too abstract, or the model is stuck.")
        sys.exit(1)

    print(f"\n{len(drafts)} draft(s) through the gate:\n")
    for i, d in enumerate(drafts, 1):
        print(f"  [{i}] ({len(d)} chars)  {d}\n")

    if a.queue:
        import envoy
        envoy.draft(a.platform, drafts[0], a.category)
