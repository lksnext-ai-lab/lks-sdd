# Presentar el plan y su ejecución

Explique objetivo y entregables; tareas y responsables; orden y dependencias;
criterios y pruebas; alcance de ejecución; riesgos y pendientes. Para cada tarea
muestre el resultado esperado, su porción y contratos compartidos. Una lista de IDs
o el número de archivos no basta. Indique entorno, rama/base y límites de efectos
externos sin confundir aprobación del plan con autorización para publicar.

Use fuentes `plan`, sus tareas y obligaciones relacionadas. Compruebe cobertura
completa, dependencias tipadas y tarea de integración cuando corresponda. Una
dependencia contractual no equivale a una implementación o prueba terminada.

Prepare `decision-view` para `authorize-plan` con `actor`, `plan` y `review_tasks`
solo para tareas propias cuyo detalle se presente. La respuesta puede aprobar el
plan, autorizar su ejecución y revisar esos encargos a la vez. Lea
[encargos](assignments.md) cuando se active esa combinación. Los registros conservan
cada efecto por separado. Para aprobar únicamente un plan, use la finalidad `plan`
de `approve`; no convierta esa respuesta en permiso de ejecución.

Si el plan o permiso ya está vigente, reutilícelo y continúe las tareas cubiertas.
Si cambia una dependencia o límite material, reevalúe la parte afectada; no añada
preguntas por registrar los mismos datos. No autorice planes aún no presentados.
