---
artifact_id: ART-GOVERNANCE
artifact_type: delivery-governance
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

# Gobierno de entrega

## Modelo vigente y cambios

| ID | State | Effective from | Delivery model | Versioning | Branching | Artifact promotion | Deployment | Recovery | Decision | Review trigger |
|---|---|---|---|---|---|---|---|---|---|---|
| CHG-001 | proposed | pending | pending | pending | pending | pending | pending | pending | pending: awaiting governance ADR | Antes de G2 y ante cambios de producto, organización, riesgo o plataforma |

Seleccione explícitamente uno de estos modelos: `bounded-release`, `continuous-evolution` o `maintenance-stream`. La decisión debe cerrar versionado de producto, ramas y merge, CI/CD, promoción de artefactos, despliegue y recuperación. Una modificación posterior añade un nuevo `CHG-###`; no reescribe el historial.

## Entornos

| ID | State | Role | Promotion order | Deployables | Approval | Configuration | Data | Observability | Recovery |
|---|---|---|---|---|---|---|---|---|---|

Defina roles de entorno y no una cantidad universal. Desarrollo, CI, preview, integración, aceptación, preproducción y producción se incluyen solo cuando sean aplicables. Si se recompila por entorno, documente que no se está promoviendo literalmente el mismo artefacto.
