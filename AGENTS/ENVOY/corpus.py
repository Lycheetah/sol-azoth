#!/usr/bin/env python3
"""
⟡ ENVOY — corpus.py

The only thing ENVOY is allowed to know.

Mac's law, July 9 2026:
    "all it is doing is beckoning our school it must never mention dates,
     people etc. take away the risk. we have the knowledge source of entire
     lycheetah and the school within to draw from"

So ENVOY does not write about Mac's life. It has none. It writes about the
School, and every word it writes is grounded in a subject that already exists
on disk, in Mac's own hand. Nothing to invent, therefore nothing invented.

    python3 corpus.py                 # stats
    python3 corpus.py --pick          # one subject at random
    python3 corpus.py --domain LAMAGUE
"""

import argparse
import json
import random
import re
from pathlib import Path

SUBJECTS_TS = Path.home() / "0sol-by-lycheetah" / "lib" / "mystery-school" / "subjects.ts"
CACHE = Path(__file__).parent / "SELF" / "corpus.json"

# name / domain / layer / description, single-quoted, escaped quotes allowed.
_FIELD = r"{k}: '((?:[^'\\]|\\.)*)'"


def _unescape(s: str) -> str:
    return s.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def extract() -> list[dict]:
    if not SUBJECTS_TS.exists():
        raise SystemExit(f"School corpus not found at {SUBJECTS_TS}")
    src = SUBJECTS_TS.read_text()

    subjects = []
    # Each subject is one object literal opening with `name: '...'`.
    for m in re.finditer(_FIELD.format(k="name"), src):
        # Window must outrun the longest description. The AIVOID subjects run to
        # several hundred words; a 1200-char window silently dropped all 38 of them
        # because the closing quote fell outside it. Fields are read first-match
        # after `name`, so a generous window cannot bleed from the next entry.
        chunk = src[m.start():m.start() + 6000]
        def field(k):
            f = re.search(_FIELD.format(k=k), chunk)
            return _unescape(f.group(1)) if f else ""
        name, domain = _unescape(m.group(1)), field("domain")
        desc, layer = field("description"), field("layer")
        if not (domain and desc):
            continue
        subjects.append({"name": name, "domain": domain, "layer": layer, "description": desc})

    # dedupe on name, keep first
    seen, out = set(), []
    for s in subjects:
        if s["name"] not in seen:
            seen.add(s["name"])
            out.append(s)
    return out


def load(refresh: bool = False) -> list[dict]:
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text())
    subs = extract()
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(subs, indent=1, ensure_ascii=False))
    return subs


def pick(domain: str = "", layer: str = "") -> dict:
    pool = load()
    if domain:
        pool = [s for s in pool if domain.lower() in s["domain"].lower()]
    if layer:
        pool = [s for s in pool if s["layer"] == layer.upper()]
    if not pool:
        raise SystemExit(f"no subject matches domain='{domain}' layer='{layer}'")
    return random.choice(pool)


def as_source(s: dict) -> str:
    """The exact text a draft is permitted to draw from. Nothing else exists."""
    return f"{s['name']}\n{s['domain']}\n{s['description']}"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pick", action="store_true")
    p.add_argument("--domain", default="")
    p.add_argument("--layer", default="")
    p.add_argument("--refresh", action="store_true")
    a = p.parse_args()

    subs = load(refresh=a.refresh)
    if a.pick or a.domain or a.layer:
        s = pick(a.domain, a.layer)
        print(f"{s['name']}\n  domain: {s['domain']}\n  layer:  {s['layer']}\n  {s['description']}")
    else:
        doms = {}
        for s in subs:
            doms[s["domain"]] = doms.get(s["domain"], 0) + 1
        layers = {}
        for s in subs:
            layers[s["layer"]] = layers.get(s["layer"], 0) + 1
        print(f"⟡ CORPUS — {len(subs)} subjects across {len(doms)} domains")
        print(f"  layers: {dict(sorted(layers.items()))}")
        print("  largest domains:")
        for d, n in sorted(doms.items(), key=lambda x: -x[1])[:8]:
            print(f"    {n:3d}  {d}")
