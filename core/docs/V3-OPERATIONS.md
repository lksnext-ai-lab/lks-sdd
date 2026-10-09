# Operaciones del contrato 3.1

Referencia de campos bajo demanda. Punto de entrada:
`python -B <runtime>/scripts/lks_sdd.py v3 ACCION <proyecto> --input <datos.json>`.
Consultas no escriben. Las mutaciones producen preview; `--output` guarda el paquete
completo. `--apply` aplica cuando la decisión de la sesión ya autoriza esos datos.
`apply --input <paquete> --authorize <preview_hash>` aplica un paquete presentado.
La entrada JSON es un transporte; el resultado canónico sigue siendo Markdown.
`decision-view` y `review` con `--compact` devuelven una presentación literal sin
duplicar cuerpos, incluido `--json`. Sin esa opción, `--json` mantiene el resultado
detallado anterior; `--details` lo solicita expresamente y `--output` lo exporta completo.
La salida ordinaria sin `--json` es compacta. El recibo y los guards son los mismos.
`context` usa aplicabilidad literal; `reference: true` obtiene el diagnóstico completo.
`catalog` con `kind: prose` pagina fuentes, hashes y estado de clasificación sin sus cuerpos.
Las declaraciones canónicas se explican en [DOCUMENT-CONTEXT.md](DOCUMENT-CONTEXT.md).
El CLI público exige método 3.1.0, colaboración y runtime fijado para escrituras
ordinarias. Los lectores antiguos y recuperadores permanecen. `migration-preview`
prepara v2 → 3.1, 3.0 → 3.1 o actualización de runtime 3.1.
`packet_directory` selecciona un directorio nuevo externo para preparar volúmenes
grandes: contiene `packet.json` y sus objetos. Conserve y transporte ambos.
`--output` guarda también un descriptor y su directorio de objetos adyacente.

`checkpoint` admite `operation_id` para reintentar una observación exacta sin crear
otro evento. Una clave reutilizada con contenido, actor o sujeto distinto se rechaza;
otra observación usa otra clave. Sin clave, cada llamada conserva su hecho distinto.
La presentación omite checkpoints simples anteriores cuando hay uno posterior del
mismo ámbito; conserva pendientes, problemas y evidencia. `trace` recupera el historial.

## Configuración y autoría

- `init`: name, actor_name, profile, controls, statement, target. Perfiles:
  individual-brief, coordinated-team, independent-review. Declare el equipo antes
  de activar revisión separada. controls contiene sonar y dependency-check con
  mode required/informative/not-used y reason. Los usados declaran executor
  existing-report/existing-command, scope, timeout_seconds y max_retries.
  availability declara state: available, source comprobable y phase: implementation.
  Si solo existe análisis en PR o falta acceso, resuelva ese impedimento antes de
  confirmar el recorrido. init admite lifecycle y members [{key,name,roles}].
  Exige runtime_bundle y collaboration con los campos de `collaboration-3.1.schema.json`.
  Para nuevas personas use `$owner` y las claves declaradas en members; se resuelven
  a UUID sin escoger personas automáticamente. Declare explícitamente los dos
  indicadores de revisión, los tres validadores y la lista de revisores, incluso vacía.
- `author`: actor, items. Cada item contiene meta y body; los campos cerrados de
  meta están en `schemas/element-3.0.schema.json`. El helper local
  `v3_contract.element(kind, title, body, **data)` genera UUID independiente.
  Relaciones usan UUID, con alias legible solo para presentación. Una revisión
  conserva UUID/tipo e incrementa revision. Eventos no se crean mediante author.
- request: data.policy/policy_digest/branches/target/base se vinculan al crear;
  relations.proposal identifica las unidades funcionales/técnicas.
- proposal: data.part functional/technical/joint; objective, included, excluded,
  behavior, solution, impact, acceptance y unresolved. body explica lo concreto.
- task: data.request, owner, scope (rutas relativas), acceptance, tests,
  dependencies [{uid,type,artifact,digest}], proposal_units opcionales.
  Dependencias: contract, available, verified. relations.covers asigna obligaciones;
  interfaces/tests/technology enlazan sus contratos. Una tarea conjunta declara
  integration: true. plan.data.request y plan.relations.tasks vinculan el plan.
- `review`: request y units opcionales. Devuelve la porción exacta que se somete a decisión.
- `approve`: actor, units, purpose proposal/plan/technology, statement, reason opcional.
- `authorize-plan`: actor, plan, statement. Registra aprobación y autorización
  separadas con una misma respuesta explícita.
- `governance`: actor, items (policy/member/project), statement, reason, requests
  afectadas. Se evalúa la autoridad previa. Las peticiones no seleccionadas conservan
  su política fijada; las bajas/roles vigentes sí se consultan antes de actuar.
- `revoke`: actor, decision, reason. Añade una revocación; conserva la decisión original.

