# Revisión global de la gestión documental del plugin

Fecha: 2026-10-09. Estado: **análisis terminado al nivel de recorridos y arquitectura;
recomendaciones pendientes de implementación**.

El usuario autorizó revisar el conjunto y preparar un plan común, ejecutable después
por fases. Sus dos objetivos son reducir tokens de IA y tiempo de desarrollo. El
[plan conjunto](PLAN.md) incorpora la incidencia como un caso de regresión.

## Alcance real de esta revisión

Se revisaron las seis entradas de skills y sus procedimientos v3, las reglas comunes,
las nueve familias de decisión, los mecanismos de consulta, autoría, aprobación,
ejecución, verificación, conservación y recuperación, y los adaptadores Codex/Copilot.
Se trazaron las **58 operaciones públicas v3** a sus familias, sin operaciones sin
asignar. El [inventario de 69 fuentes](evidence/global-audit-inventory.json) conserva
huellas, tamaños, localizadores de funciones y el mapa de operaciones.

La profundidad es una inspección funcional de los recorridos actuales y sus motores
compartidos. Inventariar un archivo no significa haber auditado cada línea. Las rutas
1.5/2.0 se examinaron en su selección, conservación y frontera de migración; no se
reejecutaron todos sus motores históricos. Los textos canónicos de contrato se
consultaron como restricciones y no se modificaron.

Se añadieron [siete consultas instrumentadas](evidence/global-flow-probe.json) sobre
una fixture desechable del runtime instalado 3.2.0. No son siete recorridos completos
de desarrollo ni una observación humana de los dos hosts. Las consultas preservaron
el snapshot documental; las únicas escrituras de la sonda fueron su preparación
sintética y la incorporación deliberada de datos sintéticos de continuidad.

La rama contiene trabajo previo de inventarios y migración. Se ha conservado. Seis
fuentes del inventario difieren del plugin instalado, identificadas explícitamente.
Las mediciones usan el runtime instalado; las recomendaciones señalan la integración
necesaria con ese trabajo pendiente. No se atribuyen sus cambios a esta revisión.

## Conclusión general

**El problema afecta a varias capas del plugin y merece un plan conjunto.** Los
mecanismos examinados amplían contexto, repiten representaciones y vuelven a cargar
datos. El coste también depende de cuántos registros de continuidad se acumulan y
de las decisiones que el método exige antes de una modificación.

Hay mejoras ya disponibles: instrucciones por familia, aprobación y autorización
agrupadas, reutilización de encargos revisados, consultas paginadas, adopción parcial,
inventarios por referencia y recuperación exacta. Conviene conservarlas y corregir
los puntos donde las guías y el comportamiento efectivo no consiguen el ahorro esperado.

No se demuestra que el método produzca siempre demasiados documentos nuevos. Sí
se demuestra sobreselección, duplicación en determinadas salidas y trabajo interno
repetido. La proporcionalidad de la definición y el coste humano requieren decisiones
de diseño y observación de los recorridos completos.

## 1. Qué exige cada skill

| Skill | Lectura y propósito necesarios | Escritura justificada | Reutilización existente | Coste o riesgo a corregir |
|---|---|---|---|---|
| `help` | Fuentes de la pregunta; catálogo, estado o historia exacta cuando corresponda. | Ninguna escritura canónica por consultar. `state-history` con destino exporta un árbol externo expresamente solicitado. | Catálogo y trazas paginados; consultas no inicializan ni migran. | Carga global para un catálogo pequeño; `status` añade recorrido integral y recalcula hechos; `review` incorpora presentación completa. |
| `define` | Petición, cobertura vigente, contrato afectado, decisiones pendientes y arquitectura real. | Propuesta nueva/modificada; después plan y tareas; decisiones explícitas y recibo de autoría. | Propuesta funcional/técnica conjunta; aprobación del plan, permiso y revisión propia agrupables. | Presentación sobredimensionada; autoría prepara más de una vista del estado; formato detallado para cambios pequeños sin una guía suficientemente concreta de mínima expresión. |
| `adopt-existing` | Fuentes expresamente seleccionadas e intención; en migración, origen, destino y conservación. | Adopción parcial/configuración o migración autorizada; conservar planes y autoridad histórica. | Inspección limitada a 50 fuentes y 8 MiB; no exige documentar el sistema entero. | Coste de corte y runtime puede preceder a una tarea pequeña; lectura de rutas antiguas extensa y orientación de compatibilidad mejorable. |
| `assess-readiness` | Tarea, actor, transición, cobertura, autoridad, dependencias y evidencia aplicables. | Ninguna: readiness observa y no autoriza. | Predicados compartidos y causas localizadas. | Comprobación de runtime más cargas posteriores; cálculo de contexto/recorrido al responder una pregunta de preparación. |
| `implement` | Contrato literal aplicable, código afectado, autorización y continuidad. | Transiciones acreditadas; checkpoint por un hito, bloqueo o relevo real; resultados de controles correspondientes. | Encargo revisado y autorización vigentes; no checkpoint por comando ni Sonar por cada operación. | Contexto conservador global; relectura tras compactación; inventarios y comprobaciones repetidos; registros de continuidad acumulados. |
| `verify` | Criterios y pruebas, sujeto exacto, evidencia vigente, interfaces y aceptación. | Evidencia real, verificación/cierre, integración y aceptación; corrección si corresponde. | Integración/aceptación agrupables; entrega sin una nueva firma SDD. | Informes completos y eventos de la petición entran en presentaciones; estados/controles recalculados; riesgo de repetir comprobaciones por falta de orientación precisa. |

