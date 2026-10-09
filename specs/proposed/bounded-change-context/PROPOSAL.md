# Trabajo documental proporcionado al desarrollo

Fecha: 2026-10-09. Revisión: 6. Identificador de mantenimiento: **MEJ-ALCANCE-01**.
Estado: **desarrollo autorizado; candidata técnica local preparada**.
Destino preparado: **3.3.0-rc.1**, pendiente de integración, gate oficial y publicación.
La aceptación de uso y el ahorro real siguen pendientes de observación.

La petición «haz una propuesta con la intención de que sea una de las mejoras
para sacar una nueva release» autoriza preparar este documento. Su inclusión
definitiva y publicación requieren sus decisiones respectivas. La petición posterior
de continuar hasta preparar una release autoriza el desarrollo descrito en
[IMPLEMENTATION.md](IMPLEMENTATION.md), planificando y comprobando cada tarea.
La revisión 2 incorpora la preocupación posterior por un posible uso excesivo de
documentación al desarrollar cualquier cambio. Amplía el diagnóstico al recorrido
habitual y deja de presuponer que nuevas declaraciones de alcance son la solución.
La revisión 3 incorpora la prioridad expresa de reducir tokens de IA y tiempo de
desarrollo, contrastada con la sesión y la respuesta original de la incidencia.
El [análisis de costes](ANALYSIS.md) desarrolla la evidencia, las prioridades y sus límites.
La revisión 4 incorpora la [revisión global de las seis skills](GLOBAL-AUDIT.md)
y el [plan conjunto por fases](PLAN.md), preparados tras la autorización del usuario.
La incidencia se conserva como un caso de regresión dentro del alcance global.

La revisión 5 incorpora una **decisión del usuario**: se admite migrar la documentación
de proyectos con plugin 3.2 si la mejora posterior lo justifica. Conservar su formato
actual deja de ser obligatorio. El formato de destino sigue siendo una propuesta por
diseñar; la evaluación incluirá el coste de migración y el ahorro posterior, por separado
en tokens y tiempo. Esta decisión no autoriza ejecutar una migración en consumidores.
Estos identificadores organizan el mantenimiento del plugin; no registran personas
ni decisiones de un proyecto consumidor. Se sigue la documentación de propuestas
existente en este repositorio, que no tiene `.lks-sdd/project.json`.

La revisión 6 incorpora esa autorización y la implementación: schema/método actuales,
selección aplicable, transporte compacto, evaluación reutilizable, continuidad y
declaraciones opcionales de prosa con revisión exacta. La transición del runtime sigue
explícita y recuperable. Las pruebas sintéticas se distinguen de aceptación humana,
consumo facturado y corrección del consumidor original.

## Objetivo

Conseguir que leer, producir, mantener y validar documentación sea proporcionado
al cambio, sus riesgos y dependencias durante todo el desarrollo con el plugin.
El incidente es el caso de regresión inicial de un posible problema transversal.
La mejora debe justificar qué información necesita cada operación, qué puede
reutilizar y qué nueva decisión o evidencia necesita registrar.
Sus resultados principales serán reducir el consumo observado de tokens y el
tiempo atribuible al trabajo documental del recorrido completo, incluyendo lecturas,
ampliaciones, herramientas, preguntas y retrabajo. Conservar el contrato aplicable
y la calidad del resultado será condición para aceptar esas reducciones.

Conservar información para trazabilidad no obliga a introducirla íntegramente en
el contexto de cada tarea ni a someterla de nuevo a aprobación. El usuario debe
entender qué se propone, qué obligaciones le afectan y cómo continuar. Se mantendrán
el contrato aplicable, la calidad del código y los controles del método.

El ámbito de trabajo será la petición y las unidades de propuesta acordadas.
«Centrarse en la sesión» expresa esta necesidad de foco: el ámbito debe persistir
al cambiar de chat, agente o worktree, y conservar las reglas globales y dependencias
necesarias. La fecha de modificación de los archivos no determinará su relevancia.

