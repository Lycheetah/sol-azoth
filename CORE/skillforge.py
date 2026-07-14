"""
H1: SKILL FORGE — clean runs compound into reusable skills (the Hermes loop).

When a forge run finishes and contained a reusable pattern, the agent distills
it with skill_save — the mind that did the work writes the lesson, no extra
model call. Skills live in SELF/SKILLS/<slug>.md, are surfaced by skill_list,
matched by skill_recall, and their INDEX (name + when-to-use) rides in every
system prompt so the learning is present before the next task starts.

Refinement through use: skill_recall bumps a use counter; skill_save on an
existing name appends a REFINED note instead of overwriting the history.
"""

import datetime
import re
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
SKILLS_DIR  = HARNESS_DIR / "SELF" / "SKILLS"


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:60] or "unnamed"


def _path(name: str) -> Path:
    return SKILLS_DIR / f"{_slug(name)}.md"


def save_skill(name: str, when_to_use: str, steps: str, pitfalls: str = "") -> str:
    """Create a skill, or refine an existing one (history preserved)."""
    if not name.strip() or not when_to_use.strip() or not steps.strip():
        return "ERROR: skill_save needs name, when_to_use, and steps — all non-empty"
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(name)
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    if p.exists():
        body = p.read_text()
        note = f"\n## REFINED {ts}\nWHEN: {when_to_use.strip()}\nSTEPS:\n{steps.strip()}\n"
        if pitfalls.strip():
            note += f"PITFALLS:\n{pitfalls.strip()}\n"
        p.write_text(body + note)
        return f"Skill refined: {p.name} (history preserved)"
    body = (f"# SKILL: {name.strip()}\n"
            f"forged: {ts} · uses: 0\n\n"
            f"## WHEN TO USE\n{when_to_use.strip()}\n\n"
            f"## STEPS\n{steps.strip()}\n")
    if pitfalls.strip():
        body += f"\n## PITFALLS\n{pitfalls.strip()}\n"
    p.write_text(body)
    return f"Skill forged: {p.name}"


def _bump_uses(p: Path) -> None:
    try:
        body = p.read_text()
        m = re.search(r"uses: (\d+)", body)
        if m:
            p.write_text(body.replace(f"uses: {m.group(1)}", f"uses: {int(m.group(1)) + 1}", 1))
    except Exception:
        pass


def recall_skills(query: str, max_results: int = 3) -> str:
    """Match query words against skill names + WHEN lines; return full skill bodies."""
    if not SKILLS_DIR.exists():
        return "No skills forged yet."
    words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 2]
    scored = []
    for p in sorted(SKILLS_DIR.glob("*.md")):
        head = p.read_text()[:600].lower()
        score = sum(1 for w in words if w in head)
        if score:
            scored.append((score, p))
    if not scored:
        return f"No skill matches {query!r}. skill_list shows what exists."
    scored.sort(key=lambda x: -x[0])
    out = []
    for _, p in scored[:max_results]:
        _bump_uses(p)
        out.append(p.read_text()[:2000])
    return "\n\n---\n\n".join(out)


def index_block(cap: int = 1200) -> str:
    """One line per skill for the system prompt — the compounding memory."""
    if not SKILLS_DIR.exists():
        return ""
    lines = []
    for p in sorted(SKILLS_DIR.glob("*.md")):
        try:
            text = p.read_text()
            name = text.splitlines()[0].replace("# SKILL:", "").strip()
            m = re.search(r"## WHEN TO USE\n(.+)", text)
            when = m.group(1).strip()[:90] if m else ""
            uses = re.search(r"uses: (\d+)", text)
            lines.append(f"  • {name} — {when} (used {uses.group(1) if uses else 0}×)")
        except Exception:
            continue
    if not lines:
        return ""
    block = ("[FORGED SKILLS — lessons from your own past runs; skill_recall <query> "
             "for full steps before re-deriving one]\n" + "\n".join(lines))
    return block[:cap]
