#!/usr/bin/env python3
"""Software Engineering Laws audit orchestrator.

Runs every scan_*.py in this directory, merges their JSON output, and writes
a findings.json conforming to ../schema/finding.schema.json.

Usage:
    python3 run_audit.py <repo> [--out PATH] [--languages-only]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from _common import is_git_repo, language_summary

SCANS = [
    "complexity",
    "duplication",
    "todos",
    "test_ratio",
    "bus_factor",
    "hotspots",
    "demeter",
    "public_api",
    "git_evolution",
    "patterns",
]


def run_scan(name: str, repo: Path, scripts_dir: Path) -> tuple[dict, str | None]:
    script = scripts_dir / f"scan_{name}.py"
    if not script.exists():
        return {"status": "skipped", "note": "script missing", "signals": []}, f"{name}: script missing"
    try:
        r = subprocess.run(
            [sys.executable, str(script), str(repo)],
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode != 0:
            return (
                {"status": "error", "note": (r.stderr or "nonzero exit")[:500], "signals": []},
                f"{name}: exit {r.returncode}",
            )
        try:
            return json.loads(r.stdout or "{}"), None
        except json.JSONDecodeError as e:
            return (
                {"status": "error", "note": f"invalid json: {e}", "signals": []},
                f"{name}: invalid json",
            )
    except subprocess.TimeoutExpired:
        return (
            {"status": "error", "note": "timeout", "signals": []},
            f"{name}: timeout",
        )
    except Exception as e:  # noqa: BLE001 — defensive barrier in orchestrator
        return (
            {"status": "error", "note": str(e)[:500], "signals": []},
            f"{name}: {e}",
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=Path)
    ap.add_argument("--out", type=Path, default=Path("/tmp/laws-findings.json"))
    ap.add_argument("--languages-only", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"error: {repo} is not a directory", file=sys.stderr)
        return 2

    langs = language_summary(repo)

    if args.languages_only:
        print(json.dumps({"repo": str(repo), "languages": langs}, indent=2))
        return 0

    scripts_dir = Path(__file__).parent
    git_ok = is_git_repo(repo)
    warnings: list[str] = []
    if not git_ok:
        warnings.append("not a git repo — history-based scans will be skipped")

    file_count = sum(v["files"] for v in langs.values())
    if file_count < 10:
        warnings.append(f"only {file_count} source files detected — signal density will be low")

    scans_out: dict[str, dict] = {}
    for name in SCANS:
        data, warn = run_scan(name, repo, scripts_dir)
        scans_out[name] = data
        if warn:
            warnings.append(warn)

    findings = {
        "repo": str(repo),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "is_git_repo": git_ok,
        "file_count": file_count,
        "languages": langs,
        "scans": scans_out,
        "warnings": warnings,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(findings, indent=2, default=str))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
