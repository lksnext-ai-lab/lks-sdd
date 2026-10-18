# LKS-SDD 4.0 — Revisión crítica del plan 0.3

Fecha: 2026-10-16. Resultado documental: **plan 0.4**.
Alcance: revisión y actualización de documentos; no implementación ni ejecución de
las tareas nuevas. Se incorpora la petición de prevenir la regresión de temporales
largos de Windows. Se mantienen seis mejoras, 23 tareas, 44 criterios y los techos
acordados. Las cuatro tareas nuevas conservan estado `planned`.

## 1. Dictamen

Las cuatro tareas son compatibles entre sí y con las seis mejoras **con las
correcciones siguientes**. El plan 0.3 no demostraba su viabilidad presupuestaria:
su suma mínima omitía un ensayo temprano y una reserva de incidencias, solo preveía
una pareja S8 final y no acreditaba capacidad suficiente en horas.

La revisión 0.4 reserva **43 de las 48 plazas** conocidas/previstas, incluida
contingencia. Comprueba el encaje aritmético de la base, no certifica saldo real.
La viabilidad integral de las **12 h de entorno y 8 h humanas sigue sin acreditarse**.
Una serie M6 adicional de doce intentos llevaría a 55/48 y queda fuera del compromiso
base. M6 se conserva como perfil y decisión motivada, pudiendo terminar sin cambios.
No se elimina ninguna de las cuatro tareas para aparentar cumplimiento.

## 2. Hallazgos y correcciones aplicadas

| Prioridad | Problema de 0.3 | Corrección 0.4 y efecto comprobable |
|---|---|---|
| Alta | V4-02B bloqueaba V4-03 y toda mejora aunque no necesitase S8. | Restaurar V4-03→V4-02. V4-02A/02B condicionan S8, actividad y optimización asociada; H2 independiente mantiene su protocolo. |
| Alta | El recorrido completo del incidente llegaba después del paquete final. | V4-06 añade una pareja S8 temprana y depende de V4-02B. Descubre fallos antes de ampliar/empacar, sin sustituir aceptación final. |
| Alta | Una pareja final no controlaba el efecto del orden. | V4-17A usa dos parejas AB/BA, cuatro intentos. Evidencia descriptiva de ese caso, sin afirmar estabilidad universal ni cumplimiento de E4. |
| Alta | El cálculo mínimo de 35 plazas ocultaba recuperación y podía sugerir que también cabía M6. | 43 plazas incluyendo cuatro de contingencia; cinco como máximo teórico libre. M6 adicional de doce no se compromete. |
| Alta | Encajar intentos se confundía con caber en horas. | Cotas de trabajo explícitas, registro de dimensiones y admisión antes de cada bloque. Tiempo humano histórico desconocido y cobertura de entorno parcial conservados como límites. |
| Alta | Investigación de una espera de 40 minutos sin corte concreto ni matriz acotada. | Dos tamaños como máximo, cuatro consultas de hasta 120 s, perfil separado de hasta 30 s y 45 min totales V4-02A. Corte no equivale a latencia aceptable ni finalización. |
| Alta | Un diagnóstico inconcluso podía hacer pasar un fixture insuficiente. | AC-37 permite disposición inconclusa; AC-38 exige fixture válido y representativo. Sin este último no se verifica V4-02A. |
| Media | Comparar por nombre/número de comandos penalizaría operaciones legítimamente agrupadas. | Mapa previo de hitos, entradas, condiciones y efectos A/B. Contar tiempo y coste una vez, conservando evaluaciones internas y guardas. |
| Alta | La reacción a interrupciones podía leerse como aborto inmediato o ausencia de efectos. | Puntos cooperativos y journal existentes; límites por fase/E/S, efectos parciales y artefactos explícitos. Sin motor transaccional nuevo ni garantías simuladas. |
| Alta | Ruido y exceso de latencia no estaban suficientemente separados. | Todo exceso válido del candidato es fallo; solo invalida causa externa preregistrada. Repetición/corrección consume capacidad y no permite buscar éxito por insistencia. |
| Media | Negativos y recorridos podían repetirse en varias tareas. | V4-06/07A/14 producen pruebas focales; V4-15 consolida y V4-17A reutiliza evidencia todavía válida. No un recorrido completo por cada negativo. |
| Alta | Nuevos destinos de captura/recuperación podían reintroducir rutas temporales largas de Windows. | Cobertura explícita en V4-04/07A/14/15/16, propagada a S8; reutilizar helpers y regresión reales. Ruta corta no sustituye prueba larga. |
| Media | Texto heredado podía seguir leyendo E5 como bloqueo técnico. | Aclarar que E5/AC-36 y comprensión humana siguen diferidos a uso real; no modificar sus criterios originales ni declarar superación. |

