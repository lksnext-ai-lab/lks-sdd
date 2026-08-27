---
artifact_id: ART-TASKS
artifact_type: development-task-board
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.13.0"
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

# Tablero de tareas de desarrollo

## PLAN-001 · Horizonte inicial

| ID | Plan | Title | Release | Increment | Unit | Profile binding | Workflow state | Health | Progress | Dependencies | Blockers | Owner | Detail | Updated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Use una tabla por `PLAN-###` o versión mayor para mantener el seguimiento legible. `Workflow state` admite `backlog`, `ready`, `in-progress`, `in-review`, `done`, `blocked` y `cancelled`; `Health` admite `on-track`, `at-risk`, `blocked` y `unknown`; `Progress` usa un entero de 0 a 100. Cada fila enlaza un detalle independiente en `./tasks/TASK-###.md`.

El tablero se deriva de las definiciones de tarea y sirve como vista operativa rápida. No duplique aquí comandos, versiones exactas, aceptación detallada ni evidencias completas.
