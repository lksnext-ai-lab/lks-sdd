# Contrato de verificación

## Estados de comprobación

- `passed`: se ejecutó y cumplió el criterio.
- `failed`: se ejecutó y no lo cumplió.
- `blocked`: un prerrequisito impidió ejecutarla.
- `not-run`: no se ejecutó; nunca equivale a éxito.
- `not-applicable`: existe una justificación documentada para el alcance.

`skipped` tampoco equivale a éxito y no es un estado admitido en la evidencia canónica del incremento; debe registrarse como `not-run` o `blocked` con su motivo.

## Clasificación del incremento

- `verified`: todas las comprobaciones aplicables pasaron y la trazabilidad está completa.
- `verified-with-reservations`: las comprobaciones críticas pasaron, pero permanecen limitaciones o comprobaciones no críticas no ejecutadas y visibles.
- `not-verified`: existe un fallo, bloqueo, ausencia crítica de evidencia o contradicción.

La clasificación técnica no aprueba producción, excepción, entrega, riesgo residual ni conformidad corporativa.

## Puerta de implementación

En 1.3 el plan se liga a una única `EXEC-###` del mismo `INC-###`, a sus `task_ids`, `profile_bindings` y locks exactos. Use `--execution-id` cuando varias ejecuciones puedan incluir la selección; el runner no elige una de forma ambigua. La proyección `implementation` se conserva por compatibilidad, pero no sustituye el historial de ejecuciones. En 1.2 se mantiene esa proyección como fuente operativa. Un estado `in-progress` permite anticipar checks, pero declara que la ejecución todavía no está habilitada.

Ejecutar cualquier check o registrar un `EVID-###` exige que ese mismo registro mantenga `implementation.status=completed`. Si falta `implementation`, el incremento no coincide, el perfil es incoherente o el estado es `not-started`, `in-progress` o `blocked`, el runner falla cerrado antes de invocar herramientas, crear evidencia o modificar trazabilidad e índice. Un plan, una autorización o unos checks potencialmente exitosos no sustituyen esta puerta.

Después de ejecutar y antes de escribir, el runner recarga `project.json` y revalida estado `completed`, incremento, tareas, bindings, todos los locks, revisión/árbol del repositorio y contrato activo contra la instantánea inicial. Si algo cambió, no crea `EVID-###` ni modifica trazabilidad o índice; la mutación externa se conserva y debe repetirse la verificación.

En 1.3 también exige que las huellas de especificación y planificación sigan vigentes, que la autorización cubra exactamente las tareas ejecutadas y que cualquier `CKPT-###` divergente haya sido reconciliado. Un checkpoint puede acreditar que se ejecutó un comando solo si contiene su resultado observado; nunca eleva por sí mismo un check a `passed`.

## Fases de trazabilidad

Antes de implementar, `preimplementation` exige una cadena no vacía de requisito confirmado, criterio de aceptación, decisión o no aplicabilidad motivada, incremento y prueba planificada. No exige fabricar evidencia antes de ejecutar. Una celda `Evidence` vacía o formada solo por espacios es el estado pendiente normal; por compatibilidad también se reconocen `none`, `pending` y `not-run`. El registrador y el lector consumen esta misma definición. `--record-evidence EVID-###` sustituye el estado pendiente por el identificador exacto solo después de superar las puertas aplicables y escribe EVID, ART-TRACE y manifest/EXEC como una unidad recuperable. No normaliza el Markdown antes de verificar, no cambia otras filas y no sobrescribe un EVID existente.

Durante verificación, la fase `verification` exige además un archivo estructurado `EVID-###` aplicable al mismo incremento, con clasificación `verified` o `verified-with-reservations`, una lista no vacía de checks y todos ellos en `passed`. Un enlace a un archivo ausente, `not-verified`, sin checks, o con cualquier check `not-run`, `skipped`, `blocked` o `failed` no satisface la trazabilidad. Si hay requisitos aplicables pero no se comprueba ninguno, ambas fases fallan de forma explícita.

El contrato activo excluye referencias rechazadas, sustituidas o retiradas como inputs de ejecución, aunque sus filas sigan conservadas para historial. La ausencia de `EVID-###` en preimplementación no es éxito de verificación; significa que la evidencia todavía debe producirse.

## Revisión visual y de interacción por slice

La aplicabilidad se calcula sobre las TASK seleccionadas, no sobre todo el incremento. El cálculo inspecciona su unidad, binding exacto, alcance y exclusiones, referencias `UX-###`/`VIS-###`, capabilities y gates frontend/browser. Si alguna TASK entrega interfaz, el slice mixto y la verificación conjunta de la release exigen revisión manual en navegador; sin evidencia, `visual-browser-review` queda `not-run` y la clasificación es `not-verified`. Una TASK backend sin interfaz, UX, VIS ni capacidades frontend/browser registra `not-applicable` con razón determinista fuera de `checks`; no crea fallo, reserva ni check no ejecutado. Una referencia UX/VIS o capability frontend/browser impide declarar no aplicabilidad.

