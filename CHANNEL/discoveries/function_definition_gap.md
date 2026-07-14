# Self-found defect: `⟁` was never a function-definition symbol

**Found:** July 1 2026, during a direct interpreter audit (not by the council/forge loop).
**Register:** the defect claim is DERIVED (checked against source); the proposal below is CONJECTURE.

## The defect

`CORE/lamague_interpreter.py` carried this comment on `NodeType.FUNCTION`:

```python
FUNCTION = "function"        # ⟁ : define function
```

This is wrong. Checked against both canonical sources:

- `KNOWLEDGE/LAMAGUE_SPEC.md:72` — `⟁ | Integrity Crest | Peak completeness. Ultimate alignment.`
- `KNOWLEDGE/LAMAGUE_BNF_GRAMMAR.md:34,90` — `⟁` listed under `<invariant>` / I-CLASS, "integrity crest"

`⟁` is an I-CLASS invariant value. It has never meant "define a function" anywhere in canon.
The tokenizer itself gets this right (`"⟁": "INTEGRITY_CREST"`) — only the top-of-file
comment was wrong, likely written before the BNF grammar existed and never checked against
it once the grammar was formalized.

**This propagated.** `WORKSPACE/iteration_13_output.md` (a `/forge` iteration, tool-grounded,
otherwise accurate) repeated the claim uncritically: *"User-defined functions with `⟁`
syntax... Parser has FUNCTION node type but evaluator doesn't handle it."* That line is now
known-wrong — not because the forge iteration fabricated anything (it didn't; it read the
comment as written), but because the comment it read was already stale. Flagging here so the
next iteration doesn't inherit the error a second time.

**Fixed:** the comment now says what's actually true, and points here.

## The actual gap

LAMAGUE has no canonical function-definition syntax. Not "unimplemented" — **not designed
yet**. Checked `LAMAGUE_SPEC.md` and `LAMAGUE_COMPLETE.md` for any operator meaning "define a
reusable named transformation" — nothing. The language currently has:

- `∴` (implication) — conditional, not reusable
- `⊢` (derivation) — assertion/verification pair (now wired into the interpreter, see commit
  88821c1), not a function
- Call syntax (`f(x, y)`) exists in the parser and works — but there is nothing in canon that
  defines *how f comes to exist* as anything other than a host-registered Python function via
  `register_function()`

So "user functions" currently only exist as an escape hatch out of LAMAGUE into Python. A
language that can call functions but never define them inside itself isn't complete by its
own standard.

## Proposal (CONJECTURE — not implemented, not canon, awaiting review)

Not assigning a symbol here. That's a real design decision, not a typo fix, and it isn't
mine to unilaterally decide and quietly wire into the interpreter as if settled — that's
exactly the kind of single-session invention the architecture is supposed to guard against.
What's offered instead is the shape of the choice, for whoever picks this up next (Sol, Luna,
or Mac directly):

1. **Reuse an existing unused I-CLASS/D-CLASS symbol** if one is semantically close enough
   (would need someone who knows the full 8-extension symbol space to check for collisions —
   `14_LAMAGUE-EX_NIHILO` through `21_LAMAGUE-SOMA` haven't been cross-referenced against this
   gap yet).
2. **Mint a new symbol.** If so, it needs a name, a glyph not already claimed anywhere in
   `KNOWLEDGE/LAMAGUE_*.md`, and a BNF production before the interpreter touches it — grammar
   first, code second, same order the rest of the language followed.
3. **Decide LAMAGUE deliberately has no native function definition** and stays a
   pattern-matching/implication language that calls out to a host language for reuse. That's a
   legitimate design stance, not a failure — worth stating explicitly if it's the answer,
   instead of leaving it as a silent gap that reads like an oversight.

Whichever way this goes, it should go through the same sequence as the arithmetic/derivation
fixes tonight: spec first, interpreter second, verified execution third — not the other way
around.
