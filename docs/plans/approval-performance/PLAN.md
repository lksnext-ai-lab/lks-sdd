# Corrección de rendimiento de aprobaciones

Fecha: 2026-10-14. Base: `a657bf7b07461c8b03516f9adbb00bb7a6b9ed7c` (3.4.2).
Rama: `codex/approval-evaluation-performance`.

## Cobertura y autorización

La petición adjunta autoriza implementar en la fuente oficial índices de identidades,
reutilización durante evaluaciones inmutables, pruebas de equivalencia, mediciones
sintéticas reproducibles y una candidata correctiva. Se reutilizan el contrato v3,
los límites, guards, almacenamiento y política de release existentes. No cambia el
método ni el esquema. No autoriza commits, integración, push, publicación o instalación.
Las tareas siguientes son mantenimiento del plugin, no registros de un consumidor.

## Hechos, decisiones e hipótesis

- Hecho comunicado: aproximadamente 1.500 elementos/35 tecnologías, 155 segundos
  en una comprobación y 78 minutos al iniciar. Son referencias, no objetivos.
- Hecho inspeccionado: `Model.get` recorre todos los elementos; `approved` crea
  `_Descriptors` cada vez; la migración pide descriptores por unidad; `facts_for`
  evalúa cada tecnología con su alternativa de propuesta.
- Decisión de implementación: índices derivados en memoria con invalidación de
  altas, sustituciones, bajas y cambios de UID/alias/tipo. Conservar ambigüedades,
  colisiones, referencias cualificadas y errores.
- Decisión de implementación: ámbito explícito y anidable por modelo y contexto
  de ejecución. Compartir pertenencias, cierre global, descriptores y originales
  verificados por ruta; liberar al salir. Sin caché persistente entre comandos.
- Decisión de implementación: evaluar un modelo inmutable; observar mutaciones y
  comprobar su revisión al salir antes de devolver resultados. Las escrituras siguen validando fuentes,
  inventarios, guards frescos y transacciones en los canales existentes.
- Hipótesis por medir: disminuirán reconstrucciones y recorridos. No se afirma
  ahorro de tokens ni se extrapolan los tiempos comunicados.

## Tareas y aceptación

1. AP-01: conservar referencia 3.4.2 con procedencia y hashes; auditar mutaciones.
2. AP-02: índices de UID/alias/tipo, con pruebas de colisión, cambio y ausencia.
3. AP-03: evaluación compartida y acotada, incluida migración. Conservar comprobación
   de cada ruta física, correspondencias, revocaciones y tecnología individual.
4. AP-04: comparación diferencial de resultados, errores, dependencias, fuentes y
   decisiones; UUID/tiempos controlados explícitamente en fixtures y comparación.
   Incluir concurrencia de modelos/proyectos/revisiones y mutación rechazada.
5. AP-05: benchmark repetido de varios tamaños (incluido 1.500/35), carga/contexto,
   identidad, clasificación/cierre, aprobación actual/heredada y operaciones públicas
   de inicio, implementación, evidencia, verificación, cierre, integración y aceptación.
   Registrar tiempo, memoria y contadores; conservar muestras, no solo promedios.
6. AP-06: validaciones focales, integridad del plugin y revisión del diff; documentar
   resultados, límites y riesgos. Preparar `3.4.3-rc.1`, sin aprobación stable inventada.

## Límites de reutilización

Las entradas son elementos completos (incluidos estado, revisión, permisos y datos
resueltos), sus rutas y el proyecto del modelo. El ámbito no cruza modelos, tareas
asíncronas independientes ni comandos; una evaluación nueva observa una revisión
nueva. Ningún resultado se usa para omitir lecturas frescas antes de materializar.
La implementación y su informe detallarán presupuestos de memoria y liberación.

## Cierre técnico y pendientes

### Iteración 3.4.3-rc.4 autorizada el 2026-10-15

El usuario autoriza probar por separado la compactación de `Element` y reutilizar
la tabla de UID, verificar equivalencia y benchmarks aislados, descartar cualquier
regresión de CPU, velocidad o tokens y preparar otra candidata sin publicar ni
instalar. Se conservan las restricciones anteriores y la referencia exacta rc.3.

- AP-18: conservar el ZIP rc.3 y generar variantes independientes, con cambios
  limitados a representación de `Element` o índice de identidades. Probar copias,
  referencias débiles, alias ambiguos, claves no canónicas e invalidación.
- AP-19: comparar cada variante con rc.3 en procesos nuevos, orden equilibrado,
  auditoría de aislamiento antes/durante/después y muestras crudas conservadas.
  Separar CPU/tiempo sin instrumentación de la memoria de asignaciones. Incluir
  carga, consultas, aprobaciones, inventarios y ciclo CLI completo de 1.500/35.
- AP-20: conservar instrucciones y llamadas. Comparar contenido emitido y contexto
  exactos; distinguir identidad/versionado del runtime de contenido contractual.
  No presentar tamaño en caracteres como tokens facturados del host.
