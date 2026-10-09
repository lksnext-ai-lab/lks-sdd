# Plan conjunto de eficiencia documental

Fecha: 2026-10-09. Revisión: 4. Estado: **candidata técnica local preparada; commit y gate oficiales pendientes**.
La petición «vamos a continuar hasta poder tener una nueva release. Quiero que
planifiques cuidadosamente cada tarea que vayas haciendo», del 2026-10-09,
autoriza concretar y ejecutar este plan y preparar una candidata verificable.
Las tareas y decisiones técnicas se registran en [IMPLEMENTATION.md](IMPLEMENTATION.md).
Los números de fase no introducen nuevas preguntas de permiso por sí mismos.
Commits, push, publicación e instalación conservan la autorización separada que
exige `AGENTS.md`; la aceptación y el ahorro observado se acreditan con evidencia.

Base: [revisión global](GLOBAL-AUDIT.md), [propuesta](PROPOSAL.md) e
[incidencia y mediciones](ANALYSIS.md). Los identificadores siguientes organizan
trabajo de mantenimiento; no crean personas, tareas ni permisos en un consumidor.

## Resultado perseguido

Reducir tokens de IA y tiempo de desarrollo mediante información proporcionada al
cambio, respuestas sin duplicación, reutilización del cálculo y continuidad útil.
El ahorro se acepta con el cambio terminado y verificado, conservando obligaciones,
autoridad, procedencia y capacidad de recuperación.

El coste se separa en: instrucciones; contenido de proyecto leído por la IA;
transporte de herramientas; cálculo/I/O interno; generación de registros; preguntas
y retrabajo. Cada fase debe identificar qué componente reduce y comprobar que no
traslada el coste a otro.

## Decisión confirmada sobre migración

El usuario acepta que la nueva release requiera migrar la documentación de proyectos
con plugin 3.2 si el resultado supone una mejora. Por tanto, conservar el formato
documental actual deja de ser una restricción de diseño. Se pueden reorganizar los
Markdown canónicos, sus relaciones y su separación entre contrato vigente e historia.

Esta decisión permite evaluar la migración; todavía no selecciona un formato ni
autoriza ejecutar migraciones en consumidores. No se exige que el runtime 3.2 pueda
operar sobre el nuevo formato. Sí se exige una transición explícita y recuperable,
conservación del significado y procedencia, y continuidad del trabajo en curso.
La evaluación incluirá el coste inicial de conversión y revisión, además del ahorro
posterior de tokens y tiempo. No se mantiene una doble vía operativa indefinida solo
para conservar el formato antiguo.

## Decisiones de diseño recomendadas

1. **Conservar las seis skills y su invocación implícita.** Ajustar sus rutas e
   instrucciones, evitando nuevas capacidades vacías o más selección de entrypoints.
2. **Una fuente canónica por contenido.** Las vistas, índices y cachés son derivados;
   no sustituyen Markdown ni se convierten en expedientes adicionales.
3. **Conservar los momentos de decisión actuales.** Reutilizar y agrupar los que ya
   permite el método. La reducción de firmas obligatorias sería un cambio de método
   separado, con su propia justificación.
4. **Proporcionalidad según novedad e impacto.** Una corrección cubierta continúa;
   un cambio nuevo acotado usa contenido conciso y referencias; contratos compartidos
   o decisiones críticas reciben el detalle necesario. No se decide por líneas de código.
5. **Aplicabilidad explícita en el motor.** Separar ámbito de la tarea, contrato
   compartido/global, incertidumbre pertinente y antecedentes recuperables.
6. **Una instantánea por fase lógica de evaluación.** Reutilizar el modelo dentro
   de esa fase, conservando comprobaciones frescas de concurrencia y las evaluaciones
   diferenciadas de origen, candidato y resultado.
7. **Salida ordinaria breve y ampliable.** Una copia de cada cuerpo necesario;
   índices, evidencia completa y diagnóstico detallado recuperables por referencia.
8. **Diseñar la transición con el almacenamiento existente.** Reutilizar CAS, diarios,
   runtime fijado y lectores de origen donde sean adecuados. Admitir un formato nuevo
   y una conversión inicial si aportan mejora neta; conservar la historia recuperable.

Estas son recomendaciones concretas para validar. La compatibilidad de nuevos
formatos de salida y cualquier formato documental que finalmente resulte necesario
se resolverán antes de implementarlos, sin alterar `specs/canonical/` para acomodar código.

## Secuencia y dependencias