## Ejecución, equipo y evidencia

- `readiness`: actor, task, action; diagnóstico de preparación de esa transición.
- `context`: roots, operation; una copia literal por bloque y adjuntos necesarios.
  La salida predeterminada conserva el contrato normativo activo; comparison: true
  ensaya la selección en una copia controlada y no sustituye el contexto de ejecución.
- `start`, `resume`, `implement`, `verify`, `close`, `pause`, `cancel`, `reopen`:
  actor, task, reason, refresh opcional para referencias compartidas.
- `checkpoint`: actor, task, result, pending; classification progress/correction/
  previous-debt/deviation/false-positive/accepted-risk/new-scope; analysis opcional.
  `deviation` conserva como hecho trabajo observado sin autorización previa y sus
  pendientes. La regularización requiere una decisión actual sobre esa porción;
  nunca crea permiso retroactivo. Ningún checkpoint cambia por sí mismo el resultado
  de calidad ni concede una excepción.
- `assign`: actor, task, recipient, reason. En equipo la oferta se acepta con previous
  y accept: true por el destinatario. `handoff` usa ese mismo recorrido y añade scope.
- `exception`: actor, task, rule, action, reason, expires_at. La excepción no omite
  identidad, autorización, conservación ni veracidad de la evidencia.
  Reglas admitidas: quality, dependencies, assigned, branch y process:<paso>.
  `propose-exception` registra rule/action/reason/effect como petición pendiente si
  el caso no está previsto; no habilita la transición por presentarlo.
- `evidence`: actor, task, tests, outcome passed/failed/not-run, source automated/
  human-observation/external-report, artifact y explanation. La evidencia se copia
  a almacenamiento documental recuperable y queda ligada al sujeto exacto.
- `integrate`: actor, request, trusted_root, statement; la base de confianza debe
  ser un checkout independiente del mismo proyecto y representar su rama destino.
  Registra revisión SDD; no mergea. La base se vuelve a comprobar al aplicar.
- `accept`: actor, request, statement. Registra aceptación funcional explícita.

## Calidad durante la implementación

`analysis` recibe actor, tasks, tool sonar/dependency-check y report. El informe
normalizado conserva analysis_id, generated_at, tool_version, subject_digest,
config_digest, context {target,base_head} y state pending/error/cancelled/completed. El wrapper de un informe
existente solo puede afirmar la procedencia realmente observada. No fabrique un
informe ni complete campos desconocidos para satisfacer el lector.

Sonar requiere projectStatus.status OK/ERROR y gate_analysis_id igual al analysis_id
terminal. Dependency-Check requiere dependencies (con vulnerabilities/CVSS cuando
existan), data_updated_at y suppression_digest coincidente con la política. Un
informe nativo sin vinculación recuperable con las entradas no acredita ese sujeto.

`analysis-run` recibe executable y arguments además de actor/tasks/tool; la política
debe contener executable_sha256 y arguments_digest exactos. Se ejecuta sin shell,
con timeout y reintentos limitados. retry_of conserva el intento anterior. Se usa
un exportador ya existente que produzca el informe normalizado; el plugin no instala
servidores, scanners, jobs ni conectores. Los casos de prueba locales no acreditan
acceso a una instancia real del consumidor.

`analysis-findings` recibe analysis, offset y limit. Muestra total y página de hallazgos
del informe conservado. El registro habitual guarda como máximo veinte hallazgos;
el original íntegro permite recuperar los restantes sin cargarlos todos en el chat.

## Consulta, adopción, migración y recuperación

`status` admite request/task, offset y limit. `catalog` admite kind y paginación;
`trace` usa uid, offset y limit para enlazar quién definió, autorizó, ejecutó, revisó,
integró o aceptó, con las fuentes históricas. Un solicitante de negocio no registrado
permanece desconocido; no se deduce que sea el operador de la sesión.
`history` requiere uid/digest. `reindex` reconstruye el índice desde Markdown válido.
`adopt-inspect` usa paths/purpose; `adopt` usa actor/inspection/observations/
confirmed_intent/statement. Un sistema existente sin SDD no pasa por un v2 ficticio.

Para v2 use [la guía específica](V3-MIGRATION.md). `recover` o `rollback` requiere
--authorize con hash de la operación interrumpida. Para una operación completada,
--receipt identifica el almacén devuelto. La recuperación rechaza cambios posteriores.

## Decisiones presentadas

`decision-view` es de solo lectura: recibe `event` y `data` de la operación prevista,
sin declaración ficticia. La CLI devuelve `markdown`, `instruction_refs`,
`intervention`, `issues`, `complete` y `receipt`; `--json` añade `sections`,
`sources`, `attachments` y la base detallada. Presente el
contenido antes de recoger una decisión. Una decisión nueva recibe `presented` con
el receipt exacto además de su `statement`; los campos y fuentes no pueden cambiar
entre ambos pasos. Una respuesta vigente se reutiliza.

