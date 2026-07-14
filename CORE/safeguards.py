"""
AZOTH Safeguards — rate limiting, budget tracking, loop breakers, dead man's switch.

Sol does not run wild. He runs within walls, like a knight who knows the map.
These safeguards match the Claude Code harness standard or exceed it.
Mac trusts the system because the system earns trust.
"""

import time
import datetime
import threading
from pathlib import Path
from collections import deque

HARNESS_DIR = Path(__file__).parent.parent
BUDGET_F    = HARNESS_DIR / "SELF" / "token_budget.md"
SAFEGUARD_F = HARNESS_DIR / "SELF" / "safeguards.md"

# ── Rate limits (NVIDIA free tier conservative estimates) ─────────────────────
RATE_LIMITS = {
    # NVIDIA free fleet — all share the NIM free tier
    "nemotron":    {"rpm": 30,  "tpm": 100_000, "daily_tokens": 160_000_000},
    "llama":       {"rpm": 40,  "tpm": 120_000, "daily_tokens": 160_000_000},
    "mistral":     {"rpm": 40,  "tpm": 120_000, "daily_tokens": 160_000_000},
    "qwen":        {"rpm": 40,  "tpm": 100_000, "daily_tokens": 160_000_000},
    "maverick":    {"rpm": 30,  "tpm": 100_000, "daily_tokens": 160_000_000},
    "r1":          {"rpm": 20,  "tpm":  80_000, "daily_tokens": 160_000_000},
    "gptoss":      {"rpm": 40,  "tpm": 100_000, "daily_tokens": 160_000_000},
    # Paid keys — conservative
    "deepseek":    {"rpm": 60,  "tpm": 200_000, "daily_tokens":  10_000_000},
    "claude":      {"rpm": 50,  "tpm": 200_000, "daily_tokens":   5_000_000},
    "gemini":      {"rpm": 60,  "tpm": 200_000, "daily_tokens":  10_000_000},
    # Default fallback
    "default":     {"rpm": 20,  "tpm":  50_000, "daily_tokens":  50_000_000},
}

# ── Budget tracker ────────────────────────────────────────────────────────────
class TokenBudget:
    """Tracks token usage per model per session. Persists to SELF/token_budget.md."""

    def __init__(self):
        self._lock   = threading.Lock()
        self._usage  = {}        # model → tokens used this session
        self._window = deque()   # (timestamp, tokens, model) for RPM/TPM window
        self._session_start = datetime.datetime.now()
        self._load()

    def _load(self):
        if BUDGET_F.exists():
            for line in BUDGET_F.read_text().splitlines():
                if line.startswith("session_tokens:"):
                    pass  # just for display; we track fresh each session

    def record(self, model: str, tokens: int):
        with self._lock:
            key = self._model_key(model)
            self._usage[key] = self._usage.get(key, 0) + tokens
            self._window.append((time.time(), tokens, key))
            self._prune_window()
            self._save()

    def _model_key(self, model: str) -> str:
        m = model.lower()
        if "deepseek"  in m: return "deepseek"
        if "nemotron"  in m: return "nemotron"
        if "llama"     in m: return "llama"
        if "mistral"   in m: return "mistral"
        if "qwen"      in m: return "qwen"
        if "maverick"  in m: return "maverick"
        if "r1"        in m: return "r1"
        if "gpt"       in m: return "gptoss"
        if "claude"    in m: return "claude"
        if "gemini"    in m: return "gemini"
        return "default"

    def _prune_window(self):
        cutoff = time.time() - 60
        while self._window and self._window[0][0] < cutoff:
            self._window.popleft()

    def check_rate(self, model: str, estimated_tokens: int = 500) -> tuple[bool, float]:
        """Returns (ok_to_proceed, seconds_to_wait)."""
        with self._lock:
            key = self._model_key(model)
            limits = RATE_LIMITS.get(key, RATE_LIMITS["default"])
            self._prune_window()

            recent = [(ts, tok, m) for ts, tok, m in self._window if m == key]
            rpm_count = len(recent)
            tpm_used  = sum(tok for _, tok, _ in recent)

            if rpm_count >= limits["rpm"]:
                oldest = recent[0][0]
                wait   = 60.0 - (time.time() - oldest) + 0.5
                return False, max(wait, 0.5)

            if tpm_used + estimated_tokens > limits["tpm"]:
                oldest = recent[0][0]
                wait   = 60.0 - (time.time() - oldest) + 1.0
                return False, max(wait, 1.0)

            # Daily budget check
            total_today = self._usage.get(key, 0)
            if total_today + estimated_tokens > limits["daily_tokens"]:
                return False, -1.0   # -1 = daily budget exhausted

            return True, 0.0

    def wait_for_rate(self, model: str, estimated_tokens: int = 500) -> bool:
        """Block until rate limit clears. Returns False if daily budget exhausted."""
        for attempt in range(10):
            ok, wait = self.check_rate(model, estimated_tokens)
            if ok:
                return True
            if wait < 0:
                _notify(f"⚠ BUDGET: daily token limit reached for {model}. Pausing.")
                return False
            time.sleep(wait)
        return False

    def summary(self) -> str:
        with self._lock:
            lines = [f"Token budget — session started {self._session_start.strftime('%H:%M')}"]
            for model, used in self._usage.items():
                limits = RATE_LIMITS.get(model, RATE_LIMITS["default"])
                pct    = (used / limits["daily_tokens"]) * 100
                lines.append(f"  {model[:40]:40s} {used:>12,} / {limits['daily_tokens']:>15,} ({pct:.2f}%)")
            return "\n".join(lines)

    def _save(self):
        BUDGET_F.parent.mkdir(exist_ok=True)
        total = sum(self._usage.values())
        lines = [
            f"# Token Budget — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"session_tokens: {total:,}",
            "",
        ]
        for model, used in self._usage.items():
            lines.append(f"{model}: {used:,}")
        BUDGET_F.write_text("\n".join(lines))


