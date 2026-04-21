#!/usr/bin/env python3
"""Public API surface — signal for Hyrum's Law and Leaky Abstractions."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from _common import (
    Signal, ScanResult, emit, walk_source_files, read_text, rel, language_of,
)

PY_TOPLEVEL_DEF = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][\w]*)", re.MULTILINE)
PY_TOPLEVEL_CLASS = re.compile(r"^class\s+([A-Za-z_][\w]*)", re.MULTILINE)
PY_ALL = re.compile(r"^__all__\s*=\s*\[([^\]]*)\]", re.MULTILINE | re.DOTALL)
JS_EXPORT = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|type|interface|enum)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
GO_PUBLIC = re.compile(r"^func(?:\s+\([^)]*\))?\s+([A-Z]\w*)|^type\s+([A-Z]\w*)", re.MULTILINE)
RUST_PUB = re.compile(r"^\s*pub(?:\([^)]+\))?\s+(?:fn|struct|enum|trait|type|mod|const|static)\s+([A-Za-z_]\w*)", re.MULTILINE)
JAVA_PUBLIC = re.compile(r"^\s*public\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?(?:class|interface|enum|\S+)\s+([A-Z]\w*)", re.MULTILINE)


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()
    per_lang: Counter[str] = Counter()
    per_file_counts: list[tuple[str, int]] = []
    total = 0

    for p in walk_source_files(repo):
        lang = language_of(p)
        text = read_text(p)
        if not text:
            continue
        count = 0
        if lang == "Python":
            m_all = PY_ALL.search(text)
            if m_all:
                items = re.findall(r"['\"]([^'\"]+)['\"]", m_all.group(1))
                count = len(items)
            else:
                # Non-underscore top-level defs/classes approximate the public API.
                for rgx in (PY_TOPLEVEL_DEF, PY_TOPLEVEL_CLASS):
                    for name in rgx.findall(text):
                        if not name.startswith("_"):
                            count += 1
        elif lang in ("JavaScript", "TypeScript"):
            count = len(JS_EXPORT.findall(text))
        elif lang == "Go":
            count = sum(1 for m in GO_PUBLIC.finditer(text) if any(m.groups()))
        elif lang == "Rust":
            count = len(RUST_PUB.findall(text))
        elif lang == "Java":
            count = len(JAVA_PUBLIC.findall(text))
        else:
            continue

        if count > 0:
            per_lang[lang] += count
            per_file_counts.append((rel(p, repo), count))
            total += count

    per_file_counts.sort(key=lambda x: -x[1])

    # Top files with a big public surface.
    for f, n in per_file_counts[:10]:
        if n >= 20:
            result.signals.append(Signal(
                law_hints=["hyrum", "leaky-abstractions", "solid"],
                severity="watch" if n < 40 else "concern",
                summary=f"Large public surface ({n} exports)",
                file=f,
                value=n,
                threshold=20,
            ))

    # Aggregate signal.
    if total >= 500:
        result.signals.append(Signal(
            law_hints=["hyrum"],
            severity="info",
            summary=f"Repo-wide public surface ≈ {total} symbols — every one is a potential Hyrum dependency",
            value=total,
        ))

    result.metrics = {
        "total_public_symbols": total,
        "by_language": dict(per_lang),
        "files_with_exports": len(per_file_counts),
    }
    emit(result)


if __name__ == "__main__":
    main()
