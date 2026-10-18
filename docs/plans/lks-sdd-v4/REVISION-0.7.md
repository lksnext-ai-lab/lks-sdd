# Plan 4.0 — revisión crítica 0.7 propuesta

**Validación posterior:** el usuario valida 0.7, 10 h adicionales y dos recorridos;
autoriza primero V4-19/V4-20 y exige resultados antes de continuar. El
[hito A está verificado en alcance sintético](RESULTS-V4-19-20.md).
[Estado y presupuesto vigentes](v4-19-20-progress.json). La redacción de propuesta
que sigue y su JSON se conservan como definición del plan validado; no son el
registro de ejecución. Posteriormente el usuario autoriza V4-21 y una plaza final adicional sin nuevas horas. V4-21 está revisada, V4-14 ampliada verificada y V4-22 completada en compactación/recuperación local. La retirada sintética tuvo autorización separada del preview exacto. V4-15, V4-16 y V4-18 completan su alcance técnico y los paquetes de desarrollo; aceptación completa, aprobación de versión, integración y gate estable siguen separados. Véase el resultado y registro compartidos, incluida su revisión crítica final.

Fecha: 2026-10-18. Sustituye la **propuesta** [0.6](REVISION-0.6.md), sin ejecutar
el plan. Mantiene las cuatro tareas, las seis mejoras y los 56 criterios totales.
Solo se actualizan documentos de planificación. Registro: [REVISION-0.7.json](REVISION-0.7.json).

## 1. Qué corregir del plan 0.6

| Hallazgo | Consecuencia | Corrección incorporada |
|---|---|---|
| Formato de paquete propio y catálogo global mutable protegido por cada transacción. | Aumenta código, escrituras, pruebas y el riesgo de que el catálogo impida recuperar su propia transacción. | ZIP estándar inmutable con índice interno; sin catálogo persistente obligatorio. Localizador en memoria, acotado a la evaluación. |
| Mezcla de compactación, grafo de referencias y recolección de contenido. | Obliga a decidir qué historia eliminar para reducir archivos. | Compactar todos los objetos válidos conservando identidades y bytes; retirar solo sus copias físicas verificadas. La eliminación de contenido queda fuera. |
| Compatibilidad del lector se comprueba después de la migración. | Orden incorrecto aunque el grafo no tenga ciclos. | Comprobar capacidad y lectura dual **antes** de convertir o retirar copias. V4-14 ampliada precede a V4-22. |
| Objetivo del 50 % sin fijar composición del histórico. | Un proyecto con poco contenido compactable no puede alcanzarlo; un fixture escogido después puede aparentar éxito. | Congelar composición y calcular el máximo ahorro antes de escribir. El 50 % se exige en el histórico representativo fijado, no se promete para cualquier repo. |
| Los 407 archivos son un censo final, no un contador de todas las creaciones temporales. | Mezclar métricas produce comparaciones inválidas. | Conservar ese denominador para altas persistentes; medir temporales y picos por separado. Prohibir publicar primero un objeto suelto por fragmento y compactarlo al final para cumplir la cifra. |
| Revalidación amplia y detalle insuficiente sobre la evidencia reutilizable. | Repite recorridos, setups y controles ya cubiertos. | Ocho familias focales, un fixture grande reutilizable, dos recorridos completos como máximo y un único gate final. |
| Estimación de 10,2–20,4 h sin limitar el prototipo ni las iteraciones. | El bloque caro puede crecer antes de saber si el diseño funciona. | Propuesta de 6–10 h adicionales, con máximo de 10 h, prototipo de 45 min y 90 min de recuperación protegidos. Son cotas, no promesa de terminar. |

Prioridad invariable: **V4-19/20 desbloquean el cierre con objetos sueltos**. No
dependen de compactar ni de resolver el host de Windows. Resolver solo el límite
no completa la corrección del crecimiento documental.

## 2. Almacenamiento mínimo suficiente

