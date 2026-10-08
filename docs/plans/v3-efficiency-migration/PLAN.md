# Plan de implementación: eficiencia documental y funcionamiento v3.1

Fecha: 2026-10-08. Revisión: 3. Rama: `codex/document-storage-growth`.
Base Git: `628d15c3d8759c6deb70d88bda9f045562c485a6`, con el desarrollo local previo de almacenamiento documental.
Estado: **implementación y validación técnica local completadas; entrega preparada**.
La petición «implementalo» autoriza implementación, pruebas y documentación. No acredita una release, instalación,
migración de consumidores ni aceptación humana. Los IDs siguientes son tareas de
mantenimiento del plugin, no registros de un proyecto consumidor.
La autorización posterior «hazlo», el 2026-10-08, incluye crear el commit de esta
entrega e integrarlo en `main` local; push y publicación permanecen separados.

## Objetivo y alcance

Entregar un recorrido operativo 3.1 que detenga la duplicación de contenidos e
inventarios, reduzca trabajo y texto innecesarios y permita migrar conservando el
contrato completo. La próxima release del plugin hará del formato 3.1 y método
3.1.0 el destino para trabajo nuevo o continuado; su número de release se decidirá
separadamente. Una versión del plugin no sustituye por sí sola el runtime fijado.

Se cubren proyectos nuevos, v2 con schema 2.0 y métodos 2.0.0/2.1.0, proyectos 3.0
y proyectos 3.1 con runtime anterior, con y sin lock. El destino operativo quedará
con runtime local fijado y adaptadores comprobados; no bastará declarar el método.
Las consultas permanecen sin escrituras.
Antes de modificar documentación o código mediante el recorrido gobernado se
comprueba el destino; una migración preparada no equivale a ejecución autorizada.
La garantía abarca las entradas soportadas y sus instrucciones; no controla un
clon desconectado, un runtime antiguo ni ediciones realizadas fuera del plugin.

Markdown sigue siendo canónico; el índice se reconstruye. Identidades, decisiones,
actores, fechas, autorizaciones, evidencias, hashes y enlaces se conservan. No se
seleccionan perfiles, controles, personas, dispensas ni tecnologías por defecto.
Los inventarios técnicos pueden referenciar objetos exactos; las obligaciones
normativas y la prosa sin clasificación no se sustituyen por resúmenes.

Se mantienen las seis skills y su invocación implícita. No se añaden servicios,
MCP, conectores, hooks, apps ni agentes ejecutables; tampoco fichas, snapshots o
informes documentales por cada comando. No se modifica `specs/canonical/` para
acomodar diferencias de implementación. Se excluyen publicación, instalación,
push y operaciones sobre consumidores de este desarrollo local. La creación de
commits y la integración local se autorizan al cerrar la entrega, por separado.

## Hechos de partida y decisiones de implementación

- La baseline publicada del [inicializador](../../../scripts/v3_authoring.py) creaba 3.0.
  La [migración](../../../scripts/v3_migration.py) convertía v2 a 3.0, creaba un miembro
  inicial y rechazaba revisión independiente. La [adopción 3.1](../../../scripts/v31_review.py)
  y el [instalador](../../../distribution/install.py) completaban un segundo corte.
- La migración usaba el lector v2 limitado a 32 MiB y contaba historia en un inventario
  de hasta 10.000 entradas. CLI/prepare/apply transportaban JSON/base64 y expandían
  cambios en memoria; la entrada CLI está limitada a 64 MiB. Un lector fragmentado
  aislado no resuelve esos límites. El cambio de runtime solo se exigía con lock.
- [El desarrollo previo](../../DOCUMENT-STORAGE.md) aporta objetos por contenido,
  inventarios referenciados, compatibilidad histórica y diarios recuperables.
  No implementaba este recorrido obligatorio ni todos los inventarios v3.
  Sus mediciones pertenecen a aquella implementación; no prueban el resultado nuevo.
- Se reutilizarán esas piezas y las transacciones existentes. No se eliminará el
  trabajo local por inferencia. Los cambios v2 se revisarán para conservar lectura,
  migración y recuperación sin desarrollar otro canal operativo v2.
