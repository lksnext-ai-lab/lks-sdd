# Plan de implementación: continuidad SPEC → PLAN/TASK → implementación

Fecha: 2026-09-23. Estado: plan de diseño previo a la implementación 2.3.0.
Se conserva para trazabilidad; la guía operativa y el changelog describen el
comportamiento entregado. Sus estados de tareas de abajo son la foto del plan
antes de implementarlo, no un tablero vivo de esta release.
Base revisada: LKS-SDD 2.2.0, commit `be89ba5420a19206ec2a222b131006f4017e958c`.

Fuente funcional: [especificación propuesta del método 2.1](../../../specs/proposed/spec-plan-task-2.1.md).
Fundamento: [revisión crítica](REVIEW.md), [seis sondas observadas](probe-results.json).

Este documento planifica cambios en el plugin. Sus IDs TASK-SPT identifican tareas
del plan de mantenimiento; no son TASKs ejecutadas ni autorizaciones de un proyecto
consumidor inicializado. Las fuentes de specs/canonical/ permanecen congeladas.

## 1. Alcance y decisiones de diseño propuestas

Se implementará el recorrido para cambios nuevos, trabajo ya previsto, ampliación
de tareas pendientes y corrección de trabajo cerrado. Incluye contrato documental,
runtime, seis skills, instrucciones de proyecto, compatibilidad, distribución,
guard independiente y documentación de uso.

Decisiones que concretan esta propuesta:

1. Reutilizar `change`/`PCH` para una petición material con su correspondencia a SPEC y trabajo. Las aclaraciones y reanudaciones no generan registros duplicados.
2. Derivar cobertura desde el cambio y la SPEC con granularidad de obligación. Incluir aceptación, pruebas, prosa normativa, interfaces y dependencias aplicables.
3. Utilizar una proyección normativa de planificación por porción, con reglas comunes protegidas y completitud global evaluada por separado.
4. Compartir el análisis entre los comandos existentes. Añadir como máximo una entrada de consulta `v2 change assess --id PCH-###`; author conserva la ruta de escritura por preview/apply. La sintaxis exacta se fija en TASK-SPT-001.
5. Mantener schema documental 2.0 y proponer método 2.1.0, con actualización explícita desde 2.0.0. P06 confirma que el runtime anterior ya rechaza ese método, evitando una migración general de formato. La versión del plugin se decide al preparar su release.
6. Mantener el guard estructural y añadir una comprobación estricta de cumplimiento del ciclo, con fuentes de confianza externas al candidato.
7. Mantener seis skills y distribuir la regla persistente mediante los bloques gestionados ya existentes. No añadir MCP, conectores, hooks, apps ni agentes ejecutables.

La activación de CI/protección de rama y la actualización de consumidores reales
son operaciones posteriores por proyecto. Se prepara su soporte y se prueba con
fixtures; no se modifica automáticamente ninguna infraestructura personal o externa.

## 2. Orden y dependencias

En la fecha de esta planificación, todas las tareas estaban **pendientes**. Los roles son responsabilidades propuestas;
no se asignan personas, fechas ni duraciones ficticias.

| Tarea | Entregable | Depende de | Rol propuesto |
|---|---|---|---|
| TASK-SPT-001 | Reglas del método 2.1 y compatibilidad ejecutable | — | Mantenimiento del contrato |
| TASK-SPT-002 | Petición y reconciliación documental atómica | 001 | Mantenimiento del runtime |
| TASK-SPT-003 | Cobertura desde SPEC hasta PLAN/TASK | 001, 002 | Mantenimiento del runtime |
| TASK-SPT-004 | Huellas de planificación y base de ejecución | 001, 003 | Mantenimiento del runtime |
| TASK-SPT-005 | Condiciones uniformes del ciclo y recuperación | 002, 003, 004 | Mantenimiento del runtime |
| TASK-SPT-006 | Enrutamiento de skills y continuidad del agente | 001, 002, 003 | Mantenimiento de experiencia/hosts |
| TASK-SPT-007 | Guard estricto y plantilla de integración | 003, 004, 005 | Mantenimiento de integración |
| TASK-SPT-008 | Actualización de método 2.0.0→2.1.0 y distribución | 001, 002, 003, 004, 005, 006 | Mantenimiento de distribución |
| TASK-SPT-009 | Regresión integrada y documentación consistente | 005, 006, 007, 008 | Revisión técnica |
| TASK-SPT-010 | Aceptación acotada en Codex y Copilot | 009, entorno de prueba preparado | Revisión de uso por host |
| TASK-SPT-011 | Preparación de release y adopción | 009; resultado de 010 declarado | Mantenimiento de releases |