- Markdown canónico, actores, decisiones, autorizaciones, evidencias e historia por
  UID permanecen en sus ubicaciones y con sus identidades. No se fusionan registros.
- Los objetos pequeños nuevos se agrupan directamente por transacción en
  `.lks-sdd/objects/packs/<SHA256>.zip`, con miembros cuyos nombres son exactamente
  sus hashes SHA-256. ZIP sin compresión; índice del propio ZIP, sin formato binario
  diseñado por el plugin. Sin archivos de índice por objeto ni por prefijo de hash.
  Orden y metadata técnica ZIP se normalizan para que el mismo lote produzca los
  mismos bytes, sin modificar el contenido original ni sus fechas documentadas.
- Se conservan las referencias `lks-sdd-object/1`. El lector busca objetos sueltos
  y entradas empaquetadas y verifica longitud/hash de cada cuerpo utilizado.
  Resuelve también las rutas lógicas usadas por fuentes, guards, staging e historia;
  cambiar solo `read_object` sería insuficiente.
- Localizador derivado solo en memoria durante la evaluación. Se enumeran nombres
  e índices de paquetes una vez por evaluación, sin leer todos sus cuerpos ni
  mantener cache de autoridad entre comandos. Consultar no crea ni repara archivos.
- Se conserva el diario de negocio 2.0/2.1 y sus referencias. Preparar todos los
  cuerpos necesarios y publicar sus paquetes **antes** de publicar el diario;
  recuperación puede encontrarlos sin un catálogo global. No se cambia el formato
  del diario de negocio salvo necesidad demostrada que obligue a revisar este diseño.
- La compactación requiere un registro físico mínimo, versionado y acotado,
  `lks-sdd-store-maintenance/1`: preview exacto, respaldo, paquetes, originales y fase.
  Usa el mismo slot exclusivo local de transacción; el recuperador distingue este
  registro del diario de negocio. No se crean dos locks independientes que puedan
  admitir escritores a la vez. La lectura compatible precede a su activación.
  Esta operación no relaja la prohibición de borrar o alterar objetos mediante
  una transacción de negocio.

Capacidad física propuesta: `lks-sdd-object-zip/1`; no se heredan los formatos
pack/catalog de 0.6. Método 3.1.0 y esquema canónico 3.1 permanecen. El soporte se
declara en distribución/runtime y se valida antes de ofrecer escritura nueva.

Límites: paquete completo ≤16 MiB; objetivo de 8 MiB, hasta 8.192 entradas y
1 MiB de índice por paquete; metadata de índices acumulada ≤16 MiB por evaluación.
Dividir lotes antes de exceder un límite. Objetos >8 MiB conservan almacenamiento
suelto y el límite actual de 64 MiB. Lotes sin objetos nuevos no crean paquetes;
si agrupar no reduce archivos, se permite el objeto suelto. Mantener las cotas
existentes de lectura, inventarios, staging y transacciones.

No usar extracción general de ZIP: aceptar solo nombres hash planos, sin enlaces,
directorios, duplicados, cifrado ni métodos de compresión distintos del acordado.
Comprobar tamaños, rangos y estructura antes de leer; rechazar cuerpos alterados o
ubicaciones contradictorias. Comprobar hash del paquete al crearlo, compactar y
exportar; las lecturas operativas comprueban el cuerpo solicitado y su índice sin
hashear repetidamente todos los cuerpos ajenos. No se debilita el guard de sus sujetos.

Riesgo que permanece: recorrer muchos índices puede resultar caro. El fixture grande
y la comparación de costes deben detectarlo. Si exige un catálogo autoritativo,
otro formato de diario o ampliar límites para pasar, se detiene el prototipo y se
revisa el diseño; no se incorpora automáticamente esa complejidad. Un servicio de
trazabilidad externo, compresión, compactación automática y GC quedan fuera de 4.0.

