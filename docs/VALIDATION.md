# Validación local

Preparar previamente el intérprete de mantenimiento con
`python -m pip install --require-hashes -r requirements-runtime.txt`, preferiblemente
en un venv externo. CI hace lo mismo en su intérprete aislado. No instalar dependencias
dentro del checkout limpio ni suponer que las bibliotecas personales están disponibles.

En Windows, la regresión `test_windows_long_paths` copia el plugin a una instalación
de más de 260 caracteres y compara contrato, perfiles, integridad completa, diagnóstico
y preview de migración con una instalación corta. Ejecutarla con
`python -B -X utf8 tests/run_unit_tests.py --suite package --module test_windows_long_paths`;
en otros sistemas queda explícitamente omitida.

## Versión 2: contrato y evidencias independientes

La versión `2.0.0` añade contrato 2.0/método 2.0.0; los procedimientos que
siguen identificados como 1.5 o 1.x se conservan para esa línea. No mezclar sus
comandos con el nuevo ciclo. La migración oficial ahora existe, exclusivamente
desde 1.5 y previa autorización; no se ejecuta por actualizar el plugin.

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v2_document_contract --module test_v2_lifecycle --module test_v2_controls --module test_v2_integration_controls --module test_v2_adoption_migration --module test_v2_query_context --module test_v2_project_variants
python -B -X utf8 scripts/v2_audit.py
python -B -X utf8 tests/v2_benchmark.py --help
python -B -X utf8 tests/v2_docker_smoke.py --help
python -B -X utf8 tests/v2_distribution_smoke.py --help
python -B -X utf8 scripts/lks_sdd.py v2 --help
```

La [matriz v2](plans/2026-09-18-lks-sdd-v2-coverage.md) conserva el alcance aprobado;
el [informe de implementación](validation/v2-implementation.md) registra lo
ejecutado. Un test sintético no cambia el estado `not-run` del piloto ni demuestra
aceptación humana/Codex/Copilot. No aumentar presupuestos para ocultar regresiones.
La auditoría enlaza 67 mejoras, 48 tareas y 60 familias con código y pruebas reales;
`--report <informe-unitario.json>` añade resultados observados, no aceptación semántica.
El smoke Docker se ejecuta explícitamente con el motor Linux y la imagen local
fijada; no opera un proyecto real. El protocolo [por host](V2-HOST-ACCEPTANCE.md)
y el [expediente v2](../quality/v2-acceptance.json) separan esos ensayos de la
aceptación humana. Para una campaña completa use `tests/run_unit_tests.py --suite
all --json-out <ruta-nueva.json>` y los evals; en un worktree de desarrollo siguen
siendo diagnóstico, no atestación publicable.

Las regresiones de migración deben comprobar además `migration-complete`, el
manifiesto de disposición uno-a-uno, la negativa ante rutas activas 1.5,
idempotencia, recuperación protegida frente a ediciones posteriores, runtime
histórico/no gestionado y continuidad selectiva por TASK. `migration-status` y
`migration-continuation` son observadores de solo lectura y no sustituyen la
validación humana del preview.
`v2_distribution_smoke.py` compara dos builds del mismo snapshot de desarrollo,
valida el archivo nativo Copilot y ensaya migración/rollback con el núcleo 1.x de
HEAD y el núcleo v2 completo en directorios temporales. `--baseline-commit
<sha-completo>` selecciona una referencia histórica 1.x sin checkout; por defecto
usa HEAD mientras siga siendo 1.x. No registra ni activa instalaciones personales.

Para medir consultas de un consumidor con el paquete completo fijado, ejecutar
`tests/v2_benchmark.py --pinned --json-out <ruta-nueva.json>`: incluye la comprobación
fresca de todos los hashes en cada consulta. Sin `--pinned` mide un proyecto sin
runtime gestionado; ese resultado no acredita el coste del runtime fijado. Ambos
modos exigen al menos veinte muestras por tamaño, sin caché persistente de confianza.

## Consultas humanas del proyecto (incluidas en v2)

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_project_query
python -B -X utf8 tests/query_benchmark.py
python -B -X utf8 scripts/lks_sdd.py query --help
```