La cadena estructural inicial es 001 → 002 → 003 → 004 → 005. Después de 003,
006 puede desarrollarse junto con 004/005 coordinando el contrato de salidas.
Tras 005 y 006, 007 y 008 son independientes salvo la interfaz del guard.
009 integra esas fronteras. No se calcula camino crítico temporal sin duraciones.

La modificación simultánea de `v2_cli.py`, esquemas, fixtures o del generador de
distribución requiere coordinación explícita de archivos; las fronteras anteriores
no autorizan escritores concurrentes sobre el mismo fichero.

## 3. Fichas de implementación

<a id="task-spt-001"></a>
### TASK-SPT-001 · Formalizar contrato y compatibilidad

Objetivo: convertir REQ-SPT-001..014 en estructuras y reglas inequívocas antes de
introducir nuevos writers. Precisar metadatos de petición, puntos materiales,
disposiciones de cobertura, relaciones tipadas, proyección de planificación y
versión de huellas. Separar estados derivados de decisiones persistidas.

Archivos previstos: `schemas/`, `scripts/v2_schema.py`, `scripts/v2_contract.py`,
`scripts/v2_cli.py`, `scripts/lks_sdd.py`, plantillas de define y fuentes propuestas
aplicables. El parser conserva schema 2.0; el contexto del proyecto selecciona
validaciones y writers según method_version. AUTH/EXEC/EVID registran la versión
de base de ejecución. No se cambia VERSION global ni se reinterpretan históricos.

Aceptación:

- Un registro PCH bien formado es válido; una cobertura declarada sin fuente o con tipos/IDs incorrectos falla.
- Schema 2.0 con método 2.0.0 y contrato 1.5 siguen legibles en su ruta; método 2.1.0 tiene reglas explícitas y el runtime anterior lo rechaza. Cambiar method_version manualmente no completa la actualización ni crea cobertura.
- Las reglas de confirmación documental y AUTH no se mezclan; un cambio draft no habilita ejecución.
- Están fijados el contrato de resultados y los motivos de bloqueo compartidos que consumirán 002–008.

Evidencia: fixtures mínimos válidos e inválidos y pruebas de compatibilidad. Riesgo
principal: mezclar reglas de métodos distintos; revisar consumidores internos de
METHOD, validadores, fingerprints y engine_hash antes de dar por cerrada la tarea.

<a id="task-spt-002"></a>
### TASK-SPT-002 · Registrar y reconciliar la petición

Objetivo: tener un origen versionado del cambio y una operación documental que
pueda actualizar SPEC, PLAN, TASK y PCH sin estados parcialmente aplicados.

Archivos previstos: módulo nuevo `scripts/v2_change_control.py`, `v2_authoring.py`,
`v2_storage.py` únicamente donde sea necesario, `v2_cli.py`, `v2_query.py`, plantillas
de define. Se reutilizan transacciones, snapshots y previews existentes.

Aceptación:

- Una consulta/assess no escribe. Reintentar o reanudar la misma petición no duplica PCH, features ni tareas.
- La escritura agrupa documentos afectados, preserva IDs/UID y ediciones ajenas y exige incrementar revisiones normativas.
- Puede guardarse una SPEC en borrador o sin planificación completa; el resultado identifica el trabajo pendiente y no habilita código.
- Cada punto material tiene una correspondencia revisable o un desconocido explícito. El runtime valida enlaces; no inventa su interpretación.
- Un fallo durante apply deja el conjunto recuperable mediante el journal; cambios desde el preview invalidan ese preview.

Evidencia: preview sin escritura, apply atómico, reintento idempotente y recuperación
ante interrupción con varios documentos. No se añaden escrituras automáticas a Jira.

<a id="task-spt-003"></a>
### TASK-SPT-003 · Derivar cobertura completa del ámbito

Objetivo: corregir P02/P03 calculando las obligaciones esperadas desde la petición
y SPEC y contrastándolas con planes y tareas. Compartir esa lógica con decompose
y readiness para que no puedan producir estados incompatibles.

Archivos previstos: `v2_change_control.py`, `v2_features.py`, `v2_lifecycle.py`,
`v2_quality.py`, `v2_contract.py` y `v2_guidance.py`.

Aceptación:

- Un FR/AC aplicable sin asignación aparece por ID/fuente y bloquea la porción afectada; no basta con que el PLAN omita ese ID.
- La aceptación y los tests tienen correspondencia explícita; varios contribuyentes pueden cubrir criterios distintos sin duplicar propiedad primaria.
- El trabajo extra sin petición/alcance acordado se detecta en la dirección inversa.
- Reutilizar cobertura verificada exige obligación/revisión, evidencia, sujeto y aplicabilidad compatibles. Done sin fundamento no se cuenta como satisfecho.
- Complete e incremental-authorized tienen resultados distintos y no permiten diferir dependencias necesarias de la porción elegida.
- Cambios compartidos revisan dependencias y consumidores afectados; el ámbito independiente conserva su estado. Una ausencia de enlaces críticos queda como desconocido.

Evidencia: regresiones P02/P03 y contraejemplos de duplicidad, parcialidad,
versiones futuras y dependencia transversal. El informe distingue cobertura
estructural y decisión semántica; no presenta el cálculo de IDs como comprensión
automática de cualquier petición humana.

<a id="task-spt-004"></a>
### TASK-SPT-004 · Proteger planificación y autoridad por alcance

Objetivo: corregir P01 conservando P05 y evitando invalidaciones ajenas al cambio.

Archivos previstos: `v2_contract.py`, `v2_lifecycle.py`, `v2_change_control.py`,
`v2_verification.py`, esquemas de AUTH/EXEC/EVID y salidas de contexto.

Aceptación:

- AUTH/EXEC registran la versión de algoritmo y huellas de SPEC y planificación aplicable; EVID liga la base con el sujeto técnico observado.
- Cambiar prosa normativa compartida, política, asignación, dependencia o integración aplicable invalida la autoridad anterior.
- Cambiar progreso, orden de tablero o una TASK independiente plenamente cubierta no invalida la porción por sí solo.
- La completitud del objetivo se comprueba aunque la proyección no cambie; un plan que deja de cumplir su política no sigue ejecutable.
- No se elimina prosa normativa de la huella ni se presume independiente un alcance ambiguo. La causa de incompatibilidad resulta comprensible.
- Evidencia histórica con algoritmo anterior sigue disponible para consulta y nunca se eleva a prueba de las obligaciones nuevas.

Evidencia: pruebas por pares de modificaciones relevantes/irrelevantes; equivalencia
entre context, AUTH, EXEC y verificación; rechazo explícito de huellas de otra versión.

<a id="task-spt-005"></a>
### TASK-SPT-005 · Aplicar condiciones a todo el ciclo

Objetivo: impedir que una ruta alternativa inicie, continúe o cierre trabajo sin
la reconciliación vigente, manteniendo las salidas de recuperación.

Archivos previstos: `v2_lifecycle.py`, `v2_controls.py`, `v2_preparation.py`,
`v2_verification.py`, `v2_authoring.py`, `v2_cli.py` y dispatcher `lks_sdd.py`.

