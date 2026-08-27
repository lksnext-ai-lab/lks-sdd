---
artifact_id: ART-ADOPT-INVENTORY
artifact_type: repository-inventory
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.13.0"
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

# Inventario del repositorio

| Aspecto | State | Hallazgo | Fuente | Naturaleza | Confianza | Limitaciones |
|---|---|---|---|---|---|---|
| Archivos | fact | {{FILES_INVENTORIED}} archivos inventariados | inventario estático | hecho | alta | Limitado al alcance confirmado |
| Manifiestos | fact | {{MANIFESTS}} | nombres de archivo | observación | alta | No demuestra uso en producción |
| Tecnologías | assumption | {{SOURCE_EXTENSIONS}} | extensiones observadas | inferencia | media | Requiere reconciliación humana |
| Sensibles | fact | {{SENSITIVE_COUNT}} rutas excluidas por posible sensibilidad | metadatos de ruta | hecho | alta | No se leyeron ni reprodujeron valores |

El detalle provisional permanece en el informe externo confirmado; este artefacto conserva únicamente el resumen saneado.
