# V4-03 — Presentación mínima y transporte compatible

Fecha: 2026-10-16. Plan 0.4 validado. Base: 3.4.3,
`bf4d059c98826039097d606121ab6406d762fcc7`.
**Entrega inicial histórica.** La revisión crítica encontró carencias y la corrigió:
consulte [el dictamen vigente y sus resultados](REVIEW-V4-03.md).
Los 37 tests y el 20,089 % siguientes describen la implementación anterior;
no deben atribuirse a la candidata corregida ni tomarse como ahorro con garantías completas.
El estado vigente se registra en [v4-03-progress.json](v4-03-progress.json).

## Hechos implementados

- Nueva opción explícita `--view operational` en el CLI v3 compartido. Compatible
  sigue siendo el valor predeterminado; la API de biblioteca conserva su resultado
  completo. No se modifica el selector de contexto ni las reglas normativas.
- La vista operativa entrega el cuerpo literal necesario una vez y sustituye solo
  el diagnóstico superior por `lks-sdd-usage-view/1`: procedencia, identidades,
  etapas, métricas y límites, sin textos de fragmentos/inputs/resultados repetidos.
  No filtra campos contractuales de negocio llamados `usage` o `usage_context`.
- `--details` permite emitir el diagnóstico íntegro. `--output` tiene prioridad
  sobre la presentación de compact/details: guarda el resultado API completo y
  muestra referencia/resumen. Se corrige el volcado duplicado compact+output.
- Apply/recover/rollback preparan sus observaciones antes de exportar. Un fallo de
  salida posterior a aplicar informa en la vista operativa de efectos y recibo,
  también con details; el error de salida no se presenta como reversión.
- Se reutiliza la compactación existente de decisión/review; no cambia la
  implementación que calcula o comprueba sus recibos. Consulta, preparación,
  autorización exacta, idempotencia y recuperación siguen en sus componentes actuales.
- La exportación de consultas usa los helpers existentes de rutas Windows. No se
  añaden temporales al producto, servicios, hooks, conectores, skills o procesos.
  El módulo común y su documentación están declarados en la distribución dual.

La [matriz de opciones](../../CLI-PRESENTATION.md) explica la precedencia completa.
Las nuevas operaciones compuestas y la captura externa V4-04 no se implementan aquí.

## Garantías y comprobación

AC-04/AC-05 están superados en el alcance focal de V4-03. Se cubren
24 combinaciones de compatible/operational, JSON, default/compact/details y salida
directa/exportada. Compact y details juntos se rechazan antes de exportar.

La cobertura focal incluye contenido largo y su negación final, impedimentos,
adjuntos no observados, fuente cambiada que invalida el recibo, campos de negocio,
diagnóstico incompleto, consulta sin escritura, preview externo, falta de
autorización, aplicación real, reintento, fallo de exportación después de aplicar,
observaciones exportadas y recuperación real de un journal interrumpido.

Han pasado 23 regresiones existentes de presentación, rutas y observación,
incluida ejecución de ambos modos desde extracciones Codex/Copilot del mismo núcleo;
y la regresión real existente de rutas largas de Windows. Estas ejecuciones no son
aceptación conversacional de Copilot, que sigue pendiente al final.

| Comprobación | Resultado y alcance |
|---|---|
| Pruebas nuevas V4-03 | 13/13 por último resultado: 12 en la segunda suite completa y la prueba Windows repetida tras corregir solo su preparación. |
| Presentación/rutas/observación existentes | 23/23. |
| Windows existente | 1/1, runtime y migración por rutas largas; 182,238 s de campaña, sin usarlo como benchmark. |
| Ambos paquetes tras el cambio de exportación | 1/1, repetición focal ya incluida entre las 23 pruebas únicas anteriores. |
| Contrato y diff | Contrato estático válido; diff revisado y sin errores de whitespace. |

Son **37 pruebas únicas**, 52 ejecuciones de tests en seis campañas completas y una
campaña interrumpida sin resultados recuperables. Se conservan los tres resultados
no satisfactorios de las dos primeras suites focales, sin contarlos como pasados.
El índice `verification-final.json` referencia los informes originales y consolida
el último resultado de cada test. El archivo `focal-final.json` conserva el resumen
de la segunda suite completa (12/13); no es el dictamen consolidado.

