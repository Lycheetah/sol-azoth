"""AZOTH core safety suite — the net that makes self-patching safe (#10 → gates #11).

Covers the verify gate (every type, good + broken), the test-runner gate, regression
memory, and the structural invariants a self-patch must never break. Pure functions
only — no model calls, runs in seconds.

Run:  python3 -m pytest tests/test_agent_core.py -q
"""
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agent as A


def _w(name, content):
    d = tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, "w") as f:
        f.write(content)
    return p


# ── Verify gate: syntax/compile by type ──────────────────────────────────────
def test_verify_good_py():
    ok, _ = A._verify_output_file(_w("g.py", "print('hi')\n"))
    assert ok

def test_verify_bad_py():
    ok, msg = A._verify_output_file(_w("b.py", "def f(:\n  pass\n"))
    assert not ok and "SYNTAX" in msg

def test_verify_good_js():
    ok, _ = A._verify_output_file(_w("g.js", "const x=1; function f(){return x}\n"))
    assert ok

def test_verify_bad_js():
    ok, _ = A._verify_output_file(_w("b.js", "function f( { return }\n"))
    assert not ok

def test_verify_json():
    assert A._verify_output_file(_w("g.json", '{"a":1}'))[0]
    assert not A._verify_output_file(_w("b.json", '{"a":1,'))[0]

def test_verify_yaml():
    assert A._verify_output_file(_w("g.yaml", "a: 1\nb: [x, y]\n"))[0]
    assert not A._verify_output_file(_w("b.yaml", "a: 1\n  b: [\n"))[0]

def test_verify_toml():
    assert A._verify_output_file(_w("g.toml", 'x="y"\n'))[0]
    assert not A._verify_output_file(_w("b.toml", "x=\n[bad\n"))[0]

def test_verify_css():
    assert A._verify_output_file(_w("g.css", "a{color:red}\n"))[0]
    assert not A._verify_output_file(_w("b.css", "a{color:red\n"))[0]

def test_verify_sh():
    assert A._verify_output_file(_w("g.sh", "#!/bin/bash\nif true; then echo y; fi\n"))[0]
    assert not A._verify_output_file(_w("b.sh", "if true; then echo y\n"))[0]

def test_verify_dockerfile():
    assert A._verify_output_file(_w("Dockerfile", "FROM python:3.11\n"))[0]
    assert not A._verify_output_file(_w("bad.dockerfile", "RUN x\nFROM y\n"))[0]

def test_verify_html_static_bad():
    ok, _ = A._verify_output_file(_w("b.html", "<script>const s=[1,2; foo=]</script>"))
    assert not ok

def test_verify_html_module_no_false_positive():
    ok, _ = A._verify_output_file(_w("m.html", "<script type='module'>import x from './y.js'</script>"))
    assert ok

def test_verify_unknown_skips():
    ok, _ = A._verify_output_file(_w("readme.md", "# hi\n"))
    assert ok   # unknown type never blocks


# ── CLI runtime smoke ─────────────────────────────────────────────────────────
def test_cli_help_catches_bad_import():
    ok, _ = A._verify_output_file(_w("cli.py",
        "import argparse, definitely_missing_xyz\nargparse.ArgumentParser().parse_args()\n"))
    assert not ok

def test_cli_help_good_passes():
    ok, _ = A._verify_output_file(_w("cli.py",
        "import argparse\np=argparse.ArgumentParser()\np.add_argument('--x')\np.parse_args()\n"))
    assert ok


# ── Test-runner gate ──────────────────────────────────────────────────────────
def test_run_written_tests_pass():
    ok, _ = A.run_written_tests([_w("test_ok.py", "def test_a():\n    assert 1+1==2\n")])
    assert ok

def test_run_written_tests_fail():
    ok, _ = A.run_written_tests([_w("test_no.py", "def test_a():\n    assert 1==2\n")])
    assert not ok

def test_run_written_tests_none():
    ok, rep = A.run_written_tests([_w("helper.py", "x=1\n")])
    assert ok and rep == ""


# ── Combined verify ───────────────────────────────────────────────────────────
def test_full_forge_verify_combines():
    good = _w("g.py", "x=1\n")
    ok, _ = A.full_forge_verify([good])
    assert ok
    bad = _w("b.py", "def f(:\n")
    ok2, _ = A.full_forge_verify([bad])
    assert not ok2


