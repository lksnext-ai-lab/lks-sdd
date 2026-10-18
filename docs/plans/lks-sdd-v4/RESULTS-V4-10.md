# V4-10 — Mantenimiento proporcional

Fecha: 2026-10-17. AC-18, AC-19 y AC-35 verificados en alcance técnico local.
Se completa M5 mediante las instrucciones compartidas y las capacidades existentes
de V4-05/06. Las pruebas no reproducen una carencia que justifique nueva lógica en
`v31_corrections`; ese núcleo permanece intacto.

## Comparación con 3.4.3 bien utilizada

| Recorrido | Referencia 3.4.3 | Entrega 4.0 | Decisiones, datos y registros conservados |
|---|---|---|---|
| Defecto cubierto durante una tarea vigente | Reutiliza propuesta, plan y autorización. Transiciones individuales de inicio, implementación, evidencia, verificación y cierre. | Mismos cinco efectos nativos; V4-06 permite transportarlos mediante `work-continue` y `work-record-results`, con preparación fresca en sus límites. | Cero decisiones nuevas de propuesta/plan; mismas pruebas afectadas, actor, alcance y evidencia del sujeto exacto. Las bases y huellas siguen siendo necesarias. |
| Cambio breve del acuerdo, incluidos permisos o interfaz | Propuesta revisada y validada antes de modificar tareas ejecutables y autorizar su plan. | Misma secuencia competente, indicada expresamente en la guía; V4-08/09 conserva alcance y obligaciones. | Se reutilizan las identidades aplicables, se incrementan sus revisiones y caducan las decisiones que ya no cubren el contenido. No se fusionan propuesta y tareas sin validación previa. |
| Capacidad nueva con rechazo previo | Clasificación explícita y petición nueva con propuesta, tareas y autorización propias. | Mismo recorrido; la guía distingue la petición nueva de la corrección cubierta y conserva la referencia al rechazo original. | Clasificar no concede autoridad. Se conserva el rechazo, el criterio correctivo y la evidencia pendiente; la tarea nueva no hereda el permiso de la anterior. |

La contribución de transporte de la primera fila pertenece a M2 y ya está acreditada
en sus pruebas; **no se vuelve a contabilizar como ahorro adicional de M5**. En las
otras dos filas no se elimina ninguna intervención competente. Los datos de negocio
y las pruebas necesarias se conservan en los tres recorridos. La guía evita
reconstruirlos o volver a consultar las mismas vistas cuando `work-prepare` ya las
ha entregado sobre una base vigente; los cambios de base exigen una nueva preparación.

La referencia no es un flujo artificial que revalide todo el proyecto. Las pruebas
comparativas confirman que 3.4.3 ya reutiliza acuerdos en la corrección cubierta.
No se afirma ahorro adicional medido de acciones, tiempo, bytes o tokens de M5.
La percepción de menor fricción sigue pendiente de uso real sostenido, AC-36.

## Implementación y garantías

Se completa [la guía condicional de correcciones](../../decision-guides/corrections.md)
con los tres recorridos, preparación compuesta, condiciones de reutilización,
reapertura, permisos vencidos/revocados, rechazo y nueva evidencia. No añade comandos,
estados, decisiones o registros de negocio. El formato de las operaciones y sus
guards permanece intacto; no cambia el runtime fijado de ningún consumidor.

**Cinco comprobaciones distintas superadas en la candidata**, cuatro de ellas
comparadas también contra el núcleo publicado 3.4.3 congelado:

- Defecto cubierto: prueba real fallida, corrección y prueba real pasada, cierre,
  reapertura y bloqueo por revocación; mismas definiciones y autorización hasta revocar.
- Cambio pequeño de permisos: no autoría conjunta prematura de propuesta/tarea,
  invalidación de autoridad anterior, propuesta antes de plan e incertidumbre crítica.
- Nueva capacidad: petición y cobertura propias, rechazo conservado y evidencia
  ausente declarada pendiente; no autorización por clasificación o por tarea anterior.
- Identidad con permiso vencido: preparación bloqueada pese al acuerdo previo.
- Regresión existente de rechazo posterior a aceptación: conserva rechazo,
  reapertura, pruebas posteriores al fallo y necesidad de volver a integrar/aceptar.

La última regresión se ejecutó en la candidata; su núcleo correctivo coincide con
la referencia. En total se aceptan nueve ejecuciones de casos: cuatro A, cuatro B y
esa regresión. Dos intentos adicionales se conservan como fallo del auxiliar: una
aserción esperaba un error posterior, pero la presentación bloqueó antes por falta
de evidencia. Se ajustó solo esa expectativa y se repitió el caso afectado. Los dos
métodos ya válidos se reutilizan con igualdad de AST, sin volver a ejecutarlos.

Las pruebas finales tardaron 70,128 s en referencia y 158,734 s en candidata,
**con coberturas distintas y ejecución concurrente**: no son una comparación de
rendimiento. El contrato estático y el diff se comprobaron. Se reutiliza la puerta
técnica anterior mediante igualdad de huellas de todos los scripts, fuentes
canónicas, esquemas y skills; no se repite Windows ni la batería general.

## Estado y continuación

Se conservan seis mejoras, 23 tareas, 44 criterios y presupuestos. Cero intentos
nuevos de la campaña de tareas completas o variantes M6; tiempos y tokens de
ahorro siguen sin acreditarse aquí, `billed_tokens: null`. No se deduce un saldo
global nuevo de la autorización de continuación.

Windows y H2 permanecen pendientes. No hay instalación, publicación, push ni commits.
V4-06 y AC-40 conservan sus pendientes de rendimiento. La siguiente tarea es V4-11;
su adaptación técnica no da por aceptado el sobrecoste pendiente de V4-07A.

Registro: [v4-10-progress.json](v4-10-progress.json).
Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-10`
(`consolidated-result.json`, resultados A/B, casos, huellas y ejecutores).
