#!/usr/bin/env python3
"""SOMA — Agent Harness Web UI.

Anthropic-level web interface for spawning and interacting with agents.
Standalone Flask SSE server.

Start:
  python3 AGENTS/SOMA/web_server.py
  # then open http://localhost:7767

Port: 7767 (set SOMA_PORT to override)
"""

import os, sys, json, time, queue, threading, datetime, uuid
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_from_directory

HERE = Path(__file__).parent.resolve()
PORT = int(os.environ.get("SOMA_PORT", "7767"))

app = Flask(__name__, static_folder=None)

# ── SSE broadcast ───────────────────────────────────────────────────────────
_subscribers: list[queue.Queue] = []
_sub_lock = threading.Lock()
_message_log: list[str] = []
_LOG_CAP = 300


def broadcast(event: str, data: dict):
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
    with _sub_lock:
        dead = []
        for q in _subscribers:
            try:
                q.put_nowait(msg)
            except:
                dead.append(q)
        for q in dead:
            _subscribers.remove(q)


def push(role: str, text: str, extra: dict = None):
    payload = {
        "role": role,
        "text": text,
        "ts": datetime.datetime.now().strftime("%H:%M"),
    }
    if extra:
        payload.update(extra)
    msg = f"event: message\ndata: {json.dumps(payload)}\n\n"
    with _sub_lock:
        _message_log.append(msg)
        if len(_message_log) > _LOG_CAP:
            del _message_log[: len(_message_log) - _LOG_CAP]
    broadcast("message", payload)


# ── Agent registry ──────────────────────────────────────────────────────────
_agents: dict[str, dict] = {}
_agents_lock = threading.Lock()


def list_agents() -> list[dict]:
    """Scan AGENTS/ for loadable agent bodies."""
    agents_dir = HERE.parent / "AGENTS"
    agents = []
    if agents_dir.exists():
        for d in sorted(agents_dir.iterdir()):
            if d.is_dir() and (d / "CONSTITUTION.md").exists():
                agents.append({
                    "name": d.name,
                    "path": str(d),
                })
    return agents


def get_agent(name: str) -> dict | None:
    with _agents_lock:
        return _agents.get(name)


def set_agent(name: str, state: dict):
    with _agents_lock:
        _agents[name] = state


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the SOMA web UI."""
    html_path = HERE / "ui" / "index.html"
    if html_path.exists():
        return send_from_directory(str(html_path.parent), "index.html")
    return "<h1>SOMA Harness</h1><p>UI not built yet.</p>", 200


@app.route("/api/agents")
def api_agents():
    """Return list of available agent bodies."""
    return jsonify(list_agents())


@app.route("/api/agents/<name>", methods=["GET"])
def api_agent_get(name: str):
    """Get agent status."""
    agent = get_agent(name)
    if agent is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(agent)


@app.route("/api/agents/<name>/spawn", methods=["POST"])
def api_agent_spawn(name: str):
    """Spawn an agent body."""
    data = request.get_json(silent=True) or {}
    model = data.get("model", "claude-sonnet-4-20250514")
    agent = {
        "name": name,
        "model": model,
        "status": "running",
        "spawned_at": datetime.datetime.now().isoformat(),
        "id": str(uuid.uuid4())[:8],
    }
    set_agent(name, agent)
    push("system", f"Spawned agent **{name}** on {model}")
    return jsonify(agent), 201


@app.route("/api/agents/<name>/kill", methods=["POST"])
def api_agent_kill(name: str):
    """Kill an agent body."""
    agent = get_agent(name)
    if agent is None:
        return jsonify({"error": "not found"}), 404
    agent["status"] = "stopped"
    set_agent(name, agent)
    push("system", f"Stopped agent **{name}**")
    return jsonify(agent)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Send a message to the current agent."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    agent_name = data.get("agent", "SOMA")
    if not text:
        return jsonify({"error": "empty message"}), 400

    push("user", text, {"agent": agent_name})

    # Echo the message back for now — real agent integration comes next
    push("assistant", f"Received: {text}", {"agent": agent_name})
    return jsonify({"ok": True})


@app.route("/api/stream")
def api_stream():
    """SSE stream for live updates."""
    def event_stream():
        q = queue.Queue()
        with _sub_lock:
            _subscribers.append(q)
            # Replay recent log
            for msg in _message_log:
                q.put(msg)
        try:
            while True:
                msg = q.get(timeout=30)
                yield msg
        except (queue.Empty, GeneratorExit):
            pass
        finally:
            with _sub_lock:
                if q in _subscribers:
                    _subscribers.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/assets/<path:filename>")
def assets(filename: str):
    """Static assets (CSS, JS)."""
    assets_dir = HERE / "ui" / "assets"
    return send_from_directory(str(assets_dir), filename)


@app.route("/api/queue")
def api_queue():
    """Return forge queue state (stub for now)."""
    return jsonify([])


# ── Main ────────────────────────────────────────────────────────────────────
# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"╔══ SOMA Harness ══╗")
    print(f"║  Port: {PORT}")
    print(f"║  Agents: {len(list_agents())} found")
    print(f"╚══════════════════╝")
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
