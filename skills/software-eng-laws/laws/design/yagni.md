# YAGNI (You Aren't Gonna Need It)

**Category**: design
**Detection**: hybrid
**Short description**: Don't add functionality until it is necessary.

## Overview

![YAGNI](../images/yagni.png)

YAGNI captures a core philosophy of agile development: don't write code for features that haven't been requested or aren't immediately needed. If you're implementing Module A and think "in the future we might need Module B to do X, so I'll code some hooks for that now," YAGNI advises against it because that future feature may never come or may change drastically.

This principle directly fights over-engineering. To apply YAGNI successfully, teams rely on confidence in refactoring. You defer a feature only if you trust you can add it later at low cost. Agile methods provide that safety net via good test coverage, refactoring tools, and continuous integration. YAGNI pushes the problem of complexity to when it's actually needed.

## Takeaways

- YAGNI reminds developers to focus on current tasks rather than implementing features that aren't needed now.
- Anticipating future needs often leads to over-engineering, adding complexity and maintenance issues.
- YAGNI encourages iterative development with minimal solutions that are refined or extended when needed.

## Examples

You're building a feature with specific behavior. You think "maybe in the future someone will want to toggle this on/off, so I'll add a configuration flag now." YAGNI challenges that. Unless there's a current requirement for configurability, implement only expected behavior, nothing more.

You're working on a library function that currently does one thing. You realize it might be useful more generally, so you consider adding parameters or abstraction tiers. YAGNI says implement it for the original task. Your app needs JSON export? Implement simple JSON, not a full serialization library supporting XML, YAML, etc.

## Signals
- Unused public methods, parameters, or classes flagged by static analysis.
- Config flags, plugin interfaces, or extensibility hooks with no call sites.
- Dead "future-proofing" abstractions (single-impl interfaces, factories with one product).
- Commit messages like "in case we need it" or "for future flexibility."

## Scoring Rubric
- 🟢 **Pass**: no unused public API, no speculative abstractions visible.
- 🟡 **Watch**: a few unused methods or single-implementation interfaces lingering.
- 🔴 **Concern**: widespread extensibility scaffolding with no consumers; config surface far exceeds usage.
- ⚪ **Manual**: inherent plugin/framework designs where extensibility IS the product.

## Evidence Format
- Cite unused-symbol counts from a linter, plus one or two file:line examples of speculative abstractions.

## Remediation Hints
- Delete unused code. Git remembers it if you change your mind.
- Wait for the third concrete use case before extracting an abstraction (Rule of Three).
- Replace speculative config flags with hardcoded defaults until you have a real second caller.

## Origins

YAGNI was part of the Extreme Programming (XP) paradigm in the late 1990s. It was promoted by Ron Jeffries, one of XP's founders, who wrote: "Always implement things when you actually need them, not when you just foresee that you need them." The slogan was adopted in XP literature, such as *Extreme Programming Installed* (2001).

## Further Reading

- [YAGNI on Martin Fowler's website](https://martinfowler.com/bliki/Yagni.html)
- [Extreme Programming Installed](https://amzn.to/4siycbq)
- [You Aren't Gonna Need It on C2 Wiki](http://wiki.c2.com/?YouArentGonnaNeedIt)

## Related Laws

- [KISS (Keep It Simple, Stupid)](../design/kiss.md)
- [DRY (Don't Repeat Yourself)](../design/dry.md)
- [Premature Optimization](../planning/premature-optimization.md)
