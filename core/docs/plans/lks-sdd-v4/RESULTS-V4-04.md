# V4-04 — Captura y conservación diagnóstica

Fecha: 2026-10-16. Plan 0.4. Ejecución autorizada tras validar la revisión de V4-03.
Base Git: `bf4d059c98826039097d606121ab6406d762fcc7`, más los cambios locales
validados de V4-03. La evidencia identifica los bytes de esta candidata sin crear
un commit ni cambiar la versión publicada 3.4.3.

## Resultado y funcionamiento

Se añade captura opcional mediante `--capture-dir`, en una carpeta dedicada fuera
del consumidor. Conserva observaciones, materiales disponibles, resultado completo
de API, input leído, objetos de paquetes referenciados, output y stdout UTF-8
preparado, incluida su referencia. Una consulta sin la opción sigue sin crear
diagnóstico persistente. La consulta capturada escribe solamente en ese destino
externo; las escrituras de output/paquetes elegidas expresamente siguen su canal.

El formato externo previsto `lks-sdd-diagnostic-run/1` usa objetos por huella y
entradas inmutables. `usage-record` prepara lotes y materiales directamente desde
la carpeta, en un único paquete del journal existente; aplicar conserva la
autorización exacta habitual. No hay un recibo canónico por cada consulta ni copiado
manual de observaciones con el modelo. `usage-report`, `usage-export` e inspección
autónoma reutilizan los mecanismos vigentes.

Para contexto se conserva un fixture documental: grafo, raíces, fuentes y adjuntos
comprobados. La prueba integrada retira texto e imagen originales, conserva los
lotes, comprueba el reenvío idempotente, exporta el caso y reproduce la selección
en otro proceso sin acceder al consumidor original. Reproducir documentos no
acredita ejecución funcional de una aplicación ni una causa general del incidente.

## Garantías y aceptación focal

| Criterio | Resultado técnico local | Evidencia |
|---|---|---|
| AC-06 | Superado en cobertura focal | Conservación con fuentes retiradas, paquete portable, reproducción independiente, interrupción, reintento, colisión, material ausente y límites. |
| AC-07 | Superado en cobertura focal | Igual cuerpo y recibo; snapshots sin cambios canónicos por consultar; fallos diagnósticos separados; corrupción canónica sigue bloqueando; efectos de aplicación conservados. |
| AC-08 | Superado en cobertura focal | Comparación de input/stdout exactos, contadores completos y procedencia; las importaciones quedan no verificadas y la recepción del host permanece no observada. |

No se amplían los máximos: 1 MiB/1.000 observaciones por lote, 20.000 por ventana,
64 MiB/10.000 archivos por captura/exportación y 64 KiB por fragmento transitorio.
Superar un límite no recorta el cuerpo normativo. Un fallo de captura se informa
sin cambiar el resultado, autoridad ni código de salida de la operación. Las
entradas incompletas y los materiales ausentes no obtienen una falsa declaración
de integridad. Los patrones de credenciales se rechazan sin guardar sus valores.

La recuperación explícita publica únicamente entradas pendientes íntegras, sin
repetir una aplicación ni modificar el consumidor. El bloqueo de archivo se libera
al terminar el proceso; no se confía en borrar un PID antiguo. Una interrupción
antes de preparar la entrada puede dejar objetos sin referencia: se señalan y
conservan, sin inventar una observación. Las entradas anteriores siguen disponibles.
Una carpeta con objetos huérfanos se inspecciona como incompleta; conservar/exportar
entradas válidas no recupera una invocación que nunca llegó a publicarse.

Windows reutiliza los helpers existentes, nombres acotados y rutas extendidas,
incluido el caso de raíz corta cuyos objetos descendientes superan 260 caracteres.
Se mantienen Unicode, espacios y reintentos sin crecimiento de nombres. No se
cambia TEMP/TMP global ni se reintenta la limpieza anteriormente rechazada.

## Verificación y revisión crítica

