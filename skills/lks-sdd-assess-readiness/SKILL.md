---
name: lks-sdd-assess-readiness
description: Use the LKS-SDD Codex plugin to assess whether one documented increment is ready for implementation, ready with non-blocking pending items, or blocked for an explained scope. Use when the user asks if an increment can pass to implementation with Codex or what prevents it; do not use to define requirements, authorize work, generate code, implement, or verify.
---

# Assess LKS-SDD Readiness

Evaluate one increment, not the whole project. A ready result is evidence for a human decision; it never authorizes implementation.

1. Read `.lks-sdd/project.json` and the canonical Markdown paths it indexes. If either is absent or invalid, report an explained blocker. A project indexed as LKS-SDD 0.6+ always uses the 0.6 gates; a downgraded Markdown header cannot turn it into legacy. Migrated projects whose index remains below 0.6 keep the legacy fallback until their visual contract is deliberately materialized.
2. Read [readiness rubric](references/readiness-rubric.md). Resolve `<plugin-root>` as the directory containing `.codex-plugin/plugin.json` for this installed skill; never resolve `scripts/` against the consumer project. Run `python "<plugin-root>/scripts/lks_sdd.py" assess-readiness "<project-root>" --increment <INC-###>`. Use `--json` when a structured result is useful.
3. Review semantic sufficiency the deterministic script cannot judge: clarity, testability, contradictions, risk, and whether recorded confirmations are explicit. Do not silently repair the specification during assessment.
4. Classify each issue as blocking or non-blocking for the affected scope. Report `specification_readiness` separately from `automation_support`: an alternative stack may be sufficiently specified while remaining unsupported for implementation by this plugin. Do not let an unrelated blocker stop independent work.
5. Return the combined safe gate plus both component outcomes, `checked_files`, the active-contract fingerprint, blockers, non-blocking pending items, limitations, and the smallest next decision or documentation change needed. The active fingerprint freezes only the canonical nodes, relations, selected profile and confirmed prototype assets that affect the increment; historical rejected or superseded assets remain auditable but do not invalidate a preview. A second validation pass blocks a contract that changes during assessment.

For an adopted project, require a materialized and current baseline. Do not produce code, change state, or infer implementation approval.
