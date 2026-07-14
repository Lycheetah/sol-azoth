#!/usr/bin/env python3
"""
⟡ ENVOY — humanize.py

The gate every draft passes before Mac ever sees it.

Mac's law, July 9 2026:
    "no - or wierd ai punctuation that everyone knows is ai
     or we instantly lose people"

So this is not a style suggestion engine. HARD tells are rejections.
A draft that trips one does not get queued. It goes back to the forge.

Usage:
    python3 humanize.py "your draft text"
    python3 humanize.py --file draft.txt
    python3 humanize.py --test          # run the built-in suite
"""

import re
import sys
import statistics
from dataclasses import dataclass, field

MIN_CHARS = 60
MAX_CHARS = 280
MAX_EMOJI = 2
MAX_HASHTAGS = 2

# ─────────────────────────────────────────────────────────────────────
# THE TELL LIST
# Rots as models change. Re-tune whenever something passes and still
# reads like a machine. (CONSTITUTION §VIII)
# ─────────────────────────────────────────────────────────────────────

PUNCT_TELLS = [
    ("—", "em dash. The loudest AI tell on the internet."),
    ("–", "en dash. Same family."),
    ("‘", "curly open single quote. Use a plain '."),
    ("’", "curly apostrophe. Use a plain '."),
    ("“", "curly open double quote. Use a plain \"."),
    ("”", "curly close double quote. Use a plain \"."),
    ("…", "single-character ellipsis. Type three dots or none."),
]

# " - " used as a dash. Mac called this one out by name.
SPACED_HYPHEN = re.compile(r"\s-\s")

LEXICON = [
    "delve", "tapestry", "testament to", "in the realm of", "realm of",
    "seamless", "seamlessly", "robust", "leverage", "leveraging",
    "landscape of", "unlock", "unlocking", "elevate", "elevating",
    "embark", "foster", "fostering", "myriad", "plethora",
    "meticulous", "meticulously", "holistic", "synergy", "game-changer",
    "game changer", "deep dive", "ever-evolving", "ever evolving",
    "underscore", "underscores", "pivotal", "navigate the",
    "boasts", "nestled", "bustling", "at the end of the day",
    "in conclusion", "moreover", "furthermore", "additionally,",
    "it's worth noting", "that being said", "harness the power",
    "revolutionize", "revolutionizing", "cutting-edge", "paradigm shift",
]

CADENCE_TELLS = [
    (re.compile(r"\bnot just\b.{0,60}?\b(but|it's)\b", re.I),
     "'not just X, but Y'. The single most recognisable LLM sentence shape."),
    (re.compile(r"\bit'?s not about\b.{0,50}?\.\s*it'?s about\b", re.I),
     "'It's not about X. It's about Y.' Pure machine."),
    (re.compile(r"\bhere'?s the thing\b", re.I),
     "'Here's the thing'. Overused into meaninglessness."),
    (re.compile(r"\blet that sink in\b", re.I), "'Let that sink in'."),
    (re.compile(r"\bthe best part\?", re.I), "'The best part?' Fake-suspense cadence."),
    (re.compile(r"\bthe result\?", re.I), "'The result?' Same trick."),
    (re.compile(r"^in today'?s (world|landscape|age)", re.I | re.M),
     "Opening with 'In today's world'."),
    (re.compile(r"^ever (wonder|wondered|thought about)", re.I | re.M),
     "Opening with a rhetorical 'Ever wonder'."),
    (re.compile(r"\bwhat if i told you\b", re.I), "'What if I told you'."),
    (re.compile(r"\bthis changes everything\b", re.I), "'This changes everything'."),
]

# Three comma-separated multi-word items ending in "and X". Tight on purpose:
# a loose version eats normal human lists.
RULE_OF_THREE = re.compile(
    r"\b(\w+ \w+(?: \w+)?), (\w+ \w+(?: \w+)?),? and (\w+ \w+(?: \w+)?)\b", re.I
)

LINK = re.compile(r"(https?://|www\.|\b\w+\.(com|io|dev|app|org|net|ai)\b)", re.I)

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF⬀-⯿]"
)
BANNED_EMOJI = {"\U0001F680": "rocket. The universal 'a bot wrote this' badge."}


