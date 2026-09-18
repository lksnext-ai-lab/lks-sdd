# Revisión crítica interna del estudio

Fecha: 2026-09-11. Alcance: artefactos locales, lectura del selector, oráculos, prompts, candidatos y resultados. No se modificaron candidatos, oráculos, runtime ni resultados congelados. Se realizaron dos comprobaciones adicionales en memoria, descritas abajo; no se incorporan retrospectivamente a las puntuaciones originales. No hubo búsquedas web.

El revisor participó en `repo-probe` y generó `candidate-full.py` antes de conocer el oráculo. Esta revisión tiene criterio propio respecto del autor del selector, pero NO constituye auditoría externa ni anonimizada. Los antecedentes distintos de los agentes siguen siendo un factor de confusión.

## Dictamen

El estudio aporta evidencia útil de fallos de selección y de compresión, y permite descartar una lectura ingenua de `coverage.by_task`. No demuestra que exista un compilador automático seguro, que se haya encontrado el mínimo de tokens ni que los resultados se generalicen a implementación real. No se detectó P0 en los artefactos experimentales. Sí hay P1 que deben impedir presentar `proposal_v2` como listo para integrar y los resultados 100% como equivalencia funcional demostrada.

## P1 — El selector puede declarar ready tras descartar una raíz obligatoria

Evidencia: `tools/selection_revision.py:20–29`, `49–50`. `eligible()` descarta estados y clases antes de agregar el fragmento; `expand()` hace `continue` sin registrar un problema. Por tanto, que una raíz o dependencia explícita exista con estado `retired`/`rejected`/`superseded` no produce el bloqueo que sí produciría una referencia ausente.

Comprobación ejecutada en memoria cargando exclusivamente definiciones del AST, sin ejecutar la escritura del módulo: entrada con `root_ids=['R1']`, ámbito `billing` y único fragmento R1 de tipo requirement, estado retired y texto «regla necesaria». Resultado observado:

```json
{"selected_ids":[],"missing_references":[],"status":"ready","problems":[]}
```

No se puede interpretar una obligación retirada como una autorización para implementar sin contrato. Una raíz inválida exige fuente sustituta vigente o contexto pendiente. También deben distinguirse enlaces históricos opcionales de dependencias obligatorias hacia fuentes históricas. El estudio original no cubre este contraejemplo.

Acción necesaria antes de integrar: validar las raíces y cada referencia obligatoria antes de excluir; hacer explícita la cadena de sustitución y exigir resolución vigente. Añadir pruebas nuevas versionadas fuera del conjunto congelado, sin arreglar sus resultados anteriores.

## P1 — El 100% depende de clasificación externa correcta y de expansión amplia por prefijo

Evidencia: `tools/selection_revision.py:20–21`, `36–49`, `74`; `cases/README.md`. El selector recibe `kind`, `scope`, `state` y `links` ya asignados. Estas decisiones son justamente parte difícil de extraer de Markdown/prosa/código reales. Un párrafo obligatorio clasificado `example` o con scope incorrecto se puede eliminar aunque su texto diga lo contrario. Un estado semánticamente pendiente etiquetado `confirmed` evita el guard. El selector no inspecciona el significado del texto para corregirlos.

Además, `scope.split('.')[0]` incorpora todos los ámbitos hermanos del mismo dominio y luego recorre enlaces inversos. Esto puede lograr alta cobertura a costa de incluir casi todo un subsistema. No existe presupuesto, validación de aplicabilidad ni demostración de mínimo en ese algoritmo. El coste puede crecer con fragmentos hermanos y encadenamientos. El stress adicional de etiquetas erróneas y sesenta fragmentos hermanos debe publicarse separadamente como validación adversarial posterior; los resultados aquí revisados preceden ese stress.

La construcción `nodes={f['id']:f ...}` tampoco rechaza IDs duplicados: el último sobrescribe el nodo del grafo, mientras `render()` puede emitir ambos textos con el mismo ID. No se observó este caso en el corpus, pero la falta de comprobación es visible en código y amenaza la correspondencia entre cobertura y contenido servido.

Acción necesaria: declarar el clasificador como componente no implementado, medir sus falsos negativos por separado y bloquear metadatos ambiguos/contradictorios. Mantener cobertura y coste como dos métricas separadas. La estructura de un índice no acredita la fiabilidad de su clasificación.

## P1 — Los brazos no demuestran causalmente el efecto de un compilador automático

Evidencia: `code-experiment/design.json`, `revision-design.json`, `tools/build_revised_code_prompt.py`. `compact_complete` fue una reescritura manual que perdió el contrato de salida de C03 y el nombre de un campo de C09; 114/121 verificaciones y 11/12 funciones completas frente a 121/121 y 12/12 de full. El nombre compact_complete no describe la completitud observada y debe conservarse solo como identificador histórico.

`contract_preserved` recupera texto del encargo tras conocer el defecto, y alcanza 121/121. Es una revisión informada, no otro brazo aleatorio independiente. Los prompts seleccionados/revisados proceden de campos ya separados en `contracts.json`; el experimento no realiza extracción fiable desde Markdown libre, ni cierre semántico del conjunto necesario.

Una sola entrega por brazo, funciones de biblioteca muy conocidas, historial diferente y reintento informado no permiten atribuir pequeñas diferencias de código solo al número de tokens. La lección apoyada es que eliminar un contrato de interfaz puede romper la entrega, y conservarlo en esta revisión restauró las pruebas disponibles. No que una compresión semántica automática preserve universalmente la calidad.

## P1 — 121/121 no significa conformidad completa: hay un incumplimiento fuera del oráculo

Evidencia: `code-experiment/candidate-contract_preserved.py:105–125`; `code-experiment/evaluate.py:119–129`. El candidato revisado acepta cualquier texto que termine en GMT si el parser tolerante puede extraer una fecha. El contrato exige None para formatos inválidos.

