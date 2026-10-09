# Coste de contexto y tiempo de desarrollo con LKS-SDD

Fecha: 2026-10-09. Estado: **diagnóstico y recomendaciones; mejora sin implementar**.
Complementa [MEJ-ALCANCE-01](PROPOSAL.md). Las prioridades expresas del usuario son
reducir el uso excesivo de tokens de IA y el tiempo de desarrollo.

Este documento conserva el diagnóstico inicial del incidente y mecanismos compartidos.
La cobertura posterior del conjunto se encuentra en [GLOBAL-AUDIT.md](GLOBAL-AUDIT.md)
y su secuencia de trabajo en [PLAN.md](PLAN.md).

## 1. Conclusión

**La preocupación tiene fundamento técnico y evidencia de uso real.** Hay mecanismos
que hacen crecer el trabajo de una petición concreta con documentación de otras
peticiones. El efecto llega a la selección, al transporte de información al agente,
al cálculo del runtime y a los bloqueos que requieren intervención humana.

La corrección inicial del ámbito de una propuesta sería necesaria, pero insuficiente
como solución general. La mejora debe reducir el coste de completar el cambio:
lecturas, llamadas, generación, esperas de herramientas, aclaraciones y reintentos.
Una salida pequeña que provoque diez consultas adicionales puede empeorar el resultado.

La meta propuesta es que el coste habitual dependa del **cambio y sus dependencias
aplicables**. Un proyecto con más historia podrá necesitar más trabajo interno de
indexación; eso no debe obligar al modelo y al usuario a recorrer esa historia en
cada corrección. La calidad funcional y las obligaciones aplicables son condiciones
de aceptación del ahorro.

## 2. Evidencia y límites

Se han utilizado cuatro fuentes:

1. Informe de la incidencia y registro original de Copilot, leído como datos.
2. Respuesta original de `decision-view`, recuperada del archivo guardado por el host.
3. Inspección del runtime instalado 3.2.0 y reproducción en proyectos desechables.
4. Medición estática existente de las instrucciones seleccionadas por recorrido.

Los agregados se conservan en [incident-cost.json](evidence/incident-cost.json),
[documentary-cost-3.2.0.json](evidence/documentary-cost-3.2.0.json),
[instruction-routes.json](evidence/instruction-routes.json) y la
[reproducción previa del bloqueo](evidence/diagnosis-3.2.0.json).
No se guardan aquí los documentos completos del consumidor ni su conversación.

El análisis de la sesión se acota desde la petición inicial de corregir el error
hasta la redirección del usuario al diagnóstico del plugin, antes de la tercera
petición del registro. Las intervenciones posteriores tienen otro alcance.
Las comprobaciones sintéticas usan el plugin instalado, no los cambios locales
pendientes del repositorio. El runtime particular del consumidor tiene diferencias
en alcance y referencias históricas; la selección de toda la prosa y la duplicación
de presentación también están presentes en su código consultado. Su estado actual
no prueba por sí solo qué bytes ejecutó la sesión en cada instante.
La [comparación de módulos](evidence/runtime-comparison.json) conserva las huellas
consultadas. «Historia ajena» designa aquí documentación de otros trabajos que sigue
en el corpus activo; la carga ordinaria excluye las carpetas dedicadas a historia,
evidencias y migraciones. No se afirma que lea todo el almacén histórico físico.

No se ha medido una implementación corregida, el coste facturado de la sesión ni
el tiempo que habría requerido el mismo desarrollo con una alternativa. Los tiempos
sintéticos son observaciones de esta máquina, con tres repeticiones por operación,
sin aislamiento de carga. No constituyen una promesa de rendimiento.

## 3. Qué ocurrió en la sesión real

### Contexto y lecturas del agente

| Medida del tramo inicial | Resultado | Interpretación |
|---|---:|---|
| Llamadas a herramientas completadas | 114 | Incluye lectura, ejecución, preguntas y otras herramientas. |
| Suma de `result_token_count` disponible | 91.856 | Tokens declarados en las salidas de herramientas; faltan métricas en 3 llamadas. |
| Lecturas mediante `view` | 71; 73.084 tokens | Una parte sustancial del contenido recibido procede de lecturas. |
| Lecturas de instrucciones y código interno del plugin | 25.978 tokens | Clasificación por rutas; incluye diagnóstico del bloqueo. |
| Lecturas de código de aplicación | 25.221 tokens | Clasificación por rutas; no representa todo el trabajo de desarrollo. |
| Primera instantánea de uso del modelo | 135.635 `prompt_tokens` | Una llamada registrada, no el total acumulado de la sesión. |
| `cache_read` de esa instantánea | 134.867 | El registro indica reutilización de gran parte del prompt. |