| Fase | Resultado | Dependencias | Riesgo principal |
|---|---|---|---|
| F0 | Contrato de eficiencia, ejemplos mínimos y referencia de coste. | Diagnóstico global disponible. | Medir solo serialización o introducir excepciones implícitas de método. |
| F1 | Consultas y transporte proporcionados. | F0. | Ocultar contenido necesario para una decisión o romper consumidores JSON. |
| F2 | Evaluación interna reutilizable. | F0; se integra con F1. | Reutilizar una instantánea después de que pierda vigencia. |
| F3 | Aplicabilidad coherente en las seis rutas y sus dependencias. | F0 y soporte de F1/F2. | Excluir una obligación válida o trasladar el bloqueo a otra fase. |
| F4 | Continuidad y documentación mínima en los recorridos. | F1–F3. | Confundir reintento con observación nueva o reducir indebidamente decisiones. |
| F5 | Transición documental, instrucciones y hosts coherentes. | Contratos de F1–F4 cerrados; se diseña desde F0 y se actualiza con cada fase. | Pérdida de significado o continuidad al migrar; guías y paquetes discordantes. |
| F6 | Comprobación integrada y candidato de release. | F1–F5. | Presentar ahorro parcial o pruebas de biblioteca como aceptación real. |

F1 y F2 permiten mejoras iniciales de menor riesgo semántico. F3 resuelve el núcleo
de la incidencia y debe quedar incluida para afirmar que el problema de alcance
está corregido. Un resultado parcial de F1/F2 puede conservarse, pero no cierra el
objetivo conjunto. No se asignan fechas ni horas sin dimensionar la implementación.

## F0. Fijar el contrato de eficiencia

**Trabajo:**

- Convertir la tabla de proporcionalidad de la auditoría en ejemplos de entrada,
  documentación mínima, decisiones y salida esperada para las seis skills.
- Precisar la información necesaria por operación: consulta, decisión, ejecución,
  verificación, continuidad e inspección de historia.
- Mantener un núcleo literal de obligaciones y procedencia; definir cuándo ampliar
  contexto y cómo explicar una incertidumbre concreta sin exigir revisión manual de todo el histórico.
- Elegir los límites de salida y presupuestos de tokens/latencia sobre los casos de
  referencia, antes de aceptar código. Un presupuesto avisa y orienta; no recorta
  obligaciones ni aprueba contenido incompleto.
- Registrar versión, host/modelo, caché y tiempos diferenciados. Reutilizar la evidencia
  existente cuando corresponda y completar solo las métricas ausentes.
- Comparar optimización del formato actual y reorganización documental con migración.
  En ambas opciones, justificar cómo se localizan obligaciones globales, ámbito de tarea,
  estado vigente y antecedentes sin releerlos todos. Elegir por coste total y calidad.
- Fijar una mezcla representativa de tareas y un horizonte de uso antes de evaluar la
  amortización. Medir tokens y tiempo por separado, incluyendo conversión automática,
  revisión humana, resolución de ambigüedades y posibles reintentos de migración.

**Entrega:** contrato de comportamiento y referencia de coste dentro de este plan y
sus evidencias. No requiere nuevos registros obligatorios en consumidores.

**Salida de fase:** es posible distinguir un cambio eficiente de uno que solo emitió
menos texto y exigió más preguntas o reintentos. Los casos y presupuestos están fijados;
las incógnitas de autoridad o compatibilidad no se trasladan a supuestos de código.

## F1. Corregir transporte y consultas

**Componentes:** `v3_decision_presentation`, `v3_lifecycle.review`, `v3_cli`,
`v3_guidance`, `v31_guidance` y la recuperación de evidencia de `v3_quality`.

**Trabajo:**

- Hacer coherente la salida habitual de `review` con una única representación útil
  del contenido. Separar transporte de fuentes, secciones y diagnóstico completo.
- Revisar salidas de estado, catálogo, hallazgos e inventarios de historia para que
  puedan localizar información sin emitir mapas completos innecesariamente.
- Recuperar informes y recursos por propósito, resultado y fragmento pertinente,
  conservando el original completo y su huella. El lector debe poder ampliar hasta
  obtener lo necesario antes de una decisión positiva.
- Mantener recibos vinculados a la versión realmente presentada. Referenciar una
  fuente no equivale a haberla observado; el cambio de formato no revoca aprobaciones antiguas.
- Definir compatibilidad del JSON antes de eliminar o cambiar campos públicos;
  una vista ampliada explícita conserva la inspección técnica.

**Comprobación:** cuerpos duplicados, truncamientos y consultas de ampliación; borrador
incompleto consultable; decisión incompleta rechazada; compatibilidad de consumidores.
Incluir el caso de diez checkpoints cuyo Markdown no cambia pero cuyo JSON sí crece.

