# Gall's Law

**Category**: architecture
**Detection**: git-history
**Short description**: A complex system that works is invariably found to have evolved from a simple system that worked.

## Overview

![Gall's Law](../images/galls-law.png)

John Gall observed that successful complex systems start as successful simple systems. Rather than attempting to build intricate architectures from scratch, the principle advocates starting with a simple, functional design and expanding it gradually through real-world testing. This approach allows developers to validate assumptions early and adapt the system incrementally, ensuring each addition maintains functionality.

Large systems typically develop organically; fully designed-from-scratch complex systems usually fail due to unforeseeable interactions. Systems that evolve tend to handle complexity better because they're tested and refined at each stage.

## Takeaways

- Begin with a simple version that works, then iterate and add complexity on a foundation you can actually experiment against.
- Large systems typically develop organically; fully designed-from-scratch complex systems usually fail due to unforeseeable interactions.
- Embrace the MVP approach with a simple working core that grows incrementally rather than attempting a big-bang development strategy.
- Systems that evolve tend to handle complexity better because they're tested and refined at each stage.

## Examples

**Facebook**: Started as a basic user profile system for Harvard students, then expanded gradually. A fully-formed "social graph platform" attempted in 2004 would likely have failed.

**Microservices**: Industry guidance (including Martin Fowler's "MonolithFirst") recommends starting with a monolith before splitting into separate services as the system matures.

## Signals
- `git_evolution` age + commit count: long-lived repos with continuous commits suggest evolution.
- Early commits adding small foundational modules, later commits layering features on top.
- Absence of "initial commit" with thousands of files (which would suggest a cold-start rewrite).

## Scoring Rubric
- 🟢 **Pass**: incremental history, years old, steady churn.
- 🟡 **Watch**: repo < 6 months old but already large — might be a transplant from elsewhere.
- 🔴 **Concern**: repo began with a huge initial commit AND is now complex AND shows stagnation (see Second-System Effect).
- ⚪ **Manual**: not a git repo or too new to judge.

## Evidence Format
- Cite `git_evolution.age_days`, `total_commits`, and first commit stat.

## Remediation Hints
- When designing, start with the smallest thing that could work. Grow it.
- Resist the urge to design "the full thing" up front; design for one user, one flow.
- If the system is already complex, add incrementally — don't rewrite.

## Origins

John Gall, an American pediatrician and systems theorist, published *Systemantics: How Systems Work and Especially How They Fail* in 1975 after 30 rejections. The third edition (2002) was retitled *The Systems Bible*. His observation drew from watching complex bureaucracies and engineered systems fail when designed top-down.

## Further Reading

- [The Systems Bible (Gall)](https://amzn.to/4svZT0K)
- [The Mythical Man-Month (Brooks)](https://amzn.to/4b4GU72)
- [MonolithFirst (Martin Fowler)](https://martinfowler.com/bliki/MonolithFirst.html)
- [Thinking in Systems (Meadows)](https://amzn.to/4qgVSvH)

## Related Laws

- [Conway's Law](../teams/conway.md)
- [Brooks's Law](../teams/brooks.md)
- [The Law of Leaky Abstractions](./leaky-abstractions.md)
- [Hofstadter's Law](../planning/hofstadter.md)
