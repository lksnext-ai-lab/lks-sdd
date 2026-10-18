# Análisis del reporte de espera en aprobaciones heredadas

Fecha: 2026-10-16. Estado: **análisis y propuestas; no modifica el plan aprobado ni autoriza implementación**.
Base examinada: LKS-SDD 3.4.3, commit `bf4d059c98826039097d606121ab6406d762fcc7`.

**Dictamen:** el mecanismo señalado ya está abordado en la fuente de 3.4.3, que
es la referencia de 4.0. El incidente aportado ejecutaba 3.4.2. No existe en este
ZIP una comparación que permita declarar resuelto el caso del equipo con 3.4.3.
Conviene ampliar la cobertura y los criterios de aceptación de 4.0, conservando
las seis mejoras, antes que encargar de nuevo la optimización ya implementada.

## 1. Evidencia y alcance comprobados

Paquete recibido: [lks-sdd-performance-20261016.zip](<C:/AI-Workspace/worktrees/codex/297f/sat-next-ai-designer/.tmp/visits/release-0.14.0/lks-sdd-performance-20261016.zip>).
SHA-256: `0d9564dda518a767bc6a004a2d3071a095b7f2b84f031039db59f32c7d4742af`.

- Se han comprobado los diez hashes de contenido del manifiesto: todos coinciden.
  Esta integridad interna no autentica por sí sola el proceso que generó el reporte.
- Los cinco hashes declarados de fuentes originales coinciden con los archivos de
  la etiqueta local `v3.4.2`. Cuatro difieren de 3.4.3; `v3_guidance.py` no cambia.
  La corrección se encuentra en los módulos que esta guía invoca.
- El perfil contiene 599 muestras en 29,95 segundos. Recalculando las pilas:
  `inherited_confirmations` aparece en 599/599 y `descriptor` en 563/599, el 94,0 %.
  Se confirman también las hojas `uid` 36,4 %, `get` 32,9 % e `id` 18,4 %.
- El desglose de tipos suma las 769 fuentes declaradas. No es el tamaño total del
  modelo. Los 7.499.762 caracteres de contexto no son tokens ni prueban lectura.
- El informe declara 39 min 50 s sin resultado terminal y 2.268,28 s de CPU, además
  de otra espera durante `integrate`. El ZIP no contiene una serie completa de
  contadores de proceso ni el resultado final: esos tiempos son observaciones
  comunicadas; el perfil confirma actividad en una ventana concreta.

La operación atascada es **`readiness(action=start)` de una nueva tarea operativa**,
posterior a la implementación funcional. Por tanto afecta a una entrega, pero no
demuestra un fallo de Docker, CI, Sonar o del mecanismo remoto de publicación.
La observación anterior en `integrate` refuerza la necesidad de cubrir el recorrido
de cierre, sin constituir una repetición controlada del incidente.

El reporte distingue correctamente plugin instalado 3.4.3 y runtime ejecutado
`3.4.2-b70010c9f8a6`. Sus recomendaciones se han tratado como propuestas, no como
órdenes. No se ha ejecutado código del ZIP ni operado sobre el consumidor.

## 2. Qué está ya resuelto en código y qué no está acreditado

En 3.4.2, comprobar las aprobaciones heredadas vuelve a construir descriptores y
cierres de dependencias. La comprobación se repite por tecnología; resolver cada
identidad recorre el modelo. El perfil es coherente con esta ruta. No determina
por sí solo su complejidad exacta ni qué porcentaje de los cuarenta minutos explica.

La fuente 3.4.3 contiene:

- Índices de UID, alias y tipo con invalidación y preservación de ambigüedades:
  [v3_contract.py](../../../scripts/v3_contract.py).
- Un ámbito inmutable compartido por `facts_for` y las aprobaciones anidadas;
  reutilización acotada del lector, cierres y descriptores:
  [v3_evaluation.py](../../../scripts/v3_evaluation.py),
  [v3_approval.py](../../../scripts/v3_approval.py) y
  [v3_workflow.py](../../../scripts/v3_workflow.py).
- Reutilización de originales heredados verificados por ruta y hash:
  [v3_migration.py](../../../scripts/v3_migration.py).
- Pruebas de reconstrucción única en un caso que cabe en los límites, cambios de
  originales, mecanismos tecnológicos mixtos e invalidación:
  [test_v3_approval_performance.py](../../../tests/test_v3_approval_performance.py).

Estas medidas coinciden directamente con la hipótesis principal del reporte.
Instalar el plugin no actualiza el runtime fijado por un consumidor: una adopción
explícita y comprobada es necesaria para que el equipo utilice esa corrección.

