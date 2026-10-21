# Petición de rediseño integral de LKS-SDD v5
## Un modelo simplificado de especificación, tarea y ejecución

**Solicitante:** Joseba  
**Destinatarios:** equipo de producto y desarrollo de LKS-SDD  
**Fecha:** 21 de octubre de 2026  
**Estado:** petición reformulada para diseño de v5; sustituye la formulación anterior de este documento.  
**Análisis adjunto:** `diagnostico-sat-next-ai-lks-sdd-2026-10-21.zip`.

## 1. Encargo y resultado esperado

Solicito una renovación integral de LKS-SDD. La experiencia analizada muestra que la administración de la metodología consume un tiempo y un esfuerzo desproporcionados para un desarrollo funcional acotado. La sobredocumentación, la repetición de controles, la expansión del contexto y la complejidad de implementación, entrega y cierre hacen inviable el uso cotidiano del flujo observado.

Conservamos las tres fases —definición, planificación y ejecución— y cambiamos su organización alrededor de **tres tipos de documentos duraderos**:

1. **Especificaciones consolidadas por unidades funcionales**, que permiten comprender el producto.
2. **Definición de cada tarea**, que explica la petición y el cambio que se va a abordar.
3. **Un único plan por tarea**, que reúne enfoque técnico, pruebas, seguimiento, decisiones de ejecución y resultado.

Esta estructura es el requisito central del rediseño. El equipo debe diseñar cómo hacerla funcionar con rapidez, sencillez y calidad, incluyendo proyectos con varias personas y años de evolución.

La v5 debe convertir proyectos anteriores a este modelo y retirar los archivos SDD sustituidos o innecesarios. La migración debe terminar con un proyecto que opere íntegramente con v5, sin una estructura legacy obligatoria.

**El resultado esperado es un sistema que ayude a desarrollar y mantener el producto, con poco trabajo administrativo y documentación útil.** La arquitectura, los comandos, los formatos internos y los estados de v4 pueden sustituirse. Cada mecanismo conservado debe justificar su valor.

## 2. Evidencia que motiva la petición

El análisis adjunto cubre dos ciclos de entrega de SAT Next AI, v0.17.0 y v0.17.1, entre el 19 y el 21 de octubre de 2026. El runtime de proyecto observado fue `4.0.2-0f0068ddaa75`; las cifras no evalúan versiones posteriores.

| Evidencia de la sesión | Magnitud observada | Problema que v5 debe resolver |
|---|---:|---|
| Duración | 31 h 39 min de calendario; 21 h 55 min con turnos abiertos | Reducir el coste completo del recorrido y distinguir trabajo de espera. |
| Preparación y consulta interna SDD capturada | Al menos 4 h 38 min | Reducir radicalmente el tiempo de administración del proceso. |
| Operaciones individuales | Verify: 21 min 51 s; implement: 15 min 30 s; integrate: 15 min 19 s | Evitar operaciones administrativas de varios minutos sobre trabajo ya realizado. |
| Llamadas de herramientas | 2.010; 517 de espera o consulta pura | Reducir fragmentación, sondeo y coordinación manual del agente. |
| Auxiliares Python escritos por Codex | 145 archivos, 6.769 líneas; 119 con lanzamiento shell observado | Resolver el flujo normal mediante capacidades del plugin. |
| Rutas cambiadas en Git | 72 de implementación, 16 de tests/Storybook y 162 SDD | Reducir la proliferación de artefactos administrativos. |
| Crecimiento SDD versionado | 51,76 MiB netos | Consolidar conocimiento y eliminar representaciones innecesarias. |
| Vistas y paquetes de contexto externos | 77 archivos; 364,89 MiB | Seleccionar información pertinente sin arrastrar todo el histórico. |
| Pipelines | 15 para dos huellas de código de aplicación | Examinar duplicidades y reutilizar validaciones cuando sus entradas lo permitan. |
| Segundo ciclo: autorización autónoma hasta primer parche | 3 h 12 min; 2 h 32 min desde el último ajuste de alcance | Acortar la preparación que retrasa el trabajo de producto. |
| Comprobación visual en producción hasta cierre del chat | Aproximadamente 1 h 49 min | Hacer breve el cierre una vez disponibles los resultados. |

