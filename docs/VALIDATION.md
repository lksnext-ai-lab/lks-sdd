# Validación local

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

`--allow-unvalidated` comprueba la estructura de los diez perfiles, incluidos los candidate; no los presenta como soportados. `validate_plugin_contract.py` exige además que cada perfil `active` tenga una certificación exacta vigente, valida catálogo, drivers, scaffolds y locks, mantiene por hash las siete fuentes canónicas, identifica separadamente la propuesta 1.4, valida el contrato 1.4, las seis skills y la ausencia de componentes fuera de alcance.

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

## Pruebas, evals y harness

```powershell
$validationDate = Get-Date -Format "yyyy-MM-dd"
python -m unittest discover -s tests -p "test_*.py" -v
python tests\run_evals.py
python scripts\run_quality_harness.py --channel candidate --date $validationDate --baseline quality\baselines\v0.6.1.json --include-complete-profile
```

Para aislar primero las regresiones 0.10.0:

```powershell
python -m unittest discover -s tests -p "test_task_tracking_v14.py" -v
python -m unittest discover -s tests -p "test_migration_v11.py" -v
python -m unittest discover -s tests -p "test_v06_quality.py" -v
python -m unittest discover -s tests -p "test_m5_pilot.py" -v
```

El harness conserva su formato de reporte 1.1 y reejecuta un perfil completo representativo; el contrato del plugin valida la cobertura exacta de todos los perfiles active. `not-run` y `skipped` nunca cuentan como `passed`. Los canales semánticos, humanos, de activación, revisión documental y piloto pueden ser opcionales para candidate según `quality/catalog.json`, pero son obligatorios para stable.

El reporte publicable debe crearse desde un checkout dedicado, limpio y sin archivos no versionados preexistentes, incluso ignorados. Una ejecución sobre el árbol de desarrollo es diagnóstico, no atestación publicable. Los tests sintéticos de tracking no ejecutan Rovo; `definition-conversation` y `pilot` conservan la evaluación humana y la interoperabilidad real Rovo/Jira como `not-run`. El procedimiento reproducible y el doble build están en `docs/DISTRIBUTION.md`.

## Validación de un proyecto consumidor 1.4

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
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" transition --task TASK-001 --to blocked --reason "PROB-001 pendiente" --actor delivery-owner --date 2026-08-22 --blocker PROB-001 --preview --json
```

La elección de tracking usa el mismo protocolo local preview/hash/apply. Los siguientes ejemplos utilizan datos sintéticos; sustituya el hash únicamente por el devuelto por la vista previa exacta:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode repository-only --decision ADR-001 --date 2026-08-25 --json
python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode repository-only --decision ADR-001 --date 2026-08-25 --apply --authorize "<mutation-hash>" --json

python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode jira-hybrid --decision ADR-002 --date 2026-08-25 --site "https://example.atlassian.invalid" --project DEMO --issue-type Task --json
python "<plugin-root>\scripts\lks_sdd.py" tracking configure "<project-root>" --mode jira-hybrid --decision ADR-002 --date 2026-08-25 --site "https://example.atlassian.invalid" --project DEMO --issue-type Task --apply --authorize "<mutation-hash>" --json
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

Los resultados actualizan únicamente `ART-TRACKING` y su índice; nunca cambian por sí solos el estado de `TASK-001`, AUTH, evidencia o `done`. La proyección solo admite `classification: internal`, `public` o `client`; rechaza una clasificación ausente/desconocida, `confidential` o `restricted`, secretos y datos personales detectables. `--site` y `--url` deben usar HTTPS sin credenciales, query ni fragmento; el site identifica solo el origen y la URL debe pertenecer al mismo origen y terminar en la key externa. Con mappings o recibos durables, 0.10.0 bloquea cambiar/abandonar el binding y no ofrece `detach`/`rebind`.

La confirmación del plan, la autorización, la preparación, los checkpoints y las transiciones que escriben usan preview, hash y apply explícito. El apply de preparación sincroniza las tareas seleccionadas a `in-progress`, crea `EXEC-###` y un checkpoint inicial; no crea commit. La verificación G3/G4 debe vincularse a revisión, árbol, build, artefactos y entorno. Ningún comando de validación autoriza merge o despliegue.

## Migraciones

Las migraciones son de un salto:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.1 --dry-run
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.2 --dry-run
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.3 --dry-run
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.4 --dry-run
```

1.0 → 1.1 bloquea apply si existe cualquier `human_review_required`; resuelva el Markdown 1.0 de origen y repita el preview. 1.1 → 1.2 crea gobierno, arquitectura, planes, tareas y bindings pendientes. 1.2 → 1.3 añade cobertura, huellas, autorizaciones y ejecuciones vacías sin inventar decisiones, tareas, avance o evidencia. 1.3 → 1.4 añade `ART-TRACKING` y su índice sin crear issues, ejecutar Rovo ni inventar confirmación; rechaza una `EXEC-###` no terminal y conserva byte a byte los `CKPT-###` históricos 1.3. Los checkpoints nuevos usan 1.4. Cada apply exige backup externo, autorización y hash exacto; el rollback utiliza el manifiesto de esa operación. La regresión debe confirmar también que el salto histórico 1.2 → 1.3 sigue generando schema 1.3, método 1.3.0 y plugin 0.9.1.

## Piloto y distribución

El ejemplo debe seguir bloqueado porque no contiene muestra, aliases, responsables, canal confidencial, checksum ni rollback confirmado:

```powershell
python scripts\manage_pilot.py validate-config pilot\pilot-config.example.json
```

El resultado esperado es `blocked` con código `3`. No convierta ese estado en una evidencia de piloto ejecutado. El empaquetado, publicación, instalación y activación requieren autorizaciones separadas y se realizan únicamente desde un commit de release limpio.

## Cierre obligatorio

Antes de entregar un cambio:

```powershell
git diff --check
git status --short
git diff --stat
```

Revise el diff completo, diferencie gates ejecutados de canales `not-run` y no cree commit, etiqueta, publicación o instalación salvo autorización separada.
