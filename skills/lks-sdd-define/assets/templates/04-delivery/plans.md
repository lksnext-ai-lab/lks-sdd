---
artifact_id: ART-PLANS
artifact_type: delivery-plans
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.15.0"
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

# Planes y releases

## Planes de desarrollo

| ID | State | Name | Delivery model | Major horizon | Objective | Increments | Dependencies | Owner | Review date |
|---|---|---|---|---|---|---|---|---|---|
| PLAN-001 | proposed | Horizonte inicial | pending | initial | Confirmar alcance y modelo de entrega | pending: increments not defined yet | not-applicable: initial plan has no predecessor | pending-assignment | {{DATE}} |

Cada `PLAN-###` delimita un horizonte mayor, release train o stream de mantenimiento. Un cambio de modelo crea o actualiza el plan mediante una decisión trazable; no borra tareas ni evidencias anteriores.

## Releases

| ID | State | Version | Plan | Target date | Branch or stream | Environments | Tasks | Commit | Artifact | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| REL-001 | draft | pending | PLAN-001 | pending | pending | pending: environments not defined yet | pending: tasks not defined yet | pending | pending | pending: no executed evidence |

La versión de producto se decide en gobierno de entrega. `Commit`, `Artifact` y `Evidence` solo se completan con valores observados; nunca se anticipan como superados.
