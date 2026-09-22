---
name: lks-sdd-assess-readiness
description: "Use with Codex. Assess documented LKS-SDD scope before implementation: distinguish specification sufficiency, whole-plan coverage, selected task dependencies, technology approval and execution authorization; report actionable blockers without changing files or granting authority."
---

# Assess LKS-SDD Readiness

## Routing por contrato

Read [SPEC to PLAN/TASK continuity](../../docs/V2-SPEC-PLAN-TASK.md) for method
2.1.0. Assess the requested slice from the material request and SPEC toward PLAN
and TASK; report omitted requirements or acceptance by ID and source. Keep the
assessment read-only and route missing definition or planning to define.

Read [v2 common policy and workflows](../../docs/V2-WORKFLOWS.md) for contract
2.0 or a new v2 project. Responsibility: Evaluar suficiencia y ejes separados, sin reparar ni autorizar.
Use only the relevant section of that shared workflow and its linked references;
do not combine v2 syntax with the legacy workflow below. Existing projects remain
on their exact pinned runtime until explicitly migrated. Unknown schemas fail
closed; a question never initiates adoption, migration or implementation.

Readiness must report migration state separately from task readiness. A clean
`migration-complete` cutover is necessary but does not approve business
semantics; use TASK-scoped continuation and do not turn `legacy`, `unknown` or
`conflict` records into active obligations implicitly.

## Workflow conservado para contrato 1.5

Use `<plugin-root>/docs/PROJECT-QUERY.md` when explaining affected requirements,
specifications and tasks. A content question remains a read-only help query,
not a readiness assessment. Its partial context never replaces the strict
assessment inputs or makes an invalid contract ready.

When a consumer differs from the project documentation, read
la declaración tecnológica local indexada. Report reference documented confirmation
and scoped consumer approval separately. A valid opt-in approval can use the
documented scope preparation/verification route; do not label an unknown stack incompatible.

For a project with `.lks-sdd/distribution-lock.json`, use its exact pinned runtime
and this workflow from that runtime, not a different global version. Run
`<plugin-root>/scripts/lks_sdd.py runtime-doctor <project-root> --json` before work;
integrity failure blocks affected actions. The invoking host adapter governs tools,
not folder presence. Preserve all method gates below. On resumption, read applicable
visual handoffs and validate their results; no handoff grants implementation authority.
Help/status remain read-only. Native Codex work never creates or announces a handoff.

Evaluate one increment, not the whole project. A ready result is evidence for a human decision; it never authorizes implementation.