- La conversión y configuración se prepararán directamente en staging 3.1 y se
  aplicarán como un paquete final. El procesamiento por fragmentos no activará
  formatos intermedios ni dispensará la validación global.
- Se conservará el historial por unidad de v3. Se añadirán manifiestos y objetos
  donde sean necesarios para reconstruir bytes, rutas, prosa y recursos de los
  estados documentales preservados; no se copiará el árbol completo en cada hito.
- Las copias históricas existentes permanecerán. Se respaldarán íntegramente las
  fuentes que vaya a modificar el corte; la historia conservada sin modificación
  tendrá referencias verificadas y dependencias de retención explícitas. No se
  promete recuperar inmediatamente el espacio ocupado por las copias antiguas.
- Formatos de almacenamiento/transporte y capacidades mínimas del lector estarán
  versionados aparte del método. El candidato rechazará mezclas incompatibles,
  referencias desconocidas o vacías. Leer datos antiguos no implica que un runtime
  antiguo admita los nuevos: esa dirección tendrá compatibilidad explícita, sin
  prometer un rechazo que un lector ya publicado no implemente.
- Mantener los presupuestos actuales: 32 MiB de Markdown activo, 64 MiB por objeto,
  16 MiB y 50.000 entradas por inventario, 32 MiB de inventarios únicos por carga y
  20.000 miembros por sujeto v3, también al resolver referencias. Los presupuestos
  adoptados son 256 MiB de Markdown original, 100.000 fuentes/2 GiB, estado de
  32 MiB y descriptor de 64 MiB; el paquete limita bytes únicos a 2 GiB.
  fragmentar datos no permite eludir límites agregados ni coherencia global.

## Interfaces implementadas

- **Sujeto e inventario:** el resolver devuelve el mismo `{scope, files, digest}`
  semántico para datos inline y referenciados. Todas las comparaciones y hashes de
  guard consumen esa vista. La externalización usa una lista de campos/rutas y tipos
  operativos reconocidos; no convierte cualquier JSON, requisito o metadata similar.
  No se cambia el algoritmo normativo para ocultar una
  diferencia; conversión y normalización conservan hash original, hash de destino
  y prueba de correspondencia. No se promete igualdad del SHA de un archivo reescrito.
- **Paquete y diario:** descriptor acotado y versionado, con manifiestos y objetos
  referenciados verificables. El hash autorizado liga el conjunto completo, incluidos
  guards, fuentes, configuración y runtime. Preparar/aplicar/recuperar no expanden
  todo el payload en RAM ni recopian historia en staging. El paquete guardado es
  portable y completo: no depende de un temporal efímero o ruta personal. La
  preparación usa staging/salida explícita; publica objetos en el consumidor al aplicar.
  El guard comprueba también pertenencia exacta al inventario, incluida historia
  referenciada: añadir una fuente tras preparar no pasa por tener intactos los hashes
  de las fuentes anteriores. Las personalizaciones y el código ajeno al corte se preservan.
- **Validación del origen:** factorizar parsers y reglas existentes; no crear un
  segundo validador permisivo. Separar representación técnica de contenido y
  descriptores originales. Sobre orígenes que caben en el lector normal, ambas
  rutas deben producir igual veredicto y contenido conservado, normalizando solo
  IDs/fechas nuevos. Se comprueban relaciones/identidades entre fragmentos.
- **Entrada operativa:** comprobar formato, configuración/política de la petición,
  capacidades y lock, no solo una cadena de versión. Sin lock, identificar el origen
  y preparar el runtime local dentro del mismo corte autorizado. Clasificar consultas,
  escrituras, migración y recuperación; esta última no depende del runtime sustituido.

## Recorrido y fronteras

1. Detectar formato canónico, índice, runtime y transacciones pendientes; diagnosticar
   sin escribir. Un índice ausente o contradictorio no autoriza inicializar o convertir.
2. Preparar el destino y agrupar únicamente decisiones que falten. Conservar las
   personas históricas y confirmar las funciones actuales, incluida independencia.
3. Revisar un paquete ligado al origen exacto, configuración y runtime comprobado.
   Reutilizar una autorización vigente que cubra ese paquete; no pedir una por comando.
