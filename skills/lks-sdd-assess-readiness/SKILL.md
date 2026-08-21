---
name: lks-sdd-assess-readiness
description: "Use the LKS-SDD Codex plugin to assess whether one documented increment and its selected TASK slice are ready for implementation, including delivery governance, plan/release, deployable-unit bindings, exact certified profile locks, and semantic specification readiness. Use when the user asks whether work can pass G2 or what prevents it; do not define requirements, authorize work, generate code, implement, or verify."
---

# Assess LKS-SDD Readiness

Evaluate one increment, not the whole project. A ready result is evidence for a human decision; it never authorizes implementation.

1. Read `.lks-sdd/project.json` and the canonical Markdown paths it indexes. If either is absent or invalid, report an explained blocker. A project indexed as LKS-SDD 0.6+ always uses the 0.6 gates; a downgraded Markdown header cannot turn it into legacy. Migrated projects whose index remains below 0.6 keep the legacy fallback until their visual contract is deliberately materialized.
2. Read [readiness rubric](references/readiness-rubric.md). Resolve `<plugin-root>` as the directory containing `.codex-plugin/plugin.json` for this installed skill; never resolve `scripts/` against the consumer project. Run `python "<plugin-root>/scripts/lks_sdd.py" assess-readiness "<project-root>" --increment <INC-###>`. Use `--json` when a structured result is useful.
3. Review semantic sufficiency the deterministic script cannot judge: clarity, testability, contradictions, risk, and whether recorded confirmations are explicit. Do not silently repair the specification during assessment.
4. For schema 1.2, require confirmed delivery governance, a confirmed or active `PLAN-###`, a planned/active/frozen `REL-###`, at least one selected `TASK-###` in `ready`, resolved dependencies, confirmed `UNIT-###`/`BIND-###`, and exact supported locks. Assess only the selected ready slice, not unrelated backlog in the same increment.
5. Classify each issue as blocking or non-blocking for the affected scope. Report `specification_readiness`, `delivery_readiness`, and `automation_support` separately: an alternative stack may be sufficiently specified while its exact composition remains unsupported. Do not let an unrelated blocker stop independent work.
6. Return the combined safe gate plus component outcomes, task/binding IDs, `checked_files`, the active-contract fingerprint, blockers, non-blocking pending items, limitations, and the smallest next decision or documentation change needed. The active fingerprint freezes only the canonical nodes, relations, selected profile bindings, locks, tasks, and confirmed prototype assets that affect the slice; historical entries remain auditable. A second validation pass blocks a contract that changes during assessment.

For an adopted project, require a materialized and current baseline. Do not produce code, change state, or infer implementation approval.
