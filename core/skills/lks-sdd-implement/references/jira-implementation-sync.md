# Reporting Jira durante la implementación

Aplica solo cuando `ART-TRACKING` confirma `jira-hybrid`. Markdown, `AUTH-###`, `EXEC-###`, `CKPT-###`, `PROB-###` y los estados TASK son autoritativos. Atlassian Rovo es el compañero opcional que realiza lecturas y escrituras; el plugin LKS-SDD solo construye intenciones deterministas y recibos locales.

## Dos capas independientes

- La proyección mantiene título, descripción y fingerprint con `preview-sync`, `authorize-sync`, `record-result` y `reconcile-result`.
- El reporting de hitos existe solo si `RPT-###` confirma `milestone-reporting`. Usa `preview-event`, `authorize-event`, `record-event-result` y `reconcile-event`.

`projection-only`, `repository-only` o reporting `paused` no publican comentarios ni transiciones. En `repository-only` no solicites Atlassian y continúa con toda la experiencia local.

## Hitos de implementación

Un `CKPT-###` se valida semánticamente: ruta canónica, archivo regular sin symlink/junction, frontmatter YAML con `artifact_id` y `artifact_type`, y una identidad única cuya TASK y EXEC coinciden con el índice. Las formas YAML equivalentes con o sin comillas son iguales. Un evento `blocked` exige el `PROB-###` abierto de esa misma TASK; el problema creado por `tasks transition --to blocked` queda disponible inmediatamente, pero `resolved`, otra TASK o una identidad inexistente fallan cerrado.

Publica únicamente eventos significativos ya durables:

| Event kind | Estado local requerido | Fuente canónica habitual |
|---|---|---|
| `started` | `in-progress` | `EXEC-###` |
| `progress` | `in-progress` | `CKPT-###` |
| `blocked` | `blocked` con problema abierto | `PROB-###` o `CKPT-###` |
| `resumed` | `in-progress` | `CKPT-###` |
| `in-review` | `in-review` | `CKPT-###` |

No comentes cada archivo, comando, test o mensaje de chat. El comentario saneado incluye estado, progreso, salud, fuente, checkpoint, bloqueos, evidencia referenciada y siguiente acción segura. No incluye logs completos, secretos, datos personales, rutas absolutas, worklogs, estimaciones ni conversaciones.

## Secuencia de producto

1. Completa primero la transición local y su `EXEC/CKPT/PROB`.
2. Ejecuta `preview-event` para una TASK, fuente y event kind exactos. La salida siempre propone un comentario y, solo si existe mapping de workflow confirmado, una transición.
3. Mediante una lectura Rovo autorizada, busca el `LKS-SDD-EVENT` exacto, confirma la identidad del work item y observa estado/transiciones disponibles. Cero comentarios coincidentes es `comment-check=no-match`; una coincidencia hace la operación idempotente y no se autoriza otra escritura.
4. Presenta el preview completo. Una única confirmación humana del `preview_hash` autoriza ese hito como unidad.
5. `authorize-event --apply` persiste antes de escribir un `SYNC-###` independiente por comentario y transición. No ejecuta Jira.
6. Ejecuta cada operación mediante Rovo y relee el resultado. Cierra cada recibo por separado con `record-event-result`. El comentario exige marker observado exacto; la transición exige el status ID objetivo observado.

La transición solo es válida si `configure-workflow` dejó confirmado el estado local con un Jira status ID numérico observado y el preflight fresco proporciona el transition ID exacto. No infieras IDs por nombres, no transiciones a un estado no mapeado y no reutilices IDs de otro proyecto.

## Fallos, pausa y gates

Con `Coordination gate=advisory`, un Jira no disponible, reporting pausado o recibo fallido se informa como degradación operativa y el trabajo local válido continúa. Con `required-before-execution`, respeta el bloqueo configurado para comenzar o reanudar la ejecución seleccionada, sin convertir Jira en autoridad técnica.

`pause-reporting` y `resume-reporting` requieren preview/hash/apply y no se permiten mientras exista una operación de hito `authorized/pending`. Pausar nunca borra recibos ni invalida código o checkpoints.

Ante timeout o resultado incierto, registra `uncertain`; no repitas el write. Realiza una lectura Rovo autorizada y añade un recibo con `reconcile-event --anchor-sync-id`. La reconciliación es append-only. Si la observación sigue siendo ambigua, conserva `conflict` o `reconciliation-required`.

No reasignes, borres, archives, registres worklogs ni modifiques campos fuera de la proyección gobernada. Un recibo Jira nunca cambia por sí mismo la TASK, autorización, evidencia o dependencia local.
