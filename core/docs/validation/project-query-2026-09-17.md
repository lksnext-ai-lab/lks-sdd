# Validación de consultas humanas del proyecto — 2026-09-17

Estado: **implementación local verificada en su alcance automatizado; sin publicar**.
La aceptación humana en Codex y Copilot sigue `not-run`. La distribución completa
no está validada: persiste el fallo previo de longitud de rutas de Copilot.
Este informe corresponde al árbol de desarrollo, no a una atestación de release.

## Entrega y límites

Se implementan los cinco módulos `query_sources`, `query_context`, `query_code`,
`query_render` y `query_project`, el schema auxiliar `query-context` 1.0 y el
comando público `query`. La [guía compartida](../PROJECT-QUERY.md) se integra en
las seis skills, sin añadir una séptima, MCP, conectores, hooks, apps ni agentes
ejecutables.

La recuperación prioriza documentos, conserva prosa y excepciones, combina
relaciones explícitas en ambos sentidos y admite documentación parcial o anterior
a SDD. La ampliación al código requiere petición expresa o carencia concreta de
implementación ligada al contexto documental actual. No se ejecuta el consumidor.
Las fuentes mantienen ruta, líneas y hash; sus cambios invalidan los extractos.

La CLI proporciona contexto y una vista determinista de extractos. La síntesis
profesional para personas y la decisión de suficiencia corresponden a las skills;
no se atribuye comprensión semántica al renderer. La recuperación no devuelve
`answered`, valida readiness ni convierte observaciones en acuerdos.

La lectura se limita al checkout actual y a texto UTF-8. No incorpora extractores
PDF/Word/imágenes, búsqueda externa, ejecución, cambios de rama ni caché persistente.
Los límites y truncamientos se declaran. La exclusión/redacción de secretos es
defensa adicional, no una garantía de detectar todos los secretos desconocidos.
El código local y la evidencia histórica no acreditan el estado de producción.

## Resultados automatizados

| Comprobación | Resultado observado | Alcance de la evidencia |
|---|---|---|
| Consulta + CLI, revisión final | 47/47 passed; 14,353 s | 44 casos de consulta y 3 de CLI sobre el código final |
| Regresión general durante integración | 447 casos: 445 passed, 1 failed, 1 skipped; 565,295 s | Snapshot anterior a los últimos ajustes locales de consulta; no suite completa repetida sobre el árbol final |
| Distribución dual, repetición aislada | 25 casos: 24 passed, 1 failed; 176,712 s | Persiste el mismo fallo previo de rutas; módulo: 176,611 s |
| Evals existentes | 6/6 passed | No son evaluación humana de la nueva experiencia conversacional |
| Seis skills + manifiesto | passed | Validez estructural, no activación real en los hosts |
| Contrato del plugin | passed | LKS-SDD 1.1.1, con ampliaciones locales sin publicar |
| Perfiles | 23 estructuras válidas | `--allow-unvalidated`; no promoción ni recertificación de candidatos |
| Manifiesto de fixtures | 14 válidas | Inventario existente |
| Ruff, reglas F | passed | Cinco módulos nuevos y pruebas/benchmark |
| Diff y conservación | passed | Sin cambios en fuentes canónicas, perfiles ni motores certificados |

Los casos automatizados cubren los aspectos mecánicos de QC-01..31: modos,
carencias, fuentes sin IDs, relaciones inversas y contribuyentes, prosa y reglas
transversales, fuentes históricas, duplicados, límites, cambios concurrentes,
inventario nuevo, rutas con espacios/Unicode, junction real, contenido sensible,
instrucciones no confiables y runtime fijado. La instrumentación comprueba cero
lecturas de código en la consulta documental, cero procesos consumidores y cero
escrituras, incluido bytecode al invocar la CLI sin `-B` desde el consumidor.

Se añaden regresiones para filas tipadas sin clave de cobertura/trazabilidad,
alias Windows, presupuestos consumidos por contenido binario rechazado,
truncamientos de índices y revalidación paralela de archivos modificados/eliminados.
Una fixture canónica completa conserva sus bytes y recupera documentación sin
inventar duplicados de entidades. Estos resultados no garantizan cobertura
semántica de cualquier proyecto ni validan respuestas finales de un modelo.

### Fallo previo, omisión y presupuesto de package

`test_native_plugin_paths_fit_a_windows_plugin_cache` sigue fallando: 125 caracteres
frente al límite de 110. El origen coincide con el documentado en la
[validación previa de variantes](project-variants-2026-09-17.md):

```text
core/docs/proposals/context-compiler-study-2026-09-11/repo-probe/corpora/parallel_three_tasks/TASK-001-seeds-only.txt
```