## 3. Tareas, orden y puntos de control

| Tarea | Trabajo concreto | Dependencias técnicas | Cierre |
|---|---|---|---|
| **V4-19 · P0** | Separar clasificación/límite elegible; captura acotada solo para `ls-files`; conservar invocación Git, rutas largas y controles compartidos. | V4-02A/B, ya disponibles en alcance técnico. | AC-45–47 |
| **V4-20 · P0** | Usar fixture y runtime sintéticos oficiales; cancelación, sucesora y cierre nativos; procedimiento para el caso real. | V4-19. | AC-48–49; presentar hito A. |
| **V4-21 · P1** | Lector dual, publicación agrupada y referencia lógica común; prototipo de guards/staging/diario antes del escritor completo. | V4-04. Se programa después del hito A; V4-19 no es una dependencia del lector. | AC-50–52 |
| **V4-22 · P1** | Compactación explícita de todos los objetos elegibles, respaldo, restauración y retirada verificada de duplicados físicos. | V4-21 y ampliación técnica de V4-14. | AC-53–55; evidencia de almacenamiento para AC-56. |

Dependencias ajustadas: **V4-21 → V4-14 ampliada → V4-22 → V4-15 → V4-16 → V4-18**.
V4-15 añade V4-22; V4-18 añade V4-20/V4-22 y conserva sus dependencias anteriores.
V4-14 ya no espera a V4-22. AC-56 cierra en V4-16, después de las pruebas y del
paquete exacto. No hay ciclo ni compatibilidad pospuesta hasta después de convertir.

V4-19 conserva 20.000 rutas elegibles y propone cota independiente de 200.000 rutas
brutas; stdout Git ≤16 MiB, stderr ≤64 KiB y 60 s, limitados **durante captura**.
No reescribir todo el ejecutor Git ni lanzar wrappers Python por cada consulta.
Conservar exclusión segura de secretos, deduplicación, normalización, invocación
Windows y comprobación fresca al aplicar; cualquier truncamiento/error invalida
el inventario. El censo exacto 20.027/18.847/1.180 se prueba con respuesta controlada;
un único fixture con Git real comprueba además la integración de más de 20.000 rutas.

Hito A no construye todos los paquetes de distribución ni repite el gate final:
genera solo el runtime provisional necesario, verifica su huella y usa actualización
nativa en el sintético. No modifica consumidores reales. El procedimiento distingue
plugin global, runtime fijado, autorización vigente y cierre administrativo real.

V4-21 empieza con un prototipo de **45 min dentro de su cota**: lectura mixta,
preview/guard sobre una ruta lógica empaquetada, staging y recuperación de un diario
2.1, sin catálogo persistente. Debe mostrar también agrupación sin copias sueltas y
un replay de crecimiento. Si pasa, continuar dentro del bloque autorizado sin otra
parada de aprobación; si descubre una contradicción, presentar el bloqueo antes
del escritor completo. Ahora solo se planifica ese futuro trabajo.

V4-22 conserva **todos** los objetos válidos, incluidos los que no tengan referencias
identificadas. Un objeto no se elimina por considerarlo inútil: cambia su soporte.
Publicar y verificar paquetes, crear respaldo independiente compacto y comprobar
restauración antes de retirar originales. La autorización de retirada es separada,
según la [guía de almacenamiento](../../DOCUMENT-STORAGE.md); debe incluirse
explícitamente en el encargo sintético futuro.
En un consumidor real, presentar antes su preview. Directorios desconocidos, archivos
no reconocidos, diarios pendientes y falta de espacio bloquean o excluyen la parte
afectada con motivo; nunca se descartan para alcanzar un porcentaje.

Comprobar una vez todos los cuerpos distintos y todas las referencias/manifiestos,
reutilizando validaciones dentro de esa evaluación. No materializar cada árbol
histórico repetidamente. Una restauración completa de objetos y un export histórico
representativo contrastan el camino de recuperación con bytes originales. Sin
borrado por edad, recolección de contenido ni retirada de runtimes/caches ajenos.

