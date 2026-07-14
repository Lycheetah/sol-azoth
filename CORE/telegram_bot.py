"""
P4-T1: Telegram Interface — AZOTH
Mac controls VAEL from his phone. Polling loop → parse command → run → reply.
Also exposes send_message() so any CORE module can ping Mac.
No webhook needed — polling only (no public server required).
"""

import os, threading, time, json, datetime, traceback
import urllib.request, urllib.parse, urllib.error
from pathlib import Path

HARNESS_DIR = Path(__file__).parent.parent

# ── Credentials (loaded from .env) ───────────────────────────────────────────
def _load_env():
    env_path = HARNESS_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

TOKEN      = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")          # Mac ↔ Sol private
SQUAD_ID   = os.environ.get("TELEGRAM_SQUAD_CHAT_ID", "")   # Mac + full army squad

API = f"https://api.telegram.org/bot{TOKEN}"

# ── Allowed commands ──────────────────────────────────────────────────────────
ALLOWED = {"/forge", "/status", "/workers", "/models", "/tasks",
           "/test", "/help", "/stop", "/pause", "/resume"}

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def _post(method: str, data: dict) -> dict:
    url  = f"{API}/{method}"
    body = json.dumps(data).encode()
    req  = urllib.request.Request(url, data=body,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def _get(method: str, params: dict = None) -> dict:
    url = f"{API}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())

# ── Public API ────────────────────────────────────────────────────────────────
def send_squad(text: str) -> bool:
    """Broadcast to the squad group (army-visible channel)."""
    if SQUAD_ID:
        return send_message(text, chat_id=SQUAD_ID)
    return send_message(text)   # fallback to private if squad not configured yet

def send_message(text: str, chat_id: str = None) -> bool:
    """Send a message to Mac (private channel by default)."""
    if not TOKEN or not (chat_id or CHAT_ID):
        return False
    try:
        _post("sendMessage", {
            "chat_id":    chat_id or CHAT_ID,
            "text":       text[:4096],   # Telegram limit
            "parse_mode": "HTML",
        })
        return True
    except Exception:
        return False

def ping_mac(message: str) -> bool:
    """Alias for send_message — used as ping_fn in scheduler and agent."""
    return send_message(f"◆ AZOTH\n{message}")

# ── Command dispatcher ────────────────────────────────────────────────────────
# Set by start() — avoids circular imports by accepting a callable
_agent_cmd: callable = None

def _dispatch(text: str) -> str:
    """Parse incoming text, run command or goal, return reply string."""
    text = text.strip()
    if not text:
        return ""

    if _agent_cmd is None:
        return "Agent not connected yet."

    try:
        result = _agent_cmd(text)
        return result if result else "done."
    except Exception as ex:
        return f"Error: {ex}"

# ── Polling loop ──────────────────────────────────────────────────────────────
_running  = False
_thread   = None
_offset   = 0

def _poll():
    global _offset, _running
    while _running:
        try:
            data = _get("getUpdates", {"offset": _offset, "timeout": 20, "limit": 10})
            for update in data.get("result", []):
                _offset = update["update_id"] + 1
                msg = update.get("message", {})
                if not msg:
                    continue
                chat_id = str(msg.get("chat", {}).get("id", ""))
                user_id = str(msg.get("from", {}).get("id", ""))
                # Authorize Mac by USER id (works in private AND group chats).
                # Mac's private chat id == his user id. Also allow a configured squad chat.
                authorized = (user_id == str(CHAT_ID) or chat_id == str(CHAT_ID)
                              or (SQUAD_ID and chat_id == str(SQUAD_ID)))
                if not authorized:
                    continue   # silently ignore strangers (no "Unauthorized" spam)
                text = msg.get("text", "").strip()
                if not text:
                    continue
                # Reply to the SAME chat the message came from (group or private)
                threading.Thread(target=_handle, args=(text, chat_id), daemon=True).start()
        except Exception:
            time.sleep(5)

def _handle(text: str, origin_chat: str = None):
    ts    = datetime.datetime.now().strftime("%H:%M")
    reply = _dispatch(text)
    send_message(f"[{ts}] {reply}", chat_id=origin_chat)

def start(agent_cmd_fn: callable = None):
    """Start the polling loop. agent_cmd_fn(text) → str result."""
    global _running, _thread, _agent_cmd
    if not TOKEN or not CHAT_ID:
        return False
    _agent_cmd = agent_cmd_fn
    if _running:
        return True
    _running = True
    _thread  = threading.Thread(target=_poll, daemon=True, name="azoth-telegram")
    _thread.start()
    return True

def stop():
    global _running
    _running = False

def is_running() -> bool:
    return _running

def status() -> dict:
    return {
        "running":  _running,
        "token_set": bool(TOKEN),
        "chat_id":   CHAT_ID,
        "offset":    _offset,
    }