La cobertura combina 20 pruebas específicas de captura, 28 regresiones de
presentación/observaciones/bundles, tres de conservación/journal y el caso Windows
existente, más una prueba que construye, extrae y ejecuta ambos paquetes: 53 casos
distintos. Los resultados por campaña, repeticiones y fallos históricos se conservan
en el índice externo; no se contabilizan como intentos completos del estudio S1–S8.

Se corrigieron durante la validación la conservación del origen importado, la
vinculación de adjuntos al fixture independiente y la pérdida de observaciones al
proyectar errores mínimos. También se ajustó el ensayo para comparar el cuerpo
real seleccionado en Windows, sin confundir CRLF con pérdida de texto, y el punto
de interrupción inyectado. Las campañas fallidas permanecen visibles: el resultado
final de cada caso sustituye su dictamen, no borra el intento anterior.
La identificación temprana del consumidor respeta opciones anteriores a la
operación: un fallo del runtime tampoco puede crear una captura dentro de él.

La prueba de empaquetado verifica igualdad de los nuevos recursos y ejecuta captura
e inspección desde extracciones Codex/Copilot, sin instalación. Esto acredita el
runtime compartido empaquetado; el uso conversacional real de Copilot sigue pendiente
al final. El validador de contrato conserva lectores 1.5/2.0/3.0/3.1 y seis skills.
Los contratos canónicos, protocolos congelados e historial de V4-03 no se reescriben.

## Coste, límites y continuación

El archivo externo `phase-costs.json` registra tiempos separados de consulta con
captura, escritura de captura, preparación/aplicación de conservación, reporte y
exportación/inspección. La escritura de captura está incluida en la consulta y no
se suma dos veces; su contador excluye preflight y primera lectura del input.
Es una muestra sintética de componentes, sin comparación emparejada con 3.4.3 ni
garantía de latencia general. Guardar fuentes completas añade I/O y espacio; elimina
la reconstrucción manual pero todavía no demuestra ahorro neto de la tarea.

En el último caso retenido: consulta con captura 3,028 s (incluye 0,774 s de
escritura diagnóstica); conservación 7,684 s; reporte 0,369 s; exportación e
inspección independiente 2,388 s. Las fases sintéticas incluyen sus lecturas y
validaciones aplicables. No son una promesa de rendimiento ni un porcentaje de
ahorro. Hubo 125 ejecuciones de tests completadas y seis resultados fallidos
históricos; los 53 casos distintos tienen resultado final aplicable superado.

Se distinguen bytes de entrada, argv serializado, stdout preparado y espacio
deduplicado en disco. No se observan shell/ejecutable/transporte del host, recepción,
lectura, comprensión ni tokens facturados. La valoración humana sigue diferida al
uso real sostenido; el ahorro integral y S8 ≥20 % permanecen pendientes sin rebajar
umbrales. La captura tampoco aporta firmas ni acredita autoría de datos importados.

Área reutilizada: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-04`.
Contiene snapshot inicial/final, huellas, caso portable y captura retenidos, inspección
independiente, campañas y registro de recursos. La retención sigue la política del
estudio: evidencia voluminosa 90 días tras cierre, registros ligeros duraderos y
conservación adicional mientras haya referencias o incidencias.

El bloque tiene corte de 2.700 s desde 11:20:44Z, incluyendo preparación, fallos,
pruebas, esperas y reporte; el registro fija el tiempo real final. No amplía los
máximos de 48 intentos completos, 8 h humanas ni 12 h de entorno, ni M6 dos variantes/
cuatro horas compartidas. No se inicia otro intento completo ni variante M6. El
saldo histórico global continúa sin certificar; cerrar este bloque no prueba que
quepa toda la release restante.

Este cierre es técnico local de V4-04. V4-05 no se ha iniciado; requiere la decisión
de continuación prevista por el usuario. Siguen pendientes H2, ahorro completo,
incidente/S8, observación real de hosts y aceptación de 4.0. No hay cambio de versión,
commit, integración, push, publicación, instalación ni activación de esta candidata.