### Hechos observados

- La respuesta original del consumidor confirma un bloqueo de `close-proposal` anterior al
  PLAN/TASK: 1.213 fuentes, 245 adjuntos, 92 pendientes de observación y 11.610.121
  caracteres de Markdown. Se comprobó la composición del paquete; no se ha revisado
  la aplicabilidad semántica individual de sus 1.213 fuentes.
- El archivo de respuesta ocupa 41.471.970 bytes; repite los cuerpos en `sections`
  y `markdown`. El host lo truncó antes de entregarlo al modelo. Su tamaño no
  equivale a tokens facturados. La llamada que generó esa vista duró 72,9 segundos.
- En el tramo inicial de la sesión hubo 114 llamadas a herramientas; sus métricas
  disponibles suman 91.856 tokens de resultados y faltan métricas en tres llamadas.
  Las lecturas del propio plugin aportaron
  25.978 tokens mediante `view`, frente a 25.221 de código de aplicación. Una
  instantánea registra 135.635 tokens de prompt y 134.867 de `cache_read`; no es
  el consumo acumulado ni puede sumarse a las salidas de herramientas.
- En la reproducción sintética local con el plugin instalado 3.2.0, una propuesta
  pasó de 1.405 caracteres y `complete=true` a `complete=false` al incorporar una
  imagen enlazada desde prosa de otro documento. Añadir 25 documentos sin relación
  elevó la vista a 105.626 caracteres. La consulta no escribió en el proyecto.
- Un requisito perteneciente a otra propuesta por sus relaciones entró en la
  selección cuando no repetía `data.request`. El mapa de pertenencias ya conocía
  su propuesta. Añadir ese campo lo excluyó en el mismo escenario sintético.
- El control de aprobación rechazó la vista incompleta incluso con su `receipt`.
  La salida compacta mantuvo todo el Markdown; el modo de comparación mantuvo
  la imagen histórica. Un `.log` de texto quedó pendiente de observación.
- La operación pública `context` usa por defecto `conservative=True`: añade
  elementos activos de todo el modelo, además de la prosa. `decision-view` y
  `facts_for` reutilizan `select`, aunque no activan esa ampliación conservadora.
  Por tanto, la incorporación de prosa no está aislada en el cierre de propuestas.
- Cuatro regresiones existentes de presentación y revisión integral pasaron durante
  el análisis; no cubrían estas combinaciones. Los resultados anteriores describen
  el defecto, no una corrección validada. Véase [la evidencia conservada](evidence/diagnosis-3.2.0.json).

**Inferencia:** existe un problema transversal potencial de selección y consumo de
documentación. Se ha comprobado la inclusión excesiva en estos mecanismos; no se
ha medido todavía su frecuencia ni coste en todas las tareas reales, ni se ha
demostrado generación excesiva de documentos o confirmaciones en todos los recorridos.
El runtime particular `3.2.0+sat-continuity.2` tiene diferencias de alcance y referencias
históricas; conserva los mecanismos principales examinados. Su código actual no
acredita los bytes ejecutados en cada momento de la sesión. No se atribuyen al plugin
las esperas ajenas, incluida una espera de 70,9 minutos por la VPN.

## Alcance incluido y excluido

**Incluido:**

- Revisar qué se lee, se entrega al modelo, se escribe y se vuelve a validar al
  consultar, definir, adoptar/migrar, comprobar preparación, implementar, verificar
  y reanudar cambios habituales. Distinguir el
  trabajo interno del runtime de la información cargada efectivamente en el host.
- Resolver el ámbito de una petición y sus propuestas antes de disponer de PLAN/TASK.
- Mantener el cierre de dependencias, interfaces compartidas, restricciones, criterios,
  política, revisores, decisiones críticas y evidencia aplicable.