El argumento `--visual-evidence` acepta un JSON 1.1 local bajo `docs/lks-sdd/evidence/visual/`. Sus claves exactas son `schema_version`, `increment`, `status`, `review_type`, `reviewed_at`, `reviewer`, `human_validation`, `baseline`, `coverage`, `screenshots`, `checks` y `limitations`. `reviewed_at` es ISO-8601 con zona horaria y, al ejecutar, no puede tener más de siete días. `reviewer` conserva rol y alias no identificativo.

`baseline` enlaza `baseline_id`, los SHA-256 actuales de implementación, `ART-INCREMENTS` y `ART-UX`, y todos los `VIS-###` confirmados. `coverage` relaciona todos los `UX-###`, `VIS-###`, estados y capturas revisados. Cada screenshot usa `SHOT-###`, ruta, SHA-256, ruta de aplicación, viewport con DPR y tipo de captura; sus dimensiones deben concordar. Cada check tiene ID, estado `passed`, UX, screenshots y nota. El JSON y capturas permanecen en el directorio visual, no usan enlaces y deben ser PNG/JPEG estructuralmente decodificables.

La evidencia canónica registra el SHA-256 del JSON, baseline, árbol de fuentes de implementación relevante y lista de capturas consumidas. El fingerprint incluye los archivos declarados y los árboles de código habituales (`apps`, `packages`, `services`, `src`, `lib` y `tests`), excluyendo dependencias, cachés y salidas de build; así no puede omitirse silenciosamente otro archivo fuente del mismo proyecto. La validación vuelve a comprobar el JSON y esos archivos; una mutación posterior queda expuesta sin copiar contenido visual sensible al Markdown.

## Gates componibles y evidencia mínima

Por cada binding perteneciente a las TASK seleccionadas se ejecutan los gates obligatorios de sus capacidades y el gate de composición exacta. Los bindings de tareas futuras o fuera del slice no se ejecutan. G2 demuestra que el contrato es preparable; G3 ejecuta calidad, build, pruebas e integración aplicables; G4 consume evidencia estructurada de promoción/despliegue. Un gate de capacidad no certifica una mezcla tecnológica distinta y un lock no sustituye el gate de composición.

La evidencia registra identificador, revisión de commit o workspace, rama, `tree_id` exacto, SHA-256 del listado del árbol, build determinista, incremento, tareas, bindings y locks, digests inmutables de artefactos, entorno, gates, resultados, limitaciones y relaciones con criterios/pruebas. No copia tokens, contraseñas, datos personales, imágenes, volcados completos ni logs productivos; para capturas conserva solo ruta y hash.

La verificación 1.2 exige cada `.lks-sdd/profiles/BIND-###.lock.json` como archivo regular idéntico al lock certificado empaquetado. Ausencia, `{}`, edición o enlace bloquean incluso `--plan`; así plan, ejecución y evidencia pertenecen a las mismas composiciones que fijó `active_contract_fingerprint` y materializó `prepare`.

`build_id` usa el contrato canónico `lks-sdd-build-1.0`: revisión, `tree_id`, `tree_sha256`, locks exactos, bindings/perfiles/versiones y digests de artefactos ordenados de forma estable. Excluye resultados, duraciones, timestamps, stdout/stderr, PID, rutas temporales y nombres Compose. `verification_run_id` identifica aparte cada ejecución y los diagnósticos completos permanecen en `checks`.

La evidencia G4 1.1 se materializa después de G3 con `--materialize-delivery-template`; nace `draft`, con `technical_run_id`, `REL-###`, `ENV-###`, revisión, árbol, build y digests ya conocidos, y todos los objetos humanos/operativos en `pending`. Tras completar promoción, smoke, observabilidad, recovery y autorización real, se cambia a `evidence_state: complete` y cada evidencia a `passed` con instante UTC y referencia verificable. La finalización mediante `--delivery-evidence` repite los gates técnicos actualmente; el mismo material debe reproducir exactamente el build ID y no puede cambiar revisión, tree ID/SHA o artefactos. El runner falla cerrado ante cualquier divergencia. La evidencia completa 1.0 sigue aceptándose por compatibilidad, aunque nuevas plantillas usan 1.1. El plugin no ejecuta ni autoriza merge, promoción o despliegue.

Cuando todas las tareas registradas de una release están `done`, aún se exige el punto de integración/verificación conjunta definido por el plan y que la cobertura continúe `complete`. Terminar todas las tareas conocidas no oculta alcance sin propietario ni autoriza promoción.

Use el dispatcher instalado y declare la fase de trazabilidad de forma explícita cuando la inferencia automática no sea apropiada:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase verification --json
python "<plugin-root>/scripts/lks_sdd.py" verify "<project-root>" --increment INC-001 --task TASK-001 --execution-id EXEC-001 --plan
```