Las pruebas de consulta pertenecen a integration. Cubren recuperación documental,
ampliación condicionada al código, seguridad de rutas, prosa/relaciones, deriva,
readonly y runtime fijado sin bytecode. El benchmark crea y limpia fixtures temporales
y separa sus tiempos de la latencia del asistente. La guía es [PROJECT-QUERY.md](PROJECT-QUERY.md).
No atribuir comprensión humana ni aceptación de host a estas pruebas automáticas.
Resultados y límites de esta entrega en
[validación de consultas](validation/project-query-2026-09-17.md).

## Variantes tecnológicas de proyecto (incluidas en v2)

```powershell
python -X utf8 tests/run_unit_tests.py --module test_project_variants
python -X utf8 tests/variant_docker_smoke.py
```

La primera prueba pertenece a integration y no ejecuta Docker. La segunda es una
aceptación explícita con Docker Linux e imagen Python fijada por digest ya local:
aprobación única, preparación sin scaffold, observer aislado real, reutilización
sin procesos, cierre TASK/EXEC/CKPT y validación canónica. No equivale a una release.
El procedimiento y los límites están en [PROJECT-VARIANTS.md](PROJECT-VARIANTS.md).

## Distribución dual

```powershell
python -X utf8 tests/run_unit_tests.py --module test_dual_distribution --module test_visual_handoff
python -X utf8 scripts/lks_sdd.py visual-handoff --help
python -X utf8 scripts/lks_sdd.py runtime-doctor --help
python -X utf8 scripts/validate_copilot_package.py RUTA_AL_ZIP_COPILOT_PLUGIN
```

Los módulos nuevos pertenecen a package e integration respectivamente. Comprueban
núcleo idéntico, reproducibilidad, instalación/actualización/retirada aisladas,
personalizaciones, integridad, recuperación y relevo con fuentes/approval canónicas.
También comprueban el manifiesto y las seis entradas del plugin nativo Copilot,
bootstrap sin skills duplicadas, migración en ambos sentidos y que actualizar
el paquete personal no cambie el lock del consumidor. El test de runtime completo
instala desde el setup nativo en un directorio temporal y ejecuta definición y
validación; no registra un plugin en la configuración personal del host.
No ejecutan sesiones reales de Copilot ni generan imágenes. Conservar `not-run` para
los canales humanos descritos en [aceptación dual](DUAL-HOST-ACCEPTANCE.md).
La release estable v2 usa `--channel stable` y su aprobación específica
`quality/release-approval-v2.0.0.json`. La aceptación humana/host permanece separada
con su estado observado; publicar no la convierte en superada.

Ejecute las comprobaciones desde la raíz del repositorio con Python 3. Los comandos de estructura no requieren red; los gates completos descargan toolchains e imágenes bloqueadas y requieren Docker.

## Puerta rápida de estructura y contrato

```powershell
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$quickValidate = Join-Path $codexRoot "skills\.system\skill-creator\scripts\quick_validate.py"
$validatePlugin = Join-Path $codexRoot "skills\.system\plugin-creator\scripts\validate_plugin.py"

python $quickValidate skills\lks-sdd-help
python $quickValidate skills\lks-sdd-define
python $quickValidate skills\lks-sdd-adopt-existing
python $quickValidate skills\lks-sdd-assess-readiness
python $quickValidate skills\lks-sdd-implement
python $quickValidate skills\lks-sdd-verify
python $validatePlugin .
python scripts\validate_reference_profile.py --all --allow-unvalidated
python scripts\validate_plugin_contract.py .
python scripts\validate_fixture_manifest.py .
```

`--allow-unvalidated` comprueba la estructura de los veintitrés perfiles, incluidos los candidate; no los presenta como soportados. `validate_plugin_contract.py` exige además que cada perfil `active` tenga una certificación exacta vigente, valida catálogo, drivers, scaffolds y locks, mantiene por hash las siete fuentes canónicas, identifica separadamente las propuestas candidate 1.4/1.5, valida el contrato 1.5, las seis skills y la ausencia de componentes fuera de alcance.

