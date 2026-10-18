# V4-02 — Revisión crítica de S1 y S2

Fecha: 2026-10-16. Complementa el plan **0.2 validado**, sin modificar sus garantías,
criterios de aceptación ni seis mejoras. Estado: **referencia técnica comprobada;
AC-33 abierto en el momento de esta revisión**.
No hay implementación de 4.0 ni autorización para iniciarla.

**Decisión posterior del usuario:** [la valoración humana se difiere a uso real
sostenido](DECISION-TECHNICAL-SCOPE.md). Se conserva el dictamen histórico siguiente;
su propuesta de repetir cronometraje/fichas queda retirada. AC-33 sigue abierto
por parámetros técnicos en esa etapa, sin exigir nuevos datos humanos ni `delta_admin`.
Cierre documental posterior: [MEASUREMENT-PROTOCOL.md](MEASUREMENT-PROTOCOL.md) 1.0
fija esos parámetros y cierra AC-33 en alcance técnico Codex, sin comparación 4.0.

## 1. Dictamen y alcance de la revisión

S1 y S2 demuestran que 3.4.3 permite completar estos dos ejercicios con pruebas
reales, evidencia recuperable y separación entre autorización, cierre técnico e
integración/aceptación. No demuestran todavía ahorro, ausencia de tedio ni calidad
general del plugin. No existe una candidata con la que compararlos.

Se han contrastado capturas, resultados, código actual, matriz congelada, copias de
evidencia y huellas. Los 22 identificadores de comprobación de S2 coinciden exactamente
con el plan 0.2; el código coincide con el probado y las evidencias originales con
sus copias en el consumidor. Los **668 archivos del runtime S2** incluidos en la
huella previa siguen iguales. La revisión no repite ejecuciones funcionales ni
convierte la revisión del asistente en revisión independiente.

La evidencia de esta revisión se conserva en el área H1 existente:
`C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/human-pilot-20261016/S2/token-review-20261016/`.
Responsable: tarea actual V4-02; hereda la conservación del área mientras el estudio
siga abierto. `evidence-critical-audit.json` vincula comprobaciones y SHA-256;
`documents-before-review/` permite comparar la documentación anterior. No se cambia
la congelación original de fuentes, paquetes, escenarios ni decisiones aprobadas.

## 2. Resultados funcionales y sus límites

| Aspecto | S1 | S2 | Valoración crítica |
|---|---|---|---|
| Resultado | `greeting()` devuelve `Hola`, sin parámetros. | `normalize_identifier(value)` recorta solo U+0020 exteriores, conserva el resto y rechaza otros tipos con `TypeError`. | Resultados conformes al contrato concreto; no extrapolables a proyectos complejos. |
| Evidencia | Proceso real con aserción del resultado y comprobación de firma. | **20 comprobaciones automáticas + 2 revisiones técnicas del asistente**, conformes. Matriz de 17 ejemplos más interfaz, idempotencia y subclase con `strip` redefinido. | No son 22 pruebas automáticas ni revisión humana/independiente. Los ejemplos cubren fronteras relevantes, no todo posible programa o entrada. |
| Alcance | Código limitado a `app.py`. | Código limitado a `app.py`; matriz, runtime y copias de evidencia contrastados. | Las escrituras canónicas del proceso se separan del código. Una función de cinco líneas no justifica eliminar casos Unicode, tipos o efectos acordados. |
| Autoridad | Corrección cubierta por historial sintético declarado; petición real del usuario. | Validación real de propuesta, aprobación de plan 0.2 y autorización expresa de ejecución. | No son recorridos equivalentes: S1 reutiliza cobertura; S2 incluye definición y planificación. |
| Estado | Cerrado técnicamente. | Cerrado técnicamente. | Integración y aceptación funcional pendientes en ambos. No son requisitos adicionales de aceptación de una candidata inexistente para AC-33. |
| Política de calidad | Configuración de laboratorio. | Sonar y Dependency-Check no usados según política sintética. | No se presentan como superados ni acreditan el flujo de una organización real. |

