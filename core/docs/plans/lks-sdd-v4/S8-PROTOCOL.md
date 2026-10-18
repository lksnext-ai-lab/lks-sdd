**Decisión posterior vigente (2026-10-18):** se acepta variabilidad de cargas y se retira la exigencia de estabilidad previa; [alcance y reglas](DECISION-SHARED-HOST-MEASUREMENT.md). Los datos y conclusiones históricos de este documento se conservan.

# S8 — Contrato de aceptación técnica 1.0

Fecha: 2026-10-16. Propietaria: V4-02B. Especificado antes de cualquier candidata 4.0;
referencia pública de preparación observada; recorrido completo futuro pendiente. [Registro numérico](S8-PROTOCOL.json).

## 1. Decisión posterior del usuario y efecto

Ante la pregunta sobre esperas aceptables de consulta/recorrido, el usuario responde:
«con ue haya una mejora de al menos el 20% es suficiente».

Se aplica **al menos 20 % de reducción del tiempo técnico completo de S8 frente a
3.4.3 correctamente utilizada**. Consulta y transiciones se informan por separado.
Esta interpretación se declara antes de candidata: no exige otra aprobación para
registrar la decisión ya recibida. No extiende el 20 % a transporte, llamadas,
tokens, M6 ni percepción humana, que conservan sus reglas originales.

La decisión sustituye los máximos absolutos de latencia de producto pendientes en
AC-39/43 del plan 0.4. No se impone un SLA adicional de 30 s o cinco minutos. Los
cortes de 120 s por componente y 600 s por intento completo siguen controlando
recursos; un timeout no pasa por mejorar una referencia más lenta. Si la referencia
no termina dentro del corte, no hay denominador comparable ni aceptación demostrada.

## 2. Unidades, orden y calidad

Referencia: runtime 3.4.3 del commit `bf4d059c98826039097d606121ab6406d762fcc7`,
caso objetivo S8 versionado de 338 elementos y 35 tecnologías. Comparación 3.4.2→3.4.3
solo diagnóstica; nunca denominador de ahorro 4.0.

La pareja temprana AB pertenece a V4-06; V4-17A usa dos parejas finales AB/BA del
paquete exacto, con restauración y procesos nuevos. Calcular por pareja
`r = 1 - T_candidata / T_referencia`; la mediana de ambas debe ser ≥0,20, ambas
reducciones positivas y sin fallo de garantías/resultado. Informar ambos valores,
segundos absolutos y limitación descriptiva de dos parejas. Una pareja no positiva
deja consistencia inconclusa; no se borra ni se repite hasta conseguir éxito.

La ventana técnica va desde la primera operación pública del caso restaurado hasta
la integración nativa final, incluyendo arranques, implementación sintética real,
prueba ejecutada, guardas, evidencia, recuperación y diagnóstico. Excluye inferencia/
esperas humanas. Preparación/restauración W0 y reporte W3 quedan fuera del denominador
de recorrido, conservando su coste total. Ningún intervalo se cuenta dos veces.

| Hito equivalente | Referencia A | Candidata B prevista, todavía inexistente |
|---|---|---|
| Preparar | Runtime doctor, contexto literal y readiness necesarios. | Consultas equivalentes o preparación compuesta; conservar todas sus condiciones. |
| Iniciar | Presentación si procede, preparación start y apply con guardas actuales. | Composición autorizada con los mismos efectos y guardas frescas. |
| Implementar/probar | Escribir app.py y ejecutar la prueba real acordada. | La misma funcionalidad y prueba; incluir ambos costes. |
| Registrar/verificar/cerrar | Operaciones públicas, presentaciones exigidas, paquetes y aplicaciones. | Registro compuesto solo donde el contrato lo permita; eventos y requisitos distintos conservados. |
| Integrar | Operación nativa explícita, base confiable y sus controles. | Misma frontera y autorización; no aceptación humana ni publicación remota implícitas. |

La tabla no fija comandos redundantes a B ni retira pasos necesarios de A. V4-06
concreta las opciones nuevas contra CONTRACT.md antes de ejecutarlas. Se mantienen
evaluaciones internas además de llamadas, fuentes completas y rechazo de datos inválidos.
Una regresión de fase >10 % activa la investigación/disposición del protocolo original.

## 3. Parámetros técnicos previos

| Parámetro | Valor / condición |
|---|---|
| Tiempo completo | Reducción mediana ≥20 %; condiciones de consistencia y E0 anteriores. |
| Consulta/transición | Tiempos visibles por hito; sin máximo absoluto de producto por la decisión posterior. |
| Corte componente / intento | 120 s / 600 s, sin prórroga automática. |
| Memoria | Pico comprometido del Job Object Windows, incluidos descendientes: ≤512 MiB y ≤1,10×referencia por pareja equivalente. Working set separado, muestreo 10 ms. |
| Primera actividad / intervalo | ≤1 s / ≤2 s en fases declaradas. Si finaliza antes de 1 s, basta el resultado final. |
| Frecuencia / evento / total | ≤1 evento/s, ≤1.024 B/evento y ≤16.384 B por intento. Agrupar señales de fases rápidas. |
| Reconocer interrupción / punto seguro | ≤2 s / ≤5 s en fases CPU cooperativas declaradas; límites reales de E/S/escritura se explicitan y prueban. |
| Sobrecoste opt-in | Tiempo y CPU ≤máximo entre 0,10 s y 5 % de la fase equivalente sin señales; bytes de actividad ≤16.384. |

512 MiB es una cota técnica inicial para el caso sintético, no una observación del
pico actual. El límite relativo de memoria explicita crecimiento relevante. Los
parámetros de actividad son decisiones técnicas conservadoras de diseño, no funciones
ya disponibles. Si no pueden verificarse o cumplirse, el criterio queda pendiente;
no se reduce la garantía para cerrar V4-07A.

JSON final, canales compatibles, journal, guardas actuales y archivos ajenos deben
conservarse. Interrupción del proceso no ejecuta `cancel` de negocio. No se promete
aborto instantáneo de E/S no interrumpible ni ausencia total de artefactos técnicos.

## 4. Windows, recursos y estado

Raíz controlada: área S8 de la operación H1. Rutas creadas observadas: 213/216
caracteres máximos, sin anidar copias ni aumentar nombres por reintento. Esto **no
supera la regresión >260 caracteres**, pendiente en V4-14/15/16 para temporales
profundos, espacios/Unicode, captura, interrupción y recuperación. Helpers y controles
de integridad/contención se mantienen; no se cambian ajustes globales de Windows.

Se conservan 48 intentos, 8 h humanas, 12 h de entorno y M6 dos variantes/cuatro
horas dentro de globales. Cero tareas completas iniciadas en este bloque. Cuatro
consultas diagnósticas ejecutadas: tres muestras terminales válidas y un timeout
invalidado por concurrencia sobrevenida. Cota agotada, sin repetición automática.
El saldo global real continúa sin certificar.

El protocolo está congelado y la decisión funcional registrada. AC-39 se verifica
en su alcance preparatorio: instrumentos ejercitados, preparación pública 3.4.3
terminal en 11,04 s y memoria observada de 68,4 MiB. El corte de 600 s permite
observar el recorrido futuro o su fallo; no se afirma todavía que este termine
dentro del corte. AC-42/43 y el ahorro 4.0 permanecen `not-run`. No falta otra
decisión sobre el 20 %. Cambios de producto requieren autorización posterior.
