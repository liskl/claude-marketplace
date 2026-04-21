#!/usr/bin/env python3
"""Churn × size hotspots — signals for Pareto Principle and Lindy Effect."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from _common import (
    Signal, ScanResult, emit, walk_source_files, read_text, rel,
    count_loc, is_git_repo, git,
)


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()

    if not is_git_repo(repo):
        result.status = "skipped"
        result.note = "not a git repo"
        emit(result)
        return

    # Commit count per file over the full history.
    out = git(repo, "log", "--name-only", "--pretty=format:", "--", ".", timeout=120)
    churn: Counter[str] = Counter()
    for ln in out.splitlines():
        ln = ln.strip()
        if ln:
            churn[ln] += 1

    # Limit to current source files.
    source_set = {rel(p, repo) for p in walk_source_files(repo)}
    source_churn = {f: c for f, c in churn.items() if f in source_set}

    if not source_churn:
        result.status = "partial"
        result.note = "no commit data for source files"
        emit(result)
        return

    total_commits = sum(source_churn.values())
    total_files = len(source_set)

    # Pareto: how many files account for 80% of churn?
    sorted_churn = sorted(source_churn.values(), reverse=True)
    cum = 0
    n_for_80 = 0
    for c in sorted_churn:
        cum += c
        n_for_80 += 1
        if cum >= total_commits * 0.8:
            break

    pareto_pct = (n_for_80 / total_files * 100) if total_files else 0
    result.signals.append(Signal(
        law_hints=["pareto"],
        severity="info",
        summary=f"{n_for_80}/{total_files} files ({pareto_pct:.1f}%) account for 80% of commits",
        value={"files_for_80pct": n_for_80, "total_files": total_files},
    ))

    # Top hotspots: churn × LOC.
    hotspots: list[tuple[str, int, int, int]] = []
    for f, c in source_churn.items():
        p = repo / f
        if not p.exists():
            continue
        loc = count_loc(read_text(p))
        hotspots.append((f, c, loc, c * loc))
    hotspots.sort(key=lambda x: -x[3])

    for f, c, loc, score in hotspots[:10]:
        result.signals.append(Signal(
            law_hints=["pareto", "tech-debt", "broken-windows"],
            severity="watch" if score > 5000 else "info",
            summary=f"Hotspot: {c} commits × {loc} LOC",
            file=f,
            value={"commits": c, "loc": loc, "score": score},
        ))

    # Lindy: files older than 2 years AND still stable (low recent churn).
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    two_years_ago = int((now - dt.timedelta(days=730)).timestamp())
    stable_ancients = 0
    for f in list(source_set)[:100]:
        out = git(repo, "log", "--format=%ct", "--", f, timeout=10)
        timestamps = [int(t) for t in out.split() if t.isdigit()]
        if len(timestamps) < 3:
            continue
        first = min(timestamps)
        last = max(timestamps)
        if first < two_years_ago and last < two_years_ago + 180 * 86400:
            stable_ancients += 1
    if stable_ancients >= 5:
        result.signals.append(Signal(
            law_hints=["lindy"],
            severity="info",
            summary=f"{stable_ancients} files (sampled) are >2yr old AND stable — Lindy-positive candidates",
            value=stable_ancients,
        ))

    result.metrics = {
        "total_commits": total_commits,
        "total_source_files": total_files,
        "files_for_80pct_churn": n_for_80,
        "pareto_concentration_pct": round(pareto_pct, 1),
    }
    emit(result)


if __name__ == "__main__":
    main()
