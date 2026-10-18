# V4-17 / V4-17A — Comparación detenida y disposición

Fecha: 2026-10-17. **No se acepta la eficiencia ni el recorrido final de 4.0**.
Se han ejecutado dos de los cuatro intentos S8 reservados. La regla de parada
detuvo los otros dos al fallar la preparación de la candidata; no hubo reintentos.
Windows y H2 siguen pendientes. No se ha instalado, publicado ni cambiado el plugin.

## Recorrido S8 final

Fuente de candidata: `working-tree:5f489951930534a51097c7d83e36c455aa91c7074d5edf2b68c96871ae291db2`.
Runtime del paquete final V4-16: `26334075bc388308823bd63350a098b1a3a5ff722c14ce02bcead6d32d4b4c53`.
Referencia: commit 3.4.3 `bf4d059c98826039097d606121ab6406d762fcc7`.
Cuatro restauraciones independientes, mismo caso de 338 elementos/35 tecnologías,
originales y base confiable, TEMP/TMP de 299 caracteres; ninguna aprobación editada.
El protocolo y las huellas se fijaron antes de ejecutar; orden AB/BA, cortes de
120 s por componente y 600 s por intento. El bloque fijó 55 min incluyendo cierre;
no certifica un nuevo saldo global de horas ni amplía las cotas anteriores.

| Intento | Resultado | Tiempo observado | Pico comprometido del job | Validez |
|---|---|---:|---:|---|
| 1 · A, 3.4.3 | Completo: prueba real, cierre, integración sin aceptación y diagnóstico conservado | 92.195 s | 112.53 MiB | Invalidado para comparación por identidades Python no atribuidas durante la ventana |
| 2 · B, candidata | `action-required` en `work-prepare`; recorrido incompleto | 11.490 s hasta detenerse | 94.15 MiB | Aislamiento acreditado; fallo de continuidad conservado |
| 3 · B / 4 · A | No ejecutados tras el fallo claro | — | — | Dos reservas retenidas |

Los tiempos incluyen el coordinador y descendientes mediante Job Object; no hay
perfilador. Se conservaron stdout/stderr, métricas de CPU, fases y procesos.
La huella preregistrada del coordinador corresponde al código con saltos LF;
`coordinator-binding.json` conserva también la huella física CRLF y comprueba la
equivalencia exacta sin modificar el manifiesto ni repetir mediciones.
La ventana A detectó dos identidades no atribuidas; no se excluyen a posteriori ni
se afirma su causa concreta sin atribución. La vigilancia B no detectó conflictos.
**No se comparan 11,490 s de rechazo con 92,195 s de trabajo completo.** No hay
porcentaje de ahorro, cociente de memoria aceptable ni pareja final válida.
La regresión anterior de V4-06 sigue abierta: este intento incompleto no la corrige.

## Hallazgo de compatibilidad

El método/runtime, base coherente, actor, literalidad y observación de adjuntos pasan.
La candidata rechaza autorización, aprobación de plan, proceso de implementación y
revisión de tarea. No inicia trabajo ni crea journal pendiente; `app.py` sigue ausente,
los originales conservan sus hashes y las salidas declaran efectos/escrituras vacíos.

Un diagnóstico posterior **de solo lectura**, sobre ese mismo consumidor intacto,
compara los módulos fijados de ambas revisiones: los descriptores de aprobación de
plan/ejecución pasan de **286 a 322 unidades**. Las decisiones previas no contienen
las **36 añadidas: una propuesta y 35 tecnologías**. No cambia la huella de ninguna
unidad ya registrada. La cobertura actual informa 40 unidades pendientes porque
también deja de acreditar entradas cuyo cierre transitivo ya no está cubierto.
La ausencia de `approval_roots` no explica por sí sola el fallo: el lector mantiene
el fallback de legado; la diferencia demostrada es el cierre ampliado de dependencias.

