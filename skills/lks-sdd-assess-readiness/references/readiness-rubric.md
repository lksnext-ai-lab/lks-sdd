# Rúbrica de readiness por incremento

La evaluación produce `ready`, `ready-with-non-blocking-pending` o `blocked`. No usa puntuaciones opacas y no autoriza implementación.

## Condiciones bloqueantes

- El índice o un documento canónico obligatorio es inválido.
- El incremento no existe, no está `confirmed` o no declara alcance incluido y excluido.
- Un requisito vinculado no está confirmado o carece de criterio de aceptación observable.
- Falta una decisión técnica crítica o permanece como `proposal`.
- Datos, identidad o integraciones relevantes siguen indeterminados para el incremento; una no aplicabilidad necesita motivo.
- No hay estrategia o pruebas previstas vinculadas.
- Existe contradicción o punto abierto marcado como bloqueante para el incremento.
- La cadena requisito → criterio → decisión → incremento → prueba no es completa.
- En un incremento 0.6+, la aplicabilidad de interfaz está `pending`, falta su fila en `ART-INCREMENTS` o una no aplicabilidad carece de motivo.
- Un incremento con interfaz aplicable no tiene al menos una pantalla, un flujo y una dirección visual confirmados. Cada pantalla necesita entrada/salida, jerarquía, acciones secundarias, permisos/variantes, responsive, accesibilidad, contenido pendiente y los seis estados contractuales; cada flujo enlaza sus pantallas y la aceptación.
- Un cambio visual aplicable no tiene un `VIS-###` confirmado y validado por una persona. El asset debe ser PNG/JPG/JPEG local bajo `docs/lks-sdd/03-solution/ui-prototypes/`, con firma real y SHA-256 exacto; una propuesta no satisface readiness.
- `Visual mode` permanece `pending`, un cambio `new`/`material-change` no enlaza un prototipo confirmado, o `none` no justifica la ausencia real de cambio visual.
- `Visual mode=reuse` no enlaza un `VIS-###` confirmado, su archivo/hash/validación humana/ADR no son íntegros, la ADR no se comparte con la dirección y decisiones del incremento, o falta delimitar qué se reutiliza.
- En ruta `adopt-existing`, la baseline no está `materialized` o está `stale`.

## Pendientes no bloqueantes

Un punto explícitamente no bloqueante, con impacto y alcance independientes, puede producir `ready-with-non-blocking-pending`. La ausencia de evidencia no se presume no bloqueante.

## Revisión semántica

El validador comprueba estructura, estados, identificadores y referencias. La skill debe revisar además claridad, atomicidad, verificabilidad, riesgos, contradicciones y suficiencia contextual. Debe explicar cada bloqueo y el cambio o decisión mínima que lo resolvería, sin editar durante la evaluación.

`checked_files` e `input_fingerprint` son parte del resultado contractual. Incluyen los Markdown consumidos y los prototipos binarios confirmados. Si cualquiera cambia, el preview de implementación anterior deja de ser válido.