- Acreditar el alcance de la prosa y seguir únicamente los enlaces aplicables;
  explicar los casos cuya relevancia todavía sea incierta.
- Aplicar esa resolución de forma coherente en vistas de decisión, revisión,
  planificación, readiness y contexto de implementación.
- Tratar documentos de texto y recursos visuales según la comprobación necesaria.
- Conservar vigencia, autoridad y trazabilidad de las decisiones; ajustar las guías
  de las seis skills y los adaptadores Codex/Copilot afectados.
- Incorporar regresiones sintéticas y una guía de continuación del consumidor.
- Reutilizar cobertura, decisiones y evidencia vigentes; evitar registros y
  confirmaciones repetidos cuando no exista un nuevo hecho o decisión material.
- Seleccionar continuidad y antecedentes de la misma petición según la operación;
  conservar el historial recuperable sin incorporarlo completo a cada respuesta.
- Hacer coherentes instrucciones, CLI y adaptadores, manteniendo lectura y recuperación
  de formatos soportados y la frontera explícita de migración para escritura actual.
- Evaluar y, si se elige el cambio de formato, preparar la conversión documental y
  actualización de runtime como parte de la solución, con conservación y coste medido.

**Excluido:** corregir `crypto.randomUUID` en la aplicación; cambiar sus APIs,
datos o infraestructura; eliminar o alterar el significado de su historia; ejecutar
instalaciones o migraciones en consumidores reales; publicar o desplegar; introducir MCP, conectores, hooks, apps,
servicios o agentes ejecutables. Tampoco se autoriza a omitir contratos por volumen
ni a declarar observado un adjunto mediante su hash solamente.

## Comportamiento esperado

1. La persona plantea una corrección y la revisión del mismo defecto en otras
   superficies. El agente registra ese alcance y sus exclusiones en una petición.
2. El plugin recupera su propuesta, obligaciones y dependencias. Reconoce la
   pertenencia por relaciones sin exigir metadatos redundantes en cada requisito.
3. Las fuentes cuya independencia esté acreditada no se convierten en contenido
   que haya que volver a validar. Las reglas globales y los contratos compartidos
   se mantienen aunque procedan de trabajos anteriores.
4. Una fuente ambigua se presenta como una duda concreta de aplicabilidad: qué
   fragmento falta clasificar, por qué puede afectar al cambio y qué decisión hace
   falta. No se exige observar todos sus recursos antes de resolver esa duda.
   Mientras pueda ocultar una obligación aplicable, impide la aprobación positiva
   de la porción afectada. Una consulta o un borrador siguen siendo posibles.
5. Acreditada la selección y revisados los recursos necesarios, se presenta la
   propuesta con los siete apartados habituales. La conformidad permite planificar.
   El plan y la ejecución mantienen sus propias autorizaciones y controles.
6. Al retomar el trabajo se recarga el contenido aplicable. Se detectan cambios
   relevantes y nuevas dependencias; no se fuerza una nueva conformidad por una
   modificación demostrablemente ajena al cambio.
7. Si el trabajo ya tiene especificación, plan y autorización suficientes, se
   continúa desde ellos. La consulta o la repetición de un comando sin un nuevo
   hecho no produce otro documento. Las decisiones compatibles se agrupan cuando
   la política lo permite, conservando sus efectos y autoridades separados.

Ejemplo de comunicación esperada: «La propuesta cubre la corrección de compatibilidad
y la revisión de las operaciones afectadas. Falta determinar si esta restricción
compartida también se aplica. Resolverlo permitirá terminar la propuesta y preparar
el plan». Las rutas, huellas y causas detalladas quedan disponibles para inspección.

## Solución técnica

Los comportamientos actuales siguientes están observados en el código. Todos los
cambios descritos son **propuestos**, pendientes de validación e implementación.

### Comprobar el coste del recorrido habitual