**Límite decisivo:** la [promoción de 3.4.3](../approval-performance/IMPLEMENTATION.md)
y su [manifiesto de evidencia](../../evidence/approval-performance-3.4.3.json)
declaran incompleta la matriz aislada de rendimiento contra 3.4.2. Se registran
pruebas técnicas y recorridos de paquetes, pero no una garantía de latencia para
este consumidor. Tampoco hay una reproducción autónoma en el ZIP recibido.

Existe un generador sintético con 35 tecnologías y aprobaciones heredadas. Sin
embargo, su caso de cálculo añade principalmente elementos `feature` de relleno,
hasta 24 reglas compartidas y originales sintéticos. Igualar el número de elementos
no demuestra equivalencia con la topología, historia, prosa y dependencias del
reporte. Debe reutilizarse y ampliarse de forma dirigida, no declararse suficiente
por su tamaño. Véase [approval_performance_support.py](../../../tests/approval_performance_support.py).

Persiste además la evaluación independiente entre comandos: la caché de una
consulta no cruza a `start`. Esa frontera protege la vigencia. Agrupar operaciones
solo evita trabajo redundante si conserva las guardas frescas al materializar;
no debe trasladar una autorización calculada a otro comando como si siguiera vigente.

## 3. Encaje con las seis mejoras

| Mejora | Aportación a este incidente | Límite o ajuste necesario |
|---|---|---|
| M1 · Transporte y diagnóstico | Reduce salida y trabajo para conservar evidencia. | No elimina el cálculo anterior a la primera salida. El progreso durante una espera no está concretado como entrega. |
| M2 · Operaciones completas | Puede evitar consultas preventivas y coordinaciones repetidas; cubre inicio y cierre técnico. | Debe medir también las evaluaciones internas; menos llamadas no garantiza menos CPU. Integración y publicación externa conservan sus fronteras. |
| M3 · Alcance documental | Puede reducir el conjunto aplicable cuando exista clasificación acreditada. | Las obligaciones globales o inciertas siguen incluidas. No sirve excluirlas para ocultar el problema. |
| M4 · Instrucciones por operación | Evita repetir consultas y permite explicar versión efectiva y siguiente paso. | No corrige por sí misma la lentitud del evaluador ni actualiza runtimes fijados. |
| M5 · Mantenimiento proporcional | Facilita encauzar una incidencia sin reconstruir acuerdos válidos. | No es la solución principal del coste de aprobaciones heredadas. |
| M6 · Cálculo medido | Es el lugar para investigar y corregir cualquier coste residual reproducido. | Parte de las correcciones ya son 3.4.3. No se contabilizarán otra vez como ahorro de 4.0. |

El plan actual ofrece encaje, pero no garantiza cerrar este incidente: S4 no exige
expresamente esta combinación de migración y aprobaciones; V4-12 comienza después
de V4-06/V4-09; y V4-13 admite descarte sin cambios. Eso es correcto para una
optimización opcional, pero no basta para disponer de un bloqueo operativo confirmado.

## 4. Ampliación propuesta, sin alterar todavía el plan

Los identificadores R1–R4 siguientes son propuestas de este análisis; no son tareas
aprobadas ni ejecutadas. No crean una séptima mejora.

| Propuesta | Encaje y dependencia | Entregable y aceptación |
|---|---|---|
| **R1 · Verificar versión efectiva y disposición de la incidencia** | Complemento de referencia previo al desarrollo; después de V4-02, con salida para V4-12 y V4-14. | Reutilizar el fixture heredado, identificar qué rasgos del reporte representa y contrastar 3.4.2/3.4.3. Registrar versiones/digests efectivos, resultado terminal, tiempo, CPU, memoria y límites. Dictamen: resuelto en caso representado, persiste o inconcluso. La comprobación del consumidor real requiere adopción autorizada y evidencia del equipo. |
| **R2 · Regresión obligatoria de proyecto migrado y recorrido de entrega** | Ampliar V4-05/V4-06, V4-12 y V4-15/V4-17; usa el caso R1. | Cubrir `readiness → start`, implementación, verificación, cierre e integración nativa. Comparar instrucciones/operaciones individuales y compuestas con mismas obligaciones y estados; contar evaluaciones internas y coste total. Separar publicación externa y su autorización. Escalar tecnologías, correspondencias y tamaño de grafo de forma dirigida, sin matriz cartesiana. |
| **R3 · Aceptación de latencia operativa y coste residual** | Ampliar V4-12/V4-13 y dictamen V4-18; objetivo fijado con R1 antes de observar candidata. | Definir un máximo absoluto de finalización para la consulta y el recorrido representativo, sobre máquina/carga declaradas. Mantener los criterios de ahorro y ruido existentes, medir memoria y probar frescura, revocación y originales ausentes/modificados. No cerrar la incidencia solo porque se ahorren cinco segundos ni porque se agote el presupuesto. |
| **R4 · Espera observable e interrupción segura** | Ampliar V4-03/V4-04/V4-07 y contrato V4-01; verificar en V4-15. | Señales acotadas de fase/actividad, sin porcentajes ficticios; resultado final inequívoco e interrupción documentada. Cancelar una consulta no modifica el contrato. Una interrupción en preparación/aplicación usa recuperación existente y no produce éxito falso ni doble efecto al reintentar. Preservar JSON y compatibilidad; contabilizar bytes, CPU y frecuencia de señales. |

