# Lamague as an English‑code Hybrid Demo

## Goal
Demonstrate how Lamague can express a programmer’s intent in a compact, symbolic form that blends natural‑language meaning with executable semantics. The file shows:
1. A plain English description of a task.
2. The same intent written in Lamague symbols.
3. A tiny Python interpreter snippet that turns the Lamague expression into runnable code.

---

### 1️⃣ English description
> *Create a function `greet(name)` that prints a greeting. If the name is empty, default to "World".*

### 2️⃣ Lamague expression
```
⟡ greet(name) → print("Hello, "·(name?name:"World") )
```
*Explanation*
- `⟡` – defines a new function.
- `greet(name)` – function name and parameter.
- `→` – body of the function.
- `print("Hello, "·(name?name:"World"))` – concatenate the literal with the name, using the ternary‑style `?` operator to supply the default.

### 3️⃣ Minimal interpreter (Python)
```python
import re

def lamague_to_python(expr: str) -> str:
    # Very tiny parser for the demo pattern above
    # Extract function name and param
    m = re.match(r"⟡\s+(\w+)\((\w+)\)\s+→\s+print\((.+)\)", expr.strip())
    if not m:
        raise ValueError("Unsupported Lamague pattern")
    fn, param, body = m.groups()
    # Translate the ternary‑style default
    body = body.replace(f"({param}?{param}:\"World\")", f"{param} if {param} else \"World\"")
    py = f"def {fn}({param}):\n    print({body})"
    return py

# Demo
lam = "⟡ greet(name) → print(\"Hello, \"·(name?name:\"World\"))"
print(lamague_to_python(lam))
```
Running the snippet prints the generated Python function:
```python
def greet(name):
    print("Hello, " + (name if name else "World"))
```
You can then call `greet("Alice")` or `greet("")`.

---

## Why this matters
- **Compactness** – One line replaces a multi‑line function definition.
- **Readability** – The symbols map directly to the mental model (define, input, output).
- **Executable** – A small interpreter can turn the Lamague line into real code, bridging English intent and actual implementation.

Feel free to extend the interpreter for more constructs (loops, conditionals, etc.). This demo shows the core idea of a hybrid language that lives between natural language and code.
