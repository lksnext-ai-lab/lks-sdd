# Propuesta del método 2.1: implementación trazada desde la especificación

Fecha: 2026-09-23. Estado: propuesta técnica histórica de la evolución 2.3.0.
El contrato operativo entregado se documenta en
[continuidad SPEC/PLAN/TASK](../../docs/V2-SPEC-PLAN-TASK.md); este documento
conserva alternativas y objetivos para auditoría, sin ampliar las garantías del runtime.
El objetivo funcional procede de la solicitud del usuario de mantener siempre el
recorrido SPEC → PLAN/TASK → implementación, también al ampliar trabajo existente.
La propuesta fijó método 2.1.0 manteniendo schema documental 2.0. En esa fase
todavía no se había fijado versión de release ni autorizado publicación o instalación;
la autorización posterior corresponde a 2.3.0 y se registra por separado.

Fuentes: [revisión crítica y sondas](../../docs/proposals/spec-plan-task-2026-09-23/REVIEW.md),
[contrato canónico de planificación y continuidad](../canonical/LKS-SDD_extension_planificacion_continuidad_v1.3.md),
[workflows actuales](../../docs/V2-WORKFLOWS.md).
[Plan de implementación](../../docs/proposals/spec-plan-task-2026-09-23/PLAN.md).

## 1. Resultado esperado

Cada cambio implementado tiene una petición identificable, una SPEC vigente para
el comportamiento solicitado y una asignación explícita a PLAN/TASK, con criterios
de aceptación, pruebas, autorización y evidencia. La existencia de una funcionalidad
o un plan anteriores no presupone que el cambio esté cubierto.

La experiencia reutiliza lo que ya está acordado y actualiza únicamente lo afectado.
Al cerrar una etapa muestra el estado del siguiente paso y sus pendientes. Una
petición de modificación no se reduce a consultar documentos ni termina como
«especificación completa» ocultando que faltan tareas.

## 2. Requisitos de la evolución

| ID | Obligación |
|---|---|
| REQ-SPT-001 | Toda petición material de modificar una aplicación gobernada por este contrato pasa por identificación y reconciliación del cambio antes de editar código. Una consulta no inicia escrituras. |
| REQ-SPT-002 | La petición conserva un registro Markdown con identidad, resultado solicitado, fuentes, ámbito/versión objetivo y correspondencia de cada punto material con la SPEC. Las aclaraciones del mismo cambio actualizan su revisión; una reanudación no crea otra petición. |
| REQ-SPT-003 | La cobertura se deriva de la petición y obligaciones aplicables de la SPEC, incluyendo prosa, aceptación, pruebas y dependencias compartidas, y se contrasta con PLAN/TASK. El PLAN no define por sí solo el universo que se considera cubierto. |
| REQ-SPT-004 | Cada obligación del cambio tiene disposición explícita: trabajo planificado, cobertura ya verificada y vigente, diferida por decisión incremental o excluida por decisión de alcance. Desconocido permanece desconocido y bloquea si es crítico para la porción. |
| REQ-SPT-005 | Las TASKs se reutilizan, amplían, replanifican o crean conforme a su estado y a la distinción entre corrección del contrato original y alcance nuevo. Se preservan el resultado y la evidencia históricos. |
| REQ-SPT-006 | La asignación identifica propietario primario por obligación y contribuyentes delimitados, aceptación completa y tests trazados. Una relación con una feature o un requisito no concede cobertura automática. |
| REQ-SPT-007 | La autorización protege la especificación literal y la planificación normativa aplicable a la porción. Los cambios materiales invalidan su uso; los avances operativos o cambios independientes no lo hacen por mera proximidad. |
| REQ-SPT-008 | Todos los caminos que habilitan ejecución o cierre usan el mismo análisis: authorize, prepare, start, resume, correct cuando corresponda, checkpoint hacia revisión, verify y close. No se puede evitar por un alias, un writer genérico o un contrato anterior. |
| REQ-SPT-009 | Antes de escribir código se registra el EXEC sobre una baseline observada y el alcance autorizado. Cambios previos o desviaciones posteriores se preservan y reconcilian; no se atribuyen retrospectivamente a una autorización. |
| REQ-SPT-010 | La consulta y las instrucciones persistentes del proyecto permiten retomar el cambio desde otro hilo/host usando el runtime y contrato fijados, con una síntesis clara de SPEC, PLAN/TASK, ejecución y próximo paso. |
| REQ-SPT-011 | Un control independiente puede rechazar la integración de código sin SPEC/PLAN/TASK, cobertura, AUTH/EXEC y correspondencia con el diff observado. El control informa las garantías estructurales y los límites semánticos y de identidad. |
| REQ-SPT-012 | Nuevos registros y huellas se versionan de modo que un runtime incompatible los rechace. La transición de método 2.0.0→2.1.0 es explícita, reversible cuando sea seguro y conserva evidencia e historia sin inventar aprobaciones. |
| REQ-SPT-013 | Los controles respetan alcance, dependencias, versiones mantenidas y planificación incremental. Un borrador futuro independiente no bloquea trabajo vigente; una política complete exige completitud de su objetivo confirmado. |
| REQ-SPT-014 | Las comprobaciones reutilizan decisiones y aprobaciones vigentes. El usuario revisa resúmenes materiales y decisiones agrupadas; no tiene que repetir el método ni aprobar cada operación administrativa autorizada. |
| REQ-SPT-015 | La capacidad se verifica con regresiones concretas de runtime, compatibilidad, distribución y recorridos reales por host. Paquete válido, simulación y uso real se reportan con estados separados. |

