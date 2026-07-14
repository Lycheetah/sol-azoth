# Orphaned AST node audit — systematic check after finding 3 by hand

**Date:** July 1 2026. **Register:** DERIVED (checked every claim by running code, not reading claims).

Tonight's session found three operators (`+`/`-`/`*`//`, then `⊢`) that had full parser methods
and evaluator cases written, but were never wired into the actual precedence chain `parse()`
walks — so they raised `ParseError` despite looking fully implemented in the source. Once
found twice, that's a pattern worth checking systematically rather than trusting the rest of
the file is fine. Wrote a script to cross-reference every `NodeType` enum member against
whether the parser ever constructs it and whether the evaluator ever handles it.

## Results

| NodeType | Parser constructs it? | Evaluator handles it? | Actual status |
|---|---|---|---|
| `BINOP` | now yes (commit 85b7d07) | now yes | **fixed tonight** |
| `DERIVATION` (`⊢`) | now yes (commit 88821c1) | yes | **fixed tonight** |
| `FUNCTION` | no | no | genuinely unimplemented — see `function_definition_gap.md`, no symbol assigned in canon |
| `MEASURE` (`⟨\|⟩`) | **no** | yes | dead node type, but `⟨\|⟩(a, b)` works anyway — see below |
| `ANCHOR`/`ASCENT`/`FOLD` (`Ao`/`Φ↑`/`Ψ`) | **no** | no | dead node types, but `Ao(a, b)` etc. work anyway — see below |
| `PRESERVE`/`DEMOTE` | **no** | no | genuinely nonfunctional — see below |
| everything else (`LITERAL`, `SYMBOL`, `CALL`, `IMPLICATION`, `CONJUNCTION`, `DISJUNCTION`, `ASSIGNMENT`, `SEQUENCE`, `COMPARISON`, `NEGATION`, `LIST`) | yes | yes | confirmed working |

## `MEASURE` / `ANCHOR` / `ASCENT` / `FOLD` — dead AST paths, but not dead features

Verified live: `⟨|⟩(5, 3)` returns `0.5`. `Ao(1, 2)` returns `2`. These are **not** broken —
but they don't work through their dedicated `NodeType.MEASURE`/`NodeType.ANCHOR` evaluator
cases, which are never reached. They work because `Π`, `⟨|⟩`, `Ao`, `Φ↑`, `Ψ` are all
registered as plain callables in `Evaluator._bind_builtins()`, so `name(args)` resolves through
the ordinary `NodeType.CALL` → `NodeType.SYMBOL` path like any user-registered function.

This isn't a bug in the sense of "produces a wrong answer" — it's a **Single Truth Rule**
flag: two implementations of the same feature exist (a dedicated AST node that's dead, and a
generic call-based path that's live), and the dead one should probably just be deleted rather
than left to confuse the next person who reads the enum and assumes it does something. Left
as-is tonight rather than deleting — removing an enum member is a smaller, cleaner fix than
tonight's other three, but it touches code shape rather than fixing a break, and didn't want to
make that call without flagging it first.

## `PRESERVE` / `DEMOTE` — genuinely nonfunctional

The enum comments describe intended syntax: `preserve={...}` (invariant set) and
`demote={...}` (contradiction set) — per the docstring, tied to the TRIAD kernel's error
handling story from earlier tonight's board discussion (`⟐(action, threshold)` silent-fail
symbol work). Verified live:

```
preserve={x=1}   -> ParseError: Unexpected token EQUALS ('=') at pos 8
demote={x=1}     -> ParseError: Unexpected token EQUALS ('=') at pos 6
{x=1}            -> {'x': 1}   (bare dict literal works fine on its own)
```

The generic `{key=val,...}` dict-literal syntax works standalone. `preserve`/`demote` are not
registered as functions in `_bind_builtins()` either, so there's currently no way to invoke
this concept at all — not via dedicated syntax, not via a function call. Same category as the
function-definition gap: a real, honestly-documented hole, not something papered over tonight.

## What this audit does NOT claim

Not claiming these are the only gaps — this checked reachability (does the parser ever build
this node, does the evaluator ever handle it), not correctness of the ones that *are* reachable
beyond what tonight's regression tests already covered. A deeper semantic audit (does
`NodeType.DERIVATION`'s `case` actually do anything useful, given the library's own `⊢`
function requires `.implies()` which nothing has) is a separate, open question — noted, not
solved, here.
