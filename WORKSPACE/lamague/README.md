# ⟁ LAMAGUE — Runnable Examples
## Verified against CORE/lamague_interpreter.py
## Forge: T6.1 · July 3 2026

These examples all pass against the actual interpreter. Run them with:

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from CORE.lamague_interpreter import LAMAGUE
lam = LAMAGUE()
# paste any example below
print(lam.eval('...'))
"
```

---

### 1. Arithmetic
```lamague
42
3 + 4
10 - 3
6 * 7
10 / 2
(3 + 4) * 2
```

### 2. Variables & Assignment
```lamague
a := 1
a := a + 1
a
```

### 3. Sequences
```lamague
a := 1; a := a + 1; a
```

### 4. Blocks
```lamague
b := {c := 10; c * 2}
```

### 5. Conditionals (Implication ∴)
```lamague
x := 20
x > 10 ∴ 100
score := 85
score > 90 ∴ "excellent" ∴ "pass"
```

### 6. While Loops
```lamague
count := 0
while (count < 5) { count := count + 1 }
count
```

### 7. Lambda Functions
```lamague
double := λ(x) x * 2
double(21)

add := λ(a, b) a + b
add(10, 32)
```

### 8. Try/Catch
```lamague
try { 42 } catch (e) { None }
```

### 9. Nested Control Flow
```lamague
{
  grade := "pass";
  score > 90 ∴ grade := "excellent";
  grade
}
```

### 10. LAMAGUE Symbols
```lamague
Π                 # truth pressure — returns function
μ                 # agency measure — returns function
σ                 # boundary integrity
ω                 # field coherence
```

### 11. Symbol Operations
```lamague
Φ↑                # ascent — amplify state
Ψ_inv             # descent — invert state
Ao                # anchor to baseline
```
