#!/usr/bin/env python3
"""Chained method-call depth — signal for Law of Demeter."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import Signal, ScanResult, emit, walk_source_files, read_text, rel

# Matches chains like `a.b().c().d()` or `a.b.c.d.e` — 4+ dots between calls.
# Intentionally simple; false positives are OK for a "watch" signal.
CHAIN = re.compile(r"[\w\)\]]\.[\w]+\s*\([^()]*\)\s*\.[\w]+\s*\([^()]*\)\s*\.[\w]+\s*\(")
DEEP_CHAIN = re.compile(
    r"[\w\)\]]"
    r"\.[\w]+\s*\([^()]*\)\s*"
    r"\.[\w]+\s*\([^()]*\)\s*"
    r"\.[\w]+\s*\([^()]*\)\s*"
    r"\.[\w]+\s*\("
)


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()
    total_chains = 0
    deep_chains = 0
    reported = 0

    for p in walk_source_files(repo):
        text = read_text(p)
        if not text:
            continue
        for i, ln in enumerate(text.splitlines(), 1):
            if DEEP_CHAIN.search(ln):
                deep_chains += 1
                total_chains += 1
                if reported < 20:
                    result.signals.append(Signal(
                        law_hints=["demeter"],
                        severity="watch",
                        summary=f"4+ chained calls: {ln.strip()[:140]}",
                        file=rel(p, repo),
                        line=i,
                        value=4,
                    ))
                    reported += 1
            elif CHAIN.search(ln):
                total_chains += 1

    result.metrics = {
        "total_chain_3plus": total_chains,
        "deep_chain_4plus": deep_chains,
    }
    if deep_chains >= 10:
        result.signals.append(Signal(
            law_hints=["demeter"],
            severity="watch",
            summary=f"{deep_chains} deep call chains (4+) across the repo",
            value=deep_chains,
            threshold=10,
        ))
    emit(result)


if __name__ == "__main__":
    main()
