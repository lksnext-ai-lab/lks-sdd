# H2 — Conciliación temporal y presupuesto 0.3

Fecha: 2026-10-16. Alcance: auditoría de los registros existentes y actualización
del plan; sin instalar, aplicar planes, iniciar H2 o modificar código del plugin.
Sustituye el bloqueo por discrepancia temporal de la preparación 0.2. No sustituye
los resultados históricos originales, que se conservan íntegros.

## Hechos contrastados

El cliente registró el turno afectado entre **16:24:22Z y 19:38:04Z**, con
11.621,611 s de duración. La suma deduplicada de 32 turnos cerrados es
48.383,730 s (**13,439925 h de calendario**). No había un error de suma ni una
conversión de zona horaria que explicase las tres horas.

Windows registra tres entradas/salidas de espera moderna, emparejadas por
ScenarioInstanceIdV2 y BootId. Están enteramente dentro del turno afectado:

| Sesión | Intervalo UTC | Registros de entrada/salida | Reposo profundo descontable |
|---|---|---|---:|
| 136 | 16:27:56,337 – 16:39:57,385 | 275888 / 275911 | 682,886544 s |
| 139 | 16:40:01,255 – 17:26:09,115 | 275923 / 275932 | 2.731,560326 s |
| 141 | 17:26:09,116 – 19:31:39,478 | 275934 / 275962 | 7.489,145174 s |

El evento de ajuste de reloj 275893 cambia la hora en aproximadamente **0,692 ms**;
no explica horas de diferencia. La herramienta devolvió a las 16:39:57Z un proceso
aún abierto tras 705,604 s. Su resultado se recogió a las 19:31:54Z. Esos 705,604 s
eran el tiempo de la primera espera, **no la duración final de la preparación**.
El archivo de planes a las 17:26:16Z demuestra actividad intermedia: no sería
correcto descontar la espera moderna completa ni todo el intervalo entre llamadas.

## Corrección contable limitada

Por sesión se descuenta únicamente el menor de los contadores de residencia
profunda de software y hardware, sin solapamientos y una sola vez. La documentación
de [Microsoft sobre DRIPS](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/prepare-hardware-for-modern-standby)
indica que en ese estado no puede ejecutarse código de CPU. Se usa el mínimo para
conservar como cargo cualquier diferencia entre ambos contadores. El resto del
turno, incluidas actividad entre suspensiones, esperas técnicas, preparación,
análisis, errores y recuperación, permanece cargado.

La inferencia contable es que esos intervalos acreditan indisponibilidad del
entorno local, no trabajo efectivo de ese entorno. No se infiere atención humana,
CPU facturada, coste del modelo o ausencia universal de actividad remota. El
calendario bruto se sigue informando: **no desaparecen tres horas del historial**.
No se buscan otros descuentos históricos ni se cambia el límite de 12 h.

Corrección identificada: **10.903,592044 s = 181,726534 min** de reposo profundo.
El turno afectado conserva un cargo de **718,018956 s = 11,966983 min**. Esto
reemplaza su anterior cargo calendario para la asignación del entorno; no se suma
como otro turno y no se descuenta además el tiempo de la herramienta.

## Presupuesto recalculado

| Cuenta | Valor |
|---|---:|
| Turnos cerrados, calendario bruto | 48.383,730 s / 13,439925 h |
| Indisponibilidad profunda acreditada | −10.903,592044 s / −3,028776 h |
| Asignación del entorno observada, corregida | **37.480,137956 s / 10,411149 h** |
| Reserva conservadora de esta conciliación | **600 s / 10 min** |
| Total conocido con esta reserva | **38.080,137956 s / 10,577816 h** |
| Margen conocido hasta 12 h, tras esa reserva | **5.119,862044 s / 85,331034 min** |
| Reserva propuesta H2 | **2.700 s / 45 min** |
| Margen común posterior a H2 | **2.419,862044 s / 40,331034 min** |

La reserva de esta conciliación empieza a las 19:39:37,614Z y termina como máximo
a las 19:49:37,614Z. Se sustituirá por su duración cerrada real, sin sumar ambas.
El saldo corresponde al registro observado; **no certifica históricos externos
desconocidos** ni se convierten horas humanas desconocidas en cero.

Los 45 minutos de H2 caben en esta cuenta conservadora. Es una reserva de recursos,
sin autorización de carga o ejecución. Mantener 10 min preparación/carga, 10 A,
10 B, 10 recuperación protegida y 5 análisis. Si la preparación no demuestra
aislamiento dentro de su corte, recuperar y no iniciar los casos.

Las seis mejoras y toda la cobertura siguen pendientes donde no haya evidencia.
El resto comparte 40,33 min conocidos, sin mantener en paralelo las antiguas bolsas
de 120/60/30 min como reservas garantizadas. No se promete que implementación
restante, S8 y cobertura real de ambos hosts puedan completarse con ese margen:
su viabilidad integral **sigue sin estar acreditada**. Ningún escenario se elimina
o sustituye para cuadrar las cifras; cada bloque requiere reserva antes de comenzar.

Los intentos no cambian: **9 cargos conocidos + 2 H2 + 24 finales + 2 S8 tempranos
+ 4 S8 finales + 4 contingencias = 45/48**. Las dos H2 ya estaban reservadas.
Se mantienen 8 h humanas, 12 h de entorno y M6 dos variantes/cuatro horas dentro
de los globales. No se solicita cronometraje humano ni ampliación del presupuesto.

## Regla de seguimiento y límites de validación

- Conservar dos cuentas: calendario bruto y asignación del entorno corregida con
  evidencia. Descontar solo residencia profunda acreditada dentro de un turno;
  intervalos dudosos permanecen cargados. Reemplazar reservas por cargos, no sumarlos.
- En H2 y cualquier comparación posterior, una suspensión se trata conforme a las
  reglas de validez del estudio: conservar intento, tiempo bruto y coste; no usar
  esta corrección presupuestaria para mejorar W1/W2 ni el denominador S8.
- Antes de cargar, revalidar planes, destinos vacíos, hashes, cliente y aislamiento.
  La autorización actual sigue siendo de preparación. CLI y prioridad H2 ya están
  validados; no se vuelven a preguntar. La carga exige autorización separada.

Evidencia privada en el área H2 existente: `windows-time-events.json` (XML original),
`time-reconciliation-raw.json` (límites y metadatos del cliente),
`time-reconciliation.json` (cálculo reproducible) y `time-reconciliation-validation.json`.
No se exportan credenciales ni el contenido de las conversaciones del estudio.
