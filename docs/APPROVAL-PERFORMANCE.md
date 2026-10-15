# Rendimiento de identidades y aprobaciones — 3.4.3

La versión estable promueve el runtime de rc.3. La [promoción](plans/approval-performance/IMPLEMENTATION.md) declara la comparación incompleta y el coste de memoria restante; los comandos rc.3 siguientes reproducen su preparación histórica.

La petición de 2026-10-14 autoriza esta corrección de la fuente oficial y su
verificación local. [El plan](plans/approval-performance/PLAN.md) conserva alcance,
decisiones, tareas y pendientes. No cambia el contrato, el método ni el esquema.

## Índices reconstruibles

`Model` mantiene en memoria un índice multivalor de UID/alias y otro por tipo.
Las identidades únicas guardan directamente el elemento; las colisiones conservan
una tupla con todos sus candidatos. Un mismo elemento cuyo alias coincide con su UID cuenta una vez; dos elementos
que comparten alias, o un alias que coincide con otro UID, conservan el error de
ambigüedad. La selección de tipo ocurre después de resolver la identidad. Las
referencias cualificadas siguen exigiendo el proyecto canónico correcto.

Los índices se reconstruyen perezosamente tras modificar el mapa `elements`,
sustituirlo, añadir, sustituir o eliminar entradas, o editar/reemplazar `Element.meta`.
Se observan los mutadores normales de diccionario, incluidos `update`, `setdefault`,
`pop`, `popitem`, `clear` y `|=`. Cambiar UID, alias o tipo invalida ambos índices.
No se guardan respuestas negativas. Los observadores usan referencias débiles;
copiar profundamente un elemento o un item produce un borrador independiente. `deepcopy(Model)`
reconstruye su tabla y observadores, sin reutilizar los índices de la fuente.
Las copias superficiales conservan la compartición normal y registran los nuevos
propietarios, incluidas las altas posteriores en una tabla compartida.

La construcción privada reúne los elementos antes de conectar una sola tabla
observable, y la validación posterior observa el modelo completo. El caso común
guarda una referencia débil al propietario; los elementos compartidos conservan
todos sus propietarios. Reinicializar un elemento adjunto también notifica y
respeta la guardia antes de editar.

La auditoría de escrituras del runtime localiza la carga en `v3_contract._load`,
las altas/sustituciones prospectivas en `v31_review.overlay` y los datos resueltos
en `v3_inventories.resolve`. Authoring, gobierno, migración y reconciliación preparan
items independientes y vuelven a cargar staging; no alteran ocultamente el mapa.
`Model.at` y los lectores amplían `hashes`, el conjunto de fuentes leídas. Este
conjunto se mantiene separado de los índices semánticos.

## Reutilización durante una evaluación

`v3_evaluation.evaluation(model)` delimita una evaluación síncrona e inmutable de
un modelo. Los decoradores de aprobación, bases de tarea, cobertura y hechos abren
ese ámbito; las llamadas anidadas del mismo modelo lo reutilizan. Modelos diferentes
se aíslan por objeto, aunque tengan el mismo proyecto o UID. Un contexto heredado
por otra tarea asíncrona no comparte el estado mutable del padre. Tampoco se
comparten estados entre hilos, comandos ni evaluaciones sucesivas.

| Cálculo | Entradas | Reutilización |
|---|---|---|
| Pertenencias | Propuestas/features legacy y todas sus relaciones de ámbito | Un recorrido por evaluación mientras permanece admitido |
| Cierre global | Pertenencias, tipos, retirada, `global`, petición y dependencias completas | Un lector compartido |
| Descriptor | Lector global y secuencia de UID resueltos | Resultado por secuencia; copia defensiva en la API pública |
| Original heredado | Raíz del modelo, ruta física y hash esperado | Lectura, hash y análisis por ruta/hash; nunca por hash solo |

La guardia usa una revisión monótona, sin serializar el contrato en cada entrada
y salida. Se observan los metadatos completos (también estados, revisión, permisos
y revocaciones), cuerpos, rutas, líneas, datos resueltos, prosa, errores y avisos.
Los mapas y listas JSON anidados notifican antes de sus mutadores normales. Un
intento de cambio durante la evaluación incrementa la revisión y lanza `ContractError`
antes de editar; aunque el llamante capture el error, el ámbito y sus consultas
posteriores quedan invalidados. Restaurar el contenido no restaura la revisión.
Con varios propietarios compartidos se marcan todas sus revisiones antes de lanzar
el error, de modo que capturarlo no deja válido otro ámbito afectado.
Los campos y colecciones privados, y llamadas deliberadas a primitivas de base como
`dict.__setitem__` u `object.__setattr__`, no son APIs de edición admitidas.
Las mutaciones prospectivas ocurren antes de abrir el ámbito o después de cerrarlo.
Una evaluación nueva observa la nueva revisión. `hashes` crece con las lecturas
verificadas y conserva las comprobaciones físicas; no es una entrada semántica.