## 4. Aceptación ajustada, siempre pendiente

| Criterio | Responsable | Condición de aceptación |
|---|---|---|
| AC-45 | V4-19 | El censo del reporte no falla por rutas internas; 20.000 elegibles aceptan y 20.001 rechazan. Inventarios antes válidos conservan contenido y semántica. |
| AC-46 | V4-19 | Límites brutos/stdout/stderr/tiempo durante captura y memoria acotada; sin inventario parcial válido, lectura de secretos ni escape por prefijos, rutas, enlaces o junctions. |
| AC-47 | V4-19 | Workflow, preparación, scope y aplicación comparten la corrección; cambios de código, política/base o sujetos entre preparación y aplicación se rechazan. |
| AC-48 | V4-20 | Un recorrido completo con Git real e historia acumulada cancela, continúa con sucesora y cierra nativamente con almacenamiento anterior; runtime corregido, trazabilidad conservada y sin journal pendiente. |
| AC-49 | V4-20 | Reutilizar solo autoridad/evidencia vigentes; negativa e interrupción focales conservan o recuperan estado válido. Procedimiento del caso real distingue solución disponible y recuperación aún no ejecutada. |
| AC-50 | V4-21 | Lector dual y rutas lógicas conservan bytes, sujetos, enlaces y Markdown; staging, packets y diarios 2.0/2.1 funcionan; capacidades comprobadas antes de escritura. ZIP inseguro/corrupto o representación contradictoria se rechaza. |
| AC-51 | V4-21 | Sobre el B congelado, altas persistentes internas ≤81 frente a 407 (≥80 % menos); incluir índices/recibos y no compensar eliminando entradas iniciales. Escritor publica agrupado, sin objetos sueltos intermedios por fragmento. Bytes nuevos persistidos ≤1,10× la referencia completa. |
| AC-52 | V4-21 | Consultas sin escritura; reintento idempotente completado sin copias nuevas. CPU mediana del componente ≤1,10× referencia; pico ≤512 MiB y ≤1,10× referencia, con integridad/localización incluidas. Informar dispersión, pared y temporales, sin atribuir mejora global de S8. |
| AC-53 | V4-22 | En histórico de composición congelada, ≥50 % menos archivos internos activos, incluidos paquetes/recibos, manteniendo runtime, Markdown y objetos lógicos. Todas las referencias se resuelven y objetos originales se restauran byte a byte. Informar archivos/bytes de backup y Git por separado. |
| AC-54 | V4-22 | Fallos antes/después de publicar, durante retirada y al completar recibo son recuperables; sin doble propietario, pérdida ni corrupción oculta. El diario de negocio se recupera sin catálogo global; mantenimiento conserva recuperación propia y no autoriza estados funcionales. |
| AC-55 | V4-22 | Preview fija originales, destinos, respaldo, espacio y protegidos; retirar solo duplicados físicos previamente verificados y autorizados. Conservar contenido de referencia desconocida; cero GC/limpieza por consulta o edad. |
| AC-56 | V4-16 | V4-14/15 aportan compatibilidad y garantías afectadas; paquetes finales declaran capacidades y pasan controles exigibles sobre su huella exacta. Rollback tras datos nuevos exige restauración/materialización compatible, no solo cambiar el pin. Sin instalación/publicación reales. |

No basta reducir archivos a costa de garantías. Si un límite de ahorro/coste no se
cumple o resulta inconcluso, se registra así; no se rebaja después de medir. Los
resultados anteriores siguen ligados a su candidato, sin repetirlos salvo impacto
en ruta lógica, lectura/escritura, guard, recuperación o empaquetado.

## 5. Pruebas mínimas con cobertura explícita

