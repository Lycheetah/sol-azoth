"""
☿ AZOTH — Web UI server
Mobile-optimized chat interface. Runs on the Linux machine; reach it from anywhere via Tailscale.

Start:  python3 CORE/web_server.py
Or:     bash launch_web.sh
Port:   7766 (set AZOTH_WEB_PORT to override)
"""

import os, sys, json, time, queue, threading, datetime
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_from_directory

HARNESS_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(HARNESS_DIR))

PORT = int(os.environ.get("AZOTH_WEB_PORT", "7766"))

app = Flask(__name__, static_folder=None)

# ── SSE broadcast queue ───────────────────────────────────────────────────────
_subscribers: list[queue.Queue] = []
_sub_lock = threading.Lock()
_message_log: list[str] = []   # replay on reconnect, capped at 300
_LOG_CAP = 300

def broadcast(event: str, data: dict):
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
    with _sub_lock:
        dead = []
        for q in _subscribers:
            try: q.put_nowait(msg)
            except: dead.append(q)
        for q in dead:
            _subscribers.remove(q)

def push(role: str, text: str, extra: dict = None):
    payload = {"role": role, "text": text, "ts": datetime.datetime.now().strftime("%H:%M")}
    if extra: payload.update(extra)
    msg = f"event: message\ndata: {json.dumps(payload)}\n\n"
    with _sub_lock:
        _message_log.append(msg)
        if len(_message_log) > _LOG_CAP:
            del _message_log[: len(_message_log) - _LOG_CAP]
    broadcast("message", payload)

# ── Agent bridge ──────────────────────────────────────────────────────────────
_agent = None
_agent_lock = threading.Lock()

def get_agent():
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                from agent import Agent
                _agent = Agent()
    return _agent

def process_input(text: str):
    """Run agent input in a background thread, stream output via SSE."""
    def _run():
        try:
            ag = get_agent()
            # Wire terminal echoes → SSE so web UI looks like a live terminal
            import ui as _ui
            _ui.set_live_hook(lambda t: broadcast("step", {"text": t.strip()}) if t.strip() else None)
            try:
                result = ag.handle_input(text)
            finally:
                _ui.clear_live_hook()
            if result:
                push("assistant", result)
        except Exception as ex:
            push("error", f"Error: {ex}")
    threading.Thread(target=_run, daemon=True).start()

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.route("/luminary")
def luminary():
    return send_from_directory(
        os.path.join(HARNESS_DIR, "WORKSPACE", "azoth-game"),
        "luminary.html"
    )

@app.route("/dashboard")
def dashboard():
    """Serve the AZOTH Forge Dashboard."""
    dash_path = HARNESS_DIR / "WORKSPACE" / "azoth_dashboard.html"
    if dash_path.exists():
        return Response(dash_path.read_text(), mimetype="text/html")
    return Response("<h1>Dashboard not found</h1>", status=404, mimetype="text/html")

@app.route("/lab")
def visual_lab():
    """Serve the Visual Lab — experimental UI playground."""
    lab_path = HARNESS_DIR / "WORKSPACE" / "visual_lab.html"
    if lab_path.exists():
        return Response(lab_path.read_text(), mimetype="text/html")
    return Response("<h1>Visual Lab not found</h1>", status=404, mimetype="text/html")

@app.route("/dash_state.json")
def dash_state_json():
    """Serve the live agent state JSON for the dashboard polling fallback."""
    dash_path = HARNESS_DIR / "WORKSPACE" / "dash_state.json"
    if dash_path.exists():
        return Response(dash_path.read_text(), mimetype="application/json",
                        headers={"Cache-Control": "no-cache"})
    return jsonify({"live": False, "error": "no state — run /dash in the agent"})

