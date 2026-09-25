# Documentación de LKS-SDD 2

Versión del plugin: **2.3.0**. Empieza por [instalación](INSTALLATION.md),
[compatibilidad](COMPATIBILITY.md) y el [historial de versiones](../CHANGELOG.md).
La autorización de publicación no sustituye los ensayos humanos/host pendientes.

| Conjunto | Fuente y propósito |
|---|---|
| Contrato | [Contrato de proyecto 2.0](../specs/proposed/project-contract-2.0.md): declaraciones tecnológicas locales y corte 1.5 → 2.0 |
| Guías de uso | [Workflows](V2-WORKFLOWS.md), [continuidad SPEC/PLAN/TASK](V2-SPEC-PLAN-TASK.md), [consultas](PROJECT-QUERY.md) y declaración tecnológica local |
| Referencia técnica | `python scripts/lks_sdd.py v2 --help`, schemas y pruebas de invariantes en tests/test_v2_* |
| Mantenimiento | [Migración](V2-MIGRATION.md), [validación](VALIDATION.md) y [distribución](DISTRIBUTION.md) |
| Estado y aceptación | [Estado actual](STATUS.md) y [aceptación por host](V2-HOST-ACCEPTANCE.md) |

La compatibilidad 1.5 se limita al runtime fijado de consumidores no migrados y a su
migración explícita; no sobreescribe el contrato 2.0. Las fuentes originales de
`specs/canonical/` permanecen intactas. La trazabilidad no acredita ejecución.
