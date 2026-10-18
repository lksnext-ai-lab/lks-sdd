# Captura y conservación diagnóstica explícita

Implementación local V4-04 sobre método 3.1; todavía sin publicación/instalación.
Añada `--capture-dir` al CLI v3. El destino es una carpeta dedicada externa al
consumidor y distinta del destino de output. Sin la opción no se crea una captura.

```text
python scripts/lks_sdd.py v3 context ROOT --input context.json --view operational --capture-dir EXTERNAL
python scripts/lks_sdd.py usage-inspect EXTERNAL
python scripts/lks_sdd.py usage-inspect EXTERNAL --recover-capture
```

`usage_context.run_id` selecciona la ventana. Si no se declara, se reutiliza el ID
de esa carpeta o se crea uno nuevo. Otro ID/consumidor en la misma carpeta provoca
fallo de captura, nunca sobrescritura. Un fallo diagnóstico se informa aparte del
resultado normativo y no deshace ni oculta efectos. La opción no concede permisos,
revisión, aceptación ni migración. Runtime o fuente incorrectos siguen bloqueando.

El formato externo `lks-sdd-diagnostic-run/1` usa `run.json`, objetos por SHA-256 y
entradas inmutables con nombres acotados. Cada entrada conserva observaciones,
metadatos diagnósticos, materiales disponibles, bytes del input utilizado y stdout
UTF-8 preparado completo, incluida su referencia diagnóstica. Argv se conserva
como valores de la interfaz v3 serializados a JSON; shell, ejecutable, transporte
del host y recepción/lectura no se observan. No son tokens facturados.

También se conserva el resultado completo de la API, el output escrito y los
objetos referenciados de paquetes de entrada/salida disponibles en ese límite.
La contabilidad del descriptor no sustituye la de sus objetos. Para `context` se
intenta guardar además un fixture documental con el grafo, las raíces, las huellas
y los adjuntos. Si cambia durante la lectura, falta o excede el presupuesto, queda
declarado incompleto. La reproducción solo ejecuta el selector de confianza sobre
documentos aislados; no ejecuta código aportado ni reproduce una aplicación.

El input se lee una sola vez cuando se captura. Se incluyen cuerpos literales y
adjuntos recuperables comprobando sus huellas; materiales ausentes/cambiados y
sobres incompletos quedan indicados. No se ejecutan materiales importados ni se
siguen enlaces/reparse points. Los patrones de credenciales se rechazan sin
guardar sus valores; no se transforma una captura redactada en bytes exactos.

Los máximos son 1 MiB/1.000 observaciones por lote, 20.000 observaciones por ventana,
64 MiB y 10.000 archivos por carpeta, incluyendo archivos de publicación pendientes
y objetos no referenciados. Los fragmentos transitorios conservan su límite 64 KiB;
fuentes mayores se conservan como materiales hasta el límite global o quedan
incompletas. Estos límites nunca recortan el resultado operativo del consumidor.
Al leer/importar se acotan también las observaciones y bytes resueltos, incluidas
referencias repetidas; la deduplicación en disco no permite multiplicar el trabajo
de lectura más allá de los máximos de la ventana.

Cada lectura de ventana verifica físicamente una vez cada objeto distinto de
material, transporte o paquete antes de devolver el resultado. Rechaza referencias
conflictivas y corrupción; no conserva confianza ni bytes entre invocaciones.
Los lotes se leen y validan por cada referencia expandida y mantienen exactamente
sus límites acumulados. La lectura de archivo reserva su tamaño observado más un
byte para detectar crecimiento, conservando el rechazo por reducción o exceso.
Stdout capturado coincide con la serialización elegida, incluida la operativa en
una línea; el resultado completo de API se conserva por separado.

Una exclusión mutua de archivo protege cada publicación y sus límites. Se escriben
objetos completos con el helper existente, luego una entrada pending y finalmente
la entrada publicada. Los temporales del helper tienen nombres cortos dentro de la
carpeta explícita. Se reutilizan rutas extendidas Windows; no se cambia TEMP/TMP
global, no se crea otro servicio y los reintentos no alargan los nombres.
Recuperar publica solo entradas pendientes íntegras; no reejecuta la operación.
Su respuesta enumera en `writes` las entradas externas realmente publicadas;
repetirla no vuelve a escribirlas. Antes de añadir otra invocación se recuperan
las pendientes. Una copia pending distinta de su entrada publicada es una colisión
y bloquea la lectura, sin repararla ni ocultarla.
Un proceso abortado antes de preparar la entrada puede dejar objetos sin entrada:
no se inventa la observación que falta. La inspección no los elimina ni repara
corrupción y señala esos objetos sin entrada como una ventana incompleta, incluso
si contiene entradas anteriores válidas. Un proceso nuevo es otra invocación; repetir una publicación idéntica
es idempotente, reutiliza objetos y rechaza identidad/contenido conflictivos.

Conserve una carpeta por ventana en un área con finalidad, responsable y retención
declaradas. La captura no añade un borrado automático; conserve mientras haya
referencias/incidencias. Para este estudio se usa el área existente del plan y su
política de evidencia voluminosa 90 días tras cierre y registros ligeros duraderos.

En hitos ya autorizados se usan los comandos existentes con entradas breves:

```json
{"actor":"MEMBER-UID","capture_dir":"EXTERNAL"}
```

`v3 usage-record ROOT --input record.json --output packet.json` prepara todos los
lotes/materiales programáticamente en un único paquete del journal existente.
Aplicar exige la autorización exacta habitual. No conserve por cada consulta.
`usage-report` y `usage-export` aceptan también `capture_dir`; la exportación
reutiliza el paquete portable vigente, con causas/material adicional cuando lo
requiera su validador. `usage-inspect BUNDLE --reproduce` sigue siendo la vía de
reproducción documental explícita. Capturar no acredita por sí solo reproducibilidad
causal, evidencia esperada o aceptación por un host.

`usage-record`, `usage-report` y `usage-export` admiten `capture_entries`, una lista de identidades
de entradas, para seleccionar un caso acotado. La exportación admite hasta tres
fixtures documentales distintos, según el formato portable existente; una ventana
mayor exige seleccionar el caso. Las entradas omitidas siguen en la captura.
Una ventana sin observaciones conservables no devuelve `already-recorded`.

La identidad reproducida incluye texto y huellas de adjuntos. Cambiar un adjunto
sin actualizar la expectativa impide declarar la reproducción. La creación y
limpieza del temporal y el recorrido documental usan rutas Windows coherentes,
también cuando una raíz corta tiene descendientes largos. No se cambia TEMP/TMP.
Un paquete puede conservar y reproducir documentos y seguir `needs-material`:
si no hay un disparador contrastable, no se presenta como listo para investigar.

La importación de la carpeta siempre queda como `unverified-import`, incluso si
se lee en el proceso que capturó. Hashes acreditan integridad de bytes, no autoría.
La corrupción de recibos/objetos canónicos anteriores mantiene su bloqueo normal;
el adaptador no la rebaja a aviso ni modifica decisiones para conservar diagnóstico.
La contabilidad distingue input, argv, stdout preparado y espacio en disco; no
suma bytes deduplicados como tráfico ni presume recepción del host. Captura,
conservación, reporte y exportación se cronometran separadamente en la validación
focal; no equivalen a ahorro total o a la aceptación temporal S8.