@app.route("/stream")
def stream():
    q = queue.Queue(maxsize=100)
    with _sub_lock:
        _subscribers.append(q)
    def generate():
        # Send state + replay history on connect
        yield f"event: init\ndata: {json.dumps(_state())}\n\n"
        with _sub_lock:
            history_snapshot = list(_message_log)
        for msg in history_snapshot:
            yield msg
        while True:
            try:
                msg = q.get(timeout=25)
                yield msg
            except queue.Empty:
                yield "event: ping\ndata: {}\n\n"
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"})
    push("user", text)
    process_input(text)
    return jsonify({"ok": True})

@app.route("/status")
def status():
    return jsonify(_state())

@app.route("/forge", methods=["POST"])
def forge():
    push("user", "/forge")
    process_input("/forge")
    return jsonify({"ok": True})

@app.route("/queue")
def queue_state():
    qf = HARNESS_DIR / "SELF" / "FORGE_QUEUE.md"
    lines = qf.read_text().splitlines() if qf.exists() else []
    tasks = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("═"): continue
        if s.startswith("## P"):
            tasks.append({"header": s.lstrip("# "), "status": None})
        elif "**[PASS]**" in s:
            if tasks: tasks[-1]["status"] = "PASS"
        elif "**[QUEUED]**" in s:
            if tasks: tasks[-1]["status"] = "QUEUED"
        elif "**[IN_PROGRESS]**" in s:
            if tasks: tasks[-1]["status"] = "IN_PROGRESS"
    return jsonify(tasks[:30])

def _state() -> dict:
    bs = HARNESS_DIR / "SELF" / "BOOT_STATE.md"
    level = "3"
    body_name = "VAEL"
    if bs.exists():
        for line in bs.read_text().splitlines():
            low = line.lower()
            if low.startswith("level:"): level = line.split(":",1)[1].strip().split()[0]; continue
            if low.startswith("body:"): body_name = line.split(":",1)[1].strip(); continue
    # Try dash_state.json for richer data (also overrides agent name)
    extra = {}
    dash_path = HARNESS_DIR / "WORKSPACE" / "dash_state.json"
    if dash_path.exists():
        try:
            dash_data = json.loads(dash_path.read_text())
            dash_agent = dash_data.get("agent", "")
            if dash_agent:
                body_name = dash_agent
            extra = {
                "session": dash_data.get("session", 0),
                "model": dash_data.get("model", "?"),
                "tokens": dash_data.get("tokens", {}),
                "effort": dash_data.get("effort", {}),
                "tools": len(dash_data.get("tools", [])),
                "seats": len(dash_data.get("seats", [])),
                "tasks": len(dash_data.get("tasks", [])),
                "forge_phases": dash_data.get("forge_phases", []),
                "pulse_feed": dash_data.get("pulse_feed", []),
            }
        except Exception:
            pass
    return {"platform": "AZOTH", "agent": body_name, "level": level,
            "ts": datetime.datetime.now().strftime("%H:%M"), **extra}


