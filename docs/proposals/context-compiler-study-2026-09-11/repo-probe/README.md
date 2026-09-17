# Prueba empírica del motor documental

Se ejecutó `probe.py` sobre seis proyectos sintéticos materializados mediante helpers existentes. No se modificó el runtime, los fixtures originales ni fuentes canónicas del plugin. No se ejecutó implementación, instalación, publicación ni llamadas externas. Los resultados no acreditan una release ni suficiencia semántica.

## Reproducción y entorno

Desde la raíz: `python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/repo-probe/probe.py`.

La ejecución efectiva utilizó Python 3.14.0. Se fijan TEMP/TMP y `tempfile.tempdir` dentro de este directorio y se deshabilitan bytecodes. `TemporaryDirectory` falló con WinError 5 incluso bajo este directorio; una comprobación separada con Python bundled 3.12 también falló. Un directorio ordinario con `Path.mkdir` sí funcionó. El harness sustituye `tempfile.TemporaryDirectory` SOLO en memoria por directorios ordinarios retenidos dentro de `temporary/`. No cambia permisos ni elimina directorios. Los helpers del plugin se ejecutan contra esas copias; los motores se usan sin modificaciones. Este detalle limita la equivalencia del harness con los tests originales en lo relativo a creación/limpieza de temporales, no a selección de contratos.

La primera ejecución con temporales estándar quedó interrumpida por permisos. La segunda completó las seis inspecciones y guardó `results.json`. Su exit code fue 1 por una modificación concurrente de `tests/reports/dual-fast.json` detectada durante el inventario de integridad; su autor es desconocido y este probe no escribe esa ruta. Es el único cambio detectado entre los archivos py/json/md/png inventariados bajo tests/scripts/skills/schemas/profiles. El árbol de trabajo ya contenía cambios previos; no se restauró ni limpió.

Se conservó esa medición en `results-first-run.json`. La repetición final excluyó `tests/reports/` del inventario de fuentes porque contiene reportes generados; conservó la inspección de código, esquemas, skills y fixtures. Completó los seis casos con exit code 0 y ninguna fuente inventariada modificada. `../evidence/repo-probe-confirmed.json` conserva el recibo (30,59 s). Los corpus y `results.json` actuales corresponden a esa repetición. La exclusión no borra ni atribuye el cambio concurrente de la primera medición.

## Fuentes reutilizadas

- `tests/test_contract_engine.py:245`: `_active_project`, fixture visual con activo confirmado e histórico rechazado.
- `tests/test_contract_engine.py:624`: variante de incremento compartido, reproducida en `shared()`.
- `tests/eval_support.py:168`: `materialize_ready_project`, proyecto de una tarea, aquí sin confirmar planning.
- `tests/test_planning_continuity_v13.py:257`: `_build_parallel_complete_plan`, tres tareas con integración y planning confirmado.
- `tests/test_planning_continuity_v13.py:214`: `_add_calculator_scope`, ampliación de doce requisitos sin cobertura completa.
- `tests/test_multi_profile_delivery.py:174`: variante de dos bindings y dos tareas, reproducida hasta la preparación documental; no se autoriza ni aplica implementación.

## Medidas y límites

`results.json` conserva caracteres Unicode y bytes UTF-8; NO son tokens. Los corpus guardados en `corpora/` permiten tokenización exacta posterior. `indexed-documents.txt` contiene los Markdown declarados en artifacts con etiquetas de origen. `active-rows.txt` es una representación tabular legible de `ActiveContract.rows`; no incluye todos los metadatos, locks, imágenes o estado, por lo que su tamaño no es el tamaño de un paquete completo. `all-model-rows.txt` muestra todo el modelo de filas.

Las métricas de texto fuera de tablas clasifican líneas que no empiezan por `|` y excluyen frontmatter; la variante narrativa excluye además encabezados y líneas vacías. Es una medida léxica, no un parser semántico de Markdown ni un inventario definitivo de obligaciones. Las proyecciones `TASK-*-seeds-only.txt` contienen solo propiedad primaria y filas de TASK presentes en el contrato activo. Son deliberadamente incompletas y no deben utilizarse para implementar.

## Resultados observados

Los seis fixtures completaron `build_project_model`, `resolve_active_increment` y el intento de `assess_planning`. Cuatro tienen `ProjectModel.valid=true`. Los fixtures mínimos visual e incremento compartido conservan errores estructurales esperables de sus tests (`LKS-ARTIFACT-MISSING` y, en compartido, además `LKS-DOMAIN-MISSING`/`LKS-REF-SYNTAX`); su contrato activo INC-001 no produjo errores. No se presentan como proyectos completos válidos.

| Caso | Filas modelo | Filas activas INC-001 | Planning |
|---|---:|---:|---|
| visual_history | 19 | 18 | not-started |
| shared_increment | 24 | 18 | not-started |
| ready_single_task | 43 | 18 | partial |
| parallel_three_tasks | 54 | 27 | complete |
| calculator_partial | 98 | 73 | partial |
| two_profile_bindings | 46 | 20 | partial |

En los seis casos, añadir una regla normativa en prosa fuera de la tabla de FR cambió `document_fingerprint` y conservó `active.fingerprint`. Modificar la celda `Statement` de FR-001 cambió ambas huellas. Las mutaciones se realizaron en copias temporales, restaurando los bytes originales y verificando la igualdad con la huella inicial después de cada conjunto. Los cuatro modelos inicialmente válidos permanecieron válidos al añadir esa prosa. Esto confirma una omisión de representación de prosa en la huella activa de estos casos; no evalúa cómo interpreta un agente esa prosa ni todos los checks de autorización.

En los dos casos visuales, cambiar los bytes de VIS-001 rechazado cambió solo la huella documental; cambiar VIS-003 confirmado cambió ambas. Los activos son bytes sintéticos del fixture, no imágenes visualmente validadas. Alterar los bytes genera además la discrepancia de checksum declarada registrada en `mutations.json`; no es una edición visual aprobada.

INC-001 del fixture compartido conserva 18 filas activas y la misma huella activa que el fixture visual base, pese a tener cinco filas adicionales de otro incremento. Conserva detalles y estados UX, y excluye los IDs extranjeros AC-002/ADR-002/TEST-002/INC-002, según los IDs completos guardados.

Un límite decisivo del selector propuesto: `coverage.by_task` expresa propiedad PRIMARIA. En `two_profile_bindings`, TASK-002 es contribuyente y recibe lista vacía, aunque su trabajo necesita requisitos compartidos. Un selector que use solo ese mapping omitiría contexto. Hay que incorporar contribuciones, definición/plan de tarea, contratos de integración y reglas transversales. El fixture paralelo también asigna ADR-001 a la tarea integradora; ello no significa que las otras tareas puedan ignorarla.

## Implicaciones para el diseño

Se necesita un índice derivado de bloques de prosa, además del grafo actual; una semilla de tarea que incluya contribuciones y contratos compartidos; y un paquete final que preserve contratos visuales, locks, instrucciones y estado operativo. La reducción entre texto completo y filas activas señala oportunidad, pero no demuestra ahorro seguro ni mínimo. No se ha medido calidad de código o suficiencia semántica en este probe.

El código real confirma el límite observado: `scripts/contract_engine.py:1260` estructura tablas, `1814` compone payloads de filas, `1873` resuelve INC; `scripts/planning_engine.py:1170` deriva by_task desde propietarios; `1244` compara huellas de autorización completas. La futura huella del paquete no debe sustituir la huella global de autorización.
