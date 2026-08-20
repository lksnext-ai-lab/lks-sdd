# Contrato de verificación

## Estados de comprobación

- `passed`: se ejecutó y cumplió el criterio.
- `failed`: se ejecutó y no lo cumplió.
- `blocked`: un prerrequisito impidió ejecutarla.
- `not-run`: no se ejecutó; nunca equivale a éxito.
- `not-applicable`: existe una justificación documentada para el alcance.

`skipped` tampoco equivale a éxito y no es un estado admitido en la evidencia canónica del incremento; debe registrarse como `not-run` o `blocked` con su motivo.

## Clasificación del incremento

- `verified`: todas las comprobaciones aplicables pasaron y la trazabilidad está completa.
- `verified-with-reservations`: las comprobaciones críticas pasaron, pero permanecen limitaciones o comprobaciones no críticas no ejecutadas y visibles.
- `not-verified`: existe un fallo, bloqueo, ausencia crítica de evidencia o contradicción.

La clasificación técnica no aprueba producción, excepción, entrega, riesgo residual ni conformidad corporativa.

## Puerta de implementación

El plan solo se calcula si `.lks-sdd/project.json` contiene `implementation` para el mismo `INC-###`, con un `profile_id` idéntico a `technology.selected_profile` y estado `in-progress` o `completed`. El estado `in-progress` permite anticipar los checks durante el handoff, pero el resultado declara que la ejecución todavía no está habilitada.

Ejecutar cualquier check o registrar un `EVID-###` exige que ese mismo registro mantenga `implementation.status=completed`. Si falta `implementation`, el incremento no coincide, el perfil es incoherente o el estado es `not-started`, `in-progress` o `blocked`, el runner falla cerrado antes de invocar herramientas, crear evidencia o modificar trazabilidad e índice. Un plan, una autorización o unos checks potencialmente exitosos no sustituyen esta puerta.

Después de ejecutar los checks y antes de cualquier escritura, el runner recarga `project.json` y revalida el estado `completed`, el incremento, el perfil, el lock H0 y el contrato activo contra la instantánea inicial. Si cualquiera de esas entradas cambió durante la ejecución, no crea `EVID-###` ni modifica trazabilidad o índice; la mutación externa se conserva para que pueda revisarse y sea necesario repetir la verificación.

## Fases de trazabilidad

Antes de implementar, `preimplementation` exige una cadena no vacía de requisito confirmado, criterio de aceptación, decisión o no aplicabilidad motivada, incremento y prueba planificada. No exige fabricar evidencia antes de ejecutar. Durante verificación, la fase `verification` exige además un archivo estructurado `EVID-###` aplicable al mismo incremento, con clasificación `verified` o `verified-with-reservations`, una lista no vacía de checks y todos ellos en `passed`. Un enlace a un archivo ausente, `not-verified`, sin checks, o con cualquier check `not-run`, `skipped`, `blocked` o `failed` no satisface la trazabilidad. Si hay requisitos aplicables pero no se comprueba ninguno, ambas fases fallan de forma explícita.

El contrato activo excluye referencias rechazadas, sustituidas o retiradas como inputs de ejecución, aunque sus filas sigan conservadas para historial. La ausencia de `EVID-###` en preimplementación no es éxito de verificación; significa que la evidencia todavía debe producirse.

## Revisión visual y de interacción

Un incremento 0.6+ con interfaz aplicable no puede quedar `verified` solo con lint, tests o build. Requiere una revisión manual en navegador de las pantallas y flujos afectados contra los `UX-###` y `VIS-###` confirmados. Sin evidencia explícita, `visual-browser-review` queda `not-run` y la clasificación es `not-verified`.

El argumento `--visual-evidence` acepta un JSON 1.1 local bajo `docs/lks-sdd/evidence/visual/`. Sus claves exactas son `schema_version`, `increment`, `status`, `review_type`, `reviewed_at`, `reviewer`, `human_validation`, `baseline`, `coverage`, `screenshots`, `checks` y `limitations`. `reviewed_at` es ISO-8601 con zona horaria y, al ejecutar, no puede tener más de siete días. `reviewer` conserva rol y alias no identificativo.

`baseline` enlaza `baseline_id`, los SHA-256 actuales de implementación, `ART-INCREMENTS` y `ART-UX`, y todos los `VIS-###` confirmados. `coverage` relaciona todos los `UX-###`, `VIS-###`, estados y capturas revisados. Cada screenshot usa `SHOT-###`, ruta, SHA-256, ruta de aplicación, viewport con DPR y tipo de captura; sus dimensiones deben concordar. Cada check tiene ID, estado `passed`, UX, screenshots y nota. El JSON y capturas permanecen en el directorio visual, no usan enlaces y deben ser PNG/JPEG estructuralmente decodificables.

La evidencia canónica registra el SHA-256 del JSON, baseline, árbol de fuentes de implementación relevante y lista de capturas consumidas. El fingerprint incluye los archivos declarados y los árboles de código habituales (`apps`, `packages`, `services`, `src`, `lib` y `tests`), excluyendo dependencias, cachés y salidas de build; así no puede omitirse silenciosamente otro archivo fuente del mismo proyecto. La validación vuelve a comprobar el JSON y esos archivos; una mutación posterior queda expuesta sin copiar contenido visual sensible al Markdown.

## Evidencia mínima

La evidencia registra identificador, revisión, incremento, perfil y lock, fecha, herramienta, comprobación, resultado, limitaciones y relaciones con criterios y pruebas. No copia tokens, contraseñas, datos personales, imágenes, volcados completos ni logs productivos; para capturas conserva solo ruta y hash.

La verificación H0 exige que `.lks-sdd/profile.lock.json` exista como archivo regular y coincida byte a byte con el lock H0 empaquetado. Un lock ausente, `{}`, editado o enlazado bloquea incluso el modo `--plan`; así el plan, la ejecución y la evidencia se atribuyen a la misma pila exacta que quedó enlazada en `active_contract_fingerprint` y fue materializada por `prepare`. La misma atribución exige coherencia entre `implementation.profile_id`, `technology.selected_profile` y el perfil H0 soportado.

Use el dispatcher instalado y declare la fase de trazabilidad de forma explícita cuando la inferencia automática no sea apropiada:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase verification --json
python "<plugin-root>/scripts/lks_sdd.py" verify "<project-root>" --increment INC-001 --plan
```