4. Verificar el destino completo, aplicar con diario y validar documentos, runtime,
   adaptadores y recibo antes de informar el corte como completado.
5. Revaluar la operación solicitada con las identidades mapeadas y contexto actual.
   Conservar contenido y planes equivalentes; no convertir permisos históricos en
   autoridad actual. Los pendientes bloquean solo la porción afectada.

El estado distingue origen pendiente, paquete preparado, corte aplicado y capacidad
de continuar la operación seleccionada. Se deriva de fuentes y recibos, sin otro
archivo de estado duplicado. Durante una interrupción se bloquean escritores; las
consultas explican el estado y permiten localizar la recuperación.
La transacción es recuperable, no una sustitución atómica de todo el filesystem:
el diario pendiente protege estados mixtos. Una decisión cambiada invalida el
paquete; no se regenera y aplica con una autorización anterior. Una consulta puede
mostrar diagnóstico parcial explícito si el origen no carga, sin declarar conformidad.
Una transacción v2 pendiente se recupera o revierte mediante su formato de origen
antes de preparar otro corte; no se convierte su diario a mitad de aplicación.

La comprobación común se conecta tanto a CLI y comandos heredados soportados como
a las seis skills antes de la primera edición gobernada. Las bibliotecas v2 que
v3 reutiliza internamente no obligan a reescribir el núcleo. Las entradas públicas
v2 del runtime nuevo quedan para diagnóstico, conversión y recuperación; traducciones
de comandos solo se admiten con equivalencia probada de argumentos y autoridad.

## Tareas y dependencias

Cada tarea incluye regresiones focales y la documentación de su interfaz necesaria.
EM-01–EM-09 están completadas técnicamente; EM-10 queda preparada para publicación
y observación autorizadas por separado. Las rutas señalan componentes a revisar, no una obligación
de editar todos los archivos. Responsable de ejecución: mantenimiento del plugin;
no se asignan personas ficticias, agentes paralelos, fechas de fin ni duraciones.

| ID | Trabajo y componentes | Depende de | Resultado exigido |
|---|---|---|---|
| EM-01 | Revisar el diff previo, cerrar las cuatro interfaces y presupuestos, y preparar fixture pequeña/baseline. `tests/test_v3_migration.py`, `test_v3_distribution.py`, `test_v31_review.py`. | — | Huecos reproducidos, formatos/capacidades y disposición del trabajo previo definidos en este plan y pruebas; sin otro expediente. |
| EM-02 | Inicialización 3.1 y cortes pequeños v2/3.0→3.1, con/sin lock, equipos y políticas de peticiones. Conectar desde aquí la comprobación común mínima. `v3_authoring.py`, `v3_migration.py`, `v3_policy.py`, `v31_review.py`, schemas, instalación/distribución y `runtime_doctor.py`. | EM-01 | CLI distribuida con paquete único, runtime fijado y una operación autorizada viable; revisión independiente conservada, interrupción básica probada y proyecto nuevo directamente 3.1. |
| EM-03 | Inventarios compartidos de baseline, sujetos y dependencias; actualizar contrato, Git, workflow, lifecycle, quality, verification, storage y `v31_*`. | EM-01 | Vista semántica equivalente, algoritmo/digest conservados y todos los consumidores localizados actualizados; objetos compartidos sin fusionar observaciones. |
| EM-04 | Manifiestos de estados/recursos, originales y enlaces históricos, exportación aislada y lectura de historias/recibos anteriores. `content_store.py`, lectores históricos, contrato/storage/migración. | EM-02, EM-03 | Bytes y rutas reconstruibles, adjuntos versionados, alteraciones detectadas; historia existente intacta y sin segunda copia completa. |
| EM-05 | Transporte/diarios versionados y referenciados; lectura incremental de manifiestos y datos, publicación exclusiva y recuperación independiente. `v3_cli.py`, `v3_storage.py`, utilidades storage/path, distribución. | EM-04 | Caso cuyo payload base64 previo excede 64 MiB funciona con descriptor acotado; ninguna expansión global. Reintentos, integridad, conflictos y rollback del runtime probados. |
| EM-06 | Origen grande con reglas compartidas del lector normal y mapas técnicos externalizados; verificación global de fragmentos, inventario activo/historia y presupuestos. `v3_migration.py`, lectores estrictamente necesarios. | EM-02, EM-05 | Paridad de validación; >32 MiB por mapas y >10.000 archivos históricos convertidos. Exceso irreducible, corrupción entre fragmentos o presupuesto agotado bloquean sin truncar. |
| EM-07 | Completar comprobación común en dispatcher, CLI, entradas heredadas y seis skills; continuidad, políticas locales, instrucciones y adaptadores. `lks_sdd.py`, CLI/skills y distribución. | EM-06 | Matriz de entradas sin bypass; consultas conservadoras, recuperación accesible y trabajo independiente autorizado viable. Runtime anterior/incompatible no se usa silenciosamente. |
| EM-08 | Salidas concisas y detalles completos compatibles; hitos y referencias aplicables. `v3_guidance.py`, `v31_guidance.py`, `v3_cli.py`, contexto/referencias solo si hay repetición medida. | EM-03 | Comparación temprana con iguales bloqueos y obligaciones. No crear otra compresión si v3 ya emite una copia literal. Selector reducido sigue en comparación, sin caché persistente/telemetría. |
| EM-09 | Recorridos integrados y medición final focal; ampliar el generador temporal existente. Validar paquetes externos reproducibles, personalizaciones y rutas largas. Actualizar almacenamiento, migración, compatibilidad, validación y changelog. | EM-04, EM-06, EM-07, EM-08 | Cobertura AC-01–AC-18 completa, resultados vinculados a fuentes exactas, regresiones explicadas y limitaciones visibles. No se suman repeticiones como casos distintos. |
| EM-10 | Preparar entrega y observación de uso con el protocolo existente; describir actualización de consumidores y futura compactación. Separar evidencia técnica, uso real y publicación. | EM-09 | Código probado y documentación consolidada; estados humanos `not-run` visibles hasta observación real. Siguiente release y actualización tienen instrucciones recuperables y autorización propia. |