Puede consultar el inventario de producto así:

```powershell
python scripts\lks_sdd.py profiles --all --allow-unvalidated --json
```

## Certificación de perfiles

Un perfil active solo es `supported` si su registro de certificación coincide con todos sus hashes actuales. Para validar esa evidencia sin ejecutar toolchains:

```powershell
$catalog = Get-Content profiles\catalog.json -Raw | ConvertFrom-Json
$catalog.profiles | Where-Object lifecycle -eq "active" | ForEach-Object {
  python scripts\validate_reference_profile.py --profile $_.id
  if ($LASTEXITCODE -ne 0) { throw "Certificación inválida: $($_.id)" }
}
```

Cuando cambie descriptor, capability, driver, scaffold, composición, gate o motor de certificación, vuelva a ejecutar el gate completo del perfil. `--record-certification` solo escribe evidencia y regenera el lock después de que todos los gates obligatorios y el gate de composición hayan pasado:

```powershell
python scripts\run_reference_profile_gate.py --profile WEB-REACT-VITE-STATIC --runtime docker --containers --record-certification --json
```

Repita el comando para cada perfil afectado. No use `--allow-unvalidated` como sustituto de esta puerta. Los perfiles candidate se mantienen sin certificación hasta que una decisión de producto autorice su promoción y exista evidencia completa.

## Puerta de release, pruebas y evals

El siguiente comando corresponde a la release 2.0.0 y su aprobación específica.
Ejecutarlo en un checkout limpio con resultados externos. Una versión posterior
necesita su propia aprobación y no puede reutilizar este fichero.

```powershell
$validationDate = Get-Date -Format "yyyy-MM-dd"
$qualityReport = Join-Path ([System.IO.Path]::GetTempPath()) ("lks-sdd-quality-{0}.json" -f [guid]::NewGuid().ToString("N"))
python scripts\run_quality_harness.py --channel stable --date $validationDate --baseline quality\baselines\v0.17.0.json --profile-mode reuse --release-approval quality\release-approval-v2.0.0.json --output $qualityReport
```

El harness es la única ejecución integral requerida para una release: valida fixtures,
contrato y perfiles, ejecuta `fast`, `integration`, `package`, `profile` y los evals una
sola vez, y comprueba las certificaciones exactas reutilizadas. Ejecute una suite o los
evals directamente sólo para diagnosticar un fallo o iterar sobre un cambio localizado;
esa repetición no añade evidencia de release y no sustituye el reporte integral.

Para feedback rápido:

```powershell
python scripts\run_fast_validation.py --focus jira-reporting
python scripts\run_fast_validation.py --focus compatibility
python scripts\run_fast_validation.py --changed-from origin/main
```

El fast gate no acredita una release. El harness integral emite quality report 1.2; el schema 1.1 se conserva únicamente para leer evidencia histórica. Cada módulo pertenece exactamente a un tier, stdout permanece JSON y el progreso se escribe en stderr. `--profile-mode reuse` comprueba todos los perfiles active contra certificaciones exactas con un máximo de 90 días; cualquier deriva o caducidad falla y requiere `--profile-mode execute` o recertificación Docker. `not-run`, `skipped` y timeout nunca cuentan como `passed`.

Los límites bloqueantes son 120 s para `fast`, 480 s para `integration`, 240 s para `package`, 180 s para `profile` en reutilización y 900 s para candidate sin Docker `execute`. Un módulo dispone de 90/180/300 s según tier; Docker `execute` conserva un máximo separado de 30 minutos. Los 90 s de `fast` dejan margen para el shard de experiencia medido en 60,191 s en un checkout limpio bajo Windows; no amplían el límite bloqueante de 120 s de la suite ni las aserciones de rendimiento del producto. Cada tier aplica su presupuesto dentro de `tests/run_unit_tests.py`; el harness reserva 900 s únicamente como techo de emergencia del despachador para que el hijo pueda devolver su JSON y limpiar procesos. Si un tier supera su propio presupuesto, sigue fallando. El timeout mata el árbol de procesos y registra si la limpieza quedó confirmada. `--preflight-only` conserva la atestación completa como diagnóstico opcional, pero la ruta estándar invoca directamente el harness: éste toma esa misma atestación exacta una sola vez antes de lanzar hijos. `--force` exige `--rerun-reason`.

