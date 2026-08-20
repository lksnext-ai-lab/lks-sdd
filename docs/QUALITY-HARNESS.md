# Harness de calidad M4

## Propósito

El harness integra el catálogo base FX-01–FX-19, la extensión v0.6 FX-20–FX-21, los corpus etiquetados de activación y conversación, la integridad de fixtures sintéticos, las comprobaciones deterministas, los umbrales y la comparación contra una release anterior. No convierte una prueba no ejecutada en un resultado satisfactorio.

FX-01 requiere entrevista adaptativa y deja de atribuirse al eval automatizado de readiness, que solo demuestra bloqueo ante información insuficiente. FX-20 cubre el snapshot de definición y FX-21 el ciclo visual con ImageGen. El corpus `quality/corpora/definition-v0.6.0.json` contiene entradas y rúbrica, no resultados.

## Canales de evidencia

- `automated`: contrato del plugin, perfil H0, pruebas unitarias y evals deterministas.
- `fixture-integrity`: inventario completo, JSON válido y hash exacto de cada fixture sintético.
- `profile-complete`: gate H0 integral en Docker, incluidos PostgreSQL, Keycloak, backend y frontend.
- `regression`: comparación de métricas comunes con una baseline versionada.
- `definition-conversation`: evaluación semántica y humana de FX-01, FX-20 y FX-21; permanece `not-run` hasta aportar sesiones controladas mediante un contrato de observaciones aprobado.
- `activation`: resultados observados en sesiones controladas de Codex contra el corpus etiquetado.
- `document-review`: rúbrica humana de diez dimensiones, de 1 a 5.
- `pilot`: resultados agregados y saneados del piloto M5.

El canal `candidate` exige automatización, fixtures, perfil completo y regresión y muestra `definition-conversation: not-run` como evidencia opcional pendiente. `stable` exige además definición conversacional, activación, revisión documental y piloto; por tanto, un reporte sin esas observaciones permanece `incomplete` para publicación estable.

## Ejecución

La puerta reproducible de candidate se ejecuta desde la raíz:

```powershell
python scripts\validate_fixture_manifest.py .
python scripts\run_quality_harness.py --channel candidate --date 2026-08-20 --baseline quality\baselines\v0.4.0.json --include-complete-profile --output C:\ruta\externa\quality-report.json
```

Sin `--include-complete-profile`, la puerta candidate queda `incomplete`. El reporte no sobrescribe una salida existente salvo con `--force`; el reemplazo es atómico.

Para aportar evidencia semántica o humana, copie `quality/observations.example.json` fuera del repositorio, sustituya los valores de ejemplo, use el hash canónico indicado por un reporte reciente y pase `--observations`. El archivo no debe contener nombres, prompts de cliente, repositorios, secretos ni contenido sustantivo.

Un resumen M5 con decisión puede incorporarse mediante `--pilot-summary`. `go` satisface el canal, `go-conditioned` queda `incomplete` y `no-go` o `withdrawal` lo dejan `failed`.

## Interpretación

- `passed`: todos los canales exigidos por el canal solicitado están completos y verdes.
- `failed`: existe un fallo crítico, un canal requerido fallido o una regresión.
- `incomplete`: falta evidencia exigida, sin presentarla como fallo ni como éxito.

Los códigos de salida son `0`, `2` y `3`, respectivamente para `passed`, error/fallo e `incomplete`.
