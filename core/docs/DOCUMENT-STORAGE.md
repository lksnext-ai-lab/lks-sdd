# Almacenamiento y funcionamiento v3.1

## Desarrollo 4.0: objetos agrupados

V4-21 añade la capacidad física `lks-sdd-object-zip/1`. Las referencias
`lks-sdd-object/1` y sus rutas lógicas `.lks-sdd/objects/sha256/<SHA256>` conservan
identidad, longitud y bytes. El lector común resuelve objetos sueltos y miembros
de `.lks-sdd/objects/packs/<SHA256>.zip`, incluidos guards, staging, historia,
inventarios y recuperación. Los Markdown canónicos no cambian de soporte.

El escritor agrupa directamente por transacción antes de publicar el diario
2.1; el lector sigue admitiendo diarios 2.0. Los ZIP son inmutables y usan
[`ZIP_STORED`](https://docs.python.org/3.11/library/zipfile.html#zipfile.ZIP_STORED),
nombres hash planos, orden y metadata técnica reproducibles. Objetivo: 8 MiB;
máximo 16 MiB, 8.192 entradas y 1 MiB de índice por paquete; índices acumulados
por evaluación hasta 16 MiB. Objetos mayores de 8 MiB o lotes unitarios conservan
el soporte suelto y el límite de 64 MiB. No se crea un catálogo persistente.

Cada cuerpo solicitado se comprueba por longitud/hash y las copias contradictorias
se rechazan. Al publicar se revisan también las copias sueltas o agrupadas que
hayan aparecido durante la escritura, antes de crear el diario. El localizador
solo conserva índices en memoria durante su evaluación;
aplicación y recuperación renuevan la observación física. Consultar no repara,
materializa ni elimina contenido. Staging agrupa también sus copias efímeras.

Distribución y runtime declaran la capacidad; se comprueba el lector fijado antes
y después de publicar cada ZIP. Un cambio incompatible detiene la operación antes
del diario; puede quedar contenido inmutable sin referencia, que no se borra ni
repara automáticamente. El CLI actual exige actualizar un pin anterior; la biblioteca de
compatibilidad mantiene escritura suelta sobre un almacén antiguo, y bloquea si
ese pin incompatible ya contiene ZIP. Una transacción de negocio no puede alterar
contenedores, tampoco mediante mayúsculas o alias cortos de Windows.

V4-14 ampliada comprueba la actualización interrumpida, su recuperación y la vuelta
al lector anterior antes de crear ZIP. Después, núcleo, diagnóstico e instalador
actual rechazan cambiar solo el pin: se necesita restaurar un respaldo completo
compatible o materializar y retirar paquetes con verificación. La primera vía está
probada en una copia sintética. V4-22 añade compactación explícita y restauración
independiente de objetos; no implementa un cambio automático al lector antiguo.
Los diarios 2.0/2.1 conservan su formato y la escritura de un corte hacia un
lector sin ZIP mantiene copias sueltas. Este desarrollo no acredita instalación,
publicación ni aceptación de host. [Evidencia](plans/lks-sdd-v4/RESULTS-V4-19-20.md#v4-14-ampliada--compatibilidad-y-recuperación).

## Problema y decisión implementada

En v2, `history_changes()` copiaba todas las fuentes de `model.hashes` en cada
autoría, corrección o replanificación. Comparten esa función `v2_authoring`,
`v2_features` y `v2_controls`; sus consumidores de enlaces y recuperación usan
ahora el lector común. El diario repetía escrituras en base64.
Por separado, ejecuciones y checkpoints incluían inventarios completos repetidos.
El límite de 32 MiB excluye historia: resolver el archivado no basta para resolver
el exceso de Markdown activo.

El destino público de la release 3.2.0 es schema 3.1 y método 3.1.0. Proyectos v2
se convierten directamente; 3.0 y 3.1 con runtime anterior preparan un corte
explícito con configuración confirmada y runtime fijado. Actualizar el plugin
personal no migra un consumidor. Las consultas no escriben ni migran.
Véase [el procedimiento](V3-MIGRATION.md).
El diagnóstico también admite v2 creado por la compatibilidad distribuida con
3.0.0/3.1.0. Sin lock, esa procedencia permanece `declared-in-index`, sin afirmar
que se haya verificado el runtime antiguo; el destino sí debe quedar fijado.

Se reutiliza el núcleo offline existente y se mantienen las seis skills.
Los requisitos, decisiones, prosa, identidades, actores, autorizaciones y evidencias
permanecen en Markdown canónico. Solo los inventarios técnicos reconocidos pasan
a referencias exactas de objetos, con versión, SHA-256 y longitud.
No se convierte JSON arbitrario ni se sustituyen obligaciones por resúmenes.

## Formatos, consumidores y compatibilidad

| Formato | Resultado en 3.2.0 |
|---|---|
| v3.1 operativo | Inicialización pública directamente 3.1; contrato/configuración/runtime comprobados antes de modificar. |
| v3.0 y v3.1 anterior | Lectura conservada; corte explícito a funcionamiento actual. No basta cambiar el índice. |
| v2 schema 2.0, métodos 2.0.0/2.1.0 | Lectura, diagnóstico y recuperación conservados; el trabajo público nuevo exige migración a 3.1. Bibliotecas internas continúan disponibles para conversión y compatibilidad. |
| v1.5 | Lectores, funciones de conversión existentes y recuperación conservados; no se añade conversión directa 1.5→3.1. Inicializadores/materializadores CLI antiguos no crean otro proyecto operativo legado. |
| Historias físicas existentes y migraciones anteriores | Permanecen intactas y legibles; el corte no las vuelve a copiar. |
| Diarios | Colección 2.0 existente; lectura de diario 2.0/base64 y 2.1/referencias. |

El lock declara capacidades de almacenamiento además del schema. El doctor
comprueba que coinciden con el núcleo fijado. Los runtimes antiguos no conocen
las referencias nuevas: no se garantiza lectura hacia delante ni rechazo seguro
por un lector ya publicado. Conserve el runtime anterior para rollback; no lo
use sobre estados nuevos fuera de ese procedimiento.

En 1.5, los snapshots de seguimiento son registros de hechos; no se encontró
el bucle de copias completas por operación de v2. La conversión de legado
conserva su respaldo de origen y no se rediseña como otro canal de escritura.
En v3, el historial existente archiva revisiones por unidad, por lo que se conserva
ese mecanismo y se añade la garantía distinta del estado exacto con recursos.

Representaciones versionadas:

- `lks-sdd-object/1`: bytes inmutables en `.lks-sdd/objects/sha256/<SHA256>`;
  referencia `{format,sha256,bytes}`. No acepta ubicaciones arbitrarias.
- `lks-sdd-inventory/1`: mapa completo `{files:{ruta:hash}}`. Baseline,
  archivos y hashes técnicos de EXEC/CKPT, sujetos `{scope,files_ref,digest}`
  y artefactos de dependencias comparten objetos idénticos.
- `lks-sdd-state/1`: estado independiente de fuentes documentales, prosa,
  índice, recursos y dependencias leídas. Un manifiesto identifica hasta 64 partes
  inmutables de rutas a objetos; partes estables se comparten entre estados.
  No hay cadena de deltas. Se admite también el manifiesto inline de este formato.
- `lks-sdd-history-cas/1`: compatibilidad del historial v2 por manifiestos.
  Los árboles físicos anteriores siguen admitidos.
- `lks-sdd-packet/1`: descriptor portable y directorio adyacente de objetos.
  Payload y diario leen/publican un objeto acotado cada vez. JSON/base64 anterior
  sigue siendo legible sin expandir todos los bytes decodificados simultáneamente.
- `lks-sdd-migration-inventory/1`: catálogo completo de fuentes originales,
  hashes y disposiciones; su digest debe coincidir con el snapshot de origen.

El resolver devuelve el mismo sujeto completo `{scope,files,digest}` a guards,
workflow, calidad, revisión e integración, incluyendo dependencias. El cache es
local a una carga y valida cada objeto distinto. La metadata canónica permanece
sin expandir: no se modifica el algoritmo de digest normativo para ocultar el
cambio de representación. La conversión registra hashes originales y destinos;
reescribir un archivo no conserva su SHA de bytes.

## Historial exacto, enlaces y recuperación

Se conserva la historia v3 por UID/digest para decisiones y aprobaciones existentes.
Los estados completos añaden la reconstrucción exacta de archivos y recursos sin
materializar otro árbol por operación. Altas, modificaciones, moves y deletes
se representan mediante el mapa de cada estado; un recurso retirado permanece
recuperable en su estado anterior.

Las rutas virtuales `history/states/<SHA256>/tree/<ruta>#ancla` resuelven bytes
verificados. También siguen resolviéndose los enlaces físicos anteriores y las
rutas virtuales CAS v2. Una copia física contradictoria no oculta corrupción.
Los previews fijan manifiestos, partes y objetos necesarios para los enlaces.

Consulta o exporte un estado v3 mediante `state-history`:

```json
{"state":"<SHA256>","destination":"<directorio-nuevo-externo>"}
```

```powershell
python -B -X utf8 scripts/lks_sdd.py v3 state-history <project-root> --input <consulta.json> --json
```

Omitir `destination` consulta el inventario exacto. Exportar exige un directorio
nuevo fuera del consumidor y publica solo un árbol completo y verificado.
No sobrescribe documentación activa ni destinos existentes.
El estado abarca fuentes documentales protegidas; no es un backup de todo el
código, Git, archivos ajenos o toda historia que el estado no haya leído.
Las transiciones separan las precondiciones de código del respaldo documental:
sus hashes y comprobaciones frescas siguen en el paquete, mientras que el estado
conserva documentos, recursos, dependencias canónicas y adjuntos presentados.
La evidencia externa indicada expresamente también conserva sus bytes. Así no se
archiva código ajeno al estado documental por aparecer en un inventario de ejecución.

Cada escritura mantiene autorización por hash exacto, fuentes, pertenencia al
inventario, rama/base y guards semánticos. La validación global del destino y
del runtime ocurre en staging antes de aplicar. Una interrupción deja un diario
durable; el estado mixto bloquea operaciones normales. Recuperar/revertir conserva
las comprobaciones de identidad, contenido y trabajo posterior.

Objetos y diario pendiente se publican desde temporales completos con fsync y
creación exclusiva. No se reemplaza un objeto corrupto. Un fallo anterior al diario
puede dejar objetos sin referencias, sin autoridad. Rollback nunca elimina objetos
compartidos. No se promete atomicidad simultánea de varios archivos, bloqueo
distribuido entre clones ni durabilidad acreditada ante cortes de energía.
La exportación exclusiva se ejecutó en Windows; Linux/macOS tienen pruebas de
despacho/rechazo, pero no aceptación de un host real.

## Presupuestos y origen de gran volumen

| Recurso | Límite |
|---|---:|
| Markdown activo normalizado | 32 MiB |
| Objeto individual | 64 MiB |
| Inventario técnico individual | 16 MiB / 50.000 entradas |
| Inventarios técnicos distintos por carga | 32 MiB |
| Sujeto v3 | 20.000 miembros |
| Estado v3 | 100.000 fuentes / 32 MiB de metadatos |
| Catálogo completo de migración | 250.000 rutas / 64 MiB de metadatos |
| Descriptor portable | 64 MiB |
| Payload portable, bytes únicos | 2 GiB |
| Markdown original del migrador v2 | 256 MiB |
| Fuentes documentales originales de migración, incluidas históricas | 250.000 rutas / 2 GiB de contenidos únicos / 16 GiB de lectura física |

Se conservan además los presupuestos previos de documentos, Git, catálogo y
colección transaccional. Los manifiestos CAS v2 conservan 4 MiB/10.000 fuentes;
la inspección de su catálogo conserva 128 snapshots/16 MiB históricos.

El migrador de gran volumen utiliza los mismos parsers, identidades, relaciones,
enlaces y validaciones globales v2. Normaliza únicamente mapas operativos conocidos
antes del límite activo. Cuerpos y decisiones irreducibles que aún excedan 32 MiB
siguen bloqueados; no se truncan ni se omiten verificaciones.
El catálogo se enumera de nuevo, rechaza enlaces/junctions/repositorios anidados
y comprueba identidad/tamaño antes y después de cada lectura.
El límite de contenido único se calcula con hashes de bytes recién leídos;
todas las copias físicas conservan su ruta y se verifican individualmente.
La enumeración y los guards de aplicación/recuperación admiten el mismo número
de rutas. El límite de lectura física controla el coste del escaneo sin confundirlo
con el volumen deduplicado. Los límites normales de contrato, inventario técnico,
estado, descriptor y escrituras no cambian.
El lector solicita tamaño observado más un byte, evitando reservas de 64 MiB
por cada archivo pequeño. No hay cache persistente de confianza.

## Eficiencia documental del conjunto del plugin

Las salidas de operaciones muestran resumen y hash; el paquete íntegro queda
disponible mediante `--output` o `packet_directory`. Trace conserva motivos,
actores y referencias, con paginación, sin volver a emitir los mapas compartidos.
Las seis skills enlazan una única regla común: una consulta no genera documento;
un checkpoint registra un hecho nuevo, impedimento o relevo, no cada comando.
No se fusionan observaciones distintas ni se suprimen intervenciones normativas.

La validación de aprobaciones reutiliza, dentro de una evaluación, el cierre completo
de obligaciones globales. Evita recalcularlo por cada unidad; cambiar cualquiera
de sus contenidos invalida la conformidad. No hay cache entre evaluaciones.

v3 ya ofrece contexto literal y vistas paginadas. Este cambio no añade otra capa
de resúmenes, fichas, telemetría ni selección reducida no acreditada. La reducción
de bytes emitidos se puede medir; tokens facturados y esfuerzo humano requieren
observación del host. No se afirma una implementación óptima universal.
El crecimiento por contenidos nuevos, observaciones y metadatos necesarios sigue
teniendo coste y límites; no se promete acumulación ilimitada.

La mejora de presentación integrada organiza las instrucciones por evento:
se lee la guía aplicable y sus dependencias, con el contenido completo disponible.
La [medición de instrucciones](plans/specification-review-presentation/evidence/instruction-measurement.json)
compara esa selección con leer las nueve guías de la misma funcionalidad; no
equipara la versión anterior, con menos funciones, ni caracteres con tokens.

## Reproducción, resultados y límites

Las fixtures se generan en directorios temporales; no se incorporan árboles grandes.
`test_document_storage` conserva regresiones históricas y `test_v3_efficiency`
añade corte público 3.1, lectura con >32 MiB de mapas, >10.000 archivos históricos
conservados, paquetes cuyo base64 excede 64 MiB, estados exactos, corrupción,
partes compartidas, pertenencia, interrupción y rollback.
Las suites existentes comprueban autoridad, revisión, evidencia, calidad,
integración, aceptación separada y distribución.

Los resultados de la primera corrección local v2 se conservan como
[evidencia anterior](evidence/document-storage-review-measurement.json);
no prueban el candidato v3 actual. Aquel caso pequeño redujo almacenamiento un
83,2 % y Markdown activo un 48,8 %, pero preparación/aplicación fueron un 20,7 %
más lentas. No se extrapola al incidente original.

El ensayo de volumen del núcleo de almacenamiento utiliza runtimes congelados
antes de integrar la presentación de decisiones; no prueba por sí solo el conjunto
final. Compara v3.1.0 y esa fase del candidato sobre el mismo contrato v3.1 e incluye
objetos/manifiestos/diarios. Sus parámetros son 800 documentos, 30 recursos, 300 archivos de código,
tres rondas, dos checkpoints por ronda y 13 operaciones comparables de archivo:
los documentos estables representan otras funcionalidades sin cambios. Se validan
todos los documentos y se compara su contrato normativo completo; no se inventan
800 obligaciones adicionales para la tarea pequeña. La cobertura global y su
invalidación se comprueban separadamente con 180 requisitos completos.

```powershell
python -B -X utf8 tests/measure_document_storage.py --format v3 --baseline v3.1.0 --documents 800 --resources 30 --resource-bytes 16384 --code-files 300 --rounds 3 --checkpoints 2 --output "$env:TEMP/lks-v3-efficiency.json"
```

La baseline v3 solo conserva revisiones por unidad: el candidato añade estados
documentales completos recuperables. Por ello los archivos históricos por sí solos
no comparan la misma garantía. Se informa el almacenamiento completo y la igualdad
del contrato normativo. La variante `--format v2 --baseline v2.3.1` reproduce el
archivado completo anterior con las bibliotecas de compatibilidad, sin habilitar
un canal público operativo v2. Los tiempos son observaciones locales de Windows;
los bytes son lógicos, excluyen bloques del filesystem y deduplicación de Git.
La ejecución técnica no acredita agilidad conversacional ni aceptación humana.

La reproducción del problema original con 800 documentos y 13 snapshots v2 dio:

| Medida | v2.3.1 | Compatibilidad del candidato |
|---|---:|---:|
| Archivos de historia y recuperación, incluidos objetos | 10.208 | 957 |
| Contenidos únicos en ese almacenamiento | 902 | 944 |
| Bytes de historia y recuperación | 103.322.031 | 14.034.538 |
| Markdown activo, 824 archivos | 2.547.561 | 1.924.179 |
| Mediana de tres cargas, segundos | 16,49 | 17,60 |
| Preparación total de 13 archivados, segundos | 886,31 | 567,15 |
| Aplicación total de 13 archivados, segundos | 1.681,11 | 670,88 |

Se reducen un 90,6 % los archivos retenidos y un 86,4 % sus bytes. La cuenta de
contenidos únicos incluye la metadata nueva: su aumento no es pérdida documental.
La carga v2 observada fue un 6,7 % más lenta en su mediana; no se afirma mejora de
latencia en toda operación. La muestra usa recursos de 16 KiB y no reproduce los
549 MiB del consumidor. Es un ensayo de bibliotecas de compatibilidad, no una
autorización para continuar operando proyectos v2 con el plugin actual.

La comparación integrada v3 usa 32 documentos estables, 30 recursos, 300 archivos
de código y 23 operaciones, de ellas 13 comparables de archivo. El digest del
contrato normativo completo coincide. El runtime de cada fase está congelado;
la baseline ya completada se reutilizó, ligada a su evidencia, configuración y
generador, para comprobar la mejora final sin repetir aquella ejecución.

| Medida v3, incluyendo objetos/manifiestos/diarios | v3.1.0 publicada | Candidato integrado |
|---|---:|---:|
| Archivos totales materializados | 129 | 504 |
| Contenidos únicos | 104 | 345 |
| Bytes totales al terminar | 3.638.989 | 2.311.540 |
| Crecimiento neto durante las 23 operaciones, bytes | 2.835.359 | 1.271.868 |
| Markdown activo, 84 archivos | 525.960 | 95.725 |
| Mediana de tres cargas, segundos | 1,343 | 0,637 |
| Preparación total de 23 operaciones, segundos | 346,52 | 241,54 |
| Aplicación total de 23 operaciones, segundos | 287,84 | 188,66 |
| Máximo Working Set observado, bytes | 52.015.104 | 42.991.616 |

El crecimiento neto se reduce un 55,1 % y el Markdown activo un 81,8 %. El número
de archivos v3 aumenta porque la baseline guardaba solo revisiones por unidad:
el candidato añade estados exactos de documentación, recursos y dependencias,
objetos de recuperación y metadata compartida. Comparar solo su carpeta de historia
ocultaría esa diferencia. Una revisión de las cuentas eliminó el respaldo innecesario
de 300 fuentes de código; conserva sus hashes, alcance y verificaciones completas.
Ese ajuste redujo 867 a 504 archivos respecto al candidato integrado intermedio.
Los tiempos son observaciones concurrentes y la baseline se midió antes: no acreditan
una reducción causal de latencia ni un ahorro facturado de tokens.

El ensayo pequeño del corte directo v2→3.1, incluyendo runtime, midió 39,13 s de
preparación y 66,91 s de aplicación; recuperación tras interrupción, 0,93 s.
Tres cargas del mismo origen dieron medianas de 0,183 s con el lector normal y
0,165 s con normalización. No es una comparación causal de latencia: hubo otras
pruebas concurrentes y la primera carga incluye calentamiento. El runtime ocupa
8.820.908 bytes. El Markdown de ese origen mínimo pasó de 4.526 a 14.261 bytes:
la configuración y procedencia necesarias de v3 tienen coste inicial. El caso
grande comprueba reducción de mapas repetidos, sin prometer que toda migración
reduce cualquier documentación de partida.

```powershell
python -B -X utf8 tests/measure_v3_efficiency.py --output "$env:TEMP/lks-v3-migration-cost.json"
```

Resultados, fases y cobertura de 110 casos distintos superados se conservan en
[la evidencia consolidada](evidence/v3-efficiency-validation.json). Incluye la
medición de volumen del núcleo previa a la integración, separada del ensayo
integrado final y de las regresiones posteriores de entradas inválidas y migración.
Estas pruebas de desarrollo no acreditan el gate de una release nueva.

## Publicación, consumidores y compactación explícita en desarrollo 4.0

La implementación y sus mediciones se completaron en `codex/document-storage-growth`
antes de crear commits. El 2026-10-08 se autorizó por separado crear el commit e
integrarlo en `main` local. Esa integración no autoriza push, publicación ni instalación.
La evidencia conserva las fases anteriores; la versión publicada 3.1.0 no contiene
esta corrección. Para distribuir: comprobar la integración, asignar y aprobar una versión nueva,
ejecutar el preflight/gate desde commit limpio y generar/validar los bundles
reproducibles según [VALIDATION](VALIDATION.md). Codex y Copilot incluyen el mismo
núcleo y capacidades; nunca se corrige una caché instalada.

En cada consumidor, diagnosticar contrato/lock, preservar respaldo recuperable,
confirmar personas/perfil/controles, preparar el corte con el bundle compatible,
autorizar sus bytes exactos, aplicar, validar doctor y continuidad, y observar el
uso real. No se actualizan consumidores en este desarrollo. Instalación personal,
corte local, permiso de tarea y aceptación son evidencias separadas.

V4-22 mantiene todos los objetos válidos, aunque no se conozcan sus referencias.
El preview fija objetos, paquetes, pin, protegidos, respaldo ZIP independiente,
destino nuevo de restauración y reserva de espacio. El alcance acotado admite
hasta 50.000 objetos. El flujo /1 conserva 64 MiB lógicos por operación; /2,
incorporado en 4.0.1, aplica 64 MiB/4.096 objetos por lote. Objetos de más de 8 MiB
permanecen sueltos. Archivos desconocidos dentro del almacén conocido bloquean;
los demás directorios del proyecto quedan fuera de la retirada.

Desde el CLI fijado compatible, `v3 store-preview` recibe un JSON con `backup_dir`
y `restore` para /2 (`backup` conserva /1), ambos fuera del consumidor, y guarda su
resultado con `--output`, también fuera de respaldo/restauración/staging.
`v3 store-compact --input <preview> --authorize <hash>` publica y comprueba los
paquetes, el respaldo y la restauración byte a byte. Conserva los originales y
el diario pendiente. Solo `v3 store-recover --authorize <hash>
--authorize-removal <mismo-hash>` permite retirar sus duplicados físicos exactos.
No se usa `--apply` ni la autorización de una tarea funcional para esa retirada.

Los diarios `lks-sdd-store-maintenance/1` y `/2` ocupan el mismo
`.lks-sdd/transaction.json` que el negocio. Un guard del sistema operativo
serializa su recuperación y se libera al terminar el proceso; no es otro diario
ni permite iniciar un segundo escritor. La recuperación de negocio distingue el
formato, conserva los diarios 2.0/2.1 y nunca concede autorización de retirada.
Los paquetes y el recibo se publican sin reemplazar archivos existentes; se
comprueban otra vez los originales y sus copias antes de retirarlos. La
restauración usa un staging identificado en el preview, recuperable tras corte.
En /2 el respaldo cubre todos los objetos lógicos, incluidos grandes y ya
empaquetados. `store-recover --status` no escribe; antes de la primera retirada,
`--finalize-without-removal` permite conservar originales y liberar el slot con
recibo explícito, sin certificar un respaldo parcial. Véase [UPGRADE-4.0.1](UPGRADE-4.0.1.md).

La validación conserva el inventario inicial, verifica cuerpos y referencias,
restaura todos los originales y exporta un histórico representativo. No repite
la materialización de cada estado. No hay GC, borrado por edad, compactación
automática ni retirada de runtimes. Se informan por separado archivos activos,
bytes, respaldo, restauración de prueba y Git. La validación sintética no acredita
instalación, publicación ni aceptación de host.
