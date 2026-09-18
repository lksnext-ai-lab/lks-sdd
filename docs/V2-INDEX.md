# Documentación de LKS-SDD 2

Versión del plugin: **2.0.2**. Empieza por [instalación](INSTALLATION.md),
[compatibilidad](COMPATIBILITY.md) y [notas de release](releases/v2.0.2.md).
La autorización de publicación no sustituye los ensayos humanos/host pendientes.

| Conjunto | Fuente y propósito |
|---|---|
| Contrato | [Contrato 2.0](../specs/proposed/project-contract-2.0.md): semántica normativa y decisiones aprobadas para implementar |
| Guías de uso | [Workflows](V2-WORKFLOWS.md), [consultas](PROJECT-QUERY.md) y [variantes](PROJECT-VARIANTS.md) |
| Referencia técnica | `python scripts/lks_sdd.py v2 --help`, schemas y pruebas de invariantes en tests/test_v2_* |
| Mantenimiento | [Migración](V2-MIGRATION.md), [validación](VALIDATION.md) y [distribución](DISTRIBUTION.md) |
| Evidencia de versión | [Estado de implementación](validation/v2-implementation.md), [cobertura](plans/2026-09-18-lks-sdd-v2-coverage.md) y aceptación por host |

Los documentos 0.x/1.x son referencia histórica o workflow de consumidores sin
migrar, no reglas que sobreescriban el contrato 2.0. Las fuentes originales de
specs/canonical/ permanecen intactas. El plan y su matriz no acreditan ejecución.

Los corpus de investigación de compilación de contexto permanecen en el repositorio
de mantenimiento, fuera del runtime instalado. No son dependencias operativas ni
evidencia de certificación; su exclusión del paquete conserva rutas compatibles
con Windows sin modificar ni eliminar los originales.
