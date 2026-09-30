# Recorrido integral 3.1

La política del proyecto activa este recorrido explícitamente. Instalar el plugin
no modifica un consumidor. Proyectos 3.0 mantienen su método; nunca asuma una migración.

## Hitos y personas

| Hito | Resultado | Intervención |
|---|---|---|
| H1 | Propuesta concreta preparada. | Aclaraciones necesarias, sin firma de borrador. |
| H2 | Propuesta integral revisada y cerrada. | Una conformidad por persona requerida; responsable y revisor pueden decidir juntos. |
| H3 | Plan detallado aprobado y ejecución autorizada. | Presentar el plan; agrupar aprobación, autorización y revisión de tareas propias explícitas. |
| H4 | Encargo revisado por su ejecutor. | Solo si no lo cubre una decisión vigente. Agrupar varias tareas de la misma persona. |
| H5 | Tareas implementadas, verificadas y cerradas. | Evidencia/pruebas; revisión humana solo cuando corresponda. |
| H6 | Integración comprobada y resultado funcional aceptado. | Una revisión final conjunta si es la misma persona y dispone de evidencia, conservando ambos resultados. |
| H7 | Información de entrega al PR preparada. | No requiere otra firma SDD; abrir/publicar requiere autorización de sesión. |

Un hito no es una pregunta. Use la misma identidad estable aunque una persona cubra
varias especialidades. En un recorrido individual normal son tres momentos: propuesta,
plan y resultado; las aclaraciones o pruebas manuales necesarias siguen aplicándose.
No invente otro revisor si el proyecto exige independencia: explique el impedimento.

## Consultar y continuar

`interventions` recibe request, actor opcional, offset/limit y object_offset. Devuelve
hitos, intervenciones agrupadas, acciones automáticas y causas; los objetos están
paginados. El resumen no sustituye la lectura del contenido exacto que se va a validar.
`status` añade journey y pagina tareas con task_offset/task_limit. `readiness` de una
tarea comprueba la transición y devuelve el mismo recorrido del actor.

Al terminar, explique qué se completó, dónde queda la petición y qué falta. Si el
siguiente trabajo está autorizado y preparado, continúe; no pida permiso para
registrar una transición técnica acreditada. Cada persona firma únicamente por sí.

## Configuración explícita

`configure-collaboration`: actor, statement, collaboration y requests opcionales.
collaboration contiene proposal_review_required y task_review_required (booleanos),
y defaults con responsible, integration_validator, functional_validator (UID de
miembros) y reviewers [{member, required, domains}]. Se deduplican personas, no roles.
El campo coordination opcional aplica una designación específica a las peticiones
seleccionadas. El motivo y las designaciones deben proceder de una decisión explícita.

La operación actualiza formato/método a 3.1/3.1.0, conserva las reglas fijadas de
peticiones no seleccionadas y no fabrica revisiones históricas. Con runtime fijado
requiere runtime_bundle compatible; la vista previa incluye el corte del runtime y
documentos. apply/recover/rollback conservan el mecanismo transaccional existente.

## Revisión y ejecución

- `review-comment`: actor, request, target, statement, blocking y critical.
- `resolve-comment`: actor, request, comment, statement y treatment
  incorporated/dismissed. El autor de una objeción confirma su tratamiento al revisar.
- `review-proposal`: actor, request, statement, outcome approved/changes-requested.
- `close-proposal`: actor, request, statement, review opcional. review=true registra
  conjuntamente la revisión propia y el cierre cuando faltaba solo esa conformidad.
- `authorize-plan`: admite review_tasks con los UID exactos de tareas propias
  presentadas y revisadas por esa misma respuesta. Omitirlo no inventa revisión.
- `review-task`: actor, request, tasks, statement, outcome approved/changes-requested.
- `start`/`resume`: review=true agrupa revisión e inicio; offer permite aceptar una
  oferta de asignación/relevo del destinatario en el mismo paquete recuperable.
- `review-exception`: actor competente, request, statement, rule integral-review,
  action close-proposal, effect y expires_at. Mantiene reservas y firmas ausentes.

Un cambio material del paquete requiere conformidades nuevas. Las tareas conservan
su revisión mientras no cambie el contrato, destinatario o porción; editar código
durante la implementación no obliga a revisar de nuevo el encargo.

## Resultado y correcciones

`integrate` conserva trusted_root y admite accept_result=true si la misma persona
puede comprobar integración y aceptar funcionalmente el candidato ya presentado.
Las dos acreditaciones se conservan; no se realiza merge.

`reject-result`: actor, request, statement, phase integration/acceptance/external,
tasks, expected, observed, artifact y requirements opcionales. Registra fallo y
definición correctiva en borrador, incluso antes de poder cerrar la integración.

`define-correction`: actor, correction, classification defect/agreement-change/
new-request/external, statement, acceptance y tasks/requirements opcionales.
Confirmar el defecto no autoriza otro alcance. Reabra trabajo cubierto por la
autorización vigente o revise propuesta/plan antes de ampliar el encargo.

`resolve-defect`: actor, problem, statement; exige definición confirmada y evidencia
de corrección vigente. Después repita integración/aceptación del nuevo resultado.
`prepare-delivery`: actor, request, statement, pr_url opcional observado. Requiere
aceptación vigente; preparar el resumen no crea ni aprueba el PR, ni ejecuta CI/CD.

Las operaciones de revisión, rechazo, definición/resolución correctiva y entrega admiten
refresh cuando el proyecto exige comprobar referencias compartidas. Los resúmenes
muestran completed-with-reservations para cierres dispensados y not-required para
revisión de encargos desactivada: ninguno acredita una firma ausente. Un reintento
de revisión o cierre vigente devuelve already-recorded, sin duplicar eventos.