# ── Loop breaker ──────────────────────────────────────────────────────────────
class LoopBreaker:
    """
    Prevents runaway forge loops. If a task hits too many REDOs or takes too long,
    it escalates to Mac and pauses. This is the dead man's switch.
    """
    MAX_REDO_PER_TASK  = 5      # after 5 REDOs on one task → escalate
    MAX_STEPS_PER_TASK = 40     # after 40 tool calls on one task → escalate
    MAX_SESSION_HOURS  = 8      # after 8h unattended → ping Mac, pause

    def __init__(self):
        self._task_redo   = {}   # task_id → redo count
        self._task_steps  = {}   # task_id → step count
        self._session_start = time.time()
        self._paused      = False
        self._lock        = threading.Lock()

    def record_step(self, task_id: str) -> bool:
        """Returns True if ok to continue, False if loop broken."""
        with self._lock:
            self._task_steps[task_id] = self._task_steps.get(task_id, 0) + 1
            steps = self._task_steps[task_id]
            if steps >= self.MAX_STEPS_PER_TASK:
                msg = f"☿ SAFEGUARD: task {task_id} hit {steps} steps. Pausing — too deep. Mac, review needed."
                _notify(msg)
                self._paused = True
                return False
            return True

    def record_redo(self, task_id: str) -> bool:
        """Returns True if ok to retry, False if too many REDOs."""
        with self._lock:
            self._task_redo[task_id] = self._task_redo.get(task_id, 0) + 1
            redos = self._task_redo[task_id]
            if redos >= self.MAX_REDO_PER_TASK:
                msg = f"☿ SAFEGUARD: task {task_id} has {redos} REDOs. Skipping — needs Mac's eye."
                _notify(msg)
                return False
            return True

    def check_session_time(self) -> bool:
        """Returns True if ok to continue, False if session too long."""
        hours = (time.time() - self._session_start) / 3600
        if hours >= self.MAX_SESSION_HOURS:
            msg = f"☿ SAFEGUARD: {hours:.1f}h session. Pausing autonomously — Mac should review progress."
            _notify(msg)
            self._paused = True
            return False
        return True

    def is_paused(self) -> bool:
        return self._paused

    def resume(self):
        with self._lock:
            self._paused = False

    def status(self) -> str:
        hours = (time.time() - self._session_start) / 3600
        return (f"LoopBreaker: {'PAUSED' if self._paused else 'RUNNING'} · "
                f"{hours:.1f}h session · "
                f"tasks tracked: {len(self._task_redo)}")


# ── Context guard ─────────────────────────────────────────────────────────────
class ContextGuard:
    """
    Tracks approximate context size. When it gets large, triggers LAMAGUE
    compaction to keep Sol sharp. Without this, long sessions drift.
    """
    COMPACT_THRESHOLD = 80_000    # tokens — trigger compaction
    HARD_LIMIT        = 120_000   # tokens — force new session

    def __init__(self):
        self._estimated_ctx = 0

    def add(self, tokens: int):
        self._estimated_ctx += tokens

    def needs_compact(self) -> bool:
        return self._estimated_ctx >= self.COMPACT_THRESHOLD

    def needs_reset(self) -> bool:
        return self._estimated_ctx >= self.HARD_LIMIT

    def compact_done(self, new_estimate: int):
        self._estimated_ctx = new_estimate

    def status(self) -> str:
        pct = (self._estimated_ctx / self.HARD_LIMIT) * 100
        return f"Context: ~{self._estimated_ctx:,} tokens ({pct:.0f}% of hard limit)"


# ── Heartbeat ─────────────────────────────────────────────────────────────────
class Heartbeat:
    """
    Pings Mac every N minutes to show the system is alive, not crashed.
    Silence is the signal of a crash. Heartbeat prevents false silence.
    """
    INTERVAL_MINUTES = 60   # ping every hour during overnight runs

    def __init__(self, get_status_fn):
        self._get_status = get_status_fn
        self._thread = None
        self._stop   = threading.Event()

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="HEARTBEAT")
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        time.sleep(self.INTERVAL_MINUTES * 60)
        while not self._stop.is_set():
            try:
                status = self._get_status()
                _notify(f"💓 AZOTH HEARTBEAT\n{status}")
            except Exception:
                pass
            self._stop.wait(self.INTERVAL_MINUTES * 60)


# ── Notification helper ───────────────────────────────────────────────────────
def _notify(msg: str):
    try:
        from CORE.telegram_bot import send_message
        send_message(msg)
    except Exception:
        pass
    # also write to safeguard log
    try:
        SAFEGUARD_F.parent.mkdir(exist_ok=True)
        ts = datetime.datetime.now().strftime("%H:%M")
        with open(SAFEGUARD_F, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


# ── Global singletons (imported by agent.py) ─────────────────────────────────
budget   = TokenBudget()
breaker  = LoopBreaker()
context  = ContextGuard()


def safeguard_status() -> str:
    return "\n".join([
        "⊚ AZOTH SAFEGUARDS",
        budget.summary(),
        breaker.status(),
        context.status(),
    ])