Antes de elegir nuevos formatos, se observarán los casos del plan conjunto: consulta,
corrección local, ajuste de interfaz, funcionalidad nueva, cambio de contrato compartido,
reanudación/relevo y adopción/migración. Se recorrerán las operaciones que realmente
correspondan a cada caso, con documentación existente y sin prepararla para que el
selector obtenga resultados favorables.

Se distinguirán cuatro costes: inspección interna de archivos e integridad;
contenido enviado al modelo y releído; documentos creados o modificados; y decisiones
solicitadas a la persona. Se medirán también finalización, correcciones y obligaciones
omitidas. Un escaneo interno global puede seguir siendo necesario sin transportar
todo su contenido al agente. Menos caracteres no acreditan una implementación correcta.

La evaluación determinará qué lecturas, escrituras y revalidaciones son necesarias,
redundantes o ampliadas por incertidumbre. Se usarán las herramientas y evidencias
existentes; este diagnóstico no añade un procedimiento documental al usuario ni
una nueva campaña permanente a la puerta de publicación.

El diagnóstico ya identifica prioridades concretas: corregir selección y ampliaciones
de alcance, transportar una sola representación del contenido y reutilizar cargas
validadas dentro de cada operación. `review` realiza dos cargas del modelo en el
perfil mínimo; un acierto de caché de `context` sigue cargando documentos y ejecutando
consultas Git. Una caché de cálculo no acredita ahorro de contexto para el modelo.
Se evaluarán índices y caché derivada con invalidación comprobable, conservando las
comprobaciones de concurrencia antes de aplicar cambios. Los presupuestos de tokens
y latencia se acordarán sobre recorridos de referencia; no se inferirán de caracteres
divididos por cuatro ni de una prueba aislada de serialización.

### Resolución del ámbito y dependencias

Componentes: [v3_scope.py](../../../scripts/v3_scope.py),
[v3_context.py](../../../scripts/v3_context.py) y
[v3_contract.py](../../../scripts/v3_contract.py).

Actualmente `memberships` calcula pertenencias por relaciones, mientras `select`
aplica parte del filtro mediante `proposal_units` y amplía por ausencia de
`data.request`. Se propone resolver primero las unidades de la petición o propuesta
seleccionada y construir un único cierre de aplicabilidad reutilizable por operación.
No necesitará que exista un plan para conocer el cambio.

El cierre conservará pertenencias múltiples, relaciones transitivas y contribuciones
entrantes relevantes. Las discrepancias entre pertenencia explícita y relaciones
se diagnosticarán; ninguna tendrá prioridad silenciosa para excluir obligaciones.
Cada inclusión tendrá procedencia y motivo. Se conservará evidencia consultable
de las exclusiones sin copiar su contenido a cada presentación.

Se comprobará con propuestas independientes, requisitos compartidos, reglas globales,
ciclos, dependencias transitivas, aportaciones entrantes y cambios de pertenencia.

### Prosa canónica y fuentes históricas

Actualmente se incorpora todo `model.prose`. Se propone determinar su aplicabilidad
reutilizando primero estructura, relaciones y decisiones existentes, con lectura
adicional cuando sea necesaria. No se considera elegida la introducción de un nuevo
registro de clasificación para cada documento o fragmento.

Si la información existente resulta insuficiente, se evaluará una declaración
verificable y reutilizable de alcance como alternativa. Deberá justificar que reduce
el trabajo total y no traslada al usuario la clasificación del histórico. Identificaría
fuente, contenido, ámbito, fundamento y procedencia en Markdown canónico; el índice
solo derivaría esa información. Su necesidad y formato siguen pendientes.

Las clasificaciones acreditadas se reutilizarán mientras sigan vigentes. No se deducirá que toda
la prosa pertenece al único bloque de un archivo: puede contener condiciones
globales o de otras unidades. Tampoco se clasificará por carpeta, antigüedad o
ausencia de cambios Git. Una contradicción o contenido cambiado requerirá reevaluación.