El reporte publicable debe crearse desde un checkout dedicado, limpio y sin archivos no versionados preexistentes, incluso ignorados. Una ejecución sobre el árbol de desarrollo es diagnóstico, no atestación publicable. Los tests sintéticos de tracking no ejecutan Rovo; `definition-conversation` y `pilot` conservan su estado real, incluido `not-run`. La promoción stable se apoya en gates técnicos y `release-approval`; no convierte esos canales opcionales en superados. El procedimiento reproducible y el doble build están en `docs/DISTRIBUTION.md`.

## Validación de un proyecto consumidor 1.5

`<plugin-root>` y `<project-root>` son ubicaciones distintas:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" validate-project "<project-root>" --json
python "<plugin-root>\scripts\lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation --json
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" validate
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" board
python "<plugin-root>\scripts\lks_sdd.py" planning "<project-root>" --increment INC-001 assess --json
python "<plugin-root>\scripts\lks_sdd.py" planning "<project-root>" --increment INC-001 next --json
python "<plugin-root>\scripts\lks_sdd.py" tracking status "<project-root>" --json
python "<plugin-root>\scripts\lks_sdd.py" assess-readiness "<project-root>" --increment INC-001 --task TASK-001 --json
python "<plugin-root>\scripts\lks_sdd.py" implement "<project-root>" --increment INC-001 --task TASK-001 --dry-run --json
python "<plugin-root>\scripts\lks_sdd.py" continuity "<project-root>" resume --json
python "<plugin-root>\scripts\lks_sdd.py" verify "<project-root>" --increment INC-001 --task TASK-001 --execution-id EXEC-001 --plan --json
python "<plugin-root>\scripts\lks_sdd.py" verify "<project-root>" --increment INC-001 --task TASK-001 --execution-id EXEC-001 --execute --environment ENV-001 --materialize-delivery-template docs/lks-sdd/evidence/delivery/REL-001-ENV-001.json --json
python "<plugin-root>\scripts\lks_sdd.py" verify "<project-root>" --increment INC-001 --task TASK-001 --execution-id EXEC-001 --execute --environment ENV-001 --delivery-evidence docs/lks-sdd/evidence/delivery/REL-001-ENV-001.json --record-evidence EVID-001 --json
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" transition --task TASK-001 --to blocked --reason "PROB-001 pendiente" --actor delivery-owner --date 2026-08-22 --blocker PROB-001 --preview --json
```

La primera ejecución técnica fija `build_id`, `verification_run_id`, revisión, árbol y digests, y crea una plantilla G4 1.1 `draft`; no acredita G4. Complete esa plantilla únicamente con promoción, smoke, observabilidad, recuperación y autorización realmente ejecutadas. La segunda ejecución consume la evidencia `complete`, falla cerrada ante cualquier deriva y no incorpora tiempos, logs, PID ni nombres temporales a la identidad del build. Una evidencia completa histórica 1.0 sigue siendo aceptada sin reescritura.

La elección de tracking usa el mismo protocolo local preview/hash/apply. Los siguientes ejemplos utilizan datos sintéticos; sustituya el hash únicamente por el devuelto por la vista previa exacta:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode repository-only --decision ADR-001 --date 2026-08-25 --json
python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode repository-only --decision ADR-001 --date 2026-08-25 --apply --authorize "<mutation-hash>" --json

python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode jira-hybrid --reporting-scope milestone-reporting --coordination-gate advisory --decision ADR-002 --date 2026-08-25 --site "https://example.atlassian.invalid" --project DEMO --issue-type Task --json
python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode jira-hybrid --reporting-scope milestone-reporting --coordination-gate advisory --decision ADR-002 --date 2026-08-25 --site "https://example.atlassian.invalid" --project DEMO --issue-type Task --apply --authorize "<mutation-hash>" --json
python "<plugin-root>\scripts\lks_sdd.py" tracking preview-sync "<project-root>" --task TASK-001 --json
```

