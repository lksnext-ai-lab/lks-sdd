# Revisión integral de equipo: propuesta validada

Paquete: **integral-review-02**. Fecha: 2026-09-29.
Estado: **propuesta integral-review-02 validada y autorizada para implementación local mediante «implementalo», 2026-09-29**.

El usuario confirma: «esta definición de hitos del proceso es correcta y debe quedar
claramente documentada». También exige que LKS-SDD guíe el recorrido y no solicite
eventos equivalentes varias veces a la misma persona. Esta confirmación no se
extiende automáticamente a todas las decisiones técnicas de la revisión anterior.

Se conserva [integral-review-01](history/integral-review-01/REVIEW.md). La revisión
02 mantiene los hitos y concreta su adaptación a personas reales. El plan autorizado está en `docs/plans/integral-review/PLAN.md`.

## Qué se propone

Un responsable prepara la propuesta, coordina su revisión integral con los
especialistas y cierra una versión concreta. Después genera el plan detallado.
Cada técnico revisa el encargo recibido, lo ejecuta y verifica su implementación.
Una persona designada valida el conjunto antes del PR. Si lo rechaza, queda una
definición concreta de las correcciones vinculada a la petición original.

El plugin comprobará este recorrido, además de explicarlo. Seguirá admitiendo una
sola persona, equipos distintos y excepciones justificadas. No se añaden reuniones,
chats ni firmas por cada registro.

La regla central pasa a ser comprobable: **los hitos describen resultados del proceso;
las intervenciones se agrupan por persona, contenido y autoridad**. Un hito no exige
por sí mismo otra pregunta. El plugin acredita cada resultado mediante evidencia,
una decisión vigente o una decisión conjunta explícita, según corresponda.

## Revisión crítica y cambios de esta versión

| Debilidad de la revisión 01 | Mejora en la revisión 02 |
|---|---|
| Permitía agrupar decisiones, pero dejaba esa agrupación a criterio del agente. | Regla predeterminada de agrupación por identidad real, con límites deterministas y controles en el núcleo. |
| Enumeraba perfiles, pero no resolvía que una persona ocupe varios. | Participantes efectivos deduplicados por UID; no una firma por etiqueta de especialidad. |
| Podía obligar al autor del plan a aceptar de nuevo sus propias tareas. | Su aprobación explícita del detalle de las tareas propias cubre su revisión del encargo; no se crea un relevo a sí mismo. |
| No distinguía suficientemente hito, evento técnico y pregunta al usuario. | Catálogo de hitos con evidencia y condiciones, separado de la presentación de intervenciones. |
| No concretaba cuánto se simplifica el recorrido individual. | Caso normal con tres momentos de decisión sobre contenidos distintos: propuesta, plan y resultado; sin preguntas administrativas intermedias. |
| La orientación al completar cada paso podía producir mensajes repetitivos. | Un resumen por avance significativo o grupo de hitos, con siguiente acción concreta; continuar si ya está autorizado. |
| La adaptación podía interpretarse como rebajar revisión independiente. | No se elimina separación de funciones por tener pocas personas; se explica la incompatibilidad y las opciones de gobierno. |

La [matriz de configuraciones y reglas](functional.md#61-hitos-e-intervenciones-son-conceptos-distintos)
y el [cálculo de intervenciones](technical.md#61-cálculo-determinista-de-intervenciones)
concretan estos cambios.

## Documentos que forman esta revisión

- [Propuesta funcional](functional.md): participantes, proceso, decisiones,
  correcciones, flexibilidad, experiencia y criterios de aceptación.
- [Propuesta técnica](technical.md): datos, controles, operaciones, vigencia,
  compatibilidad, eficiencia y límites de la solución.

Este paquete amplía v3.0.0; no sustituye sus documentos históricos ni modifica
`specs/canonical/`. No es un plan de implementación ni una aprobación de release.

## Decisiones concretas validadas

| Decisión propuesta | Efecto que se valida |
|---|---|
| Revisión integral por participantes designados para cada petición. | Todos los revisores obligatorios deben pronunciarse sobre el mismo contenido vigente antes del cierre. No se exige siempre Frontend, Backend y BBDD. |
| Cierre y planificación coordinados por el responsable. | Consolida aportaciones, cierra la propuesta y prepara el plan con el agente; las objeciones obligatorias no se descartan en silencio. |
| Revisión del encargo antes de ejecutarlo. | El técnico confirma que comprende la tarea y sus dependencias; la mera asignación no permite omitir este paso. |
| Validación técnica y funcional del conjunto antes del PR. | Pueden corresponder a una misma persona habilitada, pero requieren evidencias y decisiones distintas. |
| Correcciones explícitas y proporcionadas. | Se documenta el resultado esperado y el fallo; se reabre trabajo autorizado o se revisa propuesta/plan si cambia el acuerdo. |
| Configuración y excepciones trazables. | Se conserva el recorrido individual; cambiar reglas no concede aprobaciones retroactivas ni convierte fallos en éxitos. |
| Actualización documental explícita a formato 3.1. | Los proyectos 3.0 continúan sin cambios; un runtime antiguo no puede ignorar los nuevos controles. La versión comercial de la siguiente release se decidirá después. |
| Núcleo compartido y contexto limitado por operación. | Se mantienen seis skills, Markdown canónico, consultas paginadas y referencias recuperables; no se crean servicios, agentes ejecutables ni conectores. |
| Agrupación automática por personas reales. | Una persona con varios roles interviene una vez sobre el mismo contenido compatible; los hitos siguen acreditados por separado. |
| Reutilización de la revisión de tareas propias. | Aprobar el detalle de las tareas propias puede acreditar su revisión sin pedir una nueva aceptación administrativa. |

## Alcance de la autorización recibida

Tras revisar integral-review-02, el usuario ha indicado «implementalo» el
2026-09-29. Esta instrucción valida la propuesta y autoriza preparar su plan,
implementar localmente y ejecutar sus comprobaciones. No se extiende a commits,
push, publicación, instalación en consumidores ni apertura de un PR remoto.

## Situación de la revisión

- Base contrastada: plugin 3.0.0, commit
  `0124fdb4927e04b2fbc773e36d2073e7e962a544`.
- Hitos, adaptación funcional y diseño técnico: validados para implementación local.
- Plan y seguimiento: [PLAN.md](../../../docs/plans/integral-review/PLAN.md).
- La evidencia de implementación se registra en el plan; las comprobaciones locales
  no acreditan aceptación humana de Codex/Copilot ni publicación de una release.