Para documentos existentes se compararán reconciliación incremental y conversión
inicial a una estructura canónica más explícita. Se admite recorrer el corpus una vez
para migrarlo, contabilizando su coste; no se exige al usuario clasificar manualmente
todo el histórico. Las dudas concretas se presentarán agrupadas, con sus fundamentos,
a quien tenga autoridad. La conversión no equivaldrá a aprobar otra vez funcionalidades
históricas ni permitirá inventar pertenencias. No se podrá prometer aislamiento completo
cuando siga sin acreditarse una posible obligación transversal.

La prueba partirá del estado documental existente e incluirá cualquier preparación
o migración necesaria. No se aceptará ahorro calculado únicamente después de una
clasificación costosa omitida del balance. El diagnóstico concretará la posible afección,
sin tratar la ausencia de metadatos como prueba de que toda la historia requiera nueva
conformidad. La estructura de destino deberá facilitar tanto el uso como el mantenimiento
posterior; no bastará con trasladar el coste a registrar más metadatos en cada tarea.

Si se eligen declaraciones nuevas, su formato exacto y compatibilidad con lectores
anteriores se cerrarán antes de implementarlas. Si exigen capacidad o versión documental nueva,
se versionará y aplicará por el mecanismo explícito de actualización del runtime.
La comprobación incluirá prosa global, documentos mixtos, fragmentos obsoletos y
conservación literal de negaciones, cifras y excepciones.

### Adjuntos y construcción de la vista

Componentes: [v3_context.py](../../../scripts/v3_context.py) y
[v3_decision_presentation.py](../../../scripts/v3_decision_presentation.py).

La selección de fuentes precederá al recorrido de sus adjuntos. Se unificará el
tratamiento de recursos enlazados y artefactos de evidencia, incluyendo texto
recuperable como logs y código. Leer un script no implica ejecutarlo; leer HTML
no acredita haber inspeccionado un prototipo visual. Imágenes, PDF o prototipos
que sean necesarios para la decisión mantendrán la observación correspondiente.

La vista distinguirá contenido pendiente, alcance incierto y observación pendiente.
Explicará el bloqueo real y su siguiente acción. Mantendrá texto normativo literal,
procedencia e integridad; no truncará silenciosamente ni resolverá el volumen
mediante resúmenes que sustituyan obligaciones. Los recursos ausentes o alterados
seguirán produciendo diagnósticos explícitos.
La salida habitual transportará una única copia del contenido necesario. Los
detalles ampliados y las fuentes completas seguirán siendo recuperables mediante
referencias, sin repetirlos en varios campos de la misma respuesta. El contexto de
implementación tendrá el contenido aplicable a esa operación. Las consultas de
estado no deberán reconstruir y emitir una revisión completa si no la requieren.

### Decisiones, continuidad y contexto de ejecución

Componentes: [v3_presentation_guard.py](../../../scripts/v3_presentation_guard.py),
[v3_approval.py](../../../scripts/v3_approval.py),
[v31_review.py](../../../scripts/v31_review.py) y
[v3_workflow.py](../../../scripts/v3_workflow.py).

Se mantendrá la vinculación entre decisión y contenido realmente presentado.
La base de una nueva decisión incluirá fuentes aplicables, declaraciones de alcance,
política y adjuntos necesarios. Cada consulta recalculará la aplicabilidad para
detectar una fuente nueva, una regla global o una dependencia antes ausente.
Se conservarán los controles de concurrencia entre presentación, preparación y
aplicación, también cuando aparezcan nuevas obligaciones durante ese intervalo.

La independencia se comprobará con pares de cambios: uno ajeno no debe invalidar
la decisión; uno aplicable sí. Las aprobaciones históricas no se descartarán por
un cambio de formato, ni se reinterpretarán como aprobación de contenido nuevo.

