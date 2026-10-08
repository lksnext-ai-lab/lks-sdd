# Recorrido integral 3.1

La política del proyecto activa este recorrido explícitamente. Instalar el plugin
no modifica un consumidor. El candidato actual exige el corte confirmado a 3.1 y
runtime compatible antes de seguir escribiendo; consultar no migra. Véase
[migración y continuación](V3-MIGRATION.md).

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

Para presentar cada decisión, use [la guía por familias](USER-DECISIONS.md).
Los campos exactos están en [la referencia de operaciones](V3-OPERATIONS.md); lea
solo el bloque aplicable. La misma respuesta puede cubrir decisiones compatibles
sobre contenido ya mostrado y conservar sus efectos separados. Un cambio material
requiere nuevas conformidades afectadas; editar código no reabre por sí solo un
encargo vigente. Rechazar un resultado no amplía alcance; resolver el defecto no
sustituye aceptación nueva. Las reservas y revisiones no requeridas conservan su
significado, sin acreditar firmas ausentes. Un reintento vigente no duplica eventos.
