# Revisión crítica del plan de aislamiento H2 0.1

Fecha: 2026-10-16. Dictamen: **aritméticamente encajable, ejecución todavía no
acreditada**. La suma de cotas limita gasto, pero no demuestra que Windows termine
el setup ni que el agente cierre S1 en diez minutos. La revisión vigente es
[H2 0.2](H2-ISOLATION-PLAN.md). No se ejecutan casos o cambios operativos.

| Defecto de 0.1 | Riesgo | Corrección en 0.2 |
|---|---|---|
| Saldo calculado con el turno de preparación todavía abierto. | Reutilizar 7,56 min como si siguieran disponibles y no cargar esta revisión. | Sustituir por 36 turnos cerrados; reservar este turno completo y un margen adicional global. |
| Comprobar sandbox antes de cargar/autenticar y ajustar instrucciones. | Las operaciones posteriores cambian configuración/árboles ya comprobados. | Cargar y fijar primero; verificar después la configuración definitiva y volver a comprobar antes de cada caso. |
| Cuatro minutos incluían resolver política, preparar supervisor, setup y muchas sondas. | Un tiempo asignado aparentaba capacidad técnica demostrada. | Separar supervisor/baseline, carga/configuración y prueba final; un único intento acotado y abandono explícito si no cabe. |
| Denegación del shell confundible con control del bootstrap. | El host puede descubrir instrucciones antes de ejecutar un comando protegido. | Dos puertas independientes: aislamiento de comandos y procedencia/descubrimiento de instrucciones del host. |
| Inventario de ancestros incompleto como regla de descubrimiento. | Ignorar overrides, fallbacks, límites de tamaño o capas administradas. | Resolver la cadena efectiva desde Git/cwd, global CODEX_HOME, nombres alternativos y truncamiento; comparar catálogo y evidencia de sesión. |
| Inicio W1 descrito como primer mensaje, sin concretar bootstrap del TUI. | Leer instrucciones antes de activar la captura y desplazar coste fuera de W1. | Registrar envío del prompt inicial y activar captura antes de crear el proceso nuevo con ese prompt. |
| Sonda negativa de red sin control positivo. | Un destino caído aparenta una denegación del sandbox. | Listener local propio con control accesible desde host y rechazo desde sandbox, o evidencia equivalente; nunca usar un fallo de DNS como prueba. |
| Recuperación del residual con baseline incompleta y cuentas compartidas. | Afirmar restauración total o retirar recursos ajenos. | Registrar residual heredado, comparar solo deltas nuevos y separar perfiles, deltas propios y recursos compartidos conservados. |
| Cierre de H2 y ahorro confundibles. | Prometer resultado favorable por completar la pareja. | H2 puede completarse con ahorro rechazado; AC-34 solo se supera con todos los umbrales y garantías. |
| Falta de tiempo de transición/cancelación en los cortes. | Consumir recuperación para acabar B. | Cortes absolutos, transición dentro de B y reserva R/C intocable; cancelación se carga a R. |

Comprobación presupuestaria: 51.340,945 s cerrados − 10.903,592044 s de reposo
acreditado = 40.437,352956 s. Saldo antes de esta revisión: 2.762,647044 s.
Revisión ≤240 s + ejecución ≤2.280 s + margen 180 s = **2.700 s**;
sobran **62,647044 s** incluso reservando los tres conceptos completos.
Máximo proyectado: **43.137,352956 s = 11,982598 h < 12 h**. El margen no es una
ampliación automática de los casos. Este es el registro observado conciliado;
no certifica consumos externos desconocidos ni que el resto de 4.0 quepa.

**No se puede confirmar aún la viabilidad técnica de completar la pareja.** Se
puede confirmar que la ruta propuesta tiene controles y cotas que caben en la cuenta
conocida. Las puertas operativas decidirán si se admite cada caso; si no, se
recupera y H2 permanece inconcluso, sin fabricar resultados ni relajar aislamiento.
