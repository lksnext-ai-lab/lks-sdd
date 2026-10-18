# V4-17 — Corrección focal de coste y transporte; estabilidad pendiente

Fecha del cliente: 2026-10-18. Coste y duplicación corregidos en fuentes de
desarrollo; **la medición todavía no es estable y no se repite S8**.
Los cuatro S8 anteriores y su rechazo permanecen intactos en
[el resultado anterior](RESULTS-V4-17-PERFORMANCE.md).

## Cambios y garantías

- Captura: reserva de lectura limitada al tamaño observado más un byte; cada
  objeto distinto de material/transporte/paquete se lee y verifica antes de
  devolver cada ventana. Sin caché de confianza entre llamadas. Las referencias
  conflictivas y la corrupción bloquean; los lotes expandidos mantienen sus límites.
- Operational: JSON sin sangría y recibos `completed` de las dos operaciones
  compuestas sin repetir el campo superior `contract`. Mantienen efectos,
  condiciones, escrituras y recuperación. Consultas, previews, bloqueos y parciales
  conservan literales. API/details/output/capture explícitos completos si tienen
  éxito. Antes de trabajo nuevo se exige consultar el contrato vigente; no se
  presupone memoria del host ni se modifica autoridad/frescura/código del consumidor.
- Medición: afinidad opcional de un CPU para el job propio y descendientes antes
  de arrancar, sin modificar afinidad del controlador ni políticas de Windows.
  Control previo independiente que recalcula seis muestras ABBAAB, dispersión
  ≤5 %, sobrecoste CPU y pared ≤max(0,10 s; 5 % de off), trabajo idéntico y 16 KiB.
  Exige certificado previo de fuente/método/input, aislamiento y antigüedad ≤5 min.
  No arranca ni autoriza S8. Una futura campaña debe incorporarlo antes de lanzar;
  el driver histórico y los umbrales no se reescriben.

## Evidencia focal, sin nueva aceptación integral

| Comprobación | Resultado y límite |
|---|---|
| Lecturas físicas de objetos en la misma captura | 1.667 → 367. Perfil instrumentado 4,600 → 1,509 s; diagnóstico, sin atribuir ahorro integral. |
| Igualdad del lector anterior y corregido | Resultado completo idéntico: 7 entradas, 8 observaciones, materiales, transportes, pendientes y presupuestos. |
| Proyección estática de salidas B retenidas | −60,892 % y −60,880 % en bytes; conserva stderr y metadatos históricos, sin simular una nueva observación. |
| Consulta nativa work-prepare desde runtime sintético fijado | 268.216 B frente a 392.191 B retenidos; lista, literales y prosa íntegros; API y stdout exactos recuperables; 338 originales intactos. Es una consulta, no S8. |
| Pruebas focales | 25 CaptureTests + 5 ReceiptTransportTests + 2 MeasurementAffinityTests + 4 ControlTests: 36 métodos comprobados. Solo se repitieron los afectados por correcciones. |
| Integridad estática | Contrato válido, seis skills y 13 fixtures íntegros; no altera la puerta estable ni acredita aceptación de host. |

Se corrigieron dos errores de los propios tests: alias Windows 8.3 en una aserción
y PYTHONPATH relativo en el hijo nativo. La comparación auxiliar corrigió la ruta
de captura antes de poder leerla. No se ocultan los intentos previos ni se cuentan
 como recorridos S8. La captura actual coincide en todos sus campos con el lector
 congelado de la candidata medida. No se ha creado un nuevo paquete de release.

## Estabilidad y recuperación

Se retienen las tres series locales: inicial con calibración distinta, trabajo
igualado y una última con pausa expresamente autorizada de Vite PID 57660 y del
renderer Docker Desktop PID 58232. La pausa de esos procesos no equivale a detener
Docker completo ni a acreditar ausencia de toda carga del equipo.

La última serie mantuvo job/afinidad e aislamiento de Python. Dispersión off/on:
pared **8,54 % / 18,12 %**, CPU **12,06 % / 8,79 %**: las cuatro exceden el 5 %.
Los deltas medianos pared −0,337 s y CPU −0,141 s cumplen el límite numérico en
esa serie, pero no son aceptables con esta dispersión. La serie anterior también
falló sobrecoste y estabilidad. No se seleccionan muestras favorables ni se relajan
umbrales. El control previo rechaza el resultado; su certificado completo fue
registrado después, por lo que tampoco se presenta como preinscrito íntegro.

Ambos procesos se reanudaron mediante sus handles originales, con estado nativo
0 en ambos casos; no se detuvieron servicios ni cambiaron ajustes del sistema.
No hay otra prueba programada. Falta una ventana/control estable antes de volver
a proponer una campaña; la carga observada ahora no invalida retroactivamente
los cuatro S8 anteriores ni prueba su causa.

## Estado y presupuesto

AC-40 sigue no aceptado; AC-43 mantiene el fallo de la candidata anterior y la
corrección actual carece de validación integral. AC-42 de aquella candidata se
conserva por alcance, sin transferir aceptación a nuevos bytes. AC-26 sigue abierto.
Las seis mejoras, 23 tareas y 44 criterios no cambian. Registro conocido/reservado
**50/50**, cero plazas S8 libres, dos H2 protegidas; no se inventa saldo de horas.
Otra serie requerirá cuatro plazas adicionales y una candidata exacta; no se ha
iniciado ni financiado aquí. Windows y H2 siguen pendientes; Copilot, E1/E2/E3 de
host y percepción humana sostenida conservan su estado. Tokens facturados/host:
`null`. Sin instalación, publicación, commit o push.

Evidencia y recuperación en
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17\performance\efficiency-correction`:
`capture-cost.json`, `capture-semantic-equality.json`, `output-replay.json`,
`readonly-result.json`, controles brutos, `quiet-control/pause-recovery.json`,
`pre-s8-record.json`, `pre-s8-check.json` y `focal-completion.json`.
