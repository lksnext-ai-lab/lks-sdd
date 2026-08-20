# Cobertura auditable de M4

Este documento conserva la fotografía base cerrada por la versión `0.4.0`. Las extensiones FX-20–FX-21 y la cobertura automatizada del contrato 1.1 se describen en [el harness vigente](QUALITY-HARNESS.md) y [la cobertura 0.7](V0.7-CONTRACT-HANDOFF-COVERAGE.md).

## Hechos verificados

- El catálogo base cubre exactamente FX-01–FX-19 y distingue capas, familias, modo de evaluación y criticidad.
- El corpus de activación contiene casos positivos, negativos y de límites operativos con un único oracle etiquetado por caso.
- El manifiesto de fixtures solo admite JSON sintético declarado, detecta altas no registradas, ausencias, enlaces y deriva de hash.
- El runner ejecuta contrato, perfil, pruebas y evals, calcula umbrales, destaca fallos críticos y no promueve evidencia `not-run`.
- La comparación de releases usa métricas comunes y detecta regresiones respetando si una magnitud debe subir o bajar.
- Las observaciones semánticas y revisiones humanas quedan ligadas al hash canónico del corpus y se mantienen fuera del repositorio si contienen evidencia operacional.

## Correspondencia

| Entregable EP-10 | Implementación | Evidencia |
|---|---|---|
| Catálogo de casos | `quality/catalog.json` | Cobertura base exacta FX-01–FX-19 y validación estructural |
| Corpus etiquetado | `quality/corpora/activation.json` | 18 intenciones positivas y negativas para Codex |
| Runner | `scripts/run_quality_harness.py` | Canales candidate/stable, códigos de salida y reporte JSON |
| Reportes | `schemas/quality-report.schema.json` | Salida determinista, atómica y validable |
| Comparación entre releases | `quality/baselines/v0.3.0.json` | Detección de regresiones sobre métricas comunes |
| Gestión de fixtures | `quality/fixture-manifest.json`, `scripts/validate_fixture_manifest.py` | Inventario cerrado y hashes SHA-256 |

## Límites

- El corpus etiquetado no constituye por sí solo una ejecución semántica; sin observaciones reales el canal `activation` figura como `not-run`.
- La puntuación documental exige revisión humana saneada y no se infiere a partir de tests estructurales.
- El gate `stable` seguirá incompleto hasta incorporar el piloto M5; esto es una protección deliberada, no un resultado aprobado implícitamente.
