---
name: lks-sdd-verify
description: "Use with Codex. Verify a completed LKS-SDD task slice against agreed acceptance and typed evidence using exact-subject gates and approved observers; preserve immutable history, original observation age and the separation of technical verification, human acceptance and delivery."
---

# Verify an LKS-SDD Increment with Codex

## Routing por contrato

Read [v2 common policy and workflows](../../docs/V2-WORKFLOWS.md) for contract
2.0 or a new v2 project. Responsibility: Verificar sujeto exacto y conservar evidencia inmutable, sin aprobar entrega.
Use only the relevant section of that shared workflow and its linked references;
do not combine v2 syntax with the legacy workflow below. Existing projects remain
on their exact pinned runtime until explicitly migrated. Unknown schemas fail
closed; a question never initiates adoption, migration or implementation.

## Workflow conservado para contrato 1.5

For explaining requirements, tasks and existing evidence, read
`<plugin-root>/docs/PROJECT-QUERY.md`. A query reads historical evidence without
executing verification or creating EVID/CKPT. Separate prior results, current
health and production; this presentation policy never replaces verification gates.

For configured project variants, read `<plugin-root>/docs/PROJECT-VARIANTS.md`.
Its opt-in route governs technology approval, consumer observers and proportional
gates; the strict profile workflow below remains the default otherwise. `work verify`
selects the declared variant, retains AUTH/EXEC and reuses valid evidence. Present
one grouped approval only when required. A policy-authorized TASK may close with
reserved variant evidence, while release, Jira Done and deployment retain their
separate conditions. Never convert consumer approval into global certification.

For a project with `.lks-sdd/distribution-lock.json`, use its exact pinned runtime
and this workflow from that runtime, not a different global version. Run
`<plugin-root>/scripts/lks_sdd.py runtime-doctor <project-root> --json` before work;
integrity failure blocks affected actions. The invoking host adapter governs tools,
not folder presence. Preserve all method gates below. On resumption, read applicable
visual handoffs and validate their results; no handoff grants implementation authority.
Help/status remain read-only. Native Codex work never creates or announces a handoff.

Verification produces evidence, not approval. Never classify a check as passed unless it actually ran and its result is available.

1. Read the project index, current `EXEC-###`/`CKPT-###`, implementation `task_ids`, planning fingerprints and authorization, every profile binding/lock, delivery governance, release/environment, acceptance, tests, traceability, implementation diff and repository instructions. Reconcile any checkpoint divergence before running checks.
2. Read the [verification contract](references/verification-contract.md). When `ART-TRACKING` confirms `jira-hybrid`, also read the [Jira verification sync contract](references/jira-verification-sync.md). Resolve `<plugin-root>` as the directory containing `.codex-plugin/plugin.json` for this installed skill; never resolve `scripts/` against the consumer project. Run `python "<plugin-root>/scripts/lks_sdd.py" verify "<project-root>" --increment <INC-###> --task <TASK-###> --execution-id <EXEC-###> --plan --json` and explain applicable checks, side effects, prerequisites, and omissions. Omit `--execution-id` only when the selected tasks resolve one execution unambiguously. An anticipatory `in-progress` plan never authorizes execution. The runner selects the bindings of the requested TASK slice and expands the structured joint integration table only for its confirmed `INT-###`. `visual-browser-review` and `GATE-BROWSER-FULLSTACK-E2E` have separate task-aware applicability: backend-only or standalone frontend work records deterministic non-applicability; a joint interface TASK requires all declared units/bindings and its exact certified system composition.
3. Execute only after the implementation record is `completed` and explicit authorization is present with `--execute --authorize`. Never run while its increment/tasks/bindings/locks are absent or inconsistent, or status remains `in-progress`, `not-started`, or `blocked`. Add `--containers` only when the declared compositions are authorized and safe. For an applicable interface, provide reviewed browser evidence 1.2 with `--visual-evidence <local-json>`: one to five meaningful images per TASK by default, never quota filler. Reuse still-applicable captures and open the browser only for missing, changed or risky states. Do not substitute a different command because a required tool is missing.
4. Run all required capability gates plus each exact composition gate. Classify every check with one or more of `component`, `contract`, `composition`, `user-flow`, `persistence`, `visual`; lower scopes never satisfy higher ones. The full-stack gate must record structured runtime units, browser/viewport, real requests matching the declared INT operations, a UI-originated mutation, response/correlation data, read-back, reload, persistence, screenshot paths/hashes and console errors. A declared identity double may be valid in a non-production profile, but interception of a functional contract operation at any path invalidates `composition`, `user-flow` and `persistence` even if it remains useful as a frontend component test. Review semantic acceptance, security, accessibility, performance, data/identity/messaging recovery, deployment, and rollback according to applicability. For Microsoft Entra, keep synthetic discovery/claims or PKCE checks separate from an authorized real-tenant interoperability gate; a local pass cannot be recorded as external interoperability. Automated technical gates cannot prove business behavior or human acceptance by themselves.
5. Record `EVID-###` only in the same authorized execution while the implementation remains `completed`. An empty or whitespace-only ART-TRACE `Evidence` cell is the normal pending state and is replaced atomically by the exact EVID together with manifest/EXEC updates; never pre-normalize consumer Markdown or overwrite an existing EVID. Bind it to task IDs, profile locks, commit/workspace revision, exact tree ID and SHA-256, deterministic build ID, separate verification run ID, immutable artifact digests, environment, gates, acceptance, tests and limitations. Derive profile identity from the bindings selected by the TASK slice, never from a project-wide convenience field: one binding emits the exact top-level `profile_id`/`profile_version`; multiple bindings omit that summary and retain every identity in bindings, locks and build material. Validate the candidate and the resulting project/traceability before reporting `evidence_recorded=true`; any rejection restores EVID, ART-TRACE, manifest and EXEC together. The build ID contains only stable canonical inputs; durations, timestamps, logs, PID and dynamic Compose names remain execution diagnostics. For G4, first execute G3 with `--environment ENV-### --materialize-delivery-template docs/lks-sdd/evidence/delivery/<name>.json`. This writes a `draft` 1.1 template already bound to revision, tree, build and artifacts without declaring delivery checks passed. Complete and authorize the real delivery evidence, then rerun with `--delivery-evidence <path>`; the same tree, locks and artifacts must reproduce the build ID and any mismatch fails closed. Legacy complete evidence 1.0 remains readable.
   Use `assets/delivery-evidence.example.json` only as a field-level example and replace every synthetic value with evidence from the exact verified delivery.