| Familia | Cobertura y reutilización | Ejecución prevista |
|---|---|---|
| F1 · Inventario | Ampliar `test_v3_code_inventory`; límites 20.000/20.001, censo exacto, errores, stderr, timeout y exclusiones. Reutilizar sus casos de secretos, enlaces y scope. | Casos controlados; sin crear 20.001 fuentes de código ni repetir S8. |
| F2 · Cierre | Fixture grande válido con Git real y mayoría de rutas internas; runtime corregido; cancelación/sucesora/cierre. | **Recorrido completo 1**, corte 600 s, una vez. Conservar fixture para F6. |
| F3 · Lectura y publicación | Referencias antiguas/mixtas, cuerpos y rutas lógicas, deduplicación, overlays, publicación agrupada y staging. | Añadir casos en `test_document_storage`; v2/v3 comparten datos y comprobaciones. |
| F4 · Recuperación de negocio | Diario 2.0 y 2.1, preview obsoleto, revocación, cambios posteriores, activos retirados y export. | Reutilizar/adaptar métodos afectados de `test_v2_storage`, `test_document_storage` y `test_v4_compatibility`, sin producto cartesiano por transición. |
| F5 · Contenedor | Nombres/rangos inválidos, duplicados, cifrado/compresión no admitida, cuotas, corrupción y publicación concurrente. | ZIP pequeños construidos en test; checks de integridad y publicación compartidos con F3. |
| F6 · Compactación | Reutilizar el corpus grande; validar todos los objetos/referencias y una restauración completa. Interrupciones al publicar, antes de retirar, durante retirada y al completar recibo; sin dos escritores propietarios. | Una compactación grande. Inyectar fallos en un caso pequeño equivalente; no copiar/restaurar 20.000 archivos por cada frontera. |
| F7 · Coste y crecimiento | Mismo conjunto de cuerpos, agrupación y trabajo en escritor anterior/nuevo; censo y límites AC-51/52. | Un replay funcional y dos parejas de componente AB/BA sin perfilador, sin calentamientos ni reintentos para encontrar éxito. Medir CPU/pared/pico en procesos comparables; no son recorridos completos. |
| F8 · Integración y paquete | S8 funcional sobre fixture inicial B, lector mixto y escritor final; gate estable y empaquetado reproducible afectados. | **Recorrido completo 2**, corte 600 s. Un gate final según `docs/VALIDATION.md`; evidencia exacta reutilizada donde coincida fuente/input. |

F1/F3/F4/F5 se ejecutan por métodos afectados; mantener una sola relación
riesgo → prueba → resultado, sin contar varias veces el mismo método. Las familias
son grupos de cobertura, no ocho invocaciones ni una promesa de número fijo de tests.
Una corrección repite el test fallido y sus dependencias afectadas, no toda la matriz.
Una corrección posterior al gate que afecte su alcance obliga a repetir sus controles
afectados sobre la nueva huella; no se publica una huella sin validar para ahorrar.
La aprobación de versión/publicación queda separada: ejecutar los checks técnicos
del gate no significa superar esa aprobación ni autoriza una publicación.

No se repite la campaña temporal ABBA de S8. Los dos recorridos propuestos no son
H2 ni comparaciones de host. No ejecutar LLMs para fixtures o esperas: coordinador
local con timeouts, finalización por proceso y recibo único. El agente lee el
resultado al terminar o fallar; no consulta periódicamente logs para esperar.
No abrir sesiones, parar cargas ajenas ni buscar una ventana de estabilidad.

## 6. Ahorro comprobable y presupuesto acotado

Congelar antes de implementar: fuentes, entradas, 407 altas persistentes B y corpus
grande, con evidencia de recuento y composición. Si no se puede reconstruir el
denominador, resolver esa falta antes de comparar; no elegir otro caso favorable.
Al crear el fixture sintético grande se reproduce la proporción del incidente:
18.847 rutas internas, de ellas 10.157 objetos sueltos. Clasificar validez/tamaño
antes de fijar cuántos son compactables; el reporte no demuestra que todos lo sean.
Conservar las otras 8.690 rutas y reflejar que los contenidos son sintéticos, no
el consumidor real.