Hay límites importantes de atribución: un turno abierto puede estar esperando y no mide esfuerzo humano ni CPU. Los tiempos de CI, herramientas y turnos se solapan. Hubo ampliaciones de alcance, correcciones reales, pruebas necesarias e incidencias de VPN, AWS y backup. Los 145 auxiliares fueron escritos por Codex para distintas finalidades, no emitidos automáticamente por el plugin. Las dos huellas comparan código en `frontend/src` y `backend/app`, no todas las entradas de CI; por ello no prueban que todos los pipelines repetidos fueran prescindibles.

El rediseño debe abordar la combinación de metodología, runtime, interacción con el agente y políticas del proyecto. El análisis permite localizar fricciones; el perfilado técnico deberá confirmar sus causas internas.

## 3. Organización documental requerida

| Documento | Pregunta que responde | Información principal | Regla de mantenimiento |
|---|---|---|---|
| Especificación de unidad funcional | ¿Cómo debe funcionar esta parte del producto consolidado? | Comportamiento, reglas, datos, permisos, relaciones y restricciones relevantes. | Se actualiza al incorporar cambios; no se duplica por tarea o release. |
| Definición de tarea | ¿Qué se solicita y qué cambio se propone? | Necesidad, alcance, impacto, resultado esperado, criterios de aceptación y decisiones pendientes. | Describe la modificación y referencia las especificaciones afectadas. |
| Plan, seguimiento y resultado | ¿Cómo se realiza, comprueba y entrega? | Enfoque técnico, pasos, pruebas necesarias, avance, decisiones de ejecución y resultado. | Un archivo evolutivo durante toda la ejecución, incluido el cierre. |

Para una tarea normal, esto significa **dos archivos de trabajo —tarea y plan— más las modificaciones pertinentes en las especificaciones existentes**. Una tarea no debe generar automáticamente expedientes separados de autorización, pruebas, evidencias, verificación, integración, despliegue y cierre.

Una organización ilustrativa, cuyos nombres puede ajustar el equipo:

```text
docs/sdd/
  especificaciones/
    ordenes-de-trabajo.md
    partes-de-trabajo.md
    importaciones.md
    usuarios-y-permisos.md
  tareas/
    T-042-correcciones-de-experiencia/
      tarea.md
      plan.md
```

Los índices o vistas de navegación serán opcionales o derivados. No deben exigir mantener manualmente los mismos datos en varios lugares. Los adjuntos se incorporarán solo cuando aporten información necesaria; tener una tarea no obliga a crear capturas, diagramas ni nuevos informes.

### 3.1. Especificaciones consolidadas por unidades funcionales

La especificación debe permitir conocer el estado funcional consolidado de la aplicación sin reconstruirlo a partir de tareas cerradas. Debe describir tanto los recorridos principales como las reglas y excepciones que importan para su mantenimiento.

Las unidades se definirán por capacidades del negocio. Una unidad puede abarcar varias pantallas y servicios. Conforme crezca el producto, podrá dividirse o reorganizarse manteniendo referencias claras. No se exige una unidad por pantalla, componente técnico o endpoint.

Las reglas transversales se documentarán una vez y se referenciarán desde las unidades afectadas. La estructura debe evitar que cambiar un permiso compartido obligue a corregir numerosas copias del mismo texto.

La modificación propuesta vive en la tarea mientras se desarrolla. Al consolidarse, se incorpora a la especificación. El comportamiento aún pendiente debe quedar inequívocamente identificado. La especificación describe el contrato consolidado del producto; el plan registra en qué versión y entorno se ha entregado. Un cambio incorporado al código no debe presentarse automáticamente como desplegado o aceptado.

### 3.2. Definición de tarea

