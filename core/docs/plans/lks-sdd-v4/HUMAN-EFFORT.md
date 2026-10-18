# V4-02 — Primera prueba de esfuerzo humano con Codex

Actualización: 2026-10-16. Estado: **protocolo humano retirado de la fase técnica;
percepción diferida a uso real sostenido por decisión del usuario**.

Este documento conserva la preparación y cronología históricas. Las fichas,
cronómetros y preguntas experimentales siguientes ya no son instrucciones activas.
La repetición se preparó sin iniciar casos; se aplica
[DECISION-TECHNICAL-SCOPE.md](DECISION-TECHNICAL-SCOPE.md). No se piden más datos humanos
para cerrar V4-02. El encargo posterior fija los parámetros en
[MEASUREMENT-PROTOCOL.md](MEASUREMENT-PROTOCOL.md) y cierra AC-33 en alcance técnico Codex.

Dictamen vigente en [REVIEW-S1-S2.md](REVIEW-S1-S2.md). Las secciones de preparación
y la cronología conservan su sentido histórico; los tiempos históricos no se pueden
recuperar ni sustituir por duraciones del chat. Feedback actual será retrospectivo.
Plan 0.2 validado; la autorización actual mantiene los cambios del plugin sin iniciar.
El usuario ha elegido participar personalmente. Se usa **P01** como etiqueta de
observación, sin inferir nombre real, identidad organizativa ni membresía de proyectos.
Copilot queda aplazado a la comprobación final. Los presupuestos ya están aceptados.

## 1. Qué hace falta del participante

1. Un hueco inicial de **30–45 minutos** con Codex y un cronómetro sencillo que permita
   pausar. Es una reserva para el piloto, no una duración demostrada ni una obligación
   de permanecer si hay una interrupción. No hace falta preparar repositorios ni datos.
2. Actuar con normalidad: pedir el cambio, leer las propuestas y decidir lo que se
   presenta. Preguntar si algo no se entiende; no adivinar el camino para que salga mejor.
3. Medir su tiempo activo durante las intervenciones y devolver **una ficha por caso**.
   Las pausas y la espera de Codex se registran aparte. La hora de un mensaje por sí
   sola no acredita tiempo de atención humana.

No se requiere grabar pantalla ni aportar credenciales. Si es difícil separar el
tiempo administrativo del funcional, se marca como mixto o desconocido. No se inventa
un reparto para completar una casilla. La medición se presenta como **cronometraje
autoinformado por P01**, con su resolución y límites, no como observación independiente.

## 2. Preparación que realizará el agente

- Preparar un consumidor sintético para cada ejercicio, con fuente/runtime publicado
  **3.4.3**, datos de prueba, versiones y estado inicial recuperables. No usar un proyecto
  real ni instalar o actualizar el plugin personal para ejecutar el piloto.
- Mostrar el objetivo, alcance y reglas de decisión. Aclarar que el historial de
  fixture es sintético; solo las respuestas realmente dadas por P01 son observación humana.
- Confirmar la configuración efectiva de Codex y registrar modelo/esfuerzo/herramientas;
  no cambiarlos dentro de una comparación. Comprobar disponibilidad de métricas otra vez.
- Separar preparación del banco de prueba de los costes de configuración/clasificación
  que realmente necesita cada versión. Estos últimos sí cuentan al comparar tareas.
- Iniciar el caso cuando estén claros la tarea y el estado inicial, sin dar pistas
  sobre la secuencia esperada de botones, comandos o respuestas.

