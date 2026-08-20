---
artifact_id: ART-INCREMENTS
artifact_type: increments
schema_version: "1.0"
method_version: "1.0.0"
created_with_plugin_version: "0.1.0"
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

# Incrementos

| ID | State | In scope | Out of scope | Requirements | Acceptance | Decisions | Data | Identity | Integrations | Tests |
|---|---|---|---|---|---|---|---|---|---|---|

## Aplicabilidad de interfaz y contrato visual

| Increment | Interface applicability | UX contract | Visual mode | Visual prototype | Reason |
|---|---|---|---|---|---|

Use `applicable`, `pending` o `not-applicable` en `Interface applicability`. Para `pending` y `not-applicable`, explique el motivo. En `Visual mode` use `pending`, `new`, `material-change`, `reuse` o `none`. Un incremento aplicable enlaza los elementos `UX-###` correspondientes dentro de `ART-UX`. `new` y `material-change` enlazan `VIS-###` o permanecen `pending`; `reuse` enlaza una baseline `VIS-###` confirmada y explica qué se reutiliza; `none` usa `not-applicable: motivo` solo cuando no existe cambio visual real. No esconda una reutilización bajo `none`.

Un incremento debe ser vertical, acotado y comprobable. Datos, identidad o integraciones no aplicables se justifican como `not-applicable: motivo`. Su confirmación no autoriza implementación.