**Salida de fase:** una sola copia por cuerpo necesario; consultas sin nuevos registros
canónicos; detalle completo recuperable; ninguna aprobación basada solo en un resumen.

## F2. Evitar cálculo equivalente repetido

**Componentes:** `v3_contract`, `v3_current`, `v3_guidance`, `v31_guidance`,
`v3_approval`, `v3_authoring`, `v3_storage`, `v3_git` y frontera de `runtime_doctor`.

**Trabajo:**

- Introducir un contexto interno de evaluación con modelo validado, índices y resultados
  derivados reutilizables por instantánea. No requiere un servicio, agente o hook.
- Pasar el mismo modelo desde comprobaciones de entrada a suboperaciones que consultan
  exactamente ese estado. Eliminar el doble cálculo de hechos al construir estado y journey.
- Reutilizar descriptores de cobertura, índices y verificaciones de objetos dentro de
  la evaluación; conservar el control de identidad, integridad, política y vencimientos.
- Evaluar el coste de construir candidatos y staging; compartir los bytes ya verificados
  cuando corresponda. Origen, estado propuesto y resultado aplicado siguen siendo distintos.
- Medir doctor, Git, parseo, lectura y hashing por separado. La primera implementación
  prioriza reutilización dentro de la operación; una caché persistente solo se incorporará
  si hace falta y su invalidación está demostrada.

**Comprobación:** contar cargas, parseos y lectura de objetos en consultas y mutaciones;
alterar una fuente, política, recurso o runtime entre preparación y aplicación y exigir
el rechazo correspondiente. Mantener detección de archivos nuevos y conflictos.

**Salida de fase:** no se repite el mismo parseo/cálculo dentro de una instantánea sin
motivo explícito. Una modificación posterior no hereda confianza del estado anterior.
No se promete I/O sublineal si la comprobación de integridad requiere leer el corpus.

## F3. Resolver aplicabilidad de forma común

**Componentes:** `v3_scope`, `v3_context`, `v3_approval`, `v3_workflow.facts_for`,
`v3_decision_presentation.collect` y `v3_presentation_guard`.

**Trabajo:**

- Resolver pertenencia desde petición/propuesta antes del PLAN, utilizando las relaciones
  existentes sin exigir `data.request` redundante para excluir elementos independientes.
- Construir el cierre literal con reglas globales, contratos compartidos, dependencias
  transitivas y contribuciones entrantes. No limitarse a enlaces salientes o carpetas.
- Tratar la prosa y los adjuntos a partir de su aplicabilidad, con ampliación por dudas
  relevantes. Utilizar estructura y decisiones existentes antes de inventar metadatos.
- Comparar reconciliación progresiva y conversión inicial a una estructura más explícita.
  La conversión puede recorrer el corpus una vez y registrar relaciones acreditadas;
  no puede inventar alcance, descartar obligaciones ni exigir al usuario reclasificar
  manualmente todo el histórico. Presentar juntas las dudas concretas que sí requieren
  decisión. Justificar cualquier metadato nuevo por su utilidad y coste de mantenimiento.
- Aplicar el mismo criterio a revisión, planificación, readiness y contexto de ejecución.
  El cambio del modo conservador normal requiere evidencia de suficiencia; activar
  `comparison=true` por sí solo no es la solución.
- Separar base semántica de una decisión, contenido presentado y precondiciones de
  concurrencia. Un control global de transacción no exige transportar toda la historia a la IA.

**Comprobación:** caso original antes de PLAN; documentos ajenos y prosa sin clasificar
de origen; fuente mixta/global; requisito compartido; dependencia entrante/transitiva;
conflicto de pertenencia; adjuntos de texto y visuales; cambio concurrente aplicable.
Recorrer hasta el inicio autorizado de implementación, no detenerse al cerrar propuesta.

**Salida de fase:** el crecimiento de documentación independiente no arrastra sus cuerpos
ni recursos al contexto ni exige su clasificación general por el usuario; las obligaciones
aplicables y las dudas críticas permanecen visibles. La misma selección sirve al recorrido
completo y puede regenerarse en otro chat o worktree.

## F4. Hacer proporcionados continuidad y registros

**Componentes:** guías de las seis skills, `v3_lifecycle`, `v31_review`,
`v31_corrections`, `v3_verification`, `v3_quality` y selección de eventos.

**Trabajo:**

- Mostrar continuidad actual, bloqueos, decisiones vigentes y evidencia necesaria;
  conservar el resto del historial consultable mediante referencias.