**Hecho:** el agente consumió mediante `view` una cantidad similar de tokens leyendo
el propio plugin que leyendo código de aplicación. **Inferencia:** la incidencia
introdujo una carga importante de diagnóstico del mecanismo de desarrollo. No todas
esas lecturas son prescindibles: algunas resolvían requisitos o fallos reales.

Estas cifras no se suman entre sí: las salidas de herramientas pasan a formar parte
del contexto y pueden reaparecer en llamadas posteriores. Tampoco equivalen a una
factura: faltan las métricas completas por inferencia, las salidas generadas y las
condiciones de facturación. La caché del proveedor, la caché del runtime y la
retención del chat son mecanismos diferentes.

### Tamaño y composición de la revisión

La respuesta original confirma:

- 1.213 fuentes y 245 adjuntos.
- 756 fuentes de prosa incluidas por «ámbito no acreditado»: 1.277.018 caracteres.
- 193 fuentes incorporadas inicialmente por «regla global o alcance incierto».
- 92 recursos pendientes de observación y `complete=false`.
- 11.610.121 caracteres de Markdown.
- 41.471.970 bytes en el archivo de salida, aproximadamente 39,6 MiB.

Los cuerpos de `sections` suman 11.609.905 caracteres; el mismo contenido reaparece
en `markdown`. A ello se añaden `sources`, `attachments` y datos de integridad.
Hay dos multiplicadores: **selección amplia** y **representación repetida**. Los
adjuntos textuales también contribuyen al volumen; no todo procede de la prosa inicial.

El host truncó esa salida y guardó el archivo. **No introdujo íntegramente los
39,6 MiB en el contexto del modelo.** El problema de transporte sí causó consultas
adicionales sobre salidas guardadas: 4 lecturas `view`, con 6.892 tokens declarados.
No sería correcto convertir los millones de caracteres del archivo en tokens
supuestamente facturados.

### Tiempo observado

- La llamada que preparó los datos y solicitó `decision-view --json` duró **72,9 s**.
  La medida corresponde a toda esa llamada, no a un perfil aislado del selector.
- Una operación previa de preparación y registro seguía ejecutándose al superar
  los **120 s** de espera de la herramienta; ese dato es un límite inferior.
- Hubo seis preguntas al usuario. Una sola espera, por recuperar la VPN, duró
  **70,9 minutos**. No es tiempo atribuible a documentación.
- Otras preguntas trataban identidad, URL, estrategia HTTP/HTTPS, alcance y runtime.
  Se debe evaluar cuáles podían resolverse con información o autorización existentes;
  su mera presencia no demuestra que fueran redundantes.

Por tanto, hay latencia documental observada y una interrupción real del avance,
pero no se puede imputar al plugin toda la duración de la sesión.

## 4. Crecimiento reproducido sin aumentar el cambio

Se mantuvo una propuesta mínima y se añadieron documentos de prosa sin enlaces ni
relación con ella. Cada documento añadido contiene unas 4.000 letras y espacios.

| Documentos ajenos añadidos | Fuentes seleccionadas | Markdown de decisión | JSON completo de decisión | JSON de `review` |
|---:|---:|---:|---:|---:|
| 0 | 3 | 1.405 caracteres | 17.046 caracteres | 22.029 caracteres |
| 25 | 28 | 105.730 caracteres | 344.621 caracteres | 350.304 caracteres |
| 100 | 103 | 418.705 caracteres | 1.327.346 caracteres | 1.335.129 caracteres |

Con 25 documentos, el Markdown crece unas **75 veces**; con 100, unas **298 veces**.
No se amplió el objetivo ni sus requisitos. Estas vistas siguen siendo completas:
el exceso de consumo existe también cuando no aparece un bloqueo de observación.

El modo compacto reduce la duplicación del JSON, pero conserva el Markdown entero:
con 100 documentos todavía devuelve 420.512 caracteres. Por tanto, cambiar el formato
de salida no resuelve por sí solo la selección.

También aumentó el contexto público de implementación: de 12.152 a 123.821 caracteres
de JSON al añadir 25 documentos. El modo de comparación pasó de 10.877 a 122.546;
tampoco elimina la prosa ajena.

Las medianas de `decision_view` fueron 0,55 s, 2,17 s y 20,92 s; las de `review`,
1,39 s, 3,59 s y 23,58 s. La variación de carga del sistema impide inferir una curva
estable o trasladar esos tiempos a otro entorno. El crecimiento de contenido sí es
determinista para las entradas medidas. El tiempo de `compact` del informe mide
solo transformar una vista ya calculada: no representa el coste total del comando.

Se detuvo la campaña tras obtener esta evidencia; los casos previstos de 500
documentos, elementos estructurados, tarea autorizada y checkpoints no se ejecutaron.
El informe identifica esa limitación. No se declara una batería completa superada.