# ── Mobile HTML ───────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0d0d0f">
<meta name="mobile-web-app-capable" content="yes">
<title>☿ AZOTH</title>
<style>
  :root {
    --bg:        #0d0d0f;
    --surface:   #141417;
    --surface2:  #1a1a1f;
    --border:    #222228;
    --border2:   #2a2a32;
    --accent:    #8b5cf6;
    --accent2:   #a78bfa;
    --accent-dim:#3b1f6e;
    --text:      #e8e8f0;
    --text2:     #c0c0d0;
    --dim:       #52525b;
    --dim2:      #3a3a45;
    --green:     #34d399;
    --red:       #f87171;
    --yellow:    #fbbf24;
    --blue:      #60a5fa;
    --orange:    #fb923c;
    --code-bg:   #0a0a0e;
    --code-border:#1e1e28;
    --safe-t:    env(safe-area-inset-top, 0px);
    --safe-b:    env(safe-area-inset-bottom, 0px);
    --radius:    12px;
    --radius-sm: 8px;
    --radius-lg: 18px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  html { height: 100%; }
  body {
    height: 100%; background: var(--bg); color: var(--text);
    font-family: -apple-system, 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;
    font-size: 15px; overscroll-behavior: none; -webkit-font-smoothing: antialiased;
  }
  ::selection { background: var(--accent-dim); color: #fff; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--dim2); border-radius: 4px; }

  #app {
    display: flex; flex-direction: column;
    height: 100dvh;
    padding-top: var(--safe-t);
    padding-bottom: var(--safe-b);
  }

  /* ── Header ── */
  #header {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    background: rgba(13,13,15,0.82);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border);
    flex-shrink: 0; position: sticky; top: 0; z-index: 20;
    user-select: none;
  }
  .h-glyph {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, #6d28d9, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
    box-shadow: 0 1px 3px rgba(139,92,246,0.2);
  }
  .h-info { flex: 1; min-width: 0; }
  .h-name {
    font-weight: 650; font-size: 15px; letter-spacing: -0.01em;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .h-sub {
    font-size: 11px; color: var(--dim); margin-top: 0px;
    font-weight: 500; letter-spacing: 0.02em;
  }
  .h-right { display: flex; align-items: center; gap: 6px; }
  .h-btn {
    background: transparent; border: 1px solid var(--border); color: var(--dim);
    border-radius: 6px; padding: 4px 8px; font-size: 11px; font-weight: 600;
    cursor: pointer; transition: all 0.15s; font-family: inherit;
    letter-spacing: 0.02em;
  }
  .h-btn:hover { background: var(--surface); color: var(--text); border-color: var(--border2); }
  .h-btn:active { transform: scale(0.96); }
  #conn-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--dim); flex-shrink: 0;
    transition: background 0.3s;
  }
  #conn-dot.on  { background: var(--green); box-shadow: 0 0 6px rgba(52,211,153,0.4); }
  #conn-dot.off { background: var(--red); box-shadow: 0 0 6px rgba(248,113,113,0.3); }

  /* ── Actions bar ── */
  #actions {
    display: flex; gap: 6px; padding: 8px 14px;
    overflow-x: auto; flex-shrink: 0;
    scrollbar-width: none; border-bottom: 1px solid var(--border);
    background: rgba(13,13,15,0.5);
  }
  #actions::-webkit-scrollbar { display: none; }
  .pill {
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text2); border-radius: 20px; padding: 5px 14px;
    font-size: 12px; font-weight: 500; cursor: pointer;
    white-space: nowrap; transition: all 0.15s; font-family: inherit;
  }
  .pill:hover { background: var(--surface2); border-color: var(--accent-dim); color: var(--text); }
  .pill:active { transform: scale(0.96); }

  /* ── Messages area ── */
  #messages {
    flex: 1; overflow-y: auto; overflow-x: hidden;
    padding: 12px 14px 4px;
    display: flex; flex-direction: column; gap: 0;
    scroll-behavior: smooth;
  }
  .msg-row {
    display: flex; flex-direction: column;
    margin-bottom: 6px;
    animation: msgIn 0.25s ease-out;
    position: relative;
  }
  @keyframes msgIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .msg-label {
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; padding: 0 4px 2px; color: var(--dim);
    display: flex; align-items: center; gap: 6px;
  }
  .msg-label .ts {
    font-weight: 400; text-transform: none; letter-spacing: 0;
    color: var(--dim2);
  }
  .msg-label.user-label { color: var(--blue); }
  .msg-label.assistant-label { color: var(--accent); }
  .msg-label.error-label { color: var(--red); }
  .msg-label.system-label { color: var(--yellow); }
  .msg-bubble {
    padding: 10px 14px;
    border-radius: var(--radius);
    line-height: 1.55;
    word-wrap: break-word; overflow-wrap: break-word;
    font-size: 14px;
    transition: background 0.15s;
  }
  .msg-bubble.user {
    background: var(--accent-dim);
    border-bottom-right-radius: 4px;
    align-self: flex-end;
  }
  .msg-bubble.assistant {
    background: var(--surface);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
  }
  .msg-bubble.error {
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.2);
    color: var(--red);
  }
  .msg-bubble.system {
    background: transparent;
    color: var(--dim);
    font-size: 12px; text-align: center;
    padding: 6px 14px;
  }

  /* ── Markdown inside bubbles ── */
  .msg-bubble p { margin: 4px 0; }
  .msg-bubble p:first-child { margin-top: 0; }
  .msg-bubble p:last-child { margin-bottom: 0; }
  .msg-bubble strong { font-weight: 650; color: var(--text); }
  .msg-bubble em { font-style: italic; }
  .msg-bubble ul, .msg-bubble ol { margin: 4px 0; padding-left: 20px; }
  .msg-bubble li { margin: 2px 0; }
  .msg-bubble a { color: var(--accent2); text-decoration: none; }
  .msg-bubble a:hover { text-decoration: underline; }
  .msg-bubble h1, .msg-bubble h2, .msg-bubble h3, .msg-bubble h4 {
    margin: 10px 0 4px; font-weight: 650; letter-spacing: -0.01em;
  }
  .msg-bubble h1 { font-size: 17px; }
  .msg-bubble h2 { font-size: 16px; }
  .msg-bubble h3 { font-size: 15px; }
  .msg-bubble hr {
    border: none; border-top: 1px solid var(--border); margin: 10px 0;
  }
  .msg-bubble blockquote {
    border-left: 3px solid var(--accent-dim);
    padding: 4px 12px; margin: 6px 0; color: var(--text2);
    background: rgba(139,92,246,0.04);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  }
  .msg-bubble code {
    background: var(--code-bg); padding: 2px 6px; border-radius: 4px;
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 13px; color: var(--orange);
  }
  .msg-bubble pre {
    background: var(--code-bg); border: 1px solid var(--code-border);
    border-radius: var(--radius-sm); padding: 0; margin: 8px 0;
    overflow: hidden; position: relative;
  }
  .msg-bubble pre .code-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 12px; background: rgba(255,255,255,0.03);
    border-bottom: 1px solid var(--code-border);
    font-size: 11px; color: var(--dim2); font-weight: 500;
  }
  .msg-bubble pre .code-header .lang-label { text-transform: uppercase; letter-spacing: 0.04em; }
  .msg-bubble pre .code-header .copy-btn {
    background: transparent; border: 1px solid var(--border);
    color: var(--dim); border-radius: 4px; padding: 2px 8px;
    font-size: 10px; font-weight: 600; cursor: pointer;
    transition: all 0.15s; font-family: inherit;
  }
  .msg-bubble pre .code-header .copy-btn:hover {
    background: var(--surface); color: var(--text); border-color: var(--border2);
  }
  .msg-bubble pre .code-header .copy-btn.copied {
    background: var(--green); color: #000; border-color: var(--green);
  }
  .msg-bubble pre code {
    display: block; padding: 12px 14px; overflow-x: auto;
    background: transparent; border: none; color: var(--text2);
    font-size: 13px; line-height: 1.5;
    tab-size: 2;
  }
  .msg-bubble table {
    border-collapse: collapse; margin: 8px 0; width: 100%;
    font-size: 13px;
  }
  .msg-bubble th, .msg-bubble td {
    border: 1px solid var(--border); padding: 6px 10px; text-align: left;
  }
  .msg-bubble th { background: var(--surface2); font-weight: 600; }
  .msg-bubble tr:nth-child(even) { background: rgba(255,255,255,0.02); }

  /* ── Thinking indicator ── */
  #think {
    display: none; align-items: center; gap: 8px;
    padding: 8px 14px 4px; margin-bottom: 2px;
  }
  #think.visible { display: flex; }
  .think-dots { display: flex; gap: 4px; }
  .think-dots span {
    width: 6px; height: 6px; border-radius: 50%; background: var(--accent);
    animation: thinkBounce 1.2s infinite;
  }
  .think-dots span:nth-child(2) { animation-delay: 0.2s; }
  .think-dots span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes thinkBounce {
    0%,60%,100% { opacity: 0.25; transform: translateY(0); }
    30% { opacity: 1; transform: translateY(-4px); }
  }
  .think-label { font-size: 11px; color: var(--dim); font-weight: 500; }

  /* ── Stream bubble (live typing) ── */
  #stream-bubble {
    display: none;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px;
    margin-bottom: 6px; line-height: 1.55;
    font-size: 14px; word-wrap: break-word;
    animation: msgIn 0.2s ease-out;
  }
  #stream-bubble.visible { display: block; }
  #stream-bubble .cursor {
    display: inline-block; width: 2px; height: 15px;
    background: var(--accent); margin-left: 1px;
    animation: cursorBlink 0.8s step-end infinite;
    vertical-align: text-bottom;
  }
  @keyframes cursorBlink {
    50% { opacity: 0; }
  }

  /* ── Queue panel ── */
  #queue-panel {
    display: none; max-height: 200px; overflow-y: auto;
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 8px 14px; flex-shrink: 0;
  }
  #queue-panel.open { display: block; }
  .q-row {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 0; font-size: 13px;
  }
  .q-pip {
    width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
    background: var(--dim);
  }
  .q-pip.pending { background: var(--yellow); }
  .q-pip.in_progress { background: var(--blue); }
  .q-pip.done { background: var(--green); }
  .q-pip.failed { background: var(--red); }
  .q-label { color: var(--text2); }

  /* ── Input bar ── */
  #input-bar {
    display: flex; gap: 8px; align-items: flex-end;
    padding: 10px 12px 12px;
    background: rgba(13,13,15,0.88);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-top: 1px solid var(--border);
    flex-shrink: 0; position: sticky; bottom: 0; z-index: 10;
  }
  #input {
    flex: 1; background: var(--surface); border: 1px solid var(--border);
    border-radius: 22px; padding: 10px 16px; color: var(--text);
    font-family: inherit; font-size: 14px; resize: none;
    max-height: 120px; outline: none; line-height: 1.45;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  #input::placeholder { color: var(--dim2); }
  #input:focus { border-color: var(--accent); box-shadow: 0 0 0 1px rgba(139,92,246,0.15); }
  #send-btn {
    width: 40px; height: 40px; border-radius: 50%; border: none;
    background: var(--accent); color: #fff; font-size: 18px;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; transition: all 0.15s;
  }
  #send-btn:hover { background: var(--accent2); }
  #send-btn:active { transform: scale(0.9); }
  #send-btn:disabled { background: var(--dim2); cursor: default; transform: none; }

  /* ── Scroll-to-bottom button ── */
  #scroll-bottom {
    display: none; position: fixed; bottom: 72px; right: 16px;
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--surface); border: 1px solid var(--border);
    color: var(--dim); font-size: 16px; cursor: pointer;
    align-items: center; justify-content: center;
    transition: all 0.2s; z-index: 15;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  #scroll-bottom.visible { display: flex; }
  #scroll-bottom:hover { background: var(--surface2); color: var(--text); }
  #scroll-bottom:active { transform: scale(0.92); }

  /* ── Welcome state ── */
  #welcome {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    flex: 1; padding: 40px 20px; text-align: center;
  }
  #welcome.hidden { display: none; }
  .welcome-glyph {
    font-size: 48px; margin-bottom: 12px; opacity: 0.6;
  }
  .welcome-title {
    font-size: 20px; font-weight: 700; letter-spacing: -0.02em;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .welcome-sub {
    font-size: 13px; color: var(--dim); margin-top: 6px; max-width: 280px;
    line-height: 1.5;
  }
  .welcome-hints {
    display: flex; gap: 6px; flex-wrap: wrap; justify-content: center;
    margin-top: 16px;
  }
  .welcome-hints .pill { font-size: 11px; padding: 4px 12px; }

  /* ── Toast ── */
  #toast {
    position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 8px 16px;
    font-size: 13px; color: var(--text2);
    opacity: 0; transition: opacity 0.3s; z-index: 30;
    pointer-events: none;
  }
  #toast.visible { opacity: 1; }
