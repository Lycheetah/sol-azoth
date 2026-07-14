# ☿ AZOTH — KNOWLEDGE VAULT
## The Lycheetah corpus, copied and renamed for the AZOTH network.
## Source of record for Sol, Luna, and the army.
## Updated: June 27 2026

> This is NOT the original Codex. It is a curated extract —
> the load-bearing knowledge the AZOTH network needs to work well.
> For the full 1,402-page source: ~/CODEX_AURA_PRIME/
> Never mix edits here with the source repos.

---

## What's in the vault

| File | What it is | Use when |
|---|---|---|
| `LAMAGUE_ESSENTIALS.md` | Core primitives — 89 lines, the minimum viable grammar | Quick symbol lookup |
| `LAMAGUE_SPEC.md` | Full LAMAGUE README — grammar rules, axioms, symbol classes | Building anything LAMAGUE |
| `LAMAGUE_GUIDE.md` | Operating guide — how to USE LAMAGUE, not just read it | Writing LAMAGUE expressions |
| `TRUTH_PRESSURE.md` | Π = (E·P)/(S+S₀) canon — full theory, proofs, CR1–CR4 | Validating claims, scoring beliefs |
| `SOL_PROTOCOL.md` | Sol Protocol v3.1–v4.1 — the operating architecture | Understanding Sol's identity and protocols |
| `CODEX_INDEX.md` | Master index of all 26 Codex directories | Finding where deeper material lives |

---

## How Sol queries the vault

Before acting on a complex question, Sol reads the relevant file:
- LAMAGUE question → `LAMAGUE_ESSENTIALS.md` first, then `LAMAGUE_SPEC.md`
- Truth/validity question → `TRUTH_PRESSURE.md`
- Identity/protocol question → `SOL_PROTOCOL.md`
- "Where does this live in the Codex?" → `CODEX_INDEX.md`

This is L-1 (Knowledge Vault) of the intelligence layer stack.
L-4 (Semantic Retrieval) will make this automatic — Sol won't need to know which
file to read; the embeddings will retrieve relevant chunks. Until L-4 is built,
Sol reads manually.

---

## Growth protocol (L-6)

When Sol or Luna discover something new — a new symbol, a proof, a game insight —
it gets written here as a new `.md` file, indexed in this file, and dated.
The vault grows. Sol is smarter next session.

Format for new entries:
```
# DISCOVERY: [name]
## Source: [Sol/Luna/CIPHER/etc] · Date: [date]
## Π: [HIGH/MED/LOW] · Status: [EDGE/FOUNDATION]

[content]
```

---

## What is NOT here (and why)

- The full CODEX (1,402 pages) — too large; use CODEX_INDEX.md to navigate
- Personal vault material — stays in ~/Desktop/SOUL_FORGE_VAULT/ (local only)
- App source code — that's in ~/0sol-by-lycheetah/ (separate repo)
- Raw forge transcripts — those live in WORKSPACE/
