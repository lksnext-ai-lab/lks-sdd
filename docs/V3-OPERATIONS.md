# Operaciones del contrato 3.0

Referencia de campos bajo demanda. Punto de entrada:
`python -B <runtime>/scripts/lks_sdd.py v3 ACCION <proyecto> --input <datos.json>`.
Consultas no escriben. Las mutaciones producen preview; `--output` guarda el paquete
completo. `--apply` aplica cuando la decisión de la sesión ya autoriza esos datos.
`apply --input <paquete> --authorize <preview_hash>` aplica un paquete presentado.
La entrada JSON es un transporte; el resultado canónico sigue siendo Markdown.

## Configuración y autoría

- `init`: name, actor_name, profile, controls, statement, target. Perfiles:
  individual-brief, coordinated-team, independent-review. Declare el equipo antes
  de activar revisión separada. controls contiene sonar y dependency-check con
  mode required/informative/not-used y reason. Los usados declaran executor
  existing-report/existing-command, scope, timeout_seconds y max_retries.
  availability declara state: available, source comprobable y phase: implementation.
  Si solo existe análisis en PR o falta acceso, resuelva ese impedimento antes de
  confirmar el recorrido. init admite lifecycle y members [{name,roles}].
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
