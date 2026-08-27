# Harness de calidad M4

## Propósito

El harness integra FX-01–FX-45 históricos, el reporting Jira v0.11 FX-46–FX-51, la cobertura granular Entra v0.12 FX-52–FX-53 y los perfiles OIDC simulados v0.13 en FX-54. Cubre experiencia local sin Atlassian, hitos canónicos, comentario idempotente, una confirmación con recibos separados, workflow por IDs, reconciliación append-only, migración 1.4 → 1.5 y la separación entre cobertura diagnóstica y soporte estricto. No convierte una prueba no ejecutada o saltada en un resultado satisfactorio.

FX-01, FX-20, FX-21, FX-36 y FX-53 conservan evaluación conversacional `not-run`. FX-45 y FX-51 mantienen la interoperabilidad real Rovo/Jira como piloto `not-run`; la interoperabilidad real Microsoft Entra también sigue `not-run` en los perfiles candidate. Los perfiles simulados declaran interoperabilidad externa `not-applicable`, no `passed`. Ninguna prueba offline sustituye aceptación humana o piloto. El harness mantiene `quality/corpora/definition-v0.13.0.json` como corpus vigente; los anteriores son históricos.

## Canales de evidencia

- `automated`: contratos 0.8/1.2, 0.9/1.3 y 0.10/1.4, inventario y certificaciones exactas de perfiles active, pruebas unitarias y evals deterministas.
- `fixture-integrity`: inventario completo, JSON válido y hash exacto de cada fixture sintético.
- `profile-complete`: acreditación de todos los perfiles active. `reuse` valida sus certificaciones exactas, hashes y antigüedad máxima sin repetir Docker; `execute` reejecuta el perfil representativo en Docker. Una deriva o certificación caducada hace fallar `reuse` y exige recertificación, nunca un pase degradado.
- `regression`: comparación de métricas comunes con una baseline versionada.
- `definition-conversation`: evaluación semántica y humana de FX-01, FX-20, FX-21 y FX-36; el harness actual la mantiene siempre `not-run` porque todavía no existe un contrato ni importador de resultados ejecutados para este canal.
- `activation`: resultados observados en sesiones controladas de Codex contra el corpus etiquetado.
- `document-review`: rúbrica humana de diez dimensiones, de 1 a 5.
- `pilot`: resultados agregados y saneados del piloto M5.

El canal `candidate` exige `automated`, `fixture-integrity`, `profile-complete` y `regression`. `definition-conversation`, `activation`, `document-review` y `pilot` son opcionales solo para candidate: pueden permanecer `not-run`, pero siguen visibles y no cuentan como superados. `stable` exige los ocho canales; por tanto, un reporte con un canal requerido `not-run`, `skipped`, incompleto o fallido no puede publicarse como estable.

## Ejecución

La puerta publicable de candidate se ejecuta desde la raíz de un checkout dedicado y recién creado para el commit de release. Ese checkout debe estar limpio antes de arrancar y no debe contener archivos no versionados preexistentes, ni siquiera ignorados. Una ejecución desde el checkout de desarrollo sigue siendo útil como diagnóstico, pero no sustituye esta atestación:

```powershell
$pluginRoot = Resolve-Path "."
$reportPath = Join-Path (Resolve-Path "..") "quality-report.json"
python (Join-Path $pluginRoot "scripts\validate_fixture_manifest.py") $pluginRoot
python (Join-Path $pluginRoot "scripts\run_quality_harness.py") --channel candidate --date (Get-Date -Format "yyyy-MM-dd") --baseline (Join-Path $pluginRoot "quality\baselines\v0.12.0.json") --profile-mode reuse --output $reportPath
```

`--profile-mode not-run` deja candidate `incomplete`. `--profile-mode reuse` es la opción normal cuando las certificaciones exactas tienen como máximo 90 días y siguen ligadas a todos sus bytes. `--profile-mode execute` vuelve a ejecutar Docker y el alias heredado `--include-complete-profile` conserva ese comportamiento. Use `execute` para recertificar, investigar el runtime o por petición explícita. El reporte mantiene el esquema 1.1, registra `HEAD` y árbol `clean/dirty`, no sobrescribe salvo `--force` y falla si la fuente inicial no coincide exactamente con Git.

Para feedback cotidiano use una vía focalizada que no pretende ser evidencia de release:

```powershell
python scripts\run_fast_validation.py --focus jira-reporting
python scripts\run_fast_validation.py --focus migration
```

Esta vía evita reconstruir todos los fixtures históricos y no ejecuta Docker. La release sigue exigiendo una única suite integral desde checkout limpio, evals y el canal de perfiles. Así se elimina repetición de bajo valor durante el desarrollo sin reducir la cobertura de publicación.

La vinculación de fuente se captura antes de lanzar validadores, tests o el perfil Docker. No confía únicamente en `git status`: exige que las entradas de `HEAD` y del índice coincidan en ruta, modo, tipo y objeto, calcula contra cada archivo real el objeto Git esperado y rechaza estados no consolidados, archivos ausentes, enlaces no admisibles, gitlinks y cambios ocultos mediante `assume-unchanged` o `skip-worktree`. También enumera todos los archivos no versionados sin aplicar exclusiones, por lo que cualquier archivo preexistente —incluido uno oculto por `.gitignore` o `.git/info/exclude`— deja la fuente `dirty`.

Los artefactos que una comprobación cree después de ese snapshot no cambian retroactivamente la atestación inicial. Esto permite que el propio gate genere salidas temporales sin falsificar el estado de partida; no permite reutilizar para otra atestación un checkout que ya las contenga. El procedimiento completo para crear el checkout dedicado y generar los bundles está en `docs/DISTRIBUTION.md`.

Para aportar evidencia de activación y revisión documental, copie `quality/observations.example.json` fuera del repositorio, sustituya los valores de ejemplo, use el hash canónico indicado por un reporte reciente y pase `--observations`. Ese archivo solo alimenta `activation` y `document-review`: no cambia `definition-conversation`. El archivo no debe contener nombres, prompts de cliente, repositorios, secretos ni contenido sustantivo.

Por tanto, el canal `stable` no es alcanzable con el harness actual aunque `--observations` y `--pilot-summary` estén completos: `definition-conversation` continúa requerido y `not-run`. Además, los casos base FX-06, FX-07, FX-16, FX-17 y FX-19 aún carecen de una ejecución caso a caso; son un límite pendiente y no se consideran cubiertos por las métricas agregadas de activación o revisión documental.

Un resumen M5 con decisión puede incorporarse mediante `--pilot-summary`. Antes de interpretar `go`, el harness valida de forma cerrada todas las propiedades, tipos, mínimos, catálogos y listas únicas de `schemas/pilot-summary.schema.json`. `go` satisface el canal, `go-conditioned` queda `incomplete` y `no-go` o `withdrawal` lo dejan `failed`.

## Interpretación

- `passed`: todos los canales exigidos por el canal solicitado están completos y verdes.
- `failed`: existe un fallo crítico, un canal requerido fallido o una regresión.
- `incomplete`: falta evidencia exigida, sin presentarla como fallo ni como éxito.

Los estados de una prueba o canal conservan su semántica propia: `skipped` significa que una prueba declarada no se ejecutó y `not-run` que aún no existe una observación para ese canal. Ninguno equivale a `passed`. Un `not-run` opcional no impide candidate; el mismo estado impide stable cuando el canal es requerido.

Los códigos de salida son `0`, `2` y `3`, respectivamente para `passed`, error/fallo e `incomplete`.