Los informes de ejecución originales se conservan en `S1/execution/technical-result.json`
y `S2/EXECUTION-RESULT.md`, dentro del mismo piloto externo. Las revisiones solicitadas
por el usuario son trabajo funcional de evaluación; no son confirmaciones redundantes
impuestas por el plugin. El coste de instrumentación y de errores del observador
también se conserva, separado de su atribución causal.

## 3. Incidencias: qué está probado y qué cambia con esta revisión

| Observación | Dictamen actualizado | Consecuencia para 4.0 |
|---|---|---|
| S1: fallan `usage-report --json --compact` y `--details`. | **Defecto confirmado de presentación**: `display_summary` espera un diccionario y recibe una lista; las trazas y la respuesta recuperada por API concuerdan con el código. Dos intentos fallidos conservados. | Incorporar su reproducción y la salida real del CLI a M1. La API de respaldo permitió consultar datos; no demuestra que el CLI funcione. No se corrige ahora. |
| S2: presentación de aprobación del plan inicialmente incompleta. | **Error del auxiliar**, que envió `ids` en vez de `units`. La consulta correcta es completa. Se conserva y rectifica la atribución anterior. | No crear una corrección de núcleo para un defecto no demostrado. Mantener el coste del error como coste del estudio; revisar ayuda de uso solo si aparece confusión repetida. |
| S2: ocho avisos UF-01 de fragmentos repetidos. | Ocho candidatos, agrupables en **tres conjuntos de observaciones parcialmente solapados**: vistas de plan 0.1/0.2 y autorización, vistas de propuesta 0.1/0.2 y el subconjunto de dos vistas del plan 0.2. Comparten materiales; no son ocho defectos independientes. | Revalidar autoridad, revisar una nueva versión y atender otra decisión justifican parte de la repetición. M2 solo elimina preparación duplicada demostrablemente prescindible, conservando el contrato y la vigencia de cada decisión. No sumar ocho ahorros hipotéticos. |
| S2: un tipo de hueco, en dos sobres `prepared` de `author`. | Se localizan al preparar la creación de petición/propuesta y plan/tarea. En ambos casos la observación `applied` de la misma invocación está vinculada y sin huecos. Compatible con referencias aún inexistentes al preparar; no prueba pérdida del contrato. | Conservar ambos estados y la correlación. La cobertura de preparación sigue siendo provisional; no se declara completa ni se borra el hueco del informe original. |
| Medición de S1. | El primer auxiliar no conservó correctamente todos los metadatos del primer fallo antes de analizar stdout; existen capturas y trazas, pero no se reconstruyen tiempos/códigos ausentes. La consulta API no tuvo snapshot antes/después. | Limitación de observación, separada del defecto del CLI. No afirmar integridad observada de esa consulta ni completar datos de memoria. |

Un informe automático sin avisos no demuestra ausencia de problemas: las operaciones
`usage-*` no se observan a sí mismas y el fallo de su renderer quedó fuera de sus
hallazgos. El reporte S2 contabiliza **22 invocaciones / 34 sobres conservados**,
45.286 caracteres acumulados y 20.141 únicos por revisión. Son métricas de fragmentos
observados; no son todo el transporte, lecturas reales del modelo ni tokens del host.

## 4. Tokens: cuenta consolidada y uso correcto

Configuración observada en todos los turnos incluidos: **Codex, gpt-6.1-sol, xhigh**.
Se deduplican respuestas y se comprueba la igualdad con el contador final de cada
turno cerrado. No se exportan transcripciones.

| Ventana conservada | Respuestas únicas | Entrada | Entrada cacheada, incluida en entrada | Salida | Total observado |
|---|---:|---:|---:|---:|---:|
| S1: un turno de ejecución/estudio | 16 | 1.571.310 | 1.531.008 | 12.880 | **1.584.190** |
| S2: cinco turnos de preparación, revisiones, planificación y ejecución/estudio | 54 | 11.390.080 | 11.097.472 | 97.224 | **11.487.304** |

El primer turno atribuido a la ventana S2 incluye también contabilidad de S1. Se
conserva completo y se etiqueta mixto; no se inventa un reparto ni una sustracción.
La revisión actual queda fuera de estas ventanas funcionales históricas y constituye
coste adicional del estudio. La calibración preparatoria de 48 respuestas es otra
ventana, excluida de ambos casos.