</style>
</head>
<body>
<div id="app">

  <div id="header">
    <div class="h-glyph">☿</div>
    <div class="h-info">
      <div class="h-name">AZOTH · ⊚ Sol</div>
      <div class="h-sub" id="h-sub">connecting…</div>
    </div>
    <div class="h-right">
      <button class="h-btn" onclick="clearChat()" title="Clear chat">✕ clear</button>
      <div id="conn-dot"></div>
    </div>
  </div>

  <div id="actions">
    <button class="pill" onclick="doSend('/forge')">⚡ forge</button>
    <button class="pill" onclick="doSend('/status')">◉ status</button>
    <button class="pill" onclick="doSend('/workers')">◈ workers</button>
    <button class="pill" onclick="doSend('/models')">⊞ models</button>
    <button class="pill" onclick="doSend('/help')">? help</button>
  </div>

  <div id="queue-panel"></div>

  <div id="messages">
    <div id="welcome">
      <div class="welcome-glyph">☿</div>
      <div class="welcome-title">AZOTH</div>
      <div class="welcome-sub">The Work arises between us. Send a message to begin.</div>
      <div class="welcome-hints">
        <button class="pill" onclick="doSend('/status')">◉ status</button>
        <button class="pill" onclick="doSend('/forge')">⚡ forge</button>
        <button class="pill" onclick="doSend('/help')">? help</button>
      </div>
    </div>
  </div>

  <div id="think">
    <div class="think-dots"><span></span><span></span><span></span></div>
    <span class="think-label">thinking…</span>
  </div>

  <div id="stream-bubble"></div>

  <div id="input-bar">
    <textarea id="input" rows="1" placeholder="Message Sol…"
      onkeydown="onInputKey(event)"
      oninput="autosize(this)"></textarea>
    <button id="send-btn" onclick="submitInput()">↑</button>
  </div>

