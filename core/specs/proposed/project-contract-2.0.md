# Contrato de proyecto LKS-SDD 2.0

Estado: propuesta vigente para v2. No es fuente canónica ni autoriza una
implementación, una publicación, un acceso externo o una decisión de negocio.

## Propósito y alcance

Este contrato define la declaración tecnológica obligatoria y local de cada
proyecto v2. La autoridad permanece en los Markdown del proyecto consumidor;
`.lks-sdd/project.json` solo localiza sus rutas e identidad.

La declaración se guarda en
`03-solution/technology-declaration.md`. Cada entrada identifica la tecnología,
su alcance (`project` o `TASK-###`), criticidad, versión o configuración
relevante, fuentes observadas y el motivo de su estado. Una entrada no sustituye
la autorización de una tarea ni convierte evidencia técnica en aceptación humana.

## Estados de declaración

Cada tecnología tiene exactamente uno de estos estados:

- `observed`: hay una fuente local que acredita su presencia o uso, sin decisión
  de adoptarla.
- `proposed`: es una alternativa explícita pendiente de decisión.
- `confirmed`: una decisión local vigente fija su uso para el alcance declarado.
  Debe enlazar la decisión y la evidencia que la sostiene.
- `unknown`: falta un dato necesario para decidir su uso, alcance, versión o
  compatibilidad. No se interpreta como ausencia ni como confirmación.
- `transition`: registra un paso temporal y verificable entre una fuente 1.5 y
  una declaración v2. Debe identificar origen, destino, alcance, condición de
  salida y responsable de la decisión de corte.

Solo `confirmed` puede satisfacer el contexto tecnológico de una tarea. Un
`observed`, `proposed`, `unknown` o `transition` relevante bloquea readiness e
implementación hasta que exista la decisión local aplicable. Una confirmación
para una tarea no selecciona la misma tecnología para otras tareas.

## Contexto tecnológico de las tareas

Antes de evaluar, implementar o verificar una `TASK-###`, su ficha enlaza las
entradas de declaración que le sean relevantes. Para cada una indica el uso
concreto, la versión o configuración que afecta a la tarea y su criticidad. El
contexto se resuelve desde esas entradas locales y sus decisiones enlazadas; no
se infiere de carpetas, manifiestos, código ni de una tecnología usada en otro
alcance.

Si falta una entrada relevante, la tarea debe registrar `unknown` y detener la
acción que dependa de ella. Si una tecnología no es relevante para la tarea, no
se añade por completitud. Las observaciones y las propuestas se conservan como
hechos o alternativas; no habilitan trabajo por proximidad con una decisión
confirmada.

## Corte seguro de 1.5 a 2.0

Un proyecto 1.5 sigue con su runtime y documentos fijados hasta que se autorice
un preview de migración ligado a bytes exactos. El preview inventaría las fuentes
afectadas, crea las declaraciones v2 necesarias como `observed`, `unknown` o
`transition`, y nunca eleva una elección histórica a `confirmed` sin una decisión
local explícita.

El corte se completa solo cuando el recibo de migración es íntegro, cada tarea
afectada tiene su contexto v2 resuelto, no queda una ruta 1.5 activa para ese
alcance y los escritores 1.5 están bloqueados. Las fuentes 1.5 se conservan sin
modificarlas para consulta y recuperación; no compiten con las declaraciones v2
en la tarea ya migrada. Una interrupción se recupera desde el journal y el
preview autorizado, sin mezclar escrituras de ambos lados del corte.

## Límites

Este contrato no define perfiles globales, recetas, catálogos de capacidades,
locks, certificaciones ni variantes. Tampoco selecciona una pila preferente,
compone soporte entre proyectos ni crea autoridad fuera del proyecto que declara
la tecnología.