El modelo posee sus contenedores JSON observables. Los padres se enlazan débilmente;
desacoplar una rama no hace que su borrador invalide el modelo actual. Los inventarios
resueltos compartidos usan un único mapa observable por objeto físico en la carga,
con enlaces a sus eventos. La copia de un modelo conserva esa compartición dentro
de la copia y mantiene independencia respecto a la fuente. Las evaluaciones
simultáneas conservan su aislamiento; la guardia también rechaza una escritura
desde otro hilo mientras el modelo tiene una evaluación activa.

El almacenamiento temporal admite como máximo 256 entradas, 131.072 unidades
referenciadas (incluidas las claves de consulta) y 16 MiB de contenido de originales analizado. Aplica expulsión LRU y
omite la admisión de una entrada que excede el presupuesto; vuelve a calcularla sin
cambiar el resultado. Son límites de admisión de la reutilización, no un límite duro
de RSS de Python: el modelo, las estructuras de análisis, los observadores y
el resultado necesario siguen ocupando memoria. Permanecen los límites existentes
de contrato, lectura, inventarios, objetos y almacenamiento. Al salir, incluso por
excepción, se vacía el almacenamiento, se liberan sus referencias a modelo y tarea
asíncrona y se restaura el contexto. Las pertenencias públicas también se copian
para que modificar un resultado no altere cálculos posteriores. Las huellas de
originales se vuelven a observar en cada evaluación; un original modificado conserva
el resultado negativo de aprobación y las comprobaciones previas a materializar.

La aprobación tecnológica conserva el `all` de las decisiones individuales, con
`technology OR proposal` para cada tecnología. Unas pueden apoyarse en el primer
mecanismo y otras en el segundo. No se sustituye por una aprobación conjunta que
exija un mecanismo uniforme. El cierre y las obligaciones globales, fuentes inciertas,
dependencias y comprobaciones de revocación permanecen completos.

## Vigencia y materialización

Una evaluación opera sobre un snapshot en memoria, no bloquea ediciones externas.
Conserva cada ruta original y su hash en el conjunto de fuentes. `prepare` vuelve
a leer soportes, rechaza diferencias con las fuentes evaluadas y valida staging;
`apply` conserva comprobaciones frescas de precondiciones, inventarios, Git, sujeto,
caducidad, base confiable y transacción recuperable. Una caché de esta evaluación
no atraviesa esas fronteras. No se cachean permisos o decisiones entre comandos.
La prueba de cambio de original entre evaluación y preparación verifica el rechazo.

## Referencia y equivalencia

`tests/fixtures/approval-reference/manifest.json` vincula nueve módulos originales
a 3.4.2 y al commit `a657bf7b07461c8b03516f9adbb00bb7a6b9ed7c`; `original.zip`
conserva sus bytes. El worker comprueba inventario y cada SHA-256 antes de importar.
Es un oráculo de pruebas inerte: ningún comando operativo lo selecciona como runtime
ni lo instala como una versión alternativa en consumidores.
El snapshot inerte adicional `rc2-original.zip` conserva la candidata anterior
con manifiesto y hashes. Los diez módulos modificados se vinculan a la fuente
medida; los módulos no afectados se comparten en la comparación con 3.4.2. Los procesos separados impiden mezclar imports de ambas versiones.

La comparación diferencial conserva resultados, errores, dependencias, fuentes,
decisiones, pendientes y descriptores. Los UUID generados usan una secuencia
determinista, el reloj de generación se fija antes de importar los módulos y ambos
workers usan `PYTHONHASHSEED=0` para fijar el orden de recorridos de conjuntos. En la
prueba focal solo se normaliza la raíz temporal declarada; no se borran campos.
El benchmark de operaciones usa las mismas rutas absolutas de fixture/staging/base
confiable en cada par, de modo que también compara íntegros los hashes de paquetes,
previews, receipts y resultados. No se confunde igualdad de contenido con aprobación
humana ni se afirma equivalencia para entradas no ensayadas.

## Carga y runtime fijado

La carga consulta atributos frescos de cada componente en Windows con
`GetFileAttributesW`; no conserva una caché de confianza de rutas. Rechaza reparse
points y repositorios anidados y conserva el camino portable cuando la API no
puede observar la entrada. La lectura elimina una consulta redundante de tamaño,
pero conserva `lstat`, apertura e identidades antes/después de leer, permisos y
límites. Se ensayan sustitución, crecimiento y fallo de permiso. La API devuelve
los atributos del enlace mismo, según la
[documentación de Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileattributesw).
El doctor del runtime verifica todos los archivos e inventarios e instrucciones,
calculando SHA-256 por bloques de 64 KiB salvo los bloques de instrucciones que
requieren su normalización anterior. Ningún archivo se omite por su tamaño.