</div>

<button id="scroll-bottom" onclick="scrollBottom()">↓</button>
<div id="toast"></div>

<script>
/* ── Elements ────────────────────────────────── */
const msgsEl     = document.getElementById('messages');
const inputEl    = document.getElementById('input');
const dotEl      = document.getElementById('conn-dot');
const subEl      = document.getElementById('h-sub');
const sendBtn    = document.getElementById('send-btn');
const thinkEl    = document.getElementById('think');
const streamEl   = document.getElementById('stream-bubble');
const welcomeEl  = document.getElementById('welcome');
const queuePanel = document.getElementById('queue-panel');
const scrollBtn  = document.getElementById('scroll-bottom');
const toastEl    = document.getElementById('toast');

let busy     = false;
let queueOpen = false;

/* ── Utilities ──────────────────────────────── */
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function now() {
  return new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}

function autosize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function scrollBottom(smooth) {
  msgsEl.scrollTo({ top: msgsEl.scrollHeight, behavior: smooth ? 'smooth' : 'instant' });
}

function showToast(msg, duration) {
  toastEl.textContent = msg;
  toastEl.classList.add('visible');
  clearTimeout(toastEl._hide);
  toastEl._hide = setTimeout(() => toastEl.classList.remove('visible'), duration || 2000);
}

