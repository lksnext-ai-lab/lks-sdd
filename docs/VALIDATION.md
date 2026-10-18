# Validación y publicación

## Regla operativa

Este plugin se publica con una única puerta técnica pequeña. No existe una matriz de
certificación, una campaña Docker, una baseline de rendimiento ni una batería amplia
como requisito de release.

La puerta estable ejecuta solo cuatro comprobaciones:

1. La aprobación explícita de la versión.
2. La integridad estática: fixtures y contrato del plugin.
3. Catorce pruebas de humo que cubren declaración tecnológica, migración de legado,
   continuidad SPEC/PLAN/TASK, autoridad, guard estricto y recorridos v3 de equipo,
   propuesta, calidad, migración y aceptación separada.
4. La regresión real de rutas largas de Windows.

La batería de desarrollo incorpora regresiones focales de v2 y v3, incluido el
cambio de runtime fijado. No se convierten todas en controles obligatorios de cada
publicación: las catorce pruebas de humo y Windows siguen siendo la puerta técnica.

Los checks técnicos independientes del gate se ejecutan en paralelo para reducir el
tiempo activo del runner. Esta concurrencia no elimina checks, no acorta sus timeouts
ni cambia los estados que bloquean una release.

Las suites extensas, evals conversacionales, benchmarks, pilotos y aceptación de host
no forman parte de la publicación ni se mantienen como batería paralela.
La observación de uso de v3 se prepara una sola vez con
[su protocolo](V3-HOST-ACCEPTANCE.md); no se presenta como superada por este gate.

4.0.1 añade regresiones focales de mantenimiento por lotes (`test_store_compaction`,
`test_store_compaction_recovery`, `test_store_maintenance_batches`) y conserva las
pruebas de lector ZIP y mantenimiento /1 afectadas. El inspector JSON reutiliza
los ensayos congelados de V401-01 por igualdad de algoritmo; no se repiten grandes
casos cuando solo cambia su ubicación. La única campaña autorizada de 800 MB usa
`measure_store_compaction_v401.py`, candidato congelado, métricas del proceso,
interrupción/recuperación y restauración independiente. Es evidencia específica
del parche, no una nueva batería ni un requisito para cada publicación.

## Pull request

La comprobación automática de una PR es solo el contrato del plugin:

```powershell
python -B -X utf8 scripts\validate_plugin_contract.py .
```

## Desarrollo del recorrido integral

La corrección focal de coste/transporte verifica `CaptureTests`,
`ReceiptTransportTests`, `MeasurementAffinityTests` y `test_performance_control`,
sin repetir sus fixtures integrales ni S8. El control previo recalcula dispersión
y sobrecoste desde muestras brutas, rechaza cambios de fuente/método/input,
ventanas caducadas e aislamiento incompleto. Es un control estricto histórico, no una
autorización ni un lanzador. La decisión posterior de aceptar variabilidad retira
su exigencia de estabilidad como admisión; fuente, identidad, trabajo equivalente
y garantías siguen siendo obligatorios. No se modifica el driver histórico
ni se amplía la puerta estable. Véase el [resultado y sus límites](plans/lks-sdd-v4/RESULTS-V4-17-EFFICIENCY.md).
La revisión posterior observa clases y disponibilidad de CPU mediante CPU Sets;
evita seleccionar una CPU por su posición numérica. La política optativa del job
de medida puede fijar Above Normal y HighQoS del worker antes del arranque, sin
cambiar ajustes globales ni el núcleo del plugin. El ensayo histórico de 30.000 elementos
exigía calentamiento con trabajo idéntico y tres muestras CPU/pared estables ≤5 %.
En ese ensayo no se comparaban variantes si fallaba el calentamiento. Los cambios
no lograron estabilidad. La política vigente acepta medir con ruido declarado,
sin buscar una ventana favorable ni relajar umbrales o garantías;
[decisión y límites](plans/lks-sdd-v4/DECISION-SHARED-HOST-MEASUREMENT.md).

