"""Shared helpers for scan_*.py scripts.

Python stdlib only. No external deps.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Iterator

# File-extension -> language name. Kept small and practical.
LANG_BY_EXT: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
}

# Directories we always skip.
SKIP_DIRS: set[str] = {
    ".git", ".hg", ".svn",
    "node_modules", "vendor", "target", "build", "dist",
    "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".next", ".nuxt", ".cache", ".idea", ".vscode",
    "bower_components", "jspm_packages",
}

MAX_FILE_BYTES = 2 * 1024 * 1024  # skip files > 2MB


@dataclass
class Signal:
    law_hints: list[str]
    severity: str  # info | watch | concern
    summary: str
    file: str | None = None
    line: int | None = None
    value: object = None
    threshold: object = None

    def to_dict(self) -> dict:
        d = {
            "law_hints": self.law_hints,
            "severity": self.severity,
            "summary": self.summary,
        }
        if self.file is not None:
            d["file"] = self.file
        if self.line is not None:
            d["line"] = self.line
        if self.value is not None:
            d["value"] = self.value
        if self.threshold is not None:
            d["threshold"] = self.threshold
        return d


@dataclass
class ScanResult:
    status: str = "ok"  # ok | partial | skipped | error
    note: str = ""
    signals: list[Signal] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        out = {
            "status": self.status,
            "signals": [s.to_dict() for s in self.signals],
        }
        if self.note:
            out["note"] = self.note
        if self.metrics:
            out["metrics"] = self.metrics
        return out


def walk_source_files(repo: Path) -> Iterator[Path]:
    """Yield source file paths, skipping junk dirs and huge files."""
    for root, dirs, files in os.walk(repo):
        # Prune in place.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.startswith("."):
                continue
            p = Path(root) / name
            ext = p.suffix.lower()
            if ext not in LANG_BY_EXT:
                continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield p


def language_of(p: Path) -> str | None:
    return LANG_BY_EXT.get(p.suffix.lower())


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def rel(p: Path, repo: Path) -> str:
    try:
        return str(p.relative_to(repo))
    except ValueError:
        return str(p)


def count_loc(text: str) -> int:
    """Non-blank lines."""
    return sum(1 for ln in text.splitlines() if ln.strip())


def is_git_repo(repo: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=10,
        )
        return r.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def git(repo: Path, *args: str, timeout: int = 60) -> str:
    """Run git and return stdout. Empty string on failure."""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            return ""
        return r.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def language_summary(repo: Path) -> dict[str, dict]:
    """{lang: {files: int, loc: int}}"""
    out: dict[str, dict] = {}
    for p in walk_source_files(repo):
        lang = language_of(p)
        if not lang:
            continue
        entry = out.setdefault(lang, {"files": 0, "loc": 0})
        entry["files"] += 1
        entry["loc"] += count_loc(read_text(p))
    return out


def emit(result: ScanResult) -> None:
    """Print JSON to stdout — run_audit.py captures it."""
    print(json.dumps(result.to_dict(), default=str))