- Establecer qué dato nuevo exige un checkpoint y qué ya queda cubierto por una transición,
  evidencia o decisión. No duplicar una narración solo para cambiar de skill.
- Distinguir reintentos de una operación de observaciones posteriores. Diseñar idempotencia
  donde falte sin deduplicar por igualdad de texto ni borrar hechos distintos.
- Especificar el recorrido corto de una corrección ya cubierta; para cambios nuevos pequeños,
  usar propuesta conjunta concisa y referencias a contratos estables, manteniendo el plan suficiente.
- Reutilizar evidencia vigente solo cuando su sujeto, configuración, dependencias y edad
  lo permitan. Un fallo o una reserva no desaparece por mostrar únicamente la continuidad actual.

**Comprobación:** reanudar sin cambios, cambiar de persona, repetir consulta/operación,
añadir una observación legítima idéntica en texto, corregir dentro del encargo y ampliar
alcance. Incluir rechazo, corrección y nueva aceptación; preservar evidencia negativa.

**Salida de fase:** cero aprobaciones o documentos adicionales por una consulta/reanudación
sin hechos nuevos; decisiones y observaciones distintas conservadas; no reapertura de
especificación para una corrección que sigue dentro del acuerdo y autorización vigentes.

## F5. Preparar migración, instrucciones y distribución

**Componentes:** las seis entradas y referencias, `V3-COMMON`, `USER-DECISIONS`,
guías por familia, `V3-OPERATIONS`, bootstrap/host Copilot, `dual_distribution`,
almacenamiento, migración de documentos y runtime, y sus validadores.

**Trabajo:**

- Mantener las reglas comunes imprescindibles y localizar el procedimiento condicionado
  por operación. Medir lecturas completas y ampliaciones; no fragmentar por longitud solamente.
- Expresar sin ambigüedad qué es comando, campo de respuesta y siguiente acción.
  Corregir la orientación `journey/interventions` y el encaminamiento hacia referencias antiguas.
- Precisar formatos de origen soportados, formato de destino y runtime compatible.
  Si se elige migración, ofrecer previsualización de cambios y dudas antes de aplicar
  la conversión, con comprobación de concurrencia y conservación del estado original.
- Mantener trazabilidad de origen a destino: identidades, obligaciones, decisiones,
  responsables, fechas, evidencia y reservas. Una transformación de formato no crea
  aprobaciones nuevas ni invalida acuerdos por sí sola; una diferencia de significado
  requiere resolución explícita. Los hashes de archivos transformados pueden cambiar;
  se conserva la referencia a los originales y a la base de las decisiones históricas.
- Probar proyectos con propuestas, planes y tareas en curso, reintento tras interrupción
  y recuperación conjunta de documentos y runtime. Restaurar el estado anterior no puede
  borrar silenciosamente trabajo posterior; ese caso requiere conciliación.
- Limitar la compatibilidad antigua a lectura, conversión y recuperación necesarias.
  Un runtime incompatible debe explicar el siguiente paso sin escribir sobre el formato
  nuevo. No documentar la ejecución antigua como alternativa vigente sobre ese formato.
- Asegurar que Codex y Copilot seleccionan la misma lógica, respetan el runtime fijado
  y no cargan simultáneamente entrypoints de plugin y de proyecto.
- Verificar los escenarios condicionales visuales, controles de calidad y acciones externas
  con las capacidades reales del host. No crear integraciones nuevas para resolver el coste.

**Salida de fase:** rutas legibles y coherentes con la CLI; límites de compatibilidad
explícitos; transición comprobada desde proyectos 3.2 si cambia el formato; paquetes
concordantes. El comportamiento real de cada host se observa aparte.

## F6. Comprobar el conjunto y preparar la release candidata

### Casos de referencia

| Caso | Skills principales | Comparación necesaria |
|---|---|---|
| Pregunta de estado o comportamiento | Help | Respuesta suficiente, sin escritura ni revisión integral innecesaria. |
| Corrección local | Define/readiness/implement/verify | Variante cubierta y variante sin cobertura; completar corrección y verificación. |
| Ajuste de interfaz | Define/implement/verify | Recursos visuales necesarios y ajenos; dirección confirmada y cambio material. |
| Nueva funcionalidad | Define/readiness/implement/verify | Propuesta y plan suficientes, contrato compartido y evidencia de resultado. |
| Cambio de contrato compartido | Define/readiness/verify | Conservar consumidores y obligaciones entrantes, sin independencia ficticia. |
| Reanudación o relevo | Help/readiness/implement | Fuentes recargadas tras pérdida de contexto; autorización y responsables vigentes. |
| Adopción y migración | Adopt-existing/readiness | Alcance acotado, conservación, continuación y recuperación, sin aprobar historia de nuevo. |

