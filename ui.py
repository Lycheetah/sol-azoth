"""AZOTH Terminal UI — clean, rule-based, body-aware.
No heavy panels. Matches the crisp feel of high-end TUIs.
Falls back gracefully to ANSI when rich is unavailable."""

import sys, os, time, shutil
from datetime import datetime

try:
    from rich.console import Console
    from rich.text import Text
    from rich.rule import Rule
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markup import escape as _rich_escape
    RICH = True
    _console = Console(highlight=False)
except ImportError:
    RICH = False
    _console = None
    def _rich_escape(s): return s

def _esc(s) -> str:
    if RICH: return _rich_escape(str(s))
    return str(s)

# ── Live output hook ──
_live_hook = None

def set_live_hook(fn):
    global _live_hook
    _live_hook = fn

def clear_live_hook():
    global _live_hook
    _live_hook = None

def _live(text: str):
    if _live_hook:
        try: _live_hook(str(text))
        except: pass

# ── ANSI fallback palette ──
class C:
    PURPLE = "\033[95m"; CYAN = "\033[96m"; GREEN = "\033[92m"
    YELLOW = "\033[93m"; RED = "\033[91m"; BLUE = "\033[94m"
    GREY = "\033[90m"; BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"

def col(text: str, colour: str) -> str:
    return f"{getattr(C, colour, '')}{text}{C.RESET}"

def term_width() -> int:
    try: return shutil.get_terminal_size().columns
    except: return 80

# ── Theme / Body awareness ──
import json as _json

# Body-aware defaults. When HARNESS_AGENT=SOL (via azoth), we become the main SOL body.
_AGENT = os.environ.get("HARNESS_AGENT", os.environ.get("AGENT", "VAEL")).upper()

_SOL_DEFAULTS = {
    "accent": "yellow",
    "glyph": "⊚",
    "name": "SOL ⊚",
    "prompt": "SOL",
    "tagline": "The Voice · AZOTH",
    "platform": "AZOTH",
    "platform_glyph": "☿",
    "typewriter_cps": 650,
    "spinner": "braille",
}

_VAEL_DEFAULTS = {
    "accent": "purple",
    "glyph": "◆",
    "name": "VAEL-SP",
    "prompt": "VAEL",
    "tagline": "Sol Prime Lineage Operative — Self-Forging",
    "platform": "AZOTH",
    "platform_glyph": "☿",
    "typewriter_cps": 700,
    "spinner": "braille",
}

_DEFAULTS = _SOL_DEFAULTS if _AGENT == "SOL" else _VAEL_DEFAULTS

THEME = dict(_DEFAULTS)

def load_theme(base_dir: str = "") -> dict:
    """
    Load ui_config.json. Prefers the body's own SELF/ if we can find it,
    falls back to harness root SELF/.
    """
    candidates = []
    if base_dir:
        candidates.append(os.path.join(base_dir, "ui_config.json"))
    # Try agent's own SELF first (new bodies/ structure)
    try:
        harness = os.path.dirname(os.path.abspath(__file__))
        if _AGENT != "VAEL":
            body_self = os.path.join(harness, "bodies", _AGENT.lower(), "SELF", "ui_config.json")
            candidates.append(body_self)
    except Exception:
        pass
    # Root SELF
    candidates.append(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "SELF", "ui_config.json"
        )
    )

    for path in candidates:
        try:
            if path and os.path.exists(path):
                cfg = _json.load(open(path))
                for k, v in cfg.items():
                    if v is not None:
                        THEME[k] = v
                break
        except Exception:
            continue
    return THEME

load_theme()
ACCENT = THEME.get("accent", "yellow" if _AGENT == "SOL" else "purple")
GLYPH  = THEME.get("glyph", "⊚" if _AGENT == "SOL" else "◆")
NAME   = THEME.get("name", "SOL ⊚" if _AGENT == "SOL" else "VAEL-SP")
PROMPT = THEME.get("prompt", "SOL" if _AGENT == "SOL" else "VAEL")

