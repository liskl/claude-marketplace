---
name: software-eng-laws
description: Audit a repository against all 56 software engineering laws from lawsofsoftwareengineering.com. Produces per-law findings with evidence citations and a summary scorecard. Use when the user asks to "audit laws", "check software engineering laws", "score my repo against Conway/Hyrum/DRY/etc.", "run a software laws audit", or references specific named laws from that site.
argument-hint: "[repo-path] [--output REPORT_PATH] [--skip-manual]"
---

# Software Engineering Laws Audit

This skill audits a git repository against 54 software engineering laws and produces a per-law findings report plus a summary scorecard.

## Inputs

- `repo-path` (positional, optional): directory to audit. Defaults to cwd.
- `--output PATH`: output report path. Defaults to `<repo>/software-laws-report.md`.
- `--skip-manual`: omit the 26 manual-reflection laws from the report.

## Workflow

Follow these steps exactly. Do not skip step 3 (loading per-law reference files) — the rubrics live there, not in this file.

### 1. Resolve target and preflight

- Resolve `repo-path` to an absolute path. Default to cwd.
- Check it exists and is a directory.
- Check if it's a git repo (`git -C <path> rev-parse --git-dir`). If not, note that history-based laws will be skipped — do not abort.
- Get primary language mix: run `scripts/run_audit.py <repo> --languages-only` to get the list of detected languages.

### 2. Run the automated audit

Run the orchestrator:

```
python3 <SKILL_DIR>/scripts/run_audit.py <repo> --out /tmp/laws-findings.json
```

This produces `/tmp/laws-findings.json` matching `schema/finding.schema.json`. It runs all 10 scan scripts and merges their signals. If any script fails, its signals are omitted and a warning is recorded — continue anyway.

Read `/tmp/laws-findings.json` to inspect what the scripts found.

### 3. Score each law

For each of the 56 laws, load its reference file `laws/<category>/<slug>.md`. The reference file contains:
- Detection mode (`code`, `git-history`, `hybrid`, or `manual`)
- Signals to look for
- Scoring rubric (🟢 / 🟡 / 🔴 / ⚪ / ➖ criteria)
- Evidence format
- Remediation hints

Apply the rubric:

- **Detection `code` / `git-history` / `hybrid`**: cross-reference `findings.json` signals against the rubric. If the automated signals don't cover everything, do targeted `Grep`/`Read` to fill gaps — cite `file:line` for every concern.
- **Detection `manual`**: emit status ⚪ and include the reflection prompts verbatim from the reference file, unless `--skip-manual` was passed.
- **Not applicable** (e.g., CAP on a single-process CLI): emit ➖ with a one-line reason.

### 4. Render the report

Use `templates/report.md` as the scaffold. Three sections:

1. **Scorecard** — table of all 56 laws grouped by category: `Law | Status | One-line evidence or reflection prompt`. Use `templates/scorecard.md` as the row format.
2. **Findings** — one block per law using `templates/law_finding.md`, ordered by status severity (🔴 → 🟡 → 🟢 → ⚪ → ➖) then category. Include file:line citations for every concern. Keep each finding tight: signals observed, evidence, one or two remediation suggestions.
3. **Manual reflection** (skipped if `--skip-manual`) — the 26 manual laws with their reflection prompts, so the user can fill them in.

Write the report to the output path. Print the scorecard to stdout at the end so the user sees it without opening the file.

### 5. Summary

End with a one-paragraph summary: total counts per status, top 3 concerns with file:line, and a single sentence on the repo's overall strengths / weaknesses.

## Conventions

- Never fabricate citations. If a rubric calls for `file:line` evidence and you can't find it in the repo, mark the law ⚪ and explain why.
- Keep findings terse — the scorecard is the deliverable, per-law blocks are supporting detail.
- If the user nominates specific laws only, run the full orchestrator but only render findings for those laws. The scorecard always shows all 54.
- If the repo is tiny (<10 source files), warn the user that signal density will be low and many laws will land ⚪.
