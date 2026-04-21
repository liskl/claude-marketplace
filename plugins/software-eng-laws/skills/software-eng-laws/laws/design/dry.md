# DRY (Don't Repeat Yourself)

**Category**: design
**Detection**: code
**Short description**: Every piece of knowledge should have a single, authoritative representation.

## Overview

![DRY Principle](../images/dry.png)

The DRY principle says each fact or piece of logic in a system should be expressed once and only once. Repeated code across modules creates hidden maintenance cost: when a business rule changes, every copy must be updated, and any one that gets missed becomes a subtle bug. Following DRY means abstracting common code into a function, class, or shared module, and consolidating configuration into a single source of truth. The principle extends beyond code to database schemas, tests, and documentation.

Importantly, DRY targets duplicated *intent*, not merely similar-looking code. Two pieces of code may look identical but represent different concepts that will diverge over time. Merging them prematurely creates coupling that is painful to undo.

## Takeaways

- The principle targets duplication of *knowledge* in code. Identical logic in multiple places is a signal to refactor toward a single source of truth.
- When requirements shift, updating logic in one place prevents the "I missed a copy" class of bug.
- Apply DRY judiciously — distinguish true knowledge duplication from coincidental similarity to avoid over-complicated, prematurely-coupled abstractions.

## Examples

Storing a database connection URL in one configuration variable instead of hard-coding it in five source files gives you a single place to update when the host changes. A shared `formatDate()` utility consolidates date formatting. A shared authentication library prevents duplicating security logic across multiple apps — the place you absolutely do not want to be fixing a bug five times.

The anti-pattern: two services with similar-looking invoice calculation logic that actually implement different business rules for different customer tiers. Merging them "to be DRY" creates a tangled helper that branches on every difference and slows all future changes.

## Signals
- `duplication.duplication_ratio`: fraction of source windows that duplicate elsewhere.
- `duplication.signals`: specific duplicated blocks with file:line citations.
- Watch for "knowledge" duplication, not just syntactic: same business rule in multiple places is worse than copy-pasted utility helpers.

## Scoring Rubric
- 🟢 **Pass**: duplication_ratio < 0.01, no 4x-repeated blocks.
- 🟡 **Watch**: duplication_ratio 0.01-0.05, a handful of 2-3x repeats.
- 🔴 **Concern**: duplication_ratio > 0.05 OR any block repeated ≥4x across ≥3 files.
- ⚪ **Manual**: tiny repo.

## Evidence Format
- Top repeated blocks with all file:line locations.

## Remediation Hints
- Extract repeated business rules into a single source of truth (module, function, or constant).
- Not all duplication is wrong — sometimes "Rule of Three" applies (wait until the third occurrence).
- Prefer duplication of low-stakes utility code over premature abstraction with the wrong shape.

## Origins

Andy Hunt and Dave Thomas coined "DRY" in 1999 in *The Pragmatic Programmer*, defining it as: "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system." Earlier structured programming traditions and the Unix philosophy had promoted similar ideas, but *The Pragmatic Programmer* crystallized the name that stuck.

## Further Reading

- [The Pragmatic Programmer, 20th Anniversary Edition](https://amzn.to/4piJutH)
- [Don't Repeat Yourself - Wikipedia](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [Code Complete](https://amzn.to/3N57T8t)

## Related Laws

- [SOLID Principles](./solid.md)
- [Law of Demeter](./demeter.md)
