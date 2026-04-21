# KISS (Keep It Simple, Stupid)

**Category**: design
**Detection**: code
**Short description**: Most systems work best when they are kept simple.

## Overview

![KISS Principle](../images/kiss.png)

The KISS principle says simplicity should be an explicit design goal. Software has to be understood by humans, and straightforward designs are significantly easier to maintain. New team members ramp up faster, bugs are easier to find, and changes cause fewer unintended consequences. KISS discourages "clever" code that tries to do several things at once, and pushes back against designs built around speculative future needs that add complexity today.

## Takeaways

- KISS prioritizes avoiding complexity in designs. Prefer the simple solution that meets current requirements over the elaborate one that might fit hypothetical future ones.
- Code that is simple is faster to understand and debug — both for teammates and for your own future self.
- Solutions should remain as uncomplicated as possible, and no more complicated than necessary.

## Examples

A web app that generates reports benefits from KISS by using straightforward scripts or existing libraries to query a database and write CSV, rather than building an elaborate plugin architecture for report types that no one has asked for. A file parsing routine is better written as sequential logic — open, read lines, split fields, handle errors — than as a generic parser-combinator framework built without real requirements driving it.

The judgment call: "simple" does not mean "short" or "clever." A terse one-liner packed with chained operators is not simple; a 20-line function with named intermediate variables that reads like prose is.

## Signals
- `complexity.long_function_ratio`: fraction of functions above the comprehension threshold.
- `complexity.total_source_loc` relative to file count: large files cluster.
- Deep nesting signals in `complexity`.
- Many layers of abstraction that each do little (factory-of-factory anti-patterns).

## Scoring Rubric
- 🟢 **Pass**: long_function_ratio < 0.05, no files > 600 LOC, shallow nesting.
- 🟡 **Watch**: long_function_ratio 0.05–0.15, a few large files.
- 🔴 **Concern**: long_function_ratio > 0.15, multiple 1500+ LOC files, widespread deep nesting.
- ⚪ **Manual**: complexity is inherent to the domain (compilers, OS kernels).

## Evidence Format
- Cite top 3 longest/deepest functions with LOC.

## Remediation Hints
- Break functions > 50 LOC into smaller named steps.
- Flatten nesting > 3 levels with early returns.
- "Simple" means "easy to read," not "short" — don't mistake terseness for simplicity.

## Origins

The phrase originated in the U.S. military and is commonly credited to Kelly Johnson at Lockheed's Skunk Works during the 1960s. Johnson tasked engineers with designing aircraft that average mechanics could maintain using basic field tools. In software, programmers like Edsger Dijkstra and C.A.R. Hoare championed the related fight against unnecessary complexity throughout the history of the field.

## Further Reading

- [A Philosophy of Software Design](https://amzn.to/3N1uL0f)
- [KISS Principle - Wikipedia](https://en.wikipedia.org/wiki/KISS_principle)
- [Code Complete](https://amzn.to/3N57T8t)

## Related Laws

- [YAGNI (You Aren't Gonna Need It)](./yagni.md)
- [Principle of Least Astonishment](./least-astonishment.md)
- [Gall's Law](../architecture/gall.md)