`preview-sync` exige exactamente una `--task`. Si el plan local no está confirmado, íntegro y vigente, el tracking se informa como `not-assessed` y no se autoriza ninguna proyección. Para una acción `create`, use Rovo para buscar el marcador exacto del preview dentro del proyecto confirmado y continúe solo con cero coincidencias; para `update`, lea la identidad ya mapeada y continúe solo con una coincidencia inequívoca. Después persista la autorización durable antes del write. Las dos alternativas exactas son:

```powershell
# create, solo después de una búsqueda Rovo del marker con cero coincidencias
python "<plugin-root>\scripts\lks_sdd.py" tracking authorize-sync "<project-root>" --task TASK-001 --preview-hash "<preview-hash>" --authorized-by-role delivery-owner --authorized-on 2026-08-25 --duplicate-check no-match --apply --json

# update, solo después de leer mediante Rovo el mapping y marker coincidentes
python "<plugin-root>\scripts\lks_sdd.py" tracking authorize-sync "<project-root>" --task TASK-001 --preview-hash "<preview-hash>" --authorized-by-role delivery-owner --authorized-on 2026-08-25 --duplicate-check matched --apply --json
```

Ejecute únicamente la alternativa que corresponda a la acción del preview. `authorize-sync` devuelve y persiste un `sync_id` antes de que Rovo escriba; desde ese momento `preview-sync` mostrará `awaiting-execution` y no debe autorizarse otra escritura. Ejecute la única creación/actualización mostrada, relea el work item y cierre ese recibo. Un éxito exige identidad completa y la huella de proyección realmente observada en Jira:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" tracking record-result "<project-root>" --sync-id SYNC-001 --result succeeded --external-id "10001" --external-key "DEMO-1" --url "https://example.atlassian.invalid/browse/DEMO-1" --remote-status "To Do" --observed-correlation-marker "LKS-SDD-PROJECT: <project_id>; TASK: TASK-001" --observed-projection-fingerprint "<projection-fingerprint>" --date 2026-08-25 --apply --json
```

Use el mismo `--sync-id` con `failed`, `conflict` o `uncertain` cuando ese sea el resultado real; no invente `succeeded`. Un `uncertain` o `conflict` bloquea nuevas escrituras. Tras una lectura Rovo autorizada, `reconcile-result` se ancla en el último recibo cerrado de la TASK mediante `--anchor-sync-id`; así puede registrar la identidad/estado observados o un cambio de key que conserve el mismo `external_id` y el prefijo del proyecto confirmado aunque el plan haya derivado. No ejecuta un write ni autoriza cambiar el binding:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" tracking reconcile-result "<project-root>" --task TASK-001 --anchor-sync-id SYNC-001 --result succeeded --authorized-by-role delivery-owner --authorized-on 2026-08-25 --external-id "10001" --external-key "DEMO-7" --url "https://example.atlassian.invalid/browse/DEMO-7" --remote-status "To Do" --observed-correlation-marker "LKS-SDD-PROJECT: <project_id>; TASK: TASK-001" --observed-projection-fingerprint "<anchor-or-current-projection-fingerprint>" --date 2026-08-25 --apply --json
```

El ancla debe ser exactamente `Last operation` y estar cerrada; un recibo aún `authorized` no sirve. Para `succeeded`, la huella observada debe coincidir con la del ancla o con la proyección local actual. Si coincide con el ancla pero el plan actual ya tiene otra huella —o aún no puede proyectarse— se conserva el hecho remoto y el mapping queda `out-of-sync`, no falsamente sincronizado.

Los resultados actualizan únicamente `ART-TRACKING` y su índice; nunca cambian por sí solos TASK, AUTH o evidencia. Con mapping sincronizado y un hecho local durable, el reporting usa `preview-event`, `authorize-event`, ejecución Rovo separada y `record-event-result`; un resultado incierto se resuelve mediante `reconcile-event`. Con mappings o recibos durables, 0.15.0 bloquea cambiar/abandonar el binding y no ofrece `detach`/`rebind`.

