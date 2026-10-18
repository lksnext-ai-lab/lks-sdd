# Revisión crítica correctiva de V4-05

2026-10-16. Plan 0.4. Alcance autorizado: revisar y corregir V4-05 antes de
V4-05A. Este último no se inicia. Se conservan el informe y las evidencias de la
entrega inicial; este dictamen los sustituye solo en los puntos corregidos.

## Hallazgos contrastados

| Hallazgo | Riesgo anterior | Corrección y evidencia |
|---|---|---|
| Transacción iniciada después de cargar el modelo | La consulta podía devolver `ready` con una transacción pendiente, sin haber cambiado aún los Markdown. | Comprobar la ausencia de transacciones al comenzar y terminar el contraste físico. La consulta bloquea sin recuperar, borrar ni sobrescribir el diario concurrente. |
| Declaración de runtime capturada demasiado tarde | Un cambio entre la comprobación inicial y la lectura posterior se asumía como parte de la base válida. | Capturar las declaraciones antes de validar el método y contrastar el lock leído con esa huella inicial. |
| Declaración de runtime comprobada antes de la última validación | Un cambio durante esa validación final podía dejar `ready` vinculado a la declaración anterior. | Contrastar de nuevo las declaraciones después de validar el runtime. Una validación aislada positiva no sustituye la coherencia de toda la consulta. |
| Base declarada anterior a las lecturas históricas | El contrato podía incluir fuentes históricas en su snapshot y `basis.source_snapshot` seguir declarando otro snapshot. | Vincular la base al snapshot del contrato completo, después de contrastar sus archivos, y registrar `checked_at`. |
| Evidencia de ambos adaptadores demasiado estrecha | Se comprobaban archivos de ambos ZIP, pero se ejecutaba dos veces el mismo runtime sintético, sin extraerlo de cada paquete. | Contrastar todo el inventario del runtime y ejecutar los bytes extraídos sucesivamente de cada ZIP mediante el CLI fijado. Es una prueba de distribución sintética; no instala ni observa los hosts. |

Las reproducciones anteriores a la corrección dejan cuatro fallos contrastados:
transacción, declaración inicial, declaración final y snapshot histórico. Se conserva
además un primer caso histórico mal preparado que alteraba las condiciones de la
tarea; se corrigió su fixture antes de aislar la incoherencia real. No se cuenta ese
fallo de montaje como prueba del defecto ni se eliminan los logs fallidos.

Los cambios funcionales de esta revisión se limitan a `v4_work_prepare.py`. No cambian
los evaluadores de permisos, las transiciones, los validadores de calidad ni las
guardas de aplicación existentes. La consulta no materializa operaciones ni añade
autoridad. El contrato original, los protocolos congelados y las seis skills se conservan.

## Dictamen vigente

**Revisión incompleta: V4-05A no puede iniciarse con este dictamen.** La batería
revisada termina con 12/13 casos positivos y un fallo real en ruta larga de Windows.
Los cuatro defectos de coherencia quedan corregidos y sus pruebas pasan; se
conserva abierto el fallo Windows, sin convertirlo en aceptación con reservas.

## Comprobación de garantías

El cierre focal y las huellas exactas constan en `review-verification.json` y
[el registro actual](v4-05-progress.json). La campaña de revisión repite los límites
concurrentes corregidos, coherencia histórica, diferencial con consultas individuales,
porción independiente, captura y adjuntos, ausencia de autorización, índice opcional,
timeout Git, vigencias, contadores internos y distribución pública.

El caso Windows ejecuta el CLI público desde un consumidor/runtime con ruta superior
a 260 caracteres y falla: Git devuelve «cannot change to ... Filename too long».
La consulta devuelve `blocked` y no declara `ready`. La aserción posterior de
huellas de ese caso no llega a ejecutarse al fallar la expectativa de éxito;
la ausencia de mutaciones se acredita en los otros casos focales, no en ese paso.
El caso de distribución reforzado, extraído de ambos ZIP, sí pasa. Su limpieza usa rutas
extendidas y se limita al árbol temporal creado por la propia prueba. No cambia
TEMP/TMP globales ni elimina temporales o evidencias anteriores. Este caso complementa
la prueba con TEMP largo de V4-04; no equivale a una campaña universal de Windows.

