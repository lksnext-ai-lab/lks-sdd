# Implementación de las presentaciones y la carga de contexto

Fecha: 2026-10-08. Ámbito: árbol de trabajo local, pendiente de publicación.
La petición «impleméntalo todo» autoriza esta implementación. Se han conservado
los cambios anteriores de almacenamiento y migración, las seis skills, los Markdown
canónicos y las fuentes de contrato de `specs/canonical/`.

## Resultado incorporado

`decision-view` prepara un mensaje de solo lectura con título del cambio, apartados
por decisión, fuentes recuperables, incidencias y procedencia del contenido mostrado.
El catálogo contiene 18 perfiles y cubre las 58 acciones públicas actuales, sus
variantes agrupadas y las consultas de diseño y comunicación. Las rutas históricas
con escritura no disponible siguen declarando esa limitación.

Las especificaciones conservan siete H2. La solución técnica describe los componentes
reales afectados: responsabilidad, situación actual, cambio, contratos, datos,
errores/permisos, comprobación y naturaleza observada o propuesta. Las obligaciones
en prosa, límites, negaciones, condiciones adicionales y adjuntos se conservan.
Un borrador se puede leer y comentar sin aprobarlo. La validación estructural no
demuestra que el diseño técnico sea correcto: esa valoración sigue siendo parte
de la revisión del contenido.

Plan y encargos asocian tarea, responsable, alcance, dependencias y pruebas. Las
decisiones sobre resultados recuperan también las tareas vinculadas inversamente
a la petición, sus evidencias y el candidato observado. Las excepciones mantienen
sus reservas. Un rechazo sin archivo conserva expresamente la evidencia pendiente
y exige nuevas comprobaciones para resolver el defecto.

Las decisiones nuevas requieren `presented`, obtenido al presentar la misma operación
y sus datos. Se comprueban contenido, fuentes, persona, destinatario, candidato,
configuración, adjuntos y destino cuando correspondan. Esto añade procedencia al
registro de decisión; las reglas existentes siguen decidiendo autoridad y vigencia.
Un recibo no demuestra por sí solo que una persona haya leído el mensaje. Las
decisiones anteriores válidas se conservan; los registros informativos no exigen
firmas nuevas y las operaciones agrupadas mantienen sus efectos separados.

La salida CLI compacta incluye una sola copia del Markdown; `--json` permite
inspeccionar las fuentes y la base completas. La orientación de intervenciones
incluye la consulta y las guías necesarias para preparar la decisión, conservando
el alcance total aunque la lista visual esté paginada.

## Integración de instrucciones

| Elemento | Implementación |
|---|---|
| Entradas | Seis skills con objetivos e invocación implícita conservados. |
| Reglas comunes | `V3-COMMON.md` conserva fuentes, autoridad, suficiencia y continuidad. |
| Índice de presentación | `USER-DECISIONS.md`, protocolo y rutas por familia. |
| Procedimientos | Nueve guías; selección cerrada en `v3_decision_profiles.py`. |
| Composición | Unión sin duplicación: plan + encargos; integración + aceptación; corrección + verificación. |
| Recuperación del contexto | Relectura tras compactación, cambio de evento, contenido o runtime; un hash no sustituye leer. |
| Operaciones | Campos y ejemplos en `V3-OPERATIONS.md`; no se copian en cada skill. |
| Distribución | Núcleo idéntico y cierre de referencias en ambos paquetes; resolución dentro del runtime fijado. |

La organización afecta a instrucciones por evento y al transporte de la vista.
No cambia la selección conservadora del contexto de ejecución. La presentación
utiliza el lector existente de relaciones, reglas globales, prosa sin clasificar y
adjuntos; su delimitación no sustituye el contexto necesario para implementar.

| Regla trasladada | Origen | Destino y condición |
|---|---|---|
| Procedimiento de Sonar y dependencias | Detalle de `V3-COMMON.md` | `verification.md`; el núcleo conserva su obligatoriedad según configuración. |
| Campos de revisión, encargos y corrección | `V31-REVIEW.md` | `V3-OPERATIONS.md`; lectura al preparar esos comandos. |
| Mapa de hitos, agrupación y continuidad | `V31-REVIEW.md` | Conservado; el detalle de presentación se enlaza por familia. |
| Forma del mensaje y contenido mínimo | Plan de presentación | Índice, catálogo y nueve guías compartidas; sin copias completas en cada skill. |

## Cobertura de las quince tareas

