# Validación local

Ejecute las comprobaciones desde la raíz del repositorio con Python 3. Las rutas a las herramientas de sistema se resuelven desde `CODEX_HOME` cuando está definido y, en caso contrario, desde el perfil de usuario; no dependen de una cuenta personal concreta.

```powershell
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$quickValidate = Join-Path $codexRoot "skills\.system\skill-creator\scripts\quick_validate.py"
$validatePlugin = Join-Path $codexRoot "skills\.system\plugin-creator\scripts\validate_plugin.py"
$validationDate = Get-Date -Format "yyyy-MM-dd"

python $quickValidate skills\lks-sdd-help
python $quickValidate skills\lks-sdd-define
python $quickValidate skills\lks-sdd-assess-readiness
python $quickValidate skills\lks-sdd-implement
python $quickValidate skills\lks-sdd-verify
python $quickValidate skills\lks-sdd-adopt-existing
python $validatePlugin .
python scripts\validate_reference_profile.py
python scripts\run_reference_profile_gate.py --runtime docker --containers
python scripts\validate_plugin_contract.py .
python scripts\validate_fixture_manifest.py .
python -m unittest discover -s tests -p "test_*.py" -v
python tests\run_evals.py
python scripts\run_quality_harness.py --channel candidate --date $validationDate --baseline quality\baselines\v0.6.1.json --include-complete-profile
```

`validate_plugin_contract.py` comprueba manifiesto, coherencia dinámica de versión con changelog y nota de release, seis skills, ausencia de componentes fuera de alcance, hashes de las cinco fuentes canónicas y recursos declarados. `validate_reference_profile.py` comprueba el contrato y el lock H0. `validate_fixture_manifest.py` bloquea altas no declaradas y deriva de los fixtures sintéticos. El harness M4 vuelve a ejecutar las comprobaciones automatizables, calcula umbrales y compara contra la baseline; use `--include-complete-profile` para incorporar también Docker en su reporte. El gate completo requiere Docker y red, levanta servicios temporales y siempre ejecuta `compose down --volumes`.

El reporte candidate conserva como `not-run` cualquier canal semántico, humano, de activación, revisión documental o piloto para el que no exista evidencia. Esos pendientes pueden ser opcionales para candidate si así lo declara `quality/catalog.json`, pero son obligatorios para `stable`. `--observations` solo aporta resultados reales y saneados a `activation` y `document-review`; el harness actual no dispone de contrato ni importador de resultados para `definition-conversation`, que permanece siempre `not-run` y bloquea `stable`. Si falta cualquier canal requerido, el harness devuelve `incomplete` con código `3`; nunca lo presenta como superado.

## Infraestructura M5 y empaquetado

La configuración de ejemplo debe devolver `blocked` con código `3`: demuestra que no puede arrancar sin muestra, aliases, responsables, canal confidencial, checksum y rollback.

```powershell
python scripts\manage_pilot.py validate-config pilot\pilot-config.example.json
```

El empaquetado real se valida después de confirmar el commit de release. Para el gate publicable se crea un checkout dedicado del commit exacto: el harness rechazará cualquier archivo no versionado preexistente, incluso ignorado, además de diferencias entre `HEAD`, índice y bytes reales. El builder fallará deliberadamente sobre un working tree sucio o si el SHA no coincide con `HEAD`:

```powershell
$releaseVersion = "0.7.0"
$releaseDate = "2026-08-20"
$sourceCommit = (git rev-parse HEAD).Trim()
$packageOutput = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion-validation"
$qualityReport = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion-$sourceCommit-quality.json"
$releaseCheckout = Join-Path ([System.IO.Path]::GetTempPath()) "lks-sdd-$releaseVersion-$sourceCommit-validation-source"

if (Test-Path -LiteralPath $releaseCheckout) { throw "El checkout dedicado ya existe." }
git worktree add --detach $releaseCheckout $sourceCommit

Push-Location $releaseCheckout
try {
  python scripts\run_quality_harness.py --channel candidate --date $releaseDate --baseline quality\baselines\v0.6.1.json --include-complete-profile --output $qualityReport
  python scripts\build_candidate_package.py --date $releaseDate --source-commit $sourceCommit --quality-report $qualityReport --output $packageOutput
} finally {
  Pop-Location
}
```

La carpeta de salida y el reporte deben no existir y quedar fuera del repositorio. La atestación se captura antes de ejecutar los checks, por lo que sus artefactos posteriores no cambian retroactivamente el estado inicial; no reutilice ese checkout para obtener otra atestación sin devolverlo primero a un estado nuevamente vacío y verificable. El reporte 1.1 debe acreditar el mismo commit, árbol `clean`, gate candidate superado y baseline 0.6.1. El builder vuelve a validar el esquema y los hashes comprometidos, los inventarios y evidencias, la consistencia de las métricas y la comparación con la baseline; un reporte generado sobre un árbol `dirty` o una declaración de éxito autocontenida e inconsistente se rechaza. Para la puerta de publicación deben realizarse dos builds y compararse como indica `docs/DISTRIBUTION.md`; una sola ejecución solo comprueba que el builder acepta ese checkout.

## Proyecto consumidor

Defina una ruta externa al proyecto consumidor ya inicializado:

```powershell
$consumerRoot = Resolve-Path "..\consumer-project"

$pluginRoot = Resolve-Path "."
python "$pluginRoot\scripts\lks_sdd.py" validate-project $consumerRoot
python "$pluginRoot\scripts\lks_sdd.py" validate-spec $consumerRoot
python "$pluginRoot\scripts\lks_sdd.py" traceability $consumerRoot --increment INC-001 --phase preimplementation
python "$pluginRoot\scripts\lks_sdd.py" assess-readiness $consumerRoot --increment INC-001
```

La adopción usa los subcomandos `adopt-inspect`, `adopt-validate` y `adopt-materialize` del dispatcher, en ese orden. La migración usa `python "$pluginRoot\scripts\lks_sdd.py" migrate $consumerRoot --target-schema 1.1 --dry-run`. Si `human_review_required` contiene entradas, `--apply` falla siempre antes de crear el backup o escribir: resuelva cada entrada listada en los Markdown canónicos 1.0, valide el origen y repita el dry-run hasta obtener una lista vacía. La `Identity` agregada 1.0 se materializa aparte como identidad, seguridad y privacidad `pending`, sin referencias inferidas y con motivo; no impide aplicar una migración cuya lista esté vacía, pero sí bloquea readiness hasta resolverse en 1.1. Solo entonces aplique con backup externo, autorización y hash coincidente. Las vistas cliente se previsualizan con el subcomando `client-view --dry-run` y se escriben solo con autorización y hash coincidente.

Los códigos `0`, `2` y `3` significan respectivamente éxito/listo, contrato inválido o readiness bloqueado. Un resultado listo no autoriza implementación; la confirmación de la persona usuaria sigue siendo independiente.
