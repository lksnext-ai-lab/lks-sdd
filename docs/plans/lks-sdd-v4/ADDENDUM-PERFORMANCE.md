# Complemento de rendimiento — plan 0.4

Fecha: 2026-10-16. Revisión del complemento: 0.2. Estado: **V4-02A/B verificadas en alcance preparatorio; incidencia real inconclusa**.
La revisión crítica mantiene las cuatro tareas, las seis mejoras y los techos.
El usuario autoriza después V4-02A/B; no autoriza implementar el plugin, instalar
ni operar sobre el consumidor del equipo. [Resultados](RESULTS-V4-02AB.md).
Decisión posterior: mejora temporal S8 ≥20 % frente a 3.4.3, en [S8-PROTOCOL](S8-PROTOCOL.md).
Sustituye los máximos absolutos de latencia de producto pendientes; cortes intactos.

## 1. Referencia y alcance conservados

R1→V4-02A; R2→V4-17A; R3→V4-02B; R4→V4-07A. Se conservan sus IDs y los anteriores.
V4-02/AC-33 permanecen cerrados en alcance técnico Codex. El protocolo 1.0,
SCENARIOS.json y los registros originales de referencia/cierre conservan sus bytes.
S8 es suplementario: no sustituye S1–S7, no entra en sus medianas y no altera H2,
E1/E2/E3 ni E4. E5/AC-36 siguen diferidos a uso real; no se piden cronómetros humanos.

La revisión 0.3 completa se conserva en
[plan-before-0.4.zip](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/plan-0.4-20261016/plan-before-0.4.zip>),
SHA-256 `c131a337bb5faed63ef2d613a7e708efdcb23332b5e3e0c0fc590137ec7ccf59`.
Los hallazgos y sus correcciones se detallan en [REVIEW-0.3.md](REVIEW-0.3.md).
Los manifiestos de revisiones anteriores prueban aquellas revisiones, no la actual.

| Comparación | Finalidad y límite |
|---|---|
| 3.4.2→3.4.3 en V4-02A | Diagnóstico acotado del mecanismo comunicado. No es ahorro de 4.0 ni resolución demostrada del consumidor real. |
| 3.4.3→4.0 en S8 | Equivalencia y mejora temporal completa ≥20 % del caso, según decisión posterior. Ensayo temprano y aceptación final separados; no se mezclan muestras de candidatas diferentes. |
| Candidata previa→variante M6 | Solo acredita utilidad con las seis parejas y demás reglas del protocolo 1.0. Sin reserva completa, no se inicia ni se rebaja su exigencia. |

## 2. Dependencias sin bloqueo general ni aceptación tardía

V4-03 vuelve a depender de V4-02. Presentación, captura y preparación pueden
avanzar cuando estén autorizadas, sin esperar al diagnóstico complementario.
V4-02A→V4-02B condicionan el trabajo que sí necesita S8: el ensayo temprano de
V4-06, el contrato de actividad de V4-07A y las variantes de cálculo que lo usan.
Los parámetros S8 se fijan antes de medir cualquier candidata en ese caso o diseñar
una optimización basada en sus tiempos. Observar H2/S1 no autoriza ajustar S8 al
resultado deseado. Los umbrales de H2 ya están congelados en el protocolo 1.0.

V4-06 incorpora una pareja temprana completa de S8 sobre referencia/prototipo,
antes de escalar o empaquetar la solución. Detecta bloqueos gruesos y pérdida de
obligaciones; no acredita la latencia final ni la actividad que todavía no exista.
V4-15 consolida sus regresiones focales sin imponer otra repetición completa.
V4-17A ejecuta dos parejas finales AB/BA sobre el paquete exacto de V4-16.
Ninguna tarea anterior espera a V4-17A: no hay dependencia circular.

## 3. Fixture representativo y diagnóstico acotado

V4-02A reutiliza herramientas existentes y produce como máximo dos tamaños:
uno mínimo que activa la ruta heredada y uno objetivo con 35 tecnologías.
Ambos conservan los rasgos causales: originales v2 recuperables y decisiones
posteriores, reglas compartidas/globales, prosa incierta y dependencias.
No se construye una matriz cartesiana ni una copia del proyecto privado.