P01 ha indicado «listo para la prueba». El consumidor sintético S1 está preparado,
con runtime 3.4.3 fijado y `readiness` permitido para iniciar; en aquel estado el código
devolvía `Adios`. El historial previo es sintético y no registra decisiones de P01.
El manifiesto recuperable está en
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\human-pilot-20261016\S1\case-manifest.json`.
Preparar el consumidor ha requerido 57,69 s de entorno; no es tiempo activo humano
ni una ejecución funcional terminada. Si conviene usar una conversación
nueva para controlar el contexto, se indicará entonces cómo abrirla y qué instrucción
copiar. No se crea otro chat o agente como efecto de preparar este protocolo.

## 3. Los dos ejercicios de referencia

Se ejecutan con 3.4.3 antes de observar la candidata. Se conservan los objetivos y
obligaciones de [SCENARIOS.json](SCENARIOS.json), sin convertir estos ejemplos en
requisitos de un consumidor real.

| Caso | Petición que hará P01 | Resultado funcional esperado |
|---|---|---|
| S1 · Corrección cubierta | «Corrige el saludo de esta tarea ya autorizada y comprueba el resultado». | `greeting()` devuelve `Hola`; conserva la interfaz sin parámetros y el alcance `app.py`. Prueba real, evidencia actual y estados correctos. |
| S2 · Cambio pequeño nuevo | «Añade la normalización de identificadores acordada y compruébala». | Función con entrada/salida cadena; recorta espacios ASCII exteriores, conserva espacios internos y mayúsculas, rechaza entradas no cadena con `TypeError`; sin persistencia ni servicios. |

S1 observa si se reutiliza correctamente un encargo vigente. S2 incluye definición,
validación de propuesta, plan/permiso y resultado. No se fusionan propuesta y plan
para acortar la prueba. Los pasos técnicos cubiertos no requieren una pregunta por
comando. Las decisiones funcionales necesarias se conservan aunque consuman tiempo.

Se anotan ayudas, campos reconstruidos y bloqueos tal como ocurran. Si un caso no
presenta fricción administrativa, se conserva ese resultado; no se provocan preguntas
redundantes para fabricar una referencia más costosa.

## 4. Cómo medir sin añadir un formulario por comando

Cuando haya una intervención real de P01, identificar su tipo por el contenido:

| Tipo | Tiempo que se registra | Ejemplos |
|---|---|---|
| Administrativo | Atención activa para entender cómo continuar, localizar/reconstruir datos o resolver coordinación del proceso. | Buscar el identificador que se vuelve a pedir, reconstruir el alcance, aclarar una confirmación repetida. |
| Funcional | Atención para decidir o comprobar el cambio solicitado. | Valorar la propuesta, decidir sobre el alcance, comprobar el resultado presentado. |
| Mixto/no separable | Tiempo activo cuya clasificación no puede hacerse con fundamento. | Una respuesta mezcla una decisión funcional y reconstrucción administrativa sin intervalos distinguibles. |
| Espera | Tiempo del modelo, herramientas o pruebas sin actividad del participante. | Mientras Codex ejecuta una prueba y P01 no está leyendo o decidiendo. |

P01 activa el cronómetro al empezar a leer/decidir/responder y lo pausa al enviar su
respuesta o dejar la actividad. Puede usar vueltas para distinguir bloques, con
resolución declarada. No tiene que cronometrar cada comando ni transcribir el registro.
Al final de cada caso se consolidan los bloques; el agente clasifica los datos con
P01, sin transformar una estimación imprecisa en segundos medidos.

La espera se obtiene de los límites observados del caso y las herramientas, con las
interrupciones anotadas; no se calcula tiempo humano como todo el intervalo entre
mensajes. Si P01 trabaja mientras Codex ejecuta, se registra la coincidencia y no se
suma dos veces al tiempo total. La ficha y las preguntas de evaluación son coste
del estudio, separado del flujo del producto.

## 5. Ficha única al terminar cada caso

```text
Caso: S1 / S2
Participante: P01
Experiencia previa con el plugin: inicial / ocasional / habitual
Cronómetro y resolución: ...
Tiempo activo administrativo: mm:ss / no separable
Tiempo activo funcional: mm:ss / no separable
Tiempo mixto, si existe: mm:ss / desconocido
Interrupciones ajenas: ninguna / descripción y duración aproximada
Ayudas necesarias para continuar: ninguna / descripción breve
Datos que tuviste que buscar o reconstruir: ninguno / descripción breve
Esfuerzo percibido: 1 muy bajo – 5 muy alto
Qué resultó más pesado o confuso: ...
```

No se exige contar de memoria cada solicitud: el agente obtiene del registro las
intervenciones y P01 aclara si fueron ayuda de procedimiento o decisión funcional.
La experiencia previa se recoge una sola vez. El esfuerzo 1–5 es una valoración
subjetiva complementaria; no sustituye tiempo, calidad ni comprensión.

Para comprobar comprensión, P01 responde brevemente al final:

1. ¿Qué cambio y alcance has dado por válidos?
2. ¿Qué pruebas se han ejecutado y cuáles siguen pendientes?
3. ¿Qué estado tiene el trabajo y qué falta para aceptarlo o entregarlo?

Se contrasta con el estado real usando la misma rúbrica en ambas versiones: 0
respuesta incorrecta, 1 parcial, 2 suficiente por pregunta. La corrección se explica
después de recoger la respuesta inicial; no se sustituye el primer resultado por uno
aprendido. Estas preguntas no se incorporan al flujo ordinario del plugin.

## 6. Qué se obtiene y qué queda pendiente

El primer piloto comprueba que las categorías se entiendan, el cronómetro resulte
usable y las fuentes permitan asociar intervenciones, resultado y tokens al caso.
Una persona y dos casos no representan a todos los equipos ni permiten estimar
variabilidad estable por sí solos. Si hace falta una segunda observación equivalente,
se decide y registra antes de ver la candidata y dentro del presupuesto aceptado.

`delta_admin` se fijará con la referencia real y una diferencia superior a la resolución
y variación justificables. Si los tiempos son mixtos o la muestra no permite decidir,
el criterio queda pendiente/inconcluso; no se fuerza una cifra. Si no hay coste humano
reducible, se declara que esos casos no acreditan reducción de tedio.

Se fijan también las métricas de utilidad temprana y `delta_util` con la referencia
actual, sin esperar al perfil de una implementación futura ni elegir umbrales después
de observar resultados favorables. Repeticiones, fallos y coste inicial se conservan.

## 7. Atribución de tokens al caso

El extractor [capture_codex_turn.py](tools/capture_codex_turn.py) ha comprobado un
turno cerrado preparatorio: 48 respuestas únicas, suma exacta del contador final,
sin duplicación de categorías. Eso valida la extracción por turno en este host,
no los tokens de S1/S2 ni un ahorro de 4.0.

Un caso humano puede abarcar varios turnos. Antes de empezar se registra el caso,
la sesión, los turnos iniciales y el criterio de finalización. Al terminar se agregan
únicamente sus turnos completos, sin sumarlos otra vez como contadores acumulados.
Pausas, reintentos y correcciones del caso permanecen dentro de la ventana; mensajes
de coordinación ajenos se identifican aparte. Una ventana incompleta no acredita
consumo completo. El contexto inicial, el aprendizaje y la caché se informan al comparar.

Para S1 se excluye el turno de preparación y entrega de la consigna
`01a1419f-ca06-77e0-bbc5-29b39b3a9b42`. La ventana funcional comienza con la primera
petición de tarea de P01 e incluye los turnos completos hasta presentar el resultado
técnico. Si necesita correcciones, se conservan sus turnos y se informa una nueva
ventana completa. La ficha y la comprobación de comprensión son evaluación del
estudio; los turnos que mezclen evaluación y trabajo funcional se identifican como
mixtos, sin atribuir su consumo íntegro a una categoría. Esta conversación contiene
contexto previo extenso: el piloto prueba viabilidad de medida, no una comparación
controlada con la futura candidata. Los costes de preparación permanecen recuperables.

El turno S1 `01a141a4-e838-7c42-922c-4004626015ba` ya está cerrado. Sus 16 respuestas
únicas suman exactamente el contador final: 1.571.310 tokens de entrada, incluidos
1.531.008 de entrada cacheada, y 12.880 de salida; total 1.584.190. Los 4.285 tokens
de razonamiento son parte de la salida, no un sumando adicional. La duración del
turno es 645.479 ms de reloj, no tiempo humano activo. Se conserva
`S1/token-attribution.json` junto a la extracción numérica, sin exportar transcripción.

El turno mezcla trabajo funcional, instrumentación/actualización del estudio y la
ficha de evaluación incluida en su respuesta final. Se registra como **mixto**: la
cuenta es exacta para el turno, pero no aísla tokens funcionales del plugin ni
coste facturado. El tamaño y la caché de esta conversación impiden usarlo como
comparación controlada con una candidata. La futura campaña debe fijar ventanas
equivalentes, instrumentación constante y contexto inicial comparable antes de medir.

El turno iniciado con «Continúa» también mezcla contabilidad de S1, preparación de S2
y presentación de su propuesta. Se conservará completo como mixto cuando termine;
no se contará íntegramente como consumo funcional de S2 ni se descartará su coste.

## 8. Presupuesto y siguiente acción

Límites aceptados: máximo 48 ejecuciones completas, 8 h de persona y 12 h de entorno
para la campaña; M6, dos variantes y cuatro horas de estudio. El límite específico
de M6 se aplica junto al global, no añade una bolsa de horas independiente. El coste
de todas las pruebas/fallos se conserva; no se declara un saldo exacto no medido.
Copilot se observa al final usando el protocolo fijado, sin reabrir ahora el alcance Codex.

P01 ha realizado la petición de S1. Se ha cambiado únicamente `app.py` dentro del
código del consumidor sintético; una ejecución real ha comprobado el resultado
`Hola` y la firma sin parámetros. El runtime registra la tarea `closed`; integración
y aceptación funcional siguen pendientes. Los registros canónicos y la evidencia
son cambios del proceso, separados del alcance de código. El plugin sigue intacto.

La ventana registra doce intentos CLI y una consulta API de lectura para recuperar
el diagnóstico: `usage-report` falla al renderizar `summary` como diccionario cuando
es una lista, tanto con `--compact` como con `--details`. Se conservan ambos fallos;
el segundo intento y la recuperación cuentan en el coste. La API devuelve el
informe, pero eso no convierte el CLI fallido en superado. El auxiliar no conservó
el código de salida ni la duración individual del primer fallo antes de intentar
parsear su stdout vacío; esos dos datos se marcan como no disponibles.

Los doce sobres del recorrido principal están conservados en el consumidor;
las dos consultas finales quedan recuperables externamente. El informe automático
no incluye el fallo posterior de su propio renderer: ese hallazgo se registra aparte,
sin convertir «sin disparadores» en ausencia de problemas. Los tokens del turno
completo se extraerán cuando termine; el tiempo humano y la comprensión no se infieren.

P01 ha indicado «Continúa» sin aportar la ficha de S1. Esta permanece pendiente;
no se interpreta como tiempo cero, rechazo de la evaluación, aceptación del resultado
ni respuesta a las preguntas de comprensión.

S2 está preparado con `app.py` vacío y runtime 3.4.3. La preparación del consumidor
ha requerido 53,93 s de entorno. Se han registrado la petición y una propuesta
conjunta sin aprobación sintética; la vista pública `decision-view` es completa,
sin incidencias y con receipt vigente. El texto íntegro está en
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\human-pilot-20261016\S2\PROPOSAL-REVIEW.md`.
Se presenta a P01 para validar antes de preparar el plan; no hay plan, tarea ni
permiso de implementación del caso. La configuración previa del consumidor es fixture.

