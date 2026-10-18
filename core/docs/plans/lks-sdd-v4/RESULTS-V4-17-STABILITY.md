**Decisión posterior vigente (2026-10-18):** se acepta variabilidad de cargas y se retira la exigencia de estabilidad previa; [alcance y reglas](DECISION-SHARED-HOST-MEASUREMENT.md). Los datos y conclusiones históricos de este documento se conservan.

# V4-17 — Medición: instrumentación corregida, estabilidad aún no acreditada

Fecha del cliente: 2026-10-18. **No se da por resuelta la inestabilidad.** Se
corrigen defectos del control, pero tres componentes acotados no proporcionan una
ventana válida. Cero S8 nuevos. [Antecedente](RESULTS-V4-17-EFFICIENCY.md).

## Cambios de instrumentación, sin cambios en el plugin

1. Selección previa de CPU por topología real y permisos, excluyendo núcleos
   aparcados/reservados ajenos. Antes se escogía el bit más alto: aquí CPU 11,
   clase 0, aparcada en una observación. La regla determinista escoge CPU 2,
   clase 1, del último núcleo físico disponible de mayor clase; no prueba CPUs
   hasta encontrar tiempos favorables. La clase se interpreta según
   [CPU Sets de Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-system_cpu_set_information).
2. Trabajo de 30.000 elementos por muestra, idéntico en ambos modos, tres veces
   el componente previo de 10.000. Reduce el peso del reloj y arranque de thread;
   no cambia los umbrales de 5 %, sobrecoste, salida ni el caso/denominador S8.
   El calentamiento hace el mismo trabajo y exige tres últimas muestras CPU/pared
   con dispersión ≤5 %. Si no lo consigue, no arranca variantes. Conserva GC natural
   y mide su colección inicial; no traslada cambios de GC al recorrido de negocio.
3. Opción explícita para el job propio: Above Normal para su árbol y HighQoS
   verificado del worker suspendido antes del arranque. Evita la inferencia de
   primer/segundo plano descrita por
   [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation).
   No es prioridad High/Realtime ni un plan de energía global. El valor por defecto
   anterior permanece. Las futuras ramas A/B deben declarar la misma política.
4. Certificado previo de fuente, esquemas, input, método y contabilidad; rechazo
   ante cambios, caducidad, aislamiento, calentamiento o muestras inválidos. El
   control devuelve la causa de calentamiento sin presentar cero muestras como éxito.

## Resultados conservados

| Componente | Tiempo del job | Resultado |
|---|---:|---|
| CPU 2; trabajo original; cuatro warmups | 20,463 s | Sobrecoste numérico dentro del límite; dispersión no válida. |
| 30.000 elementos; calentamiento condicionado | 31,904 s | No llega a estabilidad; cero muestras de variantes. |
| Igual trabajo y calentamiento, más política explícita del job | 36,852 s | No llega a estabilidad; cero muestras de variantes. |

En la última serie el mismo trabajo tarda **3,460–7,268 s**. Prioridad, HighQoS, afinidad,
contabilidad e identidad del worker se comprobaron; eso no demuestra la causa de
la variación restante. No se diagnostica temperatura, batería o frecuencia sin
mediciones de esas variables. La CPU elegida antes era un defecto, no una causa
suficiente demostrada. Pausar dos procesos tampoco acredita reposo del equipo.

La cota de calentamiento de 30 s se comprobaba entre muestras completas: la última
muestra pudo sobrepasarla; la última serie duró 36,852 s. Se conserva este límite
real, sin reescribir la preinscripción. El timeout duro total de 90 s no se alcanzó.
No hubo variantes en las dos series rechazadas durante calentamiento ni reintentos
automáticos. Se detuvo una consulta opcional propia a contadores WMI que no respondió;
no se reutiliza en el camino medido.

**11 métodos focales pasan**: 7 del control, 2 de topología y 2 nativos de job,
validación y descendientes. El test nativo comprueba modo predeterminado y modo
explícito, prioridad del descendiente y conservación de afinidad del controlador.
No se repiten suites del plugin ni sus recorridos completos por estos cambios de
harness. Vite 57660 y renderer Docker 58232 se pausaron temporalmente con autorización
persistente y se reanudaron por sus handles originales en las tres operaciones,
con estado 0; los recibos quedan conservados. El backend Docker y otros trabajos
no se dieron por detenidos. No hay procesos de estas pruebas en ejecución.

## Condición para continuar

Hace falta una sesión exclusiva con Docker completo y los demás trabajos cerrados,
o un equipo/runner dedicado que el usuario identifique. Se ha solicitado esa
información; no se exploran otras máquinas ni se detienen nuevos servicios.
Después de ese cambio externo: preparar un certificado nuevo, un único control
acotado con el mismo input y umbrales y conservar todos los resultados. Si no pasa,
no iniciar S8 ni encadenar repeticiones. El calentamiento nunca se resta del
recorrido S8 ni elimina arranques en frío de las operaciones públicas.

AC-40 y la estabilidad siguen pendientes. AC-43 conserva el rechazo anterior;
estas mediciones no son aceptación integral ni invalidan los cuatro S8 históricos.
Las seis mejoras, 23 tareas, 44 criterios y presupuestos no cambian: 50/50 plazas
conocidas/reservadas, cero S8 libres y dos H2 protegidas. Otra serie S8 necesitará
cuatro plazas y la candidata exacta, separadamente. Windows/H2 quedan pendientes;
sin instalación, publicación, commit o push. Tokens facturados y de host: null.

Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17\performance\efficiency-correction\stability-resolution`.
Cada componente conserva preregistro, fuente del helper, datos brutos, verdict y
pause-recovery. `completion.json` resume duraciones y estado. La configuración del
plugin, sus fuentes canónicas y los paquetes medidos anteriores no se modifican.