Debe contener lo necesario para comprender y revisar el trabajo:

- Petición y motivo: qué necesidad se quiere resolver.
- Alcance y límites: qué se incluye y qué queda fuera cuando sea relevante.
- Unidades afectadas e impacto sobre comportamientos, datos, permisos o integraciones.
- Resultado esperado y criterios observables de aceptación.
- Decisiones necesarias, restricciones y referencias útiles.

Los apartados sin contenido pertinente no deben convertirse en formularios obligatorios. El nivel de detalle debe guardar relación con la complejidad y el riesgo.

Las decisiones y autorizaciones se recogerán de forma breve en el documento pertinente, identificando quién decidió y su alcance. No se necesita un archivo adicional ni repetir una autorización válida en varios formatos.

### 3.3. Un único plan de ejecución

El plan reunirá:

- Enfoque técnico y cambios previstos.
- Pasos, dependencias y reparto de responsabilidades cuando proceda.
- Plan de pruebas proporcional al cambio.
- Seguimiento del avance y bloqueos reales.
- Decisiones o desviaciones relevantes durante la ejecución.
- Resultados de pruebas, entrega y pendientes finales.

La definición de tarea conserva el qué y el porqué; el plan desarrolla el cómo y el resultado de ejecutarlo. Los criterios de aceptación se referencian, sin copiarlos en múltiples matrices.

El seguimiento debe ser breve. No se pide una transcripción de comandos o mensajes ni una entrada por cada operación del agente. Para continuar el trabajo deben bastar el estado actual, la siguiente acción y las decisiones relevantes.

### 3.4. Subtareas solo cuando aporten valor

Se crearán cuando el tamaño, las dependencias, la ejecución independiente o el reparto entre personas lo justifiquen. Una subtarea independiente podrá tener su propia definición y su único plan. Los pasos ordinarios permanecerán dentro del plan existente.

La tarea principal coordinará alcance, dependencias y resultado conjunto, sin reproducir los planes ni las evidencias de sus subtareas. La división debe facilitar el trabajo, no multiplicar documentos por cada corrección pequeña.

## 4. Funcionamiento de las tres fases

| Fase | Actividad esperada | Resultado y continuidad |
|---|---|---|
| Definición | Consultar especificaciones pertinentes, entender la petición y resolver dudas materiales. | Definición de tarea suficiente para revisar el cambio. |
| Planificación | Preparar enfoque técnico, pasos y comprobaciones. | Un plan proporcionado y ejecutable. |
| Ejecución | Implementar, comprobar, integrar o desplegar según alcance; consolidar y limpiar. | Especificaciones actualizadas y resultado registrado en el mismo plan. |

Las fases deben ser reconocibles, pero no imponen tres nuevas aprobaciones por petición. Se reutilizará la autoridad vigente. Cuando exista una decisión que realmente requiera intervención, se presentará de forma concreta y comprensible.

Una modificación de alcance actualizará la tarea y las partes afectadas del plan. No reiniciará todo el proceso. Las dudas que bloqueen una parte deben quedar visibles sin impedir trabajo independiente ya autorizado.

Un cierre normal consistirá en actualizar las especificaciones afectadas, resumir la ejecución y las pruebas, registrar el estado real de entrega y retirar temporales. Debe poder hacerse en una operación coherente y reanudarse si se interrumpe.

## 5. Pruebas ligeras, pertinentes y sin duplicidad

**Cada tarea tendrá el plan de pruebas necesario dentro de su archivo de planificación.** No habrá un documento de pruebas adicional obligatorio.

El plan debe relacionar los criterios de aceptación y los riesgos del cambio con comprobaciones suficientes. Bastará una tabla breve de comprobación, alcance y resultado o referencia. Las pruebas automatizadas reutilizables se mantendrán en la estructura normal de tests del producto.

Se requieren estas reglas:

1. Seleccionar las pruebas a partir del cambio y sus dependencias reales. Un cambio transversal puede exigir más cobertura; una corrección localizada debe conservar un recorrido pequeño.
2. Reutilizar resultados válidos cuando no hayan cambiado sus entradas relevantes, configuración o condiciones de ejecución.
3. Repetir lo afectado por cambios o fallos que lo justifiquen. Un resultado obsoleto no sirve para certificar una revisión nueva.
4. Consumir los resultados existentes de tests, CI y calidad. Referenciar resultados disponibles sin redactar un informe equivalente por cada herramienta.
5. Evitar que una actualización de documentación provoque otra validación completa de aplicación si no modifica entradas relevantes de esa validación.
6. **El despliegue de una tarea no ejecutará por defecto una validación general de toda la aplicación.** Solo procederá cuando el proyecto lo establezca expresamente. Las comprobaciones del despliegue se centrarán en la versión, disponibilidad y funcionamiento afectado, según corresponda.
7. Respetar los controles de calidad y entrega exigidos por el proyecto. Si una política actual provoca repeticiones, identificarla y proponer su cambio por el cauce autorizado; no eludirla.

El plugin debe implementar estas reglas de forma habitual. El agente no debería necesitar redactar una excepción cada vez que reutiliza una prueba vigente.

## 6. Colaboración y mantenimiento durante años

El modelo debe funcionar con varias personas y varios cambios concurrentes sin añadir otro sistema documental.

- Usar nombres legibles e identificadores estables de tareas, con responsabilidad y estado localizables.
- Mantener cada dato en un lugar principal; mostrar vistas derivadas cuando ayuden a navegar.
- Detectar modificaciones concurrentes de especificaciones y planes, evitando sobrescribir decisiones o perder cambios.
- Reconciliar los cambios de varias tareas sobre una misma unidad funcional. El cierre de una tarea no debe borrar el contrato incorporado por otra.
- Recuperar el trabajo entre chats, agentes o personas a partir de la tarea, su plan y las especificaciones pertinentes.
- Conservar las tareas cerradas de forma compacta cuando expliquen cambios, decisiones o pendientes útiles, fuera del contexto habitual de nuevas tareas.

El contexto inicial debe contener el trabajo vigente, las unidades afectadas y las reglas aplicables. Debe poder ampliarse ante dependencias reales. El volumen de histórico ajeno al cambio no puede obligar a releer o reconstruir todo el proyecto.

El equipo debe demostrar el comportamiento con histórico creciente y concurrencia, además de hacerlo con un proyecto recién creado.

## 7. Consolidación, conservación y limpieza

La limpieza es parte del cierre. La v5 debe distinguir conocimiento duradero, herramientas reutilizables y material temporal.

| Conservar | Retirar cuando deje de ser necesario |
|---|---|
| Especificaciones consolidadas y reglas vigentes. | Copias intermedias o versiones equivalentes de esas especificaciones. |
| Tarea y plan compactos con decisiones y resultado útiles. | Recibos, expedientes y representaciones duplicadas del mismo estado. |
| Tests y utilidades que seguirán sirviendo al producto. | Scripts auxiliares de un solo uso para tramitar o validar la tarea. |
| Referencias a commits, CI, versión y artefactos necesarios. | Volcados completos que duplican resultados recuperables y no aportan valor futuro. |
| Evidencia singular necesaria para explicar o comprobar una decisión. | Capturas redundantes, vistas de contexto y archivos temporales de diagnóstico. |

Un dato necesario para reconstruir una decisión no debe desaparecer porque su servicio externo tenga una retención breve. En ese caso se conservará el resultado mínimo útil. Las necesidades adicionales de retención deberán proceder de una política explícita, no de una conservación indiscriminada.

El plugin debe conocer qué temporales ha creado y limpiarlos sin explorar ni borrar archivos ajenos. No se exige un nuevo manifiesto permanente por tarea: el mecanismo interno será ligero y recuperable. Los resultados fallidos que aún se estén investigando se conservarán mientras hagan falta.

Tras el cierre no deben quedar carpetas de soporte crecientes por inercia. El informe final puede indicar en una línea qué se ha consolidado y retirado, sin crear otro expediente de limpieza.