El tamaño objetivo usa método 3.1.0/formato 3.1, propuesta/plan, asignación y
autorización actuales y tarea en backlog; la historia cerrada no concede permiso
nuevo. Mantener inventario esperado independiente del selector y ficha de rasgos
representados/simplificados/ausentes. Las 769 fuentes y 7.499.762 caracteres del
reporte son contexto seleccionado, no el tamaño obligatorio del modelo. No rellenar
el grafo con elementos desconectados para aparentar representatividad.

El diagnóstico permite hasta cuatro invocaciones frías de componente —dos tamaños
por dos versiones—, hasta 120 s por invocación, y un perfil de hasta 30 s separado,
todo dentro del cupo de V4-02A. Son cortes de estudio, no SLA ni latencia aceptable.
Conservar timeout como ejecución incompleta y límite inferior del coste observado;
no utilizarlo como tiempo de terminación ni repetir 3.4.2 hasta conseguir resultado.
No ampliar a tareas completas durante este diagnóstico sin una reserva explícita.

Separar dos estados: validez/representatividad del fixture y resolución del incidente.
AC-38 exige fixture válido y rasgos esenciales acreditados. Falta de fixture válido
no permite cerrar V4-02A como verificada. El diagnóstico AC-37 puede ser inconcluso
con ese fixture válido; no convierte en superada la resolución del incidente.
La limitación del consumidor exacto seguirá visible incluso si el sintético mejora.

## 4. Contrato previo de latencia y actividad

V4-02B concreta [S8-PROTOCOL.md](S8-PROTOCOL.md) y su registro JSON antes de
candidata. El usuario considera suficiente ≥20 % de mejora del tiempo técnico
completo frente a 3.4.3. La decisión posterior sustituye el máximo absoluto de
producto pendiente en 0.4; no cambia E1/E2/E3/E4, cortes ni garantías.

Consulta y transiciones siguen medidas por hitos equivalentes; no reciben un SLA
absoluto adicional. Memoria: ≤512 MiB de pico comprometido del Job Object y
≤1,10×referencia comparable. Actividad: primera señal ≤1 s, intervalo ≤2 s,
≤1 evento/s, ≤1.024 B/evento y ≤16.384 B/intento. Interrupción cooperativa:
reconocimiento ≤2 s, punto seguro ≤5 s en fases CPU declaradas; límites de E/S
explícitos. Sobrecoste opt-in de tiempo/CPU ≤máximo de 0,10 s y 5 % de la fase
equivalente. Valores técnicos elegidos antes de candidata; aún no verificados.

Mantener cortes de 120 s por componente y 600 s por intento completo; no son SLA.
Una referencia no terminal o indisponible no proporciona denominador del 20 %.
El contrato queda congelado y AC-39 preparatorio verificado tras observar la
preparación pública 3.4.3. El recorrido completo y la candidata quedan pendientes;
no condicionan circularmente este cierre. M1/H2 independiente no queda bloqueado.
El protocolo S8 conserva el mapa de entradas, efectos, guardas y comandos A/B;
no elimina trabajo necesario de A ni impone consultas redundantes a B.

## 5. Actividad e interrupción con alcance realizable

V4-07A empieza con puntos de fase/cálculo comprobables y la recuperación existente.
El canal es optativo y compatible; stdout JSON conserva su contrato. Las señales
no escriben estado canónico, no transportan el grafo completo y se cuentan en bytes,
CPU y tiempo cuando se emiten o entregan al agente. Se ensayan canal cerrado y
salida no interactiva; el fallo del canal no debe alterar decisiones ni simular éxito.

La interrupción es del proceso, nunca el comando de negocio `cancel`. En consultas,
no hay escritura contractual. En preparación/aplicación, distinguir paquete externo,
objetos inmutables, journal y efectos ya aplicados: no prometer ausencia total de
archivos ni atomicidad que el almacenamiento no ofrece. Reintentar/recuperar exige
las fuentes actuales y no sobrescribe trabajo posterior. No añadir un nuevo motor
transaccional ni un servicio residente para cumplir esta tarea.