Preflight aritmético: `T_final = T_inicial - L_retirados + P_añadidos`. Con esos
conteos, el objetivo del 50 % deja margen para **733 archivos nuevos** de almacén y
recibos **si los 10.157 originales resultan elegibles**. Si hay menos, calcular de
nuevo la viabilidad; no borrar protegidos ni ampliar el corpus para pasar. Para
repositorios reales, el preview informa su reducción alcanzable, sin prometer 50 %.

El objetivo nuevo usa `F_final menos F_inicial`, sin descontar bajas de entradas
iniciales. F8 no compacta el estado inicial para facilitar ese objetivo: conserva
los objetos sueltos iniciales y prueba lectura mixta. La compactación histórica es F6.
Medir archivos internos incluidos ignorados/no versionados, bytes nuevos completos,
temporales/picos y backup. Rutas Git indexadas pueden seguir figurando hasta integrar
las bajas; no confundirlas con archivos presentes. No reescribir historia Git ni
presentar reducción de archivos como reducción automática de bytes o tokens.

Coste del componente: dos muestras por representación, orden AB/BA, con todos los
resultados incluidos. Comparación descriptiva, sin garantía estadística de un 10 %
ni nuevas búsquedas de estabilidad. Aplicar los umbrales propuestos de AC-52; si
hay datos inválidos o resultado inconcluso, declarar pendiente y pedir disposición,
sin campañas adicionales automáticas. `billed_tokens` y tokens del host siguen null.

El registro anterior permanece en **54/54 plazas**, dos H2 protegidas y sin saldo
positivo certificado bajo las 15 h históricas. Este plan **no amplía** ese presupuesto.
Propone dos plazas completas nuevas (total 56), sin reintentos automáticos. Un fallo
consume plaza; recuperar dentro de la reserva y presentar resultado antes de pedir
otra. No esconder un recorrido completo dentro de una familia de componente.

| Bloque futuro | Máximo propuesto dentro de 10 h adicionales |
|---|---:|
| V4-19/20: corrección, controles focales, fixture y recorrido 1; hito A | 2 h |
| V4-21: prototipo con decisión técnica | 45 min |
| V4-21: completar lector/escritor y controles compartidos | 3 h |
| V4-14 ampliada / V4-22: capacidad previa, compactación y restauración | 1 h 30 min |
| V4-15/16/18: recorrido 2, gate, paquete e informe final | 1 h 15 min |
| **Recuperación y cierre protegidos** | **1 h 30 min** |
| **Total máximo propuesto** | **10 h** |

Rango orientativo **6–10 h**, de confianza limitada hasta el prototipo; no ahorro
demostrado frente a la estimación anterior. Incluye esperas de procesos, correcciones
y documentación. No equivale a diez horas continuas de IA ni de atención humana.
No iniciar operaciones si el peor corte disponible invade la reserva de recuperación.
Si no cabe, conservar estado y presentar pendiente; nunca reducir garantías para
ajustar la cota. Validar puede autorizar solo el hito A sin comprometer todo el bloque.

Documentación futura: un registro de evidencia compartido y dos resultados, hito A
y cierre final; no informe por cada familia. No repetir gate/paquetes completos en
hito A. Las decisiones sobre implementación y presupuesto quedan pendientes.

Se mantienen M1–M6, Markdown canónico y `specs/canonical/` sin cambios. Windows/H2
siguen apartados; rutas/temporales largos del plugin se comprueban en sus fronteras
afectadas y en el gate estable. AC-43 conserva el resultado temporal no cumplido y
la aceptación del compromiso por el usuario; AC-40 permanece inconcluso. Copilot y
valoración humana conservan sus pendientes. No instalar, publicar, hacer commit o push.
