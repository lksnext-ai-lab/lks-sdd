---
name: lks-sdd-assess-readiness
description: Use the LKS-SDD Codex plugin to assess whether one documented increment is ready for implementation, ready with non-blocking pending items, or blocked for an explained scope. Use when the user asks if an increment can pass to implementation with Codex or what prevents it; do not use to define requirements, authorize work, generate code, implement, or verify.
---

# Assess LKS-SDD Readiness

Evaluate one increment, not the whole project. A ready result is evidence for a human decision; it never authorizes implementation.

1. Read `.lks-sdd/project.json` and the canonical Markdown paths it indexes. If either is absent or invalid, report an explained blocker. A project indexed as LKS-SDD 0.6+ always uses the 0.6 gates; a downgraded Markdown header cannot turn it into legacy. Migrated projects whose index remains below 0.6 keep the legacy fallback until their visual contract is deliberately materialized.
2. Read [readiness rubric](references/readiness-rubric.md), then run `python scripts/assess_readiness.py <project-root> --increment <INC-###>`. Use `--json` when a structured result is useful.
3. Review semantic sufficiency the deterministic script cannot judge: clarity, testability, contradictions, risk, and whether recorded confirmations are explicit. Do not silently repair the specification during assessment.
4. Classify each issue as blocking or non-blocking for the affected scope. Do not let an unrelated blocker stop independent work.
5. Return the outcome, `checked_files`, `input_fingerprint`, blockers, non-blocking pending items, limitations, and the smallest next decision or documentation change needed. The fingerprint freezes both canonical Markdown and validated prototype images for a later implementation preview; a second validation pass blocks a contract that changes during assessment.

For an adopted project, require a materialized and current baseline. Do not produce code, change state, or infer implementation approval.