1. Read `.lks-sdd/project.json` and the canonical Markdown paths it indexes. If either is absent or invalid, report an explained blocker. LKS-SDD 0.18 requires schema 1.5/method 1.5.0; an older index is rejected without mutation and a downgraded Markdown header cannot bypass the current gates.
2. Read [readiness rubric](references/readiness-rubric.md). Resolve `<plugin-root>` as the directory containing `.codex-plugin/plugin.json` for this installed skill; never resolve `scripts/` against the consumer project. Run `python "<plugin-root>/scripts/lks_sdd.py" assess-readiness "<project-root>" --increment <INC-###>`; add one repeatable `--task TASK-###` per selected task when assessing a portion instead of the default initial slice. Use `--json` when a structured result is useful.
3. Review semantic sufficiency the deterministic script cannot judge: clarity, testability, contradictions, risk, whether one task concentrates an unreasonable or unverifiable amount of exact `coverage.by_task`, whether contributor responsibilities overlap ambiguously, and whether recorded confirmations are explicit. Do not silently repair the specification during assessment and do not impose an invented size threshold.
4. For schema 1.5, evaluate the selected slice, the complete increment/release, projection tracking and milestone reporting simultaneously while keeping their results separate. Require confirmed delivery governance, plan/release, executable selected tasks, resolved dependencies, confirmed units/bindings and exact supported locks for slice readiness. Independently derive full ownership of active scope, acceptance and tests, executable task definitions, release consistency, DAG integrity, parallel frontiers and joint integration; never infer completeness from the number of existing tasks.
5. Classify each issue against its actual axis. Report `specification_readiness`, strict `automation_support`, diagnostic `automation_coverage`, `planning_completeness`, `selected_slice_readiness`, `implementation`, `verification` and `delivery` separately. `automation_coverage` distinguishes project documentation fit, preparation, implementation, local verification, external interoperability and delivery evidence per binding; it is diagnostic-only and must never be labelled partially supported. A selected TASK may remain `ready` while planning is `partial`; an unrelated blocked task may coexist with independent ready work. A dependency is resolved only by `done`, never merely by `cancelled`.
6. When `ART-TRACKING` confirms `jira-hybrid` or the user asks about Jira tracking, read the [Jira readiness contract](references/jira-readiness-contract.md). Derive all LKS-SDD readiness axes from the repository first. Report `task_tracking` and `jira_reporting` separately; `ready`, `paused`, `pending`, `failed` or `reconciliation-required` reporting never substitutes for local readiness. If the local plan is not confirmed, integral and current, report projection `not-assessed` rather than inventing a Jira operation. Never use a Jira status or receipt as specification, authorization, dependency, TASK transition or verification evidence. Reading live Jira requires explicit authorization in the current task; assessment never writes Jira. Only a confirmed `required-before-execution` coordination gate can block execution readiness; `advisory` surfaces a warning while the valid local workflow remains usable.
7. For the selected TASK slice, report `integration_applicability` from confirmed canonical `INT-###` rows. A backend-only or standalone frontend slice is deterministically `not-applicable`; a joint owner must select every unit/binding and an exact certified system composition. Component local technology declaration support cannot make a cross-unit slice ready. If the exact composition is absent, stale or uncertified, report `automation_support=unsupported` with the interface and next documented confirmation/reconciliation step.
8. Return an action-oriented transition summary: what is completed, phase states, concrete uncovered IDs and incomplete tasks, recommended next step, available safe work and required human decision. Do not return a bare global `ready`. Use `planning-required` when specification is closed but coverage is partial; `ready-for-implementation-authorization` when planning and slice are ready but no current `AUTH-###` exists; and `ready-to-implement` only when the recorded authorization also matches both current fingerprints.
8. Also return task/binding IDs, `checked_files`, specification/planning/active-contract fingerprints, blockers, non-blocking pending items and limitations. For a candidate Entra local technology declaration, make real-tenant interoperability and exact documented confirmation visibly `not-run`; local discovery, claims or PKCE tests do not close them, and an active Keycloak local technology declaration is not an equivalent fallback. Historical entries remain auditable. A second validation pass blocks a contract that changes during assessment, and any stale authorization is reported rather than silently refreshed.

For an adopted project, require a materialized and current baseline. Do not produce code, change state, or infer implementation approval.

## Default status and narration in 0.16

Before detailed assessment run `status <project-root> --task TASK-###` and explain the whole project plus selected task in product language. The default answer uses `management`; IDs, `checked_files`, fingerprints and full diagnostics belong to `developer` or `audit`, unless they directly cause a blocker. Do not request an authorization that already matches the exact current scope and fingerprints. Exclude production-only decisions from a non-production slice and group them as future, non-blocking work. Never collapse code, tests, verification and delivery into one global blocked percentage.

Una TASK de interfaz debe poder demostrar su aceptación y riesgos con una a cinco imágenes significativas; si necesita más estados esenciales, recomienda dividir o priorizar sin rebajar el máximo. Si no existe una TASK activa inequívoca, conserva `current_task: null`. Informa verificación histórica y salud actual como ejes separados.

For exact documented scope, require dependency resolution without drift as well as current local technology declaration documented confirmation. Evaluate system composition and all participant locks from INT, not a fictitious system UNIT. Incompatibility, an unevaluated combination and missing information are distinct blockers.