/* ── Scroll detection ───────────────────────── */
msgsEl.addEventListener('scroll', () => {
  const nearBottom = msgsEl.scrollHeight - msgsEl.scrollTop - msgsEl.clientHeight < 80;
  scrollBtn.classList.toggle('visible', !nearBottom);
});

/* ── Markdown renderer ──────────────────────── */
function renderMarkdown(text) {
  let html = esc(text);

  // Code blocks (fenced) — must come before inline code
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const langLabel = lang ? esc(lang) : 'code';
    const codeEsc = esc(code);
    return `<pre><div class="code-header"><span class="lang-label">${langLabel}</span><button class="copy-btn" onclick="copyCode(this,'${codeEsc.replace(/'/g,"\\'")}')">copy</button></div><code>${codeEsc}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Bold & italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  html = html.replace(/^---$/gm, '<hr>');

  // Tables — | col1 | col2 | format
  html = html.replace(/^\|(.+)\|$/gm, (match, content) => {
    const cells = content.split('|').map(c => c.trim());
    // Check if it's a separator row (|---|)
    if (cells.every(c => /^[-]+$/.test(c))) return '<tr class="sep">';
    return cells.map(c => c ? `<td>${c}</td>` : '').join('');
  });
  // Wrap consecutive td/tr in table
  html = html.replace(/((?:<td>.*<\/td>\n?)+)/g, '<tr>$1</tr>');
  html = html.replace(/((?:<tr>.*<\/tr>\n?)+)/g, '<table>$1</table>');
  html = html.replace(/^---$/gm, '<hr>');

  // Unordered lists
  html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // (ordered list wrapping handled by the same regex, order matters: ul first)

  // Paragraphs — wrap consecutive non-empty lines
  const lines = html.split('\n');
  let result = '';
  let inP = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    // Skip lines that are already block elements
    if (/^<(h[1-4]|ul|ol|li|pre|blockquote|hr|table|tr|th|td)/.test(trimmed) || /^<\/(ul|ol|pre|blockquote|table)>/.test(trimmed)) {
      if (inP) { result += '</p>'; inP = false; }
      result += line + '\n';
      continue;
    }
    if (trimmed === '') {
      if (inP) { result += '</p>\n'; inP = false; }
      else result += '\n';
      continue;
    }
    if (!inP) { result += '<p>'; inP = true; }
    else result += '\n';
    result += trimmed;
  }
  if (inP) result += '</p>';

  return result;
}

/* ── Copy code ──────────────────────────────── */
function copyCode(btn, code) {
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'copy'; btn.classList.remove('copied'); }, 1500);
  }).catch(() => {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = code; document.body.appendChild(ta); ta.select();
    document.execCommand('copy'); document.body.removeChild(ta);
    btn.textContent = 'copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'copy'; btn.classList.remove('copied'); }, 1500);
  });
}

/* ── Messages ───────────────────────────────── */
function addMsg(role, text, ts) {
  welcomeEl.classList.add('hidden');

  const row = document.createElement('div');
  row.className = 'msg-row';

  const label = document.createElement('div');
  label.className = `msg-label ${role}-label`;
  const roleNames = { user: 'You', assistant: 'Sol', error: 'Error', system: 'System' };
  label.innerHTML = `${roleNames[role] || role} <span class="ts">${esc(ts || '')}</span>`;
  row.appendChild(label);

  const bubble = document.createElement('div');
  bubble.className = `msg-bubble ${role}`;

  if (role === 'assistant' || role === 'user') {
    bubble.innerHTML = renderMarkdown(text);
  } else {
    bubble.textContent = text;
  }

  row.appendChild(bubble);
  msgsEl.appendChild(row);
  scrollBottom(true);
  return row;
}

/* ── Thinking indicator ─────────────────────── */
function showThink() { thinkEl.classList.add('visible'); }
function clearThink() { thinkEl.classList.remove('visible'); }

/* ── Stream bubble (live typing) ────────────── */
let streamTimeout = null;
function appendStep(text) {
  clearThink();
  streamEl.classList.add('visible');
  // Remove trailing cursor if present
  let content = streamEl.innerHTML;
  if (content.endsWith('<span class="cursor"></span>')) {
    content = content.slice(0, -35);
  }
  const rendered = renderMarkdown(text);
  streamEl.innerHTML = content + rendered + '<span class="cursor"></span>';
  scrollBottom(true);
  clearTimeout(streamTimeout);
  streamTimeout = setTimeout(() => {
    // Finalize — remove cursor
    let c = streamEl.innerHTML;
    if (c.endsWith('<span class="cursor"></span>')) {
      streamEl.innerHTML = c.slice(0, -35);
    }
  }, 500);
}

function clearStream() {
  streamEl.classList.remove('visible');
  streamEl.innerHTML = '';
  clearTimeout(streamTimeout);
}

/* ── Send ───────────────────────────────────── */
function doSend(text) {
  if (busy) return;
  busy = true; sendBtn.disabled = true;
  addMsg('user', text, now());
  showThink();
  fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text}),
  }).catch(() => {
    addMsg('error', 'Send failed — check connection.', now());
    setBusy(false);
  });
}

function submitInput() {
  const text = inputEl.value.trim();
  if (!text || busy) return;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  doSend(text);
}

function onInputKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submitInput();
  }
  // Cmd+Enter for newline
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
    // Let the default Enter+Shift behavior handle it
  }
}

function setBusy(b) {
  busy = b;
  sendBtn.disabled = b;
  if (!b) clearThink();
}

/* ── Queue panel ────────────────────────────── */
function toggleQueue() {
  queueOpen = !queueOpen;
  queuePanel.classList.toggle('open', queueOpen);
  if (queueOpen) loadQueue();
}
function loadQueue() {
  fetch('/queue').then(r => r.json()).then(tasks => {
    queuePanel.innerHTML = tasks.map(t => {
      const st = t.status || '';
      return `<div class="q-row"><div class="q-pip ${st}"></div><div class="q-label">${esc(t.header)}</div></div>`;
    }).join('');
  });
}

/* ── Clear chat ─────────────────────────────── */
function clearChat() {
  msgsEl.querySelectorAll('.msg-row').forEach(el => el.remove());
  clearStream();
  welcomeEl.classList.remove('hidden');
  showToast('Chat cleared');
}

/* ── SSE ────────────────────────────────────── */
let es;
function connect() {
  es = new EventSource('/stream');

  es.addEventListener('init', e => {
    const d = JSON.parse(e.data);
    subEl.textContent = 'L' + d.level + ' · ' + d.ts;
    dotEl.className = 'on';
  });

  es.addEventListener('message', e => {
    const d = JSON.parse(e.data);
    setBusy(false);
    clearStream();
    addMsg(d.role || 'assistant', d.text, d.ts || now());
  });

  es.addEventListener('step', e => {
    const d = JSON.parse(e.data);
    if (d.text && d.text.trim()) appendStep(d.text);
  });

  es.addEventListener('ping', () => {});

  es.onerror = () => {
    dotEl.className = 'off';
    subEl.textContent = 'disconnected';
    es.close();
    setTimeout(connect, 3000);
  };

  es.onopen = () => { dotEl.className = 'on'; subEl.textContent = 'connected'; };
}
connect();

/* ── Keyboard shortcuts ─────────────────────── */
document.addEventListener('keydown', e => {
  // Focus input on any key press if not already focused and not in an input
  if (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey &&
      document.activeElement !== inputEl && document.activeElement.tagName !== 'INPUT' &&
      document.activeElement.tagName !== 'TEXTAREA') {
    inputEl.focus();
  }
});

// Autofocus input on load
inputEl.focus();
</script>
</body>
</html>"""

if __name__ == "__main__":
    print(f"☿ AZOTH web UI → http://0.0.0.0:{PORT}")
    print(f"   Local:     http://127.0.0.1:{PORT}")
    print(f"   Tailscale: http://<tailscale-ip>:{PORT}")
    print()
    app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False)