## 5. Causas y prioridad

| Causa comprobada | Efecto | Prioridad propuesta |
|---|---|---|
| `select` incorpora todo `model.prose` y recorre sus enlaces. | El tamaño del repositorio activo determina parte del contexto de cualquier petición y puede arrastrar observaciones ajenas. | P0 |
| Sin PLAN/TASK, `allowed_units` no aprovecha suficientemente las relaciones de pertenencia existentes. | Elementos de otra propuesta pueden entrar por ausencia de `data.request`. | P0 |
| `context` activa por defecto la referencia conservadora con todos los elementos normativos activos. | Resolver solo el cierre de propuesta deja pendiente el contexto de implementación. | P0 |
| La presentación incluye fuentes, secciones, adjuntos y Markdown con contenido repetido; `review` devuelve la presentación completa. | Respuestas grandes, truncamiento y recuperación adicional. | P0 |
| Varias operaciones vuelven a cargar el mismo modelo; la caché de `context` se consulta después de cargar documentos y observar Git. | Tiempo de herramienta incluso si la respuesta es pequeña o la caché acierta. | P1 |
| Las guías, estados y errores pueden llevar al agente a inspeccionar el funcionamiento interno del plugin. | Más lecturas y razonamiento operativo antes de poder desarrollar. | P1 |
| La repetición de registros y decisiones puede añadir carga de gestión. | Riesgo a evaluar en el recorrido completo; su frecuencia general no está medida. | P1, pendiente de observación |

Puntos verificables en código:
[selección y caché](../../../scripts/v3_context.py),
[carga del contrato](../../../scripts/v3_contract.py),
[revisión](../../../scripts/v3_lifecycle.py),
[presentación](../../../scripts/v3_decision_presentation.py),
[control de presentación](../../../scripts/v3_presentation_guard.py) y
[salida CLI](../../../scripts/v3_cli.py).

El perfil del caso mínimo confirma dos cargas y 16 parseos en una llamada a `review`,
frente a una carga y 8 parseos en `decision_view`. En el `context` con acierto de caché
siguen apareciendo una carga y tres procesos Git. En estos perfiles pesa la actividad
de sistema de archivos y procesos; las búsquedas lineales `Model.get` existen, pero
no fueron el principal coste del caso mínimo. No conviene priorizarlas por intuición.

Hay selección de instrucciones por operación: las rutas estáticas actuales contienen
entre 8.773 y 17.106 caracteres en 3–6 archivos. Ese avance es útil, pero mide recursos
previstos, no lecturas reales. La sesión mostró que el diagnóstico puede ampliar
considerablemente esas lecturas. Acortar únicamente los `SKILL.md` dejaría activas
las causas principales.

Respecto a escritura, debe distinguirse documento semántico de archivo físico del
almacén de objetos, inventario o transacción. Cientos de archivos internos no equivalen
a cientos de documentos redactados por IA. Este análisis no acredita generación
documental abusiva en todos los cambios; acredita sobreselección y repetición de lectura
y presentación, con riesgos adicionales de gestión.

## 6. Diseño recomendado para la mejora

### A. Seleccionar antes de transportar

Resolver la petición y sus dependencias desde las relaciones existentes, incluso
antes del plan. Recuperar contrato aplicable, código afectado y continuidad. Seguir
los enlaces pertinentes después de resolver el alcance. Una duda debe señalar qué
fuente podría afectar y por qué; la ausencia de metadatos no debe iniciar una revisión
general del histórico. Una incertidumbre material sigue impidiendo una aprobación
positiva sobre esa porción.

No exigir un proyecto previo de clasificación de todos los Markdown. El coste de
resolver ambigüedades debe estar incluido en la comparación de rendimiento. Cualquier
clasificación nueva tendrá que demostrar que ahorra trabajo total.

### B. Una representación útil por operación

Transportar una sola copia del texto necesario, con identificadores y procedencia.
Conservar un artefacto recuperable para inspección ampliada y recibos coherentes con
lo realmente presentado. Un catálogo o índice debe facilitar localizar información;
no debe expandirse automáticamente en su contenido completo. La vista de decisión
y el contexto para programar tienen necesidades distintas.

Las respuestas de estado deben explicar resultado, bloqueo y siguiente acción sin
reemitir todo el expediente. Cuando haga falta contexto adicional, recuperarlo por
la fuente o dependencia concreta. Un límite de tamaño debe detectar un exceso y
orientar su resolución; no recortar contratos silenciosamente.

### C. Reutilizar cálculo sin perder vigencia