La cadencia y reacción se garantizan solo en las fases/superficies declaradas y
ensayadas. Una operación nativa no interrumpible puede impedir una respuesta inmediata;
ese límite se comunica y su aceptación permanece pendiente si contradice la necesidad
operativa. No fingir actividad de negocio mediante un contador que avanza solo por reloj.
El harness puede cortar un ensayo sintético conservando su recuperación; eso no prueba
una cancelación cooperativa en todos los hosts ni autoriza cortar procesos ajenos.

## 6. S8 completo, comparación y regla de fallo

Recorrido: preparación/start → implementación sintética y prueba real → evidencia
→ verificación → cierre → integración nativa. La aceptación funcional real,
publicación remota y Docker permanecen fuera. La integración no se incorpora
implícitamente a una operación de cierre. A y B parten de restauraciones equivalentes,
con obligaciones y decisiones completas, y conservan los resultados por etapa.

La pareja temprana AB de V4-06 descubre defectos antes del paquete final. Las dos
parejas finales de V4-17A son AB y BA: cuatro ejecuciones, procesos nuevos y caso
restaurado. Controlan el orden sin afirmar estabilidad estadística ni un p95 poblacional.
No se reutiliza por defecto el prototipo como candidata final. Una reutilización
excepcional exige misma revisión/paquete/fixture/configuración, protocolo comparable
y justificación; las reservas no se liberan anticipadamente por esperarla.

AC-43 exige mejora temporal mediana ≥20 % en dos parejas válidas, ambas con
reducción positiva, y límites de memoria/actividad; reglas completas en S8-PROTOCOL.
Un timeout, error o resultado incompleto nunca pasa por comparación relativa. Lentitud, timeout,
fallo propio o rechazo correcto no se eliminan como ruido. Solo las causas externas
predefinidas en el protocolo 1.0 invalidan una muestra, con coste/motivo conservados.
La reposición necesita reserva de contingencia; un fallo claro no se repite hasta éxito.
Corregir código crea una revisión nueva y obliga a repetir la evidencia afectada.

Tiempo de aceptación sin perfilador; instrumentación interna en pasada separada.
Conservar CPU/memoria disponibles y su método, transporte/entradas, consultas,
reintentos, prueba y diagnóstico. Contar evaluaciones internas además de llamadas.
La actividad añadida de B es coste propio; no exigir una capacidad inexistente a A.
Un resultado correcto sin alcanzar la aceptación S8 no acredita resolución. E4 no sustituye
AC-43, y descartar una variante M6 no resuelve un bloqueo operativo confirmado.

Adversos: originales modificados/ausentes, autoridad revocada, política/rama/base
cambiadas, evidencia inválida e interrupción. Se asignan a V4-06/07A/14/15 y se
referencian una vez en AC-44; no lanzar otro recorrido completo por cada adverso.
La matriz debe señalar prueba, revisión, garantía y dueño, sin duplicar código o coste.

## 7. Presupuesto de ejecuciones: compromiso base y contingencia

Techos intactos: **48 intentos completos, 8 h humanas, 12 h de entorno; M6 hasta
2 variantes y 4 h dentro de los globales**. No se reinicia el consumo ni se reserva
otra sesión humana. El saldo real de las tres dimensiones sigue sin certificar.

| Cargo conocido o reserva | Ejecuciones |
|---|---:|
| Histórico conservador documentado | 7 |
| H2 | 2 |
| S1–S6 finales de Codex/Copilot | 24 |
| S8 temprano en V4-06 | 2 |
| S8 final AB/BA en V4-17A | 4 |
| Contingencia protegida de fallos/repeticiones | 4 |
| Total conocido y reservado | 43 |
| Margen teórico no asignado, antes de otros consumos | 5 |

La contingencia no son cuatro pruebas obligatorias ni una ampliación del tope.
La unidad es el intento de caso funcional completo del estudio, termine o falle;
una consulta/prueba de estado aislada no es otro caso. Si un runner ejecuta un caso
completo del estudio, consume su plaza aunque se llame regresión. No dividir un
recorrido ni cambiar su etiqueta para eludir el tope; clasificar antes de ejecutarlo.
Los cargos dudosos se imputan conservadoramente, sin descontar históricos.

