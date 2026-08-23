---
artifact_id: ART-ADOPT-SCOPE
artifact_type: inspection-scope
schema_version: "1.3"
method_version: "1.3.0"
created_with_plugin_version: "0.9.1"
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

# Alcance de inspección

- Raíz confirmada: `{{ROOT_LABEL}}`.
- Alcance relativo: `{{SCOPE}}`.
- Estado productivo declarado: `{{PRODUCTION_STATE}}`.
- Permiso de descubrimiento: solo lectura.
- Exclusiones confirmadas: {{EXCLUSIONS}}.
- Cobertura: {{FILES_INVENTORIED}} archivos inventariados; truncada: {{TRUNCATED}}.

No se ejecutaron código, builds, pruebas, contenedores, migraciones, hooks ni gestores de paquetes.