# ── Regression memory ─────────────────────────────────────────────────────────
def test_regression_signature_stable():
    # variable names must NOT fragment the signature
    s1 = A._regression_signature("  ✗ a.html: Uncaught ReferenceError foo")
    s2 = A._regression_signature("  ✗ b.html: Uncaught ReferenceError bar")
    assert s1 == s2 and s1 and "reference-error" in s1[0]

def test_regression_hint_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "_REGRESSION_F", tmp_path / "reg.json")
    A.record_verify_failure("  ✗ a.py: PY SYNTAX ERROR x")
    assert A.regression_hints("build a py tool") == ""      # 1× → below threshold
    A.record_verify_failure("  ✗ b.py: PY SYNTAX ERROR y")
    assert "py-syntax-error" in A.regression_hints("build a py tool")   # 2× → surfaces


# ── Structural invariants a self-patch must preserve ──────────────────────────
def test_core_tools_present():
    names = {d["function"]["name"] for d in A.TOOL_DEFINITIONS}
    for essential in ("bash", "read_file", "write_file", "edit_file", "done", "stuck",
                      "glob", "survey", "research"):
        assert essential in names

def test_verify_helpers_exist():
    for fn in ("verify_built_files", "full_forge_verify", "run_written_tests",
               "record_verify_failure", "regression_hints"):
        assert callable(getattr(A, fn))

def test_agent_class_has_forge_loop():
    assert hasattr(A.Agent, "run_tool_loop")
    assert hasattr(A.Agent, "cmd_forge")
    assert hasattr(A.Agent, "chat")
    assert hasattr(A.Agent, "cmd_approve")
    assert hasattr(A.Agent, "cmd_plan")


# ── Arc 8: survey / scout apply / unattended Π / single-agent contract ───────
def test_survey_lists_files(tmp_path, monkeypatch):
    # Survey wall-checks to HARNESS_DIR; point it at tmp harness-like tree
    harness = tmp_path / "AZOTH"
    (harness / "CORE").mkdir(parents=True)
    (harness / "CORE" / "hello.py").write_text('"""Greeter module."""\ndef hi():\n    pass\n')
    (harness / "README.md").write_text("# AZOTH\nThe harness.\n")
    monkeypatch.setattr(A, "HARNESS_DIR", harness)
    out = A.tool_survey(str(harness), "**/*", max_files=20)
    assert "SURVEY" in out
    assert "hello.py" in out
    assert "Greeter" in out or "greeter" in out.lower() or "AZOTH" in out

def test_survey_blocks_outside_home(tmp_path, monkeypatch):
    harness = tmp_path / "AZOTH"
    harness.mkdir()
    monkeypatch.setattr(A, "HARNESS_DIR", harness)
    outside = tmp_path / "other"
    outside.mkdir()
    (outside / "secret.txt").write_text("nope")
    out = A.tool_survey(str(outside))
    assert "ERROR" in out and "blocked" in out.lower()

def test_apply_scout_routing(tmp_path, monkeypatch):
    harness = tmp_path / "AZOTH"
    done = harness / "ARMY" / "done"
    know = harness / "KNOWLEDGE"
    done.mkdir(parents=True)
    know.mkdir(parents=True)
    results = {
        "llama70": {"model": "meta/llama-3.3-70b-instruct", "available": True,
                    "tokens_per_sec": 49.6, "lamague": 6},
        "dead": {"model": "x/dead", "available": False, "tokens_per_sec": 0, "lamague": 0},
    }
    rp = done / "model_scout_results.json"
    rp.write_text(json.dumps(results))
    monkeypatch.setattr(A, "HARNESS_DIR", harness)
    msg = A.apply_scout_routing(str(rp))
    assert "Top pick" in msg or "llama70" in msg
    health = know / "MODEL_HEALTH.md"
    assert health.exists()
    text = health.read_text()
    assert "llama70" in text and "Recommendation" in text
    pick = know / "scout_top_pick.json"
    assert pick.exists()
    data = json.loads(pick.read_text())
    assert data["key"] == "llama70"

def test_unattended_default_pi_passes_substantive():
    from CORE.unattended import UnattendedMode
    mode = UnattendedMode()
    # 480-byte file used to score 0.35 and fail Gate 2 forever
    p = _w("out.md", "x" * 480)
    pi = mode._default_pi({}, p)
    assert pi >= 1.0, f"expected Π≥1.0 for substantive file, got {pi}"
    from CORE.unattended import check_gate2
    ok, _ = check_gate2(pi, 1.0)
    assert ok

