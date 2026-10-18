**Decisión vigente:** el responsable valida y cierra el desarrollo, autoriza publicar 4.0.0 y distribuirla en Codex. Se mantienen las reservas de Windows/H2 y medición; los controles técnicos pendientes no se convierten en superados. Aprobación: [4.0.0](../../../quality/release-approval-v4.0.0.json); [actualización y límites](../../UPGRADE-4.0.0.md). Publicación efectiva y gate se acreditan por separado.

**Estado vigente de 0.7 validada:** V4-15 técnica, V4-16 y V4-18 cerradas con reservas explícitas; [resultado final](RESULTS-V4-19-20.md#v4-15-v4-16-y-v4-18--cierre-técnico-y-paquetes-finales-de-desarrollo). Desarrollo y paquetes preparados; aceptación completa, aprobación de versión e integración/gate estable separados. Windows/H2 pendientes; sin instalación ni publicación. Seis mejoras y presupuestos conservados.

**Resultado técnico anterior:** nueva serie ABBA completa: salida −26,7 %, flujo medido −44,9 %, llamadas −25 % y memoria válida; tiempo técnico +33,5 %, objetivo S8 no cumplido ([resultado](RESULTS-V4-17-SHARED-COMPARISON.md)). 54/54 plazas conocidas/reservadas, H2 protegida; Windows/H2 pendientes.
Actualización V4-07A: actividad e interrupción implementadas localmente;
[validación y pendientes](RESULTS-V4-07A.md). La aceptación del sobrecoste sigue
pendiente; no cambia la cobertura, las seis mejoras ni los presupuestos.

# LKS-SDD 4.0 — Plan de implementación

**Antecedente — cierre operativo:** [perfiles retirados y residual conservado](RESULTS-H2-OPERATIONAL-CLOSURE.md). La incidencia de Windows sigue abierta; H2/AC-34 inconclusos, sin nuevas pruebas, cargas o accesos.

**Antecedente — revisión de recuperación:** [incumplimiento de cota, recuperación y saldo recalculado](REVIEW-H2-MINIMAL-RECOVERY.md). El ensayo mínimo cerró en 358,500 s; H2 sigue inconcluso y no es admisible con el saldo actual. Recuperación operativa propuesta; estado nativo y retirada física pendientes.

**Antecedente — ejecución H2:** [ejecución H2 0.2: corte P2, perfiles recuperados y cero casos](RESULTS-H2-02.md). AC-34 pendiente; no se inicia V4-06. Los estados anteriores se conservan como antecedentes.

**Antecedente operativo (2026-10-16):** [carga A/B resuelta; aislamiento sin acreditar; recuperación de perfiles comprobada](RESULTS-H2-CONTINUATION.md). Ningún caso H2 iniciado, AC-34 pendiente. Se conserva estado nativo de Windows sin acreditar su reversión; no hay candidata activa. Los estados preparatorios e informes anteriores que siguen se conservan como antecedentes.

Fecha inicial: 2026-10-15. Actualización: 2026-10-16. Revisión: **0.4**.
Deriva de la 0.2 validada y revisa críticamente la ampliación 0.3; incorpora la prevención de regresiones de rutas temporales largas en Windows.
Base examinada: plugin **3.4.3**, commit `bf4d059c98826039097d606121ab6406d762fcc7`.
Estado: **plan 0.4 validado; V4-02A/V4-02B verificadas en alcance preparatorio; V4-03/V4-04/V4-05 verificadas en alcance técnico local; V4-05A con porción técnica verificada y AC-34 pendiente de H2 real**.
Actualización de 2026-10-16: Codex primero, Copilot al final; presupuestos aceptados
y participación del usuario como P01 confirmada. S1/S2 cerrados técnicamente y
[revisados críticamente](REVIEW-S1-S2.md); tiempos humanos no medidos, según P01.
AC-33 cerrado en alcance técnico Codex mediante [protocolo 1.0](MEASUREMENT-PROTOCOL.md).
H1 preparatorio completo; comparación H2 en host aún no ejecutada. Decisión del usuario:
[valoración humana diferida a uso real sostenido](DECISION-TECHNICAL-SCOPE.md);
la prueba cronometrada preparada se retira sin ejecutar. Se conservan las seis mejoras.
V4-02A/V4-02B están `verified` en alcance preparatorio; resolución del incidente real inconclusa;
V4-07A/V4-17A siguen `planned`. [Resultados y pendientes](RESULTS-V4-02AB.md).
Decisión posterior: S8 exige mejora temporal ≥20 % frente a 3.4.3, según
[S8-PROTOCOL.md](S8-PROTOCOL.md); reemplaza el máximo absoluto pendiente.
Autorización posterior: ejecutar únicamente V4-03 y presentar sus resultados antes
de continuar. [Resultados y límites de V4-03](RESULTS-V4-03.md) y
[estado actual](v4-03-progress.json). Se conservan las seis mejoras y los presupuestos;
Este registro de V4-03 es histórico; la autorización posterior inicia V4-04.
La revisión crítica posterior corrige condiciones de exportación, procedencia y
límites diagnósticos, destinos protegidos y efectos en modo compatible:
[dictamen vigente de V4-03](REVIEW-V4-03.md). El ahorro inicial queda sustituido por
la medición de la candidata corregida; no cierra eficiencia integral ni S8.
El usuario valida esa revisión y autoriza únicamente V4-04: captura y conservación
diagnóstica, garantías y presentación de resultados antes de continuar.
[Resultados de V4-04](RESULTS-V4-04.md) y [estado actual](v4-04-progress.json).
La [revisión crítica correctiva de V4-04](REVIEW-V4-04.md) sustituye el dictamen en
adjuntos, Windows, límites de lectura, recuperación y alcance de la evidencia.
Ese límite corresponde al bloque V4-04, ya finalizado.
El usuario valida su revisión y autoriza exclusivamente V4-05: consulta compuesta
y comprobaciones locales. [Resultados V4-05](RESULTS-V4-05.md) y
[estado V4-05](v4-05-progress.json). Ese límite de autorización es histórico.
El usuario valida la corrección Git/Windows y autoriza V4-05A: primer recorrido
completo, instrucciones necesarias y paquete provisional; resultados antes de
continuar. [Resultados V4-05A](RESULTS-V4-05A.md): S1 técnico 36/36, 14 regresiones
distintas y paquete reproducible; AC-34 sigue pendiente de carga autorizada y pareja
real H2 en Codex. [Estado V4-05A](v4-05a-progress.json). V4-06 y posteriores no se inician.
La [revisión crítica correctiva de V4-05](REVIEW-V4-05.md) concreta la evidencia
vigente de transacciones, declaraciones del runtime, snapshots y paquetes.
La [revisión crítica](REVIEW-0.3.md) corrige dependencias, ensayo temprano, reservas y límites.
El compromiso base reserva 43/48 plazas; dos intentos técnicos adicionales V4-05A
lo elevan aritméticamente a 45/48, sin certificar saldo. La viabilidad integral de
horas no está acreditada.
La revisión V4-05A queda validada por el usuario. Se prepara únicamente el
[plan de carga aislada, recuperación y H2](H2-LOAD-PLAN.md): sin instalación ni
ejecución, con admisión de horas pendiente y sin modificar el protocolo congelado.
El [complemento de rendimiento](ADDENDUM-PERFORMANCE.md) define S8 y su aceptación.
V4-02/AC-33 y el protocolo 1.0 permanecen cerrados/congelados en su alcance original.

## 1. Encargo y límite de autorización

**Antecedente de autorización H2:** usuario autorizó resolver la carga, comprobar aislamiento y
ejecutar H2 con recuperación dentro del saldo de los 45 min originales.
[Resultado vigente](RESULTS-H2-CONTINUATION.md): carga A/B resuelta, aislamiento
nativo sin acreditar y ningún caso iniciado. Plugin, catálogo y autenticación
temporales retirados; estado nativo de Windows conservado sin acreditar reversión.
AC-34 pendiente. No se inicia V4-06 ni se modifica el plugin.

**Autorización técnica anterior, conservada como antecedente:** el usuario valida la corrección de V4-05 y autoriza
«V4-05A. Ejecuta el primer recorrido completo y prepara el paquete provisional
dentro de los límites acordados. Comprueba las garantías y presenta los resultados
antes de continuar». Autoriza integración local de esta porción y preparación del
paquete; no instalación/registro/activación en el host, commits del plugin, push,
publicación ni tareas posteriores. La preparación sintética no sustituye H2 real.
Las peticiones iniciales de solo planificación que se citan a continuación son
antecedentes; las autorizaciones posteriores se limitan a las porciones expresas.

Petición del usuario: «Prepara el plan de implementación de la versión 4.0 con las
seis mejoras reformuladas, tareas, dependencias y criterios de aceptación. Incluye
cómo comprobar el ahorro sin perder garantías. No implementes nada todavía».

La revisión 0.2 incorpora la revisión crítica solicitada: separa cierre técnico y
aceptación en uso real, comprueba primero la viabilidad de medición, adelanta un
recorrido completo, concreta la aportación de M5 y acota la validación del ahorro.
Autorización posterior del usuario: «Valido el plan 0.2. Empieza por V4-01 y V4-02
y presenta los resultados y decisiones pendientes antes de implementar cambios en
el plugin». Se ejecutan únicamente esas dos tareas preparatorias. No cambia código
del plugin, schemas, skills activas,
versiones, configuración, contratos canónicos ni consumidores. No autoriza commits,
integración, push, etiquetas, publicación o instalación. La elección de estas seis
líneas para planificar no aprueba anticipadamente los detalles técnicos ni las
cifras objetivo de este documento.

Es un plan de mantenimiento del plugin, conforme a los precedentes de `docs/plans/`.
Petición de esta revisión: «Revisa de forma crítica el plan 0.3, mejóralo y comprueba
que las cuatro tareas nuevas encajan sin contradicciones y son viables dentro de los
presupuestos acordados. No implementes todavía». El usuario añade evitar la regresión
de temporales largos de Windows. Se autoriza actualizar documentación; no ejecutar
las tareas, modificar el plugin ni operar sobre un consumidor real.

Los IDs `V4-01` a `V4-18`, incluidos `V4-02A`, `V4-02B`, `V4-05A`, `V4-07A` y `V4-17A`, no son tareas ejecutables de un consumidor ni identidades
de personas. No se inicializa `.lks-sdd/project.json` para preparar este trabajo.
Al empezar V4-01/V4-02 se confirma el mismo HEAD y únicamente estos documentos
locales del plan. V4-02A/V4-02B, V4-03 y V4-04 cuentan con autorización expresa posterior; el resto requiere autorización de ejecución;
se comprobarán de nuevo HEAD, cambios concurrentes, runtime y alcance.

Documentos del plan:

- [Tareas, dependencias y entregables](TASKS.md).
- [Criterios de aceptación y comprobación del ahorro](VALIDATION.md).
- [Contrato operativo y compatibilidad de V4-01](CONTRACT.md).
- [Referencia y viabilidad de medición de V4-02](BASELINE.md).
- [Resultados H1 y decisiones pendientes](RESULTS-H1.md).
- [Prueba de esfuerzo humano con P01 en Codex](HUMAN-EFFORT.md).
- [Revisión crítica de S1/S2 y requisitos de cierre de V4-02](REVIEW-S1-S2.md).
- [Decisión de alcance: evaluación técnica y percepción en uso real](DECISION-TECHNICAL-SCOPE.md).
- [Ventanas comparables y umbrales técnicos congelados](MEASUREMENT-PROTOCOL.md).
- [Complemento de rendimiento, caso S8 y recursos de la revisión 0.4](ADDENDUM-PERFORMANCE.md).
- [Análisis del reporte recibido](ANALISIS-REPORTE-RENDIMIENTO-20261016.md).
- [Revisión crítica de 0.3 y cambios aplicados](REVIEW-0.3.md).
- [Registro histórico de la revisión aprobada](REVISION-0.4.json).
- [Resultados de V4-02A/V4-02B](RESULTS-V4-02AB.md).
- [Estado preparatorio histórico](v4-02ab-progress.json).
- [Contrato S8 y decisión posterior del 20 %](S8-PROTOCOL.md).
- [Implementación y resultados de V4-03](RESULTS-V4-03.md).
- [Estado histórico de V4-03](v4-03-progress.json).
- [Implementación y resultados de V4-04](RESULTS-V4-04.md).
- [Estado de ejecución actual](v4-04-progress.json).

## 2. Objetivo, hechos e hipótesis

**Objetivo funcional:** completar desarrollo y mantenimiento con menos coordinación
administrativa, repeticiones y espera, conservando acuerdos comprensibles,
autorización delimitada, implementación correcta, evidencia y continuidad.

**Hechos comprobados en la base:**

- Existen seis skills, carga progresiva, agrupación de decisiones, salidas compactas,
  contexto por aplicabilidad y reutilización dentro de evaluaciones inmutables.
- `v3_usage.fragments` puede duplicar en el diagnóstico textos ya entregados;
  `v3_cli` añade ese diagnóstico después de medir el cuerpo sin el sobre. La métrica
  declara ese límite, pero no mide el transporte completo.
- `author` puede asociar una tarea a todas las propuestas de la petición cuando
  no recibe una delimitación más precisa. La prosa no clasificada se conserva.
- La creación de tareas ejecutables exige propuesta validada. El recorrido individual
  prevé propuesta, plan y resultado como momentos de decisión, no una firma por comando.
- El contrato de continuidad no presume retención íntegra del contexto del host.
- La comparación de rendimiento general y la aceptación conversacional tienen límites
  documentados; no constituyen una referencia universal de consumo facturado.

La prueba sintética exploratoria realizada en esta conversación detectó volumen
diagnóstico significativo. No se conserva aquí como benchmark reproducible ni se
utiliza para fijar resultados de 4.0: V4-02 debe reproducir la referencia antes de
modificar producto. Tampoco se atribuye la queja de los usuarios a una causa única
sin sus versiones, configuración y observaciones reales.

**Hipótesis por comprobar:** menos transporte y operaciones del agente reducirán
consumo y tedio; delimitar documentación amortizará su coste en trabajos repetidos;
las optimizaciones del runtime reducirán espera donde exista un cuello de botella.
Ninguna hipótesis equivale a aceptación, ahorro demostrado o permiso de ejecución.

**Reporte incorporado en 0.3:** el equipo observó una espera prolongada en
`readiness(action=start)` con runtime fijado 3.4.2, aunque el plugin instalado era
3.4.3. La fuente 3.4.3 ya incorpora índices y reutilización de cálculos relacionados.
No hay reproducción exacta del consumidor ni comparación completa que acredite su
resolución. V4-02A comprueba la referencia y V4-17A exige el recorrido final S8;
la espera en una tarea de entrega no acredita un fallo de publicación remota.

## 3. Las seis mejoras y sus límites

Se conserva la numeración del análisis anterior; la antigua línea 6 no se convierte
en una séptima mejora. Su continuidad segura se integra en M2.

| Mejora | Resultado propuesto | Límite de diseño | Tareas principales |
|---|---|---|---|
| M1 · Transporte y diagnóstico — antigua 1 | Una copia del contenido operativo necesario; detalle técnico recuperable, conservación programática y actividad observable en esperas. | No esconder impedimentos, perder evidencia ni escribir silenciosamente por consultar. | V4-03, V4-04, V4-07A |
| M2 · Operaciones completas — antigua 2 | Preparar, continuar y registrar trabajo con menos coordinación del agente; reanudación e interrupción seguras. | No ejecutar decisiones humanas futuras, firmar por terceros ni atravesar una modificación material sin reevaluar. | V4-05, V4-06, V4-07, V4-07A, V4-17A |
| M3 · Alcance documental — antigua 3 | Relacionar obligaciones y porciones durante la autoría; reconciliar legado solo cuando compense. | No descartar por carpeta, similitud, falta de enlaces o presupuesto de tokens. | V4-08, V4-09 |
| M4 · Instrucciones por operación — antigua 4 | Reglas estructurales comprobadas por el núcleo e instrucciones pertinentes para el juicio del agente, disponibles con cada recorrido. | No retirar una regla sin identificar su destino; conservar explicación y excepciones necesarias. | V4-05A, V4-11 |
| M5 · Mantenimiento proporcional — antigua 5 | Hacer efectivos los recorridos existentes de corrección cubierta, cambio de acuerdo y capacidad nueva; añadir solo capacidades cuya carencia se demuestre. | No duplicar clasificación, ampliar permisos ni aprobar propuesta y plan juntos por defecto. | V4-10, integrado con M2/M4 |
| M6 · Cálculo medido — antigua 7 | Comprobar costes residuales, fijar latencia operativa y eliminar cálculo redundante demostrado dentro de fases estables. | No cachear autoridad entre comandos ni omitir comprobaciones frescas al aplicar. | V4-02A, V4-02B, V4-12, V4-13, V4-17A |

Las seis líneas se mantienen y son compatibles con G1–G10. No implican seis motores
nuevos: M5 puede resolverse mediante M2/M4 y M6 puede terminar sin cambios de código.
M1/M2/M4 aportan el primer recorrido V4-05A antes de ampliar M3/M5/M6. Un ahorro en
llamadas o texto no acredita por sí solo menor trabajo humano ni menor consumo total.
V4-02A/V4-02B son preparación temprana del caso comunicado, sin optimización de
producto. Si se reproduce un bloqueo operativo, descartar una variante M6 no
resuelve esa incidencia: V4-18 debe conservar el fallo y su decisión de alcance.

Fuera del alcance: entregar solo diferencias normativas suponiendo memoria del host;
resumir obligaciones para cumplir un máximo de tokens; aprobación conjunta indiscriminada
de SPEC/PLAN; cachés persistentes de permisos o evidencia como autoridad; reescritura
general del motor; nuevos agentes, MCP, hooks, conectores, servicios o entrypoints vacíos;
CI/CD del consumidor; publicación, instalación o migración automática.

## 4. Garantías que se mantienen

| ID | Invariante |
|---|---|
| G1 | Markdown del consumidor es canónico; índices, vistas, resúmenes y diagnóstico no deciden intención ni autoridad. |
| G2 | Se conservan obligaciones literales, condiciones, negaciones, tipos, reglas globales, contratos compartidos, dependencias entrantes y adjuntos aplicables. Incertidumbre implica ampliar o bloquear la porción afectada. |
| G3 | Propuesta, plan, autorización, implementación, verificación, integración y aceptación siguen diferenciados. Las decisiones nuevas se vinculan al contenido presentado y a autoridad vigente. |
| G4 | Alcance, persona, asignación, rama/base, sujeto, revocaciones y concurrencia observable se comprueban en los límites materiales; no se presume un bloqueo distribuido. |
| G5 | Sonar, Dependency-Check y demás comprobaciones conservan su política. Error, no aplicabilidad, no uso acordado y superación son distintos. `not-run` nunca equivale a `passed`. |
| G6 | Reintentos, recuperación y rollback conservan hechos, evidencia, autoría y cambios posteriores; no crean autorización retroactiva ni duplican un mismo efecto aplicado. |
| G7 | Consultar no muta el consumidor. Exportar/capturar tiene destino explícito y ciclo de vida. El diagnóstico no modifica bases semánticas de aprobación. |
| G8 | Mismo núcleo para Codex y Copilot, seis skills con objetivos e invocación implícita conservados. Una comprobación de paquete no demuestra uso real del host. |
| G9 | Instalar el plugin no actualiza el runtime fijado, migra consumidores ni renueva acuerdos. Plugin, método y formatos se versionan por separado. |
| G10 | No se editan `specs/canonical/` para acomodar implementación. Se preservan límites, tratamiento de datos no confiables y rechazo de rutas/materiales no admitidos. |

G1–G10 son restricciones de las seis mejoras; no se intercambian por ahorro.
La revisión técnica debe contrastarlas con los criterios AC de [VALIDATION.md](VALIDATION.md).

## 5. Propuesta técnica por frontera

### 5.1 Representación, captura y conservación

Reutilizar `v3_cli`, `v3_decision_presentation`, `v3_usage`, `usage_report` y
`usage_bundle`. Separar la representación para el agente del objeto íntegro usado
para diagnóstico. La primera incluye resultado, ámbito, impedimentos, siguiente
acción, contenido literal necesario y referencias recuperables; no repite ese
contenido dentro de la observación. `--details` y exportación conservan acceso completo.

Mantener una modalidad de salida compatible para consumidores existentes; introducir
una modalidad explícita para las skills actualizadas antes de cambiar defaults.
Esquemas y nombres de opciones se concretan en [CONTRACT.md](CONTRACT.md);
son diseño de V4-01 y no comandos disponibles hoy.

La captura técnica usa un destino local explícito de la ejecución, fuera del corpus
normativo. Conserva materiales necesarios para diagnosticar una fuente ya modificada;
un hash aislado no basta. El runtime transporta y conserva lotes en hitos ya
autorizados, sin exigir que el modelo reescriba sobres. Sin captura configurada se
declara el límite o se mantiene el transporte compatible, sin una escritura oculta.
Un problema del diagnóstico se distingue de un problema del contrato; la nueva vía
no puede silenciar corrupción de registros canónicos existentes.

V4-07A añade actividad observable mediante un canal optativo compatible, sin
contaminar stdout JSON. Debe distinguir actividad de porcentaje completado,
acotar su frecuencia/volumen y definir la interrupción de consultas, preparación
y aplicación con la recuperación existente. Interrumpir un proceso no ejecuta el
comando de negocio `cancel`. El contrato de esta ampliación se documenta antes
de implementarla y se contrasta con CONTRACT.md; no se añade un nuevo servicio.
La reacción es cooperativa en fases comprobadas. Se identifican límites de E/S y
llamadas no interrumpibles; no se promete aborto instantáneo ni ausencia de artefactos
técnicos. Cualquier efecto parcial y recuperación quedan explícitos.

### 5.2 Operaciones compuestas con límites explícitos

Tres capacidades propuestas, con interfaces concretadas en V4-01/CONTRACT.md:

1. **Preparar trabajo:** consulta que reúne estado, autorización, causas mínimas,
   intervenciones y contrato literal aplicable sobre una base coherente.
2. **Iniciar/reanudar:** registra solo las transiciones técnicas cubiertas. Recepción
   o revisión de encargo solo se agrupan si la respuesta y persona realmente las cubren.
3. **Registrar resultados:** consume evidencias observadas, conserva implementación,
   verificación y cierre como hechos distintos y aplica solo pasos cuyas condiciones
   estén acreditadas. No ejecuta ni simula una aceptación humana o un análisis externo.

Cada operación define efectos, precondiciones, parada, idempotencia y recuperación.
Usar el journal existente cuando el conjunto pueda materializarse atómicamente. Si
hay efectos separados, documentar qué queda aplicado y desde dónde se retoma; no
simular atomicidad de pruebas, ediciones o servicios externos. Cambiar contenido,
política, autoridad o base obliga a una nueva evaluación. Las operaciones individuales
permanecen disponibles para diagnóstico y compatibilidad.

La vista de reanudación se reconstruye desde hechos y fuentes: tarea, resultado,
pendientes, permisos vigentes y contenido necesario. No crea un nuevo resumen
canónico ni sustituye el contrato por diferencias. Nueva conversación, compactación
o duda de retención requieren recuperar contenido literal aplicable e identidad actual.

### 5.3 Alcance y mantenimiento

Reutilizar `v3_authoring`, `v3_scope`, `v3_context`, `v31_corrections` y las reglas
de aprobación existentes. Preparar relaciones de alcance junto con propuestas/tareas;
no añadir una pregunta por archivo. Toda exclusión requiere fundamento y cobertura
vigentes. Para prosa histórica, mantener revisión de gobierno por lote y medir coste
inicial y mantenimiento de esas declaraciones. Cambios invalidan únicamente lo
acreditadamente afectado; ante dependencias desconocidas se amplía el análisis.

M3 empieza por autoría nueva. La reconciliación de legado se ensaya con un lote
acotado y solo se amplía si el coste observado de clasificación y mantenimiento
se amortiza en los trabajos previstos con fundamento. Mantener la vía conservadora
sin clasificar masivamente. Comprobar expresamente qué cambios invalidan cada
declaración y su aprobación: no relajar la vigencia para preservar un ahorro.

| Clase | Recorrido propuesto |
|---|---|
| Defecto dentro de acuerdo y encargo vigentes | Reutilizar cobertura; conservar diferencia observada, causa y nuevas comprobaciones; escalar si cambian alcance o garantías. |
| Cambio de acuerdo existente | Presentar diferencia y contexto necesario, validar contenido afectado y después actualizar/aprobar plan y permiso afectados. |
| Nueva capacidad, impacto transversal o incertidumbre crítica | Recorrido completo aplicable; no usar el perfil breve para eludir decisiones. |
| Resultado rechazado, tarea cerrada o permiso caducado | Aplicar la reapertura/corrección y la autoridad actuales; no tratar aprobación histórica como permiso operativo. |

Clasificar no autoriza. La vista abreviada conserva todas las obligaciones nuevas y
el contexto suficiente; las decisiones anteriores solo se reutilizan si siguen vigentes.
Ni número de archivos ni tamaño del diff determinan por sí solos la clase.

La clasificación `defect`/`agreement-change`/`new-request` ya existe en 3.4.3.
V4-02 recoge los recorridos actuales y V4-10 documenta, para cada clase, antes/después:
acciones del agente, datos pedidos a la persona, registros reutilizados, decisiones
necesarias y trabajo eliminado. Si basta aplicar mejor una capacidad existente,
la entrega se realiza en operaciones/instrucciones M2/M4 y se referencia una sola vez.
Solo una carencia reproducida justifica cambiar el núcleo; no crear otro clasificador.

### 5.4 Instrucciones y cálculo

Mantener un núcleo común breve y un catálogo cerrado de instrucciones por operación.
Cada regla se asigna a validador, instrucción para juicio humano/agente o referencia
bajo demanda. Generar las rutas de ambos hosts desde la misma definición, sin un
segundo motor de política en prompts. No obligar a aprender la maquinaria interna.
La porción necesaria se entrega y observa en V4-05A; V4-11 completa las rutas de las
seis skills. No se aplaza toda adaptación conversacional hasta terminar el núcleo.

Perfilar las operaciones integradas antes de optimizar. Conservar evaluación
inmutable, límites de memoria y lecturas/verificaciones frescas en preparación y
aplicación. Una variante con regresión reproducida se descarta. Si no existe una
mejora demostrable, V4-13 puede cerrar con decisión motivada de no incorporar cambios;
no se presenta como rendimiento mejorado.
Evaluar beneficio absoluto en el recorrido, frecuencia observada y coste/riesgo de
mantenimiento, no un porcentaje fijo de una fase aislada. M6 tiene presupuesto acotado
y no es requisito del primer recorrido ni de construir la candidata principal.

## 6. Orden, hitos y responsabilidades

El detalle de las 23 tareas y sus dependencias está en [TASKS.md](TASKS.md).

| Hito | Resultado | Tareas de cierre |
|---|---|---|
| H0 | Plan 0.2 validado, ampliación 0.3 y revisión documental 0.4 solicitadas. Ejecución preparatoria autorizada de V4-01/V4-02 y después V4-02A/V4-02B. | V4-07A/V4-17A y el resto de implementación siguen sin autorización de ejecución. |
| H1 | Contratos, referencia, medición y presupuesto fijados antes de cambios de producto para el alcance actual Codex; Copilot conserva su canal aplazado al final. | V4-01, V4-02 |
| H1A | Referencia del incidente, fixture representativo y criterios S8 fijados antes de medir candidata y desarrollar su actividad/optimización; no reabre H1 ni bloquea H2 independiente. | V4-02A, V4-02B |
| H2 | Primer recorrido completo de tarea autorizada, paquete provisional y observación temprana de utilidad con M1, preparación M2 e instrucciones M4. | V4-03, V4-04, V4-05, V4-05A |
| H3 | Pareja S8 temprana y operaciones que registran cambios, continuidad, espera observable, alcance gradual, mantenimiento e instrucciones verificados. | V4-06 a V4-11, incluido V4-07A |
| HM | Perfil y disposición acotada de variantes; incorporación justificada o descarte sin cambios. No bloquea H2 ni construir H4. | V4-12, V4-13 |
| H4 | Compatibilidad, regresión y paquetes de desarrollo verificados. | V4-14 a V4-16 |
| H5 | Eficiencia, calidad, dos parejas S8 finales AB/BA y estado de 4.0 documentados. Percepción humana diferida. | V4-17, V4-17A, V4-18 |

La revisión 0.5 difiere la observación real de H2/AC-34 y aparta la incidencia de
aislamiento del host. Esa observación no bloquea el desarrollo técnico expresamente
autorizado; permanece pendiente para el dictamen final de host. Las dependencias de
V4-05A para desarrollar V4-06/V4-08 se limitan a su porción técnica verificada.
V4-08 y las demás tareas futuras conservan su necesidad de autorización posterior.

Los hitos agrupan resultados, no introducen confirmaciones por tarea. H2 completa
una corrección cubierta usando operaciones individuales vigentes para los pasos
que aún no se han agrupado. Su exigencia anterior de utilidad observada antes de
ampliar desarrollo queda sustituida por la decisión 0.5, sin declarar esa utilidad
demostrada ni dispensar su evaluación final. El paquete
provisional y la observación de H2 no dependen del cierre de V4-11/V4-16/V4-17.

Los criterios técnicos de V4-07/V4-11 y la referencia de V4-02 no requieren evidencia
de V4-17. La aceptación de continuidad, selección de instrucciones y comprensión
en host pertenece a V4-17. Verificación técnica y aceptación de producto conservan
estados separados. V4-18 registra ambas, incluidos pendientes; no los equipara.

M6 se evalúa dentro de su presupuesto. Una variante que no llegue al corte de la
candidata queda descartada de 4.0 con su motivo. Incorporarla cambia la revisión
y exige repetir las verificaciones, empaquetado y observaciones afectados; no se
reutiliza evidencia obsoleta. Un descarte motivado satisface el estudio M6 sin
acreditar aceleración. Las pruebas focales acompañan cada entrega.
La aceptación suplementaria S8 exige la mejora temporal ≥20 % fijada por la decisión
posterior del usuario y el contrato V4-02B. Un corte o fallo no acredita ese objetivo;
el ahorro mínimo M6 no lo sustituye.
No hay nuevas bolsas de horas o ejecuciones; la reserva S8 precede a optimizaciones
opcionales y no reduce las garantías ni las comparaciones de ambos hosts.

Roles propuestos: mantenimiento del núcleo, contexto/autoría, experiencia/skills,
distribución y revisión técnica; responsable del producto valida alcance y aceptación;
participantes de Codex/Copilot observan uso real. Personas, capacidad, fechas y duración
están pendientes. El grafo permite distribuir trabajo, pero este plan no crea agentes,
ramas ni worktrees ni presupone ejecución paralela.
Desde H1 salen dos ramas: V4-02 → V4-03 → H2 y V4-02 → V4-02A → V4-02B.
La segunda converge en V4-06 para la pareja S8 temprana; V4-07A se integra después
de captura y continuidad. V4-17A comprueba dos parejas finales AB/BA sobre V4-16.
Las pruebas focales acompañan V4-06/07A/14/15 y se reutilizan si siguen vigentes;
ninguna espera al resultado futuro V4-17A. Los parámetros S8 se congelan antes de
medir ese caso o diseñar su optimización/actividad, sin bloquear M1 independiente.
Los umbrales H2 del protocolo 1.0 no cambian.

## 7. Compatibilidad, distribución y reversibilidad

Destino de producto: **4.0.0**. Propuesta técnica inicial: mantener método 3.1.0 y
schema 3.1 si los cambios conservan su significado, y versionar aparte los formatos
operativos nuevos. V4-01 debe demostrarlo antes de tocar escritores. Si necesita una
regla o formato canónico incompatible, se presenta esa diferencia y se ajusta el plan;
la etiqueta 4.0 no autoriza una migración implícita.

Reutilizar distribución y validadores actuales. Codex y Copilot reciben el mismo
núcleo. Probar comandos individuales, salidas compatibles y operaciones nuevas;
mantener diagnóstico/recuperación de orígenes soportados. El ensayo principal de
actualización parte de consumidores 3.1 con runtime 3.4.3, incluidos trabajo abierto,
historia, diagnóstico y decisiones vigentes. No se promete escritura directa sobre
formatos históricos que la base ya no soporta.

Una actualización futura requiere preview explícito, respaldo recuperable, comprobación
de capacidades, continuidad y rollback. No se fuerza un runtime viejo sobre datos que
no puede leer. La recuperación se prueba también tras interrupción y con trabajo
posterior; no se restaura a costa de perderlo.

Preparar paquetes de desarrollo no equivale a publicar o instalar. La release estable
seguirá [la validación vigente](../../VALIDATION.md) sobre el commit limpio autorizado.
No se amplía su gate por añadir este estudio de eficiencia. Publicación, registro,
instalación y verificación en conversación nueva mantienen autorizaciones y evidencia
separadas. La futura gestión local utiliza `C:\AI-Workspace\extensions\bin\extensions.ps1`,
preserva identidades, pins, paquetes referenciados y recuperación según la política
central; este plan no registra paquetes, limpia históricos ni toca cachés oficiales.

**Windows y temporales:** conservar `path_utils`/`import_bootstrap` y la regresión
real `test_windows_long_paths`. V4-04/07A diseñan captura y recuperación sin crecimiento
repetido de rutas; V4-14/15/16 comprueban rutas cortas y largas (>260 caracteres),
TEMP/TMP profundo, espacios/Unicode, empaquetado, interrupción y limpieza del área
propia. La ruta corta de ensayo no demuestra compatibilidad con la larga. Mantener
comprobaciones de integridad, enlaces y contención; no exigir cambios globales de
Windows ni presentar una extracción parcial como correcta. Cobertura y coste se
concretan en [el complemento, sección 10](ADDENDUM-PERFORMANCE.md#10-windows-y-temporales-largos-regresión-obligatoria).

## 8. Decisiones y pendientes

| ID | Situación actual | Cuándo se resuelve |
|---|---|---|
| D1 | Revisión 0.5: Windows apartado, H2 pendiente, V4-06 técnicamente verificada con regresión de rendimiento abierta. | Continuación solicitada; saldo conciliado y cierre integral no financiado. Ver RESULTS-V4-06.md. |
| D2 | Diseño de salidas, captura, operaciones y compatibilidad concretado documentalmente. | CONTRACT.md; las pruebas de implementación/compatibilidad futuras siguen pendientes. |
| D3 | E1/E2/E3 conservados; utilidad H2, `delta_util`, ruido y ventanas fijados en protocolo 1.0, antes de candidata. | AC-33 cerrado técnicamente; percepción humana diferida, ahorro aún sin comparar. |
| D4 | Codex inicial, P01 habitual y Copilot al final. S1/S2 técnicos y viabilidad de contadores contrastados; históricos mixtos excluidos como denominador. Prueba humana retirada. | MEASUREMENT-PROTOCOL.md: nuevas parejas con ventana completa/configuración equivalente; no se piden fichas humanas. |
| D5 | Diseño V4-01 conserva método 3.1.0/schema 3.1 y separa formatos operativos externos. | CONTRACT.md; demostrar compatibilidad en implementación/actualización futuras. Si aparece incompatibilidad material, resolver antes del escritor afectado. |
| D6 | Máximo inicial de 12 h ampliado expresamente a 15 h; 48 ejecuciones completas y M6 dos variantes/cuatro horas se mantienen. Valoración humana diferida a uso real. | Saldo único conciliado en REVISION-0.5; no se financia automáticamente el resto de la release ni se reinicia la bolsa al apartar Windows. |
| D7 | Ruta de carga provisional y comprobación de versión/skills/runtime fijadas en protocolo 1.0. Activación candidata, integración, publicación e instalaciones reales no ejecutadas. | Revalidar la superficie del cliente y obtener autorización separada antes de carga/activación H2. Este cierre no instala ni acredita ambos hosts. |
| D8 | Las cuatro tareas se mantienen; revisión 0.4 corrige su encaje e incorpora Windows. | REVIEW-0.3.md; seis mejoras y techos intactos. Solo V4-02A/B autorizadas posteriormente. |
| D9 | Usuario fija ≥20 % de mejora temporal completa S8; resto de parámetros concretados en S8-PROTOCOL. | AC-39 preparatorio superado; protocolo congelado y referencia de preparación pública observada. Recorrido completo futuro, consulta/transiciones visibles, sin SLA absoluto adicional. |
| D10 | Tras V4-06: 13 cargos conocidos (7 históricos + 2 V4-05A + 4 S8 tempranos) + 2 H2 + 24 finales + 4 S8 finales + 2 contingencias = 45/48; no se certifica margen histórico adicional. | Se gastaron dos contingencias por fallo propio del arnés, conservando las muestras. Una serie adicional M6 de 12 no cabe; no reducir cobertura ni contingencia para hacerla caber. |
| D11 | Las cuatro tareas tienen cotas iniciales por 4 h; Windows reutilizado reserva 0,5 h de compatibilidad. No son estimaciones de finalización. | La cobertura histórica de entorno es parcial y las horas humanas desconocidas: viabilidad integral no acreditada. Registrar consumo/capacidad por bloque sin pedir nuevo cronometraje humano. |

El plan podrá autorizarse por completo o por una porción coherente. Se reutilizará
esa autorización sin preguntar por cada registro técnico. Un cambio material de
alcance, garantías o compatibilidad requerirá validar solo la parte afectada.

## 9. Cierre previsto

Se entregarán fuente y paquetes verificables, documentación de uso/actualización,
evidencia ligada a revisiones exactas y un informe con estados separados: calidad
técnica, garantías, compatibilidad, eficiencia, comprensión humana y publicación.
Un pendiente de host o de consumo facturado permanece pendiente; no se sustituye
por caracteres/4, tests estáticos o una aprobación de release.

Si V4-02 acredita que no hay métrica completa de tokens, se fija antes de desarrollar
el alcance aceptable de demostración: transporte y trabajo administrativo, con ahorro
total de tokens pendiente, o se resuelve primero la medición. Esa decisión es explícita
y no se presume aprobada en esta revisión. La decisión posterior registrada en
DECISION-TECHNICAL-SCOPE.md difiere la evaluación humana a uso real sostenido;
no se exige E5 para cerrar la fase técnica ni se declara superado. Se mantiene
la comparación técnica de seis ejecuciones primarias en Codex
(doce al completar ambos hosts) y ampliación limitada;
las garantías y la cobertura adversa no se reducen por agotar el presupuesto.

El estado actual de V4-01/V4-02 y sus decisiones pendientes está en RESULTS-H1.md.
Tras presentarlos, cualquier cambio del plugin requiere autorización posterior
expresa; no se extiende a V4-03 la autorización limitada recibida.
Ese informe, el progreso V4-02 y REVISION-0.3.json conservan el cierre histórico.
REVISION-0.4.json registra esta revisión sin convertir sus AC-37–AC-44 en superados ni modificar los
hashes del protocolo 1.0 o SCENARIOS.json. Un S8 fallido/inconcluso impide declarar
resuelto el bloqueo o aceptación técnica completa de esta ampliación; una eventual
release con reservas requiere decisión explícita y mantiene esos estados visibles.

Corrección posterior autorizada y verificada: [Git/Windows V4-05](RESULTS-V4-05-GIT-WINDOWS.md),
con condiciones de compatibilidad explícitas. La revisión incompleta anterior se
conserva como antecedente. El límite «V4-05A sin iniciar» era el de ese bloque;
la autorización posterior y el estado vigente están al principio de este plan.

Revisión posterior V4-05A: [dictamen y paquete vigentes](REVIEW-V4-05A.md).
Tres regresiones focales finales pasan, 14 observaciones auditadas por ID/contenido;
se conserva la evidencia anterior por identidad de scripts, sin repetir un S1 completo
ni Windows. Cero intentos completos adicionales; AC-34/H2 continúan pendientes y no
se instala el paquete ni se inicia V4-06.


Actualización H2 0.3: [conciliación temporal](TIME-RECONCILIATION.md) completada.
Se conserva calendario bruto y se corrige solo reposo profundo Windows acreditado:
cargo observado 10,411149 h; reservando 10 min de auditoría quedan 85,331034 min.
[H2 concreto](H2-CONCRETE-LOAD.md) propone reservar 45 min; margen común restante
40,331034 min. No acredita viabilidad integral o históricos externos. Se mantienen
las seis mejoras, toda la cobertura y 45/48 plazas conocidas/reservadas. Los planes
siguen sin aplicar; no hay instalación, H2 ejecutado o aceptación AC-34.


Resultado de ejecución autorizada H2: [inconcluso y recuperado](RESULTS-H2.md).
A: copia/registro de paquete y catálogo, instalación fallida; catálogo revertido.
B: no cargado. Credenciales temporales retiradas; configuración habitual intacta.
Cero casos y cero plazas nuevas; sin métricas comparables ni aceptación AC-34.
La reserva de 45 min es acumulada y no se reinicia para corregir la ruta de carga.

Plan Windows/H2 0.2 validado y ampliación +3 h autorizada: máximo global **15 h**. [Ejecución: corte W2, reparación local rechazada, H2 no ejecutado y recuperación con residual](RESULTS-WINDOWS-REPAIR-H2-03.md). AC-34 pendiente; no se modifica el plugin ni se inicia V4-06. El saldo no financia automáticamente el resto de la release.
