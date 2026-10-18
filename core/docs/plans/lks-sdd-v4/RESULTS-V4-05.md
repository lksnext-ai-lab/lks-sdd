# V4-05 — Consulta compuesta para preparar trabajo

Fecha: 2026-10-16. Plan 0.4; base `bf4d059c98826039097d606121ab6406d762fcc7`.
Alcance autorizado: implementación fuente local y verificación focal; las seis
mejoras y sus presupuestos permanecen. Estado: **verified en alcance técnico local**. Detalle en [registro](v4-05-progress.json).

## Resultado funcional

`v3 work-prepare` reúne estado de las tareas seleccionadas, condiciones para la
transición solicitada, intervenciones y contrato literal en una respuesta.
Comparte una carga del modelo y un ámbito de cálculo; conserva evaluaciones
internas y verificaciones físicas. No concede autoridad ni inicia trabajo.

El formato versionado valida identidad, parámetros, acción y correlación. Puede
identificar una porción independiente sin ocultar tareas bloqueadas. Mantiene
textos completos, reglas globales, dependencias entrantes, prosa incierta y adjuntos;
un binario pendiente de observación impide declarar la preparación completa.
La captura externa de V4-04 conserva también los materiales anidados.

Se contrastan fuentes, pertenencia documental, política/roles, rama/HEAD, inventario
de código, runtime/índice y vigencias antes de responder. La materialización sigue
usando las guardas actuales y debe reevaluar las condiciones. Una instantánea no
bloquea cambios posteriores ni sustituye las presentaciones requeridas.

El índice derivado puede faltar y no se reconstruye. Una selección vacía o que omite
la tarea solicitada se bloquea. Un timeout Git se convierte en causa controlada en
el helper existente, sin introducir ejecución externa en el módulo nuevo.

## Verificación y límites de la evidencia

La primera batería completa produjo 20 resultados positivos y dos fallos de montaje:
faltaba un segundo miembro para configurar revisión independiente y se esperaba
que prosa incierta apareciese en una lista reservada a elementos ampliados. Se
corrigieron las pruebas conservando las exigencias funcionales. Los logs originales
se retienen; los resultados aplicables posteriores constan en el registro adjunto.

Últimos resultados aplicables: **59 casos distintos positivos** (23 de preparación
y 36 de regresión), sin casos pendientes o fallidos en este alcance. La candidata
final repite cuatro casos afectados —incluyendo el diferencial positivo— y el caso
de CLI público/ambos paquetes; los otros resultados pertenecen a la candidata
anterior a esas correcciones locales. No se afirma una repetición íntegra final.
Los cuatro casos corregidos pasan en 277,120 s y el caso público en 151,203 s.

Regresión inicial: 36/36 casos de aprobaciones, routing, observación y exportación.
Diferenciales: contrato y condiciones equivalentes a consultas individuales; consultas
sin cambios de archivos; autoridad ausente, actor inválido, tareas retiradas/ambiguas,
revisión requerida, porciones parciales, contrato vacío y cambios concurrentes.
Los adaptadores Codex y Copilot transportan el mismo módulo/CLI/documentación y
el recorrido público usa el runtime fijado. Es prueba sintética de paquete, no uso
en el host Copilot, instalación ni aceptación conversacional.

La comprobación estática mantiene seis skills y lectores 1.5/2.0/3.0/3.1; no se
modifican contratos canónicos ni versiones. Se conserva el comportamiento Windows
de los helpers ya revisados: esta consulta no introduce temporales de producción.
No se repite una campaña completa Windows en este bloque; la aceptación consolidada
sigue en V4-15. El diff focal se revisó frente a la instantánea previa de V4-04.

## Preparación S8 y ahorro

En la candidata anterior a las correcciones finales de índices/suficiencia/timeout,
una consulta pública sobre el fixture objetivo de 338 elementos terminó `ready`
en 32,482 s, con 26,152 s de preparación de entorno separados. Retuvo 319/319
fragmentos con sus hashes esperados, prosa incierta y fuentes canónicas sin cambios.
Es evidencia del componente, no una ejecución completa S8 ni un resultado temporal
certificado de la candidata final.

Contadores observados: una carga de modelo, un ámbito de cálculo, una consulta de
estado, una de readiness, un recorrido de intervenciones, dos selecciones internas
de contexto, 14 llamadas Git y una comprobación final de runtime/vigencia. Se conserva
el trabajo interno en los contadores; captura, sobre de uso y entrega del host quedan
fuera de ese ámbito. No equivale a CPU, memoria, tokens facturados ni ahorro total.

No hay pareja comparable de rendimiento en esta entrega. El ahorro integral, tokens
facturados y mejora S8 ≥20 % permanecen pendientes en sus hitos previstos. La valoración
humana sigue diferida al uso real sostenido. Copilot se mantiene al final.

## Presupuesto y continuación

Bloque iniciado a las 12:50:16Z con cota de 45 minutos, incluidos preparación, fallos,
correcciones y reporte. Cero intentos funcionales completos nuevos; cero variantes M6.
El saldo global histórico no está certificado: no se convierte esta cota en saldo
disponible de las 12 horas. Se conservan 48 intentos, 8 h humanas y M6 ≤2 variantes/4 h.
La medición humana no se reintroduce en este ensayo técnico.

Evidencia reutilizada en `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05`:
logs por campaña, instantáneas de fuente, huellas, S8 parcial, verificación y consumo
del bloque. Se conserva el histórico; no se limpian temporales ni evidencias abiertas.

V4-05A no iniciado. Su autorización permitirá comprobar el recorrido completo y la
utilidad temprana; V4-06 y posteriores siguen pendientes. No hay commits, integración,
instalación, publicación ni activación de esta candidata.