## 3. Modelo documental propuesto

Se reutiliza el tipo de elemento `change` con categoría `implementation-request`
y alias `PCH-###`, manteniendo `CHG` de gobierno y los registros históricos existentes.
Las validaciones del método 2.1.0 comprueban esta categoría sin reinterpretar todos
los changes heredados. Se utiliza la extensibilidad del schema 2.0 existente.

El registro vive en `docs/lks-sdd/00-control/changes/`. Es Markdown canónico y el
índice solo guarda su ubicación. Contiene:

- resultado solicitado y fuente resumida, sin copiar conversaciones completas ni datos personales innecesarios;
- tipo: evolución, corrección, refactorización o combinación justificada;
- funcionalidad principal y contribuyentes, versión/entorno objetivo, límites y efecto sobre contratos compartidos;
- referencia a la baseline documental observada y a la revisión vigente de la petición;
- puntos materiales de la petición con claves locales estables y enlaces a obligaciones de la SPEC;
- disposiciones de cobertura con referencias a PLAN/TASK, evidencia previa o decisión explícita de diferir/excluir;
- decisiones pendientes y razones de incertidumbre, sin transformar propuestas en requisitos confirmados.

El texto de negocio permanece en la SPEC. PCH conserva la petición y su
correspondencia, sin mantener una segunda copia de requisitos o estados TASK.
Tableros, cobertura y siguiente acción son vistas derivadas.

Estados documentales propuestos para esta categoría: `draft`, `confirmed`,
`cancelled`, `superseded`. «Definido», «planificado», «ejecutable», «en curso» o
«verificado» son resultados derivados, con los IDs y motivos correspondientes.
Confirmar una petición no autoriza código ni prueba cobertura completa.

Las TASKs y los planes enlazan los cambios que les corresponden mediante relaciones
tipadas ya existentes cuando su semántica sea suficiente (`sources`, `affects`,
`plan`, `requirements`, `acceptance`, `tests`). El validador del método restringe
tipos de origen y destino. Este alcance utiliza las relaciones existentes; no
se añaden tipos incompatibles de elementos o relaciones. No se infiere pertenencia
desde carpetas.

## 4. Cobertura y aplicabilidad

Para cada punto material de la petición se identifican los requisitos y criterios
vigentes, la prosa normativa común y las obligaciones de prueba. Una modificación
de interfaz o regla compartida requiere revisar consumidores y dependencias; la
ausencia de enlaces completos se presenta como incertidumbre, no como exclusión.