Compartir una instantánea validada del modelo dentro de cada operación, con índices
por identidad y pertenencia. Evaluar caché derivada de parseo y dependencias entre
procesos, invalidada por cambios comprobables. `.lks-sdd/project.json` seguirá siendo
un índice; los Markdown seguirán siendo canónicos.

Conservar comprobaciones de concurrencia y cambios relevantes antes de aplicar una
decisión. Reutilizar un resultado interno no supone que el modelo conserve el texto:
al cambiar de chat o compactar debe recuperarse el contrato vigente necesario.
Las garantías de seguridad de rutas y transacciones también se mantienen.

### D. Reducir trabajo de coordinación

Las seis skills deben conducir al siguiente paso con las decisiones ya disponibles.
Cuando hay cobertura y autorización vigentes, continuar desde ellas. Agrupar dudas
compatibles; registrar hechos, decisiones y evidencia nuevos; reutilizar continuidad.
No convertir cada consulta, repetición de comando o cambio de chat en otro expediente.

La reducción de burocracia no debe sustituirse por más metadatos que redactar o por
pedir al usuario que apruebe en bloque información que no ha revisado. Tampoco se
necesitan nuevos agentes, conectores ni servicios para abordar las causas observadas.

## 7. Cómo medir si la release mejora el desarrollo

Medir el **trabajo completo**, desde la petición hasta la corrección verificada:

| Dimensión | Medida |
|---|---|
| IA | Input total por llamada, parte reutilizada según el proveedor, output, tokens de herramientas y ampliaciones; no mezclar instantáneas con acumulados. |
| Tiempo | Tiempo total, espera humana, espera de infraestructura, llamadas al modelo, herramientas y retrabajo, evitando doble conteo por concurrencia. |
| Contexto | Texto pertinente/ajeno, duplicación, relecturas, respuesta truncada y efecto de añadir historia independiente. |
| Gestión | Preguntas, decisiones nuevas y documentos semánticos creados/modificados; archivos físicos internos por separado. |
| Resultado | Cambio completado y verificado, obligaciones conservadas, errores y correcciones posteriores. |

La comparación de implementación debe conservar tarea, estado documental, modelo
y configuración equivalentes, registrar aciertos de caché y distinguir proceso nuevo
de proceso reutilizado. La espera de VPN y otras dependencias se informa por separado.
Una tarea que se bloquea antes no puede presentarse como más barata por consumir menos.

Primero se corrigen las causas P0 y las cargas repetidas observadas. Después se hace
una observación acotada de los cinco recorridos de la propuesta: corrección local,
ajuste de interfaz, nueva funcionalidad, contrato compartido y reanudación. Esa
observación se prepara una vez para aceptar esta mejora; no crea una campaña permanente
adicional a [la puerta de publicación](../../../docs/VALIDATION.md).

**Criterios concretos propuestos:**

- Añadir historia demostrablemente ajena no añade su texto ni sus recursos al contexto
  de la tarea, ni obliga al usuario a clasificarla por completo.
- El transporte ordinario contiene una sola copia de cada cuerpo necesario.
- Repetir una consulta sin cambios materiales no genera documentación ni otra aprobación.
- Una operación reutiliza su modelo validado en lugar de volver a parsearlo para cada subpaso,
  manteniendo las comprobaciones necesarias antes de aplicar cambios.
- Se reducen tokens observados y tiempo atribuible al flujo documental en los casos
  representativos, sin trasladar el coste a recuperación, preguntas, errores o retrabajo.

Los presupuestos numéricos de tokens y latencia deben fijarse con esos recorridos
de referencia antes de aceptar la implementación. Este diagnóstico no permite prometer
un porcentaje general de ahorro, una tarifa ni un tiempo máximo universal.

## 8. Qué soluciones serían insuficientes

- Cambiar solo `complete` o aceptar un recibo pese a una revisión incompleta.
- Cambiar únicamente el formato JSON o activar el modo de comparación.
- Resumir indiscriminadamente el contrato o truncar a un presupuesto arbitrario.
- Confiar en la caché del proveedor para evitar el trabajo de selección.
- Archivar o eliminar historia como condición para corregir un error pequeño.
- Introducir nuevos documentos obligatorios para clasificar todos los anteriores.
- Contar caracteres de una salida como ahorro facturado o trasladar todo el tiempo
  de la sesión al plugin.

## 9. Estado y siguiente decisión

El diagnóstico acredita un problema transversal de consumo documental en los
mecanismos examinados. La propuesta se actualiza para que **tokens de IA y tiempo de
desarrollo sean resultados explícitos de aceptación**, además de resolver el bloqueo.
Quedan pendientes el diseño concreto de aplicabilidad, los presupuestos de los
recorridos y su implementación autorizada. No se ha corregido todavía el runtime
ni el error de la aplicación, y no se acredita una nueva release.