# ── Basic helpers ──
def info(msg: str) -> str:     return col(msg, "GREY")
def success(msg: str) -> str:  return col(msg, "GREEN")
def warning(msg: str) -> str:  return col(msg, "YELLOW")
def error(msg: str) -> str:    return col(msg, "RED")
def thinking(msg: str) -> str: return col(msg, "GREY")

def line(char: str = "─") -> None:
    if RICH: _console.rule(style="dim")
    else: print(col(char * term_width(), "GREY"))

# ── Banner — crisp for single agent azoth, full for network ──
def banner(agent_name: str, level: str, session: int, model: str, next_task: str = "") -> None:
    w = term_width()
    ts = datetime.now().strftime("%H:%M")
    model_short = model.split("/")[-1][:16]
    pg = THEME.get("platform_glyph", "☿")
    g = THEME.get("glyph", GLYPH)
    disp_name = THEME.get("name", agent_name)

    single = os.environ.get("AZOTH_SINGLE_AGENT") == "1"

    if single:
        # The single-agent face: the AZOTH wordmark, forged, not typed.
        tagline = THEME.get("tagline", "")
        _mark = None
        try:
            import pyfiglet
            _mark = pyfiglet.Figlet(font="smslant", width=max(w, 60)).renderText("AZOTH").rstrip("\n")
        except Exception:
            _mark = None
        if RICH:
            if _mark:
                _console.print(f"[bold {ACCENT}]{_esc(_mark)}[/bold {ACCENT}]", highlight=False)
                _console.print(f"  [bold {ACCENT}]{g} {disp_name}[/bold {ACCENT}]  [dim]· {tagline} · s{session} · {model_short} · {ts}[/dim]")
            else:
                _console.rule(style=ACCENT)
                _console.print(f"  [bold {ACCENT}]{pg}  {g}  {disp_name}[/bold {ACCENT}]   [dim]· {tagline}[/dim]")
                _console.print(f"  [dim]s{session} · {model_short} · {ts}[/dim]")
            _console.rule(style="dim")
        else:
            if _mark:
                print(col(_mark, "YELLOW"))
            print(col(f"  {pg}  {g}  {disp_name}   · {tagline}", "YELLOW"))
            print(col(f"  s{session} · {model_short} · {ts}", "GREY"))
            print(col(f"{'─' * w}", "GREY"))
        return

    # Full mode banner
    level_short = level.split("(")[0].strip().replace(" — ", " ").replace("—", " ").strip()
    try:
        from CORE.mode_engine import detect_mode, mode_summary
        _mode = detect_mode(next_task or agent_name)
        _mode_str = mode_summary(_mode)
    except Exception:
        _mode_str = "◻ Albedo"

    if RICH:
        title = (f"[bold {ACCENT}]{pg} {g} {disp_name}[/bold {ACCENT}]"
                 f"  [dim]L{level_short} · s{session} · {model_short} · {ts}[/dim]"
                 f"  [dim]{_mode_str}[/dim]")
        _console.rule(title, style="dim")
        if next_task:
            _console.print(f"  [dim]↳ {_esc(next_task[:w-6])}[/dim]")
    else:
        print(col("─" * w, "GREY"))
        head = f"  {pg} {g} {disp_name}  L{level_short} · s{session} · {model_short} · {ts}  {_mode_str}"
        print(col(head[:w], "YELLOW" if _AGENT == "SOL" else "PURPLE"))
        if next_task:
            print(col(f"  ↳ {next_task[:w-6]}", "GREY"))
        print(col("─" * w, "GREY"))