Una serie M6 de doce tareas adicionales llevaría esta reserva a **55**, superior a
48. Por ello **no forma parte del compromiso base**. M6 conserva perfil/disposición
sin cambios y hasta dos variantes solo si existe reserva real completa de ejecuciones,
horas y contingencia antes de incorporarlas. No rebajar seis pares ni consumir la
cobertura obligatoria para aceptar una optimización. Las reservas sobrantes solo se
liberan tras cumplir su finalidad; no presumir reutilización para hacer cuadrar cifras.

## 8. Horas: cotas de trabajo, no promesa de finalización

El registro local numérico de 19 turnos cerrados suma **16.016,14 s = 4,4489 h**,
hasta 2026-10-16T08:31:48.998Z. Usa el mismo proxy de asignación histórico: duración
de turnos, incluyendo planificación; no es CPU, atención humana ni horas exactas
de máquinas. Excluye esta revisión abierta y no certifica trabajo fuera del registro.
La diferencia aritmética con 12 h, **7,5511 h**, no es saldo disponible.
La evidencia está en
[budget-observation.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/plan-0.4-20261016/budget-observation.json>).

Se fijan cotas iniciales para evitar investigación indefinida; incluyen preparación,
edición/instrumentación autorizadas, comprobación, limpieza segura e informe del bloque.
Son límites para parar, no estimaciones que demuestren que el trabajo terminará.

| Bloque añadido | Cota inicial de entorno | Qué sucede si no termina |
|---|---:|---|
| V4-02A | 45 min | Diagnóstico inconcluso; fixture inválido queda pendiente. No repetir campañas 3.4.2. |
| V4-02B | 15 min | Contrato de aceptación pendiente; afecta a S8/07A/M6, no al trabajo independiente M1. |
| V4-07A | 60 min | Limitarse al diseño mínimo previsto; si no satisface contrato, tarea pendiente, sin aceptar garantías reducidas. |
| S8 temprano y V4-17A final | 120 min conjuntos | Conservar muestras y fallo/inconcluso. Seis intentos a 600 s consumirían hasta 60 min; resto para preparación, recuperación, adversos focales e informe. |
| Total inicial de las cuatro tareas | 240 min = 4 h | Dentro de 12 h, nunca adicionales. |

El diagnóstico de cálculo V4-02A y perfiles/variantes posteriores cuentan también
contra las 4 h M6; la coincidencia entre las cuatro horas de esta tabla y el techo
M6 no crea dos bolsas nuevas ni implica que todas las tareas sean M6. Reutilizar
la misma evidencia una vez y registrar las dimensiones a las que carga cada bloque.
No desplazar preparación, diseño o reparación fuera de la cuenta para aparentar saldo.

Antes de un bloque, el ledger registra consumido observado o cota acreditada,
reserva del bloque, del resto obligatorio y de recuperación, por cada dimensión.
Condición de admisión: `consumido + reservas_obligatorias + bloque + recuperación
<= techo`, sin doble contabilizar reservas. Capacidad desconocida queda como
`viabilidad_no_acreditada`, no como cero. No basta que cada bloque aislado sea menor
que 12 h. Las cotas pueden reasignarse dentro del saldo y el alcance existente antes
de ejecutar, conservando la historia; jamás aumentan los techos ni convierten fallo en éxito.

La cobertura Windows reutilizada reserva además **30 min** en V4-14/15/16, dentro
del techo existente. No se agrega a las cuatro tareas ni modifica el gate estable.
Incluso tomando solo el proxy conocido, 4,4489 h + 4 h + 0,5 h dejan **3,0511 h**
para el resto del plan, esta revisión y costes no cubiertos. No hay una estimación
verificada que demuestre que todo cabe. El tiempo humano histórico no se pudo acotar;
se conserva desconocido, sin nueva petición de cronometraje ni afirmación de cumplir
las 8 h acumuladas. Las decisiones funcionales necesarias no se eliminan por ello.

