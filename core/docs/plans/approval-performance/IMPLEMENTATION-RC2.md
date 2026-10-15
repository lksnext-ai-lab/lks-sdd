# Corrección posterior a la revisión crítica — 3.4.3-rc.2

Fecha: 2026-10-14. Rama: `codex/approval-evaluation-performance`.
Base: `a657bf7b07461c8b03516f9adbb00bb7a6b9ed7c` (3.4.2).
Autorización: corregir rc.1, repetir equivalencia y benchmarks aislados y preparar
otra candidata. Commit, push, publicación e instalación no están autorizados.

## Cambios

- Guardia: revisión monótona y observación de contenedores JSON anidados, campos
  de elementos, raíz, tabla, prosa, errores y avisos. Rechaza el cambio antes de
  editar. Un intento capturado mantiene el ámbito invalidado; restaurar contenido
  no restaura una revisión anterior. No serializa el modelo al entrar y salir.
- Copia: `deepcopy(Model)` reconstruye observadores y tabla; los índices se vuelven
  a construir. Los inventarios siguen compartidos dentro de cada copia y se separan
  de la fuente. Los borradores desacoplados no invalidan el modelo actual.
- Inventarios: un mapa observable por objeto físico en la carga, con padres débiles
  para sus eventos; no se expande por evento al comprobar inmutabilidad.
- Procedencia: permanecen lectura física por ruta/hash, hashes de fuentes, guards,
  staging y recuperación. Los errores de claves malformadas conservan su forma
  original sin sustituir errores por éxito.

La API de edición admite los setters y mutadores normales; editar campos privados
o llamar deliberadamente a primitivas de base para eludir observadores no está
soportado. No cambia el contrato canónico, método, esquema o pila tecnológica.

## Equivalencia y validación

El oráculo conserva **seis** módulos originales, incluido ahora `v3_inventories.py`,
porque rc.2 lo modifica. Su manifiesto vincula cada byte al commit base. El resto
del experimento conserva las mismas entradas, UUID/reloj/semilla controlados y
comparación canónica íntegra de resultados, errores, fuentes y decisiones.

[Regresiones focales](evidence/rc2-equivalence.json): **18/18**. Incluyen diferencias
contra 3.4.2, copias frías/calientes, identidades, mutaciones anidadas, eliminación
de campos, intento capturado, otro hilo, datos resueltos compartidos, liberación,
aislamiento y originales cambiados antes de preparar. Las copias superficiales
conservan su compartición y registran todos los propietarios; un intento capturado
invalida todos los ámbitos activos afectados, sin depender del orden de notificación.

El [binding de fuentes](evidence/rc2-source-binding.json) fija los siete módulos de
esta candidata y los seis archivos de medición/referencia. Pasan **40 pruebas
distintas**: 18 focales, [14 de núcleo](evidence/rc2-core.json),
[7 de guards e inventarios](evidence/rc2-guards-and-inventories.json) y
[1 de rutas Windows](evidence/rc2-windows.json), sin fallos ni omisiones.
Integridad estática y 13 fixtures válidos. Esto verifica el árbol de desarrollo;
no se presume un gate de release de commit limpio.

## Benchmark aislado

Se ejecuta un único runner a la vez. Cuatro pares por tamaño y fase, en orden
referencia/candidata, candidata/referencia, referencia/candidata, candidata/referencia.
Hay 10 segundos de reposo antes de cada proceso, excluidos de las mediciones.
Cada muestra usa
un proceso frío y las mismas rutas/entradas. Se conserva CPU, tiempo, contadores,
working set antes/después, pico de working set muestreado cada 10 ms y pico
acumulado del proceso con su incremento durante cada operación. Los picos muestreados
pueden omitir transitorios más cortos; no son un perfilador de asignaciones. La CPU
incluye la instrumentación y el muestreo, activados igual en ambas versiones.

Las fases son cálculos, ciclo público de biblioteca y el caso de regresión de
inventario compartido: 80 eventos/6.000 rutas, un objeto de 498.042 bytes y contrato
activo dentro de sus límites. Se mide también su carga y el primer descriptor.

