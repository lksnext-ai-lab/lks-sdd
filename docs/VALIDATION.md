# Validación y publicación

## Regla operativa

Este plugin se publica con una única puerta técnica pequeña. No existe una matriz de
certificación, una campaña Docker, una baseline de rendimiento ni una batería amplia
como requisito de release.

La puerta estable ejecuta solo cuatro comprobaciones:

1. La aprobación explícita de la versión.
2. La integridad estática: fixtures y contrato del plugin.
3. Catorce pruebas de humo que cubren contrato, aislamiento, migración, planificación,
   tracking, evidencia, integración y adopción.
4. La regresión real de rutas largas de Windows.

La batería mantenida contiene únicamente los módulos que aportan estas pruebas de
humo, su regresión v2 y la regresión Windows. Se han retirado los módulos fragmentados y las pruebas históricas que no forman parte de este contrato de publicación.

Los checks técnicos independientes del gate se ejecutan en paralelo para reducir el
tiempo activo del runner. Esta concurrencia no elimina checks, no acorta sus timeouts
ni cambia los estados que bloquean una release.

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

El camino normal es ejecutar manualmente `stable-preflight` dentro de **Actions →
quality** sobre `main`. El job ejecuta el preflight ligero, el gate estable y un
único build de todos los paquetes de distribución; valida los paquetes Copilot,
plugin y marketplace, y publica `stable-preflight-evidence` durante 30 días. Solo un
informe de readiness y gate superados permite crear la etiqueta; el job no crea ni
publica nada.

La instalación de dependencias puede restaurar la caché pip ligada a
`requirements-runtime.txt`, pero siempre ejecuta `pip install --require-hashes`. La
caché no acredita una release ni contiene paquetes generados, candidates o evidencia.

La evidencia incluye la procedencia del run manual, vinculada a su SHA, rama, versión
e intento. Al recibir una etiqueta stable, `quality` reutiliza ese candidate solo si
el run correcto, su procedencia, readiness, gate, manifiesto, checksums, paquetes y
sección acreditada del changelog acreditan el mismo SHA. Si falta esa evidencia, ejecuta el gate y
build completos y declara `revalidated-after-missing-preflight`. Una evidencia
presente pero inválida, ambigua o no descargable bloquea la etiqueta: nunca se acepta
ni se reconstruye silenciosamente.

Para diagnosticar un bloqueo sin iniciar CI, puede ejecutar solo el preflight local:

```powershell
$releaseReadiness = Join-Path $env:TEMP 'lks-sdd-release-readiness.json'
python -B -X utf8 scripts\release_readiness.py `
  --channel stable `
  --output $releaseReadiness
```

```powershell
$releaseDate = Get-Date -Format 'yyyy-MM-dd'
$releaseGate = Join-Path $env:TEMP 'lks-sdd-release-gate.json'
python -B -X utf8 scripts\run_release_gate.py `
  --channel stable `
  --date $releaseDate `
  --release-approval quality\release-approval-v2.1.3.json `
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

python -B -X utf8 scripts\validate_release_artifacts.py `
  --candidate $artifacts `
  --output (Join-Path $artifacts 'release-package-validation.json')
```

El preflight y la ruta de reconstrucción de la etiqueta validan además una extracción
limpia de los ZIP de plugin y marketplace. La ruta reutilizada exige el informe
acreditado por esa misma validación. No se instala ni activa un plugin personal, no se
registran identidades y no se realizan operaciones sobre proyectos consumidores.

## Promoción a draft release

El workflow `release-draft` se activa después de una ejecución correcta de `quality`
sobre una etiqueta stable. Antes de solicitar aprobación de entorno, descarga el
artefacto de esa ejecución exacta y verifica gate, versión, SHA, manifiesto,
checksums, ZIP Copilot y referencia Copilot. La procedencia del candidate ya fue
verificada por la etiqueta; el draft no repite gate ni build. La promoción requiere
el entorno `release-draft` con revisores configurados fuera de este repositorio.

El único job con `contents: write` crea una draft y adjunta los assets ya acreditados.
No vuelve a ejecutar gate o build, no modifica tags y no publica la release. Una
release/draft existente bloquea el flujo para reconciliación humana.

## Observabilidad de release

El workflow `release-observability` se ejecuta después de un workflow `quality`
correcto sobre una etiqueta `v*`. Recopila los timestamps expuestos por GitHub
Actions para medir cola, dependencias, carga del artefacto y la ruta de validación.
Para una reutilización, registra resolución/verificación del preflight y declara
gate/build del tag como `not-run`; para una reconstrucción, conserva las métricas de
gate y build. El informe declara expresamente la revisión humana como `not-observed`:
no es una evidencia de aceptación ni un requisito superado.

También valida que la referencia GitHub declarada para Copilot en el catálogo del
commit etiquetado resuelva al mismo SHA. Esta comprobación es de observación y
trazabilidad; no crea ni modifica referencias remotas. Un fallo se muestra de forma
explícita en el workflow separado y conserva sus diagnósticos como artefacto.

Ejecute sus pruebas unitarias específicas al modificar el preflight u observadores:

```powershell
python -B -X utf8 tests\run_unit_tests.py `
  --module test_release_gate `
  --module test_release_readiness `
  --module test_release_observability `
  --module test_distribution_reference `
  --module test_draft_promotion `
  --module test_release_package_validation `
  --module test_preflight_provenance
```

## Diagnóstico opcional

Para investigar un defecto concreto, ejecute únicamente el test o el validador que lo
observa. No use suites globales como paso rutinario de publicación. Los contratos de
migración y consultas v2 están documentados en
[V2-MIGRATION.md](V2-MIGRATION.md) y [PROJECT-QUERY.md](PROJECT-QUERY.md).
