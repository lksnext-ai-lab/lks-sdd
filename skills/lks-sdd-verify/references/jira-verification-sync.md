# Sincronización Jira después de verificar

La evidencia LKS-SDD se produce y valida localmente. Jira solo puede reflejar un resultado que ya sea durable en el contrato canónico.

## Secuencia obligatoria

1. Planifica y ejecuta los gates aplicables sin usar Jira como evidencia.
2. Registra el resultado, `EVID-###` cuando proceda, y el checkpoint canónico.
3. Determina el estado local permitido por la evidencia ejecutada.
4. Solo después ejecuta `preview-sync` para una única `--task` y comprueba si los campos gobernados necesitan un `update` Jira.
5. Con lectura Rovo autorizada, exige que identidad y marker coincidan (`duplicate-check=matched`).
6. Persiste `authorize-sync --apply` para el hash exacto antes de escribir; después ejecuta únicamente ese update.
7. Relee el work item y cierra el recibo por `record-result --sync-id`. Un éxito exige marker y fingerprint observados, y no cambia la evidencia ni la TASK canónica.

Una autorización de verificación o promoción no autoriza Jira.

## Reglas de estado

- `not-run`, `failed`, `blocked`, `not-verified` o evidencia incompleta nunca permiten una transición Jira a Done o equivalente.
- `verified-with-reservations` no se convierte automáticamente en Done.
- Solo una `TASK-###` local que pueda pasar legítimamente a `done`, con evidencia exacta y vigente, sería elegible para proyectarse a un estado Jira equivalente.
- Un Jira ya marcado Done no prueba verificación ni permite fabricar `EVID-###`.
- La verificación conjunta de release y la promoción siguen siendo decisiones distintas del estado de sus work items.

El contrato local inicial no genera ni registra previews de transición. Aunque una tarea sea elegible, no transiciones Jira a Done desde esta skill mientras la versión instalada no pueda previsualizar la transición exacta y conservar su recibo durable. No asumas nombres o IDs de workflow.

## Comentarios y datos

El contrato inicial tampoco registra comentarios. No los publiques hasta que exista soporte de preview y recibo para esa operación. Cuando una versión posterior lo soporte y el usuario lo solicite, resume el resultado y enlaza únicamente referencias aprobadas; no copies logs completos, secretos, datos personales, rutas locales sensibles ni artefactos inaccesibles para el destinatario.

No registres worklogs, reasignes usuarios, borres, archives ni modifiques campos fuera del mapping.

## Fallo externo

Un fallo, timeout o permiso denegado en Jira no invalida gates ejecutados, evidencia, fingerprint ni estado local. Cierra el `sync_id` como `failed`, `conflict` o `uncertain`. Ante un resultado incierto/conflictivo, no repitas la operación; realiza una lectura Rovo autorizada y registra `reconcile-result --anchor-sync-id <Last-operation-cerrado>`. Un éxito exige marker exacto y una huella igual al ancla o al plan actual; un cambio de key conserva el mismo `external_id` y el prefijo del proyecto confirmado. Si coincide con el ancla pero no con el plan actual, queda `out-of-sync`; si no puede determinarse, conserva el bloqueo. Reconciliar no habilita cambiar/abandonar el binding durable y 0.10.0 no ofrece `detach`/`rebind`.

No proyectes fichas `confidential`/`restricted`, secretos o datos personales detectables, ni persistas URLs con credenciales, query o fragmento.