Orden con un ejecutor: EM-01 → EM-02 → EM-03 → EM-08 → EM-04 → EM-05 → EM-06 →
EM-07 → EM-09 → EM-10. Se prueba pronto el recorrido completo y el ahorro de salidas.
EM-03/08 no esperan la migración grande; la conexión mínima de entradas de EM-02 se
completa en EM-07. Cada porción se verifica al integrarla; la matriz final no pospone
la detección de fallos. No hay aprobación administrativa ni otro registro por tarea.

## Cobertura y criterios de aceptación

| Criterio | Propiedad y caso verificable | Tarea principal |
|---|---|---|
| AC-01 | Proyecto nuevo directamente 3.1; índice reconstruible; método, configuración, runtime fijado y adaptadores coherentes; sin dependencia de instalación global. | EM-02 |
| AC-02 | Cortes v2/3.0→3.1 con/sin lock; 3.1 con runtime anterior actualizado. Configuración de la petición y capacidades comprobadas; cambio solo del índice o mezcla de locks/lectores no acreditan el corte. | EM-02, EM-07 |
| AC-03 | Individual, equipo e independencia: funciones confirmadas, personas estables, sin revisor inventado ni rebaja de controles. | EM-02 |
| AC-04 | UUID/alias, actores/fechas, decisiones, autorizaciones y evidencias conservados; hash origen/destino y correspondencia explícitos. Transformar representación no renueva permiso ni disimula una diferencia normativa. | EM-02, EM-03 |
| AC-05 | Trabajo abierto conserva plan y alcance; reevaluación antes de continuar; un pendiente ajeno no bloquea porciones independientes autorizadas. | EM-07 |
| AC-06 | Orígenes publicados v2.0.0–v2.3.1 de las fixtures existentes; métodos soportados; legado 1.5 solo diagnóstico/ruta existente de conversión; origen desconocido falla sin mutar. No se añade conversión directa 1.5→3.1. | EM-02, EM-06 |
| AC-07 | Todas las entradas soportadas y seis skills aplican la misma política; comandos viejos no permiten bypass. Consultar, cargar una skill o actualizar el plugin personal no migra un consumidor. | EM-07 |
| AC-08 | Inline/referencias producen iguales mapas, scope y digest, también en dependencias, guards y antecedentes. Rechazo de ambiguos, ausentes, corruptos, cíclicos y formatos desconocidos; límites agregados aplicados a inventarios distintos, sin recomputar N veces el compartido. | EM-03 |
| AC-09 | N observaciones con un inventario idéntico conservan N identidades pero almacenan una sola copia de ese inventario. Crecimiento activo por registro pequeño, no proporcional al número de rutas repetidas. | EM-03 |
| AC-10 | Reconstrucción byte a byte de estados con documentos/recursos estables y cambios pequeños: altas, modificaciones, movimientos, retiradas y eliminaciones soportadas; prosa, interfaces, imágenes y evidencia preservadas. | EM-04 |
| AC-11 | Resolver enlaces físicos antiguos y referencias nuevas; adjunto histórico modificado/eliminado después sigue recuperable. Manifiestos, objetos y contenido alterados se detectan. Exportación no sobrescribe destinos. | EM-04 |
| AC-12 | Historia existente intacta; respaldo de fuentes modificadas; almacenamiento adicional medido aparte. Ninguna compactación, retirada de copia o garbage collection implícita. | EM-04 |
| AC-13 | Interrupción en cada clase de escritura: objeto, diario, documento, runtime, lock/cierre. Estado mixto bloquea escritores; recuperar/rollback externo y diarios antiguos funcionan. Falta de espacio, enlaces/junctions, repos anidados y trabajo posterior no causan pérdida. | EM-05 |
| AC-14 | Hash del paquete y fuentes exactas; cambios de contenido, inventario, rama o base invalidan aplicación. Reintento del mismo paquete idempotente; una nueva observación igual no se elimina. | EM-05 |
| AC-15 | >32 MiB por mapas y >10.000 archivos históricos convertidos; payload base64 previo >64 MiB sin elevar límites. Paquete portable aplicado tras retirar el staging de preparación. Paridad con lector normal y rechazo de corrupción/IDs duplicados/relaciones entre fragmentos; exceso irreducible bloquea sin falso `ready`. | EM-05, EM-06 |
| AC-16 | Vista compacta usada por skills con detalle y JSON completo compatibles; mismos bloqueos/decisiones. Contexto literal íntegro antes de actuar y tras chat nuevo/compactación; alcance incierto, globales y adjuntos conservados. Cada consulta deja idéntico inventario del consumidor. | EM-08 |
| AC-17 | Comparación del flujo completo: archivos, contenidos únicos, bytes incluyendo objetos/manifiestos/diarios, Markdown activo, texto emitido, operaciones, memoria/temporal y tiempos. Ahorro observado y regresiones justificados; tokens facturados solo si el host los expone. | EM-09 |
| AC-18 | Bundle externo correcto, adaptadores Codex/Copilot coherentes, hashes y personalizaciones conservados; guías de actualización y restauración. Gate técnico separado de aceptación humana, publicación y consumidores actualizados. | EM-09, EM-10 |