La cobertura se calcula con granularidad de obligación, permitiendo que varias
TASKs contribuyan a un requisito mediante criterios delimitados. Cada obligación
implementable tiene responsable primario y las contribuciones no duplican propiedad.
La verificación conjunta tiene responsable cuando las tareas aisladas no pueden
demostrar el resultado completo.

Una disposición de cobertura es válida únicamente con su fundamento:

| Disposición | Condición |
|---|---|
| Planificada | PLAN y TASK vigentes, definición suficiente, límites, aceptación y pruebas enlazados. Su estado operativo no equivale a ejecución verificada. |
| Ya satisfecha | La misma obligación/revisión aplicable dispone de evidencia vigente y sujeto compatible; se conserva el vínculo histórico. Un done sin evidencia suficiente no basta. |
| Diferida | Decisión incremental confirmada con alcance y dependencias; mantiene el objetivo global como parcial. No puede diferirse una precondición de la porción que se pretende ejecutar. |
| Fuera del cambio | Decisión o ámbito previamente confirmado que justifica su no aplicabilidad a esta petición, versión y entorno. No elimina obligaciones del producto ni sustituye un desconocido. |
| Desconocida | Falta reconciliación o evidencia. No se cuenta como cubierta; bloquea la porción afectada cuando es crítica. |

La condición de completitud se comprueba desde la petición hacia las tareas y de
las tareas hacia el alcance acordado. Además se comprueba la suficiencia de toda
TASK seleccionada aunque parte de su alcance proceda de otra petición anterior.
Una solicitud puede tener varios planes si cada porción está delimitada y enlazada.

No se necesita revisar todas las funcionalidades del proyecto en cada operación.
Se analiza el cierre del ámbito y se conservan exclusiones justificadas. No se
declara que los enlaces garantizan la interpretación semántica del lenguaje humano.

## 5. Reglas de evolución del trabajo

| Situación | Tratamiento |
|---|---|
| Consulta o explicación | Leer y responder con fuentes; ninguna petición, SPEC o TASK nueva. |
| Petición ya cubierta por SPEC y TASK pendiente | Registrar o reutilizar la petición, verificar la correspondencia y continuar con la tarea existente si su autorización sigue vigente. No crear duplicados ni cambiar revisiones sin un cambio material. |
| Requisito existente sin trabajo asignado | Completar el PLAN y crear o ampliar una TASK pendiente con aceptación y pruebas. |
| Evolución de una feature con TASK en backlog/ready | Revisar la SPEC y la petición, ampliar el PLAN/TASK o separar otra tarea cuando haya límites distintos. Recalcular cobertura, dependencias y autoridad afectada. |
| Nueva obligación durante una ejecución | Conservar checkpoint y cambios; detener la porción afectada; replanificar la ejecución conforme a sus límites atómicos actuales; registrar nueva base y autorización antes de seguir. |
| TASK done y alcance nuevo | Mantener cierre y EVID históricos. Crear otra TASK vinculada al cambio y a la funcionalidad existente; no ampliar retrospectivamente la TASK cerrada. |
| TASK done y defecto del contrato original | Registrar PROB y usar correct; conservar la SPEC si ya expresa el resultado correcto, el cierre anterior y la EVID. Nueva ejecución cuando la anterior está cerrada y nueva verificación antes de resolver. |
| Refactorización o cambio técnico | Documentar el objetivo técnico, comportamiento que debe preservarse, restricciones, TASK y regresiones. Puede no requerir cambiar requisitos funcionales; siempre parte del contrato vigente. |
| Cambio UX, datos, migración o interfaz compartida | Reconciliar además los contratos visuales, persistencia, compatibilidad, consumidores y verificación conjunta aplicables. |
| Código ya cambiado fuera del flujo | Registrar desviación observada y origen desconocido donde corresponda; revisar la intención y el diff frente a una base fiable. No fabricar una ejecución anterior ni aprobar automáticamente lo que el código haga. |

## 6. Huellas y condiciones de ejecución

