#!/usr/bin/env python3
"""Block-level duplication detection — signals for DRY.

Normalizes code to remove whitespace/identifiers noise, hashes sliding windows
of N non-blank lines, and reports blocks that repeat across files.
"""
from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

from _common import Signal, ScanResult, emit, walk_source_files, read_text, rel

WINDOW = 8        # non-blank lines per block
MIN_DUPES = 2     # block must appear at least this many times to report
MAX_REPORTED = 20

NORMALIZE = re.compile(r"\s+")
STRIP_COMMENTS = re.compile(r"(#|//).*$", re.MULTILINE)


def normalize(line: str) -> str:
    # Strip trailing comments and collapse whitespace.
    line = STRIP_COMMENTS.sub("", line)
    return NORMALIZE.sub(" ", line).strip()


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()

    blocks: dict[str, list[tuple[str, int]]] = defaultdict(list)
    total_windows = 0

    for p in walk_source_files(repo):
        text = read_text(p)
        if not text:
            continue
        raw_lines = text.splitlines()
        norm: list[tuple[int, str]] = []  # (1-indexed line, normalized)
        for idx, ln in enumerate(raw_lines, 1):
            n = normalize(ln)
            if n and len(n) > 4:  # drop empty + trivial lines
                norm.append((idx, n))

        if len(norm) < WINDOW:
            continue

        for i in range(len(norm) - WINDOW + 1):
            window = norm[i:i + WINDOW]
            key = hashlib.sha1(
                "\n".join(n for _, n in window).encode("utf-8")
            ).hexdigest()
            blocks[key].append((rel(p, repo), window[0][0]))
            total_windows += 1

    duplicated = 0
    reported = 0
    for key, locs in blocks.items():
        if len(locs) < MIN_DUPES:
            continue
        duplicated += len(locs)
        if reported >= MAX_REPORTED:
            continue
        files = {f for f, _ in locs}
        severity = "concern" if len(locs) >= 4 or len(files) >= 3 else "watch"
        first = locs[0]
        result.signals.append(Signal(
            law_hints=["dry", "broken-windows"],
            severity=severity,
            summary=(
                f"{WINDOW}-line block duplicated {len(locs)}x across {len(files)} "
                f"file(s) (also at: {', '.join(f'{f}:{l}' for f, l in locs[1:4])}"
                f"{'...' if len(locs) > 4 else ''})"
            ),
            file=first[0],
            line=first[1],
            value=len(locs),
            threshold=MIN_DUPES,
        ))
        reported += 1

    result.metrics = {
        "total_windows": total_windows,
        "duplicate_block_count": duplicated,
        "duplication_ratio": round(duplicated / total_windows, 3) if total_windows else 0.0,
        "window_size": WINDOW,
    }
    emit(result)


if __name__ == "__main__":
    main()
