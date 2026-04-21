# Software Engineering Laws Audit

**Repository**: `{{repo}}`
**Generated**: {{generated_at}}
**Languages**: {{languages_summary}}
**Files scanned**: {{file_count}}{{#if warnings}}
**Warnings**: {{warnings_count}}{{/if}}

---

## Scorecard

Legend: 🟢 Pass · 🟡 Watch · 🔴 Concern · ⚪ Manual review · ➖ Not applicable

{{scorecard_table}}

**Totals**: 🟢 {{count_pass}} · 🟡 {{count_watch}} · 🔴 {{count_concern}} · ⚪ {{count_manual}} · ➖ {{count_na}}

---

## Findings

Ordered by severity, then category.

{{findings_blocks}}

---

## Manual Reflection

The following laws cannot be detected from code alone. Consider each and note any that apply to your team or context.

{{manual_reflection_blocks}}

---

## Summary

{{summary_paragraph}}