La corrección final de rendimiento mantiene las lecturas y fronteras frescas:
`runtime_doctor` recorre cada cadena de ancestros sin reconstruir sus subcadenas;
`usage_bundle.no_links` usa atributos nativos nuevos y conserva el fallback y los
rechazos de reparse points. `FreshPathObservationTests` comprueba modificaciones,
ausencias, inventario inesperado, ancestros, junction real y errores de observación.
La serie final S8 y el sobrecoste optativo tienen evidencia separada; estas
optimizaciones no cachean confianza ni amplían la puerta estable.

V4-14 añade `test_v4_compatibility`: corte explícito desde un consumidor sintético
3.4.3, conservación del trabajo abierto, rollback, recuperación de journal y
rechazo ante cambios posteriores. V4-15 consolida evidencia vigente y V4-16
comprueba paquetes de desarrollo reproducibles desde extracciones limpias.
El cierre ampliado 4.0 vincula los controles técnicos a la huella extraída exacta,
incluidos los objetos ZIP, su mantenimiento y la integración funcional F8 sobre
la entrada B congelada. Reutiliza negativos no afectados por hash y conserva los
límites de las mediciones históricas. Los controles técnicos del gate se ejecutan
como comprobaciones de desarrollo; la aprobación estable y el checkout limpio
siguen pendientes hasta la autorización separada de versión e integración.
La [guía de candidata](V4-CANDIDATE.md) distingue estos resultados de instalación,
aceptación de host y publicación; no amplía la puerta estable.

V4-11 adapta las seis skills y añade rutas de las operaciones compuestas a
`test_v3_instruction_routing`: recursos por evento, recarga de huellas, metadatos,
enlaces y ejecución desde ambos adaptadores. Su [resultado](plans/lks-sdd-v4/RESULTS-V4-11.md)
reutiliza los controles no afectados y conserva pendientes de host y sobrecoste.

V4-10 añade `test_v4_maintenance`: comparación focal con 3.4.3 de corrección cubierta,
cambio de acuerdo, nueva capacidad y permiso vencido. Reutiliza los guards vigentes;
su [resultado](plans/lks-sdd-v4/RESULTS-V4-10.md) no acredita ahorro integral ni amplía
la puerta de publicación.

V4-07A añade `test_work_activity`: canal optativo separado, señales/JSON,
interrupción cooperativa, efectos durables, reintento y recuperación. Su aceptación
y límites constan en [los resultados](plans/lks-sdd-v4/RESULTS-V4-07A.md);
no amplía la puerta estable ni acredita ahorro de tarea completa o H2.

Las pruebas focales de `tests/test_v31_review.py` comprueban decisiones agrupadas,
revisión conjunta, encargos, correcciones, excepciones y orientación de solo lectura.
`tests/test_v3_distribution.py` comprueba adopción 3.0 → 3.1 con runtime fijado y
rollback. Son comprobaciones de desarrollo de este cambio; no acreditan aceptación
humana de Codex/Copilot ni modifican la puerta de publicación descrita aquí.
La implementación y su evidencia se documentan en
[el plan de revisión integral](plans/integral-review/PLAN.md).

