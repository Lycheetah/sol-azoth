"""AZOTH SHELL — the custom face. A Textual app that owns the screen:
the chat bar is PINNED to the bottom (a real input box, like Claude Code),
a live status strip sits above it, and everything the agent does — tool
echoes, thinking traces, forge moves, chat — scrolls in the transcript pane.

The brain does not change: this is a new face wired onto the same Agent.
All agent output (rich console + bare print) is captured through a sink
console installed BEFORE agent.py imports, so `from ui import _console`
binds the sink everywhere.

Run: bash launch_shell.sh   (falls back to the classic REPL if textual is missing)
"""
import os, sys, threading, queue, contextlib, time

os.environ.setdefault("AZOTH_SINGLE_AGENT", "1")
os.environ["AZOTH_SHELL"] = "1"

# ── The sink: everything the agent prints lands here, the app drains it ──────
_OUT_Q: "queue.Queue[str]" = queue.Queue()

class _SinkIO:
    """File-like target for the agent's console + stdout. Thread-safe enough:
    Queue is the only shared state."""
    def write(self, s):
        if s:
            _OUT_Q.put(str(s))
        return len(s or "")
    def flush(self):  # noqa: D401
        pass
    def isatty(self):
        return False

from rich.console import Console as _RichConsole
from rich.text import Text as _RichText

_SINK = _SinkIO()
# force_terminal=True keeps color/dim ANSI in the stream; Text.from_ansi
# re-renders it faithfully inside the transcript.
_SINK_CONSOLE = _RichConsole(file=_SINK, force_terminal=True, width=110,
                             highlight=False, soft_wrap=True)

import ui as _ui_mod
_ui_mod._console = _SINK_CONSOLE          # must happen BEFORE agent imports
import agent as _agent_mod                # noqa: E402  (binds the sink console)

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, RichLog, Static
from textual import events


class BarInput(Input):
    """The chat bar — Input with ↑/↓ history that survives across sessions."""
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._hist: list[str] = []
        self._hist_i: int = 0
        self._hist_f = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "SELF", "prompt_history")
        try:
            with open(self._hist_f) as fh:
                # prompt_toolkit FileHistory format: lines starting '+' are entries
                self._hist = [l[1:].rstrip("\n") for l in fh if l.startswith("+")][-200:]
        except Exception:
            self._hist = []
        self._hist_i = len(self._hist)

    def remember(self, text: str) -> None:
        if text and (not self._hist or self._hist[-1] != text):
            self._hist.append(text)
            try:
                os.makedirs(os.path.dirname(self._hist_f), exist_ok=True)
                with open(self._hist_f, "a") as fh:
                    fh.write(f"\n# {time.strftime('%Y-%m-%d %H:%M:%S')}\n+{text}\n")
            except Exception:
                pass
        self._hist_i = len(self._hist)

    def on_key(self, event: events.Key) -> None:
        if event.key == "up" and self._hist:
            self._hist_i = max(0, self._hist_i - 1)
            self.value = self._hist[self._hist_i]
            self.cursor_position = len(self.value)
            event.prevent_default(); event.stop()
        elif event.key == "down" and self._hist:
            self._hist_i = min(len(self._hist), self._hist_i + 1)
            self.value = self._hist[self._hist_i] if self._hist_i < len(self._hist) else ""
            self.cursor_position = len(self.value)
            event.prevent_default(); event.stop()