Prioridad: **R1 primero y obligatorio para atribuir la causa a una versión vigente;
R2 obligatorio para la cobertura de 4.0**. R3 debe fijar la aceptación antes de
optimizar; solo exige una nueva corrección si se reproduce un coste inaceptable.
Recomiendo incluir R4 de forma mínima, con diseño explícito: aporta diagnóstico y
control, pero no sustituye resolver la lentitud. No requiere nuevo servicio,
daemon, agente, hook ni canal de telemetría.

Para R4 conviene separar la interrupción del proceso del comando de negocio
`cancel`, que cambia el estado de una tarea. Tampoco debe imponerse un corte
brusco genérico durante una transacción: los puntos de interrupción y recuperación
se definen sobre los mecanismos ya existentes. Las señales pueden usar un canal
compatible optativo para no contaminar stdout JSON ni multiplicar lecturas del agente.

El máximo absoluto de R3 **no se deduce del ZIP**. Un límite del ensayo protege
recursos, pero no es automáticamente una latencia aceptable de producto. Se fija
antes de probar la candidata, con el caso y entorno representativos. Si 3.4.3 ya
cumple, puede mantenerse sin nuevas optimizaciones; esa conclusión se demuestra.

## 5. Medición, garantías y presupuesto

1. Mantener separadas tres comparaciones: 3.4.2→3.4.3 para diagnóstico/adopción;
   3.4.3→4.0 para el ahorro de la release; y candidata previa→variante para M6.
   El caso comunicado de cuarenta minutos no reemplaza la referencia 3.4.3.
2. Reutilizar evidencia y herramientas existentes. El nuevo caso debe tener una
   ficha de cobertura frente al incidente; un sintético representativo no se
   presenta como reproducción exacta sin el grafo original o equivalencia acreditada.
3. Las series temporales se realizan sin perfilador; CPU/memoria y contadores
   instrumentados se investigan aparte. Contar preparación necesaria, diagnósticos,
   reintentos y guardas. Un timeout conserva coste y queda incompleto; no se toma
   como tiempo de finalización ni se elimina como ruido.
4. Preservar obligaciones globales e inciertas, mecanismo individual de aprobación
   tecnológica, autoridad y evidencias vigentes. Probar cambios entre consulta,
   preparación y aplicación. El estado final y los rechazos deben ser equivalentes.
5. Mantener 48 intentos completos, 8 h humanas, 12 h de entorno y M6 de dos variantes/
   cuatro horas. La incorporación exige reasignar y reservar capacidad existente;
   no crear una bolsa paralela ni prometer ensayos ilimitados de 3.4.2. Ensayos de
   componentes consumen tiempo aunque no sean tareas completas. Si no cabe, dejar
   el resultado pendiente y explicitar su efecto en la decisión de release.
6. Mantener valoración humana para uso real sostenido. Los cuarenta minutos son
   duración de máquina comunicada; no equivalen a atención activa o esfuerzo humano.
   No hay en el reporte prueba de ahorro de tokens.

**Consecuencia para el plan aprobado:** V4-02 sigue cerrado con su alcance y
protocolo 1.0. Si se acepta esta ampliación, registrar un addendum de cobertura y
aceptación antes de ejecutar comparaciones; conservar los originales congelados.
No sustituir silenciosamente S4, sus denominadores ni los umbrales existentes.
Un bloqueo operativo reproducido en el runtime objetivo necesita corrección o
decisión explícita de alcance/riesgo; el descarte de una optimización M6 no lo resuelve.

## 6. Resultado de esta revisión

Se han examinado el ZIP, perfil, hashes, fuentes 3.4.2/3.4.3, pruebas existentes,
evidencia publicada en el repositorio y plan/protocolo 4.0. No se ha repetido una
campaña de rendimiento ni ejecutado la consulta sobre el proyecto del equipo.
Los resultados históricos se citan con sus límites y no como pruebas ejecutadas hoy.

**Recomendación:** comprobar primero la adopción y el comportamiento de 3.4.3;
incorporar R1–R4 al alcance de 4.0 con la proporcionalidad indicada. No esperar a
4.0 para investigar si la corrección ya disponible permite desbloquear al equipo.
Hasta obtener esa comprobación, la conclusión es «causa abordada en código;
resolución de este incidente pendiente de demostrar».
