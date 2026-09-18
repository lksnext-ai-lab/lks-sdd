# Compilador de contexto para LKS-SDD: revisión crítica y propuesta revisada

**Fecha de corte: 11 de septiembre de 2026. Estado: investigación y prototipos experimentales; propuesta de producto pendiente de implementación.**

## Dictamen

La propuesta inicial no supera el criterio de calidad solicitado. Encontramos tres fallos diferentes: eliminar contratos al abreviar, omitir obligaciones por confiar demasiado en índices y declarar suficiente un contexto incompleto. Una revisión conservadora recuperó la cobertura de los casos iniciales, pero nuevas perturbaciones volvieron a descubrir omisiones y una expansión de hasta 35,65 veces. Tampoco el código que pasó todas las pruebas iniciales resultó plenamente conforme al contrato.

La mejora principal debe ser **seleccionar evidencia con trazabilidad, proteger literalmente los contratos y ampliar el contexto cuando la tarea lo requiera**. La representación compacta viene después. No existe en este estudio una técnica que permita prometer «todo el contexto necesario con el mínimo de tokens» para cualquier tarea. Sí hay una arquitectura más defendible y una evaluación reproducible para evitar aprobar un ahorro aparente que empeore el código.

El estudio ha ejecutado seis sondas sobre los motores reales del plugin, 36 casos estructurales, 180 perturbaciones adicionales, cuatro entregas de código de doce funciones y pruebas de serialización. Se revisaron 21 fuentes primarias. Los originales, fallos y contraejemplos se conservan. No se han modificado el runtime, las skills ni las fuentes canónicas para implantar el compilador; tampoco se ha instalado ni publicado una nueva versión del plugin.

## 1. Qué objetivo conviene optimizar

El objetivo debe ordenarse así:

1. Evitar regresiones críticas y mantener o mejorar conformidad funcional, seguridad, integración y mantenibilidad.
2. Evitar declaraciones de suficiencia falsas, sin convertir el bloqueo de todas las tareas en una aparente solución.
3. Reducir el consumo completo para terminar correctamente la tarea, incluidas preparación, consultas, código generado, correcciones y verificación.
4. Comparar coste monetario y latencia por separado.

Una reducción del prompt no demuestra reducción del consumo total. Un contexto con todos los identificadores no demuestra comprensión. Un paquete que pasa un validador estructural no demuestra que su prosa esté completa. Y cien comprobaciones de una misma familia no equivalen a cien tareas independientes.

El mínimo buscado depende del modelo, la tarea y los descubrimientos durante la implementación. Conviene hablar de **un contexto suficiente según evidencia disponible, con incertidumbres explícitas**, no de un mínimo semántico garantizado. La ausencia de un enlace nunca debe convertirse por sí sola en prueba de irrelevancia.

## 2. Qué aporta la investigación reciente

Las publicaciones se usan como evidencia externa contextualizada, no como resultados obtenidos por LKS-SDD. La búsqueda es amplia, pero no una revisión sistemática exhaustiva. El catálogo conserva versiones, fechas y limitaciones en [research/sources.json](research/sources.json); el análisis ampliado está en [research/notes.md](research/notes.md).

