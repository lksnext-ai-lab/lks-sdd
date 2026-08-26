# Sincronización Jira durante implementación

Aplica únicamente a tareas cuyo `ART-TRACKING` tenga `jira-hybrid` confirmado y un mapping Jira inequívoco. Markdown, `AUTH-###`, `EXEC-###`, `CKPT-###` y los estados de tarea locales siguen siendo autoritativos.

## Antes de implementar

La autorización de implementación permite el cambio local acotado; no permite leer ni escribir Jira.

Si el usuario autoriza una lectura externa en la tarea actual:

1. Lee solo los work items mapeados a la slice autorizada.
2. Comprueba proyecto, `TASK-###`, fingerprint proyectado y campos gobernados.
3. Si Jira cambió campos gobernados, informa del conflicto y detén la sincronización externa. No importes el cambio como requisito ni reescribas Markdown.

Con `Sync policy=required-before-execution`, la slice no empieza mientras su evaluación local de tracking no sea `in-sync`. Una indisponibilidad posterior no invalida una ejecución local ya iniciada ni sus checkpoints.

## Orden de escritura

1. Aplica primero el preview local autorizado.
2. Persiste la transición canónica, `EXEC-###` y el `CKPT-###` correspondiente.
3. Si cambió algún campo gobernado, ejecuta `preview-sync` para una única `--task` y obtén la operación `update`, payload, marker, fingerprint y hash exactos.
4. Con lectura Rovo autorizada, confirma que la identidad mapeada y el marker namespaced `LKS-SDD-PROJECT: <project_id>; TASK: TASK-###` coinciden de forma inequívoca; `update` exige `duplicate-check=matched`.
5. Ejecuta `authorize-sync --apply` para el preview exacto y persiste el `SYNC-###` autorizado antes de escribir.
6. Ejecuta únicamente ese update mediante Rovo y relee el work item.
7. Cierra el recibo con `record-result --sync-id SYNC-### --apply`. Un `succeeded` exige el marker exacto, la `projection_fingerprint` observada, `external_id`, key y URL; el resultado solo actualiza tracking, no la TASK.

El contrato local inicial previsualiza y registra creación o actualización de la proyección, no transiciones de workflow. No transiciones Jira desde esta skill mientras la versión instalada no pueda incluir esa operación en un preview determinista y registrar su recibo. No asumas nombres de estados ni IDs de transición.

## Operaciones permitidas

La sincronización inicial puede actualizar los campos gobernados definidos durante planificación. No debe:

- transicionar estados Jira sin soporte durable de preview y recibo;
- asignar personas automáticamente;
- registrar worklogs;
- publicar comentarios, evidencias o rutas sensibles sin petición expresa;
- sobrescribir sprint, prioridad, estimación, fechas o campos gestionados por el equipo Jira;
- crear un work item nuevo durante implementación sin volver al contrato de planificación y su comprobación de duplicados.

## Fallos y reanudación

Una indisponibilidad, permiso denegado o actualización fallida no revierte código, tareas, `EXEC-###` ni `CKPT-###`. Cierra el `sync_id` como `failed`, `conflict` o `uncertain` según el resultado real y entrega la siguiente comprobación de lectura segura.

Si el resultado externo es incierto o conflictivo, no repitas la operación. Relee con autorización y usa `reconcile-result --anchor-sync-id <Last-operation-cerrado>` para registrar el hecho observado, incluso si el plan derivó; un éxito exige el marker exacto y una huella igual al ancla o al plan actual, y permite cambiar la key solo con el mismo `external_id` y el prefijo del proyecto confirmado. Si coincide con el ancla pero no con el plan actual, queda `out-of-sync`. Si sigue siendo ambiguo, conserva `conflict`/`uncertain`. Reconciliar no habilita cambiar o abandonar el binding durable, porque 0.10.0 no ofrece `detach`/`rebind`. Jira no puede convertirse en una fuente alternativa de continuidad cuando el checkpoint local es válido.

No proyectes una ficha `confidential`/`restricted`, secretos ni datos personales detectables. No persistas URLs con credenciales, query o fragmento.