## 3. Encaje de las cuatro tareas

| Tarea | Aportación y dependencia | Condición de cierre / límite |
|---|---|---|
| V4-02A · R1 | Diagnóstico y fixture tras V4-02; insumo de V4-02B y compatibilidad. | Identidad efectiva, inventario independiente y fixture válido; disposición del incidente explícita. Máximo inicial 45 min. |
| V4-02B · R3 | Contrato numérico después del fixture, antes de S8/actividad/optimización asociada. | Parámetros completos, semántica A/B comparable y comprobabilidad dentro del corte. Máximo inicial 15 min; no bloquea M1 independiente. |
| V4-07A · R4 | Actividad/interrupción después de captura V4-04, continuidad V4-07 y parámetros V4-02B. | JSON compatible, señales acotadas, recuperación y efectos reales; garantías solo en fases probadas. Máximo inicial 60 min. |
| V4-17A · R2 | Dos parejas finales después de V4-16, con fixture/criterios ya fijados. | Equivalencia, máximos absolutos y adversos vigentes. Cota conjunta de 120 min con la pareja temprana V4-06. |

El grafo mantiene dos ramas iniciales y converge antes del ensayo temprano. Ninguna
tarea previa depende de V4-17A; la comprobación final no crea un ciclo. La aceptación
de actividad no se exige al prototipo que todavía no la implementa. Los seis ejes
siguen siendo M1 transporte, M2 operaciones, M3 alcance, M4 instrucciones, M5
mantenimiento proporcional y M6 cálculo medido; las tareas nuevas desarrollan M1/M2/M6
y compatibilidad, sin crear una séptima línea.

## 4. Presupuesto y alcance viable

| Concepto | Plazas |
|---|---:|
| Cargos históricos conocidos | 7 |
| H2: referencia y candidata | 2 |
| Finales S1–S6, ambos hosts | 24 |
| S8 temprano | 2 |
| S8 final AB/BA | 4 |
| Contingencia protegida, no ejecución obligatoria | 4 |
| Total conocido/reservado | **43** |
| Máximo teórico aún sin asignar | **5** |

El total de 43 es una reserva conservadora, no una afirmación de que solo hubo siete
intentos históricos. Trabajo no registrado puede reducir las cinco plazas; no se
reinicia el contador. La contingencia cubre fallos/repeticiones y no se gasta en
optimización opcional. Si faltan más intentos para cerrar calidad, queda pendiente.

M6 mantiene sus límites de dos variantes/cuatro horas **dentro** de los globales.
La serie adicional mínima de doce intentos requeriría 55 plazas con esta reserva:
no cabe. No reducir las seis parejas del protocolo, mezclar S8 con E4 ni retirar
cobertura Copilot/Windows para compensarlo. Una variante solo se considera si puede
cumplir el protocolo íntegro con capacidad acreditada y evidencia legítimamente
reutilizable; no se promete esa posibilidad.