Fuentes: `skills/lks-sdd-*/SKILL.md`, `references/v3.md`,
[reglas comunes](../../../docs/V3-COMMON.md),
[recorrido integral](../../../docs/V31-REVIEW.md),
[operaciones](../../../docs/V3-OPERATIONS.md) y sus funciones en el inventario.

### Familias y excepciones recorridas

También se contrastaron configuración, especificación, planificación, encargos,
verificación, correcciones, excepciones/continuidad, diseño condicionado y entrega.
Los casos de rechazo, cambio de alcance, relevo, revocación, recuperación, migración,
tecnología y selección visual están contemplados en el plan. Sus obligaciones se
activan por condiciones reales, sin cargar sus nueve guías en toda interacción.

## 2. Qué documentación cumple cada función

| Clase | Función | Tratamiento recomendado |
|---|---|---|
| Instrucciones del plugin y host | Orientar al agente y aplicar el método. | Núcleo breve más procedimiento de la operación; conservar las seis skills. |
| Especificaciones, restricciones y decisiones del consumidor | Definir el comportamiento acordado. | Markdown canónico; leer obligaciones aplicables y reutilizar acuerdos vigentes. |
| Plan y tareas | Delimitar ejecución, responsabilidad, cobertura y pruebas. | Registrar el trabajo nuevo o cambiado; referenciar lo existente. |
| Transiciones, revisiones y checkpoints | Conservar quién hizo/decidió qué y permitir continuidad. | Registrar hechos distintos; seleccionar estado actual y antecedentes necesarios para la operación. |
| Evidencia e informes | Acreditar resultados sobre un sujeto concreto. | Conservar el original íntegro; consultar resultados y fragmentos necesarios con procedencia y acceso al original. |
| Índices, vistas y paquetes | Localizar, presentar o preparar una operación. | Derivados y regenerables; no convertir consultas en otra fuente canónica. |
| Objetos, manifiestos, diarios e historia | Conservar bytes y permitir recuperación. | Cálculo del runtime; no transportar su contenido al modelo salvo necesidad concreta. |

Cada cambio debe medirse en cuatro unidades distintas: documentos semánticos,
archivos físicos, bytes procesados y tokens entregados al modelo. La deduplicación
del almacenamiento ya reduce parte del crecimiento físico; no acredita por sí sola
menos lecturas de IA o menor tiempo conversacional.

## 3. Hallazgos globales

### GD-01. El ámbito de trabajo no gobierna coherentemente todos los consumidores — confirmado

`v3_context.select` añade toda la prosa activa; la ruta pública `context` conserva
además todos los elementos normativos activos. Las vistas y `facts_for` reutilizan
el selector con condiciones distintas. Resolver solo el cierre de propuesta dejaría
pendientes implementación, preparación y presentación de resultados.

Se deben alinear selección, dependencias, ámbito de evidencia y base semántica de
decisiones. La parte global necesaria del contrato se conserva. Una fuente sin
metadatos necesita análisis de aplicabilidad; esa ausencia no puede equivaler a una
revisión automática de todos sus adjuntos. [Evidencia anterior](ANALYSIS.md).

### GD-02. El transporte sigue duplicando contenido — confirmado

`decision-view --json` incluye fuentes, cuerpos de secciones y Markdown.
`review` devuelve la presentación completa incluso en su salida ordinaria. El modo
compacto de `decision-view` ya evita parte de esa duplicación y debe conservarse,
pero no reduce por sí solo las fuentes seleccionadas.

Los previews de escritura ya muestran un resumen y guardan payloads aparte. No
corresponde describir toda salida de CLI como un volcado de base64. La mejora debe
aplicarse donde persisten cuerpos e inventarios grandes, con detalle recuperable.

### GD-03. La continuidad de una petición también hace crecer la consulta — confirmado

`v3_decision_presentation.collect` incorpora eventos vinculados a la petición o sus
tareas sin una selección general por vigencia y finalidad de la presentación.
También recupera el texto completo de determinados informes de evidencia/análisis.