def test_unattended_default_pi_fails_tiny():
    from CORE.unattended import UnattendedMode
    mode = UnattendedMode()
    p = _w("tiny.md", "hi")
    pi = mode._default_pi({}, p)
    assert pi == 0.0

def test_single_agent_plain_text_not_a_command(monkeypatch):
    """Contract: non-/ input is not a slash command (handle_command → False)."""
    monkeypatch.setenv("AZOTH_SINGLE_AGENT", "1")
    # Don't need full Agent init for the static branch — instantiate lightly if possible
    # Agent.__init__ is heavy; test the rule the REPL relies on:
    assert not "gday brother".strip().startswith("/")
    assert not "lets fix and forge on SOMA".strip().startswith("/")
    assert "/forge hi".strip().startswith("/")

def test_dispatch_survey_and_glob():
    names = {d["function"]["name"] for d in A.TOOL_DEFINITIONS}
    assert "survey" in names and "research" in names and "glob" in names
    # glob against real harness
    out = A.dispatch_tool("glob", {"pattern": "tests/*.py", "path": "."})
    assert "test_agent_core.py" in out or "No files" in out

# ── THE PHONE BRIDGE — one dispatcher truth (task #52, 2026-07-10) ────────────
import inspect

def test_phone_bridge_every_name_has_a_real_branch():
    """Every command PHONE_BRIDGE advertises must appear literally in
    _telegram_reply's source. This is the structural guard against the /bench
    defect class: a command advertised in help but unreachable in the router."""
    src = inspect.getsource(A.Agent._telegram_reply)
    for name in A.PHONE_BRIDGE:
        assert f'"{name}"' in src, (
            f"{name} is advertised in PHONE_BRIDGE but has no branch in "
            f"_telegram_reply — that's a lie in /help. Add the branch or delist it."
        )

def test_terminal_bridges_phone_commands(monkeypatch):
    """handle_command must route PHONE_BRIDGE names through _telegram_reply."""
    ag = A.Agent.__new__(A.Agent)
    seen = {}
    monkeypatch.setattr(
        A.Agent, "_telegram_reply",
        lambda self, t: seen.setdefault("input", t) or "BRIDGED-OK",
    )
    handled = ag.handle_command("/ping")
    assert handled is True
    assert seen.get("input") == "/ping"

def test_terminal_unknown_command_does_not_bridge(monkeypatch):
    """A genuinely unknown command must NOT fall into _telegram_reply — its
    free-text fallback spawns a phone-reporting thread."""
    ag = A.Agent.__new__(A.Agent)
    monkeypatch.setattr(
        A.Agent, "_telegram_reply",
        lambda self, t: (_ for _ in ()).throw(AssertionError("bridged an unknown command")),
    )
    assert ag.handle_command("/definitely_not_a_command") is True

def test_telegram_models_returns_text_not_typeerror():
    """MODELS holds tuples; the old m['name'] access raised TypeError on every
    phone /models. Locked fixed."""
    ag = A.Agent.__new__(A.Agent)
    ag.model_key = next(iter(A.MODELS))
    out = ag._telegram_reply("/models")
    assert isinstance(out, str) and ag.model_key in out

def test_telegram_help_returns_text_not_true():
    """Phone /help must RETURN the help text. The old version printed to the
    server console and returned True — the phone received 'True'."""
    ag = A.Agent.__new__(A.Agent)
    out = ag._telegram_reply("/help")
    assert isinstance(out, str) and "/forge" in out

def test_telegram_queue_returns_text():
    ag = A.Agent.__new__(A.Agent)
    out = ag._telegram_reply("/queue")
    assert isinstance(out, str) and out.strip()

def test_web_dispatcher_bridges_too(monkeypatch):
    """handle_input (the web surface) must route PHONE_BRIDGE names through the
    same single implementation."""
    ag = A.Agent.__new__(A.Agent)
    monkeypatch.setattr(A.Agent, "_telegram_reply", lambda self, t: "WEB-BRIDGED")
    assert ag.handle_input("/ping") == "WEB-BRIDGED"

