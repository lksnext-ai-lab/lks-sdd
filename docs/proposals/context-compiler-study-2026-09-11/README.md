# Estudio reproducible de contexto y tokens

El documento principal es [INFORME.md](INFORME.md). La investigación y los experimentos están terminados; **el compilador propuesto no está integrado en el plugin**. No se propone promover el selector experimental v2: falló las pruebas adversas posteriores.

## Mapa de evidencia

| Archivo o carpeta | Contenido |
|---|---|
| `research/sources.json`, `research/notes.md` | 21 fuentes primarias, fechas, resultados y límites |
| `repo-probe/` | Motores existentes ejecutados sobre seis consumidores sintéticos, corpus y huellas |
| `cases/inputs.json`, `cases/oracle.json` | 36 casos y juicios separados |
| `selection-experiment/` | Selecciones congeladas v1/v2, cobertura, tokens y 180 perturbaciones posteriores |
| `code-experiment/` | Prompts, cuatro entregas sin corrección posterior, oráculo original y contraejemplos nuevos |
| `evidence/format-results.json` | 24 representaciones de cinco conjuntos de datos |
| `evidence/corpus-tokens.json` | Tokens de prompts, código y corpus de las sondas |
| `review.md` | Revisión interna adversarial, incluida la regresión fuera del oráculo original |
| `evidence/*.stdout`, `*.stderr`, `*.json` | Recibos de validaciones y fallos iniciales de permisos conservados |
| `tools/` | Harnesses de investigación; no forman parte del runtime del plugin |

Los resultados históricos se conservan aun cuando una prueba posterior invalida su interpretación favorable. `compact_complete` es el nombre congelado de un prompt que resultó incompleto. `contract_preserved` es una revisión informada y pasó el oráculo inicial, pero falló dos formatos inválidos descubiertos después. Ninguno se presenta como equivalente al contexto completo.

## Reproducir sin modificar el producto

Trabajar desde la raíz del repositorio. Python 3 y Node.js deben estar disponibles; las funciones de zonas horarias requieren datos IANA. Se usó Python 3.14. El contador carga una copia portátil de `gpt-tokenizer` 3.4.0 bajo `.vendor/`; no se instaló como dependencia del plugin. Los temporales, el tarball y la caché están ignorados por el `.gitignore` de este estudio.

Para reconstruir ese contador si no está presente:

```powershell
npm pack gpt-tokenizer@3.4.0 --pack-destination docs/proposals/context-compiler-study-2026-09-11 --cache docs/proposals/context-compiler-study-2026-09-11/.npm-cache
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/unpack_tokenizer.py
```

El segundo comando verifica SHA-512 del archivo antes de extraer solo los módulos necesarios. El hash y URL figuran en `evidence/tokenizer-provenance.json`. No se requieren claves de modelos para recalcular las mediciones guardadas.

Primero comprobar integridad de prompts, candidatos, oráculos, selecciones y enlaces locales del informe, sin regenerarlos:

```powershell
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/verify_study.py
```

Los comandos siguientes **regeneran resultados del estudio en sus rutas conocidas**. Ejecutarlos sobre una copia si se desea conservar byte por byte la evidencia entregada. No vuelven a generar código con un modelo; reproducen evaluación sobre las entregas congeladas.

```powershell
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/selection_experiment.py
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/score_selection.py v1
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/selection_revision.py
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/score_selection.py v2
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/stress_selection.py
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/check_context_integrity.py
node docs/proposals/context-compiler-study-2026-09-11/tools/format_experiment.cjs
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/measure_corpora.py
python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/tools/posthoc_code_checks.py
```

Para volver a ejecutar las 121 comprobaciones de cada entrega:

```powershell
$studyPath = 'docs/proposals/context-compiler-study-2026-09-11'
Get-ChildItem -LiteralPath "$studyPath/code-experiment" -Filter 'candidate-*.py' | ForEach-Object {
    python -B -X utf8 "$studyPath/code-experiment/evaluate.py" $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Error ejecutando el harness: $($_.Name)" }
}
```

El evaluador escribe resultados por comprobación; su salida de proceso no indica que todas hayan pasado. Revisar `passed`, `total` y `all_cases_passed` en los JSON. Un fallo del candidato es evidencia esperada del estudio y no debe corregirse para alterar la comparación.

La sonda del motor tiene instrucciones específicas en [repo-probe/README.md](repo-probe/README.md), incluida la sustitución de temporales solo en memoria. Las validaciones existentes se ejecutaron mediante `tools/run_check.py`, conservando comando, duración, stdout y stderr. Los 36 tests originales pasaron en `evidence/targeted-native.json`; los intentos iniciales con errores de permisos permanecen identificados por otros nombres. La puerta estructural completa no equivale a certificación de release ni de perfiles candidate.

## Límites de reproducción

Las selecciones y aserciones son deterministas con estas entradas y versiones. Las entregas de modelos no lo son: una repetición requeriría modelo, configuración e historiales equivalentes, además de varias muestras. Las sesiones originales no estaban aisladas ni aleatorizadas y no expusieron facturación completa. No es posible reconstruir esa facturación sumando los archivos guardados.

Las sondas dependen de los motores y helpers presentes en un árbol que ya tenía cambios. `evidence/baseline.json` y `repo-probe/source-hashes.json` conservan evidencia de ese estado; para repetir contra otra versión hay que registrar la nueva identidad y tratarlo como otra medición. Las páginas externas son fuentes consultadas, no copias congeladas de su contenido.
