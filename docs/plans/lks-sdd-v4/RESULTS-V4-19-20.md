# V4-19/20 y V4-21 — Cierre y almacenamiento agrupado

**Estado vigente:** V4-15 técnica, V4-16 y V4-18 cerradas en desarrollo con reservas de aceptación; [resultado final](#v4-15-v4-16-y-v4-18--cierre-técnico-y-paquetes-finales-de-desarrollo). Windows/H2 pendientes. Gate estable, aprobación de versión e integración separados; sin instalación ni publicación.

## Antecedente V4-19/20 validado
Fecha: 2026-10-18. Plan 0.7 y ampliación de 10 h / dos recorridos validados por
el usuario. **Revisión crítica completada con correcciones focales**; véase la
[revisión y el saldo corregido](#revisión-crítica-posterior). AC-45–49 conservan
su evidencia en el alcance indicado, con reconstrucción del paquete final pendiente.
V4-21/22 no iniciadas. Estado estructurado:
[v4-19-20-progress.json](v4-19-20-progress.json).

## Resultado funcional

| Comprobación | Resultado observado |
|---|---|
| Referencia publicada 3.4.3 | Reproduce `Inventario de código demasiado amplio` con 20.027 rutas: 18.847 internas / 1.180 externas. El rechazo conserva el estado y no deja journal. |
| Estado inicial | Original `in-progress`; sucesora `backlog`; runtime anterior válido. |
| Runtime corregido | Cambio nativo recuperable en el sintético y doctor válido, conservando trabajo abierto. El módulo usado después se carga desde el runtime fijado del consumidor. |
| Cancelación | CLI pública `v3 cancel --apply --view operational --json`: exit 0; original `cancelled`. |
| Continuidad | Nuevo plan y revisión del alcance de tres rutas autorizados mediante operaciones nativas; se conserva la propuesta validada y el trabajo ya realizado. |
| Implementación y prueba | Registro nativo de implementación, ejecución real de `greeting()` → `Hola`, cero parámetros, evidencia ligada al sujeto, verificación y cierre. Sucesora `closed`. |
| Conservación | Los nueve hechos/decisiones/autorizaciones previos mantienen su digest; los 10.157 objetos anteriores siguen byte a byte iguales. Se comprueba que la sucesora declara `replaces` sobre la original. |
| Estado final | Validación pública y doctor: válidos. Sin journal pendiente ni procesos descendientes activos del recorrido. Integración y aceptación funcional no ejecutadas. |

El total final es **20.904 rutas Git**, incluyendo el corte de runtime y los
registros del ensayo. El cierre funciona pese a superar 20.000 rutas totales.
Este censo no mide ahorro ni representa archivos generados por una tarea normal:
el histórico se creó expresamente para reproducir la incidencia y reutilizarlo en F6.

## Corrección y garantías

La única modificación de producción está en `scripts/v3_git.py`:

- Clasificar y excluir antes de aplicar el máximo de **20.000 rutas de código
  elegibles**. Conservar normalización, deduplicación, exclusiones de secretos y
  rechazo de rutas inseguras. Las carpetas con nombres parecidos siguen siendo código.
- Cotas independientes durante captura de `ls-files`: **200.000 registros brutos,
  16 MiB stdout, 64 KiB stderr y 60 s**. Drenar ambos pipes, detener el hijo ante
  exceso/error/timeout y rechazar observaciones incompletas. Los demás comandos Git
  conservan su ejecutor e invocación anteriores, incluidas rutas largas de Windows.
- Mantener lectura y hash frescos al aplicar. La reutilización de observaciones
  termina con la evaluación de lectura; ningún cache concede autoridad entre comandos.
- No eliminar historia ni modificar almacenamiento, estados, permisos, esquema o
  método. Los archivos internos siguen pasando sus validadores propios.

**Validación inicial: 38 tests focales distintos pasan**: 22 de inventario/captura, 15 de guards,
recuperación y compatibilidad, y uno adicional de salida del cache antes de la
lectura física. Incluyen 20.000/20.001 elegibles; censo exacto; límites de captura;
secretos, enlaces y repositorios anidados; revocación; código/ramas cambiados;
cancelación interrumpida y rollback que conserva trabajo posterior. Tres casos
reales de Git en rutas largas de Windows pasan sin reparar el aislamiento del host.

Contrato estático del plugin: válido. AST y diff de los seis archivos Python
modificados/añadidos: válidos; `specs/canonical/` conserva sus hashes. Se conserva
la evidencia anterior de almacenamiento no modificado; no se repite la batería
completa ni el gate final de distribución en este hito.

## Recorrido y coste

Un solo arranque real del recorrido, sin repeticiones: **479,623 s (7 min 59 s)**,
dentro de 600 s; CPU del conjunto: 369,750 s; pico de memoria comprometida del
conjunto: **163,44 MiB**, inferior a 512 MiB. Al finalizar: cero descendientes activos.
Son operaciones locales Python/Git; no se abrieron sesiones de Codex/Copilot ni se
llamó a modelos. No se presenta este ensayo como mejora temporal frente a S8.

Hubo un fallo de preparación del lanzador: el medidor anterior esperaba un CLI y
su modo habitual fija reloj/UUID de otro benchmark; además, la admisión comparó CRLF con LF
sin normalizar. El fallo ocurrió **antes de CreateProcess**, sin arrancar el caso
ni modificar el consumidor. Se conservan el registro y su coste temporal. Una
sonda real validó el modo directo, el handshake, la ausencia de importación previa
del dominio y cero procesos residuales antes del único arranque real posterior.
El comportamiento anterior del medidor se conserva por defecto. La reserva inicial
de plaza se mantuvo; no se borró un intento funcional ni se descartaron muestras.

En el recorrido inicial el módulo de producción, normalizado a LF, coincidía con el
provisional fijado; después de prepararlo se añadió un test y se adaptó el medidor externo al runtime.
Esas diferencias de harness se declaran en `journey-admission.json`; no se afirma
que este sea el paquete final de la fuente actual. V4-16 deberá reconstruirlo.

Presupuesto y saldo conservadores se cierran en el registro estructurado: tiempo
medido desde apertura más **5 min reservados para las lecturas iniciales anteriores
al registro**, sin presentarlos como cronometraje. Se conserva la reserva de 90 min
para recuperación. La plaza que se declaró disponible para el recorrido final se
corrige en la revisión posterior: las dos plazas nuevas quedan imputadas. Las dos
plazas históricas de H2 no se consumen ni se reabre la reserva ABBA anterior.

## Aplicación futura al consumidor real

La corrección está disponible en estas fuentes y en el runtime sintético; **no se
ha actualizado el plugin instalado ni el runtime del proyecto que reportó el fallo**.
El procedimiento para ese consumidor será:

1. Identificar raíz, runtime fijado, actor competente, tareas y diarios pendientes.
   Conservar el estado; no repetir el comando contra 3.4.3 esperando avances.
2. Preparar el bundle corregido exacto, respaldo y preview del cambio nativo de
   runtime. Cambiar el plugin global por sí solo no actualiza ese pin.
3. Revisar/autorizar y aplicar el corte compatible; comprobar doctor y conservación
   de las decisiones. No reutilizar un preview anterior al cambio de runtime.
4. Preparar la cancelación administrativa y la continuidad con el alcance real.
   Reutilizar únicamente decisiones/evidencias vigentes; validar solo lo que cambie.
5. Aplicar mediante operaciones nativas; verificar el sujeto completo y registrar
   evidencia todavía aplicable. Cerrar la sucesora con sus guards, sin editar estados
   a mano ni copiar los UUID o la identidad sintéticos a ese proyecto.
6. Ante interrupción, inspeccionar el journal y usar recuperación/rollback nativos
   con su autorización exacta, conservando cambios posteriores. No reiniciar a ciegas.

La ejecución real, instalación, publicación, commits y push permanecen sin autorizar.
La reducción física de archivos corresponde a V4-21/22 y todavía no se ha implementado.
Windows/H2, Copilot real y valoración humana mantienen sus pendientes anteriores;
AC-43 no se transforma en ahorro conseguido y AC-40 sigue inconcluso.

Evidencia reutilizable: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-19-20`:
binding/admission, escenario y ZIP inicial, logs focales, sonda de lanzador,
cancelación CLI, acciones, resultado/recursos y conservación final. Se conserva
el consumidor cerrado y sus dos fuentes congeladas para el trabajo posterior.

## Revisión crítica posterior

Se corrigen tres problemas, sin iniciar V4-21 ni repetir el recorrido completo:

| Hallazgo | Corrección y comprobación |
|---|---|
| Un descendiente que retuviera un pipe dejaba lectores daemon vivos tras el timeout. La limpieza contenía además un `wait()` sin cota. | Lectura de bytes disponibles de ambos pipes sin hilos lectores; cierre de handles y terminación del hijo con espera de limpieza de máximo 1 s. Se mantienen 60 s de observación, límites brutos/stdout/stderr y rechazo sin resultado parcial. Una prueba real falló antes y pasa después; comprueba descendiente realmente creado, hijo terminado y ambos lectores cerrados. El descendiente artificial se retira desde el test. |
| El ajuste del prefijo de rutas largas añadía el NUL que faltaba a una respuesta truncada. | Rechazar la salida incompleta antes de transformar prefijos. La prueba reproduce el falso inventario válido antes de corregirlo y pasa después. |
| El lanzador permitía reutilizar una reserva si el worker no había arrancado; el saldo excluía ese fallo. | Reserva durable bloqueada ante cualquier intento anterior, incluso sin worker. Se comprueba rechazo sin mutación y admisión previa. El saldo imputa el fallo de lanzamiento anterior y el recorrido real: **2/2 plazas nuevas consumidas, cero disponibles**. |

**41 tests focales pasan en 58,285 s**, sin errores, fallos ni omisiones: 26 de
inventario/captura, siete de reutilización, cinco de administración/reserva y tres
de Git real en rutas largas. La última aserción de arranque efectivo del descendiente
se ejecutó además de forma aislada y pasó (0,510 s). Se reutilizan los tres controles
de workflow anteriores, cuyo código no cambió: **44 tests distintos con evidencia
aplicable**, sin presentarlos como 44 ejecuciones nuevas. Fixtures estáticos (13),
contrato del plugin, AST y diff válidos; contrato canónico e identidad sin cambios.

La consulta de solo lectura sobre el consumidor retenido devuelve exactamente las
**1.180 rutas y hashes** del módulo congelado. Sus 20.922 archivos observados
(incluido `.git`, a diferencia del censo Git anterior) conservan tamaños/fechas de
modificación. El recorrido nativo anterior sigue acreditando cancelación, sucesora,
cierre y conservación bajo su runtime exacto; no se atribuyen sus 479,623 s ni
163,44 MiB a la nueva captura. El módulo actual ya difiere del provisional: V4-16
debe reconstruir el paquete y el recorrido final debe usar esa fuente exacta.
La rama POSIX del nuevo lector no se ha ejecutado en este host Windows.

En Windows se usa [PeekNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-peeknamedpipe)
sobre handles privados sin otra lectura pendiente; en POSIX, `select`. No se elevan
permisos, no se repara el host y no se añaden procesos envoltorio a Git.

**Desviación presupuestaria corregida:** el hito inicial reutilizó la reserva tras
el fallo previo a `CreateProcess`. Se conserva que hubo un solo recorrido real,
pero la regla «un fallo consume plaza» obliga a imputar dos lanzamientos. Esta
revisión no consume otro recorrido ni amplía el máximo. Antes del recorrido final
habrá que resolver explícitamente una plaza; el desarrollo de componentes no
concede esa autorización. El saldo horario se actualiza sin reiniciarlo en el
registro compartido, manteniendo los 90 min protegidos. Las dos plazas históricas
de H2 siguen intactas. No se altera el plan validado para ocultar esta desviación.

Evidencia añadida al mismo directorio: `review-tests.log/json` y
`review-component.json`. Los fallos reproducidos antes de corregir se conservan en
el historial de herramientas; no son ejecuciones del recorrido completo. No hay
reducción física de archivos todavía, instalación, publicación ni actuación sobre
consumidores reales. Windows/H2 y el resto de pendientes de host se mantienen.


## V4-21 — continuación autorizada

El usuario valida la revisión anterior y concede **una plaza adicional para el
recorrido final, sin ampliar horas**. Total conocido/reservado: 57; las dos plazas
nuevas anteriores siguen imputadas y la tercera queda reservada. V4-21 está
implementada y verificada por componentes. V4-14 ampliada y V4-22 no se han iniciado.

El prototipo pasó en 13.36 min de los 45
permitidos: lectura mixta, guard sobre ruta lógica, staging, diario 2.1 recuperable
y replay de crecimiento. Se continuó dentro del bloque autorizado. El lector se
integra en la frontera común de bytes/hashes; las fuentes, guards y estados siguen
usando rutas lógicas. Publicación y staging agrupan directamente con memoria
acotada, manteniendo los diarios 2.0/2.1. Distribución/runtime declaran la capacidad
y el escritor comprueba el lector fijado. Las consultas conservan su carácter de
solo lectura; no hay catálogo persistente ni compactación automática.

La referencia reutiliza el **B ya congelado**, con sus bytes y siete grupos de
transacción originales: 102 archivos iniciales y 407 altas, de ellas 389 objetos
(1.367.937 bytes). El replay deja **25 altas: siete ZIP y los mismos 18 registros**,
**93,86 % menos**, sin retirar archivos iniciales ni crear objetos sueltos nuevos.
Se validan los 458 objetos lógicos finales y el modelo canónico. Bytes añadidos:
1.473.154 → 1.552.664 (**+5,40 %**); incluyendo escrituras completas de archivos
modificados: 1.656.985 → 1.736.495 (**+4,80 %**). Ambos cumplen el máximo de +10 %.
El corpus grande del incidente se conserva intacto para V4-22.

Cuatro componentes predeclarados, AB/BA, sin calentamientos ni reintentos. A y B de
esta tabla identifican soporte suelto y agrupado sobre el mismo caso B congelado;
no son cuatro recorridos completos del producto.

| Orden | Soporte | Pared (s) | CPU del job (s) | Pico del job (MiB) | Altas |
|---|---|---:|---:|---:|---:|
| 1 | A-loose | 15.075 | 10.922 | 32.50 | 407 |
| 2 | B-ZIP | 13.496 | 9.500 | 34.18 | 25 |
| 3 | B-ZIP | 34.623 | 15.281 | 34.20 | 25 |
| 4 | A-loose | 19.624 | 12.688 | 32.50 | 407 |

CPU mediana: 11.805 → 12.391 s
(**+4,96 %**). Pico de memoria: **+5,23 %**, con máximo de
34.20 MiB, inferior a 512 MiB. Cumplen ambos
máximos relativos de +10 %. La mediana de pared aumenta **+38,67 %**; el soporte ZIP
oscila entre 13,496 y 34,623 s en este host compartido. Son resultados descriptivos
de dos muestras por soporte; no acreditan menor latencia ni generalización. Se
conservan todas las muestras, sin nueva búsqueda de estabilidad; AC-43 no cambia.

Publicaciones de objetos nuevos: 389 → siete; el máximo temporal privado derivado
para este componente es 510,885
→ 980,825 bytes. Se deriva del mayor cuerpo publicado y las
escrituras congeladas, secuenciales; no mide el pico global de staging/transporte,
bloques asignados por el sistema de archivos ni espacio de Git. El pico de memoria
sí se mide sobre el job completo. Cero descendientes activos al terminar los cuatro.

**48 tests distintos con evidencia aplicable**: 23 de almacenamiento documental,
dos de diario, cinco de prototipo/staging/idempotencia nativa, 15 de contenedor,
paquetes, pin y rutas largas, y tres de autoridad/recuperación. Cuatro tests antiguos
se adaptan a la ubicación física y al punto de inyección de fallos; conservan
comprobación de bytes, no sobrescritura, interrupción previa al diario y recuperación.
Solo se repiten esos casos y las fronteras modificadas. Se conservan los resultados
iniciales fallidos y las comprobaciones posteriores. La prueba de ruta larga corrigió
su comprobación de alias y limpieza del fixture; el temporal propio residual quedó
retirado. No se reparó Windows ni se ejecutó H2.

Contrato estático y 13 fixtures válidos, AST/diff y conservación de contrato canónico
e identidad comprobados en la primera implementación. Esa fuente coincide con sus
cuatro medidas y los originales congelados mantienen sus hashes. El dictamen vigente
de AC-50–52, tras corregir las brechas encontradas, figura en la revisión siguiente.
La compatibilidad/corte del runtime completo corresponde a
V4-14 ampliada; el paquete y recorrido finales con fuente exacta siguen en V4-16.
La compactación histórica y su restauración siguen en V4-22. Ninguna de estas
verificaciones se sustituye por el replay de cuerpos de este hito.

Saldo conservador aproximado: **8 h 30 min**, incluidos
90 min protegidos, y **una plaza final reservada**. Este hito no ejecuta recorridos
completos ni consume la plaza adicional. Windows/H2, Copilot real y valoración
humana permanecen pendientes. Sin instalación, publicación, commit o push.

Evidencia compartida añadida: `v4-21/authorization.json`, `source-before.json`,
`prototype.json`, `frozen-B.json/zip`, logs de regresión/guards,
`component-series.json`, cuatro `component-result-*.json`, `component-source.zip`
(recuperable y verificado contra las huellas medidas) y `validation.json`, bajo
la misma operación de desarrollo. Se conserva un único registro compartido y este
mismo resultado; no se crea un informe por familia.


## Revisión crítica de V4-21 — resultado vigente

La revisión reproduce y corrige cinco brechas que la comprobación inicial no cubría:

- Una copia ZIP contradictoria publicada durante la escritura podía dejar un
  respaldo ilegible y, aun así, permitir el commit. Ahora se renueva el índice y
  se verifican las representaciones competidoras antes del diario.
- El lector fijado podía degradarse o alterarse después de crear el publicador.
  Se comprueban sus capacidades e integridad antes y después de publicar el ZIP.
- `ZipInfo` normalizaba un sufijo NUL del nombre central y aceptaba una entrada
  cuyo nombre original no era un hash plano. Se exige también el nombre original.
- Mayúsculas y alias 8.3 podían eludir la prohibición de modificar contenedores
  mediante transacciones de negocio. Aplicación y recuperación usan la misma
  comprobación del directorio reservado; los alias reales se prueban en Windows.
- Un ZIP podía alterarse entre su hash completo y la lectura del índice. La
  observación de identidad del archivo permanece abierta durante toda la
  comprobación, sin volver a leer todos sus cuerpos. También se controla como
  `ContractError` una lectura corta del pie ZIP.

Los casos negativos conservan los bytes mutables originales y no dejan diario
pendiente; no reparan ni eliminan las copias inmutables corruptas o sin referencia.
No se modifica el contrato canónico, el formato de referencia ni el diario.

**35 pruebas focales pasan en 103.71 s**. Tras la última
corrección se repiten solo **29 afectadas**, en 44.71 s:
22 de contenedor, cinco de prototipo/staging/idempotencia nativa y dos de diario.
Son **36 pruebas distintas durante la revisión**, sin fallos ni skips. Se conservan
las siete comprobaciones anteriores de autoridad/documentación por no existir otro
cambio en esas reglas. Los 48 resultados iniciales conservan su propia fuente;
no se presentan como una nueva ejecución. Contrato, 13 fixtures, AST y diff válidos.

La primera serie de revisión pasó los límites. La reproducción posterior del
cambio entre hash e índice obligó a conservarla como evidencia de su fuente
intermedia y ejecutar una única serie final AB/BA. No se descartaron muestras ni
se repitió buscando éxito. Hubo además un fallo de lanzador previo a crear un
proceso: `invocation=None` no era válido como variable de entorno. Se registra,
se corrige a texto y se reanuda sin repetir las 35 pruebas. Durante esta revisión
hay ocho componentes medidos, un fallo previo al arranque y **cero recorridos
completos**; la plaza final sigue reservada.

| Orden final | Soporte | Pared (s) | CPU del job (s) | Pico (MiB) | Altas |
|---|---|---:|---:|---:|---:|
| 1 | A-loose | 23.210 | 13.172 | 32.32 | 407 |
| 2 | B-ZIP | 19.824 | 14.062 | 34.10 | 25 |
| 3 | B-ZIP | 14.792 | 11.047 | 34.05 | 25 |
| 4 | A-loose | 18.869 | 12.719 | 32.32 | 407 |

Fuente final: CPU mediana **-3.02 %**, pico de memoria
**+5.50 %**, máximo
34.10 MiB. Pasan los límites de +10 % y
512 MiB. Pared mediana: **-17.74 %**, descriptiva en este
host compartido; tampoco acredita menor latencia global de S8. Las dos muestras
por soporte no establecen una mejora general de rendimiento.

Se confirma **407 → 25 altas (−93,86 %)**, cero fragmentos sueltos nuevos,
**+5,40 % de bytes nuevos**, cero archivos iniciales retirados y 458 objetos
lógicos comprobados. El máximo temporal de contenido sigue siendo una derivación
del componente, no una medida de todo el staging/transporte. F7 usa un almacén
sin pin: mide publicación, localización e integridad; no incluye el coste de todo
el runtime fijado ni sustituye su corte/rollback. **AC-50–52 verificados por
componentes**, con integración completa pendiente de V4-14 ampliada y F8.

Las fuentes medidas y los originales congelados se comprueban por hash. Las tres
series y sus fuentes se conservan; el resultado vigente es
`v4-21/review-final-component-series.json`, con fuente recuperable en
`review-final-component-source.zip`. Pruebas y cierre en
`review-final-tests.log` y `review-final-validation.json`, dentro de la misma
operación. Este sigue siendo el único informe compartido.

Saldo conservador a 17:06 UTC: **8 h 07 min**,
incluidos 90 min protegidos, y **una plaza final**. Se carga todo el tiempo desde
el origen común, incluida esta revisión; no se amplían las diez horas ni las plazas.
V4-14 ampliada y V4-22 no se han iniciado. Windows/H2 siguen pendientes.
Sin instalación, publicación, commit, push ni cambios en consumidores reales.


## V4-14 ampliada — compatibilidad y recuperación

Autorización del usuario posterior a la revisión de V4-21. **Verificada en alcance
local sintético**, formato 3.1/método 3.1.0, desde la 3.4.3 publicada hacia la
candidata. V4-22 sigue sin iniciar; no se instala ni publica el plugin.

Se reproducen y corrigen dos incompatibilidades materiales: volver a un lector
sin ZIP conservando paquetes, y declarar ZIP en una proyección de desarrollo que
omitía `object_zip.py` por ser un archivo aún no seguido por Git. Núcleo,
diagnóstico e instalador actual bloquean la primera antes de cambiar archivos;
se mantienen copias sueltas si el destino no lee ZIP. Distribución incluye el
lector y su test; el constructor verifica sus cuatro dependencias antes de producir
el paquete. El diagnóstico conserva únicamente dependencias estándar y no importa
el motor del proyecto para comprobar su integridad.

| Comprobación | Resultado |
|---|---|
| Preview, bundle ausente y pin cambiado | Sin escrituras; un pin alterado no concede la aplicación. |
| Actualización nativa interrumpida | Recuperada; decisiones/UID, tarea, historia y código preservados, sin renovar autoridad. |
| Trabajo posterior | Se conserva una nota independiente; un pin modificado bloquea la reversión sin sobrescribirlo. |
| Reversión anterior a ZIP | En copia independiente del mismo corte: restaura los archivos previos y conserva el registro de reversión. |
| Datos nuevos agrupados | Se rechaza cambiar solo el pin; el diario 2.1 con referencias ZIP se recupera con el lector compatible. |
| Respaldo completo anterior | Restaurado a otro consumidor desechable; bytes y CLI publicada 3.4.3 válidos. El consumidor con datos nuevos queda intacto. |
| CLI fijadas finales | 3.4.3 sobre cuerpos sueltos y candidata sobre cuerpos agrupados: válidas, consultas sin escritura. |
| Mantenimiento todavía desconocido | Conserva el diario y bloquea mutaciones de negocio; su recuperador corresponde a V4-22. |

**Ocho pruebas focales distintas**: siete de frontera (incluidos diarios 2.0/2.1,
preparación/aplicación/recuperación del instalador y paquete incompleto) y una matriz
nativa consolidada. Esta última pasa en 489.43 s dentro
del corte de 720 s: **una única actualización real** y copias del estado para
contrastar recuperación antes/después de ZIP. Dos proyecciones CLI finales verifican
el diagnóstico definitivo. No se repiten cuatro actualizaciones ni S8.

Se conservan los errores iniciales: el fixture antiguo debía construirse con
cuerpos sueltos; la comprobación real detectó después la dependencia omitida.
La generación de ese fixture usa escritura antigua solo durante su bootstrap;
los controles de capacidad de la operación no se simulan y la CLI publicada valida
la referencia. Se conservan las cinco fronteras ya superadas. El último cambio del
diagnóstico se verifica por separado, sin repetir la actualización de ocho minutos.
La fuente exacta de la matriz nativa y la de las CLI finales están archivadas y
verificadas por hash; no se presentan como una única candidata byte-idéntica.

Contrato, 13 fixtures y conservación de contrato canónico/identidad comprobados.
Las mediciones F7 permanecen ligadas a la fuente de V4-21: lector ZIP, referencias
y runner conservan sus hashes; no se actualizan porcentajes ni se atribuye ahorro
global al nuevo runtime. La puerta y paquetes finales corresponden a V4-16.
Los lectores 1.5/2.0/3.0 y adaptadores reutilizan su evidencia no afectada; no se
infiere otra actualización ejecutada ni aceptación del host.

Evidencia en la misma operación: `v4-14-expanded/result.json`, logs/recibos de los
intentos conservados, `final-boundary-tests.json`, `consolidated-validation.json`,
`final-pinned-cli-old.json/new.json`, `native-tested-core.zip` y
`final-tested-core.zip`. Son fuentes de evidencia, no una instalación activa.

Saldo a 17:46 UTC: **7 h 26 min**, incluidos
90 min protegidos; una plaza final intacta. Este hito ocupa 38.0 min del
bloque conjunto de 90 min: quedan **51 min para V4-22**. Se supera el objetivo
interno inicial de 30 min al resolver las incompatibilidades; la cota compartida
y las diez horas globales no se amplían. Cero recorridos completos adicionales.
Windows/H2, Copilot real y percepción humana siguen pendientes. Sin consumidores
reales modificados, instalación activa, publicación, commit o push.

## V4-22 — compactación física y restauración verificadas

**Resultado local: AC-53, AC-54 y AC-55 superados.** Se reutilizó el consumidor
sintético cerrado de V4-19/20. Primero se proyectó un runtime compatible solo en
ese fixture, conservando los anteriores, y se congeló su composición antes de
compactar. No hubo instalación activa ni cambios en consumidores reales.

| Medida del mismo corpus | Antes | Después |
| --- | ---: | ---: |
| Archivos internos físicos, incluidos runtimes y recibos | 20.384 | **9.352 (−54,12 %)** |
| Bytes internos activos | 60.019.043 | **64.561.918 (+7,57 %)** |
| Objetos lógicos verificados | 11.038 | 11.038 |
| Originales sueltos del preview | 11.038 | 0 |

Se publicaron cinco ZIP inmutables y un recibo. Los 10.526 archivos restantes
del inventario completo, incluido el código del consumidor, conservaron sus bytes.
La reducción es de archivos activos; ZIP_STORED e información de recuperación
añaden bytes. No se atribuye ahorro de disco, tokens ni tiempo global de S8.

Respaldo independiente: **un ZIP de 32.452.648 bytes**, fuera del consumidor.
Antes de retirar se restauraron y compararon los 11.038 originales, 30.200.874
bytes. Esa restauración de prueba se conserva en el área operativa hasta el cierre
de las evidencias; sus archivos no cuentan como archivos activos del consumidor.
Git conserva 18 archivos y 26.300 bytes de metadatos, sin recuperación de historia.
Su enumeración pasó de 21.570 rutas antes de la retirada a 10.532 después; la
primera cifra ya incluía los paquetes preparados y el diario pendiente.

El usuario autorizó separadamente la retirada del preview
`5ca24965975669b58d57bf410b6b3b6390d2b6c3b1e1680628b1edf71cf9db25`,
después de comprobar respaldo y restauración. La CLI fijada realizó ambas fases;
la validación nativa posterior devolvió 0 y el doctor quedó válido. No quedan
diario pendiente, temporales del consumidor, staging de restauración ni procesos
propios activos. Los ZIP y el respaldo permanecen verificables sin catálogo global.

Comprobaciones: **12 casos de mantenimiento y 34 regresiones** de lector y
compatibilidad superados. Incluyen siete fronteras de interrupción, exclusión de
dos procesos, rutas equivalentes de Windows, diarios de negocio 2.0/2.1, corrupción,
preview obsoleto, falta de espacio, pin incompatible y conservación de contenido
desconocido/no referenciado. Se comprobaron los 16 estados históricos, sus 669
referencias y 383 referencias en objetos estructurados. Un histórico representativo
se exportó una sola vez: 39 archivos y 260.590 bytes; se contrastó de nuevo con
lecturas exclusivamente agrupadas tras retirar, sin otra materialización.

Correcciones durante el hito: el despachador conserva el límite previo de 128 MiB
para diarios de negocio; mantenimiento mantiene 16 MiB. Un diario real de más de
16 MiB recuperó correctamente. El mutex normaliza alias/prefijos de Windows para
no admitir dos recuperadores del mismo slot. Las regresiones de esas ramas se
repitieron; los casos no afectados se reutilizaron. Dos errores del verificador
sintético —buscar `snapshot.json` donde había `state.json`, y esperar objetos
sueltos después de un escritor que ya agrupa— se corrigieron conservando evidencia,
sin repetir una compactación grande ni un recorrido completo.

La fuente nativa exacta está en `v4-22/tested-core.zip`. Las correcciones finales
del mutex y de admisión de diarios tienen pruebas focales; la comparación AST
confirma que el algoritmo de empaquetado, respaldo, restauración y retirada no
cambió respecto al recorrido grande. `source-audit.json` distingue esas fuentes:
la puerta del paquete final exacto sigue en V4-16. Contrato, 13 fixtures, AST,
diff y conservación de fuentes canónicas, identidades y plan aprobado comprobados.

Evidencias: misma operación, subcarpeta `v4-22`; `result.json`, inventarios y
preview congelados, autorización separada, recibos de CLI, recursos, logs,
`checks-summary.json`, `historical-export.json` y `residual-check.json`.
Los procesos locales de preparación y cierre emplearon 320,5 s y 218,9 s,
respectivamente, sin llamadas a IA; el intento inicial fallido consumió 100,4 s
y queda registrado. No son mediciones comparables de rendimiento.

Saldo de cierre aproximado: **7 h**, incluidos 90 min protegidos. V4-14 ampliada
y V4-22 ocuparon aproximadamente 65 min de sus 90 min compartidos; no se amplían horas ni plazas.
La plaza del recorrido final está intacta. Próximo: V4-15 afectada → V4-16 → V4-18.
Windows/H2, Copilot real y percepción humana siguen pendientes. Sin instalación,
publicación, commit ni push.

## V4-15, V4-16 y V4-18 — cierre técnico y paquetes finales de desarrollo

**Desarrollo técnico cerrado; aceptación completa y release estable con reservas.**
Se mantienen las seis mejoras y se separan las 56 aceptaciones en el registro
compartido y en `v4-final-151618/acceptance-matrix.json`; G1–G10 tienen su mapa.
V4-15 cierra la comprobación técnica, V4-16 el paquete de desarrollo exacto y
V4-18 el informe para decidir una release. No se convierte ningún pendiente en pasado.

| Mejora | Estado acreditado y reserva |
| --- | --- |
| M1 · Transporte y diagnóstico | Implementada; captura y canales comprobados. Sobrecoste AC-40 inconcluso. |
| M2 · Operaciones completas | Implementada y F8 superado; continuidad/aceptación de host pendiente. |
| M3 · Alcance documental | Contexto, obligaciones y literales comprobados; comprensión humana no inferida. |
| M4 · Instrucciones por operación | Seis skills y mapa de reglas conservados; selección real de host pendiente. |
| M5 · Mantenimiento proporcional | Recorridos técnicos implementados y negativos conservados; esfuerzo humano diferido. |
| M6 · Cálculo medido | Componente acotado verificado; objetivo temporal global no alcanzado y compromiso aceptado. |

| Entrega | Evidencia final |
| --- | --- |
| Garantías afectadas | Contrato, 13 fixtures, 14 smoke tests, regresión real de rutas largas del plugin y cuatro negativos adversos pasan sobre el núcleo extraído. Las 46 comprobaciones de V4-22 se reutilizan por huella. |
| Integración F8 | Una ejecución pública completa: preparación/inicio, prueba Python real de `greeting()`, implementación/evidencia/verificación/cierre e integración explícita; aceptación funcional separada. 9 invocaciones. |
| Almacenamiento nuevo F8 | **25 archivos internos nuevos frente a 407: −93.86 %**, con 1,559,892 bytes nuevos, 1.0589× referencia, dentro de ≤81 archivos y ≤1,10× bytes. |
| Conservación | Ninguna de las 102 rutas iniciales retirada; 100 archivos inmutables, incluidos 69 objetos sueltos, byte idénticos. Los dos índices mutables conservan sus 338 elementos y seis recibos previos. Lectura mixta, base confiable intacta y ningún diario pendiente. F8 no compacta el estado inicial. |
| Paquetes | Cinco ZIP, dos construcciones byte idénticas, extracción completa de cada entrada y mismo núcleo de 660 archivos/seis skills. Validador nativo Copilot y doctor desde la extracción Codex pasan. |
| Recuperación | Datos y runtimes del caso final archivados y verificados antes de retirar solo el temporal propio; se excluyen `.git` y cachés de bytecode. No acredita restauración de un repositorio Git completo. Cero procesos propios activos; paquetes, capturas y resultados conservados. |

Fuente: `working-tree:c8fc93f4697517349286a85d91a51a520485e56b2928e3ba155957d9cabcca29`. Runtime: `079668df15a4a41e655b1ccc9eda7d27613e1c762f2bec04cdaab1e89fcf9745`.
Canal: `development-unreleased`; versión base del manifest: **3.4.3**, sin
promoción de versión ni sustitución de los assets publicados. Directorio de entrega:
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-final-151618\packages`. Manifiesto y `SHA256SUMS` acompañan a los cinco ZIP.

La ejecución final es funcional, no otra comparación temporal. El lector/escritor
y el runner F7 mantienen exactamente sus bytes; la reutilización, el resto de
fuentes y sus límites están en `reuse-map.json`. Se conservan el −54,12 % de
archivos activos del histórico F6 y su +7,57 % de bytes; no se atribuye ahorro de
disco, tokens facturados ni tiempo global a esos recuentos.

Reservas explícitas: AC-40 sigue **inconcluso**; AC-43 conserva **no alcanzado**
(la serie histórica fue aproximadamente 33,48 % más lenta; compromiso aceptado
por el usuario). AC-27/AC-42 quedan vinculados a sus dos parejas históricas y su
runtime a76207a25976; el runtime actual no se presenta como otra serie ABBA.
AC-30/AC-34, H2, Copilot real y la incidencia de aislamiento de Windows permanecen
pendientes. AC-36 se observa en uso real prolongado. AC-26 queda acreditado en
alcance técnico, con estas reservas visibles; no acredita aceptación global.

Se conservó un fallo de preparación anterior a toda operación pública: objetos
Git copiados de solo lectura y la comprobación de su ruta con alias de Windows.
Se corrigió el arnés dentro de su temporal verificado; no cambió el producto ni
se repitió el gate. La admisión posterior confirmó runtime exacto y cero escrituras;
la única plaza final se cargó antes de lanzar el único F8 completo.
Un verificador posterior exigía igualdad byte a byte también al índice y al diario
mutables. Se corrigió esa expectativa: ninguna ruta inicial retirada, 100 archivos
inmutables idénticos y todas las entradas previas de ambos índices intactas. El
recorrido ya terminado se conservó y solo se completaron sus comprobaciones finales.

Los controles técnicos del gate pasan sobre la huella extraída. **El gate estable
sigue sin ejecutarse**: faltan aprobación separada de versión y código integrado
en checkout limpio. No se fabrica aprobación, commit, tag, instalación, registro
ni publicación. El siguiente paso es decidir ese recorrido de release, manteniendo
las reservas; no hay más desarrollo autorizado pendiente en estos tres entregables.

Presupuesto: aproximadamente **27 min de 75** para este cierre; quedan aproximadamente
**6.5 h** de las diez adicionales, incluidos 90 min protegidos.
Se usó una plaza final, sin ampliación; las dos reservas históricas H2 siguen intactas.
Las esperas y pruebas fueron procesos locales, sin llamadas a IA.

### Revisión crítica de V4-15, V4-16 y V4-18

No se ha encontrado una regresión funcional en la evidencia revisada. Se corrigen
tres conclusiones/documentos sin modificar el runtime ni reconstruir sus paquetes:

| Hallazgo | Corrección |
| --- | --- |
| El estado de V4-17A aún decía «cero parejas válidas» y retenía reservas ya consumidas. | Estado vigente enlazado a las dos parejas históricas, su fuente, objetivo temporal no alcanzado y F8 funcional actual. H2 conserva sus dos reservas. |
| «Caso archivado íntegramente» podía entenderse como recuperación de todo Git. | Se limita a datos/runtimes: `.git` y bytecode quedaron excluidos. La auditoría comprueba las 905 entradas conservadas; no afirma una restauración Git completa. |
| AC-52 podía leerse como una medición comparativa del paquete final. | CPU/memoria relativas conservan su medición histórica de componente. Hay módulos compartidos modificados desde ella: identidad del codec y runner no basta para afirmar medición nueva. F8 acredita los archivos/bytes y el límite absoluto de memoria; CPU relativa final no remedida. |

La auditoría independiente vuelve a verificar checksums/CRC de los cinco ZIP,
los 660 archivos de núcleo en las cuatro variantes y los dos payloads del instalador.
Recalcula los 25 archivos/1.559.892 bytes nuevos desde el archivo conservado,
comprueba los 100 archivos iniciales inmutables y todas las entradas previas de
los dos índices. La base confiable coincide con el fixture congelado y sus cuatro
archivos de instrucciones, contrastados con los originales retenidos. Las 56
aceptaciones y seis mejoras tienen evidencia accesible; se mantienen las reservas.
El auditor inicialmente comparó también runtimes históricos no copiados al fixture;
se corrigió ese alcance, sin ejecutar operaciones de negocio.

Evidencia: `v4-final-151618/review-audit.json` y `review-findings.json`.
Cero recorridos, builds o pruebas de runtime repetidos. El runtime y los paquetes
mantienen su huella final. Presupuesto actualizado en el registro compartido,
sin ampliar horas ni plazas. Windows/H2 siguen pendientes; no se instala ni publica.

### Decisión del responsable y cierre de desarrollo

El 2026-10-18 el responsable valida lo revisado, autoriza cerrar el desarrollo y
publicar la release 4.0, incluida su distribución en Codex. Se prepara 4.0.0, con
la aprobación de versión registrada y la guía de actualización. Las reservas
Windows/H2, AC-40, objetivo temporal no alcanzado y medición comparativa final
AC-52 no observada se conservan; su aceptación no acredita pruebas no ejecutadas.
La publicación y el gate del SHA integrado se registran en la operación de release.