### Resultado local y límites de aceptación

La [evidencia consolidada](../../evidence/v3-efficiency-validation.json) identifica
110 casos distintos superados, sus fases y las fuentes congeladas de las mediciones.
No suma las repeticiones ni convierte estos ensayos en aprobación de release.

| Criterios | Comprobación realizada | Límite pendiente |
|---|---|---|
| AC-01–03 | Inicialización pública 3.1, perfiles explícitos, runtime fijado; cortes v2/3.0/3.1, con/sin lock y equipos independientes. Incluye v2 distribuido con plugin 3.1.0. | Identidades sintéticas; ninguna migración de consumidor. |
| AC-04–06 | Identidades, originales, autoridades y evidencias; continuidad de planes, tareas independientes, lectura de formatos publicados y rechazo de origen desconocido. | Autoridad histórica conservada no habilita ejecución nueva. |
| AC-07 | Dispatcher, aliases heredados en ambos órdenes, inicializadores antiguos y seis skills; runtime antiguo remite a actualización explícita. | No impide actuar desde clones/runtimes desconectados. |
| AC-08–09 | Inventarios inline/referenciados, campos normativos similares intactos, errores/formatos/presupuestos; ejecución/checkpoints comparten mapas sin fusionar observaciones. | Cada observación y manifiesto tiene metadata propia. |
| AC-10–12 | Reconstrucción exacta, recursos/enlaces antiguos y virtuales, movimientos/eliminaciones, destinos exclusivos y alteraciones detectadas; historia antigua intacta. | Compactación y recogida de objetos no ejecutadas. |
| AC-13–14 | Fallos inyectados en publicación/transacción/corte, diarios antiguos, recuperación/rollback, cambios posteriores, guards y reintentos; Windows real y rutas largas. | Fallos simulados no equivalen a ensayo físico de disco agotado ni corte eléctrico. |
| AC-15 | >32 MiB repetidos, >10.000 archivos históricos, paquete cuyo base64 anterior supera 64 MiB, transporte portable y validación global; exceso irreducible rechazado. | No se eleva el presupuesto ni se omiten documentos. |
| AC-16 | Vista completa literal, recibos vigentes, contexto de 180 requisitos íntegros, consultas sin escrituras y 12 rutas de instrucciones condicionadas. | Continuidad conversacional e invocación implícita reales: `not-run`. |
| AC-17 | Dos corpus v2/v3, igualdad normativa v3, objetos/metadata/diarios incluidos; archivos, bytes, cargas y preparación/aplicación, memoria Windows y coste pequeño de corte. | Pico temporal y tokens facturados: no medidos; tiempos locales concurrentes, sin atribución causal. |
| AC-18 | Bundles de desarrollo externos y validadores de paquete; mismo núcleo Codex/Copilot, personalizaciones y rollback comprobados. | Gate de commit limpio, publicación, instalación y aceptación humana: `not-run`. |