La primera ejecución focal completa tuvo dos problemas de prueba: comparación del
indicador de caché miss/hit entre llamadas distintas, y limpieza por ruta corta del
temporal de exportación larga. Se conserva su informe (11/13, dos fallos) y se
corrigen ambos: se compara todo el contenido excepto el indicador de caché y el
diagnóstico; se retira primero el subdirectorio propio por su ruta extendida. La
exportación larga había funcionado. La comprobación final añade Unicode y espacios.
La segunda suite completa tuvo 12/13: el chequeo de contención del caso Windows
se hacía antes de existir la ruta, por lo que no expandía su alias 8.3. Se prepara
la ruta propia, se registra su limpieza por ruta extendida y se comprueba su
contención real. Su repetición focal pasó; no hubo más cambios de producto.
Una invocación previa fue interrumpida al descubrir que importaba la clase de
pruebas integrales; no se usa como evidencia de éxito. El descubrimiento ya está
acotado a las 13 pruebas propias de V4-03.

## Ahorro y límites

Se comparan bytes UTF-8 completos de stdout, incluido su sobre diagnóstico, en dos
consultas sintéticas con el mismo estado documental. Se conservan los bytes y sus
huellas fuera del consumidor. El indicador de caché cambia entre llamadas y no se
confunde con una diferencia de contrato. La lectura del host permanece no observada.

| Muestra de consulta | Bytes completos de stdout UTF-8 |
|---|---:|
| Compatible | 17.288 |
| Operational | 13.815 |
| Diferencia observada | −3.473; **20,089 % menos** |

Una sola pareja de consulta no demuestra estabilidad o ahorro general. Este 20,089 %
de bytes no satisface el criterio S8 ≥20 % de **tiempo de recorrido completo**.

Esta medición es de transporte de una consulta; no mide tokens facturados, latencia
del recorrido, atención humana ni ahorro total de 4.0. Las observaciones completas
todavía se construyen en memoria antes de proyectarlas: V4-03 reduce lo emitido,
sin acreditar menor coste interno. La modalidad compatible conserva la duplicación
diagnóstica anterior, y el nuevo modo necesita elegirse explícitamente. Las futuras
instrucciones/operaciones deberán usarlo y comprobar su efecto integral.

La vista diagnóstica se declara incompleta como lote y no es importable como
observación íntegra. Sin output no se guarda automáticamente el sobre original;
pedir details en otra llamada produce otra observación. Exportar conserva las
limitaciones de captura originales. Estos límites quedan visibles; la conservación
externa programática pertenece a V4-04. El transporte añadido tras escribir el
archivo describe esta llamada y no se finge presente dentro del archivo guardado.

## Recursos, estado y pendientes

Se mantienen 48 intentos funcionales completos, 8 horas humanas y 12 horas de entorno;
M6 conserva dos variantes/cuatro horas dentro del límite global. Las regresiones
de componentes no se utilizan como recorridos emparejados S1–S8 ni consumen sus
plazas de comparación. No se ejecutan nuevos intentos completos del estudio.
El saldo histórico global sigue sin certificarse; no se reinicia ni se inventa.
Este bloque tiene corte de 2.700 segundos desde 10:13:31Z, incluyendo preparación,
pruebas, correcciones y entrega; sus ejecuciones concurrentes no se suman como
tiempo de pared. El registro final conserva duración y ejecuciones fallidas.

La limpieza del temporal propio `v4-03-export-r_cq2o90` fue rechazada por la revisión
automática con «blocked by policy», sin más motivo. Se conserva identificado en la
evidencia; no se insiste ni se limpia ningún temporal ajeno.

Pendientes: V4-04 y tareas posteriores, medición integral H2 y S8 ≥20 %, conservación
automática, aceptación real por host y percepción humana durante uso sostenido.
No cambian los protocolos congelados ni los resultados preparatorios históricos.
No hay actualización de versión, commit, integración, push, publicación,
instalación o activación. No hay decisión nueva necesaria para usar esta interfaz
local; avanzar a otra tarea requiere el siguiente alcance autorizado.

Evidencia externa reutilizada:
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-03`.
Incluye copia previa, procedencia, informes originales/finales, stdout sintético,
medición de componente y balance de recursos. Los archivos pesados conservan el
ciclo de vida del estudio; no se crea un soporte independiente nuevo.