Una preparación sigue siendo una instantánea informativa. Se detectan cambios en
los límites observados y se retira `ready` cuando la base deja de ser coherente.
No se promete atomicidad de lecturas ni bloqueo distribuido: los contrastes ocurren
en un intervalo. Un archivo puede cambiar después de su contraste, incluso antes de
terminar la consulta. Antes de materializar se reevalúa con las guardas actuales;
`checked_at` indica el fin del recorrido, no una fotografía atómica del sistema.
Las intervenciones de petición y sus páginas no autorizan otras tareas. Si no se
puede derivar ese recorrido se conserva la causa, sin inventar un recorrido completo;
la porción preparada se delimita por sus tareas explícitas y sus propias condiciones.

## Revisión de los resultados y del ahorro

Los 59 casos positivos de la entrega anterior eran resultados acumulados de varias
candidatas, como ya advertía su informe. No representan una batería íntegra ejecutada
sobre la última fuente. Esta revisión identifica por separado las ejecuciones sobre
su candidata, los casos anteriores reutilizables y las reproducciones negativas.
No convierte un resultado histórico en una nueva ejecución.

Se repite S8 sobre la fuente corregida y se conservan los hashes de sus componentes:
338 elementos de entrada, 319/319 comprobaciones literales positivas, prosa incierta
y fuentes canónicas sin cambios. La base y el contrato devueltos tienen el mismo
snapshot. La consulta termina `ready` en 31,010 s; preparar el entorno consume otros
16,687 s, contabilizados aparte. No se ejecutan implementación, prueba funcional,
cierre ni integración de S8 y no se consume un intento funcional completo del estudio.

Se mantienen una carga de modelo, un ámbito de cálculo, dos selecciones internas de
contexto y 14 llamadas Git. Eso no significa una sola lectura física: subsisten las
validaciones del runtime, contrastes de archivos, creación del sobre diagnóstico,
captura y entrega. Los contadores instrumentados no miden todo el I/O, CPU, memoria,
tokens facturados, recepción del host ni esfuerzo humano.

El fallo Windows ocurre en el helper Git existente al observar el consumidor.
No lo corrige habilitar `core.longpaths` solo en la invocación ni usar el alias
8.3 probado: Git también falla al recuperar su directorio actual. No se modifica
configuración global ni se añade un workaround no verificado. La compatibilidad
Git/Windows en rutas largas queda como corrección pendiente antes de V4-05A,
con regresión en `test_public_prepare_under_long_windows_consumer_path`. La
conservación temporal de V4-04 sigue acreditada en su alcance; no acredita este
nuevo recorrido público completo. No se rebaja la prevención de rutas largas.

La latencia observada no forma una pareja comparable con la medición anterior;
no se calcula ahorro entre ambas. Ahorro total y mejora S8 ≥20 % permanecen
pendientes en los hitos previstos. La valoración humana continúa diferida al uso
real sostenido y la observación de Copilot se mantiene al final.

## Presupuesto y continuación

Cota de revisión: 20 minutos desde las 13:53:31Z, incluidos lecturas, preparación,
fallos, corrección, verificación y reporte. Costes y campañas en
`review-resource-ledger.json`; el saldo global histórico sigue sin certificar.
Se mantienen 48 intentos completos, 8 h humanas, 12 h de entorno y M6 ≤2 variantes/4 h.
Esta revisión no añade intentos funcionales completos ni variantes M6 y no reinicia
los contadores históricos. La cota del bloque no acredita saldo global disponible.

Se reutiliza el área de evidencia V4-05 del estudio H1 y se conservan su snapshot
previo, logs y registro inicial. No se ejecutan limpieza de evidencia, integración,
commits, push, instalación, publicación ni activación. V4-05A requiere cerrar el fallo Windows y su autorización
posterior; V4-06 y siguientes siguen pendientes.