La revisión crítica eliminó del estado documental 300 fuentes de código usadas solo
como precondición: sus hashes y comprobaciones siguen completos. Los adjuntos y
evidencias documentales externos permanecen recuperables. El candidato integrado
pasó de 867 a 504 archivos; frente a v3 publicado el número aumenta porque se añade
una garantía de estados completos que aquel historial por unidad no proporcionaba.
La reducción de Markdown activo es 81,8 % y la del crecimiento en bytes 55,1 % en
la comparación integrada. La reproducción v2 reduce bytes retenidos 86,4 %, con
una mediana de carga 6,7 % más lenta: no se afirma mejora en toda operación.

## Fixtures, medición y validación

Usar generadores y `TemporaryDirectory`; no añadir grandes árboles ni proyectos
reales. Ampliar las suites existentes antes de crear otra batería permanente:
`test_v3_migration`, `test_v3_distribution`, `test_v31_review`,
`test_v3_workflow`, `test_v3_governance_quality`, `test_v3_integration` y
`test_document_storage`. Añadir solo casos que cubran una frontera o regresión real.

La fixture pequeña cubre migrar/configurar/autorizar/continuar/verificar con datos
sintéticos, incluido equipo. La fixture de volumen genera del orden de 830 rutas
estables, 13 operaciones sucesivas de autoría/corrección/replanificación y varios
checkpoints/ejecuciones con el mismo inventario. Otras variantes separan los límites:
>10.000 archivos históricos pequeños y >32 MiB activos por inventarios repetidos.
Incluir contratos API e imágenes con cambio posterior, nuevos adjuntos, enlaces
históricos, moves y deletes soportados; lo no soportado debe fallar conservando datos.

La comparación principal usa v3.1.0 publicado y el candidato sobre el mismo contrato
v3.1 e intención; la comparación v2 usa v2.3.1 solo para el coste de migración y el
problema original. Congelar tag/SHA, configuración de controles, generador y corpus
antes de medir. Baseline y candidato deben verificar el mismo alcance y requisitos.
El corpus de volumen conserva 800 funcionalidades ajenas sin cambios, como en
el incidente observado; su validación global y hashes completos se mantienen.
La prueba de cierre de obligaciones globales usa otros 180 requisitos íntegros.
Separar coste único de migración y operación posterior. Contar
todos los archivos y bytes, también objetos/referencias, sin confundir contenido
único con número de archivos. Medir generación, diagnóstico, preparación, aplicación,
recuperación y carga por separado, junto con el recorrido completo; distinguir
procesos CLI nuevos de reutilización dentro de una carga y esperas humanas.