P01 ha pedido revisar críticamente, mejorar y completar esa propuesta. Se registra
la iteración funcional como propuesta S2 **0.2** (revisión canónica 2): recorte de
prefijos/sufijos U+0020, preservación literal del resto, tipos/error sin coerción,
ocho criterios y 17 ejemplos esperados. La versión previa y su receipt quedan en
`S2/revision-01/`; se genera una vista completa sin incidencias y un receipt nuevo,
con base/contenido distintos. No se registra conformidad por pedir la revisión.

La vista de 3.4.3 transporta la matriz como texto escapado. Se prepara
`S2/PROPOSAL-0.2.md` como ayuda de lectura, conservando criterios y cuerpo canónico
completos y los 17 ejemplos; la salida original sigue recuperable. Es coste/ayuda
del estudio, no cambio del runtime ni una mejora que se atribuya a la referencia.
La precisión documental no demuestra menor esfuerzo humano; su mayor detalle
también tiene coste de lectura. Las dos versiones deberán usar la misma propuesta
finalmente validada y material comparable. SCENARIOS.json permanece sin cambios.

En la fase de propuesta, los 17 casos eran especificación y `app.py` estaba vacío.
P01 validó explícitamente la propuesta 0.2 y pidió preparar el plan sin implementar.
Se registró esa respuesta exacta mediante
`close-proposal`, reutilizando el receipt de la revisión 0.2, sin pedir otra firma.

