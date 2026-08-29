# Migración a LKS-SDD 0.16.0

## Alcance

No existe migración de proyecto. Un proyecto 0.15 con `schema_version: 1.5` y `method_version: 1.5.0` se abre directamente. El `plugin_version` del índice conserva la procedencia histórica y no se reescribe al actualizar el plugin.

## Evidencia existente

- No se modifican EVID, capturas, CKPT, PROB, ART-TRACE ni recibos Jira existentes.
- Las revisiones visuales 1.1 ya referenciadas por EVID siguen siendo legibles como historia.
- Una ejecución nueva de `work verify` exige revisión visual 1.2 cuando la TASK tiene interfaz.
- Las fichas de `.lks-sdd/summaries/task-evidence/` son derivadas: pueden regenerarse y no cambian ningún fingerprint.

## Preparación de una revisión visual nueva

Conserve de una a cinco imágenes significativas por TASK frontend. Registre los campos semánticos del schema 1.2 y verifique SHA-256, viewport y dimensiones reales. Para backend puro, declare `not-applicable` con la razón calculada; UX/VIS o capacidades frontend impiden esa declaración.

Un perfil puede añadir `visual-evidence-policy.json` junto a su driver para estrechar el rango, siempre dentro de 1–5. Si no existe, se usa 1–5.

## Hallazgos posteriores

No edite la EVID histórica. Abra el hallazgo mediante el flujo PROB, ejecute `work correct`, vuelva a verificar y cierre con `work resolve` solo cuando exista una EVID nueva `verified` de esa TASK. El reporting mostrará la historia y la salud actual por separado.

## Rollback

Una operación fallida restaura conjuntamente EVID, manifest, traza y fichas derivadas. Volver temporalmente al bundle 0.15 no requiere deshacer datos del proyecto, pero 0.15 no interpretará las nuevas fichas ni producirá revisiones visuales 1.2. Nunca convierta ese rollback de runtime en una reescritura de evidencias.
