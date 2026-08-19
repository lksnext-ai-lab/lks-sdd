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
- En ruta `adopt-existing`, la baseline no está `materialized` o está `stale`.

## Pendientes no bloqueantes

Un punto explícitamente no bloqueante, con impacto y alcance independientes, puede producir `ready-with-non-blocking-pending`. La ausencia de evidencia no se presume no bloqueante.

## Revisión semántica

El validador comprueba estructura, estados, identificadores y referencias. La skill debe revisar además claridad, atomicidad, verificabilidad, riesgos, contradicciones y suficiencia contextual. Debe explicar cada bloqueo y el cambio o decisión mínima que lo resolvería, sin editar durante la evaluación.
