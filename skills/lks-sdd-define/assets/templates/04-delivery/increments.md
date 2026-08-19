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

Un incremento debe ser vertical, acotado y comprobable. Datos, identidad o integraciones no aplicables se justifican como `not-applicable: motivo`. Su confirmación no autoriza implementación.