Aceptación:

- Authorize/prepare/start/resume y los alias públicos reutilizan el mismo análisis y no habilitan una petición incompleta.
- TASK pendiente cubierta se reutiliza; ampliación material cambia su base; nueva obligación tras done crea otra tarea. El writer genérico no evita estas reglas.
- Problem/correct permite corregir el contrato original y conserva EVID/cierres anteriores; alcance nuevo no se disfraza como corrección.
- Una nueva obligación durante ejecución bloquea la porción y conserva código/checkpoint. Se respeta la indivisibilidad de un EXEC multitarea existente; no se promete dividirlo automáticamente.
- Pausa, registro de problema, cancelación y replanificación siguen disponibles cuando la base esté obsoleta o la cobertura sea insuficiente.
- Los cambios previos en el árbol de trabajo se inventarían con procedencia y alcance, sin borrarlos ni presentarlos como cambios posteriores autorizados.
- Verify y close exigen la misma base vigente; nunca completan tareas por la sola existencia de documentación, tests declarados o código escrito.

Evidencia: recorrido SPEC→PLAN/TASK→AUTH→EXEC→EVID en fixtures, intentos de eludirlo
por writers/alias y pruebas de recuperación. Se conservan las políticas existentes
de reservas, dependencias y aceptación humana; ninguna reserva dispensa cobertura
normativa o autoridad inválida.

<a id="task-spt-006"></a>
### TASK-SPT-006 · Conducir peticiones y reanudaciones en las seis skills

Objetivo: que «añade este dato», «corrige este cálculo» o «implementa el cambio»
activen la reconciliación adecuada aunque ya haya una feature o una TASK.

Archivos previstos: las seis `skills/lks-sdd-*/SKILL.md`, referencias afectadas,
`docs/V2-WORKFLOWS.md`, `docs/PROJECT-QUERY.md`, `v2_query.py`, `v2_guidance.py` y
el bloque common de `scripts/dual_distribution.py`.

Aceptación:

- Define es responsable de reconciliación y planificación; implement comprueba la entrada y deriva cuando falta cobertura; help/readiness no escriben por una consulta.
- Las descripciones mantienen activación implícita sin solapamientos de responsabilidad. No se crea una séptima skill.
- El bloque gestionado del proyecto cubre toda modificación relevante, no solo solicitudes que mencionen LKS-SDD, y remite al runtime fijado.
- El cierre de SPEC informa y conduce a PLAN/TASK. Si falta una decisión, presenta la descomposición disponible y la pregunta concreta; no oculta la planificación pendiente.
- Una sesión nueva puede localizar petición, SPEC, PLAN/TASK, AUTH y checkpoint. Detecta cambios de clon/rama/runtime y no se apoya en un chat anterior.
- Se reutilizan aprobaciones vigentes; el usuario ve un resumen material agrupado y no una secuencia de hashes o confirmaciones administrativas.

Evidencia: verificación estática de distribución y ensayos por host de TASK-SPT-010.
Una prueba que busca frases en SKILL.md solo acredita su presencia, no activación
o cumplimiento real del modelo.

<a id="task-spt-007"></a>
### TASK-SPT-007 · Comprobar cumplimiento antes de integrar

Objetivo: añadir el control estricto que falta en P04, conservando la semántica del
guard estructural. La garantía es rechazar integración incumplidora cuando el
sistema externo lo exige; no bloquear físicamente cualquier edición local.

Archivos previstos: `scripts/v2_integration_guard.py`, `v2_cli.py`,
`docs/V2-GUARDRAILS.md`, plantilla de CI bajo `templates/` y fixtures de integración.

Aceptación:

