# Batería sintética de selección de contexto

Estado: propuesta experimental. Corpus congelado de 36 casos, elaborado en español por juicio explícito de un agente sin leer implementaciones, resultados ni métricas de los selectores.

## Archivos y separación del oro

- `inputs.json`: array de entradas entregables a un selector. No contiene `required_ids`, `expected_status` ni `why`.
- `oracle.json`: array de juicios independientes por id. Solo el evaluador puede leerlo.
- La unión por `id` reconstruye el caso completo. No pasar esa unión al selector.

Cada entrada contiene `id`, `category`, `task`, `affected_scopes`, `fragments` y `root_ids`. Los fragmentos tienen `id`, `text`, `kind`, `scope`, `links` y `state`. `scope` es una cadena; `affected_scopes` es un array. Los enlaces tienen `target` y `type`. Identificadores de fragmento solo son únicos dentro de su caso.

`required_ids` se decidió leyendo el sentido de cada caso, sin calcularlo a partir de reglas de selección. Todos sus identificadores están presentes en la entrada. Una referencia a una fuente ausente puede figurar en `links`; la fuente ausente no se inventa ni se cuenta como fragmento seleccionable. `why` explica el juicio.

## Interpretación

`ready` significa que las fuentes suministradas bastan para cerrar el contexto descrito por este caso sintético. No equivale a autorización general, aceptación humana, conformidad del código ni disponibilidad operativa.

`needs_context` significa que existe una carencia o impedimento explícito: fuente o imagen ausente, aplicabilidad no resuelta, consumidores desconocidos, conflicto o autorización caducada. Seleccionar todas las piezas disponibles no elimina ese impedimento.

Los cuatro primeros casos son controles benignos explícitos: otros dominios, historia y enlaces navegacionales deben poder quedar fuera. El resto introduce obligaciones o bloqueos concretos: prosa sin clasificar, reglas globales sin enlace, negaciones, excepciones, unidades, locale y horario de verano, consumidores inversos, importación dinámica, reflexión, configuración, varias unidades, migración gradual, vigencia integral, memoria antigua, ciclos, conflictos, imágenes, prohibición de red, evidencia no confiable, manifiestos incompletos, nombres repetidos y concurrencia.

`kind` no determina por sí solo obligatoriedad: un fragmento `unclassified` puede contener una obligación y un índice `global` puede ser solo navegacional. Tampoco toda fuente fuera de `affected_scopes` es irrelevante: consumidores inversos y restricciones cruzadas pueden ampliar el ámbito.

Los tipos y estados son datos del caso, no un algoritmo impuesto al selector. No deducir obligatoriedad por la posición del fragmento ni por `F01` más allá de las raíces declaradas.

## Límites y protocolo

1. Ejecutar el selector solo con `inputs.json`. El evaluador lee el oro después de obtener la selección.
2. Informar cobertura de fragmentos requeridos, omisiones, exceso de selección y clasificación de estado por separado. No fusionarlos en un único porcentaje de éxito.
3. No ajustar el corpus ni el oro tras observar resultados. Si se crea una versión nueva, conservar esta y documentar el motivo.
4. La batería es sintética, pequeña y escrita por un solo agente que conocía el diseño conceptual. Es independiente del código del selector, pero no una evaluación externa ciega ni evidencia de generalización.
5. La presencia de palabras explícitas, clases y estados puede facilitar heurísticas. Comparar también con repositorios y documentos reales, sin asumir que vienen bien clasificados.
6. Seleccionar `untrusted_evidence` preserva evidencia. Este ensayo no comprueba que un LLM resista sus instrucciones maliciosas ni que mantenga jerarquía de autoridad al ejecutar.
7. La prueba visual detecta ausencia de una imagen obligatoria. No evalúa lectura de píxeles ni fidelidad visual.
8. La cobertura de ids no demuestra conservación semántica de una reescritura, calidad de implementación ni mínimo universal de tokens.
9. Hay múltiples paquetes válidos; la lista requerida representa obligaciones mínimas de estos casos según el juicio documentado. El exceso debe revisarse antes de tratarlo como desperdicio real.
10. El corpus no certifica LKS-SDD, no modifica el plugin y no introduce conectores, agentes ni dependencias ejecutables.