## 8. Migración desde versiones anteriores y retirada del modelo antiguo

La migración es una capacidad necesaria de v5. Debe transformar la organización anterior en la nueva y **eliminar los archivos SDD que ya no tengan utilidad**, sin dejar una capa legacy operativa.

Instalar el plugin no implica migrar silenciosamente un proyecto. La conversión se realizará como una operación explícita, con una vista breve de su alcance. La autorización de esa operación cubrirá la limpieza que se haya mostrado; no se solicitarán aprobaciones repetitivas por cada archivo.

### Secuencia requerida

1. **Identificar el material SDD del proyecto.** Reconocer versión de origen, especificaciones, tareas abiertas, decisiones útiles y dependencias documentales. Limitar el inventario al alcance necesario.
2. **Preparar la consolidación.** Agrupar el conocimiento vigente por unidades funcionales y convertir las tareas activas a definición y plan. Señalar contradicciones o ambigüedades que impidan determinar el contrato válido.
3. **Mostrar una propuesta breve de conversión.** Explicar estructura resultante, información que se conservará, conjuntos que se eliminarán y decisiones pendientes. No crear un expediente por documento antiguo.
4. **Disponer de recuperación suficiente.** Usar el estado previo versionado en Git cuando cubra la información. Si existe material necesario fuera de Git, preparar una recuperación temporal acotada, con ubicación y caducidad definidas. No trasladar toda la estructura anterior a un archivo legacy permanente.
5. **Aplicar la conversión y actualizar referencias.** Ajustar instrucciones y enlaces del proyecto para que apunten a v5. Mantener alcance, responsabilidad, decisiones válidas y pendientes de las tareas activas.
6. **Verificar el resultado y retirar lo sustituido.** Comprobar cobertura funcional esencial, referencias, continuidad de tareas y funcionamiento del nuevo modelo. Eliminar las estructuras antiguas que ya no se necesitan.
7. **Entregar un resumen compacto.** Unidades resultantes, tareas convertidas, incidencias pendientes si existen y limpieza realizada. Terminar la recuperación temporal según lo acordado.

### Criterios de conservación y eliminación

No se exige convertir cada objeto, snapshot, recibo o evento histórico. Se extraerá el conocimiento que siga siendo útil; los mecanismos sustituidos se descartarán.

Podrán eliminarse índices antiguos, snapshots, vistas, capturas redundantes, metadatos administrativos y runtimes locales obsoletos **cuando sean propiedad del esquema anterior y ninguna configuración activa los necesite**. Los runtimes compartidos, instalaciones globales y archivos ajenos quedan fuera de la limpieza del proyecto.

Las tareas históricas que aporten decisiones relevantes podrán resumirse o conservarse de forma compacta. El historial de Git seguirá disponible como historia del repositorio; no formará parte del contexto operativo normal.

No debe haber doble escritura v4/v5, dependencia de un motor antiguo para operar v5 ni obligación de mantener árboles documentales equivalentes. Un lector del formato anterior puede servir para convertirlo y terminar ahí su función.

La migración no debe inventar requisitos, aceptación o estados de entrega. Si existe una ambigüedad crítica, se resolverá la parte afectada antes de eliminar su fuente. Debe tolerar interrupciones y reintentos sin pérdida ni duplicación de trabajo.

La verificación será sobre la conversión documental y operativa. No disparará una batería general de pruebas de aplicación salvo exigencia del proyecto o cambio real que la justifique.

El equipo deberá declarar qué versiones de origen soporta, empezando por el modelo observado en el caso adjunto, y cómo incorporará las restantes. Se debe evitar obligar al usuario a encadenar migraciones intermedias solo para llegar a v5.

## 9. Requisitos técnicos de eficiencia

El equipo conserva libertad de implementación dentro del modelo documental solicitado. La solución debe cumplir:

- **Operaciones completas y breves.** Consultar, preparar, actualizar, consolidar y cerrar sin encadenar trámites manuales del agente.
- **Actualización incremental.** Procesar lo modificado y sus dependencias pertinentes; invalidar resultados cuando corresponda.
- **Recuperación e idempotencia.** Reanudar desde el último punto válido sin repetir pruebas ni generar documentos equivalentes.
- **Contexto acotado y ampliable.** Respuestas pequeñas por defecto, detalle bajo demanda y restricciones relevantes disponibles.
- **Integraciones reutilizables.** Consumir los formatos normales de Git, CI, tests y artefactos, sin conversiones efímeras por tarea.
- **Evidencias tratadas según su formato.** Soportar referencias a imágenes, ZIP, logs y binarios sin obligar a convertirlos en texto.
- **Trabajo prolongado con espera adecuada.** Progreso y notificación compatibles con el host, evitando usar al modelo como temporizador de sondeo.
- **Autoridad y realidad del resultado.** Reutilizar decisiones vigentes y distinguir implementación, comprobación, publicación, despliegue y aceptación dentro del mismo plan.

Los índices o cachés internos deben ser regenerables y no sustituir la legibilidad de los documentos. Las estructuras internas no pueden convertirse en cientos de archivos versionados que el agente deba gestionar.

El lenguaje del runtime queda abierto. El problema es la necesidad de escribir auxiliares para operar el proceso y el coste que esto añade; cambiar de lenguaje sin resolverlo no cumpliría el encargo.

## 10. Cómo medir y aceptar la mejora

La aceptación debe basarse en tareas completas con calidad equivalente. Reducir caracteres de salida o acelerar una sola llamada no demuestra por sí mismo que el desarrollo resulte eficiente.

Como **objetivos iniciales para contrastar en el prototipo**, se proponen:

| Magnitud | Objetivo de partida |
|---|---|
| Documentación ordinaria de una tarea | Definición y un plan; actualización de especificaciones pertinentes. |
| Auxiliares efímeros para tramitar el flujo normal SDD | Cero. |
| Repeticiones completas injustificadas de pruebas con entradas vigentes | Cero. |
| Consulta de estado disponible | p95 ≤2 s en caliente; objetivo ≤5 s en frío. |
| Sobrecoste SDD total | ≤5 min para una corrección pequeña; ≤15 min para un cambio medio acotado. |
| Cierre con resultados y autoridad ya disponibles | ≤1 min en tarea pequeña; ≤3 min en tarea media. |
| Temporales sin utilidad futura después de consolidar | Retirados; conservación excepcional explicada brevemente. |
| Histórico no relacionado multiplicado por 10 y por 100 | Sin crecimiento proporcional del contexto ni del coste de una tarea independiente. |

Los tiempos son metas propuestas, no resultados obtenidos ni estimaciones de ahorro demostradas. El equipo deberá contrastarlas y justificar alternativas. Las clases de cambio y las condiciones de medición deben fijarse antes del ensayo.

El sobrecoste incluirá toda la administración añadida por SDD: runtime, trabajo del agente, documentación del proceso, adaptación de evidencia, reintentos y repeticiones causadas por el protocolo. Se separarán desarrollo funcional, validación pertinente, infraestructura y espera humana, indicando solapes y atribuciones inciertas.

Se medirán tiempo hasta comenzar a cambiar producto, tiempo hasta entrega y tiempo hasta cierre, además de operaciones, archivos duraderos y temporales, bytes y contexto. Las métricas deberán cubrir el recorrido completo; no desplazar costes a procesos posteriores ni a trabajo humano sin contabilizar.

### Escenarios mínimos del prototipo

