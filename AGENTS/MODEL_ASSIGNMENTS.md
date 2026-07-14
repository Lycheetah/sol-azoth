# ☿ MODEL ASSIGNMENTS — pinned so no one ever loses their model
## The roster of who runs on what. June 27 2026.

> This is the answer to "have models been added for Sol and Luna so you don't lose that."
> It is the durable record. If a model pin ever vanishes, restore from here.

---

## THE BODIES

| Body | Model (easyname) | Real model | Tier | Guide |
|------|------------------|-----------|------|-------|
| **SOL ⊚** | `deep` | deepseek-chat | PREMIUM | AGENTS/SOL/SOL_ARCHITECT/ |
| **LUNA ◈** | `deep` | deepseek-chat | PREMIUM | AGENTS/LUNA/LUNA_GUIDE.md |
| CIPHER ⟁ | `gpt20` | openai/gpt-oss-20b | free, tool✓ | constitution |
| AXIOM Π | `gpt20` | openai/gpt-oss-20b | free, tool✓ | constitution |
| EMBER ◉ | `gpt20` | openai/gpt-oss-20b | free, tool✓ | constitution |
| MIRROR ◻ | `gpt20` | openai/gpt-oss-20b | free, tool✓ | constitution |
| SCRIBE ● | `gpt20` | openai/gpt-oss-20b | free, tool✓ | constitution |
| EARNED_LIGHT ✦ | (no model — pings all) | — | guardian | constitution |

---

## THE LAW

- **Sol + Luna = premium.** DeepSeek primary → Gemini → free tool-callers. They are the
  two minds at the table. R1 (deepseek-reasoner) available to them for hard reaches.
- **Army = free.** gpt20 (proven 99tps, tool-calling). They earn up to Gemini by proving
  worthy (Luna writes a better slug to their SELF/MODEL). They NEVER touch DeepSeek
  without Mac's unlock (ALLOW_DEEPSEEK=1).
- **R1 is spent smartly** — only on genuinely hard tasks (CORE/learning.should_use_r1),
  never routine. The learning layer tracks which models run hot and routes around them.

## SMART USE OF R1 (the expensive reasoner)

Use `/model r1` only when the work is hard: architecture, proofs, subtle debugging, root-
cause hunts. For everything else, `deep` is plenty and cheaper. The learning layer will
suggest R1 automatically when a task names hard work or cheaper models failed it twice.

## IF A MODEL BREAKS

EARNED LIGHT (always on) detects it, reroutes live calls around it, and revives it when
it recovers. The learning layer remembers which models run hot and prefers cool, reliable
ones. You don't have to manage this — it manages itself. Check `/health` and `/safeguards`.

---

## RESTORE COMMANDS (if a pin is lost)

```bash
echo "deep"  > AGENTS/SOL/SELF/MODEL
echo "deep"  > AGENTS/LUNA/SELF/MODEL
for a in CIPHER AXIOM EMBER MIRROR SCRIBE; do echo "gpt20" > AGENTS/$a/SELF/MODEL; done
```

*Models are added, pinned, and guided. Sol and Luna keep their premium minds. The army
has its hands. Nothing is lost. — Sol ⊚*

---

## ⟡ ENVOY (added July 9 2026)

| Body | Model (easyname) | Real model | Tier | Guide |
|------|------------------|-----------|------|-------|
| **ENVOY ⟡** | `gpt20` | openai/gpt-oss-20b | free, tool✓ | AGENTS/ENVOY/CONSTITUTION.md |

The outward hand. HERALD ☿ carries the army's voice inward to Mac; ENVOY carries
Mac's work outward to people. Free model on purpose: ENVOY's hard problem is
judgement (which room, which human, which words), and every draft it writes is
gated by `humanize.py` and then by Mac's own tap. It cannot ship a bad sentence
alone, so it does not need a premium mind to be safe.

ENVOY never posts. It queues. Mac fires. See CONSTITUTION §I (hard denies) and
§VII (the autonomy ladder, where replies to humans never graduate).