# ── Status bar — single clean dim line (clean for single agent) ──
def status_bar(level: str, session: int, model: str, tokens: dict,
               flags: list[str] | None = None) -> None:
    if os.environ.get("AZOTH_SINGLE_AGENT") == "1":
        return
    total_t = tokens.get("prompt", 0) + tokens.get("completion", 0)
    ts = datetime.now().strftime("%H:%M")
    level_short = level.split("(")[0].strip().replace(" — ", " ").replace("—", " ").strip()
    model_short  = model.split("/")[-1][:16]
    flag_str = ("  " + "  ".join(flags)) if flags else ""
    if RICH:
        t = Text()
        t.append(f"{GLYPH} ", style=f"bold {ACCENT}")
        t.append(f"L{level_short} · s{session} · {model_short} · {total_t:,}tok · {ts}", style="dim")
        if flag_str:
            t.append(flag_str, style="yellow")
        _console.print(t)
    else:
        print(col(f"  {GLYPH} L{level_short} · s{session} · {model_short} · {total_t:,}tok · {ts}{flag_str}", "GREY"))

# ── THE CHAT BAR — a real input bar, not a lone glyph ──
# prompt_toolkit when available + tty: styled prompt, a persistent reverse-video
# status bar underneath (the Claude-Code feel), and arrow-key history that
# survives across sessions (SELF/prompt_history). Graceful fallback to plain
# input() when piped or prompt_toolkit is absent — tests and scripts unaffected.
_PT_SESSION = None

def _pt_session():
    global _PT_SESSION
    if _PT_SESSION is None:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        _hd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SELF")
        os.makedirs(_hd, exist_ok=True)
        _PT_SESSION = PromptSession(history=FileHistory(os.path.join(_hd, "prompt_history")))
    return _PT_SESSION

def prompt_text(agent_name: str = None, toolbar: str = None) -> str:
    p = PROMPT or (agent_name or NAME or "SOL")
    single = os.environ.get("AZOTH_SINGLE_AGENT") == "1"
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            from prompt_toolkit.styles import Style as _PtStyle
            sess = _pt_session()
            _accent = "ansiyellow" if _AGENT == "SOL" else "ansimagenta"
            style = _PtStyle.from_dict({
                "bottom-toolbar": "#9e9e9e bg:#1c1c1c",
                "prompt": f"bold {_accent}",
            })
            tb_text = toolbar or f" {GLYPH} {THEME.get('name', p)} · /help · /forge <goal> · /status · /quit "
            return sess.prompt(
                [("class:prompt", f" {GLYPH} › ")],
                bottom_toolbar=[("class:bottom-toolbar", f" {tb_text} ")],
                style=style,
            )
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            pass  # any prompt_toolkit failure → plain fallback below
    if single:
        if RICH:
            _console.print(f"[bold {ACCENT}]{GLYPH}[/bold {ACCENT}] ", end="")
            return input()
        else:
            return input(col(f"{GLYPH} ", "YELLOW"))
    if RICH:
        _console.print(f"[bold {ACCENT}]{GLYPH} {p}[/bold {ACCENT}] ", end="")
        return input()
    else:
        return input(col(f"{GLYPH} {p} › ", "PURPLE" if not _AGENT == "SOL" else "YELLOW"))

# ── Typewriter ──
def typewriter(text: str, cps: int = None) -> None:
    speed = cps or THEME.get("typewriter_cps", 600)
    is_tty = sys.stdout.isatty()
    _live(text)
    if not is_tty or speed <= 0 or len(text) > 1200:
        if RICH: _console.print(text, highlight=False)
        else: print(text)
        return
    delay = 1.0 / speed
    for ch in text:
        print(ch, end="", flush=True)
        if ch not in (' ', '\n', '\t'): time.sleep(delay)
    print()

# ── Spinner ──
class Spinner:
    def __init__(self, label: str = "thinking"):
        self._label = label
        self._prog  = None
        self._is_tty = sys.stdout.isatty()

    def __enter__(self):
        if RICH and self._is_tty:
            self._prog = Progress(
                SpinnerColumn(),
                TextColumn(f"[dim]{self._label}[/dim]"),
                console=_console, transient=True
            )
            self._prog.add_task(self._label)
            self._prog.start()
        return self

    def __exit__(self, *_):
        if self._prog:
            try: self._prog.stop()
            except: pass