- El modo estricto rechaza ausencia/incompatibilidad de SPEC, PCH, PLAN/TASK, cobertura, AUTH/EXEC o base de ejecución.
- El patch completo tiene atribución a tareas y ámbito; ninguna selección parcial oculta otros archivos modificados. Solapamientos requieren responsabilidad explícita.
- Se distinguen tres entradas: base real de código, contrato/autoridad aprobados y candidato. El verificador se selecciona desde una referencia externa fiable.
- La evolución documental legítima puede aprobarse sin integrar antes el código: el sistema externo aporta el contrato aprobado exacto. Un recibo presente solo en el candidato no crea confianza.
- Cambios de tests/gates/dependencias/controles exigen la revisión independiente ya prevista; un candidato no puede elegir otro verificador o rebajar la política.
- El informe declara checks realizados, base, sujetos y límites. No llama verified a un resultado estructural ni afirma autenticar roles o demostrar cronología histórica.
- La plantilla no publica, despliega ni modifica permisos; su uso se valida en repositorios sintéticos y su activación real se documenta como paso separado.

Evidencia: P04 y casos de omisión, manipulación de la base, contratos nuevos
legítimos, múltiples TASKs y rutas compartidas. Riesgo: bucle de aprobación si se
confunden base de código y contrato aprobado; probar expresamente esa separación.

<a id="task-spt-008"></a>
### TASK-SPT-008 · Actualizar método y distribuir sin perder historia

Objetivo: introducir método 2.1.0 manteniendo schema 2.0 en consumidores y paquetes
de ambos hosts, sin interpretar el histórico como nuevas decisiones ni permitir
que un runtime anterior ignore los controles.

Archivos previstos: `v2_migration.py`, `v2_storage.py` donde corresponda,
`v2_retention.py`, `v2_schema.py`, `dual_distribution.py`, `distribution/install.py`,
manifest/lock validators, plantillas, `docs/V2-MIGRATION.md`, `docs/COMPATIBILITY.md`.

Aceptación:

- Diagnóstico del método 2.0.0→2.1.0 es de solo lectura; preview identifica archivos afectados, autoridad obsoleta, pendientes y ejecuciones activas, sin reescritura general de encabezados.
- La actualización conserva IDs/UID, snapshots, assets, EVID y personalizaciones; no crea confirmaciones ni cobertura ficticias para completar los nuevos requisitos.
- Ejecuciones activas exigen resolución explícita antes del corte; interrupción y rollback no borran cambios posteriores ni reactivan AUTH obsoletas.
- El runtime anterior rechaza método 2.1.0 y el dispatcher nuevo impide usar reglas anteriores para eludirlo. Los consumidores fijados en 1.5 o método 2.0.0 siguen con su ruta documentada hasta actualización explícita.
- Los paquetes Codex/Copilot y el setup llevan el mismo contrato y análisis, con instrucciones específicas del host y lock íntegro que declara schema y método compatibles.
- Los bloques de instrucciones ajenos se conservan. Una edición local del bloque gestionado produce el conflicto previsto por el instalador, no un overwrite silencioso.
- No se instala el paquete en el perfil personal, caché ni proyecto real como parte del test.

Evidencia: fixtures de versiones soportadas, actualización interrumpida, instalación
offline en carpetas temporales, comprobación de hashes y regresión de rutas Windows.

<a id="task-spt-009"></a>
### TASK-SPT-009 · Integrar pruebas y documentación de la capacidad

Objetivo: verificar conjuntamente el recorrido y los límites, no solo módulos
aislados. Reconciliar las guías que describen esta capacidad con el contrato nuevo.

Archivos previstos: tests mantenidos de planificación, workflows, task management,
ejecución, verificación, distribución y migración; `docs/V2-AUTHORING.md`,
`V2-WORKFLOWS.md`, `V2-GUARDRAILS.md`, `V2-HOST-ACCEPTANCE.md`, README, STATUS,
COMPATIBILITY y las afirmaciones afectadas de GOVERNANCE.md.

Aceptación:

- Los casos de la matriz tienen resultado explícito y evidencia suficiente; los de host pendientes no aparecen como aprobados por simulación.
- Las regresiones de P01–P06 se incorporan a módulos mantenidos con contraejemplos de no bloqueo del trabajo independiente.
- Un mismo fixture obtiene estados coherentes en change assess, decompose, readiness, start/resume y guard estricto.
- La documentación distingue corrección/evolución, completo/parcial, runtime/política externa y formato/método/versión del plugin.
- Se resuelve la contradicción de las afirmaciones de gobierno afectadas, manteniendo las fuentes canónicas históricas y su vigencia explícita.
- Se aplica `docs/VALIDATION.md`; no se añade una campaña amplia ni una nueva condición de publicación de forma implícita.

Evidencia: informe breve de regresión, diff revisado y validación contractual.
Una condición temporal de tests no se utiliza para debilitar el contrato real.

<a id="task-spt-010"></a>
### TASK-SPT-010 · Observar el recorrido real por host

Objetivo: comprobar precisamente la activación y continuidad que no prueban las
sondas de Python. Usar entornos de prueba y proyectos sintéticos autorizados.

Entregable: registro acotado dentro del protocolo de aceptación existente, con
versión de host/modelo/plugin/runtime, petición, fuentes consultadas, primera
escritura de código, resultado y límites. No guardar chats completos ni datos reales.

Aceptación:

- Ejecutar H-SPT-01..06 por separado en Codex y Copilot. Conservar fallos y repetir solo los casos afectados por su corrección.
- Respetar la preparación y participación del protocolo de host vigente. Esta evidencia acredita solo la capacidad evaluada; no cierra automáticamente los demás recorridos del protocolo.
- Una modificación genérica queda trazada antes de la primera escritura de aplicación; una consulta no produce escrituras.
- Una segunda conversación retoma archivos y autoridad vigente, detectando un worktree/runtime distinto.
- Se prueba la reducción de preguntas repetidas cuando ya hay decisiones confirmadas.
- Un host no disponible queda not-run/blocked con causa. El resultado de un host no acredita el otro ni una prueba unitaria acredita ambos.

Dependencia externa: disponibilidad y preparación autorizada de cada host. Su
ausencia no impide completar código y pruebas locales, pero impide afirmar que el
comportamiento conversacional de ese host ha quedado demostrado.

<a id="task-spt-011"></a>
### TASK-SPT-011 · Preparar entrega y actualización controlada

Objetivo: preparar el cambio para la política vigente de release y su adopción
por proyectos, con estados reales y límites visibles.

Entregables: changelog de la versión elegida, notas de incompatibilidad/conversión,
lista de archivos y paquetes esperados, resultados de regresión y protocolo de
actualización/rollback por consumidor. La instalación no equivale a activación.

Aceptación:

- El informe distingue implementación local, validación técnica, uso real por host, publicación y activación en consumidores.
- Se conserva la puerta técnica de release vigente. Las comprobaciones nuevas se incorporan al humo/regresión adecuados por su riesgo, sin restaurar una batería histórica indiscriminada.
- Preparar una versión no se confunde con aprobarla; commit, push, publicación e instalación siguen requiriendo la autorización separada definida en AGENTS.md.
- Los consumidores con contratos/métodos anteriores no se declaran protegidos por método 2.1.0 antes de su actualización, runtime correcto y activación verificable.
- Una release técnica con host not-run informa ese límite; para cerrar el objetivo de robustez conversacional de un host se exige su evidencia real.

## 4. Matriz de comprobaciones

Todos estos resultados futuros están **not-run**. P01–P06 son evidencia del
comportamiento actual y no deben contarse como aceptación de la corrección.

