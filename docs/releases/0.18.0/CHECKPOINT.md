# Checkpoints de ejecución 0.18.0

## CKPT-018-001 — H0

Fecha: 2026-08-31. Estado: contrato materializado; implementación pendiente.

Hechos: creado worktree C:/Dev/lks-sdd-0.18.0 desde main
9b13616e9f9d67c7112ee620c65b8ea6831c50c2, rama codex/release-0.18.0.
El checkout original conserva únicamente site/ y el storyboard no versionados.
CONTRACT.md recoge 24 bloques, nueve variantes, aceptación y límites aprobados.

Verificación H0: comparación del contrato con el plan autorizado; revisión de
diff y ausencia de cambios canónicos. No se han ejecutado aún los gates H1-H6.

Pendientes: R18-02..R18-24. Certificación 0.18, publicación, registro y activación:
not-run. Piloto, producción, revisión humana e interoperabilidad: not-run.

Próximo paso: corregir ART-INTEGRATIONS y sus regresiones sin alterar IDs ni el
schema consumidor 1.5. Mantener SAT en lectura y no tocar el site original.

## CKPT-018-002 — R18-02

Fecha: 2026-08-31. Estado: corrección de tablas y referencias verificada.

Cambios: ambas tablas opcionales de ART-INTEGRATIONS reconocidas en 1.5;
delivery diferencia sistemas externos de interfaces entre unidades. Rechaza
duplicados dentro de una tabla o entre ambas sin renumerar ni escribir documentos.

Evidencia ejecutada: unittest tests.test_integrations_v018 y
tests.test_contract_engine: 17 passed; tests.test_fullstack_integration_contract_v017
y tests.test_quality_suite_registry: 18 passed. validate_plugin_contract.py:
VALID; validate_fixture_manifest.py: VALID (12 fixtures). Diff sin whitespace.
Estos resultados no acreditan todavía variantes, autenticación ni H5.

Pendientes: R18-03..R18-24. Próximo paso: observadores y operaciones declaradas
comunes, eliminando la dependencia de /api/v1 y la obligación de browser para DB.