Ejemplo de consulta: `{"event":"authorize-plan","data":{"actor":"<UID>","plan":"<UID>"}}`.
Después de mostrar la vista y recibir la respuesta, `authorize-plan` recibe esos
mismos datos, `statement` con la decisión real y `presented` con el receipt devuelto.
Los helpers Python admiten el mismo argumento adicional `presented`.

Para explicar `recover` o `rollback`, use `data.authorized_hash` y, cuando exista,
`data.receipt` de la transacción. La vista conserva el registro y explica sus
archivos afectados; no inicia la recuperación. Para imágenes, `assets` contiene
rutas locales y `observed_assets` relaciona cada ruta con la huella del archivo
efectivamente observado. No declare observación por haber leído únicamente la ruta.

Los eventos `clarify`, `identity`, `technology-choice`, `visual-choice`,
`external-action` y `client-view` son perfiles de consulta, no comandos ejecutores.
Las rutas históricas muestran su indisponibilidad y no habilitan escrituras.
Para propuesta técnica, consulte el formato de componentes en
[especificaciones](decision-guides/specifications.md).

## Configuración explícita del recorrido integral

`configure-collaboration`: actor, statement, collaboration y requests opcionales.
collaboration contiene proposal_review_required y task_review_required (booleanos),
y defaults con responsible, integration_validator, functional_validator (UID de
miembros) y reviewers [{member, required, domains}]. Se deduplican personas, no roles.
El campo coordination opcional aplica una designación específica a las peticiones
seleccionadas. El motivo y las designaciones deben proceder de una decisión explícita.

La operación actualiza formato/método a 3.1/3.1.0, conserva las reglas fijadas de
peticiones no seleccionadas y no fabrica revisiones históricas. La entrada pública
requiere runtime_bundle compatible, también sin lock previo; la vista previa incluye el corte del runtime y
documentos. apply/recover/rollback conservan el mecanismo transaccional existente.

## Revisión y ejecución

- `review-comment`: actor, request, target, statement, blocking y critical.
- `resolve-comment`: actor, request, comment, statement y treatment
  incorporated/dismissed. El autor de una objeción confirma su tratamiento al revisar.
- `review-proposal`: actor, request, statement, outcome approved/changes-requested.
- `close-proposal`: actor, request, statement, review opcional. review=true registra
  conjuntamente la revisión propia y el cierre cuando faltaba solo esa conformidad.
- `authorize-plan`: admite review_tasks con los UID exactos de tareas propias
  presentadas y revisadas por esa misma respuesta. Omitirlo no inventa revisión.
- `review-task`: actor, request, tasks, statement, outcome approved/changes-requested.
- `start`/`resume`: review=true agrupa revisión e inicio; offer permite aceptar una
  oferta de asignación/relevo del destinatario en el mismo paquete recuperable.
- `review-exception`: actor competente, request, statement, rule integral-review,
  action close-proposal, effect y expires_at. Mantiene reservas y firmas ausentes.

Un cambio material del paquete requiere conformidades nuevas. Las tareas conservan
su revisión mientras no cambie el contrato, destinatario o porción; editar código
durante la implementación no obliga a revisar de nuevo el encargo.

## Resultado y correcciones

`integrate` conserva trusted_root y admite accept_result=true si la misma persona
puede comprobar integración y aceptar funcionalmente el candidato ya presentado.
Las dos acreditaciones se conservan; no se realiza merge.

`reject-result`: actor, request, statement, phase integration/acceptance/external,
tasks, expected y observed; artifact y requirements son opcionales. La evidencia ausente queda pendiente. Registra fallo y
definición correctiva en borrador, incluso antes de poder cerrar la integración.

`define-correction`: actor, correction, classification defect/agreement-change/
new-request/external, statement, acceptance y tasks/requirements opcionales.
Confirmar el defecto no autoriza otro alcance. Reabra trabajo cubierto por la
autorización vigente o revise propuesta/plan antes de ampliar el encargo.

`resolve-defect`: actor, problem, statement; exige definición confirmada y evidencia
de corrección vigente. Después repita integración/aceptación del nuevo resultado.
`prepare-delivery`: actor, request, statement, pr_url opcional observado. Requiere
aceptación vigente; preparar el resumen no crea ni aprueba el PR, ni ejecuta CI/CD.

Las operaciones de revisión, rechazo, definición/resolución correctiva y entrega admiten
refresh cuando el proyecto exige comprobar referencias compartidas. Los resúmenes
muestran completed-with-reservations para cierres dispensados y not-required para
revisión de encargos desactivada: ninguno acredita una firma ausente. Un reintento
de revisión o cierre vigente devuelve already-recorded, sin duplicar eventos.
