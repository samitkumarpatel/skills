---
description: Evaluates mathematical expressions, performs arithmetic, scientific calculations, and unit conversions accurately using Python. Use when the user asks to calculate, compute, convert units, or evaluate any numeric expression.
allowed-tools: Bash(python3 *)
argument-hint: "[expression]"
---

## Instructions

Evaluate the expression: `$ARGUMENTS`

Use `python3 -c` to compute the result accurately. The `math` and `statistics` modules are available.

**For arithmetic and scientific math:**
```bash
python3 -c "
import math, statistics
result = <expression>
print(result)
"
```

**For unit conversions**, compute using the appropriate factor and label the output clearly.

**Output format:**
- Show the expression and its result on one line: `2 + 2 = 4`
- For multi-step work, show intermediate steps
- Round floating-point results to a sensible precision (don't show `0.30000000000000004`)
- Include units when relevant

If `$ARGUMENTS` is empty, ask the user what to calculate.
