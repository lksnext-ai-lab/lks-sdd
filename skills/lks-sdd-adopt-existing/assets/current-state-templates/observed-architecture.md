---
artifact_id: ART-ADOPT-ARCHITECTURE
artifact_type: observed-architecture
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.14.0"
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

# Arquitectura observada

| Statement | State | Source | Nature | Confidence | Limitations |
|---|---|---|---|---|---|
| Se observaron los manifiestos {{MANIFESTS}}. | fact | inventario estático | observación | alta | No acredita topología de ejecución ni uso productivo |
| Las extensiones {{SOURCE_EXTENSIONS}} sugieren componentes que deben confirmarse. | assumption | extensiones de archivos | inferencia | media | No equivale a una decisión arquitectónica |

La arquitectura deseada se define en los artefactos de solución después de reconciliar intención, restricciones y decisiones.
