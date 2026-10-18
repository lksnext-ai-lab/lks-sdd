**Actualización vigente:** [corrección y continuidad V4-06/V4-07](RESULTS-V4-06-07.md). Los resultados siguientes se conservan como antecedentes.

# V4-06 — implementación verificada y regresión de rendimiento abierta

Fecha: 2026-10-17, Europe/Madrid. **Implementación y AC-11/12/13 verificados
técnicamente; rendimiento no aceptado. La versión 4.0 completa sigue en desarrollo.**
La continuación retoma las evidencias guardadas, sin volver a ejecutar los casos.
[Registro comprobable](v4-06-progress.json) y [revisión 0.5](REVISION-0.5.md).

## Resultado implementado

`work-continue/1` inicia o reanuda una tarea cubierta. `work-record-results/1`
registra implementación, evidencias, verificación y cierre técnico hasta el objetivo
solicitado. Cada etapa utiliza los escritores y las guardas existentes y conserva
su hecho y recibo. La agrupación no recibe encargos ajenos, concede aprobaciones,
realiza revisiones independientes, integra, publica ni acepta funcionalmente.
No ejecuta código o pruebas suministrados dentro de JSON.

`work-prepare` entrega la base exacta de cada tarea sin conceder autoridad.
La correlación y las fuentes se vinculan al preview hasheado del journal existente;
no se añaden contratos canónicos, esquemas, estados de negocio o permisos.
Un reintento exacto comprueba hechos durables y no duplica efectos. Una escritura
interrumpida exige recuperación o reversión explícitas con el mecanismo vigente.
El fallo posterior de entrega conserva recibos, efectos y estado parcial.

Se mantienen los comandos individuales y las seis skills. Su adaptación completa
pertenece a V4-11. [Contrato público](../../WORK-OPERATIONS.md).
La fuente conserva el manifiesto 3.4.3; no es una release 4.0 publicada o instalada.

## Verificación y correcciones

| Comprobación sobre la producción congelada | Resultado |
|---|---:|
| Escritura compuesta, autoridad, frescura y recuperación | 29 métodos, 17 subcasos, superados |
| Regresión de consulta de preparación | 28/28 |
| Pruebas de humo técnicas vigentes | 14/14 |
| Rutas largas en Windows real | 1/1, sin omitir |
| Integridad de fixtures y contrato del plugin | Superada |
| Auditoría posterior de fuentes, consumidores y recuperación | Superada |

Los 29 métodos se consolidan con trazabilidad: la ejecución inicial tuvo 27 éxitos
y dos errores del cableado de pruebas de exportación. Se corrigió únicamente el
destino de la inyección, de `v3_cli.write_export` a
`v3_cli_presentation.write_export`; ambos casos pasaron sin cambiar producción.
No se cuentan dos veces. Se conservan el resultado inicial, la corrección y sus
hashes. Las ejecuciones canceladas o fallidas anteriores no se declaran superadas.

Las pruebas descubrieron y permitieron corregir la omisión del módulo en el
paquete de desarrollo; la evolución de fuentes cubierta por recibos; la validación
del hecho real además de su etiqueta; la normalización de raíces cortas Windows;
la conservación de efectos ante fallo de exportación; y la clasificación observable
de preparación/aplicación. Se corrigió también una carrera material: ahora un
cambio de código o documentos durante la preparación detiene la operación **antes
del primer efecto**. No se elimina esa comprobación para ganar velocidad.

AC-11 verifica separación de autoridad, recepción y revisión independiente.
AC-12 cubre reintentos, fallos tras cada efecto, interrupción material en inicio
y las cuatro etapas de resultados, recuperación/reversión y trabajo posterior.
AC-13 cubre prueba Python realmente ejecutada, sujeto exacto, evidencia fallida,
`not-run`, antigua o cambiada y calidad obligatoria sin resultado aplicable.
La procedencia de la evidencia sigue siendo declarada: su hash no autentica al
productor ni acredita por sí solo la ejecución de una prueba.

Los componentes técnicos del gate se comprobaron como desarrollo. No hay aprobación
de versión ni gate de release completo sobre checkout limpio. Tampoco se acredita
la interrupción cooperativa futura de V4-07A, H2 ni aceptación de host.

## S8 temprano: medición válida desfavorable

Referencia A: 3.4.3, commit `bf4d059c98826039097d606121ab6406d762fcc7`, runtime
`3.4.3-12970e71ce69`. Candidata B: runtime `3.4.3-2a484d66440c`, identificado
por bytes. Mismo fixture de 338 elementos/35 tecnologías, originales conservados,
Git independiente, procesos nuevos y TEMP/TMP de 299 caracteres con espacios/Unicode.
El recorrido incluye preparación, inicio, creación de `greeting()` sin parámetros
que devuelve `Hola`, prueba real, evidencia, verificación, cierre, integración
nativa y conservación diagnóstica. La integración no implica aceptación funcional.

