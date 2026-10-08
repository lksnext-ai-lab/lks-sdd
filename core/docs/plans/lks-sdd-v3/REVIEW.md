# Revisión crítica de PLAN-V3-001

Fecha: 2026-09-29. Revisión resultante: **v3-plan-02**.
Estado: **correcciones incorporadas a la planificación; implementación sin ejecutar**.

## Dictamen

El plan anterior recogía las áreas aprobadas y asignaba los 69 requisitos/100 casos,
pero eso no bastaba para considerarlo ejecutable con eficiencia. Sus principales riesgos
eran integrar tarde, dejar entradas al producto sin autoría concreta y medir al final.
Se conservan las 17 tareas y la propuesta v3-propuesta-03: se mejora su descomposición,
las condiciones de inicio/cierre y la comprobación de resultados.

## Hallazgos y correcciones

| Hallazgo sobre v3-plan-01 | Consecuencia si se ejecutaba literalmente | Corrección en v3-plan-02 |
|---|---|---|
| Alta: CLI, paquetes y aceptación se concentraban en 014–017 después de casi todo el runtime. | Descubrir tarde interfaces incompatibles, omisiones de distribución o una experiencia pesada. | Inicio independiente y cierre diferenciados; recorridos R1–R4. 013–017 preparan/contrastan porciones desde el comienzo, sin cerrar antes de integrar. |
| Alta: faltaba el recorrido completo de proyecto nuevo y existente sin SDD. | Schemas y migrador disponibles, pero sin una forma real y comprobada de crear/adoptar el proyecto. | 003 configura y resuelve autoridad inicial; 004 implementa autoría; 007 cubre rama/base naciente; 011 separa adopción acotada de migración 2.x; 016 prueba las tres entradas. |
| Alta: dependencias de integración incompletas. | 007 podía cerrarse sin 008 para vigencia por composición; 013 solo esperaba preview 011, no resultado aplicado/recuperado de 012. | Añadidas dependencias reales de cierre 007→008 y 013→012. El desarrollo temprano conserva interfaces/provisionales y no acredita integración pendiente. |
| Alta: medición de eficiencia definida demasiado tarde y comparación v2/v3 no siempre equivalente. | Perder la referencia, atribuir ahorro a capacidades ausentes o impedir la prueba de selección al exigir aceptación previa a cualquier uso. | 017 prepara referencia/protocolo temprano. Comparaciones separadas de operaciones comunes y obligaciones nuevas; prueba controlada de selección antes de activación ordinaria, con cobertura primero. |
| Alta: obtener/normalizar informes no concretaba por sí solo ejecutar→corregir→reanalizar. | Implementar lectores correctos y no comprobar el ciclo real, o aceptar el último informe de otra ejecución. | 008 fija invocación/recogida/importación, entradas exactas y formatos admitidos; 009 prueba corrección y análisis nuevo, también con código sin commit; observación real separada de fixtures. |
| Media: 69/100 asignaciones podían confundirse con cobertura semántica completa. | Dar por satisfecho un caso compuesto con una sola aserción o una tarea propietaria que no integra a sus contribuyentes. | Matriz con contribuyentes derivados y condiciones observables por recorrido; 016 exige resultado, restricciones e historia, sin un expediente por cada cláusula. |
| Media: reutilización del runtime, conservación y algunos límites de migración quedaban genéricos. | Duplicar módulos v2, degradar obligaciones existentes o convertir dependencias v2 a un tipo más débil. | Inventario de reutilización/adaptación en 001; conservación explícita en 002; dependencias heredadas y runtime coherente en 012; candidatos/formatos probados delimitados en 015. |
| Media: el grafo y las fichas podían fomentar demasiado trabajo abierto y registros duplicados. | Muchos frentes sin resultado utilizable, conflictos de archivos y coste administrativo para los agentes. | Priorizar recorridos, un integrador por archivo, porciones revisables sin nuevas autorizaciones/fichas y evidencia compartida por caso. JSON/grafos son vistas derivadas del plan Markdown. |

“Alta” indica un riesgo material para completar el alcance; no una vulnerabilidad detectada
ni un fallo observado en v3, que todavía no existe. La corrección descrita es documental.

## Cobertura funcional revisada

| Objetivo del usuario | Comprobación concreta prevista |
|---|---|
| Solo/equipo y evolución del proyecto | Alta/configuración y cambio de proceso en 003/005; tres entradas en R1; mantenimiento y roles acumulables. |
| Propuesta comprensible validada antes del plan | Autoría real y snapshots en 004; mensajes tempranos 013/014; comprensión observada 017. |
| Agilidad sin saltarse reglas | Una configuración inicial agrupada, dos decisiones para el cambio pequeño configurado, cero repetición al reanudar; distinguir preparación y aceptación final. |
| Especialistas y relevo | Porción, contribuciones, aceptación exigida y recepción real en 006/007; prueba conjunta R3. |
| Ramas/UID y trazabilidad | Rama/base incluso sin primer commit, cambios sin commit, clones, alias coincidentes, procedencia y recuperación; 002/007/012. |
| Sonar y Dependency-Check opcionales por decisión | Uso/no uso independientes, viabilidad, ciclo real y evidencia vigente; 008/009 con excepciones 005. |
| Migración y continuidad | Orígenes exactos, originales, mapa único, dependencias preservadas, autorizaciones diferenciadas y ramas antiguas; 011/012. |
| Eficiencia de contexto | Lectura progresiva, suficiencia antes de tamaño, invalidación, referencia comparable y consumo de la tarea completa; 010/014/017. |
| Compatibilidad y seis skills | Inventario de operaciones, routing, paquetes tempranos y comprobación de ambos hosts; 001/014/015/017. |
| Mantener fuera CI/CD | Lectura/uso de análisis disponibles sin pipelines ni nuevos conectores; aprobación de PR, instalación y publicación separadas. |

## Eficiencia y límites del dictamen

El cambio evita esperas de diseño artificiales, pero conserva dependencias reales para
cerrar. No estima ahorro de días, coste o tokens sin implementación y medición. Con una
persona se prioriza un recorrido a la vez; con equipo se aprovechan interfaces estables
y capacidad disponible. No se añade una tarea por cada microentrega o prueba.

Quedan datos de ejecución que no deben inventarse: participantes, hosts/medios reales
disponibles, límites de tiempo acordados y formatos/versiones de análisis concretos
acreditables. Se preparan temprano; su ausencia limita su aceptación correspondiente,
no paraliza toda la implementación independiente. Una incompatibilidad nueva que cambie
la propuesta aceptada debe volver a decisión localizada.

No se garantiza exhaustividad futura con una revisión estática. Lo comprobado ahora es
cobertura de planificación, coherencia de dependencias y fidelidad a la propuesta. La
verificación del comportamiento y la aceptación de uso continúan pendientes.

## Historia y decisión

La [revisión anterior v3-plan-01](history/v3-plan-01.zip) conserva sus 25 archivos,
incluido su descriptor original. SHA-256 del ZIP:
`40d4d835cfcd0a5f1808a2b022b47e7b739c4635910906281587414d2fe4b7f8`.
Es un **borrador histórico no aprobado**, no una aprobación anterior del plan.

Se conservan sin modificación las tres fuentes de v3-propuesta-03 y su instantánea
aceptada. [DEC-V3-001](APPROVAL.md) sigue acreditando la validación de esa propuesta.
La petición de revisión crítica no autoriza código ni aprueba v3-plan-02.
El [plan vigente](PLAN.md) está preparado para revisión y autorización de ejecución.
