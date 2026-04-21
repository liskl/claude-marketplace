#!/usr/bin/env python3
"""Test pyramid shape — signals for Testing Pyramid and Pesticide Paradox."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import (
    Signal, ScanResult, emit, walk_source_files, read_text, rel,
    is_git_repo, git,
)

UNIT_HINTS = ("unit", "spec")
INTEGRATION_HINTS = ("integration", "integ", "api_test", "api-tests")
E2E_HINTS = ("e2e", "end-to-end", "endtoend", "cypress", "playwright", "selenium", "browser")

TEST_FILE = re.compile(r"(^|[._/-])(test|tests|spec|specs)([._/-]|$)", re.IGNORECASE)
STALE_DAYS = 365


def classify(path_str: str) -> str | None:
    lower = path_str.lower().replace("\\", "/")
    if not TEST_FILE.search(lower):
        return None
    for kw in E2E_HINTS:
        if kw in lower:
            return "e2e"
    for kw in INTEGRATION_HINTS:
        if kw in lower:
            return "integration"
    for kw in UNIT_HINTS:
        if kw in lower:
            return "unit"
    return "unit"  # default for anything in a test/ dir with no other hint


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()
    counts = {"unit": 0, "integration": 0, "e2e": 0}
    total_src = 0
    test_files: list[tuple[str, str]] = []  # (rel path, kind)

    for p in walk_source_files(repo):
        r = rel(p, repo)
        kind = classify(r)
        if kind is None:
            total_src += 1
        else:
            counts[kind] += 1
            test_files.append((r, kind))

    total_tests = sum(counts.values())
    test_to_src = (total_tests / total_src) if total_src else 0.0

    if total_tests == 0:
        result.signals.append(Signal(
            law_hints=["testing-pyramid", "murphy", "linus"],
            severity="concern",
            summary="No test files detected",
            value=0,
        ))
    else:
        # Pyramid shape check: unit should dominate.
        unit_pct = counts["unit"] / total_tests * 100
        e2e_pct = counts["e2e"] / total_tests * 100
        if unit_pct < 50 and total_tests >= 5:
            result.signals.append(Signal(
                law_hints=["testing-pyramid"],
                severity="watch",
                summary=f"Inverted pyramid: only {unit_pct:.0f}% unit tests (unit={counts['unit']}, integration={counts['integration']}, e2e={counts['e2e']})",
                value={"unit_pct": round(unit_pct, 1), **counts},
                threshold="unit >= 50%",
            ))
        if e2e_pct > 30 and total_tests >= 5:
            result.signals.append(Signal(
                law_hints=["testing-pyramid"],
                severity="watch",
                summary=f"Top-heavy: {e2e_pct:.0f}% e2e tests",
                value=round(e2e_pct, 1),
                threshold="<= 30%",
            ))
        if test_to_src < 0.2:
            result.signals.append(Signal(
                law_hints=["testing-pyramid", "murphy", "linus"],
                severity="watch",
                summary=f"Low test-to-source ratio ({test_to_src:.2f})",
                value=round(test_to_src, 2),
                threshold=0.2,
            ))

    # Pesticide paradox: tests that haven't changed in a long time.
    if is_git_repo(repo) and test_files:
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc)
        stale = []
        for rel_path, _kind in test_files[:40]:  # sample
            out = git(repo, "log", "-1", "--format=%ct", "--", rel_path, timeout=10)
            ts = out.strip()
            if ts.isdigit():
                age_days = (now - dt.datetime.fromtimestamp(int(ts), dt.timezone.utc)).days
                if age_days >= STALE_DAYS:
                    stale.append((rel_path, age_days))
        if len(stale) >= 3:
            result.signals.append(Signal(
                law_hints=["pesticide-paradox"],
                severity="watch",
                summary=f"{len(stale)} test file(s) unchanged in >{STALE_DAYS} days (sampled)",
                value=len(stale),
                threshold=3,
            ))
            for f, age in stale[:5]:
                result.signals.append(Signal(
                    law_hints=["pesticide-paradox"],
                    severity="info",
                    summary=f"Stale test ({age} days)",
                    file=f,
                    value=age,
                ))

    result.metrics = {
        "unit": counts["unit"],
        "integration": counts["integration"],
        "e2e": counts["e2e"],
        "test_files_total": total_tests,
        "source_files_total": total_src,
        "test_to_source_ratio": round(test_to_src, 3),
    }
    emit(result)


if __name__ == "__main__":
    main()