En la nueva sonda, diez checkpoints sintéticos de la misma petición elevaron las
fuentes de 6 a 16 y el JSON de 28.538 a 51.108 caracteres. El Markdown se mantuvo en
1.364 caracteres. Este caso acredita exceso en el transporte detallado; **no** un
aumento del Markdown compacto. No demuestra que esos checkpoints fueran creados
innecesariamente: se incorporaron expresamente para medir su efecto.

El estado actual, los fallos pendientes y las reservas vigentes deben estar accesibles
sin emitir siempre todos los avances previos. El historial conserva su integridad
y sigue siendo recuperable. Seleccionar por fecha únicamente sería insuficiente.

### GD-04. Paginar la salida no limita la carga interna — confirmado

En la fixture de 17 documentos, pedir 1 elemento del catálogo y pedir 50 produjo
en ambos casos 1 carga, 17 parseos y 19 lecturas del lector común. La salida sí
cambió: 420 frente a 5.775 caracteres. `status` evaluó `request_facts` dos veces,
directamente y al generar `interventions`.

La ruta de readiness sobre la fixture sin runtime fijado produjo `blocked`, dos
cargas y 34 parseos al comprobar el corte y explicar la continuidad. Separadamente,
la función de biblioteca de readiness produjo `allowed`, una carga, 17 parseos y
una selección. Este segundo resultado no acredita preparación de la CLI pública:
el runtime fijado sigue siendo requisito. La distinción se conserva en la evidencia.

### GD-05. Preparar un cambio documental implica trabajo global repetido — código confirmado; peso sin medir

`author` carga el modelo; `candidate` vuelve a cargarlo, materializa una vista
temporal y valida el resultado. `prepare` carga el estado previo y `stage` valida
otra vista. El CLI comprueba el runtime y la operación conserva guards y estados
exactos; `document_state.prepare` vuelve a leer las fuentes del estado preservado.

Las validaciones del antes, candidato y después tienen finalidades distintas.
No se propone eliminarlas. Se propone reutilizar contenido y resultados válidos
dentro de cada instantánea, evitando reconstruirlos para subpasos equivalentes.
El coste de I/O, procesos Git y cálculo necesita medición focal al implementar.

### GD-06. Existe un coste mínimo del método para un cambio nuevo — confirmado; proporcionalidad pendiente de decisión

El recorrido individual documenta tres momentos humanos: propuesta, plan y resultado.
Una propuesta nueva se presenta con siete apartados y detalle por componente;
plan y permiso son efectos distintos que pueden agruparse. Las guías permiten
reutilizar cobertura y autorización cuando una corrección ya está comprendida.

Por tanto, no toda corrección exige empezar una propuesta desde cero. Pero un cambio
pequeño sin cobertura sigue teniendo un coste fijo. Falta una guía operativa verificable
de mínima expresión: qué se referencia, qué se describe una vez y cuánto detalle exige
un cambio acotado. Los campos técnicos incluyen contratos, datos y errores incluso
cuando no cambian; hoy se pide explicar ese hecho.

Se recomienda resolver primero la proporcionalidad del contenido y la reutilización.
Reducir los momentos de decisión o crear dispensas automáticas supondría otra decisión
de método; no se autoriza como una optimización interna.

### GD-07. La economía de registros depende parcialmente de las instrucciones — confirmado con alcance limitado

Las reglas comunes prohíben checkpoints por consultar. Algunas revisiones/cierres
tienen respuestas `already-recorded`; `checkpoint` crea un evento con nueva identidad
y fecha. No hay un mecanismo general que convierta cualquier reintento en una operación
idempotente. Eso no prueba abuso de escritura en sesiones habituales.

Se deben diferenciar un reintento de la misma operación y una observación posterior
legítima aunque su texto coincida. Evitar duplicados no autoriza borrar hechos,
actores o evidencias distintas, ni sustituirlos por un resumen.

### GD-08. El encaminamiento documental admite mejoras concretas — confirmado; impacto conversacional no medido

Las seis rutas básicas v3 requieren tres archivos y entre 8.773 y 10.239 caracteres
antes de guías condicionales. No se suman las seis como si se cargasen juntas. La
selección por familias ya está implementada: fragmentarla todavía más necesita una
justificación de ahorro total, incluidas nuevas consultas.

Hay puntos concretos de confusión: help indica `journey/interventions`, pero la
acción CLI es `interventions` y `journey` es un campo derivado; las referencias v2/legacy
conservan frases sobre iniciar v2 mientras la entrada actual y el CLI limitan esa ruta
a lectura/recuperación y migración explícita. Las entradas actuales prevalecen, pero
la coexistencia puede provocar lectura o intentos de comandos innecesarios.

### GD-09. Los hosts comparten núcleo, con sobrecarga y selección propias — estructura confirmada

