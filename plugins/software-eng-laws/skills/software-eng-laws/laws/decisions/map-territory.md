# The Map Is Not the Territory

**Category**: decisions
**Detection**: manual
**Short description**: Models, diagrams, and docs are useful abstractions — but they are not the actual system.

## Overview

![The Map Is Not the Territory](../images/map-is-not-territory.png)

"The map is not the territory" is a mental model from general semantics reminding us that our representations of reality are not reality itself. Software teams constantly produce maps — requirements docs, architecture diagrams, mental models of a codebase — and those maps are essential for planning and reasoning. Trouble starts when we forget they are approximations.

A common failure mode is over-confidence in early designs. Once implementation begins, unexpected issues emerge (latency between modules, a library behaving differently than the docs suggested) that the original assumptions missed. George Box put it best: "All models are wrong, but some are useful."

## Takeaways

- Design docs, UML diagrams, and architecture sketches are abstractions. Don't confuse the blueprint with the running software.
- During implementation, things will surface that the design didn't account for. Be ready to revise as real behavior pushes back on your assumptions.
- Models and designs are useful guides, but keep challenging them when the system's actual behavior disagrees.

## Examples

A microservice design has Service A talking to B and C via Kafka, with the diagram assuming "reliable networks" and "minimal latency." Cloud infrastructure reality disagrees, and the team retrofits retry logic and schema validation after first contact with production.

A performance estimate predicted a database handling 10,000 queries per second based on spec sheets. Production delivered 5,000 qps because the model ignored query optimization edge cases and real data distribution.

## Signals
- Architecture diagrams that haven't been updated in the repo in >1 year while code kept changing.
- Reliance on comments/docstrings to describe behavior that the code contradicts.
- Monitoring dashboards that disagree with log reality.

## Scoring Rubric
- ⚪ **Manual**: reflect on the prompts below.

## Reflection Prompts
- When was your architecture diagram last verified against the running system?
- Do your docs describe the system as it is, or as it was meant to be?
- When the map and the territory disagree, which do you trust?

## Remediation Hints
- Docs-as-code: generate what you can from the source.
- Verify models empirically (logs, traces) before making decisions from them.
- Treat documentation as a lagging indicator, not ground truth.

## Origins

Alfred Korzybski, a Polish-American scholar, popularized the phrase in *Science and Sanity* (1933), arguing that language and knowledge systems mislead us into treating conceptual constructs as faithful representations of reality. The idea was later picked up by Gregory Bateson and widely adopted in systems thinking, general semantics, and cognitive science.

## Further Reading

- [Science and Sanity (Korzybski)](https://www.holybooks.com/wp-content/uploads/Science-and-Sanity.pdf)
- [Steps to an Ecology of Mind (Bateson)](https://www.press.uchicago.edu/ucp/books/book/chicago/S/bo3620295.html)
- [Map-territory relation (Wikipedia)](https://en.wikipedia.org/wiki/Map%E2%80%93territory_relation)

## Related Laws

- [Goodhart's Law](../planning/goodhart.md)
- [Gall's Law](../architecture/gall.md)
- [Law of Leaky Abstractions](../architecture/leaky-abstractions.md)