| Línea | Evidencia relevante | Implicación para el plugin |
|---|---|---|
| Archivos de contexto del repositorio | La revisión de junio de 2026 sobre AGENTS.md encuentra más de un 20% de coste adicional medio y diferencias de éxito no significativas. Evalúa tareas principalmente Python, no todas las obligaciones de negocio. | Recortar explicaciones redundantes del repositorio; conservar requisitos y convenciones que no se deducen del código. [Estudio](https://arxiv.org/html/2602.11988v2). |
| Gestión sencilla del historial | Observation masking resultó competitiva frente a resúmenes por LLM, con aproximadamente la mitad del coste frente al historial completo en las configuraciones estudiadas. | Probar primero filtrado de observaciones antiguas y originales recuperables. No trasladar esa conclusión a la especificación normativa. [The Complexity Trap](https://arxiv.org/html/2508.21433v3). |
| Recuperación heterogénea de código | Agent Retrieval Bench, julio de 2026: 427 muestras de 25 repositorios, incluyendo consumidores afectados y ausencia de archivos relevantes. Ninguna familia domina todas las tareas. | Combinar símbolos, referencias, búsqueda literal y semántica según la necesidad; evaluar también búsquedas sin respuesta. [Paper](https://arxiv.org/html/2607.24882v1). |
| Poda orientada a resolver tareas | SWEzze informa reducciones del 51,8–71,3% de tokens de prompt y respuesta, con mejoras de resolución en su pipeline Agentless sobre SWE-bench Verified. | Es una dirección prometedora: preservar ingredientes de la reparación. No es una garantía trasladable a especificaciones nuevas ni una implementación disponible en este estudio. [Paper](https://arxiv.org/html/2603.28119v1). |
| Poda con acceso interno al modelo | SWE-Pruner Pro tiene resultados mixtos: en reparación un modelo mejora con más tokens y otro ahorra perdiendo resoluciones. Requiere estados internos. | No tratar el titular de ahorro como beneficio universal ni como una codificación que pueda aplicar cualquier plugin sobre una API. [Paper, julio de 2026](https://arxiv.org/html/2607.18213v1). |
| Compresión dinámica muy reciente | AttnCompress, 8 de septiembre de 2026: 53,17% de éxito frente a 51,17% de AgentDiet, pero por debajo del 55,17% sin compresión. El ahorro del 21,6% compara con AgentDiet. | La recuperación dinámica interesa; esta tabla no cumple una exigencia estricta de ausencia de regresión frente al contexto completo. [Paper](https://arxiv.org/html/2609.08318v1). |
| Contexto externo inspeccionable | RLM trata grandes entradas como un entorno consultable; Context-1 investiga recuperación y edición dinámica del contexto. Las llamadas adicionales y ventanas pequeñas pueden perjudicar. | Procesar y localizar fuera del modelo; incorporar detalle cuando se necesita y medir todas las llamadas. [RLM](https://arxiv.org/html/2512.24601v3), [Context-1](https://www.trychroma.com/research/context-1). |
| Representaciones ultracompactas | TOON/TRON muestra ahorro junto a pérdidas de exactitud y problemas de parseo en las tareas estudiadas. LLMLingua-2 aprende qué texto eliminar, con eficacia dependiente de tarea. | Mantener controles de Markdown claro y texto literal. Una estructura parseable o una alta tasa de compresión no demuestra fidelidad contractual. [TOON/TRON](https://arxiv.org/html/2605.29676v2), [LLMLingua-2](https://arxiv.org/abs/2403.12968). |

La recuperación contextual de Anthropic combina contexto de fragmento, BM25, búsqueda vectorial y reranking, y reduce fallos de recuperación en sus pruebas. Es una buena fuente de candidatos; el ranking no acredita que haya recuperado todas las restricciones necesarias. Un RepoMap también localiza símbolos sin sustituir el cuerpo de una función cuando importan sus efectos. [Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval), [Aider RepoMap](https://aider.chat/docs/repomap.html).

Las alternativas realmente alejadas del texto humano, como gist tokens o slots de un autoencoder, exigen entrenamiento y compatibilidad con el modelo. No son una notación universal que podamos guardar en Markdown y esperar que cualquier modelo descodifique fielmente. [Gisting](https://arxiv.org/abs/2304.08467v3), [ICAE](https://arxiv.org/abs/2307.06945v4).

Finalmente, caché y ahorro de contexto son cosas distintas. Un prefijo estable puede reducir procesamiento o coste sin retirar su contenido del contexto lógico. El plugin debe medir qué permite cada host; un CLI no puede prometer borrar mensajes que ya están en la conversación. Tampoco procede sumar porcentajes con denominadores diferentes. [Documentación de caché](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). Los experimentos propios de JetBrains con RTK refuerzan la necesidad de medir tareas completas: sus resultados no reprodujeron los grandes ahorros publicitados sobre salidas individuales. [Evaluación RTK](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/).

## 3. Qué ocurre realmente en LKS-SDD

Se usaron helpers existentes para materializar seis consumidores sintéticos: historial visual, incrementos compartidos, una tarea, tres tareas paralelas, ampliación parcialmente planificada y dos perfiles con una tarea contribuyente. Cuatro modelos eran estructuralmente válidos; los dos mínimos conservaban errores esperados. Los motores se ejecutaron sin modificar su lógica. [Método y resultados](repo-probe/README.md), [datos](repo-probe/results.json).

**Primer hallazgo: las filas activas no representan toda la prosa normativa.** En los seis casos, añadir una regla fuera de una tabla cambió `document_fingerprint` y no `active.fingerprint`. Editar una celda contractual cambió ambos. Los cuatro modelos válidos permanecieron válidos tras añadir la prosa. Es evidencia de un límite de representación, no una demostración de que todos los mecanismos actuales de autorización ignoren ese cambio.

**Segundo hallazgo: `coverage.by_task` representa propiedad primaria.** Una tarea contribuyente del fixture con dos perfiles recibió una lista vacía pese a necesitar requisitos compartidos. Usar ese mapping como contexto suficiente sería incorrecto. Hay que incorporar contribuciones, consumidores, contratos de integración, decisiones transversales y la definición de tarea.

**Tercer hallazgo: el contrato activo se resuelve por incremento.** No equivale a un paquete completo por tarea. Las filas activas y las proyecciones de semillas son mediciones parciales; sus reducciones aparentes no deben utilizarse como promesa de ahorro seguro.

**Cuarto hallazgo: los activos requieren tratamiento propio.** Cambiar bytes de un activo rechazado alteró solo la huella documental; cambiar uno confirmado alteró ambas. Se usaron bytes sintéticos, no validación visual. Una descripción textual o un hash no sustituye una imagen necesaria para implementar fielmente una interfaz.

Los puntos del código que explican estos resultados están en `scripts/contract_engine.py` —estructura de tablas y resolución de incremento— y `scripts/planning_engine.py` —propiedad primaria y validación de huellas globales de autorización—. El nuevo índice debe ser derivado. Los Markdown del consumidor continúan siendo canónicos, y una huella local del paquete no debe relajar las reglas actuales de autorización global.

## 4. Simulación de selección: el ahorro fácil pierde obligaciones

Un agente distinto del autor del selector preparó 36 casos con entradas y oráculo separados: 26 ejecutables y diez que requieren resolver contexto. Incluyen negaciones, excepciones distantes, DST, unidades, Unicode, aislamiento de tenants, concurrencia, migraciones, consumidores inversos, configuración dinámica, ámbitos homónimos, contribuciones compartidas, contratos visuales, memoria obsoleta y contenido no confiable. [Casos y protocolo](cases/README.md).

El selector recibió metadatos manuales: tipo, estado, ámbito y enlaces. No extrajo esos datos del lenguaje natural. Las selecciones se congelaron antes de puntuarlas. Se reservaron doce casos por su identificador; sus métricas agregadas iniciales y los valores posibles de metadatos eran visibles durante la revisión. Por ello **no se presenta esa reserva como evaluación ciega independiente**.

| Estrategia | Casos con todos los fragmentos exigidos / 36 | Tokens de referencia agregados | Ahorro agregado frente a todo |
|---|---:|---:|---:|
| Todos los fragmentos | 36 | 5.206 | 0% |
| Solo semillas de tarea | 0 | 1.116 | 78,6% |
| Cierre por enlaces explícitos | 10 | 3.319 | 36,2% |
| BM25 simple, cuatro fragmentos | 3 | 3.534 | 32,1% |
| Propuesta v1: reglas y cierre acotados por ámbito | 27 | 3.862 | 25,8% |
| Propuesta v2: expansión conservadora más amplia | 36 | 4.418 | 15,1% |

Tokens `o200k_base` del texto emitido, no facturación real. BM25 top-4 es un control sencillo, no una evaluación del mejor RAG actual. Los porcentajes de la tabla son agregados; los JSON también contienen medianas por caso y no deben confundirse. [v1](selection-experiment/results-v1.json), [v2](selection-experiment/results-v2.json).

V1 declaró listos ocho contextos que no debía y bloqueó innecesariamente dos casos. La revisión recuperó los 36 conjuntos esperados y clasificó correctamente los estados de este corpus, a costa de ampliar el contexto. Parte del éxito procede de incluir todo el dominio superior de los ámbitos afectados.

Los controles `full`, semillas, grafo y BM25 siempre devuelven `ready` por construcción; **no se compara su tasa de falsos listos con v2 para afirmar superioridad de recuperación**. La tabla compara cobertura. Para aislar readiness en una siguiente evaluación hay que aplicar el mismo guard a todos los selectores.

### Pruebas que rompen el resultado aparentemente perfecto

Se ejecutaron después cinco perturbaciones sobre cada caso: 180 simulaciones adicionales. No son 180 proyectos independientes. Algunas alteraciones incumplen esquemas que un validador previo real podría detectar; el harness estudia sensibilidad del selector sin modelar ese validador. [Resultados de estrés](selection-experiment/stress-results.json).

| Perturbación, 36 casos por variante | Resultado |
|---|---|
| Etiquetar todos los estados como activos | Ocho falsos listos, aunque la cobertura de fragmentos seguía completa |
| Asignar mal el ámbito de una pieza relevante | Once falsos listos; solo 22 contextos completos |
| Eliminar enlaces | Tres falsos listos |
| Suprimir una fuente necesaria del inventario | Doce falsos listos; 24 bloqueos, ningún contexto completo |
| Añadir 60 fragmentos hermanos normativos pero ajenos a la tarea | Sin pérdida de cobertura; crecimiento máximo de 35,65 veces |

La revisión interna descubrió además una raíz `retired` que v2 descartaba antes de validar, devolviendo `ready` con cero fragmentos. La construcción del diccionario tampoco rechazaba IDs duplicados. Se creó un **guard estructural aislado**, con ocho pruebas que pasan para raíces/dependencias inactivas, duplicados, referencias ausentes, ciclos y enlaces históricos opcionales. No se parcheó v2 retrospectivamente. El guard no identifica ámbitos semánticamente incorrectos ni archivos que el inventario omitió. [Prototipo y límites](tools/check_context_integrity.py), [ocho pruebas](selection-experiment/integrity-guard-tests.json).

La conclusión cambia: un grafo bien formado y la expansión conservadora son necesarios en algunos casos, pero insuficientes. El componente difícil que faltaba era **saber qué fuentes existen, cómo se aplican y cuándo esa clasificación es incierta**.

## 5. Código generado: conservación de contratos y límites del oráculo

Se prepararon doce funciones con requisitos menos triviales que un CRUD: redondeo por línea, DST, tombstones y duplicados, precedencia de denegaciones, copia profunda, paginación estable, formatos de Retry-After, protección de CSV, migraciones con pasos aplicados, claves Unicode exactas, control de versión y HMAC sobre bytes.

Las pruebas se escribieron y congelaron antes de recibir candidatos. Cada agente leyó únicamente el prompt asignado para generar código; no recibió el oráculo. Sus historiales previos eran distintos y no hubo varias semillas ni sesiones nuevas equivalentes. Las entregas originales no se repararon después de probarlas. Una cuarta entrega es expresamente una revisión informada, no otro brazo aleatorio independiente. [Diseño](code-experiment/design.json), [revisión](code-experiment/revision-design.json).

| Contexto servido | Tokens de entrada | Comprobaciones originales | Funciones con todas esas pruebas |
|---|---:|---:|---:|
| Completo: tarea, reglas y explicación adicional | 2.514 | 121/121 | 12/12 |
| Solo encargo directo | 655 | 101/121 | 5/12 |
| Compresión inicial supuestamente completa | 920 | 114/121 | 11/12 |
| Revisión que conserva literalmente entradas y salidas | 1.488 | 121/121 | 12/12 |

La compresión inicial **perdió el esquema de salida de `fold_events`**. El código devolvía una lista donde el contrato exigía un diccionario; siete comprobaciones fallaron. También había desaparecido el nombre exacto de un campo de migraciones, aunque ese candidato lo dedujo bien. El propio generador señaló estas carencias antes de ver los resultados. El identificador histórico `compact_complete` se conserva para reproducibilidad; no describe su calidad real.

Recuperar los contratos de entrada/salida permitió pasar las pruebas originales con un **40,8% menos de tokens de entrada**. Si sumamos únicamente prompt y archivo Python emitido, son 3.053 tokens frente a 4.229: un 27,8% menos de texto visible. No incluye instrucciones heredadas, herramientas, razonamiento, reintentos ni coste de preparar/revisar el paquete; **no es un ahorro total operativo demostrado**.

### El resultado 121/121 también falló una revisión posterior

El revisor detectó que el candidato revisado acepta `Fri, 11 Sep 2026 12:00:02 GMT junk GMT` y `... GMT GMT` como fechas válidas. Su parser tolerante extrae la fecha e ignora basura. El contrato exigía rechazar formatos inválidos. El candidato completo sí rechaza esos dos ejemplos.

Se ejecutaron los mismos tres casos nuevos —fecha válida y dos inválidas— sobre las cuatro entregas: completo 3/3; cada una de las otras, 1/3. Se conservaron en [posthoc-results.json](code-experiment/posthoc-results.json), separados del oráculo original. No se alteraron las puntuaciones históricas ni se corrigieron candidatos.

Por tanto, **no queda demostrada equivalencia de calidad entre la revisión compacta y la completa**. La revisión restauró las pruebas disponibles, pero no cerró el contrato. Ni siquiera podemos atribuir causalmente este defecto a compresión: existía una instrucción de rechazo en ambos prompts, y solo hay una muestra por entrega. Lo demostrado es que nuestro criterio de aceptación inicial era demasiado débil.

Se midió también un prompt de selección literal, sin explicación adicional: 1.610 tokens, un 36,0% menos que el completo. Su generación de código figura como **no ejecutada**. Esto deja un control especialmente importante para la siguiente evaluación: comprobar si una selección literal sencilla consigue casi todo el ahorro sin introducir otra capa de reformulación.

## 6. Cambiar Markdown no produce un ahorro universal

Se compararon 24 representaciones de cinco conjuntos: registros pequeños, cien registros regulares, estructuras anidadas, Unicode con separadores/saltos de línea y reglas con condiciones. Se midieron `o200k_base` y `cl100k_base` con `gpt-tokenizer` 3.4.0, descargado como dependencia portátil aislada y con hash verificado. No se afirma que sean el tokenizer de facturación del modelo utilizado. [Resultados](evidence/format-results.json), [procedencia](evidence/tokenizer-provenance.json).

Ejemplos en `o200k_base`:

| Contenido | JSON indentado | JSON compacto | Markdown de registros | Tabla compacta con celdas JSON |
|---|---:|---:|---:|---:|
| Dos registros | 70 | 38 | 61 | 40 |
| Cien registros uniformes | 3.402 | 1.802 | 3.099 | 1.118 |
| Anidado irregular | 143 | 68 | 94 | No aplicada |
| Unicode y caracteres que exigen escape | 86 | 63 | 81 | 66 |
| Condiciones y excepciones | 155 | 92 | 143 | 80 |

La tabla ayuda con repetición regular; JSON compacto gana en otros casos. Esto compara serializaciones concretas del estudio, no una superioridad general de JSON sobre Markdown. La reconstrucción sin pérdidas se verificó para los formatos reversibles, pero **no la comprensión del modelo**. Gzip/base64 a veces ocupa menos, pero el modelo necesita recuperar el texto: la compresión de bytes no hace desaparecer el coste semántico de leerlo. En varias entradas pequeñas incluso aumenta tokens.

Por ello, conservar Markdown para autoría y aprobación es compatible con generar vistas breves. No compensa imponer una lengua abreviada ni un diccionario críptico que traslade el esfuerzo al modelo o al revisor.

## 7. Propuesta mejorada: compilación conservadora y contexto dinámico

La versión siguiente debe separar tres productos: **contrato necesario**, **evidencia del código** y **estado de ejecución**. Cada uno admite una reducción diferente. El índice y los manifiestos extensos pueden permanecer fuera del prompt; las obligaciones y sus excepciones deben ser legibles dentro cuando afectan a la decisión.

### 7.1 Inventario e integridad antes de seleccionar

Reconciliar documentos canónicos, índice y archivos realmente existentes. Mantener cobertura de bloques de prosa, tablas, esquemas y activos, no solo IDs. Cada bloque conserva origen, rango, hash, estado, autoridad y relaciones; los campos inferidos quedan marcados como inferidos. Documentos no indexados o secciones no clasificadas deben aparecer como pendientes de análisis, sin desaparecer silenciosamente.

Separar la confianza en la procedencia de la aprobación funcional: un log es evidencia, no una instrucción; una propuesta no se convierte en requisito confirmado. Detectar IDs duplicados, referencias obligatorias ausentes, raíces retiradas y sustituciones sin resolver antes de cualquier descarte. Los ciclos requieren visita única; los enlaces históricos opcionales no obligan a cargar toda la historia.

La identidad del paquete debe detectar cambios de contenido y del inventario, incluidos bloques nuevos. Esto permite invalidar una selección sin sustituir la autorización global existente. Un hash demuestra identidad de bytes; no demuestra corrección de significado.

### 7.2 Núcleo contractual indivisible para cada comportamiento

La unidad mínima seleccionable no debe ser una frase aislada ni una fila de FR. Debe incluir el comportamiento con sus definiciones necesarias:

- Entradas y salidas: nombres de campos, tipos, estructura, unidades, codificaciones y valores por defecto.
- Condiciones, negaciones, precedencias, excepciones, orden y límites inclusivos/exclusivos.
- Errores, valores nulos, efectos laterales, mutabilidad y restricciones de seguridad.
- Criterios de aceptación, interfaces compartidas y decisiones vigentes que delimitan el cambio.

Preservar estos textos literalmente por defecto. Un extractor puede enlazar piezas distantes, pero no rellenar vacíos por inferencia y declararlos aprobados. La reformulación neural solo se ensaya como candidato separado, contra el literal y con pruebas independientes. Evitar que el propio modelo que resume sea el único juez de equivalencia.

### 7.3 Aplicabilidad con tres estados y cierre por contratos

Semillas: definición de tarea, propiedad primaria, contribuciones, interfaces tocadas, decisiones globales y perfil exacto. Cada obligación candidata tendrá aplicabilidad **confirmada, descartada con evidencia o desconocida**. Un score de similitud bajo no basta para descartarla.

Cerrar dependencias obligatorias y contratos de consumidores inversos. Una relación incorpora primero el contrato que la tarea consume; no arrastra automáticamente toda la implementación ni todos los documentos del dominio. Distinguir dependencia normativa, flujo de datos, navegación e historia. Para configuración, reflexión, generación y dependencias dinámicas, declarar límites del análisis estático y ampliar mediante inspección dirigida.

Cuando no se puede acotar una sección relevante, incorporarla completa o declarar qué falta. Si la incertidumbre afecta una decisión crítica, el sistema no debe emitir `ready`. Un ranking ayuda a ordenar la inspección, pero no decide por sí mismo suficiencia. Esta política todavía requiere implementar y evaluar un clasificador de aplicabilidad; v2 no lo hace.

### 7.4 Paquete de trabajo y ampliaciones durante la tarea

El paquete inicial contiene el núcleo contractual y el código necesario para el cambio inmediato. Puede ofrecer índices pequeños de detalles recuperables. Antes de editar un nuevo símbolo, interfaz o ámbito, reevalúa qué contratos necesita; después del diff, revisa consumidores afectados. Las ampliaciones deben traer bloques coherentes, incluyendo contexto de tipos y efectos, no líneas truncadas por relevancia lexical.

Usar presupuestos como aviso de coste, nunca como límite que recorta obligaciones. Si el núcleo excede el presupuesto, ampliar capacidad o dividir la tarea manteniendo contratos de integración. Dividir en agentes también tiene coste de duplicación y coordinación; no se considera ahorro por definición.

El acceso bajo demanda solo funciona si hay una señal fiable de qué falta. Para una regla potencialmente global o una fuente sin clasificar, posponer indefinidamente su lectura no es una solución. La evidencia visual se carga cuando es necesaria, y su coste se mide como tal.

### 7.5 Reducir antes lo que puede computarse con exactitud

Las oportunidades más defendibles son eliminar duplicados, seleccionar secciones literales, reutilizar índices vigentes y producir diagnósticos deterministas: fallos únicos de un log, cambios relevantes, símbolos afectados, resumen de pruebas con ruta al resultado completo. La transformación debe preservar los datos necesarios para diagnosticar, no esconder errores raros o contradictorios.

Mantener un prefijo estable pequeño y un estado de ejecución con tarea, decisiones aprobadas, archivos leídos con versión, cambios, pruebas fallidas y asuntos abiertos. Una memoria derivada obsoleta se invalida; no bloquea ni reemplaza al contrato vigente. Si el host permite gestión del historial, evaluar ocultación de observaciones antiguas recuperables. Si no, el plugin puede reducir futuras salidas, pero no garantizar que deje de contarse lo ya enviado.

Esto puede implementarse en los mecanismos locales existentes sin añadir MCP, conectores, hooks, apps o agentes ejecutables al producto. La arquitectura descrita es una propuesta, no una nueva capacidad activada.

### 7.6 Recibo de selección, no certificado semántico

Emitir un manifiesto externo con fuentes/versiones, obligaciones incluidas, exclusiones justificadas, incertidumbres, dependencias pendientes, transformación aplicada y medidas de tokens. El prompt necesita solo procedencia suficiente para consultar las fuentes y distinguir autoridad; no miles de hashes o campos administrativos repetidos.

Este recibo permite auditar y reproducir por qué se sirvió un contexto. No se llama prueba de suficiencia universal. Si hay una omisión, debe ser posible localizar qué componente falló: inventario, clasificación, recuperación, representación o uso del contexto por el modelo.

## 8. Validación que exigiría antes de incorporarlo como comportamiento habitual

La siguiente evaluación debe comparar flujo actual, lectura selectiva competente, selección literal conservadora y propuesta optimizada. Para representar formatos, mantener exactamente el mismo contenido; para evaluar recuperación, usar un guard común; para evaluar historial, comparar ocultación simple con resumen. Así se aíslan efectos.

| Criterio de avance propuesto | Medida y protección contra resultados engañosos |
|---|---|
| Calidad de primera entrega | Tareas reales reservadas por repositorio, pruebas ocultas y revisión de integración/mantenibilidad; informar cada regresión crítica y diferencias pareadas. Reparaciones cuentan aparte y consumen presupuesto. |
| Honestidad de suficiencia | Falsos listos y falsos bloqueos por severidad y causa. Cero falsos listos críticos observados es condición necesaria, no garantía estadística. |
| Resistencia a metadatos | Perturbaciones reservadas de ámbitos, estados, vínculos, prosa y fuentes omitidas; recuperar o declarar carencia, sin afirmar suficiencia silenciosamente. |
| Expansión ante ruido | Incrementar documentación irrelevante manteniendo las obligaciones. Medir crecimiento absoluto y percentiles; un objetivo candidato es ≤10% más contexto ante diez veces más ruido. No recortar contratos para cumplirlo. |
| Ahorro operativo | Tokens y coste de toda la tarea, incluidos fallos, bloqueos y preparación amortizada; distribución por familia y repeticiones. La calidad es una restricción previa, no una variable que se compensa con ahorro. |

La muestra debe incluir monorepos y proyectos pequeños; frontend visual/accesibilidad, API, datos y migraciones, concurrencia, seguridad, rendimiento, compatibilidad pública, configuración dinámica, idiomas y tareas sin respuesta documental suficiente. Debe separar cambios locales de transversales, especificaciones maduras de incompletas, y diferentes modelos/hosts. El tamaño de muestra y margen de no inferioridad deben definirse antes a partir del riesgo y potencia necesaria; no inventar un número de proyectos que certifique todo.

Orden de incorporación recomendado: medición e inventario; extracción literal en modo de observación; piloto optativo con ampliaciones; únicamente después optimización de formato y poda aprendida de material auxiliar. La comparación completa debe incluir también tareas fallidas o bloqueadas, evitando medir ahorro solo entre los éxitos fáciles. Toda modificación del selector o del modelo exige volver a comprobar las familias afectadas.

## 9. Qué está validado y qué queda abierto

**Ejecutado:** seis sondas sobre fixtures; 36 casos y 180 perturbaciones; cuatro entregas por 121 comprobaciones —484 aserciones, no 484 tareas—; doce comprobaciones posteriores dirigidas de fechas; ocho pruebas del guard; cinco conjuntos de serialización. Además, 36 tests existentes de contrato/continuidad pasaron, al igual que la puerta rápida de skills, plugin, perfiles, contrato y manifest de fixtures. [Recibos](evidence/), [revisión crítica](review.md).

**Límites:** metadatos manuales, corpus sintético pequeño, reserva no sellada, historiales distintos de agentes y una revisión informada. No se ha probado extracción semántica automática de Markdown libre, calidad de aplicaciones completas, mantenimiento prolongado, seguridad exhaustiva, coste total facturado ni comportamiento de usuarios reales. No se han ejecutado release, certificación Docker o piloto para este cambio documental.

Hubo fallos de permisos del entorno al crear temporales; las pruebas originales pasaron al ejecutarse con acceso local adecuado. La sonda usó directorios retenidos en lugar de `TemporaryDirectory`, solo dentro del harness en memoria. Un reporte generado cambió concurrentemente durante una primera medición; se conservó el incidente y una repetición confirmó integridad de las fuentes inspeccionadas. El repositorio ya estaba modificado al empezar; este estudio no acredita esos cambios preexistentes.

**Decisión propuesta:** conservar Markdown canónico, descartar la compresión agresiva como valor por defecto y no integrar v2. Desarrollar primero inventario verificable, núcleo contractual literal, selección por contratos y ampliación controlada. El progreso importante será reducir errores por contexto y lecturas innecesarias; cualquier porcentaje de ahorro deberá demostrarse después sobre tareas completas.
