#!/usr/bin/env python3
"""Per-file author concentration — signal for Bus Factor and Conway's Law."""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

from _common import (
    Signal, ScanResult, emit, walk_source_files, rel,
    is_git_repo, git,
)

DOMINATION_THRESHOLD = 0.8  # one author wrote >=80% of lines
MAX_FILES_SAMPLED = 200


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()

    if not is_git_repo(repo):
        result.status = "skipped"
        result.note = "not a git repo"
        emit(result)
        return

    files = [rel(p, repo) for p in walk_source_files(repo)]
    files = files[:MAX_FILES_SAMPLED]

    dominated: list[tuple[str, str, float]] = []
    project_authors: Counter[str] = Counter()
    per_dir_authors: dict[str, Counter[str]] = defaultdict(Counter)

    for f in files:
        out = git(repo, "blame", "--line-porcelain", "--", f, timeout=30)
        if not out:
            continue
        authors: Counter[str] = Counter()
        for ln in out.splitlines():
            if ln.startswith("author "):
                author = ln[7:].strip()
                if author and author != "Not Committed Yet":
                    authors[author] += 1
        total = sum(authors.values())
        if total < 20:  # too small to matter
            continue
        top_author, top_lines = authors.most_common(1)[0]
        share = top_lines / total
        project_authors[top_author] += top_lines
        top_dir = f.split("/", 1)[0] if "/" in f else "."
        per_dir_authors[top_dir][top_author] += top_lines
        if share >= DOMINATION_THRESHOLD:
            dominated.append((f, top_author, share))

    # Report worst offenders.
    dominated.sort(key=lambda x: -x[2])
    for f, author, share in dominated[:15]:
        result.signals.append(Signal(
            law_hints=["bus-factor", "conway"],
            severity="watch" if share < 0.95 else "concern",
            summary=f"{share*100:.0f}% owned by '{author}'",
            file=f,
            value=round(share, 3),
            threshold=DOMINATION_THRESHOLD,
        ))

    # Repo-wide bus factor: minimum authors whose combined lines cover 50%.
    if project_authors:
        total = sum(project_authors.values())
        covered = 0
        bf = 0
        for _author, lines in project_authors.most_common():
            covered += lines
            bf += 1
            if covered >= total * 0.5:
                break
        result.signals.append(Signal(
            law_hints=["bus-factor"],
            severity="concern" if bf <= 1 else ("watch" if bf <= 2 else "info"),
            summary=f"Repo-wide bus factor ≈ {bf} (authors needed to cover 50% of code)",
            value=bf,
            threshold=3,
        ))
        result.metrics["bus_factor"] = bf

    # Conway's hint: directories with single dominant author.
    single_owner_dirs = 0
    for d, authors in per_dir_authors.items():
        if sum(authors.values()) < 50:
            continue
        top_author, top_lines = authors.most_common(1)[0]
        if top_lines / sum(authors.values()) >= 0.9:
            single_owner_dirs += 1
    if single_owner_dirs >= 3:
        result.signals.append(Signal(
            law_hints=["conway"],
            severity="info",
            summary=f"{single_owner_dirs} top-level dirs are >90% owned by one author (module-to-person alignment)",
            value=single_owner_dirs,
        ))

    result.metrics["files_sampled"] = len(files)
    result.metrics["dominated_files"] = len(dominated)
    result.metrics["single_owner_dirs"] = single_owner_dirs
    emit(result)


if __name__ == "__main__":
    main()
