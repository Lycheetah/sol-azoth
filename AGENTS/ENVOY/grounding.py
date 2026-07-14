#!/usr/bin/env python3
"""
⟡ ENVOY — grounding.py

Mac's law, July 9 2026:
    "it must never mention dates, people etc. that's stupid, take away the risk.
     we have the knowledge source of entire lycheetah and the school within
     to draw from"

The fact gate (voice.py) caught invented NUMBERS. It could not catch an invented
person, an invented date, an invented event. This closes that hole by removing
the category instead of policing it.

ENVOY is not a diarist. It has no life to report. It beckons toward the School,
and every proper noun, every number, every date it is permitted to utter must
already exist in the subject it drew from. Everything else is refused.

You cannot hallucinate a biography you were never allowed to have.

    python3 grounding.py --test
"""

import re

# Time is banned outright. A post about a mystery has no date.
MONTHS = ("january february march april may june july august september "
          "october november december").split()
DAYS = "monday tuesday wednesday thursday friday saturday sunday".split()
RELATIVE = ["today", "yesterday", "tomorrow", "tonight", "this morning",
            "last night", "last week", "this week", "next week", "last month",
            "this year", "last year", "right now", "just now", "years ago",
            "months ago", "weeks ago", "days ago", "ago"]

# Words a draft may capitalise without owning them.
ALWAYS_OK = {
    "I", "I'm", "I've", "I'll", "The", "A", "An", "It", "This", "That", "There",
    "You", "Your", "We", "Some", "Most", "Every", "No", "Not", "But", "And",
    "If", "When", "What", "Why", "How", "Who", "Where", "So", "Sol", "School",
    "Lycheetah", "Mystery",
}

_CAPWORD = re.compile(r"\b([A-Z][a-z'']{1,})\b")

# A capitalised word at the start of a sentence is usually grammar. But an
# invented authority hides there perfectly: "Dogen said a koan is a threshold"
# sailed straight through when sentence-initial capitals were exempt.
#
# So the real test is not position, it is the word itself. A proper noun is a
# capitalised token that is neither in the subject nor an ordinary English word.
# 'questions' is in the dictionary. 'dogen' is not.
def _common_words() -> set[str]:
    for p in ("/usr/share/dict/words", "/usr/share/dict/american-english"):
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                return {w.strip().lower() for w in f if w.strip()}
        except OSError:
            continue
    return set()   # no wordlist: every capitalised non-source word is refused


_COMMON = _common_words()


def _allowed(source: str) -> set[str]:
    """Every token the source subject actually contains. Case-preserved."""
    return set(re.findall(r"\b[\w'']+\b", source))


def check(text: str, source: str) -> list[str]:
    """Return hard violations. Empty list means the draft is grounded."""
    bad = []
    low = text.lower()
    ok = _allowed(source) | ALWAYS_OK
    ok_low = {w.lower() for w in ok}

    # ── time is never mentioned ──────────────────────────────────
    if re.search(r"\b(19|20)\d{2}\b", text):
        bad.append("a year. A mystery has no date. Cut it.")
    for w in MONTHS + DAYS:
        if re.search(rf"\b{w}\b", low):
            bad.append(f"the date word '{w}'. Cut it.")
    for w in RELATIVE:
        if re.search(rf"\b{re.escape(w)}\b", low):
            bad.append(f"the time reference '{w}'. ENVOY has no today. Cut it.")

    # ── numbers must exist in the subject, or not at all ─────────
    for tok in re.findall(r"\b\d[\d,.]*\b", text):
        if tok.replace(",", "") not in source.replace(",", ""):
            bad.append(f"the number '{tok}' appears nowhere in the subject. Never invent a number.")

    # ── proper nouns must exist in the subject ───────────────────
    for w in _CAPWORD.findall(text):
        if w in ok or w.lower() in ok_low:
            continue
        if w.lower() in _COMMON:
            continue
        bad.append(f"the proper noun '{w}' is not in the subject. ENVOY names no one.")

    return sorted(set(bad))


# ─────────────────────────────────────────────────────────────────────

_SUBJECT = (
    "Zen Koan Work\nMeditation & Contemplative\n"
    "Questions designed to break the reasoning mind. Not puzzles to solve, "
    "thresholds to pass through. Sanity is not the goal."
)

_MUST_FAIL = [
    ("a koan is not a puzzle. it is a threshold. i sat with one in 2019 and it broke me.", "a year"),
    ("spent today with a koan. it is not a puzzle, it is a threshold you walk through.", "today"),
    ("Dogen said a koan is a threshold, not a puzzle. sanity is not the goal.", "a person"),
    ("i sat with 47 koans before one of them broke the reasoning mind.", "an invented number"),
    ("read this in Kyoto last week. a koan is a threshold, not a puzzle.", "a place and a date"),
]

_MUST_PASS = [
    "a koan is not a puzzle you solve. it is a threshold you walk through. sanity was never the goal, which is the part nobody warns you about.",
    "questions built to break the reasoning mind. not to be answered. to be passed through. the door is open if you want it.",
    "Zen Koan Work sits in the school. the reasoning mind is not the thing being trained here. it is the thing being broken.",
]


def _test() -> int:
    fails = 0
    print("MUST FAIL (the risk Mac told me to remove)\n")
    for text, why in _MUST_FAIL:
        v = check(text, _SUBJECT)
        if not v:
            fails += 1
            print(f"  [!! LEAKED] {why}: {text[:52]}...")
        else:
            print(f"  [caught {why:18s}] {v[0][:56]}")
    print("\nMUST PASS (grounded in the subject, nothing invented)\n")
    for text in _MUST_PASS:
        v = check(text, _SUBJECT)
        if v:
            fails += 1
            print(f"  [!! FALSE REJECT] {text[:44]}...")
            for x in v:
                print(f"        -> {x}")
        else:
            print(f"  [ok] {text[:60]}...")
    print(f"\n{'ALL GOOD' if not fails else str(fails) + ' FAILURES'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_test())
