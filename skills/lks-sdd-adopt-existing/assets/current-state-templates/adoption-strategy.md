---
artifact_id: ART-ADOPT-STRATEGY
artifact_type: adoption-strategy
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

# Estrategia de adopción

- Estrategia confirmada: `{{STRATEGY}}`.
- Alcance de escritura autorizado: `.lks-sdd/` y `docs/lks-sdd/`.
- Código, configuración, datos, infraestructura, `README.md` y `AGENTS.md`: fuera de alcance.
- Referencia de confirmación: {{CONFIRMATION_REFERENCE}}.

Cualquier normalización o modernización posterior requiere un incremento, decisiones, migración y reversión propios; esta materialización no cambia comportamiento.