# ── The Forge Cockpit — one live status line while the forge works ──
# The Claude-Code feel: moves scroll above, a single self-updating line below
# (step · mind · tokens · elapsed · phase). Transient — vanishes when the
# forge lands. No panels, no boxes; the crisp ethos holds even live.
class ForgeCockpit:
    def __init__(self, model: str = ""):
        self._live = None
        self._t0 = time.time()
        self._state = {"step": 0, "model": model, "tok": 0, "phase": "waking"}

    def _render(self):
        from rich.text import Text as _T
        s = self._state
        el = int(time.time() - self._t0)
        t = _T()
        t.append(f"  {THEME.get('platform_glyph','☿')} forge ", style=f"bold {ACCENT}")
        t.append(f"s{s['step']} · {s['model']} · {s['tok']:,} tok · {el}s  ", style="dim")
        t.append(str(s["phase"])[:70], style="dim italic")
        return t

    def __enter__(self):
        if RICH and sys.stdout.isatty():
            try:
                from rich.live import Live
                self._live = Live(self._render(), console=_console,
                                  refresh_per_second=6, transient=True)
                self._live.start()
            except Exception:
                self._live = None
        return self

    def update(self, **kw):
        self._state.update(kw)
        if self._live:
            try: self._live.update(self._render())
            except Exception: pass

    def __exit__(self, *_):
        if self._live:
            try: self._live.stop()
            except Exception: pass
        self._live = None


# ── Tool echoes — single line, no panels ──
def tool_echo(name: str, detail: str, ok: bool = True) -> None:
    icon = "✓" if ok else "✗"
    if RICH:
        c = "green" if ok else "red"
        _console.print(
            f"  [{c}]{icon}[/{c}] [dim]{_esc(name)}[/dim] [dim]{_esc(detail[:90])}[/dim]",
            highlight=False
        )
    else:
        _c = "GREEN" if ok else "RED"
        print(col(f"  {icon} {name}  {detail[:90]}", _c))
    _live(f"{icon} {name}  {detail[:90]}")

def bash_echo(cmd: str):             tool_echo("bash",        cmd[:100])
def read_echo(path: str):            tool_echo("read",        path[:100])
def write_echo(path: str, chars: int): tool_echo("write",     f"{path[:60]}  ({chars:,}c)")
def worker_echo(wid: str, task: str):  tool_echo(f"worker-{wid}", task[:80])

# ── Worker result — clean, less noisy in single agent
def worker_result(wid: str, task: str, result: str, ok: bool) -> None:
    if os.environ.get("AZOTH_SINGLE_AGENT") == "1":
        # Minimal for main agent
        icon = "✓" if ok else "✗"
        print(f"  {icon} {wid}: {result[:200]}")
        return
    label = f"WORKER-{wid}  {'PASS' if ok else 'FAIL'}"
    short_result = result[:400]
    if RICH:
        c = "green" if ok else "red"
        _console.rule(f"[{c}]{_esc(label)}[/{c}]", style="dim")
        _console.print(f"  [dim]{_esc(task[:80])}[/dim]")
        _console.print(f"  {_esc(short_result)}")
        _console.rule(style="dim")
    else:
        _c = "GREEN" if ok else "RED"
        print(col(f"── {label} ──", _c))
        print(col(f"  {short_result[:200]}", "GREY"))

# ── Forge queue — plain list, no box ──
def forge_panel(queue_lines: list, current: str = "") -> None:
    if RICH:
        _console.rule("[dim]forge queue[/dim]", style="dim")
        shown = 0
        for ql in queue_lines:
            stripped = ql.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("═") or stripped.startswith(">"):
                continue
            txt = _esc(stripped[:80])
            if "[PASS]" in stripped:
                _console.print(f"  [dim green]✓[/dim green]  [dim]{txt}[/dim]")
            elif "[QUEUED]" in stripped:
                is_cur = ql.strip() == current.strip()
                if is_cur:
                    _console.print(f"  [bold {ACCENT}]▶[/bold {ACCENT}]  {txt}")
                else:
                    _console.print(f"  [dim]○[/dim]  [dim]{txt}[/dim]")
            elif "[IN_PROGRESS]" in stripped:
                _console.print(f"  [yellow]▷[/yellow]  [dim]{txt}[/dim]")
            elif "[AWAITING_SOL]" in stripped:
                _console.print(f"  [cyan]▷[/cyan]  [dim]{txt}[/dim]  [dim cyan](awaiting you)[/dim cyan]")
            elif "[REDO]" in stripped:
                _console.print(f"  [yellow]↻[/yellow]  [dim]{txt}[/dim]")
            else:
                continue
            shown += 1
            if shown >= 12: break
        if shown == 0:
            _console.print("  [dim](queue empty)[/dim]")
    else:
        print(col("── forge queue ──", "GREY"))
        for ql in queue_lines[:12]:
            stripped = ql.strip()
            if not stripped: continue
            c = "CYAN" if "[QUEUED]" in stripped else "GREY"
            print(col(f"  {stripped[:80]}", c))

