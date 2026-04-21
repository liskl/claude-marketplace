#!/usr/bin/env python3
"""Repo evolution signals — Lehman's Laws, Gall's Law, Linus's Law, Parkinson's."""
from __future__ import annotations

import datetime as dt
import sys
from collections import Counter, defaultdict
from pathlib import Path

from _common import Signal, ScanResult, emit, is_git_repo, git


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()

    if not is_git_repo(repo):
        result.status = "skipped"
        result.note = "not a git repo"
        emit(result)
        return

    # All commits: "<ct>\t<author>\t<subject>"
    out = git(repo, "log", "--pretty=format:%ct\t%an\t%s", timeout=120)
    if not out:
        result.status = "partial"
        result.note = "no git log output"
        emit(result)
        return

    by_month: Counter[str] = Counter()
    authors: Counter[str] = Counter()
    first_ts = None
    last_ts = None
    subjects: list[str] = []
    for ln in out.splitlines():
        parts = ln.split("\t", 2)
        if len(parts) < 3:
            continue
        ts_str, author, subj = parts
        if not ts_str.isdigit():
            continue
        ts = int(ts_str)
        if first_ts is None or ts < first_ts:
            first_ts = ts
        if last_ts is None or ts > last_ts:
            last_ts = ts
        date = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
        by_month[f"{date.year:04d}-{date.month:02d}"] += 1
        authors[author] += 1
        subjects.append(subj)

    if first_ts is None:
        emit(result)
        return

    age_days = (last_ts - first_ts) // 86400
    total_commits = sum(by_month.values())

    # Lehman's laws: continuing change + declining quality (we proxy the 2nd with accelerating commit
    # count in recent months), and continuing growth. We flag if the repo shows continuous activity.
    months_active = len(by_month)
    if months_active >= 6:
        # Compare last 3 months vs prior 3 months for velocity change.
        sorted_months = sorted(by_month.items())
        recent = sum(c for _, c in sorted_months[-3:])
        prior = sum(c for _, c in sorted_months[-6:-3]) or 1
        velocity_ratio = recent / prior
        if velocity_ratio > 1.5:
            result.signals.append(Signal(
                law_hints=["lehman", "second-system"],
                severity="info",
                summary=f"Commit velocity accelerating ({velocity_ratio:.1f}x vs prior quarter)",
                value=round(velocity_ratio, 2),
            ))
        elif velocity_ratio < 0.5 and total_commits > 20:
            result.signals.append(Signal(
                law_hints=["lehman", "lindy"],
                severity="info",
                summary=f"Commit velocity decaying ({velocity_ratio:.1f}x vs prior quarter)",
                value=round(velocity_ratio, 2),
            ))

    # Gall's Law: did this evolve from simpler beginnings?
    if age_days > 365 and total_commits > 50:
        result.signals.append(Signal(
            law_hints=["gall"],
            severity="info",
            summary=f"Repo has {total_commits} commits over {age_days // 365}y — evolved from smaller over time",
            value={"commits": total_commits, "age_days": age_days},
        ))

    # Linus's Law proxy: merge-commit density + author diversity.
    merge_out = git(repo, "log", "--merges", "--oneline", timeout=60)
    merge_count = len([ln for ln in merge_out.splitlines() if ln.strip()])
    merge_ratio = (merge_count / total_commits) if total_commits else 0
    if len(authors) >= 5 and merge_ratio >= 0.1:
        result.signals.append(Signal(
            law_hints=["linus"],
            severity="info",
            summary=f"{len(authors)} authors, {merge_ratio*100:.0f}% merge commits — review visibility likely active",
            value={"authors": len(authors), "merge_ratio": round(merge_ratio, 2)},
        ))
    elif len(authors) < 3 and total_commits > 30:
        result.signals.append(Signal(
            law_hints=["linus", "bus-factor"],
            severity="watch",
            summary=f"Only {len(authors)} committer(s) — limited review surface",
            value=len(authors),
        ))

    # Parkinson's / Hofstadter's proxy: "estimate" / "estimated" / "should take" in commit messages.
    estimate_hits = sum(
        1 for s in subjects
        if any(tok in s.lower() for tok in ("estimate", "should take", "eta", "deadline"))
    )
    if estimate_hits >= 3:
        result.signals.append(Signal(
            law_hints=["parkinson", "hofstadter"],
            severity="info",
            summary=f"{estimate_hits} commit messages mention estimates/deadlines — possible planning drift",
            value=estimate_hits,
        ))

    # Goodhart's proxy: commit messages mentioning metric chasing.
    goodhart_tokens = ("coverage", "metric", "kpi", "sla target")
    goodhart_hits = sum(
        1 for s in subjects
        if any(tok in s.lower() for tok in goodhart_tokens)
    )
    if goodhart_hits >= 5:
        result.signals.append(Signal(
            law_hints=["goodhart"],
            severity="info",
            summary=f"{goodhart_hits} commits mention metrics/coverage/KPI/SLA — check for metric-gaming",
            value=goodhart_hits,
        ))

    # Second-System Effect: "rewrite", "v2", "reborn", "new-new" hints.
    rewrite_tokens = ("rewrite", "v2", "v3", "reborn", "from scratch", "redesign")
    rewrite_hits = sum(
        1 for s in subjects
        if any(tok in s.lower() for tok in rewrite_tokens)
    )
    if rewrite_hits >= 3:
        result.signals.append(Signal(
            law_hints=["second-system"],
            severity="watch",
            summary=f"{rewrite_hits} commits mention rewrites/v2/redesigns",
            value=rewrite_hits,
        ))

    result.metrics = {
        "total_commits": total_commits,
        "unique_authors": len(authors),
        "age_days": age_days,
        "months_active": months_active,
        "merge_ratio": round(merge_ratio, 3),
    }
    emit(result)


if __name__ == "__main__":
    main()