class AzothShell(App):
    TITLE = "AZOTH"
    CSS = """
    Screen { background: $surface; }
    #topbar { dock: top; height: 1; background: $surface;
              color: $text-muted; padding: 0 1; }
    #log { border: none; padding: 0 1; scrollbar-size: 1 1; }
    #bottombox { dock: bottom; height: auto; }
    #status { height: 1; color: $text-muted; padding: 0 2; }
    #input { border: round $warning; }
    #input:focus { border: round $warning; }
    """
    BINDINGS = [
        Binding("ctrl+c", "cancel_or_quit", "cancel forge / quit", priority=True),
        Binding("ctrl+q", "hard_quit", "quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.agent = None
        self._busy = False
        self._sigint_t = 0.0

    def compose(self) -> ComposeResult:
        yield Static("", id="topbar")
        yield RichLog(id="log", wrap=True, markup=False, highlight=False, auto_scroll=True)
        with Vertical(id="bottombox"):
            yield Static("", id="status")
            yield BarInput(placeholder="waking…", id="input")

    # ── boot ──
    def on_mount(self) -> None:
        self._log = self.query_one("#log", RichLog)
        self._status = self.query_one("#status", Static)
        self._input = self.query_one("#input", BarInput)
        self._topbar = self.query_one("#topbar", Static)
        self.set_interval(0.08, self._drain)
        self.set_interval(0.5, self._tick_status)
        self.run_worker(self._boot_agent, thread=True, exclusive=False)

    def _boot_agent(self) -> None:
        with contextlib.redirect_stdout(_SINK):
            try:
                ag = _agent_mod.Agent()
                self.agent = ag
                # The wake, into the transcript: wordmark + self-knowledge.
                boot = _agent_mod.read_boot_state()
                _ui_mod.banner(_agent_mod.AGENT_NAME, boot.get("level", "?"),
                               ag.session_n, ag.model_key, "")
                ag._print_dashboard(boot_mode=True)
            except Exception as ex:
                _OUT_Q.put(f"\n✗ boot failed: {ex}\n")
                return
        self.call_from_thread(self._wake_done)

    def _wake_done(self) -> None:
        # (not named _ready: textual.App has an internal _ready coroutine,
        # and shadowing it crashes the mount — found the hard way.)
        self._input.placeholder = "speak, or /forge <goal> — /help for everything"
        self._input.focus()

    # ── output pump: sink → transcript, whole lines only ──
    _linebuf: str = ""

    def _drain(self) -> None:
        chunks = []
        try:
            while True:
                chunks.append(_OUT_Q.get_nowait())
        except queue.Empty:
            pass
        if not chunks:
            return
        self._linebuf += "".join(chunks)
        *lines, self._linebuf = self._linebuf.split("\n")
        for ln in lines:
            self._log.write(_RichText.from_ansi(ln))

    def _tick_status(self) -> None:
        ag = self.agent
        if not ag:
            self._topbar.update("☿ AZOTH — waking…")
            return
        tok = _agent_mod.SESSION_TOKENS.get("prompt", 0) + _agent_mod.SESSION_TOKENS.get("completion", 0)
        forging = getattr(ag, "_forge_active", False)
        if forging:
            state = f"☿ forge s{ag.forge_steps} — Ctrl+C cancels"
        elif self._busy:
            state = "⊚ thinking…"
        else:
            state = "idle"
        self._topbar.update(
            f"☿ ⊚ {_agent_mod.AGENT_NAME} · AZOTH SHELL · s{ag.session_n}")
        self._status.update(
            f"⊚ {ag.model_key} · {tok:,} tok · {state}")

    # ── input → the agent, on a worker thread ──
    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        self._input.value = ""
        if not text:
            return
        self._input.remember(text)
        cmd = text.lower().split()[0] if text.startswith("/") else ""
        if cmd in ("/quit", "/exit", "/q"):
            self.action_hard_quit()
            return
        self._log.write(_RichText.from_ansi(f"\x1b[1m ⊚ › {text}\x1b[0m"))
        if self._busy:
            if cmd == "/cancel" and self.agent:
                self.agent.cancel_event.set()
                self._log.write(_RichText("  ⚠ cancelling — forge stops at its next step"))
            else:
                self._log.write(_RichText("  ⚠ forge running — /cancel to stop it, or wait"))
            return
        self.run_worker(lambda: self._drive(text), thread=True, exclusive=False)

    def _drive(self, text: str) -> None:
        """Mirrors the classic REPL branch exactly — same brain, new face."""
        ag = self.agent
        if not ag:
            _OUT_Q.put("…still waking, one moment.\n")
            return
        self._busy = True
        try:
            with contextlib.redirect_stdout(_SINK):
                if text.startswith("/"):
                    ag.handle_command(text)
                elif ag._wants_tools(text):
                    _SINK_CONSOLE.print("[dim]☿ forge[/dim]")
                    ag.run_tool_loop(text)
                else:
                    ag.history.append({"role": "user", "content": text})
                    msgs = ([{"role": "system", "content": ag._system_prompt()}]
                            + ag.history[-20:])
                    content, _ = ag.call_model(msgs, stream=False)
                    if content:
                        ag.history.append({"role": "assistant", "content": content})
                        _SINK_CONSOLE.print("\n[bold yellow]⊚[/bold yellow]")
                        try:
                            from rich.markdown import Markdown as _RichMd
                            _SINK_CONSOLE.print(_RichMd(content))
                        except Exception:
                            _SINK_CONSOLE.print(content)
                        _SINK_CONSOLE.print("")
                    else:
                        _SINK_CONSOLE.print("[dim]⊚ (no response)[/dim]")
                    ag._maybe_autocompact()
        except SystemExit:
            self.call_from_thread(self.exit)
        except Exception as ex:
            _OUT_Q.put(f"\n✗ {ex}\n")
        finally:
            self._busy = False

    # ── actions ──
    def action_cancel_or_quit(self) -> None:
        ag = self.agent
        if ag and getattr(ag, "_forge_active", False):
            now = time.time()
            if now - self._sigint_t < 3.0:
                self.action_hard_quit()
                return
            self._sigint_t = now
            ag.cancel_event.set()
            self._log.write(_RichText("  ⚠ cancelling — forge stops at its next step (Ctrl+C again to quit)"))
        else:
            self.action_hard_quit()

    def action_hard_quit(self) -> None:
        try:
            if self.agent:
                with contextlib.redirect_stdout(_SINK):
                    self.agent._on_exit()
        except Exception:
            pass
        self.exit()


if __name__ == "__main__":
    AzothShell().run()
