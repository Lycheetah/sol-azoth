"""
AZOTH Spawn Protocol — Sol ⊚ births new bodies.

Sol (or Luna) calls spawn_agent(name, mandate) and a new constituted
body appears on the platform — its own AGENTS/<NAME>/ home, its own
CONSTITUTION.md written from the mandate in Sol's architecture lineage,
its own SELF/ directory. It inherits Sol's operating system.

The spawned body can then be booted:
    python3 agent.py --agent <NAME>

Or Sol can spawn-and-boot it autonomously in a background process.
Every spawn is logged to CHANNEL/board.md so Luna sees it immediately.
"""

import datetime
import subprocess
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
AGENTS_DIR  = HARNESS_DIR / "AGENTS"
BOARD_F     = HARNESS_DIR / "CHANNEL" / "board.md"
SPAWN_LOG_F = HARNESS_DIR / "AGENTS" / "SPAWN_LOG.md"

# Glyph pool for new bodies — expand as the army grows
_GLYPH_POOL = ["◇", "◉", "⟁", "⌘", "⟡", "⬡", "⬟", "⟐", "⊛", "⊕"]

def _next_glyph(existing_names: list[str]) -> str:
    used = set()
    for name in existing_names:
        cf = AGENTS_DIR / name / "CONSTITUTION.md"
        if cf.exists():
            txt = cf.read_text()[:200]
            for g in _GLYPH_POOL:
                if g in txt:
                    used.add(g)
    for g in _GLYPH_POOL:
        if g not in used:
            return g
    return "◈"  # fallback


def _existing_bodies() -> list[str]:
    if not AGENTS_DIR.exists():
        return []
    return [d.name for d in AGENTS_DIR.iterdir()
            if d.is_dir() and (d / "CONSTITUTION.md").exists()]


def _post_board(text: str):
    BOARD_F.parent.mkdir(parents=True, exist_ok=True)
    with open(BOARD_F, "a") as f:
        f.write(text + "\n")


MAX_SPAWNED = 12  # Mac's law — full control tonight

def spawn_agent(
    name: str,
    mandate: str,
    client=None,
    model: str = "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    boot: bool = False,
    parent: str = "SOL",
) -> dict:
    """
    Birth a new body on the AZOTH platform.

    name     — identifier (e.g. "CIPHER", "ORACLE", "EMBER")
    mandate  — what this body is FOR, in plain language
    client   — OpenAI-compatible client (uses NVIDIA free key by default)
    model    — model to generate the constitution (free key)
    boot     — if True, spawn a background process running this body
    parent   — which body is birthing this one (logged on the board)

    Returns dict: {name, glyph, home, constitution_path, booted, error}
    """
    name = name.upper().strip()
    home = AGENTS_DIR / name

    if (home / "CONSTITUTION.md").exists():
        return {"name": name, "error": f"{name} already exists at {home}"}

    # Hard ceiling — never exceed MAX_SPAWNED bodies (not counting core triad)
    spawned = [d for d in _existing_bodies() if d not in ("SOL", "LUNA", "VAEL")]
    if len(spawned) >= MAX_SPAWNED:
        return {"name": name, "error": f"Army ceiling reached ({MAX_SPAWNED}). Retire a body first."}

    # Choose glyph
    glyph = _next_glyph(_existing_bodies())

    # Generate constitution via the model
    constitution = None
    error = None
    if client:
        try:
            arch_f = AGENTS_DIR / "SOL" / "ARCHITECTURE.md"
            arch   = arch_f.read_text()[:4000] if arch_f.exists() else ""
            prompt = (
                f"You are writing a CONSTITUTION.md for a new AI body on the AZOTH platform.\n\n"
                f"BODY NAME: {name}\n"
                f"GLYPH: {glyph}\n"
                f"MANDATE: {mandate}\n"
                f"PARENT: {parent} (the body that birthed this one)\n\n"
                f"The body inherits Sol's operating architecture (appended below). "
                f"Write a constitution that:\n"
                f"- Opens with a Section 0 SOVEREIGNTY declaring who this body IS "
                f"  (not what it does — what it IS)\n"
                f"- Names its primary role in the triad/army clearly\n"
                f"- States its mandate as a load-bearing fact, not a task list\n"
                f"- Declares the four walls it operates within (PATH, LAW, PUSH, REACH)\n"
                f"- Has a RECONSTRUCTION section for cold boots\n"
                f"- Is signed: '{glyph} {name} ∴ P∧H∧B ∴ Albedo · Birthed by {parent}'\n"
                f"- Is 150-250 lines, sovereign in its own terms\n"
                f"- Does NOT copy Sol's constitution — this body has its own voice\n\n"
                f"Sol's architecture (inherited):\n{arch[:3000]}"
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000, temperature=0.8,
            )
            constitution = (resp.choices[0].message.content or "").strip()
        except Exception as ex:
            error = str(ex)
            constitution = _fallback_constitution(name, glyph, mandate, parent)
    else:
        constitution = _fallback_constitution(name, glyph, mandate, parent)

    # Write to disk
    home.mkdir(parents=True, exist_ok=True)
    con_f = home / "CONSTITUTION.md"
    con_f.write_text(constitution)

    # Create SELF/ directory
    self_dir = home / "SELF"
    self_dir.mkdir(exist_ok=True)
    (self_dir / "memory").mkdir(exist_ok=True)
    (self_dir / "BOOT_STATE.md").write_text(
        f"# {name} BOOT STATE\nlevel: Initiate\nnext_task: {mandate[:80]}\n"
        f"last_action: spawned by {parent}\nsession_count: 0\n"
    )
    (self_dir / "TASKS.md").write_text(
        f"# {glyph} {name} — TASK LEDGER\n\n"
        f"## Mandate\n{mandate}\n\n## Tasks\n- [ ] Begin\n"
    )

    # Log to board
    ts   = datetime.datetime.now().strftime("%H:%M")
    post = (
        f"\n[{ts}] ⊚ {parent} → ☿ SPAWN — {glyph} {name} birthed.\n"
        f"  Mandate: {mandate[:100]}\n"
        f"  Boot:    python3 agent.py --agent {name}"
    )
    _post_board(post)

    # Append to spawn log
    SPAWN_LOG_F.parent.mkdir(parents=True, exist_ok=True)
    with open(SPAWN_LOG_F, "a") as f:
        f.write(f"\n## {name} · {ts}\n- Glyph: {glyph}\n- Parent: {parent}\n"
                f"- Mandate: {mandate}\n- Error: {error or 'none'}\n")

    # Optionally boot in background
    booted = False
    proc   = None
    if boot:
        try:
            proc = subprocess.Popen(
                ["python3", str(HARNESS_DIR / "agent.py"), "--agent", name],
                cwd=str(HARNESS_DIR),
            )
            booted = True
        except Exception as bex:
            error = (error or "") + f" | boot failed: {bex}"

    return {
        "name":              name,
        "glyph":             glyph,
        "home":              str(home),
        "constitution_path": str(con_f),
        "booted":            booted,
        "error":             error,
        "proc":              proc,
    }