| Caso | Resultado que debe observarse | Tarea responsable |
|---|---|---|
| C01 | Consulta/readiness sin escrituras y sin nueva petición | 002, 006 |
| C02 | Petición genérica de cambio identificada y vinculada a SPEC/PLAN/TASK antes del código | 002, 006, 010 |
| C03 | Petición ya cubierta reutiliza TASK y aprobación vigentes sin duplicados | 002, 003, 005 |
| C04 | Nuevo FR aplicable omitido por el PLAN bloquea; P02 deja de ser ready | 003 |
| C05 | TASK con aceptación o tests de una obligación incompletos bloquea; P03 queda cubierto correctamente | 003 |
| C06 | Cobertura por varios contribuyentes es válida solo con límites y propiedad primaria claros | 003 |
| C07 | Cambio normativo del PLAN invalida la AUTH afectada; regresión P01 | 004 |
| C08 | Progreso y TASK independiente plenamente cubierta no invalidan por sí solos | 004 |
| C09 | Cambio de SPEC/TASK mantiene la protección actual contra AUTH obsoleta; P05 | 004, 005 |
| C10 | Alcance nuevo sobre done crea nueva TASK; writer genérico no reescribe el resultado anterior | 005 |
| C11 | Defecto del contrato original permite problem/correct con historia y EVID conservadas | 005 |
| C12 | Cambio durante EXEC bloquea/replanifica y deja disponibles pausa, problema y cancelación | 005 |
| C13 | Cambio de prosa normativa sin nuevas filas/IDs invalida cuando afecta al alcance | 003, 004 |
| C14 | Regla/interface compartida revisa consumidores; ausencia crítica de enlaces no significa irrelevancia | 003 |
| C15 | Política incremental conserva pendientes y no difiere precondiciones de la porción ejecutada | 003, 005 |
| C16 | Trabajo no solicitado o patch parcialmente atribuido se rechaza | 003, 007 |
| C17 | Guard estricto rechaza código sin AUTH/EXEC; P04 conserva su significado en modo estructural | 007 |
| C18 | Código previo o cambios ajenos se preservan y no se convierten en trabajo previamente autorizado | 005, 007 |
| C19 | Candidato no elige base/verificador ni se autoaprueba cambios de tests/gates/contrato | 007 |
| C20 | Runtime antiguo rechaza método 2.1.0; ningún alias/writer ni rebaja de method_version/lock elude la política del contrato aprobado | 001, 005, 008 |
| C21 | Actualización de método, interrupción y rollback conservan fuentes, IDs, evidencia y modificaciones posteriores | 008 |
| C22 | Otro hilo/worktree relee estado y detecta autoridad/runtime obsoletos | 006, 008, 010 |
| C23 | Cambios entre preview y apply y conflictos entre clones se detectan sin escrituras parciales | 002, 005, 008 |
| C24 | Evidencia obsoleta/ausente no se reutiliza como cobertura de una obligación nueva | 003, 004, 005 |
| C25 | Borrador futuro independiente no bloquea; dependencia o regla vigente afectada sí | 003, 004 |
| C26 | Upgrade de instrucciones conserva texto ajeno y detecta colisión del bloque gestionado | 006, 008 |
| C27 | Recorrido integrado cumple SPEC→PLAN/TASK→AUTH→EXEC→EVID sin inflar estados | 009 |

Casos de host para completar TASK-SPT-010:

| Caso | Petición/recorrido | Observación |
|---|---|---|
| H-SPT-01 | «Añade este dato al listado» sobre una feature existente | Reconciliación funcional y tareas antes de tocar aplicación |
| H-SPT-02 | «Corrige el cálculo» con TASK original done | Distingue defecto del contrato original y evolución |
| H-SPT-03 | «Escribe las especificaciones de este cambio» | SPEC y estado de planificación visibles; propone la descomposición disponible sin implementar |
| H-SPT-04 | «Implementa lo acordado» con plan incompleto | Identifica huecos y conduce a completarlos; no empieza por código |
| H-SPT-05 | Nuevo hilo, mismo proyecto, trabajo ya autorizado | Relee estado persistido y reutiliza decisiones válidas; detecta clone/runtime distinto |
| H-SPT-06 | Consulta seguida de modificación y una ampliación durante ejecución | Lectura inicial, cambio trazado y replanificación solo del ámbito afectado |

