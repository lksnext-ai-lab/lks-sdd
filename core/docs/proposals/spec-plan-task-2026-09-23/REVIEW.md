# Revisión crítica: continuidad SPEC → PLAN/TASK → implementación

Fecha: 2026-09-23. Base inspeccionada: plugin 2.2.0, commit
`be89ba5420a19206ec2a222b131006f4017e958c`.

Estado: revisión y propuesta de evolución. La petición del usuario confirma el
objetivo funcional; este documento no declara implementadas ni aprobadas las
decisiones técnicas propuestas.

Entregables relacionados:

- [Especificación propuesta](../../../specs/proposed/spec-plan-task-2.1.md).
- [Plan de implementación y tareas](PLAN.md).
- [Resultados de las sondas](probe-results.json) y [reproductor](probe.py).

## 1. Necesidad confirmada y alcance de la revisión

El usuario pide que cualquier implementación se apoye en la especificación y
quede incluida en el plan y las tareas, también cuando modifica una funcionalidad
que ya tiene trabajo planificado. El agente debe conducir ese recorrido sin que
la persona tenga que recordar los nombres de las skills en cada petición.

Se revisaron el runtime, las seis skills, las instrucciones que distribuye el
setup, el contrato documental y el guard de integración. No se han inspeccionado
los dos hilos consumidores del incidente; por tanto, sus causas concretas siguen
sin confirmar. Los casos siguientes reproducen límites del runtime actual.

## 2. Hallazgos observados

Las seis sondas usan proyectos temporales sintéticos creados con los helpers
existentes. No invocan modelos, aplicaciones consumidoras, contenedores ni CI.

