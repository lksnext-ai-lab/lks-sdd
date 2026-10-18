# V4-05 — Corrección de Git con rutas largas en Windows

2026-10-16. Plan 0.4. Alcance: corregir la limitación abierta en la revisión de
V4-05, repetir sus comprobaciones y presentar el dictamen antes de V4-05A.
El estado exacto y los resultados finales constan en [el registro](v4-05-progress.json).
Se conservan los informes, resultados y fallos anteriores sin reescribirlos.

## Dictamen y resultados

**V4-05 verificada en alcance técnico local, bajo las condiciones de compatibilidad
indicadas abajo.** Se cierra el fallo del recorrido público largo que impedía
continuar; V4-05A no se inicia.

- 28/28 casos del módulo completo de preparación, candidata Git 1.
- 43/43 regresiones de aprobación, routing, observación, exportación y ciclo de vida.
- 17/17 casos específicos sobre la candidata final.
- 2/2 casos públicos repetidos sobre la candidata final: Windows largo y ambos paquetes.
- 88 casos distintos con último resultado aplicable positivo; las repeticiones no
  aumentan el número de casos distintos. La evidencia conserva las candidatas separadas.
- Contrato estático válido y diff sin errores de formato. Los protocolos y resultados
  históricos protegidos conservan sus bytes.

El fetch con URL absoluta también se comprobó contra un remoto local sintético:
la referencia recibida coincide con el HEAD esperado. No se realizó una publicación
ni se contactó un remoto de red.

## Corrección y garantías

Git 2.51.0.windows.2 rechaza el directorio de proceso largo incluso al habilitar
core.longpaths o pasar un alias a -C. La solución mantiene un directorio de proceso
corto y señala explícitamente los directorios Git y checkout mediante alias 8.3
existentes. Cada alias se contrasta con el directorio original; no se crean enlaces,
no se mueve el proyecto y no se modifican configuración global, PATH, TEMP o TMP.
El recorrido corto anterior se conserva.

Se reconocen directorios .git y referencias a metadatos externos, se preservan los
prefijos de consumidores anidados y se mantienen exclusiones locales, de info/exclude
y de includes ordinarios. Las rutas relativas conocidas de exclusiones, atributos y
hooks se resuelven contra el checkout. Rama, HEAD, referencias y contenido observado
se contrastan con el recorrido corto. No se cachean alias, propiedad ni configuración.

Usar Git con directorios explícitos puede saltarse su descubrimiento normal. Por eso
el recorrido largo comprueba mediante Windows que el checkout, la referencia .git
y los metadatos pertenecen al usuario del proceso. Un propietario desconocido se
bloquea; no se importan excepciones safe.directory para ampliar confianza. Esta
comprobación técnica no identifica al operador funcional ni concede autoridad SDD.

La última corrección estrecha conserva espacios significativos en las referencias
.git: un caso con dos directorios distintos mostraba que eliminarlos podía leer una
rama señuelo. También se bloquea la reinterpretación de variables que redirigen
repositorio, índice, objetos o configuración: el caso con índice relativo podía perder
un archivo rastreado que coincidía con una exclusión. Los errores de configuración
conservan el diagnóstico nativo acotado; bare y core.worktree no se reinterpretan
como otro checkout. Las reproducciones negativas y los cambios exactos se conservan.

La consulta sigue siendo informativa y sin materialización. Continúan las guardas
frescas, los permisos y el contrato literal de V4-05. No cambia specs/canonical,
método/esquemas, seis skills, versiones ni instalación activa.

## Condiciones de compatibilidad

La ruta larga necesita alias 8.3 disponibles y propiedad verificable del usuario
actual. Se bloquean expresamente condiciones Git includeIf gitdir, variables de
entorno que redirigen el repositorio/índice y rutas de configuración de entorno
relativas. Un fetch largo requiere URL absoluta configurada; las relativas se
bloquean para no contactar otro destino desde un directorio distinto. Estas
configuraciones necesitan una invocación limpia o un checkout corto. No se afirma
soporte universal de volúmenes, permisos, redes o perfiles Git de Windows.

Los contrastes de archivos siguen ocurriendo durante un intervalo; no se promete
atomicidad ni bloqueo distribuido. Antes de aplicar se reevalúa con las guardas
vigentes. El modo largo añade una consulta de configuración por invocación Git y
la contabiliza; no se oculta ese coste bajo el contador de llamadas públicas.

## Verificación y procedencia

Se repite el módulo completo test_work_prepare y las regresiones de aprobación,
routing, observación, exportación y ciclo de vida. La prueba pública larga se ejecuta
primero y comprueba los archivos antes y después. Ambos paquetes se contrastan por
su inventario completo y se ejecutan sus bytes extraídos mediante el CLI fijado;
esto no equivale a instalación ni observación humana de Codex o Copilot.

La batería completa pertenece a la primera candidata Git de este bloque, conservada
en git-candidate-1-core.zip. Tras aislar el caso de espacios y el índice relativo,
la candidata final repite las pruebas específicas y el recorrido público/paquetes.
Es una comprobación focal de las últimas guardas; no se presenta como otra ejecución
íntegra de los 28 casos. Se conservan los resultados aplicables y las huellas por
candidata en git-verification.json. Ningún fallo intermedio se convierte en éxito.

La primera campaña específica dejó errores de limpieza de objetos Git de solo
lectura, además de fallos de implementación. La limpieza de las nuevas pruebas se
corrigió usando rutas extendidas y permisos solo dentro de sus temporales propios;
las campañas posteriores verifican esa limpieza. Los restos fallidos identificados
se registran para conservación; no se limpia el resto de TEMP ni los worktrees nativos.
Una preparación auxiliar de fetch falló al clonar el fixture y otra generó configuración
inválida; esos montajes no acreditan éxito ni fallo del transporte de publicación.

## S8 y ahorro

Se repite la consulta sobre el fixture objetivo de 338 elementos y se contrastan sus
319 fragmentos literales, la prosa incierta y la conservación de fuentes. Cada
consulta conserva hashes de sus componentes. No se ejecutan implementación, pruebas
funcionales de S8, cierre o integración. Son comprobaciones de preparación, no nuevos
intentos funcionales completos ni una pareja comparable de rendimiento.

La consulta S8 final terminó en 23.835 s, con 25.233 s de preparación
de entorno separados. Resultado ready, 319/319 fragmentos y fuentes sin cambios.

Una carga del modelo no representa todo el I/O ni el coste de validar el runtime,
Git, diagnóstico o entrega. Tokens facturados y ahorro integral siguen sin medirse;
la mejora S8 ≥20 % sigue pendiente. La percepción humana permanece diferida al uso
real sostenido y la observación de Copilot se conserva para el final.

## Presupuesto y continuación

Bloque iniciado 14:14:13Z, cota 45 minutos incluyendo investigación, montajes fallidos,
correcciones, pruebas y reporte. Se mantienen 48 intentos completos, 8 h humanas,
12 h de entorno y M6 ≤2 variantes/4 h. No se añaden intentos completos ni variantes
M6 y el saldo global histórico sigue sin certificar. La cota no crea saldo adicional.
Los tiempos de campañas paralelas no se suman como si fueran tiempo secuencial.

Evidencia en el área V4-05 ya existente del estudio H1: snapshots por candidata,
probes, logs, verificaciones y git-resource-ledger.json. V4-05A no iniciado. No hay
commits en el proyecto, integración, push, instalación, publicación ni activación.