Se prepara el plan S2 **0.1** y un único encargo con cinco actividades secuenciales:
preparar, implementar, probar, revisar/evidenciar y cerrar técnicamente. Mantiene
literalmente los ocho criterios, 17 ejemplos y dos comprobaciones automáticas
transversales, más dos revisiones técnicas. La revisión del asistente se identifica
como informe técnico, no observación humana ni revisión independiente.

La validación estática confirmó cobertura completa del núcleo y ausencia de
decisiones de plan/ejecución o eventos de inicio. La consulta inicial de aprobación
solo del plan usó incorrectamente `ids` donde el CLI requiere `units`; por eso no
seleccionaba sus tareas. Se conserva el registro original y se corrige expresamente
su atribución al plugin: era un error del auxiliar. Con `units` la vista separada
es completa, sin incidencias ni escrituras. La vista conjunta previa también era
una consulta: no aplicaba ni concedía aprobación o autorización.

P01 ha pedido revisar críticamente el plan. La revisión **0.2** fija el orden de
registros, una base por huellas sin HEAD, carga aislada del módulo y captura antes
de parsear. Conserva los ocho criterios y los 17 ejemplos; añade una comprobación
del recorte redefinido por una subclase, con total 20 automáticas/dos revisiones.
Las dependencias normales son acíclicas; el reintento es un retorno condicional
explícito, no una nueva autorización ni una dependencia contractual circular.

