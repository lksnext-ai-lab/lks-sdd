# Harness de calidad M4

## Propósito

El harness integra FX-01–FX-45 históricos, el reporting Jira v0.11 FX-46–FX-51, la cobertura granular Entra v0.12 FX-52–FX-53, los perfiles OIDC simulados v0.13 en FX-54 y la verificación incremental reproducible v0.14 en FX-55. Cubre experiencia local sin Atlassian, hitos canónicos, comentario idempotente, una confirmación con recibos separados, workflow por IDs, reconciliación append-only, rechazo sin mutación de schemas de proyecto anteriores a 1.5, aplicabilidad visual por tarea, build estable, G4 no circular y CKPT/PROB consumibles. No convierte una prueba no ejecutada o saltada en un resultado satisfactorio.

FX-01, FX-20, FX-21, FX-36 y FX-53 conservan evaluación conversacional `not-run`. FX-45 y FX-51 mantienen la interoperabilidad real Rovo/Jira como piloto `not-run`; la interoperabilidad real Microsoft Entra también sigue `not-run` en los perfiles candidate. Los perfiles simulados declaran interoperabilidad externa `not-applicable`, no `passed`. Ninguna prueba offline sustituye estos resultados. El cierre estable puede basarse en una decisión agregada del responsable del proyecto sin transformar esos estados. El harness conserva como diagnóstico el corpus `quality/corpora/definition-v0.18.0.json`.

## Canales de evidencia

- `automated`: contratos 0.8/1.2, 0.9/1.3 y 0.10/1.4, inventario y certificaciones exactas de perfiles active, pruebas unitarias y evals deterministas.
- `fixture-integrity`: inventario completo, JSON válido y hash exacto de cada fixture sintético.
- `profile-complete`: acreditación de todos los perfiles active. `reuse` valida sus certificaciones exactas, hashes y antigüedad máxima sin repetir Docker; `execute` reejecuta el perfil representativo en Docker. Una deriva o certificación caducada hace fallar `reuse` y exige recertificación, nunca un pase degradado.
- `regression`: comparación de métricas comunes con una baseline versionada.
- `definition-conversation`: evaluación semántica y humana de FX-01, FX-20, FX-21 y FX-36; el harness actual la mantiene siempre `not-run` porque todavía no existe un contrato ni importador de resultados ejecutados para este canal.
- `activation`: resultados observados en sesiones controladas de Codex contra el corpus etiquetado.
- `document-review`: rúbrica humana de diez dimensiones, de 1 a 5.
- `pilot`: resultados agregados y saneados del piloto M5.
- `release-approval`: decisión durable del responsable del proyecto, informada
  por el uso real que considere suficiente y almacenada sin identidades ni
  conversaciones.

El canal `candidate` exige `automated`, `fixture-integrity`, `profile-complete` y `regression`. `stable` exige esos cuatro canales técnicos más `release-approval`. `definition-conversation`, `activation`, `document-review` y `pilot` permanecen visibles como evidencia detallada opcional en ambos canales: pueden conservar `not-run`, pero nunca cuentan como superados. Un canal requerido `not-run`, `skipped`, incompleto o fallido bloquea la release.

## Ejecución

La puerta publicable se ejecuta desde la raíz de un checkout dedicado y recién creado para el commit de release. Ese checkout debe estar limpio antes de arrancar y no debe contener archivos no versionados preexistentes, ni siquiera ignorados. Una ejecución desde el checkout de desarrollo sigue siendo útil como diagnóstico, pero no sustituye esta atestación. Para una candidate:

```powershell
$pluginRoot = Resolve-Path "."
$reportPath = Join-Path (Resolve-Path "..") "quality-report.json"
python (Join-Path $pluginRoot "scripts\run_quality_harness.py") --channel candidate --date (Get-Date -Format "yyyy-MM-dd") --baseline (Join-Path $pluginRoot "quality\baselines\v0.17.0.json") --profile-mode reuse --output $reportPath
```

Para 1.1.1 estable, la misma puerta incorpora la decisión del responsable:

```powershell
python scripts\run_quality_harness.py --channel stable --date (Get-Date -Format "yyyy-MM-dd") --baseline quality\baselines\v0.17.0.json --profile-mode reuse --release-approval quality\release-approval-v1.1.1.json --output $reportPath
```

`--profile-mode not-run` deja candidate `incomplete`. `--profile-mode reuse` es la opción normal cuando las certificaciones exactas tienen como máximo 90 días y siguen ligadas a todos sus bytes. `--profile-mode execute` vuelve a ejecutar Docker y el alias heredado `--include-complete-profile` conserva ese comportamiento. Use `execute` para recertificar, investigar el runtime o por petición explícita. El reporte usa el esquema 1.2, conserva 1.1 como contrato histórico, registra `HEAD`, ejecución y rendimiento, y falla en la atestación inicial si la fuente no coincide exactamente con Git. `--preflight-only` conserva esa atestación completa como diagnóstico opcional; no precede a la ruta estándar porque el harness la repite de forma segura antes de sus hijos. Una ruta de salida ya existente se rechaza antes de lanzar tests; `--force` requiere `--rerun-reason` y esa razón queda registrada en `execution.rerun_reason`.

Para feedback cotidiano use una vía focalizada que no pretende ser evidencia de release:

```powershell
python scripts\run_fast_validation.py --focus jira-reporting
python scripts\run_fast_validation.py --focus compatibility
python scripts\run_fast_validation.py --changed-from origin/main
```

