# Reporting Jira después de verificar

La verificación y su evidencia se producen localmente. Jira solo refleja un resultado ya durable; nunca demuestra que un gate se ejecutó ni autoriza `done`. Los lectores de CKPT parsean YAML y su identidad TASK/EXEC; no dependen de comillas literales. Los eventos bloqueados solo aceptan un PROB abierto de la misma TASK.

## Hitos de verificación

Con `jira-hybrid` y `RPT-###` en `milestone-reporting`:

| Event kind | Condición local | Fuente |
|---|---|---|
| `verification-passed` | EVID actual `verified` | `EVID-###` |
| `verification-failed` | evidencia ejecutada `not-verified` | `EVID-###` |
| `finding-opened` | hallazgo posterior abierto | `PROB-###` |
| `correction-completed` | corrección durable pendiente de re-verificación | `CKPT-###` |
| `reverification` | EVID nueva `verified` que cierra el ciclo | `EVID-###` |

`not-run`, `blocked`, `not-verified`, evidencia incompleta o `verified-with-reservations` nunca se convierten en una transición Jira a Done-equivalente. Un Jira ya marcado Done tampoco permite fabricar evidencia local.

## Secuencia obligatoria

1. Ejecuta y registra primero los gates, `EVID-###`, checkpoint y transición TASK canónicos.
2. Mantén la proyección de campos gobernados por su flujo separado si ha cambiado.
3. Genera `preview-event` para una sola TASK y fuente exacta. `done` falla cerrado si el manifest no enlaza la evidencia verified.
4. Con lectura Rovo autorizada, verifica identidad, ausencia del marker exacto y, si hay mapping de workflow, status ID actual y transition ID disponible.
5. Presenta comentario y transición opcional como una unidad. Una confirmación del `preview_hash` es suficiente para el hito, pero `authorize-event` registra un `SYNC-###` por operación antes de cualquier escritura.
6. Ejecuta las operaciones mediante Rovo, relee Jira y cierra cada recibo de forma independiente con `record-event-result`.

Cada hito produce como máximo una actualización. El comentario resume TASK, resultado, pruebas ejecutadas, número de imágenes, hallazgos, revisión y próxima acción. Adjunta imágenes solo si el peer lo permite; en caso contrario usa referencias versionadas accesibles y nunca rutas absolutas locales. Los comentarios son resúmenes saneados: no copies logs, secretos, datos personales o artefactos inaccesibles. No registres worklogs, no reasignes, no borres y no archives.

## Fallo externo

Un fallo Jira no invalida gates, fingerprints, evidencia o TASK local. Registra `failed`, `conflict` o `uncertain` según el hecho observado. No repitas un resultado incierto: realiza una lectura autorizada y usa `reconcile-event --anchor-sync-id`; la resolución queda como un nuevo recibo append-only. Con gate `advisory`, entrega la verificación local y señala la degradación. Con gate `required-before-execution`, aplica únicamente la coordinación previamente confirmada sin reescribir la evidencia.