Los adaptadores resuelven runtime, host y skill. El núcleo compartido conserva las
mismas obligaciones; las herramientas visuales y externas dependen del host. El doctor
verifica inventario y bytes del runtime. Algunas rutas vuelven a hacerlo dentro de
la operación. Esa verificación es I/O local, no lectura de IA de todos esos archivos.

Debe comprobarse que cada host carga únicamente la rama vigente, que no duplica
entrypoints y que consulta los campos concretos de la operación. La revisión estática
de wrappers no acredita el comportamiento de una conversación real en Copilot o Codex.

### GD-10. El almacenamiento ya tiene una solución que no debe rehacerse — confirmado

Inventarios por referencia, objetos por hash, estados exactos, diarios y lectores de
historia evitan copias físicas completas y permiten recuperación. Los registros
semánticos siguen en Markdown. El corpus activo carga también eventos, aunque la
carpeta de historia, evidencia bruta y migraciones esté excluida del escaneo ordinario.

Se debe optimizar la consulta de ese corpus acumulado y la reutilización por operación.
Una reorganización documental puede formar parte de la transición diseñada para esta
mejora, con coste explícito y recuperación. No se exige limpiar manualmente ni eliminar
historia de consumidores como condición de entrada. Se conserva la solución de almacenamiento
existente donde sea adecuada al formato elegido.

### GD-11. Las métricas actuales no acreditan coste total — confirmado

Caracteres/4, recuentos de archivos y reducción del Markdown activo no equivalen a
tokens facturados ni a duración del desarrollo. La caché del runtime devuelve texto
literal; la caché del proveedor tiene otra función. Los checkpoints de uso de la sesión
son instantáneas y no se suman como consumo total. La comparación debe incluir también
recuperaciones, reintentos, preguntas y verificación final.

## 4. Proporcionalidad propuesta para los recorridos

| Situación | Trabajo documental recomendado | Condición que amplía el recorrido |
|---|---|---|
| Consulta | Recuperar las fuentes de la pregunta; ningún registro nuevo por consultar. | El usuario pide una decisión o cambio concreto. |
| Corrección cubierta y autorizada | Reutilizar especificación/plan; registrar avance y evidencia nuevos cuando corresponda. | Cambia contrato, alcance, responsable, riesgo o autorización aplicable. |
| Cambio pequeño sin cobertura | Propuesta conjunta concisa y plan mínimo suficiente; referenciar contratos existentes. | Hay dependencias o efectos que requieren más detalle o tareas. |
| Funcionalidad nueva | Definir comportamiento, componentes, criterios y plan de sus dependencias. | Interfaces compartidas, datos, seguridad, despliegue o equipos afectados. |
| Cambio transversal | Mostrar el cambio y su impacto en contratos y consumidores; revisiones competentes. | Incertidumbre material o dependencias no resueltas. |
| Reanudación/relevo | Recuperar contrato vigente, estado, pendientes y nueva asignación si existe. | Pérdida de contexto, cambios materiales o autoridad diferente. |
| Adopción/migración | Inspección o corte delimitado; conservar acuerdos e historia. | Origen no soportado, contradicción o falta de decisiones críticas. |

La proporcionalidad depende de novedad, efecto y riesgo, no del número de líneas
de código. La propuesta mantiene las obligaciones aplicables y evita que información
ya acordada deba redactarse de nuevo en cada etapa.

## 5. Decisiones recomendadas y límites de la siguiente fase

1. Adoptar un plan común con mejoras entregables por fases; la incidencia deja de
   ser la frontera del análisis.
2. Conservar las seis skills, los Markdown canónicos y las garantías de autorización,
   evidencia, integridad y recuperación.
3. Abordar transporte, cálculo repetido, aplicabilidad y continuidad como piezas
   coordinadas; simplificar instrucciones y registros donde lo justifique el recorrido.
4. Mantener en esta mejora los momentos de decisión vigentes. Cualquier reducción
   de esos momentos se evaluaría como cambio de método explícito.
5. Validar ahorro sobre trabajo terminado, con los errores y ampliaciones incluidos.

**Decisión posterior del usuario:** se admite migrar la documentación de proyectos 3.2
si aporta mejora. Se incorpora al [plan conjunto](PLAN.md) como libertad de diseño y
condición de evaluación: coste inicial más ahorro recurrente, conservación y continuación.
No cambia los hechos medidos de esta auditoría ni demuestra todavía que la migración
sea necesaria o rentable.

El diagnóstico y el plan no acreditan la implementación, el ahorro obtenido, la
aceptación humana en ambos hosts ni una release. La sonda es pequeña y no permite
extrapolar sus latencias. El [análisis anterior](ANALYSIS.md) conserva la medición
de la incidencia y del crecimiento con documentación ajena.