Esta vía ejecuta siempre contratos y `fast`, añade solo los módulos afectados conocidos y cae en `integration` ante una ruta nueva. No ejecuta Docker ni acredita una release. La release ejecuta `fast`, `integration`, `package` y `profile` exactamente una vez desde checkout limpio, además de evals; `--profile-mode reuse` comprueba certificaciones exactas y `execute` reserva su fase Docker independiente. Cada tier impone dentro de su propio runner el presupuesto comprometido; el harness sólo usa un techo de 900 s para recuperar JSON y limpiar un despachador bloqueado, sin ampliar los presupuestos de tier. El proceso publica heartbeats cada 30 segundos, limita cada módulo y mata su árbol completo al agotar el tiempo.

Los presupuestos comprometidos están en `quality/performance-policy.json`: 120/480/240/180 segundos para `fast`, `integration`, `package` y `profile`, 900 para candidate sin Docker `execute` y 1800 para ese perfil. Un límite absoluto siempre bloquea. La comparación relativa solo se aplica cuando coincide el fingerprint no personal del runner; una diferencia de entorno queda visible y no se presenta como comparación superada. La baseline no se actualiza automáticamente.

Para actualizarla se necesitan exactamente tres resultados `--suite all` pasados, funcionalmente idénticos y producidos por el mismo fingerprint desde un checkout limpio. Primero revise el preview y después repita con `--apply`; la razón y el commit quedan en el diff:

```powershell
python scripts\update_performance_baseline.py --result run-1.json --result run-2.json --result run-3.json --reason "Baseline medida para la release 0.15.0"
python scripts\update_performance_baseline.py --result run-1.json --result run-2.json --result run-3.json --reason "Baseline medida para la release 0.15.0" --apply
```

La vinculación de fuente se captura antes de lanzar validadores, tests o el perfil Docker. No confía únicamente en `git status`: exige que las entradas de `HEAD` y del índice coincidan en ruta, modo, tipo y objeto, calcula contra cada archivo real el objeto Git esperado y rechaza estados no consolidados, archivos ausentes, enlaces no admisibles, gitlinks y cambios ocultos mediante `assume-unchanged` o `skip-worktree`. También enumera todos los archivos no versionados sin aplicar exclusiones, por lo que cualquier archivo preexistente —incluido uno oculto por `.gitignore` o `.git/info/exclude`— deja la fuente `dirty`.

Los artefactos que una comprobación cree después de ese snapshot no cambian retroactivamente la atestación inicial. Esto permite que el propio gate genere salidas temporales sin falsificar el estado de partida; no permite reutilizar para otra atestación un checkout que ya las contenga. El procedimiento completo para crear el checkout dedicado y generar los bundles está en `docs/DISTRIBUTION.md`.

Para aportar evidencia opcional de activación y revisión documental, copie `quality/observations.example.json` fuera del repositorio, sustituya los valores de ejemplo, use el hash canónico indicado por un reporte reciente y pase `--observations`. Ese archivo solo alimenta `activation` y `document-review`: no cambia `definition-conversation`. El archivo no debe contener nombres, prompts de cliente, repositorios, secretos ni contenido sustantivo.

Para certificar `stable`, use una aprobación versionada que cumpla `schemas/release-approval.schema.json` y pásela mediante `--release-approval`. Debe corresponder a la versión exacta, limitarse a `stable-release`, declarar el rol `project-owner`, conservar evidencia agregada sin identidades y no tener hallazgos bloqueantes. La aprobación acredita la decisión de promoción, no ejecuciones caso a caso. Los casos FX detallados sin observación siguen `not-run` y pueden retomarse para aprendizaje sin reabrir por sí solos una release ya aprobada.

Un resumen M5 con decisión puede incorporarse mediante `--pilot-summary`. Antes de interpretar `go`, el harness valida de forma cerrada todas las propiedades, tipos, mínimos, catálogos y listas únicas de `schemas/pilot-summary.schema.json`. `go` satisface el canal, `go-conditioned` queda `incomplete` y `no-go` o `withdrawal` lo dejan `failed`.

## Interpretación

- `passed`: todos los canales exigidos por el canal solicitado están completos y verdes.
- `failed`: existe un fallo crítico, un canal requerido fallido o una regresión.
- `incomplete`: falta evidencia exigida, sin presentarla como fallo ni como éxito.

Los estados de una prueba o canal conservan su semántica propia: `skipped` significa que una prueba declarada no se ejecutó y `not-run` que aún no existe una observación para ese canal. Ninguno equivale a `passed`. Un `not-run` opcional no bloquea la release; cualquier canal requerido que no esté `passed` sí la bloquea. En `stable`, `release-approval` es requerido.

Los códigos de salida son `0`, `2` y `3`, respectivamente para `passed`, error/fallo e `incomplete`.

## Extensión 0.16

El catálogo conserva FX-56 a FX-60 y añade el corpus `definition-v0.17.0.json`. La suite integration incluye `test_validation_evidence_v016` y `test_fullstack_integration_contract_v017`: límites visuales, integridad/semántica, salud actual, fichas derivadas, integración multiunidad, mocks, reconciliación, atomicidad y determinismo. La comparación candidate usa como baseline publicada `quality/baselines/v0.15.0.json`; los canales humanos, semánticos, piloto y externos conservan su estado real.