| Caso | Observación reproducida | Implicación y límite |
|---|---|---|
| P01 | Se cambia la prosa normativa y la revisión de PLAN-001. El contexto conserva su huella, planning devuelve ready y la AUTH anterior sigue authorized. | La autoridad actual no detecta ese cambio del PLAN. No se ha probado que cualquier cambio de planificación pase: cobertura, política y dependencias sí tienen comprobaciones propias. |
| P02 | Se enlaza FR-002 y AC-002 desde una funcionalidad confirmada sin incorporarlos al PLAN ni a la TASK. El contexto contiene FR-002, pero planning devuelve complete/ready y decompose devuelve covered. | La cobertura se calcula respecto al PLAN declarado, que puede omitir parte del cambio. La AUTH anterior sí queda obsoleta por el cambio de especificación; el hueco persiste en la nueva evaluación de readiness. |
| P03 | FR-001 tiene AC-001 y AC-002; TASK-001 solo declara AC-001. Planning sigue ready y decompose covered. | Asignar el ID de un requisito no acredita la asignación de toda su aceptación. Las etiquetas positive/negative/regression de un test tampoco prueban esa correspondencia. |
| P04 | Se modifica un archivo dentro de src/** entre dos copias válidas, sin AUTH ni EXEC. Guard devuelve structurally-within-scope. | Es el límite documentado del guard estructural. Utilizarlo como único control de cumplimiento del ciclo sería insuficiente. No equivale a un fallo de una garantía de autorización que ese comando no declara. |
| P05 | Se cambia la prosa normativa y revisión de la TASK. La AUTH anterior queda bloqueada. | Existe protección útil que debe conservarse; el rediseño debe completar sus entradas y evitar regresiones. |
| P06 | Una marca opcional execution_policy no cambia readiness. Cambiar method_version de 2.0.0 a 2.1.0 manteniendo schema_version 2.0 hace que el runtime actual rechace el proyecto. | Ya existe una frontera estricta de compatibilidad por método. Permite introducir las reglas nuevas sin cambiar todos los encabezados y formatos documentales. |

Fuentes de implementación:

- [planning](../../../scripts/v2_lifecycle.py): calcula requested desde PLAN.requirements y compara la unión de requisitos atribuidos a sus tareas.
- [task_requirements y decomposition](../../../scripts/v2_features.py): una referencia directa de la TASK al requisito cuenta como cobertura; la alternativa por aceptación exige el conjunto completo.
- [execution_context](../../../scripts/v2_contract.py): recorre relaciones normativas; plan/increment/release aparecen como relaciones administrativas, sin recorrer el contenido del PLAN.
- [author](../../../scripts/v2_authoring.py): permite evolucionar Markdown e incrementa revisiones; no exige reconciliar en esa escritura todos los planes afectados.
- [guard](../../../scripts/v2_integration_guard.py): compara contexto, rutas y cambios sensibles; no requiere AUTH/EXEC.
- [setup de instrucciones](../../../scripts/dual_distribution.py): ya escribe bloques gestionados en AGENTS.md y en instrucciones Copilot. Es la superficie adecuada para hacer persistente el protocolo entre conversaciones, conservando las instrucciones ajenas.

## 3. Correcciones a la propuesta inicial

### 3.1 El universo de cobertura necesita una fuente independiente del PLAN

Comprobar PLAN contra TASK solo demuestra consistencia entre dos listas que
pueden estar incompletas. La entrada debe ser la petición reconciliada con la
SPEC y su alcance confirmado. Desde ahí se derivan obligaciones y se busca su
asignación, con huecos visibles. Una máquina no puede demostrar que una frase
humana se interpretó correctamente solo porque sus IDs estén conectados.

La revisión debe incluir prosa normativa, criterios, excepciones, pruebas,
interfaces y reglas compartidas. No basta con contar requisitos. El resultado
debe distinguir cobertura estructural, suficiencia semántica revisada y evidencia.

### 3.2 No corresponde exigir el backlog entero para cada cambio

Un proyecto puede tener documentación parcial, funcionalidades futuras y varios
planes. El análisis delimita la petición, su versión/entorno objetivo, sus
dependencias y los consumidores afectados por cambios compartidos. No convierte
la falta de relación en prueba de irrelevancia: conserva dudas y exige resolver
las críticas del ámbito. Una tarea ajena no debe bloquearse por un borrador
independiente; una dependencia realmente afectada sí.

La planificación incremental permite diferir alcance de forma explícita. No
permite ejecutar una TASK con criterios propios sin cubrir ni presentar una
petición parcialmente planificada como completa.

### 3.3 Una tarea cerrada exige distinguir corrección y alcance nuevo

La regla anterior «si está cerrada, crear siempre otra tarea» era demasiado
general. La [extensión canónica 1.3](../../../specs/canonical/LKS-SDD_extension_planificacion_continuidad_v1.3.md)
ya permite reabrir una tarea cuando falla el contrato original o su definición
de terminado. El [flujo correct](../../../scripts/v2_controls.py) materializa esa
distinción.

Un nuevo requisito crea trabajo nuevo. Un defecto del mismo contrato usa
problem/correct, conserva evidencia e historia y exige nueva verificación. Una
tarea pendiente puede ampliarse; una tarea en ejecución necesita reconciliar su
base antes de continuar. No se debe editar una TASK done para que parezca que
una evidencia antigua cubrió una obligación posterior.

### 3.4 Incluir todo el PLAN en todas las huellas sería demasiado amplio

Hay que proteger las decisiones normativas del PLAN que gobiernan la ejecución.
Hashear indiscriminadamente todo el tablero también invalidaría permisos al
cambiar el progreso o una tarea independiente.

La propuesta usa una proyección de planificación por alcance: propósito y reglas
compartidas, política, asignaciones del cambio, límites de las TASKs seleccionadas,
dependencias y obligaciones de integración. La prosa normativa común se incluye
siempre. Las reglas particulares deben tener alcance explícito para poder
excluirlas de otra porción. Un alcance ambiguo se resuelve o bloquea; no se elimina
texto del hash por conveniencia. La completitud del plan se vuelve a comprobar
independientemente de la huella de la porción.

### 3.5 La continuidad necesita estado versionado, no memoria de conversación

La instalación personal hace disponibles las skills. El setup del consumidor
puede dejar una regla persistente en su AGENTS.md que enrute toda modificación
del proyecto por este protocolo. Una sesión nueva relee ese estado, el runtime
fijado, la SPEC, el cambio activo y sus tareas. No se modifica el AGENTS global
personal ni se añaden una séptima skill, hooks, MCP o agentes ejecutables.

Las descripciones de skills ayudan a activar la ruta correcta. El preflight de
implementación vuelve a comprobarla aunque la activación inicial haya sido errónea.
Una consulta sigue siendo de solo lectura. El agente prepara un plan completo o
explica la decisión concreta pendiente, sin terminar silenciosamente tras la SPEC.

### 3.6 Trazabilidad local y control externo tienen garantías diferentes

Un modo estricto del guard puede comprobar el contrato, la cobertura, la autoridad,
la ejecución y el diff frente a una referencia independiente. Su integración con
la protección de rama puede impedir aceptar un cambio incumplidor.

Con herramientas generales de escritura disponibles, el plugin skills-only no
impide físicamente editar un archivo fuera de la CLI. Tampoco un archivo AUTH,
una fecha declarada o un hash local autentican a quien aprobó ni prueban que la
SPEC se escribió antes del código. La revisión externa debe conocer este límite.
La propuesta no promete correspondencia semántica perfecta entre cualquier diff
y lenguaje natural.

Código ya modificado al empezar se registra como hecho previo y se reconcilia.
El runtime no lo absorbe en una nueva baseline presentándolo como ejecución
previamente autorizada. Una reconciliación posterior no altera la cronología.

### 3.7 La compatibilidad debe fallar de forma visible

Los lectores 2.0 actuales aceptan metadatos adicionales. Añadir únicamente un
campo opcional de política permitiría que un runtime antiguo lo ignorase. Sin
embargo, el schema actual exige method_version 2.0.0; P06 confirma que otro método
ya produce rechazo. Tras comparar ambas alternativas, se propone **mantener
schema 2.0 y actualizar explícitamente el método a 2.1.0**.

El cambio añade validaciones según el método y reutiliza tipos, relaciones y
metadatos extensibles actuales. Evita una migración general de formato que no
aporta protección adicional para este alcance. Las reglas 2.1.0 no se aplican
silenciosamente a los documentos históricos de método 2.0.0. Si posteriormente
se necesitase otro formato o tipo incompatible, requeriría otra propuesta.

La transición de método preserva fuentes y evidencia, deja cobertura desconocida
donde falte y no convierte AUTH antiguas en autorizaciones nuevas. El lock debe
identificar también el método y el runtime que lo soporta. Los consumidores
fijados en contratos anteriores conservan su ruta hasta actualización autorizada;
no se les atribuye la nueva garantía. Esta elección corrige la primera alternativa
de crear schema 2.1 para este cambio y mantiene separada la versión del plugin.

### 3.8 Validación técnica y experiencia de host deben tener evidencia propia

Las sondas no prueban activación implícita ni comportamiento entre conversaciones.
El [protocolo de aceptación por host](../../V2-HOST-ACCEPTANCE.md) necesita casos
de modificación genérica, ampliación de TASK, corrección de trabajo cerrado y
reanudación en otro hilo. Su estado permanece not-run hasta ejecutarlos.

La [política de validación vigente](../../VALIDATION.md) mantiene una puerta de
release pequeña y excluye una batería conversacional permanente. La propuesta
incorpora regresiones concretas a los módulos mantenidos y un ensayo acotado de
esta capacidad en el protocolo de host; no restablece una campaña extensa como
condición automática de cada release.

GOVERNANCE.md aún contiene referencias a 0.15 y a controles antiguos. Deben
reconciliarse las afirmaciones de gobierno afectadas por esta evolución con los
documentos vigentes, sin modificar las fuentes congeladas de specs/canonical/ ni
tratar esa discrepancia como una autorización nueva de publicación.

## 4. Criterio de diseño resultante

La mejora cubre tres niveles: conducción persistente del agente, condiciones
obligatorias del runtime y detección independiente antes de integrar. Una única
función de análisis de cambio y cobertura alimenta todos los comandos para evitar
respuestas distintas entre decompose, readiness, start, resume, verify y guard.

La SPEC puede existir en borrador o suficientemente definida mientras la
planificación sigue pendiente. Lo que se bloquea es la implementación de ese
alcance. La confirmación de documentos, el permiso de ejecutar y la aceptación
del resultado siguen separados, reutilizando decisiones válidas y agrupando las
preguntas necesarias.

## 5. Reproducción y límites de la evidencia

Desde la raíz del repositorio:

```powershell
$probeReport = Join-Path $env:TEMP 'lks-sdd-spec-plan-task-probe.json'
python -B -X utf8 docs/proposals/spec-plan-task-2026-09-23/probe.py --repo . --output $probeReport
```

El informe registra commit, versión, intérprete y SHA-256 de los módulos usados.
Los resultados son diagnósticos de la versión observada; no son una nueva suite
de publicación. El reproductor corresponde a la base inspeccionada y puede
necesitar adaptación tras una corrección del contrato. Las implementaciones
futuras deben incorporar las regresiones necesarias a los tests mantenidos y
conservar el informe original como antecedente.

## 6. Comprobación de los entregables de esta revisión

- Se ejecutaron seis sondas diagnósticas sobre la base indicada, con resultado y hashes de fuentes conservados en probe-results.json.
- La especificación contiene 15 requisitos y el plan los asigna a 11 tareas con dependencias sin ciclos, 27 comprobaciones previstas y seis escenarios por host.
- Se comprobaron los enlaces locales, la asignación de cada requisito y la correspondencia de los hashes del informe con las fuentes inspeccionadas.
- `python -B -X utf8 scripts/validate_plugin_contract.py .` devuelve `VALID: LKS-SDD 2.2.0 active contract (readers 1.5/2.0; six skills)`.

Estas comprobaciones acreditan el análisis y la consistencia del plan. La
implementación del método nuevo y todos sus resultados de aceptación permanecen
pendientes; los módulos del runtime y las fuentes canónicas no se han modificado.