| Caso | Resultado que debe demostrar |
|---|---|
| Corrección pequeña | Dos archivos de tarea suficientes, pruebas pertinentes y cierre breve. |
| Lote como el analizado | Gestión conjunta sin un expediente completo por ajuste. |
| Cambio complejo con subtareas | Reparto efectivo, sin duplicar planes y resultados en la tarea principal. |
| Contrato funcional compartido o permisos | Identificación de dependencias y pruebas afectadas. |
| Dos personas sobre una misma unidad | Consolidación sin sobrescritura ni pérdida de cambios. |
| Interrupción, compactación o cambio de chat | Continuidad con el estado actual y poco contexto. |
| Caída de CI, VPN o credenciales | Avance independiente y reanudación sin reconstruir todo el proceso. |
| Tests vigentes y cambio documental | Reutilización correcta; validación específica cuando proceda. |
| Despliegue de una tarea | Comprobaciones de entrega; sin regresión general automática salvo política expresa. |
| Migración de un proyecto con histórico | Especificaciones consolidadas, tareas activas preservadas, estructura antigua retirada. |
| Migración interrumpida o con contradicción | Recuperación sin pérdida y resolución localizada de la ambigüedad. |
| Cierre y limpieza | Solo permanece material útil; los archivos ajenos están intactos. |

Estos escenarios sirven para validar el producto LKS-SDD v5. No se convierten en una lista de comprobaciones obligatoria para cada tarea de las aplicaciones que utilicen el plugin.

Los resultados deben indicar entorno, versiones, tamaño del proyecto y repeticiones. Los percentiles requieren muestras suficientes. La prueba con el caso adjunto se hará en una copia controlada, sin operar sobre producción.

## 11. Respuesta solicitada al equipo

Se solicita **una propuesta integrada y un prototipo vertical**, con resultados compactos y reproducibles. La propuesta debe explicar:

1. Cómo implementa los tres documentos y las tres fases con el mínimo de operaciones.
2. Qué obligaciones actuales elimina, fusiona o automatiza y qué valor conserva.
3. Cómo organiza unidades funcionales, tareas, subtareas y trabajo concurrente durante años.
4. Cómo selecciona pruebas y reutiliza resultados respetando las políticas del proyecto.
5. Cómo consolida el conocimiento y limpia los temporales.
6. Cómo convierte versiones anteriores, retira el modelo antiguo y recupera una conversión interrumpida.
7. Qué demuestra el prototipo sobre calidad, experiencia, tiempo, archivos y operaciones.

El prototipo debe recorrer definición → planificación → ejecución y pruebas → consolidación y limpieza, incluyendo reanudación y un caso real de migración. La documentación de diseño y los resultados se actualizarán sobre las mismas referencias; no se pide una colección de informes por experimento.

La propuesta será insuficiente si conserva esencialmente los trámites actuales, obliga al agente a generar wrappers, añade documentos obligatorios por transición, mantiene una capa legacy operativa o declara eficiencia sin medir la tarea completa.

**La prioridad de v5 es hacer útil SDD en el desarrollo cotidiano: conocimiento funcional consolidado, tareas comprensibles, ejecución bien preparada, comprobaciones suficientes y un cierre rápido y limpio.**

## 12. Material para la revisión

Este documento contiene la petición vigente. El análisis adjunto conserva las mediciones originales; sus recomendaciones deben leerse junto con el modelo simplificado fijado aquí.

El ZIP de diagnóstico incluye:

- `informe.html`: diagnóstico visual, filtros, fases y cronología.
- `informe.md`: explicación detallada, atribución y límites.
- `datos.json` y cuatro CSV: operaciones, SDD/CI, archivos y tiempos reconstruidos.
- `analizar-sesion.py` y la plantilla HTML: método de extracción y presentación.

Conviene empezar por esta petición y después abrir `informe.html`. Los datos detallados permiten contrastar los problemas y seleccionar los casos del prototipo.

El paquete contiene nombres y rutas técnicas del proyecto y está preparado para revisión interna. No incorpora el repositorio completo, los logs originales ni el runtime: permite revisar el diagnóstico, pero reproducir la extracción o perfilar el motor requiere preparar las fuentes pertinentes en un entorno controlado.

El envío no supone una migración ni una modificación de los proyectos actuales. Se solicita diseñar y demostrar la nueva versión sobre esta base.

