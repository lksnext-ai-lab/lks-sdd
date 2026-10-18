# Revisión crítica y corrección de V4-03

Fecha: 2026-10-16. Plan 0.4, sin cambios de las seis mejoras, dependencias,
criterios ni presupuestos. El usuario autoriza revisar/corregir V4-03 y comprobar
sus garantías antes de avanzar. V4-04 sigue sin iniciar.

Estado: **V4-03 verified; AC-04/AC-05 passed en el alcance técnico corregido**. El
[registro actual](v4-03-progress.json) conserva el dictamen técnico definitivo.

## Hallazgos y correcciones

| Hallazgo crítico | Consecuencia de la entrega anterior | Corrección y cobertura |
|---|---|---|
| Condiciones ocultas en la referencia exportada | La matriz comparaba condiciones en el archivo, pero no en stdout. Una decisión incompleta perdía `complete/issues`; readiness podía ocultar causas. | Conservar condiciones, errores, suficiencia, límites, siguiente paso y condiciones de revisión en la referencia. Casos reales incompletos, readiness bloqueada y revisión con pendientes. No emitir recibo de decisión sin leer el cuerpo. |
| Procedencia y huecos incompletos en el diagnóstico mínimo | Se eliminaba `runtime/window_state`; los gaps de fragmentos grandes/binarios y del sobre recortado no estaban en `row.gaps` y desaparecían. El 20,1 % ahorraba también datos necesarios. | Retener runtime/ventana originales, `fragment_gaps` sin textos y límites de input/result en `diagnostic_gaps`. Prueba con `observe` real: texto >64 KiB, binario pendiente y sobre >512 KiB. Sigue siendo una vista no importable como observación completa. |
| Exportación capaz de sobrescribir el consumidor o la entrada | El guard de destino solo protegía previews. Una consulta podía escribir JSON sobre app.py o el índice; apply podía destruir su descriptor de entrada tras aplicarse. | Validar destino antes de ejecutar: externo al consumidor, distinto de la entrada incluso por hardlink y sin archivos con múltiples enlaces. Comprobar antepasados existentes resuelve alias Windows en rutas todavía inexistentes. Snapshots de consumidor, entrada, aplicación bloqueada y rutas profundas/Unicode. |
| Efectos ocultos al fallar la salida compatible | Se protegía operational, pero compatible podía decir blocked sin mostrar la operación ya aplicada. | Informar efectos y recibos en ambos modos, también con details. Se verifica aplicación real, fallo posterior de salida y replay sin nuevos writes. No cambiar el estado normativo ni afirmar reversión. |

Estas son correcciones de V4-03. No se modifican reglas de decisión, selector,
almacenamiento normativo, recuperación, schemas, skills o formatos persistentes.
No se añade captura V4-04 ni se crea un sistema de temporales nuevo.

## Compatibilidad y límites explícitos

Se mantienen comandos, opciones, resultado API íntegro, modo compatible por
defecto y recibos de decisión. La salida exportada incorpora condiciones y una
advertencia de lectura separada del siguiente paso real. Sin status propio se
identifica como `exported`, no como un preview ficticio; no significa aprobación.
La corrección compact+output y estos metadatos impiden prometer igualdad binaria
con los sobres anteriores. La [interfaz](../../CLI-PRESENTATION.md) lo documenta.

Restringir destinos dentro del consumidor, sobre la entrada o con múltiples
enlaces es una incompatibilidad deliberada de seguridad del transporte: antes
podían destruir archivos y no eran una alternativa de escritura normativa. La
sobrescritura explícita de un archivo externo ordinario se conserva. La validación
de alcance no garantiza permisos de escritura ni elimina errores/races posteriores
de E/S; sus efectos se informan sin fingir atomicidad del conjunto aplicación/export.

El modo mínimo sigue siendo explícito. Las observaciones se construyen completas
antes de proyectarlas; no se acredita ahorro interno de CPU/memoria. Sin output no
se conserva automáticamente el sobre original; pedir details después es otra
invocación. La captura y conservación programática siguen pendientes de V4-04.

## Comprobación y valoración corregida

La revisión añade tres pruebas únicas y amplía las anteriores. Hay **40 pruebas
únicas con resultado satisfactorio**: 16 focales V4-03, 23 regresiones existentes y
la regresión real Windows. La matriz de 24 combinaciones sigue comprobando cuerpo,
recibo, opciones y exportación; los negativos reales cubren ahora los datos antes
omitidos. Las extracciones de ambos paquetes comprueban además igualdad exacta del
módulo y documentación comunes. No se convierte esto en aceptación humana de host.
La revisión ejecuta 46 tests contando repeticiones justificadas, todos superados;
los tres resultados no satisfactorios históricos de la entrega inicial se conservan.
El contrato estático sigue válido, el diff se revisa y los documentos/protocolos
históricos congelados se comparan por bytes con su copia previa.

Se conservan informes por ejecución. Solo se repiten pruebas afectadas por cambios
posteriores: condiciones de revisión y siguiente paso, guard de hardlinks y paquete
final. Los casos restantes se reutilizan porque sus ramas no cambiaron. No se
reutiliza el recuento inicial de 37 como certificación automática de la corrección.

| Misma consulta sintética, stdout UTF-8 completo | Candidata corregida |
|---|---:|
| Compatible | 17.288 bytes |
| Operational | 14.858 bytes |
| Diferencia observada | −2.430 bytes; **14,056 % menos** |

El 20,089 % anterior queda como observación histórica de una implementación que
omitía procedencia/límites; no es una estimación válida del ahorro con las garantías
corregidas. Los bytes actuales incluyen esos datos. El cuerpo contractual es igual,
exceptuando únicamente diagnóstico e indicador de caché entre llamadas. Se guardan
stdout y huellas. Una pareja de consulta no demuestra ahorro general ni estadístico,
tokens facturados, lectura del host, esfuerzo humano o latencia S8. El criterio de
S8 ≥20 % de tiempo completo permanece pendiente y no se rebaja.

## Recursos y decisión de continuación

Se reutiliza el área `management/operations/lks-sdd-v4-h1-20261015/v4-03`, con
archivos `review-*` separados de la evidencia inicial. La revisión tiene corte de
1.200 s desde 10:51:41Z, sin ampliar el techo global ni reiniciarlo. Es cota de
parada, no saldo disponible acreditado. Todas las lecturas, ediciones, pruebas,
fallos de preparación, esperas e informe cuentan en ese tiempo de entorno. No se
ha realizado otro intento completo S1–S8 ni otra campaña M6.

Los máximos siguen siendo 48 intentos completos, 8 h humanas y 12 h de entorno;
M6 dos variantes/cuatro horas compartidas. El saldo histórico global continúa
sin certificar. La percepción humana queda para uso real sostenido y Copilot real
al final. No se intenta retirar el temporal anterior cuya limpieza fue rechazada;
permanece identificado en el registro original.

Tras estas comprobaciones, V4-03 conserva su cierre técnico focal;
no acredita todas las garantías de 4.0 ni su eficiencia integral. Pendientes:
V4-04, comparación H2/S8, aceptación por host y decisión de release. No se actualiza
la versión, instala, activa, publica, integra ni crea commits. Avanzar a V4-04 queda
fuera de esta ejecución de revisión.