La ruta pública `context` mantiene actualmente una referencia conservadora más
amplia. Esta mejora necesita una decisión explícita sobre su evolución, respaldada
por las mismas garantías de aplicabilidad. Cambiar únicamente `decision-view` o
activar `comparison=true` no cumple esta propuesta. La validación debe recorrer
propuesta, plan, tarea y contexto efectivo de implementación.

### Instrucciones y distribución

Se ajustarán las reglas comunes y las referencias aplicables de las seis skills
para explicar el ámbito persistente, resolver dudas de relevancia y continuar lo
ya autorizado. Se mantendrán sus objetivos e invocación implícita. Los paquetes
Codex y Copilot deberán ejecutar el mismo comportamiento y conservar las mismas
garantías. La documentación distinguirá lectura de un borrador, conformidad,
autorización, ejecución y aceptación del resultado.
Se revisarán también las instrucciones que provocan ampliaciones y lecturas repetidas.
Un catálogo disponible servirá para localizar información; sus enlaces no implicarán
cargar todo el catálogo. La creación de documentación deberá corresponder a una
decisión, obligación, evidencia o necesidad real de continuidad identificable.

## Impacto

**Beneficio esperado:** un coste documental proporcionado al trabajo, menos contenido
ajeno y menos gestión repetida, con continuidad entre sesiones. La mejora se medirá
en el recorrido completo: obligaciones conservadas, calidad y finalización, lecturas,
escrituras, confirmaciones y tiempo observado. No se promete ahorro de tokens facturados.

**Riesgo principal:** excluir una obligación válida al determinar el alcance.
Las pruebas negativas y la vigencia de las declaraciones son esenciales. Otro
riesgo es resolver la presentación y trasladar el mismo bloqueo a planificación
o ejecución. Añadir metadatos y aprobaciones de clasificación podría aumentar la
carga administrativa; la evaluación comparará ese coste antes de elegir el mecanismo.

**Compatibilidad:** Markdown seguirá siendo canónico, aunque su organización y formato
puedan cambiar. Se conservarán significado, identidades, decisiones, evidencia y
procedencia, con correspondencia de origen a destino y originales recuperables.
Se comprobará la continuación de propuestas, planes y tareas en curso. El cambio de
documentos y runtime fijado tendrá previsualización, autorización y recuperación;
instalar la release no actualizará automáticamente al consumidor. No se exige que 3.2
opere sobre el formato nuevo. El corte, las capacidades de lectura/conversión y el
procedimiento de recuperación dependerán del contrato validado; no se mantendrá una
doble vía operativa indefinida solo por compatibilidad de formato.

**Encaje en la release:** esta propuesta es una mejora candidata independiente.
Puede compartir release con las correcciones de inventarios y migración actualmente
en trabajo, manteniendo evidencia y aceptación separadas. La integración deberá
comprobar su interacción con carga documental, almacenamiento y actualización de
runtime. Su implementación prepara metadatos y changelog de `3.3.0-rc.1`, etiquetados
como candidata local. No reutiliza la aprobación de 3.2 ni declara publicada la mejora.

La validación técnica de publicación seguirá [docs/VALIDATION.md](../../../docs/VALIDATION.md).
Las regresiones focales siguientes acreditarán esta implementación cuando exista;
no crean una batería global adicional obligatoria para toda release. Publicación,
instalación, observación por host y verificación en el consumidor se registrarán
por separado, conservando `not-run` cuando corresponda.

## Criterios de aceptación

Estos son los criterios del objetivo completo. El diagnóstico prueba el comportamiento
previo; la evidencia actual por criterio y las reservas se registran en
[la ejecución](IMPLEMENTATION.md). Las comprobaciones técnicas no acreditan por sí
solas los criterios de tokens facturados, tiempo humano o funcionamiento real del host.