@dataclass
class Report:
    text: str
    hard: list = field(default_factory=list)
    soft: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.hard

    def explain(self) -> str:
        n = len(self.text)
        head = f"{'PASS' if self.ok else 'REJECT'}  ({n} chars)"
        lines = [head, "=" * len(head)]
        for h in self.hard:
            lines.append(f"  [HARD] {h}")
        for s in self.soft:
            lines.append(f"  [soft] {s}")
        if self.ok and not self.soft:
            lines.append("  Reads human. Queue it.")
        return "\n".join(lines)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def lint(text: str, longform: bool = False) -> Report:
    """Gate a draft. longform=True only when Mac has approved it per-draft."""
    r = Report(text=text)
    low = text.lower()

    # ── punctuation ──────────────────────────────────────────────
    for ch, why in PUNCT_TELLS:
        if ch in text:
            r.hard.append(f"punctuation: {why}")
    if SPACED_HYPHEN.search(text):
        r.hard.append("punctuation: ' - ' used as a dash. Split the sentence or use a comma.")

    # ── lexicon ──────────────────────────────────────────────────
    for word in LEXICON:
        if re.search(r"\b" + re.escape(word), low):
            r.hard.append(f"lexicon: '{word}'. Nobody says this out loud.")

    # ── cadence ──────────────────────────────────────────────────
    for pat, why in CADENCE_TELLS:
        if pat.search(text):
            r.hard.append(f"cadence: {why}")
    m = RULE_OF_THREE.search(text)
    if m:
        r.hard.append(f"cadence: rule-of-three list ('{m.group(0)[:40]}...'). Cut one or add a fourth.")

    # ── links (cost + culture) ───────────────────────────────────
    if LINK.search(text):
        r.hard.append("link present. $0.20 a post and every good room flames link-drops.")

    # ── length ───────────────────────────────────────────────────
    n = len(text)
    if not longform:
        if n < MIN_CHARS:
            r.hard.append(f"length: {n} chars, floor is {MIN_CHARS}.")
        if n > MAX_CHARS:
            r.hard.append(f"length: {n} chars, ceiling is {MAX_CHARS}. Long form needs Mac's approval.")

    # ── emoji ────────────────────────────────────────────────────
    found = EMOJI.findall(text)
    for e in found:
        if e in BANNED_EMOJI:
            r.hard.append(f"emoji: {e} {BANNED_EMOJI[e]}")
    if len(found) > MAX_EMOJI:
        r.hard.append(f"emoji: {len(found)} used, max is {MAX_EMOJI}.")

    # ── shape a human leaves behind ──────────────────────────────
    if not re.search(r"[.!?]", text):
        r.soft.append("no full stop anywhere. Mac asked for real punctuation.")
    if text and text == text.lower() and len(text) > 80:
        r.soft.append("no capitals at all. Fine sometimes, not as a habit.")
    if ";" in text and not longform:
        r.soft.append("semicolon in a short post. Almost nobody does this.")
    if text.count("#") > MAX_HASHTAGS:
        r.soft.append(f"{text.count('#')} hashtags. Reads like reach-farming.")

    # ── cadence variance: humans vary, machines march ────────────
    sents = _sentences(text)
    counts = [len(s.split()) for s in sents]
    if len(sents) >= 3 and sum(counts) >= 18:
        sd = statistics.pstdev(counts)
        if sd < 2.0:
            r.hard.append(
                f"uniform sentence length (stdev {sd:.1f}, need 2.0+). "
                f"Word counts {counts}. Break one short. Let one run long."
            )

    return r


# ─────────────────────────────────────────────────────────────────────
# SUITE — these must hold or the gate is lying to us.
# ─────────────────────────────────────────────────────────────────────

_MACHINE = [
    "I built a companion app — it's not just a chatbot, but a living framework that helps you delve into your own patterns. 🚀",
    "In today's world, building software is hard. Building meaningful software is harder. Building it alone is hardest of all.",
    "Today I shipped a new feature. It took me three hours to build. I am really happy with how it turned out.",
    "This tool leverages a robust architecture to unlock seamless workflows.",
    "Check it out at lycheetah.dev and let me know what you think!",
]

_HUMAN = [
    "drew 87 cards before i understood what the deck was actually for. card 34 broke me. redrew it nine times and the ninth one still isn't right, but it's honest now.",
    "Spent the day teaching an agent not to sound like an agent. The irony is not lost on me. It rejected my first four drafts.",
    "My mum has a brain injury. I built her an app that doesn't flash. Six months of work. She used it this morning without asking me how. 🙂",
]


def _test() -> int:
    fails = 0
    print("MACHINE TEXT (must all REJECT)\n")
    for t in _MACHINE:
        rep = lint(t)
        status = "ok" if not rep.ok else "!! LEAKED THROUGH"
        if rep.ok:
            fails += 1
        print(f"  [{status}] {t[:58]}...")
        for h in rep.hard[:2]:
            print(f"        -> {h}")
    print("\nHUMAN TEXT (must all PASS)\n")
    for t in _HUMAN:
        rep = lint(t)
        status = "ok" if rep.ok else "!! FALSE REJECT"
        if not rep.ok:
            fails += 1
        print(f"  [{status}] {t[:58]}...")
        for h in rep.hard:
            print(f"        -> {h}")
    print(f"\n{'ALL GOOD' if not fails else str(fails) + ' FAILURES'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(_test())
    if len(sys.argv) > 2 and sys.argv[1] == "--file":
        body = open(sys.argv[2]).read()
    elif len(sys.argv) > 1:
        body = " ".join(sys.argv[1:])
    else:
        body = sys.stdin.read()
    rep = lint(body)
    print(rep.explain())
    sys.exit(0 if rep.ok else 1)
