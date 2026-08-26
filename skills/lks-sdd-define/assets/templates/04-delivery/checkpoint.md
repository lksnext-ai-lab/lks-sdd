---
artifact_id: ART-{{CHECKPOINT_ID}}
artifact_type: implementation-checkpoint
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.12.0"
project_id: "{{PROJECT_ID}}"
baseline_id: "{{BASELINE_ID}}"
status: confirmed
classification: internal
audience:
  - delivery-team
owners:
  - {{OWNER_ROLE}}
source_of_truth: true
last_updated: "{{DATE}}"
---

# {{CHECKPOINT_ID}} · Checkpoint de implementación

## Identidad y repositorio

| Checkpoint | Execution | State | Tasks | Increment | Release | Authorization | Branch | Revision start | Last observed revision | Tree state | Specification fingerprint | Planning fingerprint | Updated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {{CHECKPOINT_ID}} | {{EXECUTION_ID}} | {{EXECUTION_STATE}} | {{TASK_IDS}} | {{INCREMENT_ID}} | {{RELEASE_ID}} | {{AUTHORIZATION_ID}} | {{BRANCH}} | {{REVISION_START}} | {{LAST_REVISION}} | {{TREE_STATE}} | {{SPECIFICATION_FINGERPRINT}} | {{PLANNING_FINGERPRINT}} | {{DATE}} |

## Archivos observados

| Path | State | SHA-256 | Task | Notes |
|---|---|---|---|---|
{{FILE_ROWS}}

## Entregables

| Task | Deliverable | State | Acceptance | Evidence | Notes |
|---|---|---|---|---|---|
{{DELIVERABLE_ROWS}}

## Aceptación, pruebas y gates

| Task | Contract item | Kind | Result | Evidence | Revision | Notes |
|---|---|---|---|---|---|---|
{{CHECK_ROWS}}

## Problemas, bloqueos y decisiones

| ID | State | Kind | Description | Resolution condition | Owner role | Evidence |
|---|---|---|---|---|---|---|
{{ISSUE_ROWS}}

## Reanudación segura

| Completed | Partial | Pending | Blocked | Next safe action | Independent ready tasks | Reconciliation required |
|---|---|---|---|---|---|---|
| {{COMPLETED}} | {{PARTIAL}} | {{PENDING}} | {{BLOCKED}} | {{NEXT_SAFE_ACTION}} | {{INDEPENDENT_TASKS}} | {{RECONCILIATION}} |

Este checkpoint registra estado observado. No constituye por sí mismo commit, evidencia de gate, autorización de publicación ni prueba de terminado.
