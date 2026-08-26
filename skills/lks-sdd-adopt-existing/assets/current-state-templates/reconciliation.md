---
artifact_id: ART-ADOPT-RECONCILIATION
artifact_type: reconciliation
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.12.0"
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

# Reconciliación `as-is` / intención

- Informe externo confirmado: `sha256:{{REPORT_SHA256}}`.
- Decisión estructurada: `sha256:{{DECISION_SHA256}}`.
- Alcance y cobertura confirmados: sí.
- Coincidencias confirmadas: {{MATCHES}}.
- Contradicciones: {{CONTRADICTIONS_SUMMARY}}.
- Desconocidos: {{UNKNOWNS_SUMMARY}}.

La reconciliación confirma un punto de partida documental; no certifica homologación, seguridad, cumplimiento ni adecuación universal.