Comprobación postmedición ejecutada sin modificar archivos, con now=`2026-09-11T12:00:00.500000+00:00` y cap=100:

| Retry-After | Resultado observado | Resultado exigido por formato |
|---|---:|---|
| `Fri, 11 Sep 2026 12:00:02 GMT` | 2 | 2 |
| `Fri, 11 Sep 2026 12:00:02 GMT junk GMT` | 2 | None |
| `Fri, 11 Sep 2026 12:00:02 GMT GMT` | 2 | None |

El resultado congelado 121/121 sigue siendo correcto respecto de esas 121 verificaciones. Sin embargo, «misma calidad que full» no está demostrado: el candidato full tiene validación gramatical adicional y este contraejemplo descubre una diferencia contractual material. No se corrigió ninguno de los dos.

Otros límites del oráculo, por inspección: el test `upper-hex` (`evaluate.py:188`) convierte también el prefijo a mayúsculas, de modo que puede pasar por rechazo del prefijo sin probar minúsculas obligatorias del digest. Las salidas no comprueban el uso interno de `compare_digest` exigido, ni ausencia de float en toda implementación posible, ni IO prohibida. Los candidatos revisados sí muestran `compare_digest`; el oráculo por sí solo no certifica esas propiedades. No hace falta inflar la batería con pruebas espejo, pero las obligaciones relevantes deben tener evidencia adecuada o quedar explícitamente no verificadas.

## P2 — false_ready mezcla selección con un guard que las referencias no tienen

Evidencia: `tools/score_selection.py:22–25`, `39`; `tools/selection_experiment.py`, rama full; `tools/selection_revision.py:65`. Full selecciona todos los fragmentos pero devuelve siempre ready. Por eso obtiene diez false_ready pese a cobertura completa. BM25/roots/graph también carecen del guard específico de v2.

La comparación es legítima como comparación de pipelines completos distintos si se explica. No demuestra que seleccionar todo sea menos seguro por exceso de texto: el error proviene del guard ausente por diseño. Para aislar recuperación, comparar cobertura y exceso con un guard común; para aislar readiness, servir el mismo contexto a cada clasificador. No restar precisión ni declarar ventaja semántica de v2 sobre full basándose en esos diez casos.

`precision` compara IDs seleccionados con un único conjunto mínimo juzgado por el autor. Algunos fragmentos extra pueden ser útiles, y los resultados no evalúan esa utilidad. `weighted_coverage` pondera por número de fragmentos, no por criticidad: un fallo en una negación puede valer una omisión aunque altere por completo una implementación.

## P2 — Los tokens son medidas textuales de referencia, no ahorro operativo completo

Evidencia: `evidence/corpus-tokens.json`, `format-results.json`, `tools/count_tokens.cjs`. Se midieron cadenas exactas con o200k_base/cl100k_base. Eso permite comparar esas serializaciones; no acredita que sean el tokenizer de facturación del modelo/host utilizado. No incluye instrucciones heredadas, skills, razonamiento, código de salida, contexto de herramientas, relecturas, comprobaciones, revisión, fallos, historial reinyectado ni píxeles de activos visuales.

Las proyecciones de `repo-probe` omiten deliberadamente partes necesarias y están etiquetadas seeds-only/incompletas. Su diferencia frente al corpus documental completo es oportunidad de selección, no ahorro listo para producción. Los seis corpus tampoco representan seis proyectos independientes del mundo real: varias variantes reutilizan el mismo helper sintético.

Para el encargo real, la variable objetivo debe ser consumo total para completar correctamente una tarea y su revisión, manteniendo cobertura. Separar también coste y latencia, porque caching puede reducir coste sin reducir contexto lógico. Incluir el coste amortizado de construir/actualizar índices y clasificaciones cuando intervenga un modelo. No sumar porcentajes de serialización y selección medidos sobre denominadores distintos.

## P2 — Treinta y seis casos y doce holdout no permiten afirmar generalización

Evidencia: `cases/README.md`, `selection-experiment/freeze-v2.json`. El corpus fue escrito por un agente que conocía la idea y contiene solo unas pocas piezas por caso. Los estados y ausencias aparecen explícitos. El holdout tiene doce casos separados por módulo del identificador; en v2 ya se habían visto sus métricas agregadas y frecuencias de metadatos. Está bien documentado como no sellado, pero no debe llamarse validación ciega externa.

Los 36 casos son adecuados como batería de desarrollo de fallos concretos. No estiman una tasa de omisión en repositorios grandes ni son suficientes para declarar riesgo residual aceptable. Las 121 aserciones tampoco equivalen a 121 proyectos o implementaciones independientes; provienen de doce funciones en un único lote. Informar números absolutos y denominadores, conservar errores y reconocer falta de intervalos de confianza. Añadir nuevas familias de repositorios, tareas y autores independientes antes de estimar generalización.

## Qué queda defendible

- Se ejecutaron motores reales sobre copias sintéticas y se verificó el distinto efecto de prosa y celdas sobre las huellas.
- `coverage.by_task` no basta para contribuyentes, y las filas activas por incremento no equivalen a contexto de tarea completo.
- La compresión manual agresiva perdió información de interfaz y falló pruebas; recuperar esa información reparó las pruebas disponibles en una revisión informada.
- La versión v2 cubrió los IDs y estados esperados del corpus congelado, pero los contraejemplos de esta revisión impiden promoverla sin validación adicional.
- La conclusión de producto razonable es diseñar una selección conservadora con procedencia, validación de metadatos y ampliación controlada, y ensayarla con tareas reales. No afirmar «mínimo de tokens» ni «todos los requisitos garantizados» a partir de este microbenchmark.