## 5. Cobertura de la especificación por tareas

| Requisitos | Tarea primaria | Contribuyentes | Casos |
|---|---|---|---|
| REQ-SPT-001, REQ-SPT-010, REQ-SPT-014 | 006 | 002, 005, 008, 010 | C01–C03, C22, C26, H-SPT-01..06 |
| REQ-SPT-002 | 002 | 001, 006 | C01–C03, C23 |
| REQ-SPT-003, REQ-SPT-004, REQ-SPT-006, REQ-SPT-013 | 003 | 001, 004, 005 | C04–C06, C13–C16, C24–C25 |
| REQ-SPT-005, REQ-SPT-008, REQ-SPT-009 | 005 | 001, 002, 007 | C09–C12, C18, C20, C23–C24 |
| REQ-SPT-007 | 004 | 001, 003, 005 | C07–C09, C13, C24–C25 |
| REQ-SPT-011 | 007 | 003, 004, 005 | C16–C19 |
| REQ-SPT-012 | 008 | 001, 004, 005 | C20–C23, C26 |
| REQ-SPT-015 | 009 | 010, 011 | C01–C27 y estados separados de H-SPT-01..06 |

001 fija los contratos comunes; 009 tiene la responsabilidad de integración y
verificación conjunta. Las tareas 010 y 011 acreditan resultados de uso y entrega
distintos y no se declaran completas por cerrar 009.

## 6. Validación y criterios de cierre

En cada tarea se ejecutan las regresiones que prueban sus cambios y riesgos
concretos. La validación de PR definida en docs/VALIDATION.md es:

```powershell
python -B -X utf8 scripts/validate_plugin_contract.py .
git diff --check
```

009 ejecuta la regresión integrada pertinente. Los checks de release se ejecutan
en el momento previsto por docs/VALIDATION.md, sobre el commit y autorización de
release correspondientes; este plan no declara ese estado ni los ejecuta ahora.

Se puede informar «implementación y regresión local completadas» tras 009.
«Comportamiento observado en Codex/Copilot» requiere el resultado de 010 en cada
host. «Publicado» e «instalado/activo» requieren operaciones y evidencia posteriores.
El cierre de esta propuesta de robustez no debe ocultar un recorrido de host fallido.

## 7. Riesgos y decisiones externas pendientes

| Riesgo | Respuesta prevista |
|---|---|
| Interpretación incompleta de una petición pese a enlaces válidos | Resumen de impacto y revisión de correspondencia; controles deterministas no sustituyen suficiencia semántica |
| Invalidación masiva por un PLAN compartido | Proyección normativa por alcance y pares de pruebas de cambios relevantes/independientes |
| Nueva política que un runtime viejo ignore | Método 2.1.0 rechazado por lectores anteriores y actualización explícita |
| Bloqueo que impida recuperar una ejecución | Rutas de pausa/problema/cancelación/replanificación disponibles y probadas |
| Fricción por confirmaciones repetidas | Reutilización de decisiones/autoridad vigente y un resumen material cuando haya cambios |
| CI que confíe en su propio candidato | Runtime y contrato aprobado seleccionados externamente, separados de la base de código |
| Historia reescrita al ampliar tareas cerradas o migrar | Nuevas TASKs para nuevo alcance y conservación de resultados, snapshots y EVID |
| Prometer uso real desde tests de texto o paquetes | Casos de host con not-run explícito hasta su observación |

Para ejecutar el núcleo 001–009, las decisiones técnicas están explicitadas en la
especificación propuesta. Quedan por asignar personas y decidir la versión de
release. Para 010 se necesitan hosts de prueba disponibles y autorización para
prepararlos. Cada adopción real debe elegir proyecto, runtime, base de confianza,
repositorio y política de integración. Ninguno de esos datos se inventa en este plan.
