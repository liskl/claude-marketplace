#!/usr/bin/env python3
"""Function length, nesting depth, and file size — signals for KISS, Kernighan's Law, Tesler's Law."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import (
    Signal, ScanResult, emit, walk_source_files, read_text, rel,
    count_loc, language_of,
)

LONG_FUNCTION_LOC = 60
VERY_LONG_FUNCTION_LOC = 120
DEEP_NESTING = 5
LARGE_FILE_LOC = 600

# Language-specific function opener regex. Matches a line that begins a function.
# We detect END by brace-depth for C-family, and by indentation for Python.
FUNC_OPEN = {
    "Python": re.compile(r"^(?P<indent>\s*)(?:async\s+)?def\s+(\w+)\s*\("),
    "JavaScript": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("),
    "TypeScript": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\("),
    "Go": re.compile(r"^func\s+(?:\([^)]*\)\s+)?(\w+)\s*\("),
    "Rust": re.compile(r"^\s*(?:pub\s+(?:\([^)]+\)\s+)?)?(?:async\s+)?fn\s+(\w+)\s*[\(<]"),
    "Java": re.compile(r"^\s*(?:public|private|protected|static|\s)+\S+\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?\{"),
}


def analyze_python_function(lines: list[str], start: int) -> tuple[int, int]:
    """Return (loc, max_nesting) for a Python function starting at `start`."""
    m = FUNC_OPEN["Python"].match(lines[start])
    base_indent = len(m.group("indent")) if m else 0
    end = start + 1
    max_nest = 0
    while end < len(lines):
        ln = lines[end]
        if ln.strip() == "":
            end += 1
            continue
        stripped = len(ln) - len(ln.lstrip(" \t"))
        if stripped <= base_indent and ln.strip():
            break
        # Nesting proxy: extra indent levels beyond base.
        nest_level = max(0, (stripped - base_indent) // 4)
        if nest_level > max_nest:
            max_nest = nest_level
        end += 1
    loc = sum(1 for ln in lines[start:end] if ln.strip())
    return loc, max_nest


def analyze_braced_function(lines: list[str], start: int) -> tuple[int, int]:
    """For C-family: count until matching braces balance."""
    depth = 0
    seen_open = False
    end = start
    max_nest = 0
    for i in range(start, len(lines)):
        ln = lines[i]
        for ch in ln:
            if ch == "{":
                depth += 1
                seen_open = True
                if depth > max_nest:
                    max_nest = depth
            elif ch == "}":
                depth -= 1
        end = i
        if seen_open and depth == 0:
            break
    loc = sum(1 for ln in lines[start:end + 1] if ln.strip())
    return loc, max_nest


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()

    total_functions = 0
    total_long = 0
    file_loc_total = 0

    for p in walk_source_files(repo):
        lang = language_of(p)
        text = read_text(p)
        if not text:
            continue
        lines = text.splitlines()
        file_loc = count_loc(text)
        file_loc_total += file_loc

        if file_loc >= LARGE_FILE_LOC:
            result.signals.append(Signal(
                law_hints=["kiss", "tesler", "broken-windows", "second-system"],
                severity="watch" if file_loc < 1500 else "concern",
                summary=f"Large file ({file_loc} LOC)",
                file=rel(p, repo),
                line=1,
                value=file_loc,
                threshold=LARGE_FILE_LOC,
            ))

        opener = FUNC_OPEN.get(lang or "")
        if not opener:
            continue

        for i, ln in enumerate(lines):
            if not opener.match(ln):
                continue
            total_functions += 1
            if lang == "Python":
                loc, nest = analyze_python_function(lines, i)
            else:
                loc, nest = analyze_braced_function(lines, i)

            if loc >= VERY_LONG_FUNCTION_LOC:
                total_long += 1
                result.signals.append(Signal(
                    law_hints=["kiss", "kernighan", "tesler"],
                    severity="concern",
                    summary=f"Very long function ({loc} LOC)",
                    file=rel(p, repo),
                    line=i + 1,
                    value=loc,
                    threshold=VERY_LONG_FUNCTION_LOC,
                ))
            elif loc >= LONG_FUNCTION_LOC:
                total_long += 1
                result.signals.append(Signal(
                    law_hints=["kiss", "kernighan"],
                    severity="watch",
                    summary=f"Long function ({loc} LOC)",
                    file=rel(p, repo),
                    line=i + 1,
                    value=loc,
                    threshold=LONG_FUNCTION_LOC,
                ))

            if nest >= DEEP_NESTING:
                result.signals.append(Signal(
                    law_hints=["kiss", "kernighan"],
                    severity="watch",
                    summary=f"Deep nesting ({nest} levels)",
                    file=rel(p, repo),
                    line=i + 1,
                    value=nest,
                    threshold=DEEP_NESTING,
                ))

    result.metrics = {
        "total_functions": total_functions,
        "long_functions": total_long,
        "long_function_ratio": round(total_long / total_functions, 3) if total_functions else 0.0,
        "total_source_loc": file_loc_total,
    }
    emit(result)


if __name__ == "__main__":
    main()