**Dictamen:** encaje estructural y de plazas del compromiso base comprobado;
viabilidad integral de horas **no acreditada**. La ejecución futura exige reserva
real del bloque y resto obligatorio; ante insuficiencia se detiene con pendientes.
La autorización futura no inventa capacidad. No se elimina ninguna de las cuatro
tareas ni se declara la release aceptada para salvar el presupuesto.

## 9. Estados y compatibilidad

Estado posterior: AC-37/38/39 `passed` en alcance preparatorio; incidente real
inconcluso. AC-40–AC-44 `not-run`. V4-02A/B `verified` con límites visibles;
V4-07A/17A `planned`. Ver v4-02ab-progress.json y RESULTS-V4-02AB.md.
V4-14/16 verifican ambos adaptadores; V4-17 mantiene Codex primero y Copilot al final.
S8 es técnico, no un piloto conversacional adicional ni medición humana. Una eventual
release con reservas requiere decisión explícita y mantiene los fallos visibles.
No se cambia el gate estable ni se crea telemetría recurrente o infraestructura nueva.

## 10. Windows y temporales largos: regresión obligatoria

Petición adicional del usuario: evitar arrastrar o reintroducir el problema conocido
con temporales largos de Windows. La fuente actual contiene `path_utils`,
`import_bootstrap` y `tests/test_windows_long_paths.py`; el gate estable ya exige
esa regresión. Son mecanismos/cobertura existentes, no evidencia de que la futura
4.0 haya pasado. No se atribuye la lentitud del ZIP a rutas sin demostrarlo.

| Frontera | Responsable y cobertura |
|---|---|
| Fixture y medición S8 | V4-02A/02B registran raíces/longitudes y mantienen condiciones A/B equivalentes; raíz explícita y nombres acotados. No multiplicar rendimiento por cada ruta. |
| Captura/exportación/temporales | V4-04 reutiliza helpers existentes, evita copias anidadas y crecimiento de nombres por reintento; conserva destinos y ciclo de vida explícitos. |
| Interrupción/recuperación | V4-07A conserva evidencia/efectos parciales; limpieza solo del área propia verificada, sin archivos ajenos ni cambios posteriores perdidos. |
| Compatibilidad y regresión | V4-14 propietaria y V4-15 consolidación: ruta corta y >260 caracteres, TEMP/TMP profundo, espacios/Unicode, consulta, captura, aplicación y recuperación en Windows real. |
| Distribución y aceptación | V4-16 comprueba helpers/recursos y extracciones completas de ambos paquetes; V4-17A referencia evidencia vigente del núcleo exacto sin repetir todas las tareas. |

Diseño futuro: distinguir ruta física extendida de identidad lógica; conservar hashes,
rechazo de escapes/enlaces y guardas actuales. No resolverlo deshabilitando integridad,
aceptando extracción parcial o exigiendo cambios globales del equipo. Registrar
limitaciones reales de Python/volumen/soporte 8.3; no prometer compatibilidad ilimitada.
La ruta corta controlada reduce problemas operativos, pero no sustituye la prueba larga.
Reutilizar áreas de ensayo pertinentes conforme a política; ninguna se crea o limpia
por esta revisión. La limpieza futura verifica ruta absoluta y propiedad antes de retirar.

Las aserciones deben comprobar igual contrato/resultado, recursos completos, captura
recuperable, reintentos sin crecimiento de rutas y conservación de archivos ajenos.
Un skip por sistema operativo, fallo de importación o prueba limitada a ruta corta
deja la cobertura larga pendiente. Ejecutar las regresiones focales necesarias una vez
por revisión afectada; el gate oficial mantiene sus propios checks/timeouts.

Se reserva una cota inicial conjunta de 30 min para desarrollo/validación de esta
cobertura en V4-14/15/16, dentro de 12 h, con reutilización justificada de evidencia.
Es una condición de parada del estudio, no estimación ni permiso para recortar el gate.
Si no basta, conservar el pendiente y revisar capacidad; no declarar compatibilidad.
No cambia 43 plazas reservadas por añadir una campaña completa: las comprobaciones
focales consumen horas y cualquier tarea completa adicional también consume intento.
