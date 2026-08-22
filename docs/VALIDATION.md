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

`--allow-unvalidated` comprueba la estructura de los diez perfiles, incluidos los candidate; no los presenta como soportados. `validate_plugin_contract.py` exige además que cada perfil `active` tenga una certificación exacta vigente, valida catálogo, drivers, scaffolds y locks, las siete fuentes canónicas, el contrato 1.3, las seis skills y la ausencia de componentes fuera de alcance.

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

El harness conserva su formato de reporte 1.1 y reejecuta un perfil completo representativo; el contrato del plugin valida la cobertura exacta de todos los perfiles active. `not-run` y `skipped` nunca cuentan como `passed`. Los canales semánticos, humanos, de activación, revisión documental y piloto pueden ser opcionales para candidate según `quality/catalog.json`, pero son obligatorios para stable.

El reporte publicable debe crearse desde un checkout dedicado, limpio y sin archivos no versionados preexistentes, incluso ignorados. Una ejecución sobre el árbol de desarrollo es diagnóstico, no atestación publicable. El procedimiento reproducible y el doble build están en `docs/DISTRIBUTION.md`.

## Validación de un proyecto consumidor 1.3

`<plugin-root>` y `<project-root>` son ubicaciones distintas:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" validate-project "<project-root>" --json
python "<plugin-root>\scripts\lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation --json
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" validate
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" board
python "<plugin-root>\scripts\lks_sdd.py" planning "<project-root>" --increment INC-001 assess --json
python "<plugin-root>\scripts\lks_sdd.py" planning "<project-root>" --increment INC-001 next --json
python "<plugin-root>\scripts\lks_sdd.py" assess-readiness "<project-root>" --increment INC-001 --task TASK-001 --json
python "<plugin-root>\scripts\lks_sdd.py" implement "<project-root>" --increment INC-001 --task TASK-001 --dry-run --json
python "<plugin-root>\scripts\lks_sdd.py" continuity "<project-root>" resume --json
python "<plugin-root>\scripts\lks_sdd.py" verify "<project-root>" --increment INC-001 --task TASK-001 --execution-id EXEC-001 --plan --json
python "<plugin-root>\scripts\lks_sdd.py" tasks "<project-root>" transition --task TASK-001 --to blocked --reason "PROB-001 pendiente" --actor delivery-owner --date 2026-08-22 --blocker PROB-001 --preview --json
```

La confirmación del plan, la autorización, la preparación, los checkpoints y las transiciones que escriben usan preview, hash y apply explícito. El apply de preparación sincroniza las tareas seleccionadas a `in-progress`, crea `EXEC-###` y un checkpoint inicial; no crea commit. La verificación G3/G4 debe vincularse a revisión, árbol, build, artefactos y entorno. Ningún comando de validación autoriza merge o despliegue.

## Migraciones

Las migraciones son de un salto:

```powershell
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.1 --dry-run
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.2 --dry-run
python "<plugin-root>\scripts\lks_sdd.py" migrate "<project-root>" --target-schema 1.3 --dry-run
```

1.0 → 1.1 bloquea apply si existe cualquier `human_review_required`; resuelva el Markdown 1.0 de origen y repita el preview. 1.1 → 1.2 crea gobierno, arquitectura, planes, tareas y bindings pendientes. 1.2 → 1.3 añade cobertura, huellas, autorizaciones y ejecuciones vacías sin inventar decisiones, tareas, avance o evidencia. Cada apply exige backup externo, autorización y hash exacto; el rollback utiliza el manifiesto de esa operación.

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