```powershell
python -B -X utf8 tests/measure_approval_performance.py `
  --sizes 100:5 500:15 1500:35 --repetitions 4 --order alternating --cooldown 10 `
  --phases calculations workflow --timeout 3600 `
  --output docs/plans/approval-performance/evidence/rc2-isolated.json
python -B -X utf8 tests/measure_approval_performance.py `
  --sizes 1500:35 --repetitions 4 --order alternating --cooldown 10 `
  --phases shared-inventories --timeout 3600 `
  --output docs/plans/approval-performance/evidence/rc2-shared-inventories.json
python -B -X utf8 tests/combine_approval_measurements.py --isolated `
  --output docs/plans/approval-performance/evidence/rc2-measurement.json
```

La [matriz principal](evidence/rc2-isolated.json) y el
[caso compartido](evidence/rc2-shared-inventories.json) están completos:
**28/28 pares equivalentes**, 56 procesos fríos y **536 filas de operaciones**.
La [consolidación](evidence/rc2-measurement.json) exige matriz completa, mismos
resultados y fuentes exactas. La [verificación](evidence/rc2-verification.json)
comprueba además los seis archivos de medición/referencia, los seis originales
contra Git y las 112 auditorías antes/después limpias.
No se reutilizan como prueba aislada los tiempos de rc.1 bajo doce runners
simultáneos. El [informe histórico](IMPLEMENTATION-RC1.md) conserva esa evidencia
y sus límites; los archivos de esta nueva iteración llevan el prefijo `rc2-`.
También se excluyen las rondas de desarrollo de rc.2, incluida una
ronda detenida al detectar otro driver propio activo. La serie final incorpora
auditoría CIM antes y después de cada worker; el
[ensayo de aislamiento](evidence/rc2-isolation-check.json) verifica que rechaza el
runner conflictivo. Esto no controla toda la actividad del sistema operativo.

### Cálculos con 1.500 elementos y 35 tecnologías

Medianas de cuatro procesos por versión; segundos. El tiempo de carga incluye
lecturas físicas y validación, con un archivo canónico por elemento.

| Operación | Tiempo 3.4.2 → rc.2 | CPU Python 3.4.2 → rc.2 |
|---|---:|---:|
| Carga | 29,211 → 45,060 | 26,211 → 37,672 |
| Contexto | 0,638 → 0,289 | 0,609 → 0,234 |
| 3.004 identidades | 1,056 → 0,012 | 0,844 → por debajo de resolución |
| Aprobaciones actuales | 2,243 → 0,081 | 2,125 → 0,070 |
| Aprobaciones heredadas | 69,704 → 0,269 | 59,984 → 0,258 |

Los contadores reproducibles reducen lectores de descriptores 52 → 1 en las
actuales y 910 → 1 en las heredadas; lecturas y análisis de originales 70 → 2,
con ambas rutas físicas conservadas. La resolución evita los 4.512.008 elementos
recorridos por las 3.004 consultas originales. Estas consultas son calientes: el
coste de construir el índice permanece en carga/contexto. La CPU de operaciones
muy cortas tiene resolución gruesa en Windows;
una lectura cero no significa trabajo gratuito.

La carga **no mejora** en esta matriz. Sus rangos de tiempo se solapan ampliamente:
9,388–57,520 s frente a 25,215–71,780 s. En 500 elementos su CPU mediana también
sube, 12,977 → 16,086 s; en 100 queda en 0,742 → 0,742 s. La instrumentación conserva
lecturas físicas y comprobaciones de rutas. No se ha aislado la causa de la variación
de E/S ni se considera resuelta una posible regresión de carga. No se atribuye a
antivirus, disco o frecuencia sin evidencia adicional.

### Ciclo público de biblioteca

Cada cifra suma `prepare` y `apply` dentro de cada proceso y después calcula la
mediana; no suma medianas independientes. Incluye Git, guards, staging y journal.
Segundos de CPU Python, sin sumar procesos Git hijos.

| Operación | 100/5: 3.4.2 → rc.2 | 500/15: 3.4.2 → rc.2 | 1.500/35: 3.4.2 → rc.2 |
|---|---:|---:|---:|
| Inicio | 5,180 → 4,133 | 11,039 → 13,328 | 12,000 → 8,562 |
| Implementación | 5,344 → 4,383 | 12,297 → 14,008 | 11,281 → 8,758 |
| Evidencia | 7,711 → 3,750 | 12,773 → 12,180 | 7,453 → 8,336 |
| Verificación | 9,289 → 6,523 | 16,125 → 14,852 | 12,312 → 9,188 |
| Cierre | 9,094 → 4,109 | 12,883 → 13,609 | 13,094 → 9,312 |
| Integración | 11,367 → 8,211 | 20,070 → 25,188 | 22,320 → 18,141 |
| Aceptación | 11,734 → 7,953 | 15,352 → 19,414 | 16,969 → 13,219 |

Se conservan las medianas peores: inicio, implementación, cierre, integración y
aceptación en 500; evidencia en 1.500. Sus rangos se solapan. Por ejemplo, integración
en 500 registra 7,750–25,562 s frente a 12,453–28,766 s de CPU. Evidencia en 1.500
registra 7,094–9,219 s frente a 6,797–9,359 s. El beneficio focal de aprobaciones está
medido; una mejora general de latencia o ausencia total de regresiones no lo está.

Sumando las catorce fases del ciclo dentro de cada worker, las medianas completas
son las siguientes. De nuevo, no son la suma de las medianas de la tabla anterior.

| Tamaño | CPU Python total: 3.4.2 → rc.2 | Tiempo total: 3.4.2 → rc.2 |
|---|---:|---:|
| 100/5 | 62,891 → 38,828 | 112,787 → 89,996 |
| 500/15 | 106,414 → 98,719 | 158,925 → 165,407 |
| 1.500/35 | 97,422 → 76,406 | 118,590 → 95,964 |

En 1.500 los rangos completos quedan separados en esta serie: CPU
90,141–99,031 → 68,734–79,312 s y tiempo 111,325–132,843 → 88,296–99,805 s.
En 100 y 500 los rangos se solapan y no sustentan la misma conclusión. La mejora
del ciclo grande se limita a este fixture y sus controles de biblioteca; no es una
predicción del caso privado de 78 minutos.

### Memoria de la matriz principal

Máximo de los picos acumulados de proceso de los cuatro workers de cada versión,
en MiB. No es el pico exclusivo de una función ni el máximo de una única ejecución
que recorriera las tres tallas. Se conservan además working set antes/después y
muestreo de 10 ms en cada fila original.

| Tamaño | Cálculos: 3.4.2 → rc.2 | Ciclo público: 3.4.2 → rc.2 |
|---|---:|---:|
| 100/5 | 46,90 → 45,73 | 47,29 → 47,61 |
| 500/15 | 47,68 → 48,51 | 56,63 → 55,70 |
| 1.500/35 | 50,82 → 52,79 | 73,41 → 82,56 |

La corrección **no reduce toda la memoria**: el ciclo de 1.500 sube 9,15 MiB
(12,5 %) y los cálculos suben 1,97 MiB. Los observadores e índices tienen coste,
además de las estructuras y resultados necesarios. Los presupuestos LRU limitan
admisión de reutilización; no son un límite duro de RSS ni de todos los objetos
temporales de preparación/staging. El caso de inventario compartido se analiza
aparte para distinguir este coste de la expansión por evento de rc.1.

### Inventario compartido y regresión de rc.1

Las ocho muestras del [caso compartido](evidence/rc2-shared-inventories.json)
conservan **1.582 elementos**, 35 tecnologías y 80 eventos que resuelven **un único
mapa** de 6.000 rutas/498.042 bytes. La carga completa supera `require_valid` y
permanece dentro de los límites de contrato y lectura.

| Operación | Tiempo mediano 3.4.2 → rc.2 | CPU Python mediana 3.4.2 → rc.2 |
|---|---:|---:|
| Carga con inventario compartido | 26,984 → 25,047 s | 26,031 → 24,320 s |
| Primer descriptor | 49,992 → 2,347 ms | 46,875 ms → por debajo de resolución |
| Segundo descriptor, nueva evaluación | 89,184 → 2,909 ms | 85,938 ms → por debajo de resolución |
| Tercer descriptor, nueva evaluación | 55,507 → 2,328 ms | 54,688 ms → por debajo de resolución |

Cada descriptor abre y libera su propia evaluación; no hay caché persistente entre
las tres llamadas. Los rangos del primero quedan separados: 33,494–77,836 ms
frente a 1,760–4,163 ms. En carga se solapan: 23,888–28,127 frente a 23,411–31,169 s;
no se afirma mejora causal de la carga. Ambas versiones realizan 1.583 lecturas
físicas y 1.583 comprobaciones compartidas de ruta en cada muestra de carga.

El máximo del pico acumulado hasta el primer descriptor es **88,72 → 89,45 MiB**;
el incremento máximo del pico durante ese descriptor es 0 → 0,031 MiB. El máximo
muestreado durante el descriptor es 86,71 → 89,43 MiB. No se presenta el pico acumulado
como memoria atribuible exclusivamente al descriptor. La serialización completa
de rc.1 se ha eliminado y el mapa no se duplica por evento. La reproducción crítica
anterior observó hasta 197 MiB con rc.1; es evidencia histórica de aquel defecto,
no una tercera versión ejecutada dentro de esta matriz de cuatro pares.

## Alcance y pendientes

El ciclo usa las operaciones públicas de biblioteca de inicio, implementación,
evidencia, verificación, cierre, integración y aceptación, con Git, staging y journal
reales. Usa el fixture de revisión integral 3.1 y `apply(current=False)`, igual en
ambas versiones: no cubre la comprobación del runtime fijado como actual. No
ejecuta el proceso CLI completo ni mide su arranque, runtime-doctor o el asistente.
Tampoco ejecuta una prueba funcional
independiente de la aplicación sintética: mide el manejo contractual de su evidencia.
No se extrapolan resultados a datos privados ni se atribuye ahorro de tokens.

La topología es sintética y dispersa, con hasta 24 reglas globales compartidas;
no representa todas las densidades posibles. Las cachés del sistema, frecuencia y
otra actividad ajena a los runners conocidos no están controladas. Los perfiles de
desarrollo sobre fuentes anteriores quedan fuera de los resultados finales.

## Candidata preparada y valoración

`3.4.3-rc.2` corrige los defectos reproducidos de rc.1: serialización expansiva,
observadores/índices perdidos al copiar y cambios capturados o temporales que
podían dejar reutilización obsoleta. Las 40 pruebas y 28 pares cubren esos casos;
no constituyen una demostración de equivalencia para toda entrada posible.

La preparación produce `tests/reports/lks-sdd-3.4.3-rc.2.patch`, su manifiesto y
los paquetes de desarrollo de ambos hosts. El manifiesto registra aplicación y
reversión contra la base en un índice temporal, índice real sin cambios, dos builds
idénticos por SHA-256, siete módulos de runtime exactos y validación del paquete
Copilot nativo. El builder normaliza textos a LF: se registra expresamente la
derivación del manifiesto de referencia, sin cambiar los originales archivados.
La [integridad estática final](evidence/rc2-static.json) conserva contrato y 13
fixtures válidos, diff sin errores y especificaciones canónicas sin cambios.

Valoración técnica: candidata disponible para revisión, **sin promoción automática**.
Permanecen por aclarar las medianas peores de carga/CPU y valorar el coste adicional
de memoria del ciclo grande. No se declara ausencia de regresiones ni aceptación
del rendimiento. No se ejecuta gate ligado a commit limpio, build acreditado de
release, CLI/host completo, revisión humana o piloto. No hay commit, integración,
push, etiqueta, publicación, registro ni instalación de esta candidata.