- AP-21: incorporar solo variantes con equivalencia, menor memoria viva y sin
  empeoramiento reproducido de CPU/tiempo. Una mediana peor exige confirmación
  independiente; si se reproduce, descartar el cambio. Un resultado incierto no
  acredita ausencia de regresión. Combinar únicamente tras comprobar la combinación.
- AP-22: validar fuente y ambos paquetes, preparar rc.4 reproducible y evidencia
  externa vinculada por hash. Host conversacional/piloto siguen pendientes.

Estas tareas están autorizadas; su ejecución y aceptación técnica se registrarán
en evidencia externa. No se presume completada la matriz pendiente de rc.3.

### Iteración 3.4.3-rc.3 autorizada el 2026-10-14

La petición posterior autoriza investigar y corregir las regresiones de carga y
memoria de rc.2, comprobar el ciclo CLI/host y preparar otra candidata con
mediciones aisladas. Se conserva la prohibición de publicar, instalar, commit o
push. La comprobación técnica usará proyectos y runtimes temporales; no modifica
hosts, consumidores o cachés instalados. Una observación conversacional real
requiere un host que pueda cargar la candidata sin instalación; no se sustituye
por una simulación ni se presume disponible.

- AP-12: conservar rc.2 y su evidencia por hash antes de modificar; perfilar por
  separado E/S, construcción del modelo, índices y memoria viva/temporal.
- AP-13: reducir asignaciones y trabajo de carga que se reproduzcan, manteniendo
  guardia monótona, copias, invalidación y comprobaciones físicas frescas.
- AP-14: equivalencia contra 3.4.2 y regresiones de rc.2, con pruebas de límites,
  enlaces/junctions, sustituciones, permisos y liberación si se afectan esos canales.
- AP-15: ejecutar el CLI público en procesos fríos, con runtime fijado/doctor,
  presentación, preparación, aplicación y ciclo completo; comprobar los paquetes
  y entrypoints de ambos hosts en proyectos sintéticos.
- AP-16: medir CPU, tiempo y memoria en series secuenciales equilibradas, sin otros
  runners; comparar también rc.2 y distinguir contadores de variación nativa.
- AP-17: preparar `3.4.3-rc.3`, parche y paquetes reproducibles, con informe de
  causas, resultados y límites. Mantener host conversacional/humano como pendiente
  si no se dispone de un medio real compatible con no instalar.

AP-12–AP-13 implementadas. El cierre verificable de AP-14–AP-17 se registra en el
manifiesto externo `tests/reports/lks-sdd-3.4.3-rc.3.manifest.json` y su informe
adjunto; no se presume superado por preparar esta fuente. La evidencia final queda
fuera del runtime para conservar exactamente los paquetes medidos.

### Iteración 3.4.3-rc.2 autorizada el 2026-10-14

La petición posterior autoriza corregir los hallazgos de rc.1 y la guardia de
inmutabilidad, repetir equivalencia y benchmarks aislados de CPU/memoria, incluido
el ciclo público, y preparar otra candidata. No autoriza publicar, instalar, commit
o push. Se conservan AP-01–AP-06 y el alcance contractual.

- AP-07: sustituir la serialización repetida por observación de cambios anidados y
  una revisión monótona. Rechazar también un cambio intentado y capturado dentro
  de la evaluación; conservar mutaciones legítimas fuera de ella.
- AP-08: reconstruir tabla, observadores e índices de `deepcopy(Model)` y ensayar
  alias, UID, tipo y altas con índices fríos/calientes.
- AP-09: conservar el inventario compartido sin expansión por evento; medir el
  caso válido de 80 eventos/6.000 rutas, además de los tamaños anteriores.
- AP-10: equivalencia contra 3.4.2, cálculos y ciclo público en procesos secuenciales,
  cuatro pares equilibrados por caso, orden alternado y reposo entre procesos,
  con CPU, memoria y fuentes exactas.
- AP-11: validaciones vigentes, diff, evidencia recuperable y `3.4.3-rc.2` preparada.

AP-07–AP-11 completadas como corrección, verificación y preparación local de
`3.4.3-rc.2`: 40 pruebas distintas y 28 pares/536 operaciones equivalentes, con
fuentes fijas y benchmarks secuenciales. Los costes medidos y las limitaciones
permanecen visibles; no se declara aceptación del rendimiento ni ausencia de
regresiones de carga, CPU o memoria. Véase [IMPLEMENTATION-RC2.md](IMPLEMENTATION-RC2.md).

AP-01–AP-06 implementadas y comprobadas localmente. Resultados, equivalencia,
mediciones y límites en [IMPLEMENTATION.md](IMPLEMENTATION.md). Revisión humana, integración,
preflight de commit limpio, build acreditado, publicación, instalación y aceptación
real de host se mantienen pendientes hasta su ejecución y autorización separadas.