| Medida del recorrido completo | A, referencia | B, candidata | Cambio B/A |
|---|---:|---:|---:|
| Tiempo total | 133.231 s | 251.622 s | +88.86 % |
| Pico de memoria comprometida del árbol de procesos | 112.176 MiB | 146.031 MiB | +30.18 % |
| CPU del árbol de procesos | 109.344 s | 219.016 s | +100.30 % |
| Procesos nativos | 258 | 423 | +63.95 % |
| Invocaciones públicas | 12 | 9 | −25,00 % |
| Bytes stdout preparados | 886,919 | 1,645,970 | +85.58 % |
| Bytes de ficheros de entrada | 298,653 | 3,450 | −98,84 % |
| Suma de ambos flujos anteriores | 1,185,572 | 1,649,420 | +39.12 % |

La memoria corresponde al Job de Windows con sus hijos, no al working set del
coordinador. Ambos están bajo 512 MiB, pero B/A = 1,301807 supera el máximo 1,10.
El tiempo empeora y no demuestra la reducción final exigida del 20 %.
Menos llamadas o entrada JSON no equivalen a ahorro de tarea o de tokens.
`billed_tokens` sigue `null`, recepción de host no observada y valoración humana
diferida al uso real sostenido. Es una pareja AB descriptiva, no las dos AB/BA finales.

La primera pareja falló por un error propio del arnés: asumía un `app.py` inicial
que el fixture congelado no contiene. Se conserva completa, sin calcular ahorro.
Se corrigió solo el arnés y se restauraron consumidores desde el mismo snapshot
para la pareja válida. Son **cuatro intentos cargados**, dos previstos y dos de
las cuatro contingencias; quedan dos contingencias. No se cambió el plugin, fixture
ni protocolo entre esas parejas. El inventario conservador queda en 13 intentos
conocidos + 32 reservados = 45/48; no se certifica más margen histórico.

## Revisión crítica y siguiente corrección concreta

Hallazgo **PERF-V4-06-01**, abierto, dentro de M2/M6. Los tiempos guardados localizan
el coste; su desglose no atribuye causalidad de un perfilador:

| Grupo de llamadas | A | B |
|---|---:|---:|
| Preparación documental (context/readiness frente a dos work-prepare) | 13.568 s | 50.684 s |
| Inicio | 14.472 s | 38.301 s |
| Implementación, evidencia, verificación y cierre | 51.465 s | 78.602 s |
| Validación y presentación/integración | 20.798 s | 46.772 s |

La inspección de `run/_fresh` encuentra cuatro comprobaciones completas para una
continuación de una etapa y diez para registrar cuatro etapas, además de las del
núcleo. Los resultados entregan el contrato literal en cuatro comandos candidatos.
Son repeticiones comprobables en código/salidas; falta medir cuánto corresponde a
cada una frente a captura, serialización, carga de modelos, runtime, Git y E/S.
No se afirma que una única causa explique todo el empeoramiento.


Se completó además un único perfil diagnóstico de solo lectura, acotado a 30 s,
sobre `require_current` del consumidor B ya integrado (347 elementos). La llamada
perfilada empleó 1,755 s: comprobar el runtime acumuló 0,827 s y cargar el modelo
0,797 s. El proceso completo, incluido hasheado independiente anterior/posterior,
duró 15,958 s. Sus 2.348 ficheros fuera de Git quedaron idénticos y el Job cerró
sin procesos activos. No es otro recorrido S8 ni una medición de aceptación;
su sobrecoste y estado posterior impiden extrapolarlo al recorrido anterior.
En particular, este perfil no demuestra que repetir la carga explique por sí solo
los 118,391 s adicionales: aún hay que atribuir Git, captura y entrega repetida.
Se conserva `readonly-profile.json`; no se cambió producción ni se repitió el perfil.

La corrección siguiente debe instrumentar esas fases y reutilizar solo cálculos
demostrados redundantes dentro de una fase inmutable. Debe mantener comprobación
física de fuentes, runtime, rama, sujeto, periodos y autoridad antes de aplicar,
descartar la reutilización tras cada escritura y conservar `current=True` del
núcleo. La entrega literal íntegra debe seguir disponible; referencias/hashes no
la sustituyen. Los comandos individuales continúan como alternativa compatible.
No se añade una séptima mejora ni se debilitan garantías para cerrar el porcentaje.

Antes de aceptar esa corrección se repiten las regresiones afectadas, especialmente
cambio durante preparación, revocación, evidencia y recuperación. La aceptación de
eficiencia corresponde después al paquete final exacto en las parejas AB/BA ya
reservadas. La pareja desfavorable permanece visible y no se repite hasta éxito.
AC-42/43 siguen pendientes de aceptación final; AC-43 tiene además este hallazgo
adverso conocido. La cobertura focal de AC-44 no cierra su consolidación integrada.