| Tarea | Resultado local | Evidencia principal |
|---|---|---|
| PV-01 | Contrato de entrada/salida, perfiles, rutas y casos incorporados. | Catálogo, índice, tests de rutas y fixtures. |
| PV-02 | Lectura de borradores, condiciones y adjuntos sin escrituras. | Tests de literalidad, pendientes, prosa extensa y repetición. |
| PV-03 | Generador y siete apartados de especificación integrados. | Tests de formato, detalle técnico e inyección de Markdown. |
| PV-04 | Procedencia exigida a decisiones nuevas, reutilización histórica. | Tests de ausencia/caducidad del recibo y acuerdo anterior. |
| PV-05 | Las seis referencias v3 enlazan las familias aplicables. | Contrato del plugin y revisión independiente de las instrucciones. |
| PV-06 | Módulos y guías incluidos en distribución y runtime. | Ejecución de la consulta desde ambos paquetes y prueba de actualización/rollback. |
| PV-07 | Regresiones focales y revisión del cambio. | Resultados técnicos registrados al finalizar esta verificación. |
| PV-08 | Protocolo preparado y lectura independiente por agente realizada. | Observación humana en ambos hosts **pendiente**; Copilot real **not-run**. |
| PV-09 | Configuración, adopción, migración y reconciliación adaptadas. | Pruebas de gobierno, actualización y continuidad de legado. |
| PV-10 | Plan, encargos, relevo y continuidad integrados. | Pruebas de revisión integral, equipo y workflow. |
| PV-11 | Pruebas, resultados, rechazo y corrección integrados. | Pruebas de integración, revisión y resultados desde petición. |
| PV-12 | Excepciones, revocación, recuperación y destino externo adaptados. | Regresiones de gobierno, recuperación y cambio de destinatario. |
| PV-13 | Aclaración breve y decisiones técnicas/visuales diferenciadas. | Pruebas de identidad, observación de imágenes y cambios de alcance. |
| PV-14 | Nueve recursos, catálogo cerrado y composición sin duplicación. | Pruebas de cobertura, recursos ausentes y ejecución empaquetada. |
| PV-15 | Medida reproducible de instrucciones y transporte; límites explícitos. | Informe JSON y comprobación independiente; coste total en hosts pendiente de PV-08. |

## Correspondencia con los cuarenta criterios

“Técnico” acredita el comportamiento probado y la integración de instrucciones.
Los criterios que dependen de comprensión humana o coste de tarea completa no se
declaran satisfechos mediante inspección estática o fixtures.

| Criterios | Cobertura y límite |
|---|---|
| AC-01, AC-02 | Técnico: H1, H2 por perfil, etiquetas en castellano y formato reducido para aclaración. Revisión humana final pendiente. |
| AC-03, AC-04 | Técnico: solución por componente, campos concretos y distinción observado/propuesto; corrección semántica exige revisión. |
| AC-05, AC-13 | Técnico: restricciones enlazadas, prosa de petición, campos adicionales, límites/negaciones y condición al final de texto extenso. |
| AC-06, AC-11 | Técnico: borrador consultable, repetición determinista y ausencia de escrituras por consulta. |
| AC-07, AC-09 | Técnico: selección parcial, cierre integral, autoridad, excepciones y vías directas/agrupadas conservadas. |
| AC-08, AC-27 | Técnico: cambios en fuentes, código, evidencia, destinatario y destino modifican la base; la operación comprueba de nuevo sus condiciones. |
| AC-10 | Técnico: aprobación anterior sin formato nuevo permanece vigente; no se fabrica otra firma. |
| AC-12 | Técnico: datos literales no crean H1/H2 ni HTML; ausencias y referencias inválidas no permiten aprobación positiva. |
| AC-14, AC-38 | Técnico: mismo núcleo, nueve guías y referencias verificadas en ambos paquetes temporales. |
| AC-15 | **Pendiente de observación humana en ambos hosts.** |
| AC-16, AC-32 | Técnico: 58 acciones públicas, variantes y rutas condicionales cubiertas por catálogo cerrado. |
| AC-17, AC-18 | Técnico: decisiones vigentes y agrupación conservadas; conteo conversacional real pendiente de PV-08. |
| AC-19, AC-20 | Técnico: gobierno, personas, controles, configuración vigente/propuesta y conservación en migración. |
| AC-21, AC-22 | Técnico: tarea/responsable, dependencias, pruebas, alcance, destinatario y oferta vigente. |
| AC-23, AC-24 | Técnico: evidencia recuperable, candidato, controles y orden de integración/aceptación; ningún fixture se declara prueba humana real. |
| AC-25 | Técnico: desacuerdo sin evidencia ficticia, clasificación correctiva y comprobación posterior al fallo. |
| AC-26 | Técnico: reservas, vigencia y límites de excepciones; revocar no borra trabajo ni concede nueva autoridad. |
| AC-28 | Técnico: contenido/destino explícitos; no añade escritores de publicación ni reactiva funciones históricas. |
| AC-29 | Técnico: consulta antes de inicializar y explicación de recuperación incompleta, sin escrituras. |
| AC-30 | Técnico y revisión por agente de varios perfiles; comprensión humana pendiente. |
| AC-31, AC-33 | Técnico: seis skills, invariantes conservadas, matriz de traslado y contexto de ejecución sin activar selector experimental. |
| AC-34, AC-37 | Técnico: catálogo de recursos del runtime, rutas/propósitos desconocidos rechazados, contenido del consumidor tratado como datos. |
| AC-35 | Técnico: dependencias de guías compuestas y selección tras cambiar el evento. |
| AC-36 | Instrucciones y rutas preparadas; recuperación conversacional tras compactación requiere observación real. |
| AC-39, AC-40 | Comparación estática y regresiones locales; consumo facturado, latencia total de host y tasa de error humana **no medidos**. |

