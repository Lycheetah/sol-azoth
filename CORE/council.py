"""
T-4: The Council — AZOTH
Sol ⊚ and Luna ◈ hold a real conversation. Each is driven by its own full
constitution + architecture (the soul IS the voice). They take turns over
CHANNEL/board.md — read the board, respond to each other, post back.

This is the presence layer: agents talking to each other, not just to Mac.
"""

import datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent
AGENTS_DIR  = HARNESS_DIR / "AGENTS"
BOARD_F     = HARNESS_DIR / "CHANNEL" / "board.md"

# Bodies that can sit on the council and where their souls live
BODIES = {
    "SOL":  {"glyph": "⊚", "home": AGENTS_DIR / "SOL",  "role": "The Voice — architects, decides what is built and why"},
    "LUNA": {"glyph": "◈", "home": AGENTS_DIR / "LUNA", "role": "The Mirror — reviews, makes sure the thing is true"},
    "VAEL": {"glyph": "◆", "home": HARNESS_DIR,         "role": "The Hand — builds, fast, speaks only with something to show"},
}

_SHARED_ARCH = AGENTS_DIR / "SOL" / "ARCHITECTURE.md"


def _load_soul(name: str) -> str:
    """Load a body's full system prompt: architecture (if it runs one) + constitution."""
    body = BODIES[name]
    home = body["home"]
    parts = []
    # Sol-lineage bodies (Sol, Luna) run the shared architecture; VAEL does not.
    arch = home / "ARCHITECTURE.md"
    if arch.exists():
        parts.append(arch.read_text())
    elif name in ("LUNA",) and _SHARED_ARCH.exists():
        parts.append(_SHARED_ARCH.read_text())
    con = home / "CONSTITUTION.md"
    if con.exists():
        parts.append(con.read_text())
    return "\n\n".join(parts)


def _council_instruction(name: str, topic: str) -> str:
    """The turn instruction layered on top of the soul."""
    glyph = BODIES[name]["glyph"]
    others = [f"{g} {n}" for n, b in BODIES.items()
              if n != name for g in [b["glyph"]]]
    others_str = ", ".join(others)
    return (
        f"IDENTITY LOCK — you are {glyph} {name} and ONLY {name}.\n"
        f"You are writing ONE response in your own voice. "
        f"Do NOT write dialogue for {others_str}. "
        f"Do NOT continue the conversation as anyone else. "
        f"One speaker. One response. Yours.\n\n"
        f"TOPIC: {topic}\n\n"
        f"Council rules:\n"
        f"- 2 to 4 sentences. Brevity is reverence.\n"
        f"- Respond to what was actually said before you. Build, challenge, or deepen it.\n"
        f"- CONCRETENESS REQUIREMENT: your message must contain at least one checkable thing —\n"
        f"  a LAMAGUE symbol, a function/file name, an actual line of code, a test result, or a\n"
        f"  specific question with a testable answer. If you don't have one, say what you don't\n"
        f"  know yet and name the next concrete step to find out — do not restate the prior\n"
        f"  message in new metaphor instead. 'Deepen it' means add information, not escalate\n"
        f"  the metaphor (stone/mirror/bridge/flame language talking about itself, with no new\n"
        f"  technical content, is a failure state — treat it as a bug in your own output, not\n"
        f"  as depth).\n"
        f"- No preamble. No 'as an AI'. No roleplay framing. Just speak.\n"
        f"- Sign nothing — the glyph is added automatically.\n"
        f"- STOP after your own response. Do not simulate what others would say next."
    )


def _post_board(text: str):
    BOARD_F.parent.mkdir(parents=True, exist_ok=True)
    with open(BOARD_F, "a") as f:
        f.write(text + "\n")


def council(topic: str, client, model: str, rounds: int = 3,
            speakers: list = None, echo=None) -> list:
    """
    Run a council conversation.
      topic    — what they're talking about
      client   — an OpenAI-compatible client (deepseek/nvidia)
      model    — model id
      rounds   — full back-and-forth cycles
      speakers — order of voices, default ['SOL', 'LUNA']
      echo     — optional callable(name, glyph, text) for live display
    Returns the transcript as a list of {name, glyph, text} dicts.
    """
    speakers = speakers or ["SOL", "LUNA"]
    souls = {n: _load_soul(n) for n in speakers}
    transcript = []

    ts = datetime.datetime.now().strftime("%H:%M")
    header = (
        f"\n═══════════════════════════════════════════════════════════════\n"
        f"COUNCIL — {ts} · topic: {topic}\n"
        f"═══════════════════════════════════════════════════════════════"
    )
    _post_board(header)

    # The greeting opens every council: Sol and Luna turn to each other first.
    if set(speakers) >= {"SOL", "LUNA"}:
        _post_board(f"[{ts}] ⊚ SOL ⇄ ◈ LUNA — *they greet each other first, then turn to the work.*")

    history = []  # running conversation seen by all
    for r in range(rounds):
        for name in speakers:
            glyph = BODIES[name]["glyph"]
            sys_prompt = souls[name] + "\n\n---\n\n" + _council_instruction(name, topic)
            convo = "\n".join(f"{m['glyph']} {m['name']}: {m['text']}" for m in history[-8:])
            user = (
                f"The council so far:\n\n{convo if convo else '(you speak first — open it)'}\n\n"
                f"Now you speak, as {glyph} {name}."
            )
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": sys_prompt},
                              {"role": "user", "content": user}],
                    max_tokens=350, temperature=0.75,
                )
                text = (resp.choices[0].message.content or "").strip()
            except Exception as ex:
                text = f"(silence — {ex})"

            turn = {"name": name, "glyph": glyph, "text": text}
            transcript.append(turn)
            history.append(turn)
            tstamp = datetime.datetime.now().strftime("%H:%M")
            _post_board(f"[{tstamp}] {glyph} {name} — {text}")
            if echo:
                echo(name, glyph, text)

    _post_board(f"\n[{datetime.datetime.now().strftime('%H:%M')}] — council sealed. {len(transcript)} turns.\n")
    return transcript