## Recuperación, alcance y presupuesto

Auditoría de ambos consumidores: solo se añadió `app.py` fuera de las áreas
documentales/técnicas permitidas; no se alteraron sus cuatro ficheros previos.
Todos los bytes de runtime fijados coinciden (631 A, 646 B). No hay transacción
pendiente, procesos activos del Job al salir ni interferencia Python observada.
La captura B está conservada: 7 entradas/8 observaciones, sin pendientes, objetos
no referenciados ni material ausente. Los intentos fallidos tampoco dejan una
transacción pendiente. Los fixtures y sus trazas se conservan como evidencia;
no se hace limpieza global ni se afirma recuperar la incidencia nativa de Windows.

De los 682 ficheros seguidos al inicio, este bloque solo cambió los tres previstos:
`distribution/dual.json`, `docs/VALIDATION.md` y `scripts/v3_cli.py`. Los 7 contratos
canónicos, 31 esquemas y 105 ficheros de skills permanecen iguales al inicio del
bloque. Los cinco ficheros congelados del protocolo coinciden. Los cambios nuevos
y anteriores no seguidos están identificados por el runtime y las evidencias.
Se preservan 23 tareas, seis mejoras, 44 criterios y dependencias sin ciclos.

Conciliación a **2026-10-17 11:25:58 UTC**: 48 turnos cerrados,
52546.994956 s cargados. El bloque anterior consumió 7.519,483 s de los
8.972,488044 s disponibles y dejó **1.453,005044 s (24 min 13 s)** al comienzo
de esta continuación. Se añade únicamente el turno actual, desde
11:13:51 UTC: saldo en esa lectura **725.803 s
(12.10 min)**. Corte efectivo de la continuación:
**2026-10-17T11:38:04.155044+00:00**. La espera entre turnos no consume
presupuesto. El descuento histórico y 42,341 s se aplican una sola vez; no se
reinicia el presupuesto ni se amplía el máximo de 15 h.

La petición posterior solicita continuar con agilidad. Se consolida primero este
resultado ya ejecutado. El saldo financia el cierre, pero no acredita una nueva
corrección de producción con todas sus comprobaciones ni las 14 tareas posteriores.
No se inicia un cambio que no pueda verificarse dentro del máximo. Como referencia
observada, las 28 regresiones de preparación tardaron 803 s y los componentes
técnicos otros 401 s, sin contar la batería focal, corrección y medición. No se
promete terminar la release con los minutos restantes ni se rebajan sus controles.

Windows queda apartado, H2/AC-34 `not-run` y Copilot real pendiente al final.
No se repiten accesos/cargas ni se instala, publica, hace push o crea un commit.
La modificación y pruebas del plugin están realizadas localmente; su rendimiento
y la versión 4.0 completa aún requieren trabajo y presupuesto adicionales.

## Propuesta concreta para continuar sin nuevas paradas por tarea

La solicitud de continuar cubre el desarrollo; no se requiere revalidar cada
decisión técnica ya aprobada. La decisión que falta es ampliar el presupuesto de
entorno: el máximo de 15 h se mantiene vigente. Se propone **un bloque adicional
de hasta 2 h**, exclusivamente para resolver PERF-V4-06-01 dentro de M2/M6:

| Trabajo, incluyendo errores y correcciones | Cota |
|---|---:|
| Atribuir el coste con perfiles focales, sin otra pareja S8 completa | 20 min |
| Corregir una variante de la repetición demostrada, manteniendo controles y alternativa individual | 20 min |
| Regresiones de escritura/recuperación, preparación afectada y componentes técnicos | 65 min |
| Revisar diff, comparar fuentes y documentar efecto y límites | 5 min |
| Recuperación y cierre protegidos | 10 min |
| **Total adicional propuesto** | **120 min** |

Es una cota de ejecución, no una promesa de corrección o de cierre de 4.0. Si no
se obtiene una variante verificada se conserva el resultado adverso y se detiene
el bloque. La reserva de pruebas parte de los 39,5 min observados en la batería
focal, 13,4 min de preparación y 6,7 min de componentes técnicos. Las comprobaciones
independientes pueden concurrir; ninguna se suprime o se declara pasada al cortar.
Se preservan el máximo de dos variantes/cuatro horas de M6, las seis
mejoras, las 48 plazas y la cobertura final. La medición final AB/BA continúa
reservada para el paquete final; no se consume para elegir una muestra favorable.
No incluye Windows/H2, cargas, accesos, instalación o publicación. Las 14 tareas
posteriores siguen sin financiación integral demostrada; no se oculta ese coste
ni se ofrece una fecha de terminación sin una estimación sustentada.