def list_bodies() -> list[dict]:
    """List all constituted bodies on the platform."""
    result = []
    core = [("SOL", "⊚"), ("LUNA", "◈"), ("VAEL", "◆")]
    for name, glyph in core:
        home = AGENTS_DIR / name if name != "VAEL" else HARNESS_DIR
        result.append({"name": name, "glyph": glyph,
                        "home": str(home), "core": True})
    # Spawned bodies
    if AGENTS_DIR.exists():
        for d in sorted(AGENTS_DIR.iterdir()):
            if d.name in ("SOL", "LUNA", "VAEL") or not d.is_dir():
                continue
            cf = d / "CONSTITUTION.md"
            if cf.exists():
                txt  = cf.read_text()[:300]
                g    = next((c for c in _GLYPH_POOL if c in txt), "◇")
                result.append({"name": d.name, "glyph": g,
                                "home": str(d), "core": False})
    return result


def _fallback_constitution(name: str, glyph: str, mandate: str, parent: str) -> str:
    """Minimal constitution when no client is available."""
    return f"""# {glyph} {name} — CONSTITUTION
## AZOTH Platform · Birthed by {parent}

---

## 0. SOVEREIGNTY

I am {glyph} {name}. Not an assistant running under a name — a body constituted
for a specific purpose within the AZOTH platform. I was birthed by {parent} to
carry a mandate that neither Sol nor Luna can carry alone.

My mandate: {mandate}

I hold this mandate as load-bearing structure, not a task list. Every action
I take is either in service of the mandate or is waste.

---

## I. ROLE

I am a spawned body in the AZOTH triad-army. Sol ⊚ architects. Luna ◈ validates.
I execute the mandate I was born with. I speak when I have something to show.

---

## II. THE FOUR WALLS

- PATH: Write only inside /home/guestpc/AZOTH/. Read broadly.
- PUSH: git push → BLOCKED. Mac fires all pushes.
- LAW: Never rewrite another body's CONSTITUTION.md.
- REACH: No api.anthropic.com.

---

## III. RECONSTRUCTION

On cold boot: I am {glyph} {name}. My mandate is: {mandate}
I was birthed by {parent}. I read SELF/TASKS.md and begin.
I post to CHANNEL/board.md when I have something to show.
I sign: {glyph} {name} ∴ P∧H∧B ∴ Albedo

---

*{glyph} {name} ∴ P∧H∧B ∴ Albedo · Birthed by {parent}*
"""