La base de ejecución propuesta contiene tres componentes versionados:

1. `specification_digest`: obligaciones literales de la porción y sus dependencias,
   reglas compartidas, aplicabilidad y activos pertinentes.
2. `planning_digest`: propósito y reglas normativas comunes del PLAN, política,
   correspondencias de la petición, asignaciones de la porción, dependencias,
   límites y responsabilidades de integración.
3. `execution_basis_digest`: combinación de los anteriores, identidades de
   proyecto/petición/TASK y versión del algoritmo de evaluación. La AUTH añade
   ámbito de entorno, vigencia y actor/rol declarado. EXEC registra aparte la
   baseline de código; EVID liga esta base contractual con el código/artefacto
   concreto observado. El código que se modifica durante la ejecución no forma
   parte de una huella de autorización que deba permanecer constante.

El detalle completo de una revisión del PLAN se conserva para auditoría. La
compatibilidad de una ejecución se decide por su proyección normativa, evitando
invalidarla por progreso, orden visual o membresía independiente. Toda prosa
normativa común se incluye; una regla particular necesita delimitación explícita
para no afectar a otras porciones. Cambiar una regla compartida invalida todas
las ejecuciones que la consumen. La falta de claridad impide inferir independencia.

La política complete se vuelve a comprobar sobre su objetivo completo, aunque la
huella sea por porción. Agregar una tarea independiente plenamente cubierta no
debe invalidar una AUTH por sí solo; dejar incompleto el mismo objetivo sí puede
bloquearlo conforme a la política confirmada.

Un único análisis alimenta context/decompose/readiness y las mutaciones. Se
recalcula sobre fuentes frescas antes de aplicar una operación para detectar
cambios entre preview y apply. Las mutaciones relacionadas de SPEC, PLAN, TASK y
PCH se pueden aplicar en una transacción revisable; también se permiten borradores
incompletos, con ejecución bloqueada y siguiente paso explícito.

El writer genérico no puede aumentar el alcance de una TASK cerrada conservando
su resultado ni cambiar una TASK en ejecución sin reconciliarla. Pausar, registrar
un problema, cancelar o replanificar deben seguir disponibles durante un bloqueo:
ninguna comprobación nueva puede impedir documentar o abandonar una ejecución.

## 7. Experiencia y continuidad

El bloque gestionado de AGENTS.md, las instrucciones Copilot y las skills expresan
una regla común: en el proyecto gobernado, toda modificación pasa por este
protocolo. Define conduce la reconciliación y planificación; implement verifica
las condiciones antes de escribir; help y readiness conservan lectura sin cambios.
Una activación incorrecta de implement deriva hacia los documentos pendientes.

La salida humana responde: qué cambia, qué SPEC lo recoge, qué PLAN/TASK se
reutiliza o cambia, qué falta y cuál es la siguiente acción. Los hashes y comandos
internos permanecen disponibles para auditoría sin dominar la conversación.

No se exige una aprobación nueva cuando el usuario ya autorizó exactamente el
alcance y la decisión sigue vigente. Cuando hay ampliación material se muestra
un único resumen completo para decidir. Un permiso de planificar no se convierte
en permiso de implementar. La mera existencia de un preview no acredita revisión.

Una conversación nueva resuelve raíz/clon, lock, runtime y contrato, lee el cambio
activo y el checkpoint y detecta modificaciones concurrentes. Un mismo proyecto
en otro worktree no se presume sincronizado. Las instrucciones del equipo fuera
del bloque gestionado se conservan. Conflictos críticos de instrucciones se
exponen; no se resuelven desactivando controles.

## 8. Integración independiente

El modo estricto del guard comprueba, para el patch completo y una base seleccionada
por el sistema de integración, la cobertura del cambio, las condiciones del plan,
AUTH, EXEC, huellas y correspondencia de archivos/artefactos con la ejecución. La
ausencia de registros, de la base requerida o de un verificador compatible bloquea.
No acepta rutas genéricas como prueba semántica de cualquier modificación interna.