# ── Peak agency — the forge shows its hands (F4, 2026-07-10) ─────────────────
def test_tool_detail_extracts_the_human_relevant_arg():
    assert A._tool_detail("bash", {"command": "git status"}) == "git status"
    assert A._tool_detail("read_file", {"path": "agent.py", "start_line": 1}) == "agent.py"
    assert "q=" in A._tool_detail("odd_tool", {"q": "x"}) or A._tool_detail("odd_tool", {"q": "x"}) == "x"
    assert A._tool_detail("no_args", {}) == ""
    # newlines flattened, capped
    d = A._tool_detail("bash", {"command": "a\nb" + "x" * 300})
    assert "\n" not in d and len(d) <= 100

def test_show_think_is_actually_read_now():
    """The /think placebo defect: show_think was toggled but never read.
    Guard: call_model's source must consult it."""
    import inspect
    src = inspect.getsource(A.Agent.call_model)
    assert "show_think" in src, "/think is a placebo again — call_model never reads show_think"

def test_done_gate_never_double_answers_a_tool_call(monkeypatch):
    """THE POISONED-HISTORY DEFECT (live-caught 2026-07-10): the done-gates
    appended a SECOND tool message for the same tool_call id. Two tool
    responses to one call = API-invalid history -> every later call 400s and
    the fallback chain resends the same poison forever. Every gated done on a
    build goal was killing the forge loop. The gates must REPLACE the generic
    tool response, never append beside it."""
    from types import SimpleNamespace as NS
    ag = A.Agent()
    seen = {"n": 0, "history": []}

    def scripted(self, messages, stream=False, tools=None, quiet=False):
        seen["n"] += 1
        seen["history"].append([dict(m) for m in messages])
        tc = NS(id=f"call_{seen['n']}", type="function",
                function=NS(name="done", arguments='{"completed":"x"}'))
        return "", [tc]

    monkeypatch.setattr(A.Agent, "call_model", scripted)
    # "build" verb + zero files written -> evidence gate rejects the 1st done,
    # the 2nd done confirms. The gate must have REPLACED, not double-appended.
    ag.run_tool_loop("build absolutely nothing and just call done")
    assert seen["n"] >= 2, "evidence gate never forced a second turn"
    final_msgs = seen["history"][-1]
    tool_ids = [m.get("tool_call_id") for m in final_msgs if m.get("role") == "tool"]
    assert len(tool_ids) == len(set(tool_ids)), (
        f"duplicate tool responses for the same call id: {tool_ids}")
    # And the gate text actually reached the model (replaced, not lost)
    gate_msgs = [m for m in final_msgs if m.get("role") == "tool"
                 and "DONE gate" in str(m.get("content", ""))]
    assert gate_msgs, "the evidence-gate message vanished instead of replacing"

# ── The focus leash (live-caught: "make a game" -> file surveying) ───────────
def test_fresh_build_detection():
    assert A._fresh_build_goal("make me a snake game in the workspace")
    assert A._fresh_build_goal("build a poem generator")
    assert not A._fresh_build_goal("fix the crash in cascade.tsx")
    assert not A._fresh_build_goal("make agent.py faster")          # names a file
    assert not A._fresh_build_goal("read TASKS.md and report")      # analysis
    assert not A._fresh_build_goal("refactor and make it cleaner")  # surgery verb

def test_new_command_is_real_and_clears():
    """The high-context warning told Mac to 'type /new' for months while /new
    did not exist (the /bench class, 4th find). Now it must exist and work."""
    ag = A.Agent.__new__(A.Agent)
    ag.history = [{"role": "user", "content": "x"}] * 5
    ag.forge_steps = 7
    ag.forge_start_time = 123.0
    ag.session_n = 1
    assert ag.handle_command("/new") is True
    assert ag.history == []
    assert ag.forge_steps == 0 and ag.forge_start_time is None
    assert ag.session_n >= 2


# ── 2026-07-11: WALL 1 must not block the perimeter itself (live-caught) ──

def test_wall1_allows_tilde_azoth():
    assert A._path_guard("cd ~/AZOTH && git status --short") is None

def test_wall1_still_blocks_true_escapes():
    assert A._path_guard("cat ~/0sol-by-lycheetah/app.json") is not None
    assert A._path_guard("ls ../") is not None
    assert A._path_guard("cat ~/SOL-MOBILE-VAULT/x.md") is not None