Declarar antes de medir las repeticiones y condiciones; informar mediana, rango y
límites del entorno. En la fixture pequeña medir también lector normal y lector de
migración para detectar sobrecoste. Una regresión observada, incluida la del desarrollo
previo, se perfila y explica; si queda sin resolver, no se declara mejora de latencia.
No crear un benchmark como puerta de publicación ni igualar bytes a tokens facturados.
La aceptación estructural exige que los contenidos idénticos no se materialicen por
estado y que el Markdown no replique mapas completos; los manifiestos y observaciones
distintas tienen coste propio explícito. La agilidad real exige observación de host.
Para comprobar crecimiento, variar por separado el número de rutas N y de operaciones R:
inventario idéntico compartido una vez y coste activo de referencia por registro;
modificar un contenido añade sus bytes y metadata necesaria, sin otra copia del conjunto.
Reportar por separado almacenamiento antiguo conservado, respaldo nuevo y crecimiento.

Comandos de desarrollo, desde la raíz del repositorio:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v3_migration --module test_v3_distribution --module test_v31_review --module test_v3_workflow --module test_v3_governance_quality --module test_v3_integration --module test_document_storage
python -B -X utf8 scripts/validate_plugin_contract.py .
python -B -X utf8 scripts/validate_fixture_manifest.py .
git diff --check
```

Seleccionar durante el desarrollo los módulos/casos afectados; ejecutar el conjunto
focal al cerrar EM-09. Comprobar las 14 pruebas de humo y la regresión real de Windows
con los procedimientos de [VALIDATION](../../VALIDATION.md), sin reutilizar la
aprobación de la release 3.1.0 para otra release. El gate estable exige versión
aprobada y commit limpio integrado; no se ejecuta ni se declara superado desde esta
rama sin commit. Los ensayos Linux/macOS y humanos que no se ejecuten quedan `not-run`.

Para interacción e invocación implícita utilizar el protocolo de
[aceptación de host](../../V3-HOST-ACCEPTANCE.md): orden real de lecturas y ediciones,
decisiones agrupadas por persona, continuidad y ausencia de confirmaciones por
comando. Los tests CLI, fixtures y textos de skills no acreditan ese comportamiento.
La falta de participante/host no bloquea entregar el código local probado; sí impide
afirmar que la agilidad conversacional o aceptación humana estén acreditadas.

## Documentación, publicación y cierre

Actualizar [DOCUMENT-STORAGE](../../DOCUMENT-STORAGE.md),
[V3-MIGRATION](../../V3-MIGRATION.md), [COMPATIBILITY](../../COMPATIBILITY.md),
[V3-COMMON](../../V3-COMMON.md), [V31-REVIEW](../../V31-REVIEW.md),
referencias operativas de las skills y [VALIDATION](../../VALIDATION.md) solo donde
cambie comportamiento. Changelog para la nueva release. Una evidencia de desarrollo
consolidada y vinculada al runtime final recoge cobertura, mediciones y límites;
los informes previos no se reetiquetan como resultados del código nuevo.
Este plan se actualiza con estado/resultados, sin fichas ni reports por cada tarea.

La entrega local termina al completar EM-01–EM-09 y preparar EM-10, con diff revisado,
casos técnicos exigidos superados y los estados de uso real explícitos. Publicación,
instalación y migración de cada consumidor requieren su autorización correspondiente.
La ruta futura usa una release nueva y bundle reproducible: comprobar lock/configuración,
preparar paquete exacto con respaldo, aplicar corte, verificar runtime y continuar
solo trabajo cubierto. Instalar el plugin personal no actualiza runtimes compartidos.

Una futura compactación será otra operación: inventario completo de referencias
incluidos recibos/diarios, respaldo independiente, reconstrucción comparada y
restauración probada. Retirar copias exige una segunda acción explícita después
de verificar su conservación; no se borra un objeto aún referenciado.
Consolidar el plan cerrado en las guías activas conforme a
[MAINTENANCE](../../MAINTENANCE.md), sin retirar evidencia única durante este encargo.
