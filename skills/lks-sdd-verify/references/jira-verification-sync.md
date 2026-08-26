# Reporting Jira después de verificar

La verificación y su evidencia se producen localmente. Jira solo refleja un resultado ya durable; nunca demuestra que un gate se ejecutó ni autoriza `done`.

## Hitos de verificación

Con `jira-hybrid` y `RPT-###` en `milestone-reporting`:

| Event kind | Condición local | Fuente |
|---|---|---|
| `verification-pending` | TASK `in-review`; verificación aún pendiente | `CKPT-###` |
| `verification-failed` | TASK `in-review`; evidencia ejecutada no supera gates | `EVID-###` |
| `done` | TASK `done`; manifest `verification.status=verified` para la TASK | el `EVID-###` exacto |

`not-run`, `blocked`, `not-verified`, evidencia incompleta o `verified-with-reservations` nunca se convierten en una transición Jira a Done-equivalente. Un Jira ya marcado Done tampoco permite fabricar evidencia local.

## Secuencia obligatoria

1. Ejecuta y registra primero los gates, `EVID-###`, checkpoint y transición TASK canónicos.
2. Mantén la proyección de campos gobernados por su flujo separado si ha cambiado.
3. Genera `preview-event` para una sola TASK y fuente exacta. `done` falla cerrado si el manifest no enlaza la evidencia verified.
4. Con lectura Rovo autorizada, verifica identidad, ausencia del marker exacto y, si hay mapping de workflow, status ID actual y transition ID disponible.
5. Presenta comentario y transición opcional como una unidad. Una confirmación del `preview_hash` es suficiente para el hito, pero `authorize-event` registra un `SYNC-###` por operación antes de cualquier escritura.
6. Ejecuta las operaciones mediante Rovo, relee Jira y cierra cada recibo de forma independiente con `record-event-result`.

Los comentarios son resúmenes saneados: no copies logs, secretos, datos personales, rutas absolutas o artefactos inaccesibles. No registres worklogs, no reasignes, no borres y no archives.

## Fallo externo

Un fallo Jira no invalida gates, fingerprints, evidencia o TASK local. Registra `failed`, `conflict` o `uncertain` según el hecho observado. No repitas un resultado incierto: realiza una lectura autorizada y usa `reconcile-event --anchor-sync-id`; la resolución queda como un nuevo recibo append-only. Con gate `advisory`, entrega la verificación local y señala la degradación. Con gate `required-before-execution`, aplica únicamente la coordinación previamente confirmada sin reescribir la evidencia.
