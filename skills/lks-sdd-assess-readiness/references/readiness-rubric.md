# Rúbrica de readiness por incremento

La evaluación produce un estado combinado `ready`, `ready-with-non-blocking-pending` o `blocked`, y explica por separado `specification_readiness` y `automation_support`. No usa puntuaciones opacas, no selecciona una pila y no autoriza implementación.

## Preparación de la especificación

`specification_readiness` evalúa si el incremento está suficientemente definido para un handoff. Sus condiciones bloqueantes son:

- El índice o un documento canónico obligatorio es inválido.
- El incremento no existe, no está `confirmed` o no declara alcance incluido y excluido.
- Un requisito vinculado no está confirmado o carece de criterio de aceptación observable.
- Falta una decisión técnica crítica o permanece como `proposal`.
- Datos, identidad, seguridad, privacidad o integraciones relevantes siguen indeterminados para el incremento; una no aplicabilidad necesita motivo.
- No hay estrategia o pruebas previstas vinculadas.
- Existe contradicción o punto abierto marcado como bloqueante para el incremento.
- La cadena requisito → criterio → decisión o no aplicabilidad motivada → incremento → prueba no es completa en fase `preimplementation`. `EVID-###` solo se exige al comprobar la fase `verification`.
- Una relación activa apunta a una fila inexistente, rechazada, sustituida o retirada. El historial se conserva para auditoría, pero no forma parte del contrato activo del incremento.
- En un incremento 0.6+, la aplicabilidad de interfaz está `pending`, falta su fila en `ART-INCREMENTS` o una no aplicabilidad carece de motivo.
- Un incremento con interfaz aplicable no tiene al menos una pantalla, un flujo y una dirección visual confirmados. Cada pantalla necesita entrada/salida, jerarquía, acciones secundarias, permisos/variantes, responsive, accesibilidad, contenido pendiente y los seis estados contractuales; cada flujo enlaza sus pantallas y la aceptación.
- Un cambio visual aplicable no tiene un `VIS-###` confirmado y validado por una persona. El asset debe ser PNG/JPG/JPEG local bajo `docs/lks-sdd/03-solution/ui-prototypes/`, con firma real y SHA-256 exacto; una propuesta no satisface readiness.
- `Visual mode` permanece `pending`, un cambio `new`/`material-change` no enlaza un prototipo confirmado, o `none` no justifica la ausencia real de cambio visual.
- `Visual mode=reuse` no enlaza un `VIS-###` confirmado, su archivo/hash/validación humana/ADR no son íntegros, la ADR no se comparte con la dirección y decisiones del incremento, o falta delimitar qué se reutiliza.
- En ruta `adopt-existing`, la baseline no está `materialized` o está `stale`.

## Pendientes no bloqueantes

Un punto explícitamente no bloqueante, con impacto y alcance independientes, puede producir `ready-with-non-blocking-pending`. La ausencia de evidencia no se presume no bloqueante.

## Soporte de automatización

`automation_support` informa `selection-required`, `supported` o `unsupported` según el perfil confirmado, su registro, lock y capacidad implementable. La especificación puede quedar `ready` mientras la automatización está bloqueada; esto describe dos hechos distintos. El estado combinado permanece `blocked` para implementar hasta disponer de un perfil seleccionado y soportado, pero la skill no cambia la conclusión funcional ni elige H0 automáticamente.

En 0.7.0, solo `WEB-FASTAPI-REACT-KEYCLOAK-PG` aporta automatización H0 empaquetada. Una pila alternativa puede documentarse y alcanzar preparación de especificación sin prometer scaffold, ejecución o verificación automatizada.

Antes de `prepare`, readiness valida el perfil y el lock H0 empaquetados. La ausencia de `.lks-sdd/profile.lock.json` en el consumidor todavía es válida porque `prepare` es quien planifica y materializa esa copia. Si el archivo consumidor ya existe, debe ser un archivo regular idéntico byte a byte al lock empaquetado: `{}`, una versión editada, un symlink o cualquier otra divergencia bloquean readiness. La huella activa incorpora el SHA-256 del lock empaquetado incluso antes de materializarlo, de modo que la copia exacta posterior no cambia el contrato que se aprobó.

## Revisión semántica

El validador comprueba estructura, estados, identificadores y referencias. La skill debe revisar además claridad, atomicidad, verificabilidad, riesgos, contradicciones y suficiencia contextual. Debe explicar cada bloqueo y el cambio o decisión mínima que lo resolvería, sin editar durante la evaluación.

`checked_files`, `active_contract_fingerprint`, `profile_lock` y `document_fingerprint` son parte del resultado contractual. La huella activa representa únicamente los Markdown, relaciones, lock exacto y assets confirmados que alimentan el incremento; la huella documental también detecta cambios históricos. Un cambio de input activo invalida el preview de implementación. Una edición exclusivamente histórica sigue siendo visible para auditoría sin convertirse por ello en alcance implementable.

Los proyectos 1.0 se evalúan en modo de compatibilidad y conservan avisos de sintaxis o estados legacy. Migrar a 1.1 es una operación separada y explícita; readiness no reescribe documentos.
