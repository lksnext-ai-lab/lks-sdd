# Validación y publicación

## Regla operativa

Este plugin se publica con una única puerta técnica pequeña. No existe una matriz de
certificación, una campaña Docker, una baseline de rendimiento ni una batería amplia
como requisito de release.

La puerta estable ejecuta solo cuatro comprobaciones:

1. La aprobación explícita de la versión.
2. La integridad estática: fixtures, contrato del plugin y estructura de perfiles.
3. Catorce pruebas de humo que cubren contrato, aislamiento, migración, planificación,
   tracking, evidencia, integración y adopción.
4. La regresión real de rutas largas de Windows.

La estructura de perfiles se valida porque forma parte del paquete; no se exige
certificación, caducidad, Docker ni recertificación de perfiles.

La batería mantenida contiene únicamente los módulos que aportan estas pruebas de
humo, sus fixtures compartidos y la regresión Windows. Se han retirado los módulos
fragmentados y las pruebas históricas que no forman parte de este contrato de
publicación.

Las suites extensas, evals conversacionales, benchmarks, pilotos y aceptación de host
no forman parte de la publicación ni se mantienen como batería paralela.

## Pull request

La comprobación automática de una PR es solo el contrato del plugin:

```powershell
python -B -X utf8 scripts\validate_plugin_contract.py .
```

## Release estable

Ejecute una vez desde un checkout limpio del commit ya integrado. El comando no acepta
un árbol con cambios ni reutiliza un informe existente.

```powershell
$releaseDate = Get-Date -Format 'yyyy-MM-dd'
$releaseGate = Join-Path $env:TEMP 'lks-sdd-release-gate.json'
python -B -X utf8 scripts\run_release_gate.py `
  --channel stable `
  --date $releaseDate `
  --release-approval quality\release-approval-v2.0.2.json `
  --output $releaseGate
```

Un resultado `passed` acredita únicamente las cuatro comprobaciones anteriores. No
acredita aceptación humana, uso real de Copilot/Codex, navegación, generación visual,
piloto, Jira o despliegue.

## Un único build

Tras superar el gate, cree una sola vez el conjunto de artefactos y valide su ZIP
Copilot. El builder genera `package-integrity.json`, manifiestos y `SHA256SUMS`; lee
los bytes del commit exacto, exige la misma versión, fecha y revisión acreditadas, y
rechaza secretos, enlaces y fuentes fuera del repositorio.

```powershell
$sourceCommit = git rev-parse HEAD
$artifacts = Join-Path $env:TEMP 'lks-sdd-release'
python -B -X utf8 scripts\build_candidate_package.py `
  --date $releaseDate `
  --source-commit $sourceCommit `
  --quality-report $releaseGate `
  --output $artifacts

python -B -X utf8 scripts\validate_copilot_package.py `
  (Join-Path $artifacts 'lks-sdd-copilot-plugin-v2.0.2.zip')
```

La automatización de etiqueta valida además una extracción limpia de los ZIP de plugin
y marketplace. No se instala ni activa un plugin personal, no se registran identidades
y no se realizan operaciones sobre proyectos consumidores.

## Diagnóstico opcional

Para investigar un defecto concreto, ejecute únicamente el test o el validador que lo
observa. No use suites globales como paso rutinario de publicación. Los contratos de
migración y consultas v2 están documentados en
[V2-MIGRATION.md](V2-MIGRATION.md) y [PROJECT-QUERY.md](PROJECT-QUERY.md).