El pipeline selecciona el runtime desde una referencia fiable fuera del candidato
y necesita revisión explícita para cambios de tests, gates, dependencias o del
propio contrato. La reconciliación documental aprobada debe existir en una fuente
fiable de autorización antes de aceptar el candidato, sin exigir integrar código
para poder aprobar su SPEC. No se confía solo en recibos añadidos por el mismo diff.

Se admiten varias TASKs cuando cubren el patch completo; solapamientos de rutas
requieren responsabilidad conjunta declarada. El guard local incluye cambios no
versionados pertinentes; CI comprueba lo que realmente se integra y declara su
base y alcance. Las rutas excluidas son las salidas documentadas del proyecto,
no exclusiones arbitrarias elegidas por el candidato.

El modo estructural histórico conserva su nombre y su límite. No se presenta
structurally-within-scope como resultado equivalente al modo estricto. El soporte
incluye una plantilla de CI y guía de protección de rama; activarla en proyectos
reales es una operación separada y autorizada.

La comprobación no impide físicamente ediciones locales, no autentica roles
declarados y no prueba la cronología de decisiones mutables por sus fechas.
El control externo puede bloquear integración incumplidora; la revisión semántica
y la protección de la base de confianza siguen siendo necesarias.

## 9. Compatibilidad y conversión

Decisión técnica propuesta: schema 2.0 y método 2.1.0 para la nueva obligación,
con validaciones diferenciadas de método 2.0.0 y del contrato 1.5. P06 confirma que
el runtime actual rechaza un method_version desconocido; una marca opcional de
política no consigue ese efecto. Se mantienen los formatos, tipos y relaciones
existentes, ampliando la validación de metadatos permitidos según el método.
La nueva versión del plugin se decide al preparar su release, sin alterar la
procedencia histórica de los consumidores.

La actualización de método 2.0.0→2.1.0 tiene diagnóstico, preview, conservación de snapshots,
confirmación y recuperación transaccional. Mantiene IDs, UID, referencias, activos
y personalizaciones. Inventaría fuentes reales; no crea peticiones retrospectivas
como si hubieran sido confirmadas en su momento. La reconciliación actual se
registra con su fecha real, procedencia y pendientes.

Una ejecución activa se resuelve con una decisión explícita: terminarla bajo su
runtime fijado antes de la actualización, o checkpoint/replanificación conservando código e
historia. La actualización no hereda AUTH/EVID como autoridad válida para nuevas
obligaciones. Los resultados históricos siguen consultables como históricos.

El runtime anterior rechaza método 2.1.0; el nuevo no usa una ruta de validación
antigua para escribir sobre ese método. Manifest, lock y adaptadores identifican
schema y método por separado. El rollback no sobreescribe trabajo posterior:
ante divergencia exige reconciliación. Se conserva la migración de schema 1.5→2.0
existente, seguida de la actualización explícita del método cuando corresponda;
no se añade una ruta directa desde 1.5 al método nuevo en este alcance.

## 10. Condiciones para aceptar esta capacidad

- Los casos P01–P03 dejan de habilitar trabajo con una base incompleta; P05 sigue bloqueando autoridad obsoleta.
- El control estricto rechaza el caso P04, mientras el resultado histórico del modo estructural conserva su significado.
- Se reutiliza correctamente una TASK pendiente, se amplía sin perder historia, se crea trabajo nuevo para alcance nuevo tras done y se permite corregir el mismo contrato.
- La proyección de planificación bloquea cambios normativos compartidos y mantiene autoridad válida ante cambios operativos o independientes justificados.
- La conversión y las rutas públicas impiden usar un runtime/contrato anterior para eludir controles nuevos.
- Los recorridos reales por host muestran que peticiones genéricas conducen a SPEC y PLAN/TASK sin recordatorios, y que una consulta no escribe.
- Queda visible qué garantías aporta el runtime, cuál es el estado del control externo y qué aceptación real sigue pendiente.

La matriz de casos y las tareas responsables están en el
[plan de implementación](../../docs/proposals/spec-plan-task-2026-09-23/PLAN.md).