No se elimina el estudio ni se relaja el límite para ocultar el fallo. Debe
resolverse antes de acreditar una distribución. El test visual de symlink quedó
`skipped` por `WinError 1314`; no se convierte en passed. El test de junction
específico de consulta sí se ejecutó y pasó.

La suite general también superó el presupuesto de package: **258,734 s > 240 s**.
La repetición aislada del módulo dual tardó 176,611 s, pero no repite todo el tier
ni elimina el fallo de presupuesto observado. No hay una validación global verde
ni un harness de release ejecutado sobre el árbol final.

## Rendimiento de la consulta

Runner: Windows 11, build 26200, CPython 3.14.0, AMD64. Cada ejecución crea fixtures
temporales de 100 documentos/2.236.800 bytes y 1.000 documentos/22.368.000 bytes,
y realiza 20 consultas temáticas por tamaño. Se lee y revalida el corpus completo;
no se recorta el texto ni se consulta código para cumplir los objetivos.

Las primeras iteraciones no fueron suficientes: p95 de 10,3066 s y 7,0066 s para
1.000 documentos. Una optimización posterior obtuvo 4,2761 s, pero la siguiente
medición volvió a fallar con 8,9985 s. Se conservan estos resultados; el favorable
intermedio no se utilizó para declarar el cierre.

El ajuste final reutiliza comprobaciones de metadatos y paraleliza únicamente
las lecturas independientes de revalidación, con un máximo de cuatro hilos.
Mantiene comprobaciones de rutas, identidad del archivo abierto, cambios durante
la lectura y SHA-256. La selección, los límites y la composición siguen ordenados;
no lanza procesos, agentes ni código del consumidor.

| Medición final | Documentos | Mediana | p95 | Máximo | Objetivo p95 | Resultado |
|---|---:|---:|---:|---:|---:|---|
| Revalidación optimizada | 100 | 0,2494 s | 0,2819 s | 0,2872 s | ≤ 2 s | passed |
| Revalidación optimizada | 1.000 | 2,2547 s | 2,3912 s | 2,4433 s | ≤ 5 s | passed |
| Repetición de confirmación | 100 | 0,1968 s | 0,2160 s | 0,2242 s | ≤ 2 s | passed |
| Repetición de confirmación | 1.000 | 2,2889 s | 2,4607 s | 2,5463 s | ≤ 5 s | passed |

No se modifican umbrales ni corpus entre estas dos ejecuciones finales. No existe
caché persistente del plugin; la caché del sistema operativo no está controlada.
La primera consulta se informa por separado, pero no se presenta como arranque
frío garantizado del sistema. Estas medidas corresponden al motor sintético:
latencia del asistente, ampliaciones conversacionales, costes facturados y
aceptación humana siguen `not-run`.

## Compatibilidad, conservación y canales pendientes

- La intersección de archivos cambiados con `CERTIFICATION_ENGINE_FILES` es vacía.
  No se modifican `specs/canonical/`, `profiles/` ni el schema del consumidor.
- Se preservan por hash los archivos previos de variantes no compartidos. En los
  archivos compartidos se añaden consultas sin retirar las modificaciones de variantes.
- El inventario de distribución incluye módulos, schema y guía de consulta; los
  tests existentes verifican núcleo dual y runtime temporal. La validez estructural
  o la instalación en fixtures no equivalen a activación conversacional real.
- No se crea commit, tag, push, publicación, instalación activa ni aprobación de
  release. La versión instalada del usuario no se actualiza con este trabajo.
- Q11/QC-32 siguen `not-run`: comprensión humana, selección de formato, fidelidad
  de respuestas finales, invocación natural y apertura de enlaces/diagramas en
  Codex y Copilot requieren una sesión de aceptación separada.

## Reproducción y reportes

Desde la raíz del repositorio:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_project_query --module test_public_cli
python -B -X utf8 tests/query_benchmark.py
python -B -X utf8 tests/run_unit_tests.py
python -B -X utf8 tests/run_unit_tests.py --module test_dual_distribution
python -B -X utf8 tests/run_evals.py
```

La puerta estructural y los procedimientos de release permanecen en
[VALIDATION.md](../VALIDATION.md). Los JSON se conservan en el temporal local de
Windows, directorio `lks-query-0b72bac6256141a7a87426c5895797e7`:

- `unit-tests.json`: regresión general y fallo de presupuesto.
- `package-isolated.json`: repetición aislada, con el mismo fallo funcional.
- `query-final-v3.json`: 47 comprobaciones finales superadas.
- `benchmark-final.json`: medición previa fallida, conservada.
- `benchmark-parallel.json`: primera medición del ajuste final.
- `benchmark-confirmation.json`: repetición sobre el mismo código final.

Son artefactos de diagnóstico temporales, no un bundle inmutable de release.
