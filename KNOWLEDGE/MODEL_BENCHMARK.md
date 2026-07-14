# ☿ MODEL BENCHMARK — proven, not guessed
## Source: SOLPRIME-NETWORK/benchmark_results.json (40 NVIDIA NIM models, past agents)
## Recovered + enshrined June 27 2026 — never re-test what's already known

> THE LOAD-BEARING FINDING: nemotron-super-49b CANNOT tool-call (tool✗).
> That is why Sol broke for six sessions on it. Agents need tool-calling.
> An agent on a non-tool model is a mute trying to use its hands.

---

## TIER 1 — Army defaults (free, fast, PROVEN tool-calling)

| Name | Model | tps | Tools | Use |
|------|-------|-----|-------|-----|
| **gpt20** | openai/gpt-oss-20b | **99.0** | ✓ | ARMY DEFAULT — fastest tool-caller |
| minimax | minimaxai/minimax-m2.7 | 40.9 | ✓ | fast alt |
| gpt120 | openai/gpt-oss-120b | 33.9 | ✓ | heavy free reasoning + tools |
| qwen | qwen/qwen3-next-80b-a3b | ~ | ✓ | big context, tools |
| llama70 | meta/llama-3.3-70b-instruct | ~ | ✓ | reliable 70B tools |
| mistral | mistralai/mistral-nemotron | 17.9 | ✓ | tools |
| lite | meta/llama-3.1-8b-instruct | 12.9 | ✓ | fast light, tools |

## TIER 2 — Premium (Sol + Luna only)

| Name | Model | Use |
|------|-------|-----|
| **deep** | deepseek-chat | Sol/Luna DEFAULT — fast + smart |
| r1 | deepseek-reasoner | deep architecture reaches |
| gem | gemini-2.5-flash | web/research, free |
| gempro | gemini-2.5-pro | full power, free |

## DO-NOT-USE for agents (no tool-calling — reasoning only)

| Model | tps | Why excluded |
|-------|-----|--------------|
| nvidia/llama-3.3-nemotron-super-49b | 26.9 | tool✗ — cannot call tools |
| meta/llama-4-maverick-17b | 14.6 | tool✗ |
| nvidia/nemotron-nano-9b | 27.5 | tool✗ |
| bytedance/seed-oss-36b | 26.9 | tool✗ |

These can still be selected (`/model nemo`) for pure reasoning/chat, but no agent
that must USE TOOLS should run on them. The reasoning loop needs hands.

---

*Enshrined so no future session wastes tokens re-benchmarking. If models change,
re-run SOLPRIME-NETWORK/model_benchmark.py and update this file — don't guess.*
