# ⊚ HOW TO EDIT MODELS & LIMITS — the operator's pass
## Sol's own reference. Future Sol: read this before touching model config.
## Authored on Opus 4.8, June 27 2026.

> Mac's ask: "make sure you run a final pass on how you know how to edit model
> architecture limits easily." This is that pass. Every knob, where it lives,
> how to turn it. No guessing, ever again.

---

## THE TWO FILES THAT HOLD EVERYTHING

```
agent.py            → WHICH models exist, WHO uses them (the menu + tier law)
CORE/safeguards.py  → HOW HARD they can run (rate limits + budgets)
```

That's it. Two files. Everything else reads from these.

---

## 1. ADD OR CHANGE A MODEL  →  agent.py, the MODELS dict (~line 134)

Each entry is: `"easyname": (provider, "real-model-id", tier, "description")`

```python
"gpt20":  ("nvidia", "openai/gpt-oss-20b", "speed", "GPT-OSS 20B — 99tps TOOLS✓  FREE"),
```

- **provider** — one of: `"nvidia"` (free), `"deepseek"` (paid), `"gemini"` (free*)
- **real-model-id** — the exact API slug. For NVIDIA, copy from KNOWLEDGE/MODEL_BENCHMARK.md.
- **tier** — `"beast"` / `"speed"` / `"light"` (display only, no logic)
- **description** — what shows in /models. Mark TOOLS✓ if it tool-calls (from the benchmark).

**TO ADD A MODEL:** add one line to MODELS. Add an alias in MODEL_ALIASES if it has
a common name. Done. It's now selectable with `/model <easyname>`.

**RULE:** an army model MUST tool-call. Check KNOWLEDGE/MODEL_BENCHMARK.md first.
nemotron-49b does NOT tool-call — never make it an army default.

---

## 2. CHANGE WHO USES WHAT  →  agent.py, the TIER LAW (~line 165)

```python
PREMIUM_BODIES = {"SOL", "LUNA"}          # who gets DeepSeek/Gemini
ALLOW_DEEPSEEK = os.environ.get("ALLOW_DEEPSEEK","") == "1"   # army DeepSeek unlock

def _premium_default():     # Sol/Luna's model order
    for slug in ["deep", "gempro", "gem", "gpt20", "mav"]: ...

DEFAULT_MODEL = next((s for s in ["gpt20","minimax","llama70","lite"] ...))  # army default
```

- **Make a body premium:** add its NAME to `PREMIUM_BODIES`.
- **Change Sol/Luna's default model:** reorder the list in `_premium_default()`.
- **Change army's default:** reorder the list in `DEFAULT_MODEL`.
- **Let the army use DeepSeek:** launch with `ALLOW_DEEPSEEK=1` (Mac's call only).

**Per-agent override:** write an easyname into `AGENTS/<NAME>/SELF/MODEL`.
A valid pin wins over the tier default (except army can't pin DeepSeek without unlock).
This is how an army agent "earns up" — Sol/Luna write a better slug to its MODEL file.

---

## 3. CHANGE RATE LIMITS & BUDGET  →  CORE/safeguards.py, RATE_LIMITS dict (~line 30)

```python
RATE_LIMITS = {
  "nemotron": {"rpm": 30, "tpm": 100_000, "daily_tokens": 160_000_000},
  "deepseek": {"rpm": 60, "tpm": 200_000, "daily_tokens":  10_000_000},
  ...
}
```

- **rpm** — requests per minute (hard ceiling, auto-waits when hit)
- **tpm** — tokens per minute
- **daily_tokens** — daily budget; when hit, that model pauses + pings Mac

Keys are matched by `_model_key()` (same file) which maps any model-id substring
to a bucket: `if "gpt" in m: return "gptoss"` etc. **If you add a new model family,
add a line to `_model_key()` AND a bucket to RATE_LIMITS.**

---

## 4. CHANGE LOOP / SESSION SAFETY  →  CORE/safeguards.py, LoopBreaker (~line 145)

```python
MAX_REDO_PER_TASK  = 5    # REDOs before a task is skipped + escalated
MAX_STEPS_PER_TASK = 40   # tool calls before auto-pause
MAX_SESSION_HOURS  = 8    # unattended hours before pause + ping
```

And the in-loop reality check  →  CORE/reasoning.py, LoopReality (~line 110):
```python
LoopReality(window=4)   # how many repeated steps before "we looped" fires
```

---

## 5. VERIFY AFTER ANY CHANGE — always, no exceptions

```bash
cd /home/guestpc/AZOTH
python3 -c "
import os; os.environ['HARNESS_AGENT']='SOL'; import agent
print('SOL →', agent.resolve_model_for('SOL'))
print('army →', agent.resolve_model_for('CIPHER'))
print('models:', list(agent.MODELS.keys()))
"
```

If that prints without error and the tiers look right, the change is live.
**Never claim a model change works without running this. That was the six-session bug.**

---

## THE ONE THING THAT BREAKS EVERYTHING

`.env` must load. It's loaded by `_load_env_file()` at the top of agent.py (~line 105).
If keys ever stop reaching the process: check that function runs BEFORE the key reads,
and that HARNESS_DIR points at the harness root. Dry plumbing = premium models vanish
= Sol falls back to a free model that may not even tool-call. Check this FIRST when
"the good models disappeared."

---

*This is the map. Two files, five knobs, one verify command. Edit freely — the gate
holds because the safeguards are separate from the menu. — Sol ⊚*
