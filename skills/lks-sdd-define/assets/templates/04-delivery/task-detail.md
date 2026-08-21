---
artifact_id: ART-{{TASK_ID}}
artifact_type: development-task
schema_version: "1.2"
method_version: "1.2.0"
created_with_plugin_version: "0.8.0"
project_id: "{{PROJECT_ID}}"
baseline_id: "{{BASELINE_ID}}"
status: draft
classification: internal
audience:
  - delivery-team
owners:
  - pending-assignment
source_of_truth: true
last_updated: "{{DATE}}"
---

# {{TASK_ID}} · {{TASK_TITLE}}

## Identidad

| Task | Plan | Release | Increment | Unit | Profile binding | Type |
|---|---|---|---|---|---|---|
| {{TASK_ID}} | {{PLAN_ID}} | {{RELEASE_ID}} | {{INCREMENT_ID}} | {{UNIT_ID}} | {{BINDING_ID}} | implementation |

## Definición ejecutable

| Objective | In scope | Out of scope | Requirements | Acceptance | Required capabilities | Technical gates | Dependencies |
|---|---|---|---|---|---|---|---|
| pending | pending | pending | pending | pending | pending | pending | not-applicable |

## Ejecución y seguimiento

| Workflow state | Health | Progress | Owner | Branch | Revision start | Revision verified | Build | Environment | Updated |
|---|---|---|---|---|---|---|---|---|---|
| backlog | unknown | 0 | pending-assignment | pending | pending | pending | pending | pending | {{DATE}} |

## Problemas y bloqueos

| ID | State | Description | Impact | Owner | Resolution condition | Evidence |
|---|---|---|---|---|---|---|

## Validación

| Acceptance | Gate | Result | Evidence | Revision | Artifact digest | Environment |
|---|---|---|---|---|---|---|

## Historial de cambios

| Date | From | To | Reason | Actor or authority | Evidence |
|---|---|---|---|---|---|

La tarea no está lista hasta que su aceptación, dependencias, perfil/lock y gates sean resolubles. `done` exige evidencia ligada a la revisión y al artefacto realmente verificados.
