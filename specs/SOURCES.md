# Procedencia de las especificaciones canónicas

Las tres fuentes originales de `specs/canonical/` se incorporaron de forma aditiva el 19 de agosto de 2026 y permanecen inmutables. El 20 de agosto de 2026 se añadieron dos fuentes, también aditivas: la extensión de definición y diseño visual 0.6 y el contrato documental y de handoff 1.1. El 21 de agosto de 2026 se añadió el contrato 1.2 de gobierno de entrega, perfiles multiperfil y tareas. El 22 de agosto de 2026 se añadió la extensión 1.3 de planificación integral y continuidad. Ninguna reescribe retrospectivamente las fuentes anteriores.

| Archivo versionado | SHA-256 |
|---|---|
| `LKS-SDD_definicion_plugin_v1.md` | `4DE2D0AE75B2FF75BBC0C38D05C38AC2D90B57EA4472D46A85BF33C597D79700` |
| `LKS-SDD_paquete_preimplementacion_v0.1.md` | `A5FFD0D5CA1D9B7AC96D1DABB4A411739E18A01345348D9250F857D5F941504B` |
| `LKS-SDD_baseline_normativa_candidata_v0.1.md` | `083DED8FB14D77D899CB4F955AEA67D9A21FBA66AC25D7CF28D8C5111C1D1162` |
| `LKS-SDD_extension_definicion_visual_v0.1.md` | `ABA2B063A31192D5971CE9DC05323405BF7655737076AC924011E77E2C15ACA3` |
| `LKS-SDD_extension_contrato_documental_v1.1.md` | `84CEAA4C5243B2942CAA0EDE9288173A603E12640645C6D1E0C2915DED3B0C7D` |
| `LKS-SDD_extension_gobierno_entrega_perfiles_tareas_v1.2.md` | `45EB724665ACC88913775EC56A9F0D4DD2F07579D7E6674C8E479A2D29790C53` |
| `LKS-SDD_extension_planificacion_continuidad_v1.3.md` | `1CE7721E3B75DF475572DDEEB451243B13EC5D1F0FCDEA0E3780E16327263942` |

La definición funcional y arquitectónica gobierna el propósito y los límites generales del producto. El paquete de preimplementación concreta contratos, M0–M1 y evals. La baseline normativa aporta reglas candidatas y no se interpreta como política aprobada. La extensión visual concreta, para el alcance 0.6, la entrevista inicial, la cobertura y el ciclo condicional con ImageGen. La extensión 1.1 gobierna la ontología por tabla, la gramática de referencias, el grafo activo, la aplicabilidad por dominio, el handoff y la compatibilidad 1.0. La extensión 1.2 gobierna modelos de entrega, planes, releases, tareas, unidades desplegables, bindings, soporte estricto y evidencia de G2–G4. La extensión 1.3 gobierna cobertura integral, autorización delimitada, ejecuciones, checkpoints y cambio vivo; no altera el estado normativo de las fuentes anteriores.

## Extensión propuesta para evaluación candidate

`specs/proposed/LKS-SDD_extension_tracking_operativo_v1.4.md` documenta la propuesta 1.4 de selección del backend de seguimiento y proyección operativa opcional en Jira mediante Atlassian Rovo. `specs/proposed/LKS-SDD_extension_reporting_jira_v1.5.md` (`SHA-256 E8A711DDAECF51491D7CFB85D84097157C9CC5039218573E9A77BFEBBF0A5A98`) añade reporting opcional por hitos, mappings de workflow explícitos, una confirmación por preview y recibos separados. Ambas son **no canónicas**: no forman parte del inventario anterior, no modifican sus hashes y no se presentan como política corporativa aprobada. La implementación 0.11.0 las usa como contratos candidate evaluables; una eventual promoción exigiría una decisión metodológica separada y una incorporación canónica explícita, sin reescribir ninguna fuente previa.

Si una futura revisión detecta una contradicción material que no pueda resolverse con esta jerarquía y el alcance específico de la extensión, debe detener el cambio y solicitar una decisión concreta. Una diferencia entre implementación y contrato se corrige en la implementación; nunca reescribiendo retrospectivamente una fuente canónica.