La observación numérica de 19 turnos cerrados suma 16.016,14 s (**4,4489 h**) hasta
2026-10-16T08:31:48.998Z. Es el proxy histórico de duración de turnos, no medida exacta
del entorno ni de atención humana; excluye esta revisión abierta y cualquier coste
fuera de su cobertura. El registro se conserva en
[budget-observation.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/plan-0.4-20261016/budget-observation.json>).

Las cuatro tareas tienen cotas de parada por **4 h**, incluyendo preparación,
implementación futura, prueba, recuperación e informe. La cobertura Windows reutilizada
reserva **0,5 h** de compatibilidad. Incluso con el proxy conocido quedarían solo
**3,0511 h nominales** para el resto, esta revisión y trabajo no observado. No existe
estimación contrastada que pruebe que basta. Las cotas limitan el gasto; no demuestran
que el trabajo pueda terminar en ellas.

Antes de ejecutar se exige capacidad por bloque y resto obligatorio, sin doble cuenta
de reservas ni conversión de desconocido a cero. No se solicitan nuevas mediciones
de atención humana; su valoración se mantiene para uso real sostenido. Tampoco se
afirma cumplir retrospectivamente las ocho horas humanas desconocidas. Los presupuestos
no se elevan ni se transforma falta de capacidad en aceptación técnica.

## 5. Windows: conservar la solución y cubrir las fronteras nuevas

La fuente actual incluye [helpers de rutas](../../../scripts/path_utils.py),
[arranque de imports](../../../scripts/import_bootstrap.py) y
[regresión real de rutas largas](../../../tests/test_windows_long_paths.py).
La [validación vigente](../../VALIDATION.md) ya la exige en la puerta estable.
Este hecho confirma una protección existente, no que la candidata futura la pase.

El riesgo específico de 4.0 es recrear rutas profundas con capturas, bundles,
temporales de preparación, reintentos y recuperación. Se prueba equivalencia corta/
larga (>260 caracteres), TEMP/TMP profundo y espacios/Unicode, recursos completos,
integridad, archivos ajenos y recuperación. Conservar nombres y rutas acotados donde
se controla su creación; no confundir ese diseño con soporte de cualquier herramienta
externa, volumen o configuración. La dependencia 8.3 del bootstrap se declara cuando
aplique; no modificar ajustes globales como efecto de una prueba.

V4-14 es propietaria, V4-15 consolida y V4-16 comprueba ambos paquetes. AC-06/07/08/
12/24/25/26/29 se conservan literalmente y se detallan mediante esta cobertura;
AC-41/44 incorporan su relación con recuperación/S8. No se crea otro gate ni se
recortan timeouts del actual. Una extracción incompleta, skip o uso exclusivo de
ruta corta deja la comprobación pendiente. Un fallo de Windows bloquea afirmar
compatibilidad; no se imputa a ruido de rendimiento ni se compensa con tokens.

## 6. Evidencia y pendientes reales

Se preservan G1–G10, AC-01–AC-36, protocolo 1.0, SCENARIOS.json, cierre V4-02 y
documentos históricos. AC-37–AC-44 se precisan sin marcarse superados; tampoco se
ejecuta la regresión Windows para comprobar una edición documental.

La revisión 0.3 completa está en
[plan-before-0.4.zip](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/plan-0.4-20261016/plan-before-0.4.zip>)
(SHA-256 `c131a337bb5faed63ef2d613a7e708efdcb23332b5e3e0c0fc590137ec7ccf59`).
El [registro 0.4](REVISION-0.4.json) enlaza validación documental, hashes y diff;
esas comprobaciones no acreditan ningún criterio funcional de producto.

Pendientes: autorización de ejecución, capacidad real de cada bloque, validez del
fixture, números operativos de V4-02B y resultados de implementación/aceptación.
No se necesitan cronometrajes humanos para cerrar esta revisión documental. Copilot
permanece al final. La compatibilidad está diseñada y revisada; la finalización de
toda la release dentro de los techos no puede prometerse con la evidencia disponible.
