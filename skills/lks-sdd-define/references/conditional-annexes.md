# Anexos condicionales

Materialice un anexo únicamente cuando su aplicabilidad esté confirmada. Antes de escribir, muestre la ruta, el motivo y cualquier colisión; preserve contenido existente y añada el nuevo artefacto al índice operativo. Sustituya todos los tokens de la plantilla y valide después el proyecto.

| Preocupación aplicable | Ruta canónica sugerida | Plantilla empaquetada |
|---|---|---|
| Stakeholders y usuarios detallados | `01-context/stakeholders-and-users.md` | `assets/templates/01-context/stakeholders-and-users.md` |
| Arquitectura detallada | `03-solution/architecture.md` | `assets/templates/03-solution/architecture.md` |
| Datos, migración y retención | `03-solution/data.md` | `assets/templates/03-solution/data.md` |
| APIs e integraciones | `03-solution/integrations.md` | `assets/templates/03-solution/integrations.md` |
| Seguridad, privacidad e identidad | `03-solution/security-privacy-identity.md` | `assets/templates/03-solution/security-privacy-identity.md` |
| UX y accesibilidad | `03-solution/ux-accessibility.md` | `assets/templates/03-solution/ux-accessibility.md` |
| Roadmap de varios incrementos | `04-delivery/roadmap.md` | `assets/templates/04-delivery/roadmap.md` |
| Estrategia de pruebas detallada | `05-quality/test-strategy.md` | `assets/templates/05-quality/test-strategy.md` |
| Despliegue e infraestructura | `06-operation/deployment.md` | `assets/templates/06-operation/deployment.md` |
| Observabilidad | `06-operation/observability.md` | `assets/templates/06-operation/observability.md` |
| Operación, continuidad y recuperación | `06-operation/operations.md` | `assets/templates/06-operation/operations.md` |

Para una decisión arquitectónica individual, use `assets/templates/03-solution/decisions/decision-record.md`, asigne un `ADR-###` estable y guarde el documento bajo `03-solution/decisions/`. Registre cada `ADR-###` en una sola tabla estructural para evitar duplicados y enlace el resto por referencia. No convierta la propuesta de la plantilla en una decisión confirmada.

Costes, licencias y cumplimiento pueden registrarse en `ART-CONSTRAINTS` mientras el volumen sea manejable. Cree un anexo específico solo si mejora la decisión o la auditabilidad. Los entregables de cliente son vistas derivadas y permanecen fuera de M1.
