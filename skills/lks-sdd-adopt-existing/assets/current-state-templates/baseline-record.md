---
artifact_id: ART-ADOPT-BASELINE
artifact_type: baseline-record
schema_version: "1.0"
method_version: "1.0.0"
created_with_plugin_version: "0.3.0"
project_id: "{{PROJECT_ID}}"
baseline_id: "{{BASELINE_ID}}"
status: confirmed
classification: internal
audience:
  - delivery-team
owners:
  - pending-assignment
source_of_truth: true
last_updated: "{{DATE}}"
---

# Registro de baseline adoptada

| Campo | Valor |
|---|---|
| Baseline | `{{BASELINE_ID}}` |
| Revisión Git | `{{REVISION}}` |
| Rama | `{{BRANCH}}` |
| Estado inicial | `{{DIRTY_STATE}}` |
| Fingerprint de inventario | `sha256:{{INVENTORY_FINGERPRINT}}` |
| Informe | `sha256:{{REPORT_SHA256}}` |
| Decisión | `sha256:{{DECISION_SHA256}}` |
| Materialización | `{{DATE}}` |

`Baseline adoptada` significa punto de partida gobernable. No significa aplicación homologada ni verificada.