La confirmación del plan, la autorización, la preparación, los checkpoints y las transiciones que escriben usan preview, hash y apply explícito. El apply de preparación sincroniza las tareas seleccionadas a `in-progress`, crea `EXEC-###` y un checkpoint inicial; no crea commit. La verificación G3/G4 debe vincularse a revisión, árbol, build, artefactos y entorno. Ningún comando de validación autoriza merge o despliegue.

## Corte histórico de contrato de proyecto 1.x

1.0 valida únicamente `schema_version: 1.5` y `method_version: 1.5.0`. Compruebe el corte y la procedencia histórica sin escribir:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" doctor "<project-root>" --quick --view audit --json
python "<plugin-root>\scripts\lks_sdd.py" validate-project "<project-root>"
python "<plugin-root>\scripts\lks_sdd.py" status "<project-root>" --view audit --json
```

Los paquetes 1.x no tenían comando `migrate`. La versión 2 incorpora la ruta
oficial explícita 1.5→2.0, descrita en [V2-MIGRATION.md](V2-MIGRATION.md); los demás
orígenes siguen fallando cerrados. Un proyecto 1.5 puede conservar su valor
histórico de `plugin_version`; el runtime activo se presenta por separado.

## Piloto y distribución

El ejemplo debe seguir bloqueado porque no contiene muestra, aliases, responsables, canal confidencial, checksum ni rollback confirmado:

```powershell
python scripts\manage_pilot.py validate-config pilot\pilot-config.example.json
```

El resultado esperado es `blocked` con código `3`. No convierta ese estado en una evidencia de piloto ejecutado. El piloto es opcional para stable y no sustituye la aprobación del responsable. El empaquetado, publicación, instalación y activación requieren autorizaciones separadas y se realizan únicamente desde un commit de release limpio.

## Cierre obligatorio

Antes del cierre 1.0 ejecute además:

```powershell
python -X utf8 tests\run_unit_tests.py --module test_product_experience_v015
python -X utf8 scripts\benchmark_experience.py --json
```

El primero cubre comprensión management, lifecycle de problemas, autorización vigente, alcance local, doctor, caché y matriz de mutaciones. El segundo exige 13 tareas, 420 relaciones, management JSON menor de 8 KB, status menor de 5 s y reducción administrativa mínima del 50 % frente a 0.14.2.

Antes de entregar un cambio:

```powershell
git diff --check
git status --short
git diff --stat
```

Revise el diff completo, diferencie gates ejecutados de canales `not-run` y no cree commit, etiqueta, publicación o instalación salvo autorización separada.

## Evidencia 0.17, integración y benchmark

```powershell
python -X utf8 scripts\validate_fixture_manifest.py --json
python -X utf8 tests\run_unit_tests.py --module test_validation_evidence_v016
python -X utf8 tests\run_unit_tests.py --module test_fullstack_integration_contract_v017
python -X utf8 scripts\benchmark_experience.py --iterations 5 --json
python -X utf8 scripts\validate_plugin_contract.py .
```

La suite focalizada 0.17 contiene diez casos: falso positivo por componentes, integración real, backend-only, frontend-only, slice mixto, mock funcional, doble OIDC controlado, historia/reconciliación, atomicidad y determinismo. El perfil `WEB-FASTAPI-REACT-KEYCLOAK-PG` 2.1 fue promocionado a `active` únicamente después de ejecutar con Docker `GATE-BROWSER-FULLSTACK-E2E` y registrar una certificación exacta nueva. Cualquier cambio posterior en sus entradas certificadas exige recertificación y debe volver a fallar de forma cerrada mientras falte.

Antes de empaquetar, ejecute también todos los tiers, los evals y los gates de perfiles. Construya dos veces desde el mismo commit limpio y compare hashes; extraiga después el ZIP en un directorio temporal, valide el manifest y las seis skills y ejecute una instalación limpia aislada, sin modificar la instalación activa.