Para cambios de presentación y selección de instrucciones se añaden las regresiones
focales `test_v3_decision_presentation` y `test_v3_instruction_routing`. Comprueban
prosa literal, borradores, decisiones antiguas, caducidad del contenido mostrado,
composición, recogida de evidencia por petición y ejecución desde ambos paquetes.
V4-03 añade `test_v4_cli_presentation`: modo operativo explícito, matriz de 24
combinaciones de opciones, exportación íntegra, recibos, bloqueos, efectos tras
error de salida, recuperación y exportación Windows larga con Unicode/espacios.
La interfaz y sus límites están en [CLI-PRESENTATION.md](CLI-PRESENTATION.md).
V4-05A integra el recorrido provisional descrito en [WORK-PREPARE.md](WORK-PREPARE.md).
La regresión pública de `test_diagnostic_capture` conserva el resumen en lista y el
contenido del reporte sin escrituras de consulta. `test_v3_instruction_routing`
comprueba los mismos bytes de estas instrucciones en ambos adaptadores. El recorrido
S1 desde el paquete de desarrollo comprueba prueba real, evidencia, verificación,
cierre y conservación; no sustituye la pareja H2 en chats nuevos del host.
Estas pruebas de desarrollo no amplían la puerta estable ni acreditan ahorro de
tarea completa o aceptación humana de un host.
Los recorridos de revisión, equipo, calidad, integración y distribución se mantienen.
La corrección de antecedentes migrados añade `test_v3_historical_presentation`:
procedencia recuperable, responsables literales, pendientes, consultas directas,
adjuntos, propietarios actuales estrictos y caducidad de receipts y guards. Su
[cobertura](HISTORICAL-TASK-PRESENTATION.md) no amplía el gate estable.
Las comprobaciones y límites quedan en
[la cobertura de esta implementación](plans/specification-review-presentation/IMPLEMENTATION.md).
La comparación de instrucciones se reproduce con
`python -B -X utf8 tests/measure_v3_instruction_context.py`; registra caracteres,
lecturas previstas y huellas, sin presentarlos como tokens facturados ni coste total.

## Release estable

El diagnóstico de uso se comprueba con `test_usage_observation`,
`test_usage_findings`, `test_usage_report`, `test_usage_bundle` y
`test_usage_workflow`. Incluyen límites, procedencia, siete reglas, conservación,
aislamiento de decisiones, guard fresco, exportación e inspección independiente.
Son regresiones de desarrollo; no amplían la puerta estable de catorce pruebas.
La cobertura y medición focal se conservan en
[el seguimiento](plans/plugin-improvement-feedback/IMPLEMENTATION.md).

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
  --release-approval quality\release-approval-v4.0.1.json `
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

La captura explícita V4-04 se verifica de forma focal, junto a los adaptadores que
conservan diagnóstico y a los helpers Windows existentes:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_diagnostic_capture
python -B -X utf8 tests/run_unit_tests.py --module test_usage_observation --module test_usage_bundle
python -B -X utf8 tests/run_unit_tests.py --module test_v3_instruction_routing --test test_both_packages_execute_the_same_decision_view
python -B -X utf8 tests/run_unit_tests.py --module test_windows_long_paths
```

El contrato y los límites están en [DIAGNOSTIC-CAPTURE.md](DIAGNOSTIC-CAPTURE.md).
Estas pruebas no acreditan el ahorro integral ni la aceptación de un host real.

Para investigar un defecto concreto, ejecute únicamente el test o el validador que lo
observa. No use suites globales como paso rutinario de publicación. Los contratos de
migración y consultas v2 están documentados en
[V2-MIGRATION.md](V2-MIGRATION.md) y [PROJECT-QUERY.md](PROJECT-QUERY.md).

## Retención operativa

La corrección focal de aprobaciones se reproduce con:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v3_approval_performance
python -B -X utf8 tests/measure_approval_performance.py `
  --sizes 100:5 500:15 1500:35 --repetitions 4 --cooldown 10 `
  --output output/approval-performance/measurement.json
python -B -X utf8 tests/measure_approval_performance.py `
  --sizes 1500:35 --repetitions 4 --order alternating --cooldown 10 `
  --phases shared-inventories --timeout 3600 `
  --output output/approval-performance/shared-inventories.json
```

La iteración rc.3 añade comparación secuencial con rc.2 y CLI completo desde
el ZIP preparado, sin instalarlo. Se reproduce con `tests/measure_approval_rc3.py`
y `tests/check_approval_cli_hosts.py`, como indica la cobertura enlazada abajo.
Los informes finales quedan fuera del runtime para preservar los bytes medidos;
la memoria comprometida del job se distingue del working set. La aceptación
conversacional de host continúa pendiente.

Su [cobertura, presupuestos y límites](APPROVAL-PERFORMANCE.md) y la evidencia
antes/después son específicos de esta corrección. No amplían el gate estable ni
acreditan ahorro de tokens o aceptación de host.