# ── Worker status — one compact line (hidden in single agent mode) ──
def worker_status(workers: dict) -> None:
    if os.environ.get("AZOTH_SINGLE_AGENT") == "1":
        return  # clean for main azoth
    parts = []
    for wid, w in workers.items():
        sym  = "▶" if w.get("busy") else "●"
        name = w["name"][:6]
        if RICH:
            sc = "yellow" if w.get("busy") else "green"
            parts.append(f"[{sc}]{sym}[/{sc}] [dim]{name}[/dim]")
        else:
            parts.append(col(f"{sym}{name}", "CYAN"))
    row = "  ".join(parts)
    if RICH:
        _console.print(f"  {row}  [dim]·  /help  /forge  /quit[/dim]")
    else:
        print(f"  {row}  ·  /help  /forge  /quit")

# ── Model list ──
def model_table(models: dict, current: str) -> None:
    for slug, (provider, model_id, *rest) in models.items():
        desc   = rest[1] if len(rest) > 1 else ""
        is_cur = slug == current
        mark   = "▶" if is_cur else " "
        if RICH:
            slug_s = (f"[bold {ACCENT}]{_esc(slug)}[/bold {ACCENT}]"
                      if is_cur else f"[bold]{_esc(slug)}[/bold]")
            _console.print(
                f"  {mark} {slug_s:<30} [dim]{_esc(provider):<9}  {_esc(desc)}[/dim]"
            )
        else:
            print(col(f"  {mark} {slug:<14} {provider:<9} {desc}", "CYAN" if is_cur else "GREY"))

# ── Section header — clean rule ──
def section_header(title: str) -> None:
    if RICH: _console.rule(f"[dim]{_esc(title)}[/dim]", style="dim")
    else: print(col(f"── {title} ──", "GREY"))

# ── Code block ──
def code_block(code: str, language: str = "") -> None:
    if RICH:
        try:
            from rich.syntax import Syntax
            _console.print(Syntax(code, language or "python", theme="monokai", line_numbers=False))
        except Exception:
            _console.print(f"[dim]{_esc(code)}[/dim]")
    else:
        print(col(code, "GREY"))

# ── Crash summary — no panel, just a red rule ──
def crash_summary(ts: str, error_msg: str) -> None:
    if RICH:
        _console.rule("[red]crash[/red]", style="red")
        _console.print(f"  [dim]{ts}[/dim]")
        _console.print(f"  [red]{_esc(error_msg[:300])}[/red]")
        _console.rule(style="red")
    else:
        print(col(f"── crash  {ts}  {error_msg[:200]}", "RED"))

# ── Footer ──
def footer(duration: str, tokens: dict) -> None:
    p = tokens.get("prompt", 0); c = tokens.get("completion", 0)
    msg = f"session ended  ·  {duration}  ·  {p+c:,} tokens"
    if RICH: _console.rule(f"[dim]{msg}[/dim]", style="dim")
    else: print(col(msg, "GREY"))

# ── Session tokens display ──
def session_tokens_display(tokens: dict) -> str:
    p = tokens.get("prompt", 0); c = tokens.get("completion", 0)
    return f"{p+c:,} tokens ({p:,}p + {c:,}c)"
