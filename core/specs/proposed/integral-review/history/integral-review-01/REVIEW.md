# Revisión integral de equipo: propuesta para validar

Paquete: **integral-review-01**. Fecha: 2026-09-29.
Estado: **propuesto; pendiente de validación funcional y técnica**.

## Qué se propone

Un responsable prepara la propuesta, coordina su revisión integral con los
especialistas y cierra una versión concreta. Después genera el plan detallado.
Cada técnico revisa el encargo recibido, lo ejecuta y verifica su implementación.
Una persona designada valida el conjunto antes del PR. Si lo rechaza, queda una
definición concreta de las correcciones vinculada a la petición original.

El plugin comprobará este recorrido, además de explicarlo. Seguirá admitiendo una
sola persona, equipos distintos y excepciones justificadas. No se añaden reuniones,
chats ni firmas por cada registro.

## Documentos que forman esta revisión

- [Propuesta funcional](functional.md): participantes, proceso, decisiones,
  correcciones, flexibilidad, experiencia y criterios de aceptación.
- [Propuesta técnica](technical.md): datos, controles, operaciones, vigencia,
  compatibilidad, eficiencia y límites de la solución.

Este paquete amplía v3.0.0; no sustituye sus documentos históricos ni modifica
`specs/canonical/`. No es un plan de implementación ni una aprobación de release.

## Decisiones concretas que se someten a validación

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

## Qué permite aprobar este paquete

La validación funcional y técnica de **integral-review-01** permitirá preparar un
plan de implementación con tareas y pruebas que cubra los criterios de aceptación.
No autoriza todavía implementación, commits, push, publicación, instalación,
migración de consumidores ni apertura de un PR remoto.

Si se solicita modificar una parte, se revisará este paquete indicando qué cambia;
la respuesta no se interpretará como aprobación de contenidos no confirmados.

## Situación de la revisión

- Base contrastada: plugin 3.0.0, commit
  `0124fdb4927e04b2fbc773e36d2073e7e962a544`.
- Requisitos y diseño propuestos: contenidos en los dos documentos enlazados.
- Validación del usuario: pendiente.
- Planificación e implementación de esta evolución: no iniciadas.
- Viabilidad comprobada mediante lectura del núcleo actual; no acredita que los
  comportamientos nuevos estén implementados o probados.