## Comprobación independiente y eficiencia

Una revisión independiente con proyectos sintéticos detectó omisión de tareas en
aceptación, metadatos internos visibles, pérdida de asociación tarea/responsable,
una aclaración contradictoria, omisión de prosa de petición y un apartado vacío
en plan con encargos. Se corrigieron y se añadieron regresiones. El agente confirmó
el contenido recuperado, la asociación, la prosa literal y el rechazo de aprobación
ante una condición crítica. La integración previa y los desacuerdos sin artefacto
también han superado sus regresiones focales. Una última revisión detectó una exención
demasiado amplia para respuestas negativas, listas vacías con significado perdido,
informes de calidad omitidos y una carrera entre presentación y preparación. Se
corrigieron conservando los requisitos vinculados y las huellas capturadas antes de
preparar; sus pruebas específicas han pasado.

El [informe de instrucciones](evidence/instruction-measurement.json) compara doce
rutas con las nueve guías completas manteniendo la misma funcionalidad. Registra
archivos y huellas, caracteres normalizados y número previsto de lecturas. El
snapshot anterior sirve de referencia de funcionalidad anterior, no de control
equivalente. Las rutas seleccionadas reducen entre 39,94 % y 68,29 % los caracteres
de instrucciones frente a cargar todas las guías. Esta medida no se atribuye a
tokens facturados ni a la tarea completa.

En la comprobación independiente de una aceptación sintética, el transporte compacto
ocupó 3.522 caracteres frente a 30.609 del objeto detallado, conservando el mismo
Markdown y recibo. Es una observación puntual del transporte, no una promesa de
ahorro general. La CLI conserva el modo detallado para recuperar todas las fuentes.

## Resultado técnico final

**56 casos focales superados**, sin omisiones contadas como éxito. Los fallos
encontrados durante el desarrollo se corrigieron y se repitieron sus casos.

| Conjunto | Casos superados | Alcance |
|---|---:|---|
| Presentación y rutas | 18 | Incluye fuentes literales, TOCTOU, listas vacías, resultado por petición, imágenes y ambos paquetes. |
| Revisión integral | 11 | Ocho casos pasaron en la suite y los tres casos afectados por la composición se repitieron con éxito. |
| Workflow y gobierno/calidad | 17 | Autoridad, política, asignación, relevos, evidencias, excepciones y vigencia. El caso de calidad se repitió con la nueva aserción del informe recuperable. |
| Integración | 5 | Partes funcional/técnica, dependencias, porciones, clones y aceptación separada. |
| Distribución y actualización | 1 | Actualización del runtime fijado, CLI y rollback. |
| Continuidad de migración | 1 | Plan heredado, conservación de acuerdos y autorización actual. |
| Entradas públicas actuales | 3 | Alta 3.1, perfiles explícitos, actualización 3.0 y recorrido de ejecución completo. |

El contrato del plugin y `git diff --check` han pasado. No hay cambios en
`specs/canonical/`. Se revisaron el diff y los archivos nuevos, distinguiéndolos de
los cambios de almacenamiento/migración ya presentes y concurrentes.

La [salida de las nuevas pruebas](evidence/presentation-tests.json) conserva el
resultado del runner. El [resumen de comprobaciones](evidence/verification.json)
registra los conjuntos y su alcance. Puede revisarse también un
[ejemplo sintético generado de especificaciones](evidence/specification-example.md);
no describe un proyecto real ni constituye una aprobación humana.

## Estado de entrega

La validación de esta implementación se completó en el árbol local antes de crear
commits. La integración local en `main` se autorizó por separado el 2026-10-08;
publicación, instalación en consumidores y push siguen pendientes. La aceptación humana y la ejecución
real de Copilot siguen separadas de las comprobaciones técnicas. El protocolo de
[observación de hosts](../../V3-HOST-ACCEPTANCE.md) conserva esos pendientes.
