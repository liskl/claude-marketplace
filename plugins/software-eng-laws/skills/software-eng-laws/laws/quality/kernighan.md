# Kernighan's Law

**Category**: quality
**Detection**: code
**Short description**: Debugging is twice as hard as writing the code. If you write the code as cleverly as possible, you are, by definition, not smart enough to debug it.

## Overview

![Kernighan's Law](../images/kernighan-law.png)

Kernighan's Law says that debugging requires understanding what the code *actually* does, which can be twice as hard as writing it. When coding, a developer works with a specific mental model and full context. When debugging, they may encounter unfamiliar code — or their own code after the context has faded — and must reconstruct what it does from scratch.

Writing "clever" or complex code is essentially setting a trap for your future self. A maintainable approach typically surpasses an optimized version that is difficult to comprehend. If you write code at the limit of your intelligence, you won't be able to understand or troubleshoot it later. Even if it runs successfully when first written, it stays fragile.

## Takeaways

- Bug detection and removal is more complex than programming, because debugging requires understanding both the code *and* why it doesn't work.
- If you write code at the limit of your intelligence, you won't be able to understand or troubleshoot it later.
- Simple code with good structure and documentation is easier to debug, which saves time in the long run.
- Even code that runs successfully when you write it is fragile if it is too complex — you just haven't seen the bug yet.

## Examples

A compressed, "clever" function might be satisfying to write in 30 minutes but require 3 hours to debug months later. A clear, more verbose version of the same function might take 45 minutes to write initially but only 30 minutes to debug — a net win once you sum over the life of the code.

The asymmetry shows up everywhere: chained one-liner comprehensions with nested conditionals, unreadable regex, decorator stacks five deep, macros that generate code you can't grep for. Each is cheap to write and expensive to diagnose.

## Signals
- `complexity.long_functions` + deep nesting signals — functions you wrote at your cleverness limit.
- Heavy use of advanced language features (macros, metaclasses, reflection, decorators stacking 5 deep).
- One-liner list/dict comprehensions with nested conditionals.
- Regex > 80 chars without comments.

## Scoring Rubric
- 🟢 **Pass**: short functions, shallow nesting, readable idioms.
- 🟡 **Watch**: some clever sections that would benefit from explanation or extraction.
- 🔴 **Concern**: many long/deep functions, complex regex/meta-programming without comments.
- ⚪ **Manual**: domain inherently requires the cleverness (compilers, parsers).

## Evidence Format
- File:line of longest/most-nested functions + any clever regex/macro.

## Remediation Hints
- Write for the reader, not yourself. Extract and name intermediate steps.
- If it's clever, it needs a comment explaining the "why."
- Max function length you should tolerate: ~50 LOC. Max nesting: 3.

## Origins

Brian Kernighan expressed this concept in *The Elements of Programming Style* (1974; second edition 1978), co-authored with P.J. Plauger. Kernighan, renowned for co-authoring foundational programming texts, emphasized simplicity during the era of resource-constrained computing — a mindset that has aged well even as hardware got cheaper.

## Further Reading

- [The C Programming Language](https://amzn.to/3YLSFYy)
- [The Elements of Programming Style](https://www.amazon.com/Elements-Programming-Style-2nd/dp/0070342075)
- [Code Complete](https://amzn.to/4smkSmE)

## Related Laws

- [KISS (Keep It Simple, Stupid)](../design/kiss.md)
- [Premature Optimization](../planning/premature-optimization.md)
