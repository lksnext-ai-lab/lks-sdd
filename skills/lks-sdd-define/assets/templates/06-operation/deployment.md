---
artifact_id: ART-DEPLOYMENT
artifact_type: deployment
schema_version: "1.3"
method_version: "1.3.0"
created_with_plugin_version: "0.9.1"
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

# Despliegue e infraestructura

| Environment | State | Role | Deployment unit | Artifact strategy | Configuration | Deployment strategy | Recovery | Observability | Requirements |
|---|---|---|---|---|---|---|---|---|---|

No incluya secretos ni presuponga una nube, plataforma o pipeline no confirmados. Distinga rollback de artefacto, configuración, esquema, datos, caché, replay, compensación y forward-fix según aplicabilidad.