Los cinco turnos S2 suman 3.015,394 segundos de ejecución del agente; S1 registra
645,479 segundos. No incluyen necesariamente toda espera entre mensajes ni son
minutos de atención humana. Caché y razonamiento son subconjuntos, no importes que
añadir al total. No hay factura atribuible acreditada.

La cuenta prueba **disponibilidad y consistencia de la métrica**, no el consumo
aislado del plugin. La conversación larga, la instrumentación, las revisiones pedidas
y las ayudas de presentación contaminan una comparación causal. S2 no demuestra que
el plugin consuma un múltiplo de S1; tampoco el recorte del plan de 9.439 a 7.107
caracteres (24,71 %) demuestra ahorro de tokens o de trabajo humano.

## 5. Qué implica para las seis mejoras

| Mejora | Evidencia que la apoya | Límite / decisión recomendada |
|---|---|---|
| M1 · Presentación y captura | Fallo real del renderer y volumen diagnóstico ya medido en BASELINE. | Prioridad mejor fundamentada. Medir salida completa, incluida captura/exportación, y corregir el fallo sin perder acceso íntegro. Ahorro todavía desconocido. |
| M2 · Operaciones y continuidad | Recorridos con varias consultas, transiciones y registros; materiales repetidos entre vistas. | Oportunidad plausible de coordinación. Separar duplicación evitable, lectura normativa y decisiones humanas distintas; no fusionar aprobaciones ni conservar autoridad caducada. |
| M3 · Alcance explícito | Ambos casos pequeños y alcance `app.py` controlado. | No prueban poda segura en repositorios grandes ni legado heterogéneo. Mantener cobertura conservadora y validación adversa prevista. |
| M4 · Instrucciones por operación | La base ya tiene doce rutas selectivas de 3–6 archivos; hubo un error de uso del auxiliar. | Comparar con esa base bien usada; no prometer reducción por sustituir una carga indiscriminada ficticia. Un error del observador no demuestra un defecto de instrucciones. |
| M5 · Correcciones existentes | S1 completó una corrección cubierta sin repetir la validación funcional. | Confirma capacidad ya disponible; priorizar su mejor uso con M2/M4. No justifica una nueva clase de núcleo. |
| M6 · Optimización acotada | Hay tiempos descriptivos de componentes y del recorrido de referencia. | No se ha probado un cuello de botella causal ni beneficio útil repetible. Perfil dentro del presupuesto; descarte sin cambios sigue siendo válido. |

Las seis siguen siendo compatibles como líneas de trabajo. Eliminar decisiones,
resumir obligaciones con pérdida, atribuir avisos automáticamente a defectos o
optimizar sin beneficio acreditado siguen fuera del plan. La evidencia favorece
empezar por M1/M2/M4 cuando se cierre H1 y exista autorización posterior.

## 6. Actualización del protocolo y cierre de V4-02

P01 confirma en esta revisión: **«No los cronometré»**. Los tiempos activos de S1/S2
pasan a **no medidos confirmados**. No se solicitan estimaciones para rellenarlos.
La experiencia, esfuerzo y dificultades aún pueden recogerse como valoración
retrospectiva, sin convertirlas en medición contemporánea. Tras explicar los
resultados, una respuesta de comprensión actual tampoco reconstruye la comprensión
inicial del piloto. Ninguna de estas ausencias equivale a cero fricción.

