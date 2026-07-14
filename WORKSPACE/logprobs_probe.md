# Logprobs Probe — P6-T1
## Date: 2026-06-27
## Register: MEASURED

### VERDICT

| Provider | logprobs exposed | top_logprobs | Notes |
|---|---|---|---|
| DeepSeek (deepseek-chat) | ✓ YES | ✓ YES (3) | Full token confidence, bytes, alternates |
| NVIDIA (super49b NIM) | ✓ YES | ✓ YES (3) | Full token confidence — think-tokens visible too |
| Gemini (2.5-flash) | ✗ NO | ✗ NO | Unknown field — OpenAI-compat doesn't expose it |

### SIGNAL QUALITY (from sample)

DeepSeek: `logprob=0.0` on "sky" (P=1.0, zero strain), `-1.14e-05` on "The" (near-certain, tiny strain)
NVIDIA: `logprob=-1.19e-06` on first token (near-certain). Think-stream tokenized and exposed.

### IMPLICATIONS FOR Π

logprob is in log-probability space. Convert: confidence = exp(logprob)
- logprob=0.0     → confidence=1.0  → strain contribution S≈0
- logprob=-1.0    → confidence=0.37 → S≈medium
- logprob=-9999   → confidence≈0    → S≈max (forced/hallucinated token)

S from logprobs = 1 - mean(exp(logprob)) across factual claim tokens
This makes Π = (E·P)/(S+S₀) a live measured quantity, not an estimate.

### NEXT: P6-T2
Build CORE/logprob_pi.py:
- Wrap call_model to capture logprobs per call
- Compute mean confidence over response tokens
- Return as S signal feeding truth_pressure.py