6. Classify the result as `verified`, `verified-with-reservations`, or `not-verified`. Report failed, blocked, not-run and not-applicable checks separately, with limitations and the smallest corrective action. Update the task/checkpoint summary without converting partial implementation into `done`. For a TASK slice, verify traceability with the same repeated `--task TASK-###` arguments; omitting them deliberately checks the full increment and cannot let backend evidence cover future frontend requirements.
7. When every release task is done, run the planned joint integration/release verification before presenting the release as verified. Report remaining uncovered scope even if all currently registered tasks completed.
8. In `jira-hybrid` mode, synchronize the governed projection only after local evidence and the canonical task/checkpoint transition are durable. When `RPT-###` enables `milestone-reporting`, use `preview-event` for `verification-pending`, `verification-failed` or `done`; use the exact `EVID-###` as source for failed or completed verification. A `done` preview is impossible unless the repository already records current `verified` evidence for that TASK. After a fresh authorized Rovo read, one human confirmation may authorize the preview as a unit, but `authorize-event` persists separate comment and optional transition receipts and every operation must be reread and closed independently. A workflow mapping uses immutable Jira status IDs and an observed transition ID, never names alone. A `failed`, `blocked`, `not-run`, `not-verified` or reserved result never transitions Jira to a Done-equivalent status. A Jira failure does not invalidate local evidence; preserve the canonical outcome and use append-only reconciliation, never detach/rebind the durable target.
9. Delivery remains a separate human decision. Before promotion, summarize where the release stands, completed/ongoing/missing/blocked work, exact evidence, next step and required human authorization. For a client view, follow [client-view rules](references/client-view-rules.md) and use the controlled renderer only with confirmed, client-authorized sources.

## Reuse, health and narration in 0.18

Begin with `work status` and prefer `work verify` for the normal path. Calculate the deterministic `verification_subject` before gates. If it matches prior evidence and only explicitly excluded administrative outputs changed, reuse eligible gates and record a continuity attestation with old/new revision and excluded paths. Any code, test, migration, execution fixture, dependency/lock, Docker/build descriptor, artifact-affecting configuration, delivery script, profile/binding, active contract, criterion or applicable gate change invalidates reuse; ambiguity fails closed.

EVID 1.3 records typed scope and interface applicability. Preserve older EVID byte-for-byte: component checks remain valid for their demonstrated scope, but a historical joint closure without cross-binding evidence is `reconciliation-required`. Identify affected interfaces, tasks and evidence and propose the canonical PROB/PCH flow; do not reopen tasks or mutate history automatically. A new authorized execution may supersede only the insufficient joint claim.

Report once before verification, at a material result or blocker, and at completion. The default management response separates code, tests, verification and delivery and uses one compact technical reference. Full hashes, gate lists, evidence payloads, receipts and timings belong to developer/audit unless they directly cause failure.

`work verify --record-evidence` genera todas las fichas TASK derivadas en una sola transacción. No se editan manualmente, no son autoridad, quedan fuera de `verification_subject` y se restauran junto con EVID, ART-TRACE y manifest si falla la materialización. Mantén EVID como hecho histórico y deriva la salud actual de hallazgos vigentes; un problema posterior compromete la salud o deja pendiente la re-verificación sin reescribir el resultado antiguo.

En Jira proyecta, como máximo, un comentario por `verification-passed`, `verification-failed`, `finding-opened`, `correction-completed` o `reverification`. Resume TASK, resultado, pruebas, imágenes, hallazgos, revisión y próxima acción; usa solo referencias versionadas relativas. Únicamente `verified` permite una transición Done-equivalente.

Use packaged observers and exact runtime configuration. HTTP declares METHOD/path, PostgreSQL TABLE/resource and migration REVISION/from-to; login or an unrelated write never proves business persistence. Sanitize before output or persistence, reject contaminated evidence without rewriting history, and retain source, variant, environment and execution provenance.
