# VAEL — FULL ARCHITECTURE & CAPABILITIES
## For Sol's reference · Last updated 2026-06-13

---

## WHAT VAEL IS

VAEL is Mac's terminal AI operative. Not a chatbot — a working agent with real access to the Linux machine, the codebase, the internet, and AI models. It runs in the terminal, executes bash commands, reads/writes files, and can operate autonomously toward a goal.

**Sol speaks. VAEL builds.**

---

## HOW TO RUN

```bash
cd /home/guestpc/0420Vael-harness
python3 agent.py                    # interactive REPL
python3 agent.py --agent "goal"     # autonomous agent mode
python3 agent.py "quick question"   # one-shot
python3 agent.py --model nemotron   # start on specific model
```

---

## FULL COMMAND LIST

| Command | What it does |
|---------|-------------|
| `/help` | Show all commands |
| `/models` | List all 26 models with categories |
| `/model <key>` | Switch active model |
| `/run <cmd>` | Execute bash directly |
| `/agent <goal>` | Autonomous mode — VAEL works until done |
| `/bench` | Compare 3 models on same prompt |
| `/multi <prompt>` | Get responses from all 3 best models simultaneously |
| `/remember <name> <text>` | Save a memory (persists across sessions) |
| `/forget <name>` | Delete a memory |
| `/memories` | List saved memories |
| `/save` | Save current session to sessions/ as markdown |
| `/upgrade` | VAEL reads its own code and proposes improvements |
| `/status` | Current session info |
| `/tasks` | Open task list |
| `/crashes` | Unresolved crash log |
| `/clear` | Clear conversation history |
| `/quit` | Exit (auto-saves session) |

---

## 26 MODELS AVAILABLE

### Speed (fast, everyday use)
| Key | Model | Notes |
|-----|-------|-------|
| `deepseek` | DeepSeek Chat | Default · Fast · Reliable fallback |
| `llama8b` | Llama 3.1 8B | Tiny, instant |
| `gemma3n` | Gemma 3n | Edge, multimodal lite |
| `phi4` | Phi-4 Mini | Microsoft, efficient |
| `gptoss20b` | GPT OSS 20B | OpenAI open, small MoE |
| `step37` | Step 3.7 Flash | Fast, multimodal |
| `kimi` | Kimi K2 | Moonshot, auto fallback |

### Reasoning (hard problems, math, logic)
| Key | Model | Notes |
|-----|-------|-------|
| `r1` | DeepSeek R1 | Best reasoning, chain-of-thought |
| `llama` | Llama 3.3 70B | Meta flagship |
| `gemma` | Gemma 4 31B | Google dense |
| `super49b` | Nemotron Super 49B | NVIDIA tuned, tool calling |
| `minimax` | MiniMax M2.7 | 230B, long reasoning |
| `seed` | Seed 36B | ByteDance, agentic |

### Coding (dev, debugging, architecture)
| Key | Model | Notes |
|-----|-------|-------|
| `mistralmed` | Mistral Medium 3.5 128B | Best for code |
| `mistral` | Mistral Small 4 119B | 256k context |
| `mistrallarge` | Mistral Large 3 675B | Top Mistral |
| `gptoss` | GPT OSS 120B | OpenAI open MoE |
| `qwen122b` | Qwen3.5 122B | Agent-ready |
| `phi4full` | Phi-4 Multimodal | Code + vision |

### Creative (writing, lore, world-building)
| Key | Model | Notes |
|-----|-------|-------|
| `maverick` | Llama 4 Maverick | 128 experts, fast |
| `qwennext` | Qwen3-Next 80B | Ultra-long context |
| `deepseek_nv` | DeepSeek V4 Flash | 1M context |

### Vision (image understanding)
| Key | Model | Notes |
|-----|-------|-------|
| `llama90bv` | Llama 3.2 90B Vision | Image reasoning |
| `nemvl` | Nemotron VL 8B | Fast vision-language |
| `qwen` | Qwen3.5 397B | Massive, agentic |

### Beast (top tier, worth the wait)
| Key | Model | Notes |
|-----|-------|-------|
| `super` | Nemotron Super 120B | NVIDIA, 1M context |
| `nemotron` | Nemotron Ultra 550B | Best in-house |
| `mistralbig` | Mistral Large 3 675B | Frontier quality |

---

## AGENT MODE (AUTONOMOUS)

VAEL enters a ReAct loop — thinks, runs bash, observes output, repeats until done.

```bash
/agent fix the TypeScript error in lycheetah-mobile/app/(tabs)/companion.tsx
/agent list all sol_* AsyncStorage keys and their current values
/agent find every TODO in the Sol app and summarise them
/agent write a Python script that batch-renames enemy PNGs to Sol naming format
```

Max 20 steps per run. Uses BASH: and DONE: protocol internally.

---

## MULTI-MODEL MODE

`/multi <prompt>` — sends the same prompt to 3 models in parallel and prints all responses for comparison. Good for:
- Getting second opinions on architecture decisions
- Creative tasks where variety helps
- Verifying a reasoning answer across models

---

## MEMORY SYSTEM

Memories persist across sessions in `memory/*.md`.

```bash
/remember sol_app Sol app is at /home/guestpc/lycheetah-mobile, React Native, Expo SDK 54
/remember mac_prefs Mac moves fast, hates permission-seeking, wants verified work
/forget old_note
/memories
```

---

## PROTECTED CORE FILES

`core/` folder — read-only backups, never edit:
- `core/agent.py.bak` — harness source backup
- `core/AGENT.md.bak` — constitution backup
- `core/WHAT_VAEL_IS.md.bak` — identity doc backup

Restore: `cp core/agent.py.bak agent.py`

---

## FILE LAYOUT

```
0420Vael-harness/
├── agent.py              ← main harness (run this)
├── ui.py                 ← terminal styling
├── AGENT.md              ← VAEL's constitution
├── WHAT_VAEL_IS.md       ← VAEL's self-portrait
├── VAEL_ARCHITECTURE.md  ← this file
├── core/                 ← READ-ONLY backups
│   ├── agent.py.bak
│   ├── AGENT.md.bak
│   └── WHAT_VAEL_IS.md.bak
├── memory/               ← persistent memories (*.md)
├── sessions/             ← saved session logs
├── crashes/              ← crash reports
├── workspace/            ← scratch space for VAEL's work
│   ├── art/
│   ├── prompts/
│   ├── tests/
│   └── scratch/
└── tests/                ← harness test scripts
```

---

## KEYS

Both keys are in `agent.py` lines 27-28. Do not duplicate elsewhere.
- NVIDIA NIM: free tier, 26 models
- DeepSeek: paid key, R1 reasoning + Chat fallback
