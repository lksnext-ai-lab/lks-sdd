# Readiness con proyección Jira opcional

Jira es una dimensión operativa separada. La evaluación normativa se deriva siempre del índice y del Markdown canónico antes de considerar la proyección externa.

## Orden de evaluación

1. Ejecuta y revisa la evaluación local completa.
2. Valida `ART-TRACKING` y confirma el único binding `TRK-###` del proyecto, su modo y políticas.
3. Evalúa offline si cada tarea necesita `create`, `update`, `noop` o está bloqueada por reconciliación.
4. Solo si el usuario autoriza una lectura Jira en la tarea actual, consulta los work items mapeados y sus campos gobernados.
5. Compara sin modificar ninguno de los dos lados.

El modo previamente confirmado no es por sí solo autorización para leer datos externos en una conversación nueva.

## Resultado separado

Reporta `task_tracking` con el estado local 1.4 aplicable:

- `decision-required`: el modo sigue pendiente;
- `not-assessed`: el plan local de la selección no está confirmado, íntegro y vigente, por lo que todavía no existe una proyección evaluable;
- `not-required`: se confirmó `repository-only`;
- `pending`: alguna tarea necesita creación;
- `out-of-sync`: alguna tarea necesita actualización;
- `in-sync`: todas las tareas seleccionadas producen `noop` con mappings válidos;
- `reconciliation-required`: mapping ambiguo o resultado externo previo incierto.
- `invalid`: `ART-TRACKING`, su índice o sus recibos incumplen el contrato.

Añade por separado `degraded` o `unavailable` como diagnóstico de la conexión viva cuando corresponda; no lo confundas con el estado offline del contrato. Incluye tareas afectadas, alcance de la lectura, hora de observación si está disponible y limitaciones. No copies descripciones completas, secretos, datos personales ni URLs con query. Las fichas `confidential`/`restricted` no son proyectables.

## Relación con G2

- Jira nunca demuestra cierre de especificación, cobertura completa, resolución de dependencias, autorización, implementación o verificación.
- Un work item en Done no convierte una `TASK-###` local en `done`.
- Un recibo `SYNC-###` succeeded o un cambio de key observado dentro del prefijo confirmado tampoco modifica la TASK, AUTH, evidencia o dependencias canónicas.
- Un Jira inaccesible no invalida fingerprints, evidencia o autorizaciones locales ya válidas.
- Con `Sync policy=required-before-execution`, una tarea seleccionada que no esté `in-sync` bloquea su preparación para ejecución; el binding 1.4 hace esa política explícita.
- Incluso cuando bloquea esa política operativa, conserva y reporta por separado el resultado de todos los demás ejes.

Esta skill no crea, edita, enlaza, comenta, asigna ni transiciona Jira. Ante drift, devuelve el menor paso de lectura y `reconcile-result` necesario, sin ejecutarlo. No presenta la reconciliación como permiso para abandonar/cambiar un binding durable: 0.10.0 no ofrece `detach`/`rebind`.