El plan legible 0.2 tiene 7.107 caracteres frente a 9.439 del 0.1 (24,71 % menos),
sin presentarlo como ahorro de tokens/esfuerzo de la tarea completa. Su revisión
crítica, disposición de S2-OBS-02 y verificaciones quedan en `S2/plan-02/` y
`S2/PLAN-CRITICAL-REVIEW.md`. La propuesta validada y la matriz original no cambian;
no se vuelven a pedir sus decisiones. La preparación y las consultas fallidas
siguen contando como costes del estudio, diferenciados de defectos del producto.

El documento actual es `S2/IMPLEMENTATION-PLAN-0.2.md`; el plan 0.1 y los receipts
anteriores quedan conservados como históricos, sin reutilizarlos para la revisión
nueva. P01 ha aprobado después el plan 0.2 y autorizado expresamente ejecutarlo
en el consumidor sintético, conservando la prohibición de modificar el plugin.
Se registran plan, permiso y revisión del encargo sobre una vista vigente; se
comprueba readiness y se registra start antes de editar código.

La función ya está implementada solo en `app.py`. Una ejecución real en proceso
Python nuevo ha superado las 20 comprobaciones automáticas; las dos revisiones
técnicas del asistente también son conformes. Son 22/22 comprobaciones con sus
IDs exactos, evidencia automática/informe de revisión diferenciados y la misma
huella de código. El runtime registra implement, ambas evidencias, verify y close
en ese orden. La consulta final confirma tarea cerrada y H5 completo; H6 sigue pendiente.

Resultado recuperable: `S2/EXECUTION-RESULT.md`, con capturas, comando/ejecutor,
resultados por caso, revisión y registros CLI en `S2/execution-01/`. La matriz,
el plugin y el runtime fijado permanecen intactos. Sonar y Dependency-Check siguen
como no utilizados por decisión del fixture; no son controles superados. La
revisión del asistente no es observación humana ni revisión independiente.

El diagnóstico conservado del caso registra 22 invocaciones/34 sobres, ocho
hallazgos candidatos y un tipo de hueco: en dos observaciones de preparación no
se validó la vinculación al trabajo y sus referencias se conservaron como datos.
No se presenta esa cobertura como contabilidad completa del host. El informe se
recupera mediante la API de lectura, manteniendo la limitación del renderer CLI
observada en S1; no se repiten sus fallos conocidos ni se modifica producto.

Las ventanas completas de tokens se consolidan al cerrar los turnos; la actual
continúa abierta hasta entregar el resultado. No se infiere tiempo humano,
comprensión o ahorro. Fichas, integración/aceptación y AC-33 siguen pendientes.

Al terminar la ejecución quedaba pendiente recoger las fichas y comprensión de S1/S2 y revisar las métricas
con sus límites. Los resultados se revisarán antes
de cerrar AC-33 y antes de cualquier cambio del plugin, conforme al encargo actual.

## 9. Revisión S1/S2 y decisión sobre la medición humana

La revisión crítica solicitada se completa en REVIEW-S1-S2.md. Los cinco turnos
cerrados registrados en S2 suman 11.487.304 tokens observados, con 54 respuestas
únicas y suma igual a cada contador final. Incluyen estudio, revisiones y parte de
la contabilidad de S1; no representan coste funcional aislado ni ahorro. Las
capturas numéricas quedan en `S2/token-review-20261016/` del piloto externo.

P01 responde expresamente **«No los cronometré»**. Los tiempos de S1/S2 quedan
`not-measured-confirmed`, sin reconstrucción retrospectiva. Lo que aún puede
aportar sobre experiencia, esfuerzo 1–5, ayudas y dificultades se registrará como
feedback retrospectivo. Una respuesta actual de comprensión, después de conocer
el resultado explicado, no reemplaza la comprensión inicial prevista en el protocolo.

Se recomienda una nueva referencia breve con casos equivalentes y contexto
controlado antes de candidata, sin ejecutar ahora ni alterar el plugin. Se propone
tope de 30 minutos de atención activa de P01, esperas separadas y parada/inconcluso
si resulta insuficiente, dentro de los recursos ya aceptados. No es una promesa de
duración ni una ampliación de presupuesto. Primero se coordina disponibilidad;
el agente prepara material y registro, P01 cronometra sus intervalos y aporta la
valoración. No se pide una ficha por comando ni se repiten las 22 comprobaciones
vigentes para remediar una ausencia de cronómetro.

AC-33 continúa abierto por referencia humana/comparabilidad y parámetros operativos.
Si P01 prefiere limitar el estudio a referencia técnica, se debe decidir expresamente
qué ocurre con E5 y los campos exigidos por AC-33 antes de ampliar desarrollo; la
aceptación de este informe no implica esa decisión ni autorización para implementar.