## Reproducción y resultados

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v3_approval_performance `
  --module test_v3_code_inventory --module test_approval_load_regressions
python -B -X utf8 tests/measure_approval_rc3.py `
  --package tests/reports/lks-sdd-3.4.3-rc.3-development/lks-sdd-plugin-v3.4.3-rc.3.zip `
  --output tests/reports/rc3-isolated.json
python -B -X utf8 tests/check_approval_cli_hosts.py --host codex `
  --package tests/reports/lks-sdd-3.4.3-rc.3-development/lks-sdd-plugin-v3.4.3-rc.3.zip `
  --output tests/reports/rc3-host-codex.json
python -B -X utf8 tests/check_approval_cli_hosts.py --host copilot `
  --package tests/reports/lks-sdd-3.4.3-rc.3-development/lks-sdd-copilot-plugin-v3.4.3-rc.3.zip `
  --output tests/reports/rc3-host-copilot.json
```

El runner secuencial crea contratos sintéticos 100/5, 500/15 y 1500/35 con
reglas globales y contenido literal completo. Compara 3.4.2, rc.2 y candidata en
cuatro órdenes ABC, CBA, CAB, BAC: cada pareja tiene ambos órdenes dos veces.
Mide carga, contexto, identidad, clasificación, dependencias, aprobaciones
actuales/heredadas y el ciclo público de biblioteca. Otro caso conserva 80 eventos
que comparten 6000 rutas. Cada worker es frío, con diez segundos de reposo,
CPU Python, working set muestreado cada 10 ms, pico acumulado y contadores.
La auditoría nativa antes/después identifica procesos Python por PID y creación;
CIM identifica las líneas de comando para su huella; cualquier proceso Python
ajeno impide comenzar, aunque el nombre de su script no parezca un runner.
Durante cada worker un monitor nativo observa aproximadamente cada 500 ms: admite
solo el worker propio y sus descendientes. Una identidad Python
nueva ajena o un error de observación invalida el grupo ordenado completo, que se
conserva como excluido y se repite tras recuperar aislamiento. El coordinador espera
si hay otro proceso Python activo; no lo interrumpe. `--resume` reanuda únicamente con
los mismos inputs/configuración y descarta el grupo incompleto del checkpoint.
No controla la frecuencia de CPU, antivirus, caché de disco u otra actividad nativa.

El ciclo CLI compara rc.2 y el ZIP exacto de la candidata en cuatro pares
alternados. Ejecuta doctor, validación, readiness, presentación requerida y
preparación/aplicación de siete operaciones hasta aceptación, con comprobaciones
físicas actuales. La evidencia contiene la salida de un test sintético ejecutado.
Cada comando es un proceso frío. El wrapper de medición importa el contrato y
fija UUID/reloj antes del dispatcher; su coste está incluido en ambas versiones.
Los recorridos funcionales de los paquetes se repiten sin ese wrapper. Un Job
Object se asigna antes de reanudar su
hilo inicial. Se registra CPU Python y CPU de todo el árbol, incluidos Git hijos,
pico de memoria comprometida del job y working set observado del proceso principal.
La memoria comprometida y el working set son magnitudes distintas; no se suman.
El muestreo puede perder picos breves de RSS. La CPU de biblioteca no suma hijos.

La equivalencia de biblioteca compara hashes semánticos completos sin eliminar
campos. El CLI conserva todos los envelopes, paquetes y receipts, y valida cada
hash y guard propio. Compara el estado funcional final completo, readiness,
acciones, estados y rutas escritas; excluye solo `usage` de esos estados. Las
rutas escritas conservan categorías y multiplicidad, normalizando únicamente las
direcciones SHA-256 de objetos CAS y snapshots históricos ligados a cada runtime;
las rutas de elementos canónicos se comparan literalmente. Las
identidades de runtime, hashes de paquetes y telemetría difieren deliberadamente
entre versiones, por lo que no se afirma igualdad binaria entre sus envelopes.

Los perfiles cProfile/tracemalloc son diagnósticos separados y no se mezclan con
los tiempos finales. El [informe de preparación](plans/approval-performance/IMPLEMENTATION.md)
identifica la evidencia externa final. Los resultados se escriben fuera del
runtime para no reconstruir después el paquete exacto medido. Los volúmenes no
reproducen datos privados ni garantizan la latencia comunicada. No se afirma ahorro
de tokens ni aceptación del rendimiento para entradas no ensayadas.

Las comprobaciones de ambos paquetes y adaptadores son técnicas en proyectos
propios temporales: incluyen runtime modificado, ausente y extra, launcher ajeno
y fuente obsoleta, sin escrituras ante rechazo. La activación conversacional real
de Codex/Copilot y la aceptación humana se mantienen `not-run`. Preparar, comprobar,
publicar e instalar siguen siendo estados separados; el gate estable no se amplía.
