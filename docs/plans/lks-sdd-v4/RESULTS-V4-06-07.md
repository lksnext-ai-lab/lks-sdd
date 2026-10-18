# V4-06: optimizaciones y continuidad V4-07 — resultados

Fecha: 2026-10-17. **Garantías técnicas comprobadas; mejora integral de rendimiento
todavía no acreditada. Windows y H2 siguen pendientes.** No es la release 4.0 completa.

## Implementación

- V4-06 reutiliza confirmaciones heredadas por unidad dentro de una evaluación
  inmutable, con presupuesto acotado y copias independientes de sus resultados.
  La tabla compartida evita expulsiones repetidas en proyectos de más de 256 unidades.
- Las observaciones Git locales se reutilizan solo durante una preparación.
  Fetch, referencias compartidas, otros repositorios, hilos y tareas asíncronas
  conservan sus lecturas propias. La caché se vacía antes de las guardas físicas.
- Se elimina una comprobación envolvente redundante anterior a cada preparación:
  el escritor nativo sigue leyendo el estado actual, se revalida físicamente
  después de preparar y `current=True` sigue comprobando cada aplicación.
  Se mantienen la frontera inicial y la comprobación final.
- La evaluación rechaza cambios de hashes ya observados, también sin cambio de
  revisión del modelo. Ampliar la huella con fuentes nuevas sigue permitido.
- La correlación técnica copia solo las dos estructuras que modifica, sin
  duplicar los cuerpos/objetos preparados para añadir el identificador del journal.
- V4-07 añade `continuity` dentro de `work-prepare`: estado y fuentes de las tareas
  seleccionadas, operador aportado, paradas, siguiente acción y referencias al
  contrato literal/intervenciones. Se proyecta de los resultados ya comprobados,
  sin nuevas consultas, checkpoints ni escrituras canónicas. El propietario nunca
  se adopta como operador. Un bloqueo de frescura produce vista no disponible.

## Comprobación

V4-06: **90 métodos únicos superados**: 30 de composición/recuperación (17 subcasos),
28 de preparación, 10 de reutilización/inmutabilidad, 6 de aislamiento Git,
14 de humo, 1 Windows largo real y 1 de confirmaciones heredadas. Integridad
estática superada. Es evidencia de desarrollo; no aprobación ni publicación.

V4-07: **7 comprobaciones nuevas superadas**, incluido proceso público nuevo sin
historia del chat, identidad ausente/desconocida, cambio de base, bloqueo físico,
solo lectura y recuperación de pausa. Se comprueba por AST que la preparación
anterior conserva su código y solo añade la proyección; se reutilizan expresamente
sus 28 casos previos. Los componentes técnicos se repitieron y pasaron.

El intento adicional de repetir los 28 casos tras V4-07 agotó 1.200 s: **no se
declara superado**. El primer runner de continuidad también descubría por error
la clase importada de preparación (28 casos adicionales); se canceló y se corrigió
el descubrimiento para seleccionar exactamente los siete casos nuevos. Se conservan
los intentos y resultados parciales; no se suman casos duplicados como cobertura.

Los escritores de V4-06 siguen idénticos a la tanda de 90 casos. Permanecen intactos
los contratos canónicos, esquemas y seis skills respecto al inicio del trabajo.

## Rendimiento y recuperación

La candidata pasó sus controles funcionales en los dos recorridos BA, pero ambas
ventanas detectaron nuevos procesos Python de otros proyectos. Se conservan como
**muestras inválidas por concurrencia**, sin calcular ahorro ni sustituir la pareja
adversa anterior. No se afirma corregida la regresión integral ni un ahorro de tokens.
El perfil focal distingue preparación, comprobación del runtime y captura diagnóstica;
esta última sigue siendo un coste material. Los perfiles no son aceptación de S8.

Ambos Jobs terminaron sin hijos activos ni transacción pendiente. No se detuvo
trabajo ajeno, reparó Windows, cargó un host, instaló, publicó, hizo push o creó commits.
Las dos plazas de contingencia restantes se consumieron: quedan 15 ejecuciones
conocidas + 30 reservadas = 45/48; no se certifican plazas históricas adicionales.
Las cuatro S8 finales, H2 y cobertura real de Copilot se mantienen pendientes.

Se conservan las seis mejoras del plan y los 44 criterios, sin declararlos todos implementados.
V4-07A y las tareas posteriores no se presentan como implementadas. La continuación
requiere conservar una ventana comparable para rendimiento y respetar los límites
de ejecución; no se comprometen más casos ni horas automáticamente.

Evidencia compacta: `closure-result.json`, `verification-result.json`,
`continuity-final.json` y `paired-final/results.json` en `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-06\correction`.
