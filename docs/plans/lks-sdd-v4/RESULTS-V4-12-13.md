# V4-12/V4-13 — Perfil y disposición acotada

Fecha: 2026-10-17. V4-12 verificada en alcance diagnóstico local; sus dependencias
de aceptación siguen abiertas. V4-13: `evaluated-no-change`, conforme al corte del
plan. No se incorpora una optimización adicional ni se acredita aceleración.

## Perfil recuperable y límites

Se congeló por SHA-256 el núcleo actual posterior a V4-11 y se proyectó a dos
consumidores sintéticos ya disponibles: pequeño (33 elementos) y objetivo (338).
Runtime fijado: `42d8cd73a568083592b62bdaa852906e0478cd5ef36f095bc7f060216b1f6ff1`.
No se eligió un tercer tamaño: estos dos extremos y los perfiles previos bastan
para priorizar costes sin abrir otra campaña.

Cuatro consultas públicas `work-prepare`, con captura externa, procesos Python
nuevos y orden pequeño sin/con perfil, objetivo con/sin perfil; máximo 120 s por
consulta, sin reintentos. Se guardan entradas, salidas completas, stderr vacío,
pstats, revisión, configuración y vigilancia de identidades de proceso.
Un intérprete nuevo no implica caché de disco fría. La actividad optativa estaba
desactivada: este bloque no vuelve a medir AC-40.

Las cuatro terminaron en `action-required`, conservando íntegro el consumidor y
sin efectos/escrituras de negocio. En cada tamaño coinciden estado, porción,
condiciones y bases de operación entre ejecución instrumentada y ordinaria.
La autoridad, aprobación de plan, proceso y revisión no quedan acreditados con la
procedencia actual; se conserva el rechazo, sin reconstruir aprobaciones antiguas
ni afirmar que se ha perfilado un arranque autorizado o el recorrido S8 completo.
El método/runtime, base coherente, actor, contrato literal y observación de adjuntos
sí pasan sus condiciones. Las cuatro capturas se conservan fuera del consumidor.

Había Python ajenos en **todas** las muestras y aparecieron otros durante las dos
primeras. No se terminaron ni se repitieron muestras hasta conseguir aislamiento.
Los tiempos son indicios de localización del coste bajo ese entorno, sin aceptación
de latencia, ahorro, causalidad entre tamaños ni sobrecoste de instrumentación.

| Entrada del perfil | Pequeño, s | Objetivo, s | Interpretación |
|---|---:|---:|---|
| Importación | 1,118 | 1,089 | Arranque/importación transitiva |
| Integridad de runtime | 5,056 | 12,892 | Tres comprobaciones por consulta |
| Carga del modelo | 0,703 | 1,180 | Lectura/parseo/validación incluidos |
| Evaluación de aprobaciones | 0,183 | 0,922 | 10 / 41 invocaciones |
| Serialización JSON | 0,025 | 0,219 | Cálculo de transporte, no lectura del host |
| Captura diagnóstica con persistencia | 0,900 | 4,711 | Conservación externa |
| Publicación durable de objetos | 0,588 | 3,680 | 30 / 335 publicaciones, dentro de captura |

**Son tiempos inclusivos y se solapan: no se suman ni se convierten en porcentajes
del recorrido.** Los pstats conservan todos los nodos; `phase-analysis.json` extrae
estas entradas sin ejecutar otra consulta. `profile-results.json` conserva además
grupos de tiempo propio disjuntos por archivo/función. Su grupo nativo/residual es
grande: no se atribuye artificialmente a una fase. El acceso nativo a archivos,
atributos y rutas destaca entre las funciones de mayor tiempo propio.

Las duraciones ordinarias observadas fueron 16,547 y 11,822 s, y las instrumentadas
9,427 y 22,348 s. Esa dispersión y la concurrencia impiden inferir ahorro.

## Oportunidades y decisión V4-13

| Prioridad | Oportunidad | Disposición para este bloque y garantías |
|---|---|---|
| 1 | Integridad y recorridos físicos repetidos | No admitida como variante. Hay 12.993 consultas de atributos por perfil; fusionar trabajo exige demostrar la misma frescura, defensa de rutas/enlaces e integridad del pin. No eliminar comprobaciones ni cachear autoridad. |
| 2 | E/S de publicación diagnóstica | No admitida. Agrupación o reutilización de lecturas verificadas exige cubrir fallo, manipulación concurrente y recuperación. Omitir sincronización o posponer evidencia no es una optimización equivalente. |
| 3 | Modelo y evaluación | Sin cambio adicional. Ya existe memo acotada dentro de una evaluación inmutable; una mejora de fase no demuestra los 5 s mínimos del recorrido. |
| 4 | Importación y transporte JSON | Sin cambio adicional. No hay beneficio absoluto suficiente demostrado que justifique una reescritura. |

Se reutilizan los perfiles anteriores de V4-06: la consulta con captura gastó
9,252 s inclusivos en conservación; las fronteras frescas y la carga también
destacaron. El recorrido S8 observado conservó la regresión de tiempo y memoria;
la pareja posterior contaminada no la corrige. Son revisiones anteriores: sirven
de contexto para el ranking, no como baseline exacta de una variante nueva.

El pequeño 3.4.3 histórico tardó un 14,8 % más que 3.4.2 en una sola pareja. Su
núcleo pasó de 556 a 631 archivos, y subieron CPU y memoria pese a mejorar contadores
de cálculo. Arranque, integridad y carga siguen siendo contribuyentes plausibles;
no se reparte causalmente aquel 14,8 % usando estos perfiles de otra revisión.
No se repite la referencia ni se presenta la reutilización ya existente como ahorro M6.

El último registro de intentos conocido y reservado suma **45/48**. Una variante
requiere como mínimo seis pares AB/BA (12 intentos), llevando esa reserva a
**57/48**. Se preservan los cuatro intentos S8 finales y dos H2; no se abre una
variante ni se consumen reservas protegidas. El 55/48 del plan 0.4 es histórico.
Siguen vigentes máximo dos variantes y cuatro horas M6: no crean intentos nuevos.
No se recalcula ni se certifica aquí un saldo global de horas para etapas futuras.

AC-22 queda documentada en alcance diagnóstico; AC-23 verifica la disposición sin
optimización incorporada, no una prueba de mejora. AC-40 y la regresión AC-43 siguen
pendientes. Un descarte opcional no convierte esos pendientes en aceptación.

## Garantías y siguiente paso

Cero cambios de código del plugin, contrato canónico o esquemas en este bloque;
huellas del núcleo idénticas antes/después. Se reutilizan las garantías anteriores
de autoridad, frescura, recibos y recuperación. No hay motivo para repetir suites
de negocio sin cambios de producción. Se revisa el diff y la integridad estática.

Se mantienen las seis mejoras, 23 tareas y 44 criterios. Cero intentos nuevos de
tarea completa y cero variantes M6. No se deducen tokens facturados ni ahorro
integral: ambas mediciones de tokens siguen `null`. Windows y H2 permanecen
pendientes; Copilot/observación de host y percepción humana real siguen fuera de
esta comprobación. Sin instalación, publicación, commit ni push.

Siguiente tarea: V4-14, compatibilidad y actualización recuperable.

Registro: [v4-12-13-progress.json](v4-12-13-progress.json).
Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-12-13`
(`predeclared.json`, `profile-results.json`, `phase-analysis.json`, `disposition.json`
y los cuatro originales; históricos en `v4-06/correction` y `s8/small-cost-review.json`).
