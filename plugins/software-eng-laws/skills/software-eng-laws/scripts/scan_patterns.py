#!/usr/bin/env python3
"""Grep-based pattern signals — distributed fallacies, Postel's, Zawinski's, Murphy's, etc."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import Signal, ScanResult, emit, walk_source_files, read_text, rel

# Hardcoded IPs / localhost / latency-is-zero fallacies.
HARDCODED_IP = re.compile(r"\b(?:127\.0\.0\.1|0\.0\.0\.0|localhost|(?:\d{1,3}\.){3}\d{1,3})\b")
HARDCODED_PORT = re.compile(r":\s*\b(?:80|443|3000|5000|8000|8080|8443)\b")
SILENT_EXCEPT = re.compile(r"except\s*(?:Exception\s*)?:\s*(?:#.*)?$")
SILENT_EXCEPT_PASS = re.compile(r"except[^:]*:\s*\n\s*pass\s*$", re.MULTILINE)
CATCH_EMPTY = re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")
PROCESS_EXIT_IN_LIB = re.compile(r"(sys\.exit|os\._exit|process\.exit|panic!|panic\()")
INFINITE_TIMEOUT = re.compile(r"timeout\s*=\s*(?:None|null|-1|0\s*[,)])", re.IGNORECASE)
EMAIL_PROGRAM = re.compile(r"\b(?:smtp|mailto|send_email|send_mail|nodemailer|smtplib)\b", re.IGNORECASE)

# Postel's Law: strict input handling (we want to see validation AND liberal parsing).
INPUT_VALIDATION = re.compile(
    r"\b(validate|schema|pydantic|zod|joi|yup|ajv|jsonschema)\b", re.IGNORECASE
)


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    result = ScanResult()

    hardcoded_ip_count = 0
    silent_except_count = 0
    exit_in_lib_count = 0
    infinite_timeout_count = 0
    email_features = 0
    validation_hits = 0
    files_scanned = 0

    for p in walk_source_files(repo):
        text = read_text(p)
        if not text:
            continue
        files_scanned += 1
        relpath = rel(p, repo)

        for i, ln in enumerate(text.splitlines(), 1):
            # Skip obvious test / fixture files for network signals.
            if SILENT_EXCEPT.search(ln):
                silent_except_count += 1
                if silent_except_count <= 10:
                    result.signals.append(Signal(
                        law_hints=["murphy", "broken-windows"],
                        severity="watch",
                        summary="Bare except — errors will be silently swallowed",
                        file=relpath, line=i,
                    ))
            if CATCH_EMPTY.search(ln):
                silent_except_count += 1
                if silent_except_count <= 10:
                    result.signals.append(Signal(
                        law_hints=["murphy"],
                        severity="watch",
                        summary="Empty catch block — errors will be silently swallowed",
                        file=relpath, line=i,
                    ))
            if HARDCODED_IP.search(ln) and HARDCODED_PORT.search(ln):
                hardcoded_ip_count += 1
                if hardcoded_ip_count <= 10:
                    result.signals.append(Signal(
                        law_hints=["distributed-fallacies"],
                        severity="watch",
                        summary=f"Hardcoded host:port — {ln.strip()[:140]}",
                        file=relpath, line=i,
                    ))
            if PROCESS_EXIT_IN_LIB.search(ln) and "main" not in relpath.lower() and not relpath.endswith(("_cli.py", "cli.py", "__main__.py")):
                exit_in_lib_count += 1
                if exit_in_lib_count <= 5:
                    result.signals.append(Signal(
                        law_hints=["least-astonishment", "leaky-abstractions"],
                        severity="watch",
                        summary=f"Process exit / panic in non-entry file: {ln.strip()[:120]}",
                        file=relpath, line=i,
                    ))
            if INFINITE_TIMEOUT.search(ln):
                infinite_timeout_count += 1
                if infinite_timeout_count <= 5:
                    result.signals.append(Signal(
                        law_hints=["distributed-fallacies", "murphy"],
                        severity="watch",
                        summary=f"Timeout set to None/0/-1 — {ln.strip()[:120]}",
                        file=relpath, line=i,
                    ))

        # File-level pattern checks.
        if SILENT_EXCEPT_PASS.search(text):
            # Already handled above; count only.
            pass
        if EMAIL_PROGRAM.search(text):
            email_features += 1
        if INPUT_VALIDATION.search(text):
            validation_hits += 1

    # Zawinski's Law: does this non-email program do email?
    if email_features >= 1 and files_scanned > 20:
        result.signals.append(Signal(
            law_hints=["zawinski"],
            severity="info",
            summary=f"{email_features} file(s) reference email/SMTP functionality — Zawinski watch",
            value=email_features,
        ))

    # Postel's Law: little or no input validation.
    if files_scanned >= 20 and validation_hits == 0:
        result.signals.append(Signal(
            law_hints=["postel"],
            severity="watch",
            summary="No input validation library references found",
            value=validation_hits,
        ))

    result.metrics = {
        "files_scanned": files_scanned,
        "silent_exceptions": silent_except_count,
        "hardcoded_host_port": hardcoded_ip_count,
        "exit_in_lib": exit_in_lib_count,
        "infinite_timeouts": infinite_timeout_count,
        "email_features": email_features,
        "validation_hits": validation_hits,
    }
    emit(result)


if __name__ == "__main__":
    main()
