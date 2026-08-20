# Contrato de verificación

## Estados de comprobación

- `passed`: se ejecutó y cumplió el criterio.
- `failed`: se ejecutó y no lo cumplió.
- `blocked`: un prerrequisito impidió ejecutarla.
- `not-run`: no se ejecutó; nunca equivale a éxito.
- `not-applicable`: existe una justificación documentada para el alcance.

## Clasificación del incremento

- `verified`: todas las comprobaciones aplicables pasaron y la trazabilidad está completa.
- `verified-with-reservations`: las comprobaciones críticas pasaron, pero permanecen limitaciones o comprobaciones no críticas no ejecutadas y visibles.
- `not-verified`: existe un fallo, bloqueo, ausencia crítica de evidencia o contradicción.

La clasificación técnica no aprueba producción, excepción, entrega, riesgo residual ni conformidad corporativa.

## Revisión visual y de interacción

Un incremento 0.6+ con interfaz aplicable no puede quedar `verified` solo con lint, tests o build. Requiere una revisión manual en navegador de las pantallas y flujos afectados contra los `UX-###` y `VIS-###` confirmados. Sin evidencia explícita, `visual-browser-review` queda `not-run` y la clasificación es `not-verified`.

El argumento `--visual-evidence` acepta un JSON 1.1 local bajo `docs/lks-sdd/evidence/visual/`. Sus claves exactas son `schema_version`, `increment`, `status`, `review_type`, `reviewed_at`, `reviewer`, `human_validation`, `baseline`, `coverage`, `screenshots`, `checks` y `limitations`. `reviewed_at` es ISO-8601 con zona horaria y, al ejecutar, no puede tener más de siete días. `reviewer` conserva rol y alias no identificativo.

`baseline` enlaza `baseline_id`, los SHA-256 actuales de implementación, `ART-INCREMENTS` y `ART-UX`, y todos los `VIS-###` confirmados. `coverage` relaciona todos los `UX-###`, `VIS-###`, estados y capturas revisados. Cada screenshot usa `SHOT-###`, ruta, SHA-256, ruta de aplicación, viewport con DPR y tipo de captura; sus dimensiones deben concordar. Cada check tiene ID, estado `passed`, UX, screenshots y nota. El JSON y capturas permanecen en el directorio visual, no usan enlaces y deben ser PNG/JPEG estructuralmente decodificables.

La evidencia canónica registra el SHA-256 del JSON, baseline, árbol de fuentes de implementación relevante y lista de capturas consumidas. El fingerprint incluye los archivos declarados y los árboles de código habituales (`apps`, `packages`, `services`, `src`, `lib` y `tests`), excluyendo dependencias, cachés y salidas de build; así no puede omitirse silenciosamente otro archivo fuente del mismo proyecto. La validación vuelve a comprobar el JSON y esos archivos; una mutación posterior queda expuesta sin copiar contenido visual sensible al Markdown.

## Evidencia mínima

La evidencia registra identificador, revisión, incremento, perfil y lock, fecha, herramienta, comprobación, resultado, limitaciones y relaciones con criterios y pruebas. No copia tokens, contraseñas, datos personales, imágenes, volcados completos ni logs productivos; para capturas conserva solo ruta y hash.