Son observaciones acotadas de esta mejora, con escenarios negativos focales que se
reutilizan entre casos. No se crea una campaña permanente adicional de publicación.
La comprobación de recuperación, excepciones y formatos se mantiene en las regresiones
existentes, ampliadas solo donde cambien contratos de lectura o escritura.

### Medidas y condiciones de aceptación

- **Tokens:** entrada y salida por inferencia cuando el host las exponga, distinguiendo
  caché; resultados de herramientas y texto único/acumulado por separado. Una instantánea
  de prompt no es un acumulado. Si el host no expone la medida, declarar la limitación.
- **Tiempo:** tiempo total y atribuible al plugin, I/O/herramientas, espera del modelo,
  infraestructura y personas, con el retrabajo incluido y sin doble conteo de concurrencia.
- **Gestión:** documentos semánticos, consultas, ampliaciones, confirmaciones y reintentos.
  Contar objetos del almacén por separado.
- **Resultado:** tarea completada, contrato conservado, pruebas suficientes, errores y
  correcciones. Un flujo bloqueado no puede computar como una entrega más barata.
- **Comparabilidad:** misma tarea y estado de origen, modelo/configuración, host y condiciones
  de caché documentadas. Repetir solo cuando la variación impida decidir el efecto observado.
- **Migración y amortización:** comparar el coste inicial más el trabajo posterior en
  el formato nuevo con el mismo trabajo continuando en 3.2. Informar por separado del
  punto de compensación en tokens y en tiempo para el horizonte fijado en F0. Incluir
  mantenimiento de metadatos y excepciones; declarar los límites de extrapolación.
  Si se exige migración, el ahorro recurrente debe compensarla en ambas medidas dentro
  de ese horizonte. Un caso bloqueado, un resumen insuficiente o costes omitidos no
  acreditan ahorro. La comparación parte de documentación 3.2 sin preparar a mano.

Los presupuestos establecidos y justificados en F0 se comprueban aquí. Se exige reducción observable de
tokens y tiempo documental en corrección/reanudación, y ausencia de regresiones sin
justificar en los demás casos. El ahorro no puede conseguirse a costa de más consultas,
decisiones innecesarias, errores o revisión manual general del histórico. La conversión
inicial automatizada, cuando se elija, se contabiliza como migración. Una comparación
inconcluyente permanece pendiente; no se sustituye por un porcentaje de caracteres.

### Entrega técnica y publicación

1. Revisar diff, contrato, fixtures y regresiones focales de los componentes modificados.
2. Acreditar paquetes, formatos y comportamiento equivalente del núcleo en los dos hosts.
3. Registrar por separado observación real de Codex, de Copilot y límites pendientes.
4. Componer la release candidata con las demás mejoras ya aceptadas, incluidas las de
   migración/inventario si corresponde. Confirmar compatibilidad y versión por los cambios
   efectivos, sin asumir de antemano que basta una patch release.
5. Seguir [VALIDATION.md](../../../docs/VALIDATION.md) para publicación cuando exista la
   autorización correspondiente. El gate técnico no convierte `not-run` humano en aceptación.

No se crean commits, pushes, instalaciones ni actualizaciones de consumidores como
parte de este plan. El runtime del consumidor requerirá su actualización autorizada;
publicar el plugin no corrige automáticamente la aplicación de la incidencia.

## Trazabilidad y estado

| Hallazgo global | Fases que lo tratan |
|---|---|
| GD-01: aplicabilidad y contexto | F0, F3, F5, F6 |
| GD-02: duplicación de transporte | F1, F5, F6 |
| GD-03: historial en presentaciones | F1, F3, F4, F6 |
| GD-04: paginación y evaluación | F1, F2, F6 |
| GD-05: preparación y validaciones | F2, F6 |
| GD-06: coste mínimo del método | F0, F4, F5, F6 |
| GD-07: registros y reintentos | F4, F6 |
| GD-08: rutas de instrucciones | F5, F6 |
| GD-09: hosts y runtime | F2, F5, F6 |
| GD-10: almacenamiento existente | F2, F4, F5, F6 |
| GD-11: medición completa | F0, F6 |

La revisión global y la preparación de este plan están completadas. La posibilidad de
migrar documentación a cambio de una mejora está aceptada por el usuario. F0–F6 están
autorizadas para desarrollo; su progreso, comprobaciones y límites se registran en
[IMPLEMENTATION.md](IMPLEMENTATION.md). La autorización no acredita resultados futuros.
