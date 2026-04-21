#!/usr/bin/env python3
"""TODO/FIXME/HACK/XXX counts — signals for Broken Windows, Technical Debt, Ninety-Ninety Rule."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from _common import Signal, ScanResult, emit, walk_source_files, read_text, rel, is_git_repo, git

PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG|KLUDGE|DEPRECATED)\b[:\s(]", re.IGNORECASE)
HIGH_DENSITY_PER_KLOC = 5
VERY_OLD_DAYS = 365


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()
    tag_counts: Counter[str] = Counter()
    found: list[tuple[str, int, str, str]] = []  # file, line, tag, text
    total_loc = 0

    for p in walk_source_files(repo):
        text = read_text(p)
        if not text:
            continue
        for i, ln in enumerate(text.splitlines(), 1):
            total_loc += 1 if ln.strip() else 0
            m = PATTERN.search(ln)
            if not m:
                continue
            tag = m.group(1).upper()
            tag_counts[tag] += 1
            found.append((rel(p, repo), i, tag, ln.strip()[:160]))

    # Density check
    density = (len(found) / total_loc * 1000) if total_loc else 0

    if density >= HIGH_DENSITY_PER_KLOC:
        result.signals.append(Signal(
            law_hints=["broken-windows", "tech-debt", "ninety-ninety"],
            severity="concern" if density >= HIGH_DENSITY_PER_KLOC * 2 else "watch",
            summary=f"High TODO/FIXME density ({density:.1f} per kLOC, {len(found)} total)",
            value=round(density, 2),
            threshold=HIGH_DENSITY_PER_KLOC,
        ))

    # Report up to first 20 hits individually so Claude can cite them.
    for rel_path, line, tag, snippet in found[:20]:
        sev = "concern" if tag in {"FIXME", "BUG", "HACK"} else "watch"
        result.signals.append(Signal(
            law_hints=["broken-windows", "tech-debt"],
            severity=sev,
            summary=f"{tag}: {snippet}",
            file=rel_path,
            line=line,
            value=tag,
        ))

    # Git blame age check — sample up to 10 TODO hits
    if is_git_repo(repo) and found:
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc)
        old = 0
        for rel_path, line, _tag, _snip in found[:30]:
            out = git(repo, "blame", "-L", f"{line},{line}", "--porcelain", "--", rel_path, timeout=10)
            for bl in out.splitlines():
                if bl.startswith("author-time "):
                    try:
                        ts = int(bl.split()[1])
                        age_days = (now - dt.datetime.fromtimestamp(ts, dt.timezone.utc)).days
                        if age_days >= VERY_OLD_DAYS:
                            old += 1
                    except (ValueError, IndexError):
                        pass
                    break
        if old >= 3:
            result.signals.append(Signal(
                law_hints=["broken-windows", "tech-debt", "lindy"],
                severity="watch",
                summary=f"{old} TODO/FIXME older than {VERY_OLD_DAYS} days (sampled)",
                value=old,
                threshold=3,
            ))

    result.metrics = {
        "total_tags": len(found),
        "per_kloc": round(density, 2),
        "tag_counts": dict(tag_counts),
    }
    emit(result)


if __name__ == "__main__":
    main()