Esto limita la matriz afirmada en V4-14: su actualización sintética sencilla pasó,
pero **no prueba continuidad de todas las decisiones del caso migrado S8**.
Hay que revisar si la expansión entrante es correcta y exige adopción revisada,
o si incorpora alcance ajeno y requiere corrección compatible. No se relajan guardas
ni se renuevan aprobaciones para producir una medida favorable. La disposición queda
en `compatibility-finding.json`; AC-26 conserva este nuevo pendiente material.

Las obligaciones y la prosa incierta esperadas se comprobaron también sobre la salida
ya conservada del rechazo, sin otra consulta. La captura se inspeccionó y está
`stored`. El canal optativo de esa invocación emitió 7 eventos,
159 bytes, primera señal a 0.371 s y máximo
intervalo de 1.517 s. Es cobertura parcial del canal,
**no** medición on/off ni aceptación del sobrecoste AC-40. No hay journal pendiente
en A ni B; se retienen consumidores/capturas como evidencia, sin recuperación que aplicar.

## V4-17: objetivos y evidencia disponible

| Objetivo | Disposición |
|---|---|
| E1, menos salida completa S1/S2/S4 ≥30 % | Sin nueva serie comparable: no aceptado. La reducción estática de instrucciones V4-11 no mide esta unidad. |
| E2, menos administración S1/S2 ≥20 % | No medido: menos llamadas técnicas por sí solo no acredita esfuerzo administrativo. Se conserva la comparación funcional M5 sin duplicar ahorro M2. |
| E3, tokens observados del host ≥15 % | No medido; tokens de host/facturados `null`. No se estiman desde caracteres, bytes, tiempo o CPU. |
| M4, rutas de instrucciones | Se reutilizan las mismas 12 rutas de V4-11: 5,04–11,97 % menos caracteres, alcance exclusivamente estático; aceptación real del host pendiente. |
| E4/M6, optimización de cálculo | Disposición sin variante incorporada de V4-13; no se atribuye un ahorro nuevo a reutilización existente. |
| AC-43, S8 final ≥20 % y memoria/consistencia | No aceptado: cero parejas finales válidas y candidata sin completar. |
| E5/AC-36, percepción/esfuerzo humano | Diferido al uso real sostenido, conforme a decisión del usuario; no se solicita cronometraje. |
| AC-30, uso real de hosts | No ejecutado: H2 y Copilot real pendientes. CLI sintética no acredita comprensión/continuación del agente. |

Se consolidan garantías focales de V4-06/07A/08-11/14-16 por identidad del código,
incluida la cobertura del plugin de rutas largas; no se repiten suites ni señales
nativas. La incidencia de aislamiento de Windows no se ha retomado. No se ejecuta
una campaña adicional S1–S7 ni se consumen reservas H2 para suplirla.
AC-27 queda parcial; AC-28 se acredita solo como informe que distingue unidades y
ausencias; AC-31 documenta disposición sin dar objetivos por logrados. AC-42/43 no
se aceptan y AC-44 conserva evidencia negativa focal con recorrido positivo incompleto.

## Presupuesto y continuación

Se mantienen seis mejoras, 23 tareas, 44 criterios y **48/48 conocidos/reservados**.
Se usan dos slots S8 ya reservados, se retienen dos sin ejecutar y los dos H2.
Cero slots nuevos, reintentos o variantes M6. No se reinicia una serie de cuatro
con solo dos slots disponibles ni se sustituye una revisión a mitad de comparación.

Siguiente decisión técnica: resolver el cierre de descriptores/adopción de decisiones
anteriores y acordar cómo completar cobertura válida dentro de las reservas reales.
V4-18 puede documentar el bloqueo; no puede declarar aceptada 4.0 mientras persista.
Los paquetes V4-16 conservan sus bytes y estos límites; no se promueven a stable.

Registro: [v4-17-progress.json](v4-17-progress.json).
Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17` (`predeclared.json`, `results.json`, salidas por fase,
`approval-diagnosis-A/B.json`, `compatibility-finding.json`, `comparison.json`).