| ID | Resultado exigido | Comprobación propuesta |
|---|---|---|
| AC-01 | Se revisa y cierra una propuesta concreta sin necesitar PLAN/TASK previo. | Recorrido sintético equivalente al incidente con responsables y política válidos. |
| AC-02 | Un requisito de otra propuesta no entra por faltar `data.request` si su independencia está acreditada. | Pertenencia por relaciones; variante compartida que sí debe entrar. |
| AC-03 | Se conservan reglas globales, restricciones y dependencias aplicables. | Casos transitivos, entrantes, ciclos y conflictos de pertenencia. |
| AC-04 | La prosa acreditada como ajena no arrastra sus imágenes ni logs. | Reproducción del enlace fuera de bloques con clasificación válida; variante global incluida. |
| AC-05 | La ambigüedad relevante bloquea la aprobación y explica qué falta clasificar. | Prosa sin alcance, documento mixto y declaración contradictoria u obsoleta; borrador consultable. |
| AC-06 | Los textos recuperables se leen como texto y los recursos visuales necesarios se observan. | `.log`, `.py`, HTML fuente/prototipo, imagen, recurso perdido y contenido alterado. |
| AC-07 | Una selección incompleta o un recibo obsoleto impiden aprobar; la herramienta no rellena observaciones automáticamente. | Llamadas directas, CLI y guías; autoridad y revisión obligatoria conservadas. Un hash no demuestra comprensión humana. |
| AC-08 | La decisión cambia ante obligaciones aplicables y permanece vigente ante contenido acreditado como ajeno. | Cambios pareados, reglas globales nuevas y aparición de dependencias entre consulta y aplicación. |
| AC-09 | El caso avanza por cierre de propuesta, plan autorizado, revisión de tarea e inicio de implementación. | Recorrido completo con contexto efectivo suficiente y controles de permisos, rama y calidad. |
| AC-10 | Retomar en otro chat o worktree recupera el mismo ámbito y contenido vigente. | Reinicio del proceso y fuentes recargadas; no dependencia de memoria del host. |
| AC-11 | La corrección avanza desde documentación existente sin exigir al usuario una clasificación manual general del histórico. | Fixture con prosa sin clasificar de origen y una variante de mayor volumen; resolver dudas concretas conservando obligaciones. Si requiere conversión inicial, incluir su coste. Se rechaza un ensayo que presuponga todo el histórico ya etiquetado. |
| AC-12 | Las consultas son de solo lectura y las clasificaciones se registran por operaciones autorizadas. | Comparación de snapshots y revisión de autoridad/procedencia. |
| AC-13 | La transición conserva significado, decisiones, procedencia, historia y trabajo en curso de un consumidor soportado. | Origen 3.2, correspondencia documental, runtime fijado, rechazo de escritura incompatible, interrupción/reintento y recuperación; sin migración silenciosa ni pérdida de trabajo posterior. |
| AC-14 | Codex y Copilot distribuyen el mismo comportamiento y las guías conducen al siguiente paso correcto. | Pruebas focales de paquetes e instrucciones; observación conversacional registrada aparte. |
| AC-15 | Los recorridos de las seis skills incluidos en el plan conjunto justifican el trabajo documental exigido y conservan la calidad del resultado. | Comparar consulta, corrección, interfaz, funcionalidad nueva, contrato compartido, reanudación/relevo y adopción/migración: inspección interna, contexto, relecturas, escrituras y confirmaciones; conservar los límites observados. |
| AC-16 | Consultar y reanudar trabajo ya cubierto no genera documentación o aprobaciones redundantes. | Repetición sin cambios materiales, continuación autorizada y variante con cambios aplicables que sí exige nueva decisión. |
| AC-17 | El crecimiento de historia independiente no arrastra un crecimiento equivalente de contexto ni de intervención humana. | Mismo cambio con distintos volúmenes documentales; contrastar fuentes necesarias, dudas justificadas y calidad, sin truncar obligaciones. |
| AC-18 | La mejora reduce tokens observados y tiempo documental del recorrido completo con un resultado equivalente. | Comparación antes/después por recorrido, con presupuestos definidos, métricas de caché, herramientas, preguntas y retrabajo; separar esperas de infraestructura y no sumar instantáneas como consumo total. |
| AC-19 | El transporte habitual evita cuerpos duplicados y las operaciones reutilizan su modelo validado cuando corresponde. | Contar contenido emitido, cargas y parseos; comprobar vigencia y concurrencia. Evitar trasladar el ahorro a consultas adicionales o a una revisión general del histórico. |
| AC-20 | La continuidad actual no requiere reenviar todos los eventos de la misma petición y el histórico sigue siendo recuperable. | Añadir avances anteriores sin modificar contrato ni resultado vigente; conservar bloqueos, reservas y evidencia necesarios. Distinguir el JSON detallado de la presentación ordinaria. |
| AC-21 | Si se exige migración, el ahorro posterior compensa su coste en tokens y tiempo dentro del horizonte de uso acordado. | Comparar conversión, revisión, dudas y mantenimiento más las tareas posteriores con las mismas tareas en 3.2. Fijar mezcla de tareas y horizonte antes de evaluar; informar ambos puntos de compensación y las métricas no observadas. |

