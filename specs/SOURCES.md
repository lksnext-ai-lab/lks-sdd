# Procedencia de las especificaciones canónicas

Las tres fuentes originales de `specs/canonical/` se incorporaron de forma aditiva el 19 de agosto de 2026 y permanecen inmutables. El 20 de agosto de 2026 se añadió una cuarta fuente, también aditiva, para registrar la evolución confirmada de definición y diseño visual de la versión 0.6.0 sin reescribir el contrato anterior.

| Archivo versionado | SHA-256 |
|---|---|
| `LKS-SDD_definicion_plugin_v1.md` | `4DE2D0AE75B2FF75BBC0C38D05C38AC2D90B57EA4472D46A85BF33C597D79700` |
| `LKS-SDD_paquete_preimplementacion_v0.1.md` | `A5FFD0D5CA1D9B7AC96D1DABB4A411739E18A01345348D9250F857D5F941504B` |
| `LKS-SDD_baseline_normativa_candidata_v0.1.md` | `083DED8FB14D77D899CB4F955AEA67D9A21FBA66AC25D7CF28D8C5111C1D1162` |
| `LKS-SDD_extension_definicion_visual_v0.1.md` | `ABA2B063A31192D5971CE9DC05323405BF7655737076AC924011E77E2C15ACA3` |

La definición funcional y arquitectónica gobierna el propósito y los límites generales del producto. El paquete de preimplementación concreta contratos, M0–M1 y evals. La baseline normativa aporta reglas candidatas y no se interpreta como política aprobada. La extensión v0.1 concreta, para el alcance de definición y UX de la versión 0.6.0, la entrevista inicial, los snapshots de cobertura y el ciclo visual condicional con ImageGen; no altera el estado normativo de las fuentes anteriores.

Si una futura revisión detecta una contradicción material que no pueda resolverse con esta jerarquía y el alcance específico de la extensión, debe detener el cambio y solicitar una decisión concreta. Una diferencia entre implementación y contrato se corrige en la implementación; nunca reescribiendo retrospectivamente una fuente canónica.