| Elemento de AC-33 | Estado tras revisar | Acción necesaria |
|---|---|---|
| Fuentes, paquetes, hashes, referencia y casos | Disponible, con límites explícitos. S1/S2 funcionales completos; no campaña completa S1–S7. | Preservar referencia y costes fallidos; no repetir las 22 comprobaciones sin cambio o preocupación nueva. |
| Host y contadores reales | Viabilidad Codex contrastada; ventanas históricas mixtas. Copilot aplazado por decisión vigente. | Fijar ventanas comparables antes de comparar una candidata; validar otra vez la extracción del host. No hace falta comprar acceso para esta métrica local. |
| Medición humana | S1/S2 sin cronómetro; feedback retrospectivo todavía ausente. | Recomendación: breve repetición de referencia 3.4.3 con dos casos equivalentes nuevos y cronómetro, dentro de los límites aceptados. |
| Responsables y recursos | P01 participante; agente prepara/observa/consolida; usuario interlocutor de valoración. Techos 48 ejecuciones, 8 h humanas, 12 h de entorno; M6 dos variantes/cuatro horas dentro de los globales. | Conservar dos casos completados en este piloto y el resto de intentos/componentes por separado. No hay saldo histórico exacto de horas; iniciar registro de intervalos y reconciliar el ledger antes de reservar nuevas ejecuciones. No contar 54 respuestas ni 22 pruebas como ejecuciones completas. |
| E1/E2/E3 | Objetivos validados: 30 % transporte, 20 % llamadas administrativas, 15 % tokens comparables. | No se reabren ni se declaran alcanzados. E3 sigue sin evaluación comparable. |
| Utilidad H2, `delta_admin`, `delta_util` | No congelados; no inventar cifras a partir de tokens ni de esperas del chat. | Concretar con la referencia y antes de ver una candidata. El agente prepara la justificación; P01 aporta percepción de utilidad y medición humana, no cálculos internos. |

**Repetición recomendada, aún sin ejecutar:** fijar antes fuente/configuración,
contratos equivalentes y límites de caso en conversación con contexto inicial
controlado; separar setup, instrumentación y evaluación del trabajo funcional y
contabilizar también sus costes. Captura numérica externa, sin pedir un formulario
por comando; mismas ayudas y política en referencia/candidata. Mantener lectura
íntegra de obligaciones. Incluir en el caso todas las decisiones, errores y
recuperaciones necesarias, sin dar a la candidata una solución ya preparada.

P01 cronometra lectura/decisión/respuesta, separando administrativo, funcional y
mixto cuando pueda; desconocido/no separable sigue siendo válido. Se propone una
primera sesión con **tope de 30 minutos de atención activa**, más esperas registradas
aparte, con parada y dictamen inconcluso si no alcanza. Es un límite propuesto de
sesión, no una duración prometida ni una ampliación de los presupuestos.

La referencia determina si existe trabajo administrativo reducible y su resolución.
Si no permite justificar `delta_admin` por encima de resolución/variación, se mantiene
pendiente y se decide una repetición adicional acotada **antes** de observar candidata;
no se lanzan intentos indefinidos. Si el coste reducible es cero, se conserva cero y
se resuelve expresamente el alcance de E5. Para H2 no basta ahorrar un byte: se debe
fijar magnitud útil y trabajo evitable concreto con esa referencia. Para M6 se fija
un beneficio absoluto y regla de ruido previos a ensayar variantes; el descarte no
requiere inventar una optimización.

**Qué falta del usuario para cerrar:** indicar disponibilidad para esa sesión de
referencia y aportar una valoración breve de cada caso (esfuerzo 1–5 y qué obligó a
leer, buscar, preguntar o corregir), más experiencia previa una sola vez. Durante
la repetición, aportar tiempos activos y respuestas iniciales de comprensión antes
de explicarlas. El agente prepara material/registro, compara fuentes y concreta los
umbrales a partir de evidencia suficiente. La disponibilidad por sí sola no cierra
AC-33: deben quedar medidos o expresamente limitados los campos y congelados sus
valores antes de la candidata.

Si P01 prefiere no repetir, cabe proponer un cierre de alcance reducido: referencia
técnica/descriptiva, ahorro humano y tokens comparables sin demostrar. **No se adopta
automáticamente:** el plan 0.2 exige E5 y valores completos en AC-33; haría falta una
decisión expresa sobre ese alcance y su criterio pendiente. No se marca AC-33 como
superado solo por aceptar el informe o por presentar la alternativa.

V4-02 queda **en curso**, con la revisión documental y consolidación técnica
terminadas. No hace falta aceptar/integrar los consumidores sintéticos, elegir otra
vez host/presupuesto ni autorizar cambios de plugin para resolver esta fase.