La corrección de crecimiento documental tiene una reproducción temporal y pruebas
focales, sin añadir controles al gate de publicación:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_document_storage
python -B -X utf8 tests/run_unit_tests.py --module test_v3_efficiency
```

El formato, compatibilidad, mediciones y condiciones de compactación separada se
documentan en [almacenamiento documental](DOCUMENT-STORAGE.md).

La acumulación de controles se diagnostica sin mutación:

```powershell
python -B -X utf8 scripts\v2_cli.py retention-status <project-root> --json
```

El archivado requiere una previsualización y la autorización exacta de esa
previsualización. Solo afecta registros operativos cerrados:

```powershell
python -B -X utf8 scripts\v2_cli.py retention-compact <project-root> `
  --at 2026-01-02T00:00:00+00:00 --json
python -B -X utf8 scripts\v2_cli.py retention-compact <project-root> --apply `
  --at 2026-01-02T00:00:00+00:00 --authorize <PREVIEW_HASH> --json
```

Los comandos de compactación anteriores describen el runtime v2 publicado, no
un canal de escritura del candidato actual. En este candidato se conservan
consulta y recuperación; continuar trabajo exige el corte v3.1 documentado en
[V3-MIGRATION](V3-MIGRATION.md). La limpieza de historia existente es otro encargo.

La operación histórica es reversible mediante `retention-restore --id AUTH-001` (o el
identificador operativo correspondiente), también con preview y autorización
exacta. EVID y los documentos normativos no son candidatos.

## Consulta compuesta V4-05

La preparación informativa se comprueba frente a las consultas individuales y
con negativos de autoridad, contrato incompleto, runtime y cambios concurrentes:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_work_prepare
python -B -X utf8 tests/run_unit_tests.py --module test_v3_approval_performance --module test_v3_instruction_routing --module test_usage_observation --module test_usage_bundle
```

[WORK-PREPARE.md](WORK-PREPARE.md) delimita la operación. Las pruebas de paquete
son sintéticas; no acreditan instalación, uso conversacional ni ahorro integral.


La corrección Git/Windows de V4-05 añade:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_windows_git_paths
```

Comprueba inventario, exclusiones, prefijos anidados, referencia `.git`, rama/base,
alias, propiedad y límites de configuración antes de repetir el recorrido público
con runtime/consumidor largo de `test_work_prepare`. No amplía el gate de release ni
acredita todos los volúmenes o configuraciones de Windows.

## Operaciones compuestas V4-06

La continuación y el registro de resultados conservan las transacciones del núcleo,
las comprobaciones vigentes de cada etapa y sus recibos separados:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_work_operations --module test_work_operation_guards --module test_work_operation_recovery
```

Incluyen pruebas realmente ejecutadas sobre `app.py`, revisión independiente,
recepción ajena, falta de revisión, permisos revocados, calidad obligatoria,
evidencia fallida/antigua, cambios de sujeto/alcance/base, intención distinta,
fallo de entrega, interrupción material en cada etapa, recuperación y reversión
explícitas, reintentos sin duplicados y conservación de trabajo posterior.
[WORK-OPERATIONS.md](WORK-OPERATIONS.md) explica el contrato y los límites.
No amplían el gate estable de cuatro comprobaciones y catorce smoke tests.
La pareja S8 temprana es descriptiva; H2, ahorro de tokens y aceptación final
permanecen separados de estas comprobaciones técnicas.

## Regresiones de reutilización y continuidad de 4.0

`test_migration_evaluation_reuse` y `test_git_observation_scope` comprueban alcance
inmutable, presupuesto, cambios de fuentes, aislamiento y lecturas físicas tras
la preparación. `test_work_continuity` contiene siete casos propios de consulta
sin escrituras, identidad explícita, base cambiada, bloqueo, proceso nuevo y pausa.
Se reutiliza la cobertura del núcleo que no cambia; los intentos cancelados,
timeouts y ventanas de medición concurrentes conservan su estado y evidencia.
Estas regresiones no amplían la puerta estable ni acreditan H2, Copilot real,
percepción humana, ahorro facturado o aceptación completa de 4.0.
