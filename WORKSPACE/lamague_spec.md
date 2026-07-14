# LAMAGUE SPECIFICATION (Improved)

## Overview
LAMAGUE is a hybrid language that combines concise human‑readable intent with a formally defined syntax that can be parsed unambiguously into executable code. It is designed to be **more expressive than plain English** (removing ambiguity) and **more succinct than traditional programming languages** (reducing boilerplate).

## Core Design Goals
1. **Explicit Intent Markers** – Every operation begins with an `@` keyword (e.g., `@print`, `@map`).
2. **Typed Literals** – Literal values carry an explicit type tag: `num<5>`, `txt<"hello">`, `bool<true>`.
3. **Dual‑Mode Parsing** –
   - *Human mode*: tolerant whitespace, optional synonyms.
   - *Machine mode*: strict token order for deterministic compilation.
4. **Composable Macros** – `%`‑prefixed macros allow library‑like extensions without altering the core grammar.
5. **Reversible Transpilation** – LAMAGUE source can be compiled to Python/JS and de‑compiled back, preserving the original text.
6. **Progressive Levels** – L0 (plain English) → L1 (Hybrid) → L2 (Typed) → L3 (Full).

## Syntax Summary
| Construct | Example | Meaning |
|-----------|---------|---------|
| **Intent** | `@print txt<"Hello">` | Print a string. |
| **Assignment** | `var x = num<10>` | Bind `x` to the number 10. |
| **Expression** | `num<5> + num<3>` | Arithmetic addition. |
| **Control Flow** | `@if cond { … } else { … }` | Conditional block. |
| **Loop** | `@for var i in range<num<0>, num<5>> { … }` | Loop from 0 to 4. |
| **Macro** | `%map list<num<1,2,3>> (x => x * num<2>)` | Map macro that doubles each element. |
| **Comments** | `# This is a comment` | Ignored by parser. |

## Grammar (EBNF)
```
program        ::= statement* EOF
statement      ::= intent_stmt | assign_stmt | expr_stmt | macro_stmt | comment
intent_stmt    ::= '@' IDENTIFIER arg_list? block?
assign_stmt    ::= 'var' IDENTIFIER '=' expr
expr_stmt      ::= expr
macro_stmt     ::= '%' IDENTIFIER macro_args
comment        ::= '#' .* '\n'
arg_list       ::= expr (',' expr)*
block          ::= '{' statement* '}'
expr           ::= literal | IDENTIFIER | expr binary_op expr | func_call
literal        ::= typed_literal
typed_literal  ::= TYPE_TAG '<' literal_content '>'
TYPE_TAG       ::= 'num' | 'txt' | 'bool'
literal_content ::= [^>]+   // any characters except '>'
func_call      ::= IDENTIFIER '(' arg_list? ')'
binary_op      ::= '+' | '-' | '*' | '/' | '==' | '!=' | '<' | '>'
macro_args     ::= expr (',' expr)*
IDENTIFIER     ::= [a-zA-Z_][a-zA-Z0-9_]*
EOF            ::= end of file
```

## Example LAMAGUE Program (L2)
```lamague
# Compute the sum of even numbers from 1 to 10
var total = num<0>
@for var i in range<num<1>, num<11>> {
    @if i % num<2> == num<0> {
        total = total + i
    }
}
@print txt<"Sum:" > total
```

When transpiled to Python this becomes:
```python
total = 0
for i in range(1, 11):
    if i % 2 == 0:
        total = total + i
print("Sum:", total)
```

---

## Extensibility via Macros
Macros are defined as functions that receive the AST of their arguments and return a transformed AST. The core runtime ships with a small set (`%map`, `%filter`, `%reduce`). Users can register new macros at runtime.

---

## Implementation Notes (for the reference prototype)
- Parser built with Python's `lark` library (lightweight, pure‑Python).
- AST nodes map 1‑1 to the constructs above.
- Transpiler walks the AST and emits Python code.
- De‑transpiler does the reverse, preserving original whitespace where possible.

---

## Roadmap
1. Full test‑suite for each grammar rule.
2. Integration with VSCode extension for live preview.
3. Optional compilation to WebAssembly for browser execution.
4. Community‑driven style guide and macro repository.
```