Para declarar la mejora implementada se aportará evidencia recuperable por criterio,
incluidos casos negativos y reservas. Para incluirla como funcionalidad entregada
en una release, deberán estar validados su alcance y diseño, completado el plan
autorizado y superadas las comprobaciones aplicables a la implementación. La puerta
de publicación acreditará el candidato conjunto según la política vigente.

## Decisiones del desarrollo y reservas

**Ya decidido por el usuario:** una migración documental es admisible si supone mejora,
y se autoriza continuar el desarrollo hasta preparar una candidata. Las elecciones
técnicas y pruebas se detallan en el registro de implementación. No se presume ahorro
facturado ni se autoriza una migración real en consumidores.

| Decisión | Resolución del desarrollo | Reserva |
|---|---|---|
| Objetivo y alcance. | Desarrollo autorizado e incorporación a candidata 3.3.0-rc.1. | Aceptación del uso y publicación separadas. |
| Prosa y alcance existentes. | Declaraciones opcionales por fuente, hash y gobierno con presentación /2; sin conversión obligatoria del corpus. | La primera revisión de prosa no clasificada puede ser costosa; el consumidor original no ha sido reconciliado. |
| Contexto público. | Cierre literal común a decisiones y ejecución; referencia completa explícita. | Adopción mediante actualización autorizada del runtime fijado. |
| Presupuestos. | Una copia del cuerpo, una carga por consulta, cero escrituras por consulta; comparación sintética del recorrido y coste de clasificación. | Tokens facturados, tiempo humano y amortización real no observados. El horizonte inicial es una hipótesis de evaluación. |
| Versiones y compatibilidad. | Plugin 3.3.0-rc.1, presentación /2; schema 3.1 y método 3.1.0 conservados. | Runtime 3.2 continúa conservador; no activa la nueva acreditación de prosa. |
| Composición de candidata. | Eficiencia documental más correcciones previas de inventarios/migración, con evidencia separada. | Commit limpio, gate oficial y autorización de publicación pendientes. |

La respuesta original de `decision-view` y el registro de sesión ya se han analizado.
Faltan métricas completas por inferencia, una clasificación semántica de todas las
fuentes seleccionadas y un recorrido equivalente con la corrección implementada.
Esos límites impiden cuantificar aún el ahorro total o facturado y declarar resuelto
el caso del consumidor.

El plan conjunto se está ejecutando con la autorización posterior del usuario.
Su registro mantiene comprobaciones, fallos, correcciones y límites de evidencia;
la aceptación del objetivo completo y la publicación siguen separadas.
El siguiente paso del consumidor, una vez exista
una corrección disponible y autorizada para su runtime, será regenerar la revisión
de su petición, validar la propuesta, preparar y autorizar su plan y corregir el
error funcional. La nueva release del plugin no acreditará por sí sola ninguno de
esos resultados en la aplicación.
