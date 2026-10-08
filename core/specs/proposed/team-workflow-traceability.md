# Propuesta funcional para LKS-SDD v3: equipo, flujo, ramas y calidad

Fecha: 2026-09-28. Estado: propuesta funcional completa para revisión.
Última revisión: 2026-09-29. Incorpora flexibilidad, agilidad, acompañamiento,
validación previa a la planificación y migración de proyectos 2.x a 3.x.
Revisión del paquete: **v3-propuesta-03**, pendiente de validación. Conserva las
mejoras de los siete puntos y añade eficiencia de contexto con suficiencia comprobada.
Origen: conversación de definición del plugin sobre trabajo individual y en
equipo, especialistas, identidad, mantenimiento evolutivo, ramas y comprobaciones
con Sonar y Dependency-Check durante la implementación.

Este documento recoge necesidades expresadas por el usuario y propone cómo
incorporarlas al método. No es un contrato canónico ni acredita soporte nuevo en
el runtime. Propone v3.0.0 como destino de producto, sujeto a validación; no cambia
la versión instalada, el método o schema vigente ni autoriza implementación.
Los identificadores REQ-EQT y AC-EQT son locales a esta propuesta de mantenimiento.

La revisión conjunta se presenta en el [paquete para validar v3](lks-sdd-v3-validation.md),
con esta definición y la [propuesta técnica](lks-sdd-v3-technical-proposal.md).

Guía de lectura: alcance y fuentes en las secciones 0–2; requisitos en la 3;
trazabilidad, equipo y ramas en la 4–6; Sonar y Dependency-Check en la 7;
aceptación en la 8; experiencia, modelo documental y adopción en la 9–11;
ejemplo completo, validación antes de planificar y decisiones propuestas en la 12–14.

En lenguaje sencillo: cada proyecto acuerda cómo quiere trabajar. El plugin aplica
ese acuerdo, explica dónde está el trabajo y qué viene después. El equipo puede
cambiar el acuerdo o apartarse de él en un caso concreto con validación y motivo
registrados. El historial debe distinguir lo que se hizo de lo que se decidió omitir.

## 0. Objetivo, alcance y decisiones de la conversación

El objetivo es que una persona o un equipo puedan llevar una petición desde su
definición hasta una implementación verificada e integrada, con un flujo de proyecto
que indique quién debe intervenir, qué puede hacer y qué falta para avanzar.
El contexto debe poder recuperarse desde el repositorio al cambiar de chat,
especialista, rama o herramienta de asistencia.

**Confirmado por el usuario:** incluir trabajo individual y de equipo, evolución de
miembros y cuentas, responsabilidades y delegaciones, ramas por petición, identidad
de los elementos documentales y trazabilidad. Sonar y Dependency-Check forman parte
del ciclo de implementación y corrección cuando el proyecto los utiliza; el proyecto
puede declarar expresamente su no utilización. La gestión de CI/CD queda fuera de
esta propuesta por la última delimitación de alcance del usuario.
La revisión posterior confirma que el proceso debe poder adaptarse durante la vida
del proyecto, admitir excepciones validadas y orientar al usuario tanto al consultar
el estado como al completar cada paso, con recomendaciones fundamentadas.
La última aportación exige que el proceso sea ágil y que la propuesta funcional y
técnica concreta se valide antes de elaborar el plan que ejecutarán los agentes.
Se incorpora la migración 2.x → 3.x como requisito; el salto a v3 se presenta como
destino propuesto por el usuario, aún pendiente de la validación del conjunto.

**Propuesto para revisión:** los comportamientos, roles, reglas, representaciones y
criterios que siguen. La autorización para redactar esta propuesta no aprueba todas
sus opciones de diseño ni habilita su implementación.

| Dentro de esta propuesta | Fuera de esta propuesta |
|---|---|
| Configuración del equipo, flujo SDD y condiciones para avanzar. | Diseño, creación, modificación u orquestación de pipelines de CI/CD. |
| Peticiones, SPEC, PLAN/TASK, asignaciones, relevos, revisión e integración funcional. | Gobierno de releases, artefactos de distribución, promoción entre entornos y despliegues. |
| Ramas de trabajo, destinos, procedencia Git, conflictos e identidades documentales. | Operación de infraestructura, secretos corporativos, runners, observabilidad de producción y recuperación operacional. |
| Ejecutar u obtener análisis Sonar y Dependency-Check con medios disponibles y autorizados; corregir y volver a comprobar durante la implementación. | Crear un agente DevOps, otro plugin, conectores, MCP, hooks o una plataforma de identidad corporativa. |
| Revisar la vigencia de evidencias al integrar y preparar la información trazable del PR/MR. | Configurar protecciones del servidor, aprobar/fusionar PR automáticamente o certificar un pipeline por tener análisis de tarea satisfactorios. |

Un informe puede proceder de infraestructura ya existente. Consumir esa evidencia,
o invocar el análisis específico con un medio autorizado, no amplía el alcance a
administrar dicha infraestructura. La futura ejecución sigue sometida a los permisos
del host y del proyecto; esta redacción no inicia análisis ni acciones externas.

El límite de CI/CD es de esta evolución funcional. No elimina ni cambia por sí solo
los contratos de entrega que ya existen en el producto. Las comprobaciones de
compilación, regresión, interfaces y aceptación de una implementación siguen
aplicándose según su especificación, aunque no se diseñe aquí un pipeline.

Revisión respecto al borrador anterior: U12 delimita U9; los requisitos 021, 026 y
028 y la sección 7 se acotan a implementación e integración. Se conserva su identidad
para permitir revisar la evolución de la propuesta.

### 0.1 Resultado de la revisión crítica

| Carencia detectada | Mejora incorporada |
|---|---|
| La flexibilidad se describía como variación de nombres y revisiones de un recorrido casi fijo. | El proyecto configura pasos, condiciones, orden, agrupación y trabajo en paralelo; los ejemplos son orientativos. |
| Se versionaban las reglas sin concretar qué ocurre con las peticiones ya iniciadas. | Cada cambio decide su aplicación al trabajo nuevo y al abierto, con correspondencia de pasos y sin reiniciar por defecto. |
| Se mencionaban excepciones, pero predominaba el bloqueo y no se definían validación, efecto o vencimiento. | Se define un recorrido explícito para solicitar, validar, aplicar y resolver excepciones, conservando el resultado real de los controles. |
| Las consultas describían tareas aisladas sin exigir una vista del recorrido completo del proyecto. | El estado muestra el proceso configurado, avances, pendientes, excepciones y siguiente intervención de cada participante. |
| La explicación didáctica quedaba como orientación general y no como comportamiento comprobable. | Se exige una explicación al terminar cada paso y se añaden ejemplos y casos de aceptación del lenguaje y las recomendaciones. |
| «El plugin vela por el flujo» no concretaba cómo lo hace ni sus límites. | Se comprueba la transición antes de actuar, se registra su resultado y después se comunica; las acciones fuera del plugin mantienen sus límites de control. |
| Acumular controles podía convertir el trabajo en aprobaciones y registros repetitivos. | Se establecen criterios de agilidad comprobables, agrupación de decisiones, reutilización y comprobaciones proporcionales al cambio. |
| Había una descomposición preliminar antes de validar una propuesta funcional y técnica concreta. | Se retira ese plan preliminar del paquete vigente y se introduce una validación explícita de la propuesta antes de planificar. |
| La migración se trataba de forma genérica, sin destino v3 ni contrato de compatibilidad. | Se añade un diseño de evolución a v3 y una ruta explícita 2.x → 3.x con conservación y recuperación. |

## 1. Necesidades expresadas por el usuario

| Fuente | Necesidad |
|---|---|
| U1 | Un responsable recoge y especifica una petición; diferentes especialistas pueden implementar frontend, backend, BBDD u otros ámbitos de la misma funcionalidad. |
| U2 | El proyecto configura su flujo y responsables. Las nuevas mejoras y evolutivos deben seguir ese esquema de forma guiada y con controles de cumplimiento. |
| U3 | Otra persona puede asumir toda una implementación o una parte; ese cambio debe permitirse y quedar registrado. |
| U4 | Los nombres, cuentas asociadas y responsabilidades se gestionan y evolucionan con el tiempo. |
| U5 | El plugin debe servir tanto a una persona como a un equipo, desde un proyecto nuevo de alcance limitado hasta su mantenimiento evolutivo. |
| U6 | Estos aspectos deben formar parte de la trazabilidad de las implementaciones. |
| U7 | Cada nueva petición debe recorrer definición, planificación e implementación en una rama claramente identificada, y las tareas deben trazar esa relación. |
| U8 | La documentación producida en ramas diferentes debe poder integrarse sin confundir elementos cuyos identificadores coincidan. El problema afecta también a elementos distintos de las tareas. |
| U9 | El plugin debe integrarse de forma natural en el ciclo completo de desarrollo y sus controles reales, incluida la preparación y validación del PR de la funcionalidad. |
| U10 | Cuando se utilicen Sonar y el análisis de dependencias, deben formar parte de la implementación y comprobarse antes de dar por completada la tarea, adelantando la validación respecto al PR. |
| U11 | Un proyecto puede declarar que no utiliza Sonar o dependency check. Debe poder continuar, dejando esa decisión documentada en el proyecto. |
| U12 | Elaborar la propuesta funcional completa con todo lo anterior, excluyendo CI/CD e incluyendo expresamente Sonar y Dependency-Check en la fase de implementación. Esta precisión acota el alcance de U9. |
| U13 | Cada proyecto define su forma de trabajar y puede cambiarla durante su vida: una persona o equipo, controles utilizados, responsabilidades y recorrido SDD. |
| U14 | Permitir apartarse puntualmente del mecanismo fijado, con validación y registro del motivo. |
| U15 | Al consultar el estado, situar el proyecto en todo su proceso SDD, explicar pasos ejecutados y pendientes e indicar qué se espera del usuario. |
| U16 | Cada vez que se completa un paso, explicar dónde se está, qué se ha completado, qué falta y cómo continuar. |
| U17 | El plugin debe respetar y hacer cumplir el flujo, usar lenguaje sencillo y didáctico y recomendar cuando disponga de criterios suficientes. |
| U18 | El uso del plugin debe ser ágil y proporcionado; las pautas no deben convertir el desarrollo en un proceso pesado que anule su utilidad. |
| U19 | La propuesta funcional y técnica debe quedar clara y validarse antes de pasar a la planificación. El usuario debe saber que es el momento de validar y qué versión y alcance concretos se someten a su decisión. |
| U20 | Se plantea que esta evolución sea la versión 3 del plugin y se requiere poder pasar un proyecto de la línea 2.x a la 3.x. |
| U21 | Mejorar los siete puntos débiles identificados: agilidad operativa, comprensión de la validación, reutilización de aprobaciones, configuración manejable, coordinación cotidiana, calidad sin esperas innecesarias y migración sencilla. |
| U22 | Evitar que el propio plugin resulte pesado y consuma contexto de forma ineficiente durante su uso; mejorar la propuesta cuando sea necesario. |

El usuario plantea como alternativa usar identificadores temporales y asignar un
código final al integrar. Se conserva como alternativa de diseño, no como decisión
adoptada. También solicita valorar una solución que funcione con el repositorio.

La pregunta sobre reconocer al operador en Codex o Copilot deja abierta la elección
del mecanismo de identidad. No constituye una aprobación de una integración ni
permite equiparar una identidad declarada con una autenticada.

## 2. Hechos observados en la base actual

- La [planificación compartida](../../docs/V2-AUTHORING.md) contempla propietario,
  dependencias, integración y conflictos entre clones.
- La [continuidad SPEC/PLAN/TASK](../../docs/V2-SPEC-PLAN-TASK.md) relaciona la
  petición con requisitos, aceptación, pruebas, tareas, autoridad y ejecución.
- Los [workflows](../../docs/V2-WORKFLOWS.md) registran actor/rol y continuidad;
  los [límites](../../docs/V2-GUARDRAILS.md) aclaran que no autentican personas ni
  proporcionan un bloqueo distribuido o protección de rama automática.
- El [registro de autorización](../../scripts/v2_lifecycle.py) distingue
  explícitamente `identity_assurance: declared-not-authenticated`.
- El [schema de elementos](../../schemas/element-2.0.schema.json) ya distingue
  `uid` de `id`, y la guía de autoría define este último como alias legible.
  Sin embargo, las relaciones y rutas actuales utilizan esos alias: disponer de
  un UUID no convierte por sí solo todos los enlaces en referencias independientes.
- `next_id` en el [ciclo operativo](../../scripts/v2_lifecycle.py) calcula el
  siguiente número con lo visible en el clon. `record` deriva su UUID de proyecto
  y alias; los [recibos](../../scripts/v2_controls.py) usan el mismo patrón.
  Por inspección, dos clones de la misma base pueden generar el mismo alias y
  UUID para actuaciones independientes. No se ha ejecutado aquí una prueba de merge.
- El [renombrado de alias](../../scripts/v2_features.py) rechaza la reparación
  cuando afecta a elementos operativos o a sus referencias. `merge-preview`
  detecta cambios concurrentes, pero no garantiza compatibilidad semántica.
- Los [workflows actuales](../../docs/V2-WORKFLOWS.md) permiten determinadas reservas
  explícitas y diferencian cierre ordinario, cierre con reservas y resultado técnico.
  Su alcance no equivale a la vía general de excepciones propuesta en esta revisión.
- El [manifiesto actual](../../.codex-plugin/plugin.json) declara plugin 2.3.1. El
  [lector](../../scripts/v2_contract.py) utiliza schema 2.0 y admite métodos 2.0.0 y
  2.1.0. Son versiones diferentes. La [migración documentada](../../docs/V2-MIGRATION.md)
  cubre 1.5 → 2.0 y una actualización de método dentro de v2; no acredita una ruta v3.

Estos hechos son una base reutilizable. No prueban que la política de equipo y su
trazabilidad completa, descritas a continuación, estén implementadas.

La inspección estática para esta revisión muestra un punto de partida para optimizar:
las [skills](../../skills/lks-sdd-implement/SKILL.md) reúnen rutas v2 y legado en sus
entrypoints, aunque sus instrucciones indiquen utilizar solo la ruta aplicable. El
[contexto v2](../../scripts/v2_contract.py) ya selecciona por TASK y conserva contenido
literal; su respuesta incluye material normativo tanto en `normative` como en `elements`.
La propuesta debe aprovechar esa base y evitar duplicación en la vista para el modelo.
No se ha medido aquí el consumo real de una sesión, ni estos hechos demuestran que
el host cargue todas las skills o todo el manual en cada operación.

## 3. Requisitos propuestos y trazabilidad con la petición

| ID | Fuente | Comportamiento propuesto |
|---|---|---|
| REQ-EQT-001 | U2, U5, U13 | Configurar la forma de trabajo de cada proyecto: pasos, responsables, controles y condiciones de avance. Adaptar el recorrido real de las peticiones a esas decisiones; no limitar la configuración a renombrar un flujo fijo ni inventar asignaciones pendientes. |
| REQ-EQT-002 | U4, U6 | Mantener una identidad estable por miembro y conservar la evolución de nombres, cuentas, pertenencia y roles con su vigencia. Un cambio de cuenta no crea otra persona ni reatribuye sus actuaciones anteriores. |
| REQ-EQT-003 | U1, U2, U6 | Distinguir operador de la sesión, responsable de la tarea, ejecutores de cada porción, revisores, autorizadores e integrador. Poder acumular roles cuando la política lo permita sin perder la distinción de funciones. |
| REQ-EQT-004 | U1, U3, U6 | Registrar reasignaciones completas, delegaciones parciales y colaboraciones con origen, destino, alcance, motivo, estado entregado, pendientes, decisión habilitante y vigencia. Conservar qué realizó cada participante. |
| REQ-EQT-005 | U2, U4, U6 | Vincular cada ejecución y sus transiciones a la revisión aplicable de la política, las asignaciones y las decisiones. Reconstruir el contexto vigente al actuar sin deducirlo de la configuración actual. |
| REQ-EQT-006 | U3, U4, U6, U13 | Evaluar el impacto de cambios de equipo, política o asignación sobre el trabajo abierto. Acordar qué continúa con las reglas anteriores y qué adopta las nuevas; reconciliar solo lo afectado, conservar historia y reutilizar autorizaciones vigentes. |
| REQ-EQT-007 | U1, U6 | Trazar las contribuciones de especialistas hasta los requisitos, interfaces y criterios que cubren, y asignar explícitamente la integración. La suma de resultados de componentes no acredita por sí sola la funcionalidad conjunta. |
| REQ-EQT-008 | U5 | Adaptar el flujo a trabajo individual o de equipo y a creación, entrega acotada, evolución o mantenimiento. Reutilizar las decisiones vigentes y definir solo los ámbitos afectados por cada petición. |
| REQ-EQT-009 | U2, U6, U14, U17 | Comprobar las reglas aplicables al iniciar, reanudar, revisar, verificar, cerrar e integrar. Permitir la vía ordinaria o la excepción validada de esa transición; ante incumplimiento, explicar causa, responsable y opciones para continuar sin dar el paso por realizado. |
| REQ-EQT-010 | U4, U6 | Registrar la procedencia y grado de comprobación de la identidad del operador. Separar identidad declarada, cuenta observada e identidad autenticada, sin convertir ninguna automáticamente en autoridad sobre el proyecto. |
| REQ-EQT-011 | U3, U5, U6 | Reconstruir el trabajo al cambiar de compañero, chat, clon o host desde los artefactos del proyecto. Una sesión nueva no hereda por defecto la identidad del operador anterior. |
| REQ-EQT-012 | U6 | Ofrecer una consulta legible de quién pidió, definió, autorizó, implementó, revisó, integró y aceptó cada cambio, con reglas, relevos, resultados y pendientes enlazados a sus fuentes históricas. |
| REQ-EQT-013 | U7, U14 | Asociar cada petición, en su recorrido ordinario, a una rama de trabajo identificada, un destino configurado y una base Git concreta antes de materializar su documentación. Conservar esos vínculos y registrar cambios; una excepción a la rama prevista mantiene identificables el trabajo y su base real. |
| REQ-EQT-014 | U1, U3, U7 | Permitir ramas de especialistas o tareas vinculadas a la misma petición, con porciones y destinos explícitos. Mantener la trazabilidad cuando una tarea necesite varias ramas o una rama contenga varias tareas del mismo cambio. |
| REQ-EQT-015 | U6, U7 | Registrar repositorio, petición, tareas, rama, base de código y sujeto exacto comprobado, junto con el resultado de integración. Un nombre de rama no sustituye los identificadores del commit, árbol o artefacto observado. |
| REQ-EQT-016 | U8 | Crear una identidad permanente y resistente a colisiones por elemento nuevo, también para autorizaciones, ejecuciones, checkpoints, evidencia, decisiones y recibos. Conservarla en reintentos, cambios de estado, ramas e integración; una entidad heredada conserva su identidad y una creación independiente recibe otra. |
| REQ-EQT-017 | U6, U8 | Separar la identidad de los códigos de presentación. Resolver relaciones e historia sin ambigüedad aunque coincidan alias visibles; no renumerar registros cerrados ni alterar evidencia o autorizaciones para facilitar un merge. |
| REQ-EQT-018 | U2, U7, U8 | Comprobar rama, base, identidades, relaciones, alcance y conflictos antes de escribir y al integrar. Diferenciar alias repetidos, modificaciones concurrentes de un mismo elemento, duplicidad de intención y contradicciones compartidas. Un merge textual limpio no equivale a aceptación. |
| REQ-EQT-019 | U5, U8 | Permitir crear elementos en clones independientes sin reservar un contador central. Evitar puntos de escritura global innecesarios y reconstruir el índice desde documentos canónicos reconciliados; nunca resolver conflictos con la última copia del índice. |
| REQ-EQT-020 | U6, U7, U8 | Conservar procedencia tras merge, squash, rebase, cherry-pick, renombrado o retirada de ramas. Comprobar de nuevo la aplicabilidad de la evidencia sobre el resultado integrado y conservar historia de cambios cancelados cuando proceda. |
| REQ-EQT-021 | U2, U10, U12 | Configurar por proyecto Sonar y Dependency-Check para la implementación, con uso/no uso, ámbito, responsable, reglas de aceptación, fuente de resultados y condiciones de reutilización. Resolver su aplicabilidad a cada tarea y funcionalidad antes de ejecutar. |
| REQ-EQT-022 | U10 | Integrar los controles Sonar y de dependencias utilizados en el ciclo implementar, comprobar y corregir. Exigir sus resultados finales y aplicables antes del cierre ordinario de la tarea cuando la política los declare obligatorios; no posponer su primera comprobación hasta la aprobación del PR. |
| REQ-EQT-023 | U11 | Permitir que el proyecto declare cada herramienta o control como no utilizado, con decisión, motivo, alcance y vigencia. Esa situación no bloquea por su mera ausencia ni se presenta como control superado. Desconocimiento, falta de acceso o fallo no equivalen a no utilización acordada. |
| REQ-EQT-024 | U6, U9, U10 | Separar decisión de uso, aplicabilidad, obligatoriedad, estado de ejecución y resultado. Conservar pendientes, errores técnicos, fallos de calidad, excepciones y resultados reutilizados sin convertirlos en aprobaciones implícitas. |
| REQ-EQT-025 | U6, U9, U10 | Relacionar cada comprobación con tareas cubiertas, código/artefacto observado, base pertinente, configuración y reglas, herramienta, fuente, ejecución, fecha y datos externos cuando influyan. Una ejecución puede acreditar varias tareas solo si cubre realmente sus obligaciones y alcance. |
| REQ-EQT-026 | U7, U10, U12 | Preparar la información SDD del PR y comprobar la vigencia de evidencias sobre el candidato conjunto. Reutilizar resultados aplicables y repetir los controles afectados por cambios de código, destino, configuración, composición o datos externos; no afirmar aprobación del PR ni cumplimiento de CI/CD por sumar tareas completadas. |
| REQ-EQT-027 | U2, U9, U11 | Versionar cambios en controles, umbrales, exclusiones, supresiones y excepciones con motivo, responsable y alcance. Una incidencia técnica no desactiva automáticamente un control y una modificación de política no reescribe el resultado histórico. |
| REQ-EQT-028 | U5, U10, U12 | Aplicar comprobaciones proporcionales al cambio y separar tarea implementada, verificación, cierre, integración y aceptación funcional. Reutilizar medios disponibles sin convertir esos resultados en aprobación de PR o de entrega. |
| REQ-EQT-029 | U2, U4 | Configurar quién puede gestionar miembros, asignar funciones, modificar políticas y aprobar excepciones. La nueva regla no puede otorgarse a sí misma la autoridad necesaria para ser aprobada. |
| REQ-EQT-030 | U4, U6 | Resolver la vinculación de operador y miembro antes de una actuación atribuible. Solicitar aclaración ante ambigüedad y reutilizar una vinculación vigente sin convertirla en usuario global del repositorio. |
| REQ-EQT-031 | U1, U2 | Definir tareas con alcance, responsable, criterios, pruebas, interfaces, dependencias, controles y revisión. Planificar la integración conjunta cuando intervienen varias porciones, sin crear tareas vacías para especialidades ausentes. |
| REQ-EQT-032 | U2, U5, U13, U14 | Guiar las transiciones del flujo configurado, con sus condiciones ordinarias o excepción validada y sin falsear lo realizado. Permitir revisión, corrección, pausa, cancelación y replanificación con causas y efectos explícitos; una etiqueta de estado no elude condiciones. |
| REQ-EQT-033 | U3, U6 | Formalizar los relevos con propuesta, decisión y aceptación del destinatario según política; activar una asignación inequívoca y conservar el estado anterior. Registrar actuaciones concurrentes incompatibles como conflicto por resolver. |
| REQ-EQT-034 | U2, U5, U15, U16, U17 | Mostrar en lenguaje sencillo la situación dentro del proceso del proyecto, qué se completó, qué falta, quién debe actuar y qué se espera del usuario. Recomendar el siguiente paso cuando haya base y permitir avanzar el trabajo independiente autorizado sin repetir decisiones vigentes. |
| REQ-EQT-035 | U10, U12 | Trazar los hallazgos, correcciones y comprobaciones posteriores de Sonar y Dependency-Check. Distinguir deuda previa, falso positivo y riesgo aceptado; ampliar SPEC/PLAN/TASK si una corrección exige nuevo alcance. |
| REQ-EQT-036 | U12 | Mantener CI/CD fuera de esta evolución. Admitir evidencia de un análisis existente sin diseñar pipelines, administrar despliegues ni incorporar capacidades ejecutables nuevas fuera de las seis skills. |
| REQ-EQT-037 | U4, U5, U8 | Adoptar las nuevas reglas mediante una transición explícita y compatible: conservar historia y referencias, detectar ambigüedad heredada y no inventar identidad, aprobaciones o políticas pasadas. |
| REQ-EQT-038 | U10, U12 | Registrar errores, esperas, cancelaciones y reintentos de análisis sin duplicar hechos ni declarar éxito por agotamiento de reintentos. Poder reanudar con una ejecución identificada y resolver un bloqueo técnico. |
| REQ-EQT-039 | U4, U5 | Mantener el mismo contrato funcional en Codex y Copilot, diferenciando capacidades disponibles y evidencia observada por host. Una limitación de herramienta no rebaja las exigencias de identidad o calidad. |
| REQ-EQT-040 | U6, U8, U10 | Conservar evidencias recuperables y procedencia suficiente sin credenciales en el repositorio. Una ruta, hash o enlace que no permite recuperar el contenido no basta por sí solo; un informe perdido no se presenta como verificado de nuevo. |
| REQ-EQT-041 | U13 | Configurar pasos agrupados, opcionales o condicionados, orden compatible con sus dependencias y trabajo en paralelo. Mantener su relación con las obligaciones de la petición y distinguir lo no aplicable de lo omitido excepcionalmente. |
| REQ-EQT-042 | U13 | Validar y registrar un cambio de proceso con vigencia, impacto y correspondencia entre pasos anteriores y nuevos. Actualizar el recorrido visible y el trabajo abierto afectado sin reinicios, cierres ni invalidaciones masivas por defecto. |
| REQ-EQT-043 | U14 | Ofrecer una vía de excepción para reglas de proyecto: indicar motivo, alcance, efecto solicitado, validador competente y condiciones. Permitir el avance o cierre autorizado con sus límites; conservar omisiones, fallos y obligaciones aplazadas sin presentarlos como comprobaciones superadas. |
| REQ-EQT-044 | U15 | Construir el estado desde los documentos y evidencias disponibles y el flujo vigente de cada petición. Mostrar recorrido completo, pasos completados/en curso/pendientes, revisiones, excepciones y acciones de usuario, distinguiendo proyecto, petición y tarea y las limitaciones de observación. |
| REQ-EQT-045 | U16 | Comunicar proactivamente cada paso del proceso confirmado como completado y cada avance por excepción: situación, resultado, pendientes y continuación. Aplicarlo en las seis skills; no supeditarlo a que el usuario pida estado ni confundir un comando terminado con un paso completado. |
| REQ-EQT-046 | U17 | Utilizar nombres comprensibles y explicar términos necesarios. Recomendar una opción con una razón basada en el proyecto y expresar incertidumbre si faltan datos; separar recomendación, decisión y autorización, sin imponer una elección universal. |
| REQ-EQT-047 | U2, U17 | Comprobar la transición contra la revisión vigente del proceso, asignación, autorización y evidencia; aplicar solo el cambio válido y confirmar su persistencia antes de anunciar finalización. Detectar divergencias manuales o concurrentes sin aceptar la última escritura como aprobación. |
| REQ-EQT-048 | U5, U13, U17 | Mantener una experiencia proporcionada: configuración guiada mínima, funciones acumulables donde proceda, decisiones agrupadas, autorizaciones reutilizables y detalle técnico bajo demanda. Si el siguiente paso ya está autorizado, explicarlo y continuar sin pedir un permiso redundante. |
| REQ-EQT-049 | U18 | Comprobar la agilidad con recorridos representativos: cero confirmaciones redundantes, ninguna comprobación costosa repetida sin causa y registros proporcionales a hitos. Agrupar decisiones relacionadas y ampliar el proceso solo por impacto, riesgo o elección expresa. |
| REQ-EQT-050 | U19 | Presentar antes de planificar una propuesta funcional y técnica concreta: objetivo, alcance incluido/excluido, comportamiento, solución técnica, cambios previstos, criterios de aceptación, impacto y decisiones pendientes. Una lista genérica de temas no satisface este requisito. |
| REQ-EQT-051 | U19 | Validar una revisión identificada y recuperable de esa propuesta, con alcance y documentos exactos, persona/función que decide y resultado. Anunciar que es el momento de validarla y qué permite la aceptación; no inferirla del silencio o de comentarios ambiguos. |
| REQ-EQT-052 | U18, U19 | Revalidar solo la parte materialmente modificada y sus dependencias. Conservar las decisiones anteriores y mostrar el cambio; una aprobación de otra revisión no se transfiere silenciosamente ni exige reiniciar lo independiente. |
| REQ-EQT-053 | U19 | Elaborar el PLAN/TASK ejecutable después de validar la propuesta del alcance correspondiente. Distinguir esa validación de la aprobación del plan y la autorización de implementación; una exploración previa no es un plan comprometido. |
| REQ-EQT-054 | U20 | Diseñar la evolución como candidata v3, distinguiendo versión del plugin, método y formato documental. No cambiar versiones activas, instalar, publicar o migrar por el mero hecho de aprobar la definición. |
| REQ-EQT-055 | U20 | Ofrecer diagnóstico y conversión explícita de proyectos 2.x a 3.x según su formato/método reales y runtime fijado. Cubrir los orígenes 2.x documentados mediante pruebas; conservar y explicar los casos desconocidos sin adivinar transformaciones. |
| REQ-EQT-056 | U20 | Migrar mediante vista previa exacta, autorización, conservación de originales, aplicación recuperable y comprobación del resultado. Una interrupción, cambio del origen o colisión no debe perder trabajo ni presentar un corte parcial como completado. |
| REQ-EQT-057 | U18, U19, U20 | Conservar especificaciones, identidades, planes, historia, evidencia y decisiones recuperables. Reconciliar solo el trabajo activo afectado y reutilizar una validación anterior únicamente si se acredita su correspondencia; no inventar una aprobación v3 por convertir documentos. |
| REQ-EQT-058 | U20 | Separar instalación del plugin y migración del proyecto, impedir escrituras incompatibles sobre un checkout migrado y gestionar la incorporación de ramas o clones 2.x pendientes. Permitir recuperación sin sobrescribir cambios posteriores ni prometer un bloqueo distribuido. |
| REQ-EQT-059 | U18, U21 | Ofrecer un recorrido breve con presupuesto de intervenciones, documentos de lectura y repeticiones; distinguir configuración inicial, desarrollo y aceptación. Comprobarlo con personas y explicar toda desviación del presupuesto mediante una causa observable. |
| REQ-EQT-060 | U19, U21 | Presentar la validación como una decisión comprensible: situación actual, comportamiento y solución propuestos, ejemplos, consecuencias, exclusiones y efecto de aceptar. Separar la revisión funcional y técnica por responsabilidad, sin exigir al usuario dominar los metadatos internos. |
| REQ-EQT-061 | U18, U19, U21 | Identificar unidades de aprobación funcional/técnica por porción y dependencias; componer un paquete con revisiones de unidad distintas sin trasladar una aprobación a contenido modificado. Reutilizar lo idéntico y no afectado con comprobación explícita; el juicio del modelo no equivale a una aprobación. |
| REQ-EQT-062 | U13, U14, U21 | Ofrecer recorridos iniciales concretos y editables, separar garantías del método y reglas configurables, resolver la precedencia y validar que el proceso puede terminar. Una configuración contradictoria explica su corrección mínima antes de activarse. |
| REQ-EQT-063 | U1, U2, U7, U21 | Coordinar decisiones entre ramas mediante una referencia compartida y revisiones observadas; distinguir preparado localmente, compartido y recibido. Definir actualización, trabajo sin conexión y recepción de cambios materiales sin exigir una sincronización por cada comando. |
| REQ-EQT-064 | U10, U11, U18, U21 | Comprobar la viabilidad del medio de análisis antes de comprometer el flujo, agrupar controles por entradas y ámbito y distinguir dependencias de contrato, resultado disponible y resultado verificado. Permitir trabajo autorizado compatible durante una espera sin presentar la tarea como cerrada. |
| REQ-EQT-065 | U18, U20, U21 | Ofrecer una matriz de orígenes de migración y un resumen accionable antes/después: convertido automáticamente, conservado, decisiones requeridas y tareas que pueden continuar. Evitar revisar historia cerrada y medir las intervenciones necesarias en proyectos sencillos y de equipo. |
| REQ-EQT-066 | U18, U22 | Cargar progresivamente las instrucciones y fuentes necesarias para la operación, versión, rol y porción actuales. Mantener las seis skills descubribles, evitar instrucciones de rutas inactivas y no enviar al modelo inventarios, historia, informes o manuales completos por defecto. |
| REQ-EQT-067 | U19, U22 | Conservar íntegros los contratos, restricciones, aceptación y evidencia necesarios para decidir o implementar la porción. Seleccionar con procedencia y dependencias; la ausencia de enlaces no acredita irrelevancia. Ampliar ante incertidumbre y no declarar suficiencia por caber en un presupuesto. |
| REQ-EQT-068 | U18, U22 | Producir contexto derivado sin duplicación y reutilizarlo solo con fuentes y capacidad de sesión comprobadas. Invalidar por cambios relevantes, altas/bajas de fuentes, dependencias, autoridad y entorno. Tras pérdida de contexto, recuperar las obligaciones literales necesarias sin usar resúmenes o huellas como sustitutos. |
| REQ-EQT-069 | U18, U22 | Medir el consumo de la operación y tarea completas, con presupuestos iniciales de sobrecarga, lecturas, expansiones, reintentos y resultados. Comparar ahorro y calidad con el flujo actual; no acreditar eficiencia si aumenta omisiones o errores ni afirmar ahorro facturado sin datos del host. |

## 4. Información propuesta para cada implementación

La trazabilidad organizativa y la validación propuesta amplían la cadena existente:

`petición → propuesta funcional/técnica → validación explícita → PLAN/TASK → autorización → ejecución/corrección → evidencia → revisión/cierre → integración/aceptación funcional`

Esta cadena expresa relaciones funcionales, no un orden universal entre aceptación
e integración: el proyecto fija ese orden. La entrega operacional posterior queda
fuera de esta propuesta.

Cada registro relevante enlaza el contexto que le corresponde; no se copia un
directorio completo de personas en cada tarea ni se crea otro tablero canónico.

| Información | Qué debe permitir reconstruir |
|---|---|
| Identidades y funciones | Miembro estable, función ejercida en esa operación, procedencia de identidad y grado de comprobación. |
| Política aplicable | Revisión y vigencia de las reglas del proyecto para la porción y etapa ejecutadas. |
| Propuesta validada | Revisión exacta funcional/técnica, alcance aceptado, decisión, reservas y correspondencia de las tareas posteriores. |
| Recorrido aplicable | Versión del proceso de la petición, pasos que agrupa y correspondencia con las obligaciones de cada tarea. |
| Asignación y contribución | Responsable, participantes, parte realizada por cada uno y límites de su intervención. |
| Autoridad | Decisión o autorización que habilitó la operación, su alcance y su relación con la política. |
| Relevos | Qué se transfirió, entre quiénes, cuándo, por qué, desde qué estado y con qué pendientes. |
| Base de trabajo | Revisión contractual, base de código y contexto de ejecución que representan el trabajo entregado. |
| Trabajo en Git | Repositorio, petición, ramas de origen y destino, tareas vinculadas, base observada, revisiones comprobadas y correspondencia con el resultado integrado; enlace a PR/MR cuando exista. |
| Comprobaciones y decisiones | Evidencia exacta, resultado, revisión, reservas o excepciones y aceptación cuando corresponda. |
| Política de controles | Qué se utiliza o no, para qué ámbito y etapa, con qué obligatoriedad y condiciones. Decisiones, exclusiones, supresiones y excepciones aplicables. |
| Excepción puntual | Regla afectada, motivo, alcance, validación, efecto sobre el avance/cierre, vigencia y pendientes que conserva. |
| Procedencia del análisis | Herramienta y reglas, ejecución y fuente del resultado, sujeto y base analizados, tareas cubiertas, fecha, antigüedad de datos externos y motivo de reutilización cuando exista. |
| Integración funcional | Responsable, contribuciones integradas, comprobación conjunta y aceptación del alcance; enlace al PR/MR si existe, sin asumir su aprobación. |

Debe distinguirse el momento de la actuación, el de su registro y la vigencia de
una decisión cuando difieran. Una incorporación tardía se identifica como tal;
no puede fingir autorización previa ni conocimiento histórico inexistente.

La representación concreta en elementos, relaciones, revisiones y registros queda
pendiente de diseño. Los Markdown del consumidor siguen siendo canónicos y el
índice solo facilita su localización. Los registros cerrados y sus referencias se
conservan; las correcciones se añaden con procedencia, sin sobrescribir la historia.

## 5. Evolución y continuidad propuestas

Un cambio de nombre o cuenta mantiene la identidad del miembro. La baja impide
nuevas asignaciones ordinarias desde su vigencia y obliga a resolver el trabajo
pendiente afectado; no borra sus contribuciones ni invalida automáticamente sus
aprobaciones pasadas.

Una delegación parcial delimita una porción verificable y su integración. Queda
propuesto representarla mediante una TASK vinculada cuando tenga aceptación o
ejecución independiente; una ayuda puntual se registra como contribución en la
misma TASK. La descomposición redistribuye obligaciones y evita duplicar su cobertura.
Ayudar o revisar no cambia por sí solo la responsabilidad principal ni concede
autoridad.

Un cambio de política declara cómo se aplica al trabajo futuro y al ya iniciado.
Se analiza el efecto sobre autorizaciones, separación de funciones, revisiones y
pendientes. No se supone que todo continúa ni que todo debe volver a aprobarse.
Un cambio de alcance o interfaz compartida requiere su propia reconciliación.

La identidad activa de una sesión no se guarda como un usuario global compartido
por el repositorio. La vinculación personal puede facilitar nuevos chats, pero
debe reconciliar cambios de cuenta, entorno o persona. No se almacenan credenciales
en los registros de trazabilidad; se limita la información de cuentas a la necesaria.

### 5.1 Configuración funcional del proyecto

La configuración inicial recoge las decisiones necesarias para el siguiente paso.
Una consulta o un borrador pueden conservar pendientes. Para iniciar una actuación
se exigen únicamente las decisiones críticas de su ámbito. Se proponen perfiles
orientativos que el responsable confirma; no se activan por inferencia del modelo.

| Bloque | Contenido mínimo propuesto |
|---|---|
| Contexto | Proyecto nuevo o existente, trabajo individual o equipo y momento de su vida: alcance acotado, evolución o mantenimiento. Son dimensiones independientes. |
| Gobierno | Responsable inicial confirmado y funciones que pueden cambiar equipo, flujo, asignaciones, controles y excepciones. |
| Miembros | Identidad estable, nombre de presentación, pertenencia activa/inactiva, cuentas y funciones con vigencia. |
| Flujo | Pasos, condiciones de aplicación, agrupación, dependencias, orden, paralelismo, revisión y condiciones de cierre. |
| Asignación | Reglas por ámbito, responsable de petición e integración; requisitos de delegación, aceptación y sustitución. |
| Identidad | Fuentes admisibles, nivel de comprobación exigido por operación y comportamiento ante ausencia o contradicción. |
| Git | Identidad del repositorio, destino, convención de ramas, base de trabajo y reglas de integración. |
| Calidad | Configuración independiente de Sonar y Dependency-Check descrita en la sección 7. |
| Excepciones | Quién puede validar una desviación, qué puede autorizar, límites y sustitución si no está disponible; procedimiento para casos no previstos. |
| Historia | Vigencia de la política, aplicación al trabajo abierto, conservación de evidencias y tratamiento de datos personales. |

La incorporación inicial no puede depender circularmente de un administrador aún
inexistente. Se propone una decisión explícita de la persona responsable del proyecto
que documente la configuración y la primera asignación, con la garantía de identidad
realmente disponible. No acredita por sí misma un cargo corporativo autenticado.
Después, cada cambio se evalúa contra la política y autoridad anteriores.

La configuración se guarda en Markdown versionado del proyecto. La organización
puede aportar plantillas de referencia; su adopción es explícita, con versión y
adaptaciones visibles. Esta propuesta no crea un directorio corporativo compartido
ni sincroniza automáticamente configuraciones entre repositorios.

Los perfiles son puntos de partida editables. Un proyecto puede agrupar definición
funcional y técnica en «Preparar la propuesta», separar revisión técnica y
funcional, trabajar en paralelo por especialidades o utilizar un recorrido reducido
para cambios pequeños. Cada variante explica cuándo aplica y qué obligaciones cubre.
No se crean pasos vacíos para conservar un esquema universal. Las dependencias deben
permitir un recorrido ejecutable; volver a corregir un resultado es un retorno previsto,
no una dependencia circular imposible de resolver.

Para cada paso se define, en términos comprensibles, su finalidad, cuándo aplica,
quién interviene, qué necesita para empezar, qué resultado permite terminarlo y
qué puede hacerse después. El grado de detalle se ajusta al proyecto: estos datos
pueden compartirse entre pasos y no requieren una ficha o aprobación por cada campo.

Configurar el proceso cambia cómo se organiza el trabajo. Las necesidades del cliente
siguen teniendo su especificación y cualquier cambio de alcance se registra como tal.
Las garantías comunes son conservar la historia, atribuir actuaciones y decisiones
con honestidad, disponer de autoridad suficiente y no presentar como comprobado lo
que no se ha comprobado. Las reglas de organización del proyecto pueden revisarse o
tratarse mediante la excepción validada de la sección 5.8.

La libertad de presentación no elimina la validación funcional y técnica antes de
planificar. Aunque la interfaz agrupe actividades bajo un mismo nombre, esa decisión
conserva su momento, su alcance y el resultado que permite pasar a planificación.

#### Recorridos iniciales utilizables

Estos son valores propuestos para confirmar o adaptar, no políticas activadas por el
modelo. No son tres contratos incompatibles: usan el mismo método y pueden evolucionar.

| Recorrido | Organización propuesta | Decisiones e integración |
|---|---|---|
| Individual breve | Una persona acumula responsabilidad funcional, técnica y ejecución. Una ficha funcional/técnica y una rama por petición. | Valida la propuesta; después aprueba el plan y autoriza su ejecución conjuntamente. Revisión final propia si el proyecto la exige. |
| Equipo coordinado | Responsable de petición, participantes por las especialidades necesarias e integrador identificado. Ramas de contribución solo si hay trabajo paralelo. | Cada función valida su porción; una persona con varias funciones puede agrupar su respuesta. Contratos compartidos antes de repartir trabajo dependiente. |
| Equipo con revisión separada | El recorrido de equipo añade revisión independiente en los ámbitos declarados, con sustitución prevista. | El ejecutor no sustituye al revisor exigido. Se agrupan sus decisiones por paquete; no se exige que revise cada comando o registro. |

Proyecto nuevo o existente y mantenimiento son dimensiones adicionales. En mantenimiento
se parte del comportamiento y decisiones vigentes, se describe la diferencia y su
regresión; no se vuelve a especificar la aplicación completa. El recorrido breve se
recomienda para un cambio acotado sin nueva tecnología, migración de datos, permisos o
contrato compartido. Ante esos impactos se propone ampliar solo la parte necesaria.
El tamaño del diff por sí solo no clasifica el riesgo y la recomendación no cambia
la política sin decisión del proyecto.

La primera configuración se presenta en una sola propuesta legible: recorrido,
responsabilidades, destino Git y decisiones independientes sobre Sonar y
Dependency-Check. Se reutilizan los datos ya confirmados. Solo se pregunta lo que
falta para el siguiente paso; umbrales, sustituciones especiales y otras ampliaciones
se concretan al ser aplicables. No se inventa una decisión de no uso para abreviar.

#### Garantías, reglas configurables y precedencia

| Capa | Regla de resolución propuesta |
|---|---|
| Garantías comunes | Historia honesta, atribución con garantía real, validación del contenido antes de planificar y autorización del plan antes de ejecutar. No admiten una excepción que falsifique hechos o sustituya una decisión ausente. Los permisos del host o de terceros siguen sus propios límites. |
| Autoridad vigente | Las pertenencias, funciones y revocaciones conocidas en la referencia de coordinación determinan quién puede decidir ahora. Una política antigua de petición no restaura una función revocada. |
| Proceso de la petición | Se aplica su revisión acordada. Una política nueva solo la sustituye con una decisión que incluya esa petición y su momento de aplicación. |
| Excepción concreta | Modifica únicamente reglas configurables identificadas, durante su vigencia y con autoridad suficiente. Todo lo demás conserva su condición ordinaria. |

Entre decisiones incompatibles no gana la última fecha ni la última escritura.
Se requiere una sustitución explícita o reconciliación por la función competente.
La configuración se comprueba antes de activarse: responsables existentes, sustitución
para revisiones exigidas, condiciones expresables, dependencias ejecutables, salida de
las esperas y ruta hasta el cierre. Los ciclos de corrección tienen condiciones de
retorno; no se admite una dependencia que exija tener el mismo resultado terminado
para poder empezarlo. Ejemplo: en un proyecto individual una revisión independiente
sin revisor ni sustituto exige corregir esa regla o incorporar al revisor; no se inventa.

### 5.2 Funciones y responsabilidades

Las siguientes son funciones propuestas, no puestos obligatorios ni cuentas reales.
Una persona puede ejercer varias si la política lo permite. El ámbito de una función
puede ser el proyecto, una petición o una especialidad concreta.

| Función | Responsabilidad | Límite propuesto |
|---|---|---|
| Solicitante/interlocutor | Aportar la necesidad y aclarar el resultado esperado. | No recibe permisos de implementación o aprobación por ser origen de la petición. |
| Responsable de proyecto | Confirmar el flujo, gestionar responsabilidades y decidir cambios de gobierno. | No puede borrar historia ni atribuirse retroactivamente una aprobación. |
| Responsable funcional | Especificar la petición y criterios, y coordinar aclaraciones con el solicitante. | Una definición no autoriza por sí sola a programar. |
| Responsable de tarea | Responder por el alcance, coordinar contribuciones y preparar su revisión. | Delegar una parte no transfiere automáticamente toda la responsabilidad. |
| Ejecutor especialista | Implementar la porción asignada y corregir los hallazgos correspondientes. | No amplía alcance ni modifica controles para conseguir un resultado satisfactorio. |
| Revisor | Comprobar el resultado técnico o funcional del ámbito asignado. | La política determina si puede revisar su propio trabajo. |
| Autorizador | Habilitar una actuación o excepción concreta dentro de sus atribuciones. | Identidad, asignación y autorización se verifican por separado. |
| Integrador | Coordinar interfaces, incorporar contribuciones y comprobar el resultado conjunto. | No presume aceptación funcional por ausencia de conflictos Git. |

El operador del chat es quien utiliza la herramienta en ese momento; puede desempeñar
una de estas funciones o estar consultando en nombre de otra persona. Se registran
ambos contextos cuando proceda, sin atribuir al operador decisiones del compañero.
La herramienta/agente se registra como medio de trabajo, no como una persona del
equipo ni como el revisor humano requerido.

Una matriz de reglas puede exigir revisión por otra persona para ciertos cambios.
El perfil individual permite acumular funciones donde se haya acordado; si una regla
exige independencia, tener un único miembro no elimina esa condición. Se permite
configurar una alternativa autorizada antes de la actuación, sin inventar revisores.

### 5.3 Identidades, cuentas y sesión

Cada miembro conserva una identidad estable del proyecto. Sus cuentas indican
proveedor, identificador disponible, alias visible, vigencia y procedencia. Cuando
el proveedor ofrezca un identificador estable comprobable, se utiliza para resolver
la cuenta; un nombre visible o correo coincidente no basta para unir personas.

Al comenzar o reanudar trabajo atribuible, el plugin propone resolver el operador:

1. Leer las reglas de identidad del proyecto y la vinculación local vigente, si existe.
2. Contrastar las cuentas observables con los miembros del ámbito, sin presuponer
   que el host expone su identidad autenticada al plugin.
3. Si no hay correspondencia inequívoca, pedir identificación o aclaración. Conservar
   el nivel real: declarado, cuenta observada o autenticación comprobada mediante un
   mecanismo expresamente admitido.
4. Comprobar vigencia de pertenencia, función y autorización para la operación.
5. Registrar el contexto utilizado; reutilizarlo mientras siga siendo aplicable.

La consulta ordinaria puede continuar sin atribuir una actuación formal. Una cuenta
del sistema operativo o la configuración de autor de Git son indicios, no prueba
automática de quién opera. La sesión de Codex o Copilot tampoco acredita por sí sola
una función del proyecto. Si se exige una garantía que no está disponible, se explica
el bloqueo; no se rebaja a identidad declarada silenciosamente.

La vinculación de sesión se mantiene fuera de los archivos compartidos y se revisa
ante cambio de cuenta, persona, host, proyecto o política relevante. No se infiere
que quien abre un chat heredado es su operador anterior. Una importación futura de
cuentas o una fusión de miembros duplicados necesita revisión y correspondencias
trazadas; una cuenta reutilizada no reatribuye actuaciones pasadas.

### 5.4 Reasignación, delegación y colaboración

Se proponen tres operaciones: reasignar una tarea completa; delegar una porción
verificable; registrar colaboración sin cambiar al responsable. Cada una identifica
origen, destinatario, alcance, motivo, versión del trabajo, pendientes y reglas.

Un relevo tiene las situaciones conceptuales propuesto, aceptado/activo, rechazado,
cancelado y finalizado. Su activación necesita la decisión habilitante y la aceptación
del destinatario que exija la política. El proponente no puede simular esa aceptación.
Puede preacordarse una asignación directa; para ausencias se admite una sustitución
autorizada por la función prevista, que se registra como tal.

Hasta activarse el relevo, la responsabilidad anterior permanece visible. La activación
del nuevo alcance y el fin del anterior se registran conjuntamente sobre una revisión
conocida. Si dos clones producen relevos incompatibles, ambos hechos se conservan y
se bloquea la porción afectada hasta reconciliar; no se afirma exclusión distribuida.

El paquete de continuidad incluye SPEC y TASK aplicables, rama/base, cambios realizados,
checkpoint, evidencia, hallazgos Sonar/Dependency-Check, trabajo pendiente y quién
integra. La aceptación del relevo no amplía por sí sola la autorización para implementar.
Las comunicaciones o asignaciones en servicios externos no forman parte del relevo
local y no se envían automáticamente.

### 5.5 Flujo funcional y condiciones de avance

Las etapas siguientes son una propuesta de experiencia. Sus nombres no crean estados
nuevos del schema: su traducción al modelo vigente se concretará en el diseño técnico.
Este recorrido es orientativo. El proyecto puede agrupar, separar, condicionar y
ordenar pasos según sus necesidades, conservando las dependencias y la cobertura de
lo acordado. No tiene que mostrar todas estas filas como fases independientes.

| Etapa/transición | Condiciones para avanzar | Resultado visible |
|---|---|---|
| Recoger y definir | Petición identificada; responsable y rama/base resueltos al materializar; alcance y dudas distinguidos. | SPEC y criterios, con pendientes explícitos. |
| Validar la propuesta | Propuesta funcional y técnica concreta, revisión identificada y decisión de las personas competentes sobre ese alcance. | Propuesta aceptada para planificar, cambios solicitados o validación parcial explícita. |
| Planificar | Propuesta del alcance validada; cobertura, tareas, responsables, dependencias e interfaces coherentes con ella. | PLAN/TASK que se presenta para aprobación y autorización de ejecución. |
| Iniciar o reanudar | Identidad y función suficientes, autorización vigente, rama/base y asignación correctas, dependencias satisfechas. | Porción activa y límites de actuación. |
| Implementar y corregir | Código dentro del alcance; pruebas y controles aplicables; trazabilidad de contribuciones. | Resultado y hallazgos, con ciclos de corrección registrados. |
| Revisar y verificar | Resultado exacto disponible, controles finales válidos y revisiones exigidas, conforme al orden del proyecto. | Evidencia técnica y decisión humana separadas. |
| Cerrar tarea | Condiciones de cierre satisfechas o excepción de cierre expresamente validada, con documentación y relevos reconciliados. | Tarea cerrada por la vía ordinaria o aceptada con reservas explícitas; sus comprobaciones conservan el resultado real. |
| Integrar la funcionalidad | Contribuciones compatibles, dependencias y referencias completas, responsable de integración y evidencia conjunta. | Resultado integrado y aceptación funcional según política; información para el PR/MR. |

Cada TASK concreta objetivo, alcance incluido/excluido, requisitos y criterios,
responsable, participantes, interfaces, dependencias, revisores, controles y definición
de terminado. Una integración con trabajo propio tiene su TASK y depende de los
componentes pertinentes. Un frontend validado con mocks conserva ese alcance y no
acredita la comunicación real con el backend.

Una tarea puede estar implementada con Sonar pendiente; en ese caso se muestra como
pendiente de comprobación, salvo la continuación o cierre con reservas que se haya
validado expresamente. La excepción conserva el resultado, los pendientes y los límites
de continuación; no convierte un resultado fallido en verificación ordinaria superada.
Al confirmarse cualquier paso se emite la orientación de la sección 9.2.

Pausar o cancelar conserva cambios y su procedencia. Reanudar reevalúa lo afectado por
política, identidad, base, asignación y controles. Una corrección del comportamiento
acordado sigue el flujo de defecto; una ampliación de alcance vuelve a SPEC/PLAN/TASK.
El agente no encadena correcciones fuera de alcance para eliminar todos los avisos de
un proyecto antiguo ni crea tareas futuras sin concretar su necesidad.

### 5.6 Adaptación a la vida del proyecto

| Situación | Comportamiento propuesto |
|---|---|
| Una persona, proyecto nuevo acotado | Un responsable puede acumular funciones admitidas, una rama por petición y controles declarados. Se omiten especialidades y ceremonias sin necesidad real. |
| Equipo, proyecto nuevo | Definición compartida, tareas por responsabilidades reales, interfaces acordadas y coordinación explícita de integración. |
| Proyecto existente | Adoptar la base mediante el flujo existente cuando sea necesario. Distinguir lo observado de lo aprobado y no reconstruir autores o decisiones desconocidas. |
| Mantenimiento evolutivo | Reutilizar la especificación vigente; cada petición delimita el cambio y su regresión, con deuda previa y nuevas obligaciones diferenciadas. |
| Cambio de composición o etapa | Versionar equipo y política, decidir vigencia sobre el trabajo abierto y conservar la continuidad del mismo proyecto. |

### 5.7 Cambiar la forma de trabajo durante el proyecto

Una petición como «ahora trabajaremos en equipo» o «vamos a empezar a utilizar Sonar»
abre una revisión de la configuración. El plugin explica qué cambia, propone el
alcance de aplicación y presenta una decisión conjunta al responsable competente.
No obliga a empezar de nuevo el proyecto ni da por aprobada una configuración sugerida.

| Aplicación del cambio | Efecto propuesto |
|---|---|
| Solo peticiones nuevas | Las abiertas conservan su versión del proceso. La vista indica cuáles siguen cada recorrido. |
| Trabajo abierto seleccionado, al llegar a un paso acordado | Se prepara la correspondencia de pasos y se adopta la nueva versión en ese punto. Los resultados reutilizables se conservan. |
| Aplicación inmediata al trabajo afectado | Se explica qué necesita revisión, reasignación o comprobación adicional; se retiene solo el avance cuya validez esté afectada. |

La decisión indica vigencia, peticiones/tareas afectadas y tratamiento de revisiones,
asignaciones, autorizaciones, evidencias y excepciones abiertas. Si no se decide el
efecto sobre una tarea iniciada, se conserva su configuración confirmada mientras sea
compatible con las decisiones vigentes; una contradicción real requiere aclaración.
No se asume una nueva obligación sobre trabajo cerrado ni se borra un fallo antiguo
por dejar de utilizar una herramienta.

Un paso agrupado o dividido conserva la relación con las obligaciones y resultados
anteriores. La vista pasa a mostrar el nuevo recorrido y qué queda por hacer; no se
marca un paso nuevo como terminado por semejanza de nombre. Si dos ramas cambian la
política de manera incompatible, se reconcilian sus decisiones antes de aplicarlas.

### 5.8 Excepciones puntuales validadas

Apartarse justificadamente del recorrido es una operación prevista del sistema.
No basta con ofrecer «bloquear» o «cambiar para siempre la política». El usuario
puede solicitar omitir un paso, aplazarlo, sustituirlo, variar su orden, asumir otra
función o utilizar otra rama para un caso concreto. La excepción no se aplica sola
por haber una urgencia, una sugerencia del agente o un error técnico.

Se distinguen cuatro situaciones:

| Situación | Tratamiento |
|---|---|
| El proyecto no utiliza un control o un paso no aplica según sus reglas | Se aplica la configuración vigente, sin pedir excepciones repetidas. |
| Se quiere cambiar habitualmente la forma de trabajo | Se revisa la política con la sección 5.7. |
| Se necesita una desviación para un caso concreto | Se valida una excepción delimitada y se conserva la regla habitual. |
| Ya se actuó fuera del recorrido sin validación previa | Se registra la desviación y se decide cómo regularizar lo pendiente, sin inventar una autorización anterior. |

El recorrido de la excepción es:

1. **Concretar:** regla o paso afectado, petición/tarea, motivo y efecto solicitado:
   continuar, aplazar, sustituir u omitir, o cerrar con reservas.
2. **Explicar:** consecuencias sobre el resultado y sobre otras tareas, alternativas
   razonables y medidas compensatorias cuando sean necesarias. Si no hacen falta,
   no se inventa una tarea compensatoria por formalismo.
3. **Validar:** la función competente comprueba que la solicitud entra en sus
   atribuciones y decide sobre la propuesta concreta. Se registra quién valida,
   cuándo, qué alcance acepta y su motivo. El agente puede recomendar, sin suplir
   una aprobación humana requerida. Una decisión explícita suficiente no se pide dos veces.
4. **Aplicar y registrar:** indicar duración o condición de término, usos permitidos,
   qué transición habilita y qué obligaciones conserva. El avance ordinario de otras
   tareas permanece sujeto a sus propias condiciones.
5. **Resolver:** cuando venza, se complete la obligación aplazada o se revoque, registrar
   el resultado y comprobar si quedan pendientes que afecten a pasos futuros.

El motivo es obligatorio y proporcional: una explicación concreta puede bastar para
un caso sencillo. En un proyecto individual, la misma persona puede solicitar y
validar cuando tenga ambas funciones; no se exige un segundo miembro por defecto.
En equipo se respeta la separación de funciones configurada. La excepción reutiliza
la autoridad existente; no permite concederse nuevas atribuciones en la solicitud.

Si el caso no estaba previsto, se remite al responsable con capacidad vigente para
resolver esa clase de decisión o revisar la política. La ausencia de una excepción
predefinida no produce una prohibición permanente ni una aprobación automática.
Si esa autoridad no puede acreditarse, queda pendiente su validación. Una excepción
del proyecto tampoco modifica permisos de herramientas o decisiones externas.

El estado puede ser solicitada, validada, rechazada, aplicada, resuelta, vencida o
revocada. Son situaciones funcionales propuestas, no nuevos valores del schema.
Omitir Sonar se muestra como «Sonar omitido por excepción validada»; aplazarlo mantiene
un pendiente con responsable y condición de resolución. Aceptar un cierre con reservas
no equivale a un análisis superado ni habilita automáticamente las tareas dependientes.
Si deben continuar, la decisión identifica también ese efecto y su alcance concreto.

Una excepción vencida, revocada o de otra tarea no habilita nuevas actuaciones. Se
conserva lo ocurrido mientras estuvo vigente. Las medidas pendientes se revisan en
las consultas y transiciones pertinentes, sin crear un servicio de seguimiento en
segundo plano. Si se repite la misma necesidad, se recomienda revisar la configuración,
sin modificarla automáticamente.

La vía general aquí propuesta amplía la definición del producto y debe traducirse al
método antes de implementarse. El runtime actual tiene reservas más acotadas en los
[workflows vigentes](../../docs/V2-WORKFLOWS.md); este texto no activa una excepción
que esa versión no admita ni introduce un permiso genérico para ignorar controles.

La validación de qué se va a hacer, exigida en la sección 13, precede a la planificación.
Una excepción puede permitir validar una porción acotada con reservas visibles; no
convierte «planificar primero y validar después» en una aprobación ya existente.

### 5.9 Cumplimiento del recorrido por el plugin

Antes de cada actuación que cambie el estado, el plugin resuelve el proceso y su
versión, la petición/tarea y la función que interviene. Comprueba las condiciones
ordinarias o la excepción válida para ese paso, junto con el alcance autorizado y
los resultados reales. No escoge la versión más permisiva entre ramas o documentos.

Si puede avanzar, realiza la actuación, registra el resultado y confirma que el estado
ha quedado guardado antes de anunciar el paso como completado. Si detecta un cambio
concurrente o falla el registro, conserva el trabajo realizado, muestra la divergencia
y recupera el estado; no repite efectos externos ni afirma un cierre no confirmado.

Si no puede avanzar, indica la regla concreta, su efecto sobre esa porción y una
salida posible: corregir, aclarar, aportar una comprobación, validar una excepción
o modificar la configuración. Una petición como «márcalo terminado» no elude esta
comprobación. Se aprovechan las autorizaciones vigentes y se permite continuar lo
independiente. Al cambiar de skill o de chat se aplica el mismo contexto documentado.

El plugin gobierna las actuaciones que realiza y detecta divergencias observables
al reanudar o validar. No garantiza impedir físicamente toda edición manual o acción
externa; configurar esa protección sigue fuera del alcance de esta propuesta.

### 5.10 Agilidad como condición de aceptación

La configuración debe reducir trabajo administrativo. Se propone un recorrido breve
para cambios acotados y ampliaciones solo cuando las justifiquen su impacto, riesgo,
dependencias o la elección del proyecto. Un cambio pequeño puede describirse y validarse
en una ficha breve con su parte funcional y técnica; no necesita reproducir la
documentación de todo el sistema ni rellenar apartados que no aplican.

Reglas de experiencia y coste propuestas:

- Una solicitud agrupada de validación por revisión de propuesta y función que deba
  aprobarla. Si la misma persona valida ambas partes, puede decidirlas conjuntamente.
- El plan y la autorización para ejecutar su alcance pueden presentarse en una sola
  interacción cuando el usuario ya dispone del plan concreto. No se solicita otra
  autorización por cada tarea incluida, skill, registro técnico o paso automático.
- Se reutilizan contexto, decisiones, revisiones y análisis que sigan siendo válidos.
  Un cambio material explica qué ha dejado de ser aplicable y por qué se repite algo.
- Los resultados e historial se registran automáticamente dentro del trabajo autorizado;
  el usuario decide sobre el desarrollo, no actúa como secretario del plugin.
- Se comprueba el ámbito afectado. No se ejecutan todas las pruebas, se relee toda la
  aplicación o se repite un análisis completo por cada comando si no lo exige el cambio.
- Los mensajes se emiten en los hitos del proceso y ante incidencias relevantes, con
  detalle ampliable; una consulta breve no desencadena una campaña de comprobaciones.

La agilidad se verificará en recorridos individual, equipo, reanudación sin cambios y
evolutivo pequeño. Se observarán decisiones solicitadas, repeticiones, trabajo
administrativo y tiempo del plugin separado de pruebas y servicios externos. El criterio
es cero confirmaciones redundantes, cero ejecuciones costosas sin causa y ausencia de
fichas vacías obligatorias. Los permisos adicionales que imponga el host se identificarán
por separado; el plugin no puede eliminarlos ni atribuirlos a su flujo.

Antes de considerar aceptada la experiencia de v3 debe haber prueba de uso con personas
sobre esos recorridos y resultados visibles, no solo validadores de estructura. No se
fija una latencia universal sin medirla ni se presenta el menor número de preguntas
como éxito si se ha omitido una decisión necesaria.

#### Presupuesto de interacción y criterio de prueba

Se propone este presupuesto para los recorridos sin incidencias, con necesidad clara,
herramientas disponibles y sin decisiones nuevas de terceros. Una intervención es una
respuesta que el plugin exige para poder avanzar; un mensaje informativo no cuenta.

| Recorrido | Presupuesto propuesto |
|---|---|
| Primera configuración | Una propuesta agrupada y una decisión por persona con autoridad necesaria; solo las aclaraciones críticas no conocidas se añaden antes. |
| Cambio pequeño con configuración vigente | Dos decisiones antes de ejecutar: propuesta funcional/técnica y plan con autorización. Cero confirmaciones administrativas adicionales y cero edición manual de registros internos. |
| Aceptación final | Una decisión si el proceso exige aceptación humana final, diferenciada de las dos anteriores. No se omite para cumplir un presupuesto. |
| Reanudación sin cambios | Cero nuevas decisiones, análisis costosos o registros duplicados por cambiar de chat o skill. |
| Equipo sin cambios de alcance | Una solicitud agrupada por función revisora y paquete aplicable; una misma persona puede responder a varias funciones juntas. |

Para el cambio pequeño se ofrece una ficha de revisión, un plan breve y un resumen de
resultado; pueden ser vistas del mismo documento. El número de archivos internos no
se convierte en trabajo de lectura o mantenimiento manual para el usuario. La sección
13 contiene el recorrido conversacional completo y el caso con especialistas.

Una intervención adicional solo se justifica por una necesidad concreta: dato crítico
ausente, cambio material, conflicto, incidencia de herramienta, regla del proyecto o
permiso externo. El registro identifica qué cambió y por qué las decisiones existentes
no bastan. «Por seguridad» o «por el proceso» sin causa concreta no justifican el exceso.

La aceptación de uso recorre cambio pequeño, equipo, reanudación y mantenimiento tanto
en Codex como en Copilot. Se anotan intervenciones, documentos que la persona tuvo que
abrir/editar, repeticiones y tiempo administrativo observado, separando modelo, runtime,
herramientas externas y espera humana. Antes de la prueba se acuerda un límite de tiempo
administrativo para cada escenario y se conserva la medición; no se ajusta después para
dar por superado un resultado. La comparación con v2 sirve de referencia, no sustituye
los presupuestos anteriores. Si falta prueba con personas o un límite acordado, la
aceptación de agilidad sigue pendiente. Es aceptación del producto, no una ampliación
automática de la puerta de publicación vigente en `docs/VALIDATION.md`.

### 5.11 Eficiencia de contexto durante el uso

La agilidad también depende de lo que el modelo tenga que leer y mantener en memoria.
La documentación completa permanece disponible en el repo; no es el contenido que se
inyecta íntegramente al iniciar una tarea. Las instrucciones del método se organizan
en una entrada breve y referencias por versión y operación, conservando sus garantías.
El runtime puede comprobar más datos localmente de los que necesita enviar al modelo.

| Operación | Contexto que se presenta por defecto |
|---|---|
| Consultar estado o una regla | Estado derivado y fuentes pertinentes a la pregunta; sin código, informes completos ni historia ajena salvo necesidad concreta o comparación solicitada. |
| Definir y validar una porción | Propuesta en revisión, decisiones y restricciones compartidas aplicables, diferencias y dependencias afectadas; sin repetir la definición entera del proyecto. |
| Planificar después de validar | Unidades aceptadas, cobertura, responsabilidades, contratos compartidos y dependencias de la porción; no solo un resumen de títulos. |
| Implementar o verificar | Contrato literal completo de la porción y de sus dependencias aplicables, autorización, estado y código/evidencia necesarios. El selector no sustituye estas obligaciones por resúmenes. |
| Reanudar | Estado mínimo, revisión comprobada y cambios relevantes. Se reutiliza lo realmente disponible; un chat nuevo o una compactación exige recuperar el contrato necesario. |
| Migrar | Inventario procesado localmente, resumen antes/después y conflictos que requieren decisión. Los originales e informes íntegros siguen accesibles sin volcarlos al chat. |

El modelo recibe una sola copia de cada bloque seleccionado, con referencia a su origen.
Los errores y hallazgos se agrupan por causa; las listas grandes se paginan y el informe
íntegro queda disponible. El total y los pendientes permanecen visibles. Una salida
recortada no significa que se hayan leído o resuelto sus elementos omitidos.

La selección incluye obligaciones transversales y consumidores afectados, incluso si
una tarea contribuye a ellos sin ser su propietaria principal. La prosa fuera de tablas,
los anexos y las decisiones históricas todavía aplicables también pueden ser necesarios.
Cada fuente es aplicable, excluida con motivo comprobable o de aplicabilidad desconocida.
Ante una duda crítica se amplía el contexto y, si no se resuelve, queda pendiente esa
actuación. No se elimina una obligación para obtener una lectura más corta.

Se proponen presupuestos iniciales para la sobrecarga controlada por el plugin, con
detalle técnico en la sección 6 de la propuesta técnica: entrada y recorrido activo
breves, diagnósticos acotados y aviso de crecimiento del paquete de trabajo. Son objetivos
de aceptación por medir, no límites que permitan truncar un contrato. Si un caso necesita
más contexto, el plugin amplía automáticamente dentro del alcance autorizado y explica
una intervención solo cuando cambie una decisión real. No pregunta al usuario por tokens
ni exige confirmar cada lectura.

La prueba compara operaciones completas de estado, cambio pequeño, reanudación,
especialistas, mantenimiento y migración. Incluye un proyecto con mucha historia no
relacionada y casos con metadatos incompletos. Cuenta instrucciones, contenido normativo,
código, salidas, ampliaciones y correcciones. La calidad y cobertura no pueden empeorar
para acreditar ahorro; un mensaje inicial más pequeño no basta si provoca más relecturas
o errores. Se separa lo medido por el host de una estimación de texto. La documentación
del producto puede ser extensa sin obligar a cargarla por completo en el uso cotidiano.

Ejemplo: para añadir la búsqueda de la sección 13.3 se cargan la tarea, comportamiento
vigente de la lista, reglas compartidas aplicables y sus pruebas. Las actas de peticiones
cerradas sin relación permanecen localizables; no se envían al modelo. Si una regla
general exige filtrar solo proveedores autorizados, se conserva literalmente aunque no
esté enlazada correctamente desde esa tarea. Optimizar no puede hacer desaparecer esa
restricción. Repetir una consulta sin cambios evita otro volcado de todo ese contenido.

## 6. Modelo de ramas e identidades propuesto

### 6.1 Una petición, una rama de coordinación y destinos explícitos

La política del proyecto elige la rama de integración. `main` es una opción,
no una suposición universal: puede ser `develop` o una línea de mantenimiento.
También define convención de nombres, quién integra, estrategia de merge y
controles requeridos. Una consulta no obliga a crear una rama.
Una desviación puntual respecto de la rama prevista usa la sección 5.8 y conserva
repositorio, rama/base real y procedencia; no se registra una rama que no existe.

Al materializar una petición se propone generar su identidad, comprobar el
checkout y seleccionar o crear su rama a partir de una referencia exacta. Los
cambios ajenos se conservan. Si ya hay documentación o código pendiente, se
reconcilia su procedencia antes de atribuirlo al nuevo cambio. Crear una rama no
equivale a autorizar commits, push, integración, implementación o publicación.

Si el repositorio aún no existe o carece de una base válida, se declara el requisito
previo pendiente. Puede prepararse un borrador de descubrimiento, pero no presentarlo
como petición materializada con trazabilidad Git. Inicializar un repositorio o crear
su primer commit exige su propia autorización. Una rama existente se reutiliza solo
cuando representa la petición y no contiene trabajo incompatible; no se atribuyen
automáticamente todos sus archivos modificados a la nueva solicitud.

En el caso sencillo, definición, plan y código comparten la rama de la petición.
Cuando intervienen especialistas en paralelo, cada porción puede tener otra rama
y un checkout separado, con destino a la rama coordinadora o al destino acordado.
No se impone una rama por persona ni una relación uno a uno entre rama y tarea.
Las tareas conservan sus dependencias y una responsabilidad explícita de integración.

Ejemplo conceptual de nombres, pendiente de concretar como convención:

```text
main
  codex/pch-7f3c2a9d-proveedores
    codex/pch-7f3c2a9d-frontend
    codex/pch-7f3c2a9d-backend
```

La indentación expresa el flujo acordado de integración; no una jerarquía de
ramas que Git mantenga automáticamente. El fragmento visible identifica la
petición para las personas; no es la clave técnica completa ni garantiza unicidad
por sí solo. Debe comprobarse cualquier coincidencia de nombres.

Antes de cada transición material se comprueba el checkout, la rama y su base.
Un cambio de rama o base obliga a reconciliar lo afectado, no a inventar un
historial nuevo. Cada integración registra origen, destino anterior y resultado,
con los sujetos de evidencia y las decisiones aplicables. Una rama es una
referencia móvil; esa es la razón para conservar también revisiones exactas
([glosario de Git](https://git-scm.com/docs/gitglossary)).

Si el destino avanza mientras se revisa, se vuelve a evaluar el candidato contra
el nuevo destino antes de integrarlo. La revisión del conjunto incluye código,
contratos compartidos, reglas, asignaciones y evidencia. La propuesta no confiere
a la propia rama candidata capacidad de aprobar sus controles: se conserva la
separación de confianza del guard y la política de revisión aplicable.

### 6.2 Identidad permanente desde la creación

Se recomienda ampliar la separación existente entre identidad y alias:

- Cada elemento nuevo recibe un UUID completo, generado una vez y conservado.
  Como opción inicial se propone UUIDv4 con generación aleatoria del sistema;
  la elección final y su compatibilidad quedan pendientes.
- El nombre legible combina tipo, título y una representación corta que pueda
  desambiguarse. Por ejemplo, `TASK-7F3C2A9D · Validar proveedor` es una propuesta
  de presentación, no sintaxis aceptada por el schema actual.
- Las relaciones y la procedencia se resuelven mediante la identidad completa;
  los alias, enlaces de lectura y rutas se diseñan para mantener esa resolución.
- Dos clones que modifican una tarea heredada mantienen su UUID. Dos tareas
  creadas independientemente reciben UUID distintos, aunque compartan petición,
  nombre o un contador local. Un espacio de nombres por petición con `TASK-001`
  sigue pudiendo colisionar si varios especialistas crean tareas en esa petición.
- Al fusionar se conserva la identidad. Cambian su estado o su presencia en la
  rama de integración, no su nacimiento. Si se necesita un número correlativo
  posterior, será un alias adicional registrado y requerirá asignación coordinada.

Los UUID permiten generación sin registro central; no se afirma imposibilidad
matemática de colisión. Hay que validar duplicidades y distinguir una colisión de
generador de una identidad heredada. Una fecha sola, el nombre de una persona o
el nombre de rama no bastan como identidad permanente. Referencia técnica:
[RFC 9562, UUID y generación distribuida](https://www.rfc-editor.org/rfc/rfc9562.html).

### 6.3 Alternativas consideradas

| Alternativa | Valoración propuesta |
|---|---|
| Contador global consultado en cada clon | No coordina creaciones simultáneas: ambos clones pueden elegir el mismo siguiente número. |
| Reservar números o rangos en una rama central | Puede hacerse con Git y actualización condicionada a la base, pero introduce coordinación, conectividad y contención para asignar códigos. |
| Fecha/hora como código | Ayuda a leer el orden aproximado; no resuelve por sí sola concurrencia ni diferencias de reloj. |
| Código temporal y renumeración obligatoria al fusionar | Desplaza el conflicto al merge y obliga a tratar enlaces, revisiones, autorizaciones y evidencia producidos antes. No se recomienda como identidad primaria. |
| UUID permanente y alias legible | Opción recomendada: creación independiente y continuidad de referencias. Un alias correlativo posterior sería opcional y no sustituiría la identidad. |

### 6.4 Conflictos que siguen necesitando control

| Situación | Tratamiento propuesto |
|---|---|
| Mismo alias, UUID distintos | Conservar ambos elementos y resolver la presentación ambigua antes de integrar; no tratarlos como una única tarea. |
| Mismo UUID heredado, modificaciones distintas | Comparar contra el ancestro común y reconciliar contenido, autoridad y revisión. |
| UUID distintos, mismo requisito o finalidad | Revisar si son duplicados conceptuales, contribuciones o capacidades independientes; el UUID no decide el significado. |
| Cambios en contratos o reglas compartidas | Revisar consumidores, tareas, autorizaciones y pruebas afectadas aunque Git fusione sin conflicto textual. |
| Índice o rutas coincidentes | Conservar documentos de ambas ramas, resolver identidades y reconstruir el índice; no descartar una copia completa. |
| Referencias a elementos que no llegarán al destino | Bloquear o separar expresamente el alcance; una fusión parcial no deja enlaces activos sin resolver. |

Se propone almacenar elementos/eventos independientes en archivos con rutas
estables basadas en su identidad, evitando un contador o un registro global que
todos deban editar. Los documentos compartidos conservarán conflictos reales y
necesitarán revisión. La creación puede ser distribuida; la integración en cada
destino se coordina y valida contra su estado vigente.

Esto es viable sin una base de datos externa para asignar identidades. Los controles
locales y la revisión pueden vivir en el repo. Garantizar que nadie omita el proceso
requiere además permisos y comprobaciones exigidas por el servidor de integración;
las instrucciones al modelo no sustituyen esa protección. No se configura aquí CI.

Un squash o rebase puede cambiar los commits relacionados, y una rama puede
eliminarse. Se conserva la relación con el resultado integrado y los snapshots o
artefactos de evidencia necesarios; citar un commit que deja de ser recuperable
no basta para una trazabilidad durable. Una reintroducción de trabajo no crea
otra identidad por copiar los archivos: debe decidirse si continúa el elemento
original o materializa un alcance nuevo.

### 6.5 Coordinación cotidiana entre participantes

En equipo, cada proyecto acuerda una referencia Git compartida para su política y
equipo. Cada petición acuerda su rama de coordinación para propuesta, contratos,
asignaciones y resultados. Pueden coincidir; si son distintas, la petición conserva
la revisión de política que aplica y la última autoridad observada. En un proyecto
individual exclusivamente local, la referencia acordada puede ser local: no se exige
remoto, publicación ni recepción de otro participante. No se crea una rama técnica
adicional obligatoria ni se atribuye coordinación a `main` por defecto.

Un cambio de coordinación distingue **preparado localmente**, **compartido en una
revisión identificada** y **recibido por el participante**. Guardar una asignación en
el propio clon no permite anunciar que el compañero ya la conoce o la ha aceptado.
Compartir usa las autorizaciones Git existentes o deja la publicación pendiente;
este flujo no autoriza por sí mismo commits, push ni mensajes externos.

| Momento | Comprobación y comportamiento |
|---|---|
| Iniciar o reanudar una porción, aceptar un relevo o revisar | Actualizar la referencia compartida mediante el acceso autorizado y comparar las revisiones observadas antes de actuar. Si no puede actualizarse, indicar el alcance local de la información. |
| Mismo trabajo autorizado y sin cambios relevantes | Reutilizar la comparación durante esa operación; no pedir sincronizar por cada edición. |
| Cambio material de interfaz, responsabilidad, autoridad o proceso | Compartir la decisión con las porciones afectadas y exigir recepción antes de su siguiente actuación dependiente. Si está preparada pero no compartida, queda visible esa limitación. |
| Cierre e integración | Comprobar de nuevo el candidato y las referencias de coordinación disponibles. Un avance remoto durante la comprobación obliga a reevaluar lo afectado. |
| Trabajo sin conexión | Solo continuar la porción previamente autorizada que la política permita, contra la revisión conocida. Las decisiones que requieren estado compartido vigente quedan pendientes; el resultado local se reconcilia al reconectar. |

La recepción registra automáticamente la revisión utilizada al reanudar; solo pide
una decisión humana si hay un cambio que la requiera. No es una firma adicional por
cada actualización. En un relevo se conserva aparte la aceptación del destinatario
cuando la política la exija. Una revocación desconocida no puede impedirse a distancia:
el proyecto debe decidir si permite trabajo desconectado y con qué límites.

Ejemplo: backend propone cambiar un campo compartido. Hasta publicar y reconciliar
la revisión, frontend sigue viendo el contrato anterior y no se anuncia coordinación
completada. Al recibir el cambio, se identifica su impacto y se actualiza solo el trabajo
afectado. La documentación o pruebas independientes ya autorizadas pueden continuar.
La vista de estado indica «según la revisión compartida observada…» y qué contribuciones
no publicadas o no recibidas faltan; no presenta el clon como un tablero global en vivo.

## 7. Sonar y Dependency-Check durante la implementación

### 7.1 Política explícita del proyecto

El proyecto declara por separado qué controles utiliza y las condiciones de cada uno.
En esta propuesta, Dependency-Check se refiere a OWASP Dependency-Check; Sonar designa
el producto y servicio concretos que el proyecto confirme. Esta nomenclatura no fija
versiones, licencias, instalaciones ni credenciales. Si el proyecto emplea otra
herramienta, su equivalencia y evidencia requieren declaración expresa; no se asume.

La política debe poder representar estas situaciones sin mezclarlas:

| Dimensión | Tratamiento propuesto |
|---|---|
| Uso en el proyecto | Utilizado, no utilizado por decisión documentada o pendiente de decidir. |
| Aplicabilidad | Aplica a esta porción/etapa o no aplica con motivo. Una tarea documental no obliga por sí sola a analizar todos los componentes. |
| Obligatoriedad cuando se usa | Se propone obligatorio antes del cierre cuando es aplicable. Un uso solo informativo requiere decisión explícita del proyecto y no se presenta como garantía exigida. |
| Ejecución | No iniciada, en curso, terminada o impedida por una incidencia técnica. |
| Resultado y vigencia | Superado, incumplido o no evaluable, con sujeto observado y comprobación de aplicabilidad actual. |
| Disposición | Ejecutado ahora, reutilizado con fundamento, omitido por política o excepción explícita cuando esté permitida. |

Son dimensiones propuestas para el diseño, no estados nuevos ya admitidos por el
schema. La decisión de no utilizar un control puede mantenerse durante la vida del
proyecto o hasta una revisión acordada; no requiere una excepción por cada tarea.
Debe registrar quién la decide, motivo, alcance y vigencia. Cambiar esa decisión
activa el análisis de impacto sobre trabajo abierto y mantiene el historial.

Un control no utilizado no acredita calidad ni un fallo de ejecución. Una caída
del servidor, credencial ausente, timeout o resultado desconocido tampoco acreditan
que el proyecto haya decidido prescindir de él. Un control obligatorio sin resultado
aplicable impide el cierre ordinario. Las excepciones siguen la política vigente;
se solicitan y validan mediante la sección 5.8 y no cambian un resultado fallido a
superado. Un control informativo puede permitir
continuar, mostrando sus hallazgos y el tratamiento acordado.

La definición de cada control incluye:

| Dato de configuración | Decisión funcional necesaria |
|---|---|
| Uso y alcance | Utilizado/no utilizado/pendiente, motivo, componentes y tareas a los que aplica. Sonar y Dependency-Check pueden tener decisiones distintas. |
| Autoridad | Quién configura, revisa hallazgos y autoriza cambios de reglas, exclusiones o excepciones. |
| Medio de análisis | Herramienta y versión compatibles, servicio/proyecto objetivo cuando exista y mecanismo de ejecución o de obtención de informes ya disponible. |
| Criterio de aceptación | Quality Gate y reglas aplicables para Sonar; umbrales y tratamiento de hallazgos para Dependency-Check. Sin porcentajes o severidades universales inventados. |
| Base de comparación | Código nuevo, deuda previa, componentes, lenguajes/ecosistemas y exclusiones explícitas. Un ámbito no analizable no se presenta como cubierto. |
| Vigencia | Entradas que invalidan un resultado, antigüedad máxima cuando proceda y condiciones de reutilización. |
| Continuidad | Esperas y reintentos acotados, responsables ante incidencias y tratamiento permitido de excepciones. |
| Evidencia | Informe recuperable, procedencia admitida, conservación y datos mínimos para vincularlo con la tarea y el código. |

Una decisión pendiente permite definir y explorar alternativas. Si condiciona la
solución o su aceptación, se resuelve antes de validar esa porción y planificarla;
los datos no críticos pueden quedar como pendientes explícitos. Una no utilización puede
deberse a la naturaleza del proyecto o a una decisión del responsable autorizado;
el plugin la muestra y la reutiliza sin convertirla en una excepción por tarea.

Antes de confirmar un recorrido que dependa de estos controles se prepara una ficha de
viabilidad: medio disponible, acceso permitido, ámbito que puede analizar, forma de
identificar el código, cómo obtener el resultado final y límites de espera/reintento.
Se comprueba lo observable con medios autorizados; un dato no comprobado permanece como
tal. Una prueba de acceso no equivale a un análisis superado. No exige instalar, ejecutar
un análisis completo ni crear un PR solo para configurar el proyecto.

Si el único medio requiere un PR previo, se identifica quién puede prepararlo y bajo
qué autorización; el recorrido no se presenta como listo mientras falte ese requisito.
Se recomienda habilitar un medio válido, conservar ese ámbito pendiente o decidir
explícitamente el no uso si el proyecto lo admite. Una indisponibilidad temporal sobre
un recorrido ya viable utiliza la continuidad definida, no cambia automáticamente la
política. Así se evita descubrir por primera vez al cerrar que el control era imposible.

### 7.2 Cierre de tarea con controles ya comprobados

La implementación realiza el ciclo de cambio, comprobación y corrección antes
de solicitar el cierre. El mismo agente que implementa puede ejecutar u obtener
el análisis y corregir sus resultados. No requiere otro agente especialista ni un
orquestador nuevo. Puede utilizar una ejecución local autorizada o recibir evidencia
de un servicio existente durante el trabajo de la rama. El plugin no crea ni modifica
pipelines para hacerlo. Las comprobaciones rápidas del editor ayudan, pero solo el
resultado aceptado por la política acredita el control correspondiente.

El recorrido propuesto es:

1. Resolver los dos controles para la TASK y comprobar la disponibilidad de sus medios.
2. Implementar la porción autorizada y ejecutar las pruebas aplicables.
3. Identificar el sujeto a analizar: commit con árbol limpio o snapshot reproducible
   que incluya las modificaciones relevantes. Un SHA no representa cambios locales
   sin registrar; no se exige crear un commit únicamente para poder analizarlos.
4. Lanzar u obtener cada análisis con alcance y autorización válidos. Conservar su
   identificador y esperar un resultado terminal dentro de los límites configurados.
5. Interpretar hallazgos, decidir el tratamiento permitido e implementar correcciones
   dentro de alcance. Los cambios que excedan ese alcance vuelven a definición.
6. Repetir análisis y pruebas afectados; comprobar otra vez la vigencia del otro
   control si la corrección ha cambiado sus entradas.
7. Registrar el resultado final y las incidencias previas, preparar la revisión
   requerida y comprobar las condiciones ordinarias de cierre o la excepción de
   cierre validada. Comunicar el resultado y la siguiente acción según la sección 9.

Si falta un medio válido para un control obligatorio, se muestra el bloqueo y quién
puede resolverlo, incluida la opción de solicitar una excepción delimitada cuando
proceda. El control continúa sin resultado; la validación cambia únicamente lo que
se permite hacer con ese pendiente. No se instala una herramienta ni se cambian
permisos automáticamente.
Un informe aportado por una persona puede ser admisible si la política lo contempla y
su sujeto y procedencia se pueden comprobar; la afirmación informal «ha pasado» no
equivale a un resultado recuperable.

Para Sonar se comprueba el resultado final del Quality Gate de la ejecución
identificada. Terminar o enviar el análisis no demuestra por sí solo ese resultado;
Sonar documenta la espera explícita del gate en sus
[parámetros de análisis](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/analysis-parameters/parameters-not-settable-in-ui).

El ámbito técnico puede ser un módulo o proyecto completo, aunque la decisión de
cierre sea por TASK. No se recorta artificialmente un análisis a líneas cambiadas
si la herramienta o las obligaciones requieren más contexto. Un informe puede
referenciar varias tareas cubiertas sin duplicar la ejecución.

La política concreta herramientas/versiones, ámbito y exclusiones, reglas o
umbrales, cobertura requerida, base de código nuevo, entorno, fuente de resultados
y responsables de corrección o revisión. Los umbrales y la deuda previa se acuerdan
explícitamente; el agente no los reduce ni suprime hallazgos para obtener un pase.

Para dependencias también importa la vigencia de la información de vulnerabilidades.
OWASP Dependency-Check utiliza fuentes externas y mantiene datos locales, según su
[documentación de fuentes](https://dependency-check.github.io/DependencyCheck/data/index.html).
Un lock sin cambios no prueba por sí solo que un informe antiguo siga siendo válido.
Se registran versiones resueltas, alcance, fuentes/fecha de actualización y
supresiones aplicadas; la política define cuándo actualizar o repetir el control.

Antes del cierre se enlazan resultado, tareas cubiertas, commit o snapshot exacto,
base pertinente, configuración y reglas, ejecución, fecha, entorno y evidencia
recuperable. No basta un enlace al último informe mutable del proyecto ni un texto
de consola que diga passed. Los accesos y secretos se gestionan fuera del contrato.

#### Agrupación y continuidad durante la espera

Se agrupan tareas por ámbito real del analizador y entradas compatibles. La agrupación
se concreta en el plan ya autorizado y puede ampliarse dentro de su alcance sin nueva
decisión administrativa. Un grupo identifica componentes, configuración, sujeto exacto,
tareas cubiertas y condiciones de vigencia. No agrupa por persona o por número de TASKs.

Se ejecuta una vez por conjunto de entradas vigente; consultar o vincular ese resultado
a varias tareas no repite el análisis. Si el analizador necesita todo el proyecto, no
se simula una ejecución parcial. El grupo puede cerrar varias tareas a la vez cuando
todas sus obligaciones estén cubiertas, pero no obliga a esperar tareas ajenas a esas
entradas. Un cambio posterior, una nueva base o la caducidad de datos externos tiene
que explicar la repetición necesaria; no reabre cierres históricos automáticamente.

Las dependencias expresan el resultado necesario, además de la tarea productora:

| Dependencia | Qué permite continuar | Qué no acredita |
|---|---|---|
| Contrato validado | Diseñar e implementar contra la revisión acordada, incluidos mocks cuando se declaren. | Que el productor esté implementado o funcione conjuntamente. |
| Resultado disponible | Consumir un artefacto o snapshot concreto con las comprobaciones mínimas declaradas en el plan. | Su cierre ordinario o el pase de un análisis todavía pendiente. |
| Resultado verificado | Continuar cuando estén las comprobaciones y revisiones exigidas para ese resultado exacto. | La integración final si falta verificar la composición. |

Una dependencia existente sin clasificación no se rebaja automáticamente: conserva su
condición previa hasta revisarla. El modelo puede recomendar una dependencia menos
restrictiva al definir el plan, pero no cambiarla durante una espera para evitarla.
El cierre ordinario y la aceptación conjunta siguen exigiendo los controles aplicables.

Ejemplo: backend tiene contrato validado y un resultado disponible con sus pruebas;
Sonar está en curso. Frontend puede implementar contra ese contrato o probar con ese
snapshot si el plan lo permite. Backend sigue «implementado, comprobación pendiente»;
la integración ordinaria espera la calidad y las pruebas conjuntas. Esto es continuidad
normal configurada, no una excepción que haya que solicitar cada vez que tarda Sonar.

La espera realiza consultas acotadas y reutiliza el identificador del análisis. El
agente continúa trabajo independiente autorizado y comunica el pendiente. Si finaliza
el chat, la siguiente operación recupera ese identificador; no se crea un servicio de
monitorización. Un resultado incumplido requiere corrección y nuevo análisis afectado;
un error técnico se reintenta solo conforme a los límites acordados. Ninguno cierra la
tarea. La equivalencia de evidencia exige entradas comprobables, no una conjetura del
modelo de que el cambio «parece no afectar».

### 7.3 Hallazgos y correcciones

Cada hallazgo tratado conserva herramienta, identificador cuando exista, localización
o dependencia afectada, resultado observado, responsable, acción y comprobación
posterior. Se proponen las siguientes disposiciones, sin mezclar clasificación
técnica con decisión humana:

| Situación | Tratamiento |
|---|---|
| Problema introducido por el cambio | Corregir dentro de alcance y volver a comprobar antes del cierre cuando incumpla la política. |
| Deuda previa | Comparar con la base acordada. Aplicar la política del proyecto; registrar trabajo adicional sin atribuir al cambio toda la deuda histórica. |
| Posible falso positivo | Aportar justificación y obtener la revisión prevista. No suprimirlo automáticamente por considerarlo molesto. |
| Riesgo aceptado o corrección aplazada | Decisión con autoridad, motivo, alcance, vigencia y seguimiento. Conservar el resultado original y el tipo de cierre/continuación que realmente admite el método. |
| Corrección que cambia contratos o introduce dependencias nuevas | Reconciliar SPEC/PLAN/TASK y decisiones técnicas antes de ampliar la implementación. |
| Hallazgo fuera del ámbito de la TASK | Registrar y asignar su tratamiento; resolver su efecto bloqueante según política, sin ocultarlo ni apropiarse de otro alcance. |

Dependency-Check puede requerir revisar correspondencias entre componentes y
vulnerabilidades. Su mecanismo de supresión permite registrar excepciones técnicas;
la decisión de usarlas y su vigencia siguen las reglas del proyecto, con revisión de
su justificación ([documentación de supresiones](https://dependency-check.github.io/DependencyCheck/general/suppression.html)).

Una actualización de dependencia exige las comprobaciones de compatibilidad y
regresión afectadas. No se propone actualizar indiscriminadamente a la versión más
reciente ni eliminar dependencias funcionales para hacer desaparecer un hallazgo.
Un informe de dependencias no acredita automáticamente licencias, ausencia de malware
o toda la seguridad de la aplicación; cada resultado conserva su alcance real.

Una modificación posterior al análisis puede volverlo inaplicable. La decisión de
reutilizarlo exige comprobar sus entradas; no depende solo de que el fichero editado
parezca ajeno al hallazgo. Las exclusiones y la definición de código nuevo también
son entradas relevantes.

### 7.4 Integración: comprobar vigencia y composición

La preparación SDD de la integración reúne los controles de tarea realizados o su
no utilización documentada. Comprueba cobertura de toda la funcionalidad y vigencia
de la evidencia frente al candidato conjunto y al destino actual. Puede alimentar
la descripción y revisión de un PR/MR sin gestionar su pipeline ni su aprobación.

Se reutiliza lo que siga representando el alcance, entradas, reglas y sujeto
comprobados. Un cambio de código, resolución de conflictos, dependencias, reglas,
destino o composición puede requerir otra comprobación. Si faltan datos para
demostrar equivalencia, se repite el control afectado o queda pendiente; no se
inventa un resultado nuevo a partir del anterior. Se conserva el cierre histórico
de la tarea y se identifica el trabajo o verificación que exige el candidato actual.

Si la infraestructura disponible solo produce el análisis después de abrir un PR,
el responsable debe resolver cómo obtenerlo durante la implementación, por ejemplo
mediante un PR borrador ya autorizado y gestionado externamente. Esta propuesta no
abre PR ni configura esa infraestructura automáticamente. Mientras no haya resultado
válido, el cierre ordinario sujeto a ese control queda pendiente; no se traslada
silenciosamente la primera comprobación a después de completar la tarea.

### 7.5 Disponibilidad, reintentos y evidencia

Se distinguen ejecución en curso, error técnico, cancelación, resultado de calidad
incumplido y resultado no evaluable. Cada intento se conserva con su resultado; el
estado vigente referencia el intento pertinente. Consultar el mismo análisis no
genera otra ejecución ni duplica un cierre. Reintentar crea un intento relacionado,
sin sustituir ni borrar el anterior.

La espera y el número de reintentos se acotan por configuración. Al agotarse, el
agente explica la incidencia y propone resolver el acceso, aportar evidencia
admisible, reintentar o solicitar una decisión permitida. No sigue corrigiendo código
para resolver una caída del servicio ni comunica éxito por ausencia de respuesta.

El informe se conserva en el repositorio o en una ubicación admitida que permita
recuperar su contenido durante el periodo acordado, con referencia e integridad
comprobables. Los metadatos mínimos siguen siendo accesibles desde el proyecto.
No se guardan tokens, contraseñas ni volcados sensibles de diagnóstico. Un hash
verifica integridad si existe contenido recuperable; no demuestra quién lo produjo.
La política determina qué procedencia acepta, especialmente para aprobaciones.

La conservación de un resultado histórico no acredita que siga vigente. Un informe
perdido o caducado se declara como tal y se obtiene una nueva evidencia si es necesaria.
No se incorporan monitorización periódica de vulnerabilidades, notificaciones ni
automatizaciones en segundo plano como parte de esta propuesta.

### 7.6 Relación con las demás comprobaciones SDD

Sonar y Dependency-Check complementan las obligaciones de la tarea. Un resultado
satisfactorio en ambos no sustituye sus pruebas y revisiones. Se mantienen, según
el alcance ya definido, estas comprobaciones de implementación:

| Aspecto | Qué debe comprobar la tarea cuando aplique |
|---|---|
| Funcionalidad y regresión | Criterios positivos/negativos y conservación del comportamiento afectado. |
| Compilación, tipos y convenciones | Construcción y comprobaciones locales necesarias con entradas conocidas. |
| Interfaces y datos | Compatibilidad entre componentes, contratos, persistencia y cambios de esquema/datos incluidos en la tarea. |
| Seguridad del cambio | Controles de acceso, validación y tratamiento de datos exigidos por la especificación. |
| UX y accesibilidad | Estados, recorridos y revisión visual/funcional que correspondan. |
| Revisión y documentación | Revisión humana requerida y actualización de la documentación afectada. |

Esta relación conserva el alcance de verificación SDD; no impone una batería nueva
universal ni especifica cómo automatizarla mediante CI/CD.

## 8. Casos de aceptación propuestos

Estos escenarios son criterios para una implementación futura. Todos están
**pendientes de ejecución**; no son resultados de validación del runtime actual.

| ID | Caso y resultado esperado | Requisitos |
|---|---|---|
| AC-EQT-001 | Una persona inicia un proyecto acotado y asume las funciones permitidas. Cada cambio conserva su recorrido sin tareas de especialidades que no intervienen. | 001, 003, 008 |
| AC-EQT-002 | Frontend, backend y BBDD contribuyen a una funcionalidad. La consulta identifica su cobertura, el responsable de integración y la evidencia conjunta pendiente o ejecutada. | 003, 007, 012 |
| AC-EQT-003 | Otra persona recibe una tarea empezada. Conserva base, trabajo previo, autorización aplicable y pendientes; el historial no atribuye al nuevo responsable todo lo realizado. | 004, 005, 006, 011 |
| AC-EQT-004 | Se delega solo una parte. El resto mantiene su responsable y se explicitan entrega e integración, sin duplicar obligaciones ni ampliar permisos. | 003, 004, 007 |
| AC-EQT-005 | Cambian nombre o cuenta de un miembro. Se resuelve su identidad actual y se reconstruye la identidad y función registradas en una implementación anterior. | 002, 005, 010, 012 |
| AC-EQT-006 | Un miembro deja el equipo. Se señalan asignaciones abiertas que necesitan decisión y se conservan sus actuaciones y aprobaciones históricas. | 002, 004, 006 |
| AC-EQT-007 | Cambia una regla de revisión con trabajo en curso. Solo se reconcilia el alcance afectado y queda registrada la política usada en cada etapa. | 001, 005, 006, 009 |
| AC-EQT-008 | El proyecto pasa de primera entrega a mantenimiento con más participantes. Reutiliza historia y especificación, y cada evolutivo se gobierna por las reglas vigentes. | 001, 002, 008, 012 |
| AC-EQT-009 | No hay identidad autenticada disponible o cambian cuenta y host. Se registra la incertidumbre y se aplica la política de identidad; no se hereda silenciosamente otra persona ni se inventa autenticación. | 009, 010, 011 |
| AC-EQT-010 | Falta una revisión obligatoria sin excepción validada, o se intenta atribuir autoridad no concedida. La transición no se habilita; se explica cómo resolverla y una delegación ordinaria no elimina el control. | 003, 004, 009, 010, 043 |
| AC-EQT-011 | Se consulta una implementación antigua tras varios relevos. Se enlazan las contribuciones, reglas, autorizaciones y evidencias de cada momento; un dato histórico ausente permanece desconocido. | 002, 004, 005, 012 |
| AC-EQT-012 | Dos clones aportan asignaciones incompatibles. La integración requiere reconciliación y no acepta la última escritura como decisión de gobierno. | 004, 006, 009, 011 |
| AC-EQT-013 | Se materializa una petición nueva. Sus documentos y tareas quedan asociados a una rama identificada, destino y base explícitos; una consulta previa no crea ramas. | 013, 015, 018 |
| AC-EQT-014 | Dos especialistas crean tareas en clones de la misma petición y eligen el mismo alias. Sus identidades completas son distintas y la integración conserva ambas y sus referencias. | 014, 016, 017, 019 |
| AC-EQT-015 | Dos ramas crean autorizaciones, ejecuciones o recibos desde la misma base. No comparten identidad o ruta por utilizar el mismo contador local; reintentar una creación sí conserva su identidad. | 016, 017, 019 |
| AC-EQT-016 | Dos ramas modifican una regla heredada. Se conserva su identidad y se revisan los cambios y consumidores, sin asumir que ausencia de conflicto textual acredita compatibilidad. | 006, 018 |
| AC-EQT-017 | Se cambia de rama con trabajo pendiente o el destino avanza durante la revisión. Se preservan los cambios y se reconcilian base, alcance, autoridad y verificaciones antes de continuar o integrar. | 013, 015, 018 |
| AC-EQT-018 | Una integración usa squash o rebase y retira la rama de trabajo. Las tareas conservan identidad y permiten reconstruir origen, resultado y evidencia con artefactos recuperables. | 015, 017, 020 |
| AC-EQT-019 | El destino es una rama de mantenimiento y se aplica parcialmente un cambio. No se presupone main ni se permite que falten referencias, obligaciones o dependencias del alcance integrado. | 013, 014, 018, 020 |
| AC-EQT-020 | Se integran documentos nuevos de dos clones e índices desactualizados. Se reconstruye el índice desde las fuentes reconciliadas sin perder elementos; cambiar un alias de presentación no reescribe evidencia cerrada. | 016, 017, 019 |
| AC-EQT-021 | Sonar y dependencias son obligatorios y aplicables. La tarea solo puede cerrar de forma ordinaria tras obtener sus resultados finales satisfactorios para el trabajo realizado; enviar un análisis no basta. | 021, 022, 024, 025 |
| AC-EQT-022 | El proyecto declara no utilizar Sonar o el control de dependencias. Las tareas pueden continuar sin ese control, mostrando decisión, motivo y alcance; no se informa como superado ni se vuelve a pedir la decisión en cada cierre. | 021, 023, 024, 028 |
| AC-EQT-023 | Un control obligatorio está en cola, falla técnicamente o no tiene credenciales. Permanece pendiente o bloqueado y no se transforma automáticamente en no utilizado. | 022, 023, 024, 027 |
| AC-EQT-024 | Un análisis cubre varias tareas y conserva sujeto, reglas y vigencia aplicables. Se reutiliza con referencias a esas tareas y se evita ejecutarlo de nuevo sin motivo; su uso no acredita controles externos del PR. | 025, 026, 028 |
| AC-EQT-025 | Las tareas estaban verificadas, pero cambian código, destino o composición al preparar el PR. Se mantiene la evidencia histórica, se identifica lo afectado y no se da el nuevo candidato por validado automáticamente. | 025, 026, 028 |
| AC-EQT-026 | No cambia el lock de dependencias, pero el informe supera la antigüedad admitida o cambia su fuente de vulnerabilidades. Se comprueba de nuevo su aplicabilidad conforme a la política. | 021, 025, 026 |
| AC-EQT-027 | Se propone bajar un umbral, excluir código o suprimir un hallazgo. Se exige la decisión prevista por la política y queda trazada; la excepción no reescribe el resultado ni concede permisos generales. | 021, 024, 027 |
| AC-EQT-028 | Una tarea documental no requiere análisis de código y una tarea funcional requiere integración posterior. Ambas muestran sus controles aplicables y pendientes, sin confundir tarea cerrada con funcionalidad aceptada o entrega autorizada. | 021, 024, 026, 028 |
| AC-EQT-029 | Una rama candidata intenta conceder al ejecutor permiso para aprobar su propia excepción mediante una nueva política. La transición exige autoridad de la base de gobierno anterior y no admite la autoatribución. | 001, 005, 009, 027, 029 |
| AC-EQT-030 | Dos miembros tienen nombres iguales o una cuenta ha cambiado de titular. Se pide aclaración antes de atribuir la actuación, se conservan vigencias y no se reescribe la autoría pasada. | 002, 010, 030 |
| AC-EQT-031 | Un plan distribuye frontend, backend y BBDD pero omite la prueba de integración o contiene dependencias cíclicas. Se señalan las obligaciones sin cobertura y no se presenta la funcionalidad como preparada íntegramente. | 007, 009, 031 |
| AC-EQT-032 | Se renombra una etapa como completada o se reanuda una tarea cancelada. La etiqueta no evita controles: se comprueban obligaciones, autoridad, base y estado, conservando el historial de pausa/cancelación. | 005, 009, 032 |
| AC-EQT-033 | Se propone un relevo que exige aceptación y el destinatario aún no lo ha aceptado. No se activa ni se atribuye su decisión; una sustitución por ausencia usa la regla específica y no simula aceptación. | 003, 004, 009, 033 |
| AC-EQT-034 | Dependency-Check bloquea una porción y otra tarea no depende de ella. La vista explica causa, responsable y siguiente acción, y permite continuar solo el trabajo independiente autorizado. | 008, 009, 034 |
| AC-EQT-035 | Un hallazgo es previo al cambio, otro parece falso positivo y otro requiere modificar una interfaz. Se conservan sus clasificaciones, se revisa cualquier supresión y el nuevo alcance vuelve a SPEC/PLAN/TASK. | 022, 027, 031, 035 |
| AC-EQT-036 | Se aporta un informe válido de una infraestructura existente. Se incorpora su evidencia sin crear agentes, pipelines o despliegues y sin declarar aprobado el PR. | 026, 028, 036 |
| AC-EQT-037 | Un proyecto anterior tiene alias repetidos, historia incompleta y runtime antiguo. La adopción muestra impacto y correspondencias; no inventa autores ni modifica registros cerrados para hacerlos encajar. | 016, 017, 019, 037 |
| AC-EQT-038 | Un análisis tarda demasiado, se cancela o se consulta repetidamente. Se conservan intentos y estado real, los reintentos son acotados y la consulta no duplica evidencias ni cierres. | 022, 024, 025, 038 |
| AC-EQT-039 | Se continúa la misma tarea en Codex y Copilot con distintas capacidades de acceso a Sonar o identidad. Se conservan obligaciones e historia; se declara la capacidad ausente y no se degrada la política. | 010, 011, 021, 030, 039 |
| AC-EQT-040 | Se elimina una rama o caduca el enlace a un informe. La consulta recupera los artefactos conservados o declara su ausencia; nunca presenta un hash sin contenido o un enlace mutable como prueba nueva suficiente. | 012, 015, 020, 025, 040 |
| AC-EQT-041 | Un proyecto individual agrupa definición funcional y técnica, omite Sonar por decisión y acumula funciones; otro separa especialidades y revisiones. Ambos siguen su recorrido y validan la propuesta antes de planificar, sin imponer las mismas fases visibles o miembros. | 001, 008, 023, 041, 048, 053 |
| AC-EQT-042 | Un proyecto incorpora un equipo y activa Sonar. Se decide qué peticiones conservan el proceso anterior y cuáles adoptan el nuevo, se actualizan sus pasos y pendientes y no se reinicia ni invalida indiscriminadamente el trabajo previo. | 005, 006, 021, 042 |
| AC-EQT-043 | Sonar está inaccesible y se valida aplazarlo para una tarea con motivo, responsable y condición de resolución. Se permite la transición autorizada, el análisis sigue pendiente y no se habilita un cierre que la decisión no incluya. | 009, 022, 024, 043 |
| AC-EQT-044 | Se solicita cerrar con un control omitido y la función competente valida esa excepción concreta. El resultado técnico se conserva y el cierre se explica con reservas; las tareas dependientes no se habilitan salvo decisión válida que cubra su continuidad. | 009, 024, 027, 032, 043 |
| AC-EQT-045 | Se intenta reutilizar una excepción vencida, revocada o de otra tarea. Se rechaza ese nuevo uso y se explican alternativas, conservando el avance histórico que sí estaba autorizado y los pendientes de resolución. | 005, 006, 043, 047 |
| AC-EQT-046 | Un caso no estaba previsto en el catálogo de excepciones. Se permite presentarlo al responsable con atribuciones vigentes; en un proyecto individual puede validarlo la misma persona si tiene esa función. No se inventan terceros ni autoridad ausente. | 003, 029, 043, 048 |
| AC-EQT-047 | Se pregunta por el estado de un proyecto con varias peticiones en etapas distintas, una fase parcial y datos de otro clon no observados. La respuesta muestra el recorrido de cada grupo, lo realizado, lo pendiente y quién debe actuar, sin una fase o porcentaje global engañosos. | 012, 034, 042, 044 |
| AC-EQT-048 | Se completa un paso configurado sin que el usuario pida estado. Cualquiera de las seis skills informa del resultado confirmado, dónde queda la petición, lo que falta y la siguiente acción; no espera al final de toda la funcionalidad. | 034, 045, 047 |
| AC-EQT-049 | Se aplica una omisión validada y después puede continuar un paso ya autorizado. Se explica la omisión y su límite, se indica que no hace falta intervención del usuario y se continúa sin pedir otro «adelante» ni presentar el control como superado. | 024, 043, 045, 048 |
| AC-EQT-050 | Una edición manual cambia el estado a terminado o una escritura falla tras comprobar una base anterior. El plugin comprueba las condiciones actuales y la persistencia, conserva lo realizado y no anuncia un cierre no confirmado. | 018, 032, 047 |
| AC-EQT-051 | El usuario pide orientación y hay dependencias que favorecen una opción. Se recomienda esa opción con una razón comprensible; si falta un dato decisivo se pide ese dato, sin inventar certeza ni registrar como aceptada la recomendación. | 034, 046, 048 |
| AC-EQT-052 | Se consulta desde otro chat una petición cuyo proceso cambió y tiene pasos no aplicables y una revisión esperando al usuario. Se reconstruye el recorrido desde el repo, se explican esos estados y se pide la revisión concreta en lenguaje sencillo, sin volcar códigos internos. | 011, 041, 042, 044, 046 |
| AC-EQT-053 | Se repite una misma excepción en varias peticiones. El plugin recomienda revisar la configuración con la evidencia de repetición, pero mantiene la política vigente hasta una decisión y no crea seguimiento automático. | 006, 036, 042, 043, 046 |
| AC-EQT-054 | Se descubre trabajo ejecutado sin la validación previa del paso. Se registra la desviación y la decisión actual de regularización con sus pendientes, sin afirmar que la autorización existía ni borrar lo sucedido. | 005, 012, 043, 047 |
| AC-EQT-055 | Se recorre un cambio pequeño con una persona: una ficha concreta reúne la propuesta funcional/técnica, se valida conjuntamente y luego se presenta un plan cuyo alcance puede autorizarse en la misma decisión. No aparecen fichas vacías, preguntas repetidas ni permisos nuevos por cada TASK. | 048, 049, 050, 053 |
| AC-EQT-056 | Se reanuda sin cambios una ejecución autorizada con evidencia vigente. Se recupera el contexto, se explica el siguiente paso y se continúa sin repetir aprobaciones o análisis por cambiar de chat o skill. | 011, 025, 048, 049 |
| AC-EQT-057 | La propuesta solo contiene títulos como «hacer backend» y «mejorar seguridad». El plugin concreta comportamiento, solución técnica, cambios y aceptación antes de pedir validación; no presenta una lista genérica como revisión preparada. | 046, 050, 051 |
| AC-EQT-058 | La propuesta está lista y el usuario aún no la ha validado. Se anuncia el momento de decisión, se muestran alcance y revisión exactos y se ofrecen aprobar o pedir cambios; no se materializan PLAN/TASK ejecutables. | 050, 051, 053 |
| AC-EQT-059 | Se aprueba una revisión y después cambia una interfaz o el alcance de un módulo. Se conserva la decisión anterior, se muestra el cambio y se revalida la parte afectada antes de planificarla; las porciones independientes siguen vigentes. | 006, 051, 052, 053 |
| AC-EQT-060 | El usuario dice «tiene buena pinta» o responde sobre un detalle, sin aceptar la propuesta completa. No se registra aprobación general. Una aceptación explícita y suficientemente delimitada se registra una sola vez y no se vuelve a pedir con terminología técnica. | 046, 048, 051 |
| AC-EQT-061 | Se acepta una porción completa y se dejan otras para más adelante. El plan solo cubre lo aceptado, conserva los pendientes y no trata el proyecto completo como validado. Aprobar la propuesta no inicia código. | 031, 050, 051, 053 |
| AC-EQT-062 | Se instala una futura versión 3 con un proyecto fijado a v2. El proyecto conserva su formato y reglas hasta la migración explícita; el sistema diferencia plugin, método y schema y no reescribe el proyecto al consultar. | 037, 054, 055, 058 |
| AC-EQT-063 | Se diagnostican muestras representativas de todos los formatos/métodos documentados de la línea 2.x. Cada origen tiene ruta probada o diagnóstico concreto; un origen desconocido o personalizado conserva sus datos y no se convierte cambiando el encabezado. | 054, 055, 056 |
| AC-EQT-064 | Se migra una copia 2.x autorizada con tareas, evidencia, adjuntos, identidades y políticas. El inventario final acredita conservación y correspondencias; ninguna persona, validación funcional o prueba se inventa durante la conversión. | 002, 016, 040, 055, 056, 057 |
| AC-EQT-065 | Cambia el origen después de aprobar la vista previa o la aplicación se interrumpe. Se rechaza la vista obsoleta o se recupera el estado registrado; los archivos conservan procedencia y no se declara completada una mezcla parcial 2.x/3.x. | 018, 047, 056, 058 |
| AC-EQT-066 | Un proyecto 2.x tenía un plan en curso y una propuesta previamente validada. Se acredita qué decisión y contenido siguen siendo equivalentes, se reconcilia únicamente lo afectado y se informa de las autorizaciones que necesitan renovación antes de reanudar. | 048, 051, 052, 055, 057 |
| AC-EQT-067 | Tras migrar llegan cambios de un clon antiguo o se intenta volver a v2 con trabajo nuevo v3. Se detecta la incompatibilidad, se conserva el trabajo posterior y se prepara una reconciliación o recuperación explícita; no se fuerza un merge ni se promete bloquear el clon desconectado. | 017, 018, 020, 056, 058 |
| AC-EQT-068 | En recorridos individual, equipo y mantenimiento se cuentan decisiones, repeticiones y coste administrativo. Se comprueba que cada petición de intervención tiene causa, cada repetición costosa está justificada y las explicaciones permiten actuar; la agilidad queda pendiente si solo se han pasado validadores estáticos. | 034, 045, 046, 048, 049 |
| AC-EQT-069 | Una persona realiza el cambio pequeño de la sección 13 con configuración vigente: dos decisiones previas a ejecutar, una aceptación final solo si se exige, ninguna edición manual de registros internos ni lectura de fichas vacías. Un exceso sin causa concreta incumple el presupuesto. | 048, 049, 059 |
| AC-EQT-070 | Falta una regla funcional crítica en ese cambio. Se pregunta el dato mínimo una vez, se registra la causa y después se mantiene el recorrido breve; no se inicia un cuestionario completo ni se omite la decisión para cumplir el presupuesto. | 046, 049, 059 |
| AC-EQT-071 | Se prueba la experiencia en ambos hosts con personas y límites de tiempo administrativo acordados antes. Se miden intervenciones y coste por escenario, separando herramientas y espera; si falta una observación o se excede un límite sin resolución, no se acredita agilidad. | 039, 049, 059 |
| AC-EQT-072 | Un responsable funcional revisa el caso de especialistas: puede identificar antes/después, reglas, exclusiones y ejemplos sin interpretar hashes o estados internos. El técnico ve contratos y cambios de datos; una omisión material en el resumen impide presentar el paquete como listo. | 046, 050, 051, 060 |
| AC-EQT-073 | Cambia una decisión técnica interna sin modificar la unidad funcional ni sus contratos de dependencia. El paquete conserva su aprobación funcional original y muestra la nueva revisión técnica pendiente; no exige que todas las unidades tengan el mismo número de revisión. | 051, 052, 061 |
| AC-EQT-074 | Cambia el significado de una respuesta de API aprobada. Se revalida el contrato y sus consumidores afectados; no basta con que el texto funcional permanezca sin editar. Las porciones independientes conservan sus decisiones. | 031, 052, 061 |
| AC-EQT-075 | El modelo considera editorial una frase normativa modificada o no puede probar que una dependencia sigue vigente. No genera equivalencia aprobada por su juicio; presenta el cambio localizado para revisión sin invalidar todo el paquete. | 047, 051, 052, 061 |
| AC-EQT-076 | Se incorpora un proyecto con el recorrido individual y después pasa a equipo. Se proponen valores concretos y solo decisiones críticas ausentes; no se activa un control, un no uso o una separación de funciones por inferencia. El cambio aplica según la vigencia acordada. | 001, 006, 042, 062 |
| AC-EQT-077 | Coinciden política antigua de petición, nueva autoridad compartida y excepción. Se respeta la revocación conocida y el alcance exacto de la excepción; dos decisiones contradictorias sin sustitución explícita no se resuelven por fecha o última escritura. | 003, 042, 043, 047, 062 |
| AC-EQT-078 | Una configuración exige revisor independiente inexistente o una dependencia circular sin salida. El diagnóstico muestra la contradicción y la corrección mínima; no activa el recorrido ni inventa responsables. | 008, 041, 062 |
| AC-EQT-079 | Una reasignación solo está guardada en un clon. Se muestra preparada localmente, no recibida ni aceptada por el compañero. Tras compartirla y reanudar, se registra la revisión recibida y se solicita únicamente la aceptación que exija la política. | 007, 011, 018, 063 |
| AC-EQT-080 | En equipo, una rama cambia un contrato mientras otra está desconectada. El trabajo local permitido conserva la revisión conocida; al reconectar se revisa solo lo afectado antes del siguiente paso dependiente. En uso individual local, se valida la referencia local sin exigir remoto. El estado no afirma conocimiento remoto inexistente. | 014, 018, 044, 047, 063 |
| AC-EQT-081 | Al configurar Sonar obligatorio se descubre que solo hay análisis mediante un PR aún no disponible. Se explica el requisito y su responsable antes de confirmar el recorrido; ni se instala infraestructura ni se promete cierre ejecutable con ese medio ausente. | 021, 022, 024, 064 |
| AC-EQT-082 | Varias tareas comparten entradas y alcance de análisis. Se usa una ejecución terminal para las tareas cubiertas; consultar, reanudar o añadir sus referencias no genera ejecuciones adicionales. Un cambio de entradas obliga a explicar la nueva comprobación. | 025, 049, 059, 064 |
| AC-EQT-083 | Backend espera Sonar y frontend depende de su contrato validado o de un resultado disponible acordado. Frontend continúa autorizado sin excepción rutinaria; la dependencia de resultado verificado y el cierre conjunto permanecen pendientes. | 008, 028, 034, 064 |
| AC-EQT-084 | Durante la espera se modifican entradas o el análisis falla. Se conserva su resultado real, se corrige o reintenta según su causa y se mantiene vigente solo evidencia aplicable; no se rebaja la dependencia ni se cierra por haber agotado el tiempo. | 024, 025, 038, 064 |
| AC-EQT-085 | Se migra el ejemplo individual de método 2.0.0: una decisión agrupada sobre conversión y configuración, cero revisión de historia cerrada. Una tarea activa sin aprobación recuperable exige solo la revisión actual de su porción, explicada antes del corte. | 055, 056, 057, 059, 065 |
| AC-EQT-086 | Se migra método 2.1.0 con propuesta exacta aprobada y plan activo. Se conserva el contenido y se muestra qué autorización operativa debe renovarse por el nuevo contrato; no se pide otra aprobación de negocio sin cambio material. | 051, 052, 055, 057, 065 |
| AC-EQT-087 | En el ejemplo de equipo se comparte un único mapa de migración y llega una rama v2 después. Se reutilizan las identidades, se conservan sus cambios y solo se solicita decisión sobre conflictos o autoridad afectados. Ningún clon crea una segunda migración independiente del mismo origen. | 018, 056, 058, 063, 065 |
| AC-EQT-088 | Un origen desconocido o una extensión no reconciliada aparece en la vista previa. Se distingue conservación de conversión admitida, se explica su efecto en tareas y se evita el corte incompatible. Las intervenciones adicionales se enumeran antes de decidir, sin presentar el diagnóstico como migración probada. | 055, 056, 059, 065 |
| AC-EQT-089 | Al entrar en una skill para un proyecto v3 se carga la ruta aplicable y se mantienen descubribles las otras cinco skills. No se incluyen manuales v1/v2 o capacidades inactivas por estar empaquetados; se miden las instrucciones realmente expuestas por cada host. | 039, 066, 069 |
| AC-EQT-090 | Una consulta de estado sobre una petición en un proyecto con mucha historia ajena usa la vista pertinente. Aumentar diez veces esa historia sintética sin cambiar obligaciones no aumenta su contenido normativo enviado al modelo; se informa por separado del coste local de indexación. | 044, 066, 068, 069 |
| AC-EQT-091 | Una tarea contribuye a una interfaz y existe una restricción global relevante en prosa fuera de tablas o con enlaces incompletos. Se conservan ambas obligaciones literales o se amplía para resolver la duda; el selector no considera ausencia de enlace como exclusión válida. | 031, 050, 067 |
| AC-EQT-092 | Se solicita una tarea inexistente, retirada o con referencias ambiguas. El paquete no declara suficiencia vacía ni usa otro elemento con el mismo alias; informa la causa concreta antes de ejecutar. | 016, 047, 067 |
| AC-EQT-093 | La vista compacta incluye cada bloque normativo una sola vez, con fuente y revisión. El formato completo sigue recuperable y los validadores mantienen sus entradas/huellas; reducir la representación no elimina condiciones, tipos, excepciones o adjuntos aplicables. | 051, 067, 068 |
| AC-EQT-094 | Tras construir contexto aparece una regla global nueva, cambia una interfaz, una función se revoca o se elimina una fuente. Se detecta el cambio del inventario/dependencias y se invalida lo afectado, aunque el archivo de la tarea no cambie. | 047, 061, 063, 068 |
| AC-EQT-095 | Se reanuda en otro chat o después de compactación sin garantía de conservar el contrato. El checkpoint orienta y se recuperan las fuentes literales necesarias; no se declara cargado un contenido porque exista su hash o un resumen. No se pide otra aprobación vigente. | 011, 048, 067, 068 |
| AC-EQT-096 | Una operación supera el umbral de contexto por obligaciones reales. Se conserva el contenido y se amplía dentro del alcance; si no cabe el mínimo necesario, se explica la limitación y se propone dividir el trabajo para validarlo. Nunca se recorta silenciosamente para marcarlo suficiente. | 050, 053, 066, 067, 069 |
| AC-EQT-097 | Un análisis produce un informe grande. Se muestran estado, totales, causas y hallazgos de la porción con acceso paginado al original; los pendientes no mostrados siguen contabilizados y no se presenta la primera página como revisión completa. | 024, 025, 066, 068 |
| AC-EQT-098 | Se compara flujo actual y optimizado sobre las mismas tareas y criterios, incluyendo ampliaciones, correcciones y verificación. Si reduce el primer prompt pero empeora calidad o consumo total, la eficiencia no se acepta. | 049, 059, 067, 069 |
| AC-EQT-099 | El host no expone tokens facturados, caché efectiva o estado exacto de contexto. Se informa de mediciones de texto o estimaciones con su procedencia, sin inventar ahorro monetario o persistencia de memoria. | 039, 068, 069 |
| AC-EQT-100 | El selector propuesto se contrasta sin sustituir el contexto necesario para actuar. Si su alcance discrepa del contrato de referencia o deja incertidumbre crítica, se amplía o conserva la ruta suficiente; no se activa una optimización por haber pasado solo pruebas de tamaño. | 047, 067, 069 |

Los números de la última columna remiten a los sufijos de REQ-EQT de la sección 3.

## 9. Experiencia de uso y consultas

El acompañamiento es un requisito del producto, común a las seis skills. Debe servir
a una persona que no conoce el método ni recuerda lo ocurrido en otro chat. Los nombres
de pasos y las explicaciones proceden del proceso configurado; no se muestra un recorrido
genérico que contradiga la forma de trabajar acordada por el equipo.

### 9.1 Al consultar el estado

La respuesta se construye desde los documentos, decisiones y evidencias disponibles.
Consultar no cambia estados, no lanza análisis ni intenta completar lo pendiente.
El usuario debe poder identificar:

| Información | Cómo se explica |
|---|---|
| Qué se está consultando | Proyecto completo, petición o tarea; si hay varias peticiones activas, se distinguen sus situaciones. |
| Recorrido del proyecto | Los pasos configurados y su relación: qué viene antes/después y qué puede hacerse en paralelo. Si conviven versiones del proceso, se indica cuál usa cada petición. |
| Qué se ha hecho | Pasos realmente completados y resultado obtenido; sin atribuir al proyecto entero la finalización de una tarea. |
| Dónde está el trabajo | Pasos en curso, trabajo parcial, revisiones esperando a una persona y bloqueos relevantes. Puede haber varios pasos activos. |
| Qué queda | Pasos futuros, dependencias, comprobaciones y decisiones pendientes. Los pasos no aplicables, omitidos o aplazados se muestran con su motivo. |
| Qué debe ocurrir ahora | Acción recomendada, motivo, quién la realiza y qué necesita el usuario decidir o aportar. Si no necesita intervenir, se dice expresamente. |

En proyectos grandes se agrupa el detalle por peticiones y fases reales, conservando
la visión del recorrido completo y dando prioridad a las acciones que afectan al
usuario. Una fase parcialmente realizada sigue siendo parcial; no se calcula un
porcentaje global a partir de pasos que tienen alcances distintos. Una petición
cancelada no cuenta como terminada satisfactoriamente.

Si solo se dispone de una copia local desactualizada o falta evidencia de otro
especialista, se explica esa limitación. No se inventa un estado global actualizado.
Una comprobación técnica histórica puede permanecer superada para su sujeto original
y necesitar otra comprobación para el trabajo actual; la respuesta distingue ambas.

Ejemplo ficticio de consulta, con un recorrido elegido por ese proyecto:

> La mejora de proveedores está en implementación. El recorrido acordado es:
> preparar y validar la propuesta → planificar → implementar → revisar en equipo →
> comprobar la integración.
>
> Ya se ha validado la propuesta y repartido el trabajo. Backend está terminado; frontend sigue
> en curso. Después quedan la revisión conjunta y la prueba del recorrido completo.
>
> En frontend falta que confirmes el mensaje que verá el usuario cuando se rechaza
> un proveedor. Recomiendo resolverlo ahora porque condiciona la pantalla y su prueba.
> El trabajo de backend no necesita una nueva aprobación.

La explicación debe permitir consultar también quién solicitó, definió, autorizó,
ejecutó, revisó e integró, con fuentes históricas accesibles. Los códigos y detalles
técnicos se ofrecen como ampliación; no ocupan el lugar de la explicación del estado.

### 9.2 Al completar un paso o avanzar excepcionalmente

Cada vez que se confirma la finalización de un paso del proceso, el plugin comunica
el cambio sin esperar una consulta de estado. La explicación contiene:

1. Qué paso se ha completado y qué resultado se obtuvo.
2. En qué punto del recorrido queda la petición o tarea y su relación con el proyecto.
3. Qué pasos o comprobaciones quedan, incluidas reservas y excepciones.
4. Cuál es el siguiente paso recomendado y quién lo realizará.
5. Qué necesita hacer el usuario, o que no necesita intervenir porque la continuación
   ya está autorizada.

Se informa cuando el resultado y el estado están confirmados, antes de presentar
como realizado el siguiente paso. Si una misma operación completa varios pasos,
una explicación puede identificar cada uno. No se crea una notificación por cada
comando ni se repite el resumen tras cada edición dentro del mismo paso.

Ejemplo ficticio de finalización cuyo siguiente paso es una comprobación conjunta
ya preparada y autorizada:

> He terminado la implementación del backend y sus comprobaciones, incluidos Sonar
> y Dependency-Check. Ahora comprobaré su funcionamiento junto con el frontend;
> después quedará la revisión funcional de la persona responsable. Continúo con esa
> comprobación, que ya está autorizada. Por ahora no necesitas hacer nada.

Ejemplo ficticio de finalización que necesita intervención:

> Las pruebas acordadas están completadas. Falta tu revisión funcional para cerrar
> esta petición. Comprueba el recorrido de alta de proveedor y confirma si el resultado
> coincide con lo acordado; si ves una diferencia, indícala para corregirla.

Cuando se aplica una excepción se explica el avance y la omisión por separado:

> Se ha validado continuar con la revisión aunque Sonar esté temporalmente inaccesible.
> El análisis sigue pendiente y lo retomará la persona responsable antes de la
> integración. Puedes revisar ahora la pantalla; la tarea aún no tiene cierre ordinario.

No se presenta un paso omitido como completado ni una autorización de continuación
como permiso para cerrar. También se da orientación al pausar, bloquear, reanudar,
activar un relevo o cambiar el proceso. Un fallo al guardar el estado se comunica
como pendiente de conciliación, aunque parte del trabajo ya se haya realizado.

### 9.3 Lenguaje, recomendaciones y decisiones

El lenguaje se adapta al usuario y mantiene frases concretas: «falta revisar el
resultado», «esta persona debe decidir» o «puedo continuar con lo ya autorizado».
Los términos necesarios se explican al usarlos; por ejemplo, «criterios de calidad
de Sonar» antes de depender del término Quality Gate. Los identificadores, huellas,
estados internos y comandos se reservan para ampliar o diagnosticar cuando sea útil.

Se recomienda cuando hay una base suficiente: reglas del proyecto, dependencias,
impacto observado, información confirmada o experiencia documentada aplicable.
La recomendación indica una opción y una razón concreta; si hay una alternativa
relevante, explica su consecuencia. No usa «lo recomendable» sin fundamento ni
convierte una preferencia del modelo en una norma del proyecto.

Si falta información que puede cambiar la decisión, se reconoce y se pide el dato
mínimo necesario. Las preguntas se agrupan y se evitan interrogatorios o listas de
decisiones futuras sin efecto inmediato. La consulta «qué recomiendas» sigue siendo
una consulta; una propuesta no se registra como aceptada por el mero hecho de explicarla.

Ante un bloqueo se ofrece una salida concreta y, cuando haya base, se recomienda una:
corregir, aportar evidencia, resolver una asignación, validar una excepción o revisar
la configuración. Se explica qué parte independiente puede continuar. El plugin
realiza el trabajo autorizado que pueda ejecutar y no lo devuelve al usuario como
una lista de comandos por conveniencia.

Una nueva aprobación solo se solicita por una decisión material que no esté cubierta.
Se reutilizan decisiones y autorizaciones vigentes, incluso al cambiar de skill o chat.
El mensaje didáctico orienta; no obliga a detener cada paso esperando «continúa».

## 10. Modelo documental funcional y conservación

Los siguientes conceptos describen información que debe existir. No prescriben
todavía nuevos tipos de schema, nombres de ficheros ni otra base de datos.

| Concepto | Contenido y relaciones |
|---|---|
| Política de proyecto | Revisión, vigencia, autor de la propuesta, autoridad que la confirma, reglas y efecto sobre trabajo abierto. |
| Recorrido de una petición | Versión del proceso, pasos aplicables, correspondencia tras cambios y situación de cada paso. Es una vista derivada, no otro tablero canónico. |
| Excepción | Regla afectada, motivo, propuesta, validación, efecto permitido, vigencia y pendientes; relación con los resultados técnicos que conserva. |
| Miembro y cuentas | Identidad estable, nombres, pertenencia, cuentas con procedencia/vigencia y funciones autorizadas. |
| Petición | Origen, alcance, responsable, SPEC/PLAN, repositorio, rama coordinadora, base y destino. |
| Asignación/relevo | TASK o porción, responsable, participantes, origen/destino, aceptación o sustitución autorizada y vigencia. |
| Ejecución/contribución | Operador, función, autoridad, trabajo realizado, revisión de la política, rama/base y checkpoint. |
| Análisis | Control, sujeto, alcance, tareas cubiertas, entradas/reglas, origen, intentos, resultado, hallazgos e informe recuperable. |
| Revisión/cierre | Sujeto revisado, persona y función, evidencia, decisión, reservas y condiciones satisfechas. |
| Integración | Origen, destino, resultado, contribuciones, reconciliaciones y comprobaciones conjuntas. |

Cada concepto enlaza los registros existentes cuando son suficientes. El diseño debe
evitar otro tablero de tareas o copias divergentes del mismo dato. Las vistas y el
índice se derivan de Markdown reconciliado; los hechos de una herramienta se conservan
con su procedencia, sin convertirse automáticamente en decisiones humanas.

Los registros históricos se corrigen por adición y relación explícita. Se conservan
fechas de actuación y registro, contexto aplicable y referencias anteriores. El
proyecto define la conservación de informes y la minimización de datos personales;
no se copian directorios completos de cuentas en cada ejecución.

Una modificación manual de Markdown se somete a validación antes de habilitar una
transición. Un archivo con una aprobación escrita no demuestra por sí solo identidad
autenticada ni autoridad. Se mantiene la separación entre guía del modelo, comprobación
local del runtime y protecciones externas: la instalación del plugin no impide toda
edición o integración que se haga fuera de él.

## 11. Compatibilidad y adopción

La propuesta se plantea para ambos hosts, Codex y GitHub Copilot, con las mismas
obligaciones funcionales. Los medios disponibles para identidad, análisis y acceso
a evidencia pueden variar. Cada host debe declarar y comprobar sus capacidades;
ninguna equivalencia de soporte se considera probada por compartir instrucciones.

Para proyectos existentes se propone:

1. Inspeccionar sin mutación versión fijada, documentos, identidades, relaciones,
   políticas y evidencia. Identificar lo recuperable y lo desconocido.
2. Preparar una vista de impacto: datos que se añaden, correspondencias propuestas,
   ambigüedades, trabajo abierto afectado y compatibilidad de lectores/escritores.
3. Confirmar la configuración inicial y autorizar la transición concreta. A partir
   de su vigencia, atribuir actuaciones nuevas con el modelo acordado.
4. Conservar documentos y evidencia históricos. No completar retrospectivamente
   nombres, reglas o aprobaciones que no puedan demostrarse.
5. Validar referencias, consultas históricas y continuidad antes de permitir nuevas
   escrituras; mantener una recuperación documentada si la transición falla.

Cambiar el generador de UUID no resuelve por sí solo las colisiones del modelo actual.
Se deben cubrir rutas, relaciones, aliases, huellas, autorizaciones, índices y lectores.
Si dos registros heredados independientes comparten UUID y alias, no se fusionan:
se conservan sus originales y se requiere una correspondencia explícita basada en
procedencia recuperable. Si no puede establecerse, la ambigüedad permanece bloqueada.
Una nueva representación puede referenciar esos originales sin reescribir su evidencia.

Los runtimes anteriores no pueden escribir silenciosamente el nuevo formato en un
checkout ya migrado. La propuesta técnica concreta como destino plugin 3.0.0, método
3.0.0 y schema 3.0, sujetos a validación. Actualizar el plugin no migra automáticamente
los proyectos ni cambia sus controles, cuentas o responsables.

La ruta 2.x → 3.x debe conservar el estado de los proyectos y presentar un inventario
antes/después, una vista previa aprobable y una recuperación comprobable. No basta con
cambiar la versión del índice. La configuración futura, las aprobaciones de contenido y
las autorizaciones de ejecución se evalúan por separado; la conversión documental no
las concede. El [diseño técnico de v3](lks-sdd-v3-technical-proposal.md) concreta lectores,
correspondencias, trabajo activo, ramas antiguas y recuperación.

La primera entrega de esta evolución debe permitir el uso completo con repositorio
y documentos locales, sin un servicio central para reservar identificadores o
gestionar personas. La obtención de análisis seguirá necesitando las herramientas
que el proyecto haya declarado; si no están disponibles, se informa el límite.

### 11.1 Experiencia de migración y coste para el usuario

La vista previa comienza con cuatro grupos legibles: qué se convierte automáticamente,
qué se conserva sin reinterpretar, qué decisiones faltan y qué trabajo podrá continuar.
El inventario técnico y las correspondencias quedan disponibles para ampliar el detalle.
Cada tarea activa muestra su condición concreta; «migrado» no equivale a «autorizado».
La matriz de orígenes y tratamientos se concreta en la sección 9 de la propuesta técnica.

El presupuesto del caso sencillo es una decisión agrupada por autoridad competente
sobre conversión y configuración v3 presentada, cero decisiones por archivo y cero
revalidaciones de tareas cerradas. Si también hacen falta decisiones de negocio o
autorizaciones operativas, se enumeran antes del corte y se agrupan por alcance/función;
no aparecen como preguntas inesperadas después de declarar la migración completada.
Una aprobación no cubre objetos que la vista previa no haya mostrado.

| Ejemplo ficticio | Conversión y conservación | Intervención y continuidad |
|---|---|---|
| Individual, schema 2.0/método 2.0.0, ocho tareas cerradas y ninguna activa | Conservar contenido e historia de las ocho tareas; actualizar referencias mediante un mapa único y proponer recorrido individual, usando decisiones previas recuperables. | Una decisión sobre la vista previa y configuración. No revisar de nuevo las ocho tareas. Las peticiones nuevas siguen el recorrido v3. |
| Mismo proyecto con una tarea abierta sin aprobación recuperable | Conservar su especificación, plan, cambios y evidencia; la carencia de aprobación no se rellena durante la conversión. | Mostrar antes del corte que esa porción necesitará validación funcional/técnica actual y después autorización del plan existente reconciliado. No se regenera el plan ni se revalida el resto. |
| Equipo, schema 2.0/método 2.1.0, propuesta exacta validada y trabajo en tres especialidades | Un coordinador prepara el mapa común; backend cerrado conserva historia, frontend activo mantiene plan y cambios, la rama BBDD pendiente se reconcilia con el mismo mapa al incorporarse. | Decisión agrupada de migración por las funciones competentes y renovación de las autorizaciones operativas afectadas. Se conserva la aprobación de negocio equivalente; los conflictos de la rama pendiente no bloquean porciones independientes tras completar el corte. |

Para el caso de equipo se acuerda pausa y revisión de partida. Las ramas y trabajos
pendientes se inventarían antes del corte; el trabajo no compartido se declara como
limitación, nunca como inventariado. Un clon que no pueda participar conserva v2 hasta
recibir el mapa; no puede presentar su conversión independiente como la del proyecto.
Las decisiones necesarias se muestran como acciones de personas concretas por función,
sin exigir que cada especialista vuelva a aprobar toda la migración.

La aceptación de migración observa estos recorridos con proyectos de muestra y luego
uso humano, contabiliza preguntas/reconciliaciones y comprueba la recuperación. Las cifras
de los ejemplos son escenarios de prueba, no resultados observados. Ni la conservación
de archivos ni la ejecución del validador bastan para demostrar una migración sencilla.

## 12. Escenario completo ilustrativo

Este caso es ficticio y no registra personas, tareas ni autorizaciones reales.

1. El responsable recoge una petición para modificar la ficha de proveedor. El
   proyecto ya tiene flujo, funciones, destino Git y los dos controles de calidad
   confirmados; se reutilizan esas decisiones.
2. La petición recibe identidad permanente y rama de coordinación desde la base
   acordada. Allí se describe y valida una revisión concreta de la propuesta funcional
   y técnica, con comportamiento, solución prevista y criterios de aceptación.
3. Después se planifican las porciones de BBDD, backend y frontend, los contratos que
   comparten y la comprobación conjunta. Se presenta el plan y se autoriza su alcance.
   Cada porción tiene responsable y dependencias.
4. Los especialistas trabajan en sus ramas vinculadas cuando necesitan aislamiento.
   Sus documentos nuevos reciben identidades independientes; todos conservan las
   identidades de requisitos e interfaces compartidos.
5. La persona responsable de backend delega una parte a otro compañero. Se registra
   el alcance y el relevo se activa conforme a la política. Las contribuciones previas
   permanecen atribuidas a sus autores.
6. Durante la implementación se obtiene Sonar y Dependency-Check. Un hallazgo exige
   corregir el código; otro requiere actualizar una dependencia compatible. Se
   realizan las correcciones autorizadas y las comprobaciones afectadas.
7. Cada tarea reúne evidencias del código final, revisiones y documentación antes
   del cierre. La tarea de BBDD declara explícitamente la aplicabilidad y cobertura
   reales de cada herramienta; no inventa un análisis para un ámbito no soportado.
8. El integrador reconcilia cambios e identidades, comprueba las interfaces reales
   y verifica qué evidencia sigue siendo aplicable al resultado conjunto. Quedan
   enlazadas las tareas, ramas, revisiones y decisiones en la información del PR/MR.
9. La aceptación funcional se registra según el flujo. Este escenario termina en
   la integración y aceptación SDD; no genera ni ejecuta un proceso de CI/CD.

En un proyecto individual, una persona puede desempeñar las funciones admitidas y
utilizar una única rama de petición. Si no se utiliza uno de los controles, su
decisión registrada sustituye la exigencia de ese análisis, sin simular un resultado.

## 13. Validación funcional y técnica antes de planificar

El recorrido común propuesto es:

`definir la propuesta → validarla → preparar el plan → aprobar/autorizar su alcance → implementar y verificar`

La validación es un momento visible de decisión. El plugin indica expresamente:
«La propuesta está preparada para tu revisión. Ahora necesitamos validar qué vamos
a hacer y cómo; después prepararé el plan de tareas». Debe mostrar la propuesta
concreta y explicar qué habilita la decisión. No pide aprobar «el proyecto» en abstracto.

| Contenido que se valida | Detalle necesario, proporcional al cambio |
|---|---|
| Propuesta funcional | Problema, destinatarios, comportamiento esperado, recorridos/reglas relevantes, alcance incluido y excluido, ejemplos y criterios de aceptación. |
| Propuesta técnica | Componentes y contratos afectados, solución prevista, tecnologías confirmadas o propuestas, datos/interfaces, compatibilidad, riesgos y cómo se comprobará. |
| Cambios concretos | Qué se añadirá, modificará o retirará respecto a la situación actual y las consecuencias relevantes para el proyecto. |
| Límites y pendientes | Qué no se hará, qué se aplaza y qué decisiones afectan a la porción. Una incertidumbre crítica se resuelve o queda fuera de la parte que se valida. |
| Objeto de la decisión | Revisión identificada, documentos/artefactos exactos, alcance, personas que deben validar y efecto: habilitar la planificación de esa porción. |

El resumen debe bastar para entender la decisión y enlazar el detalle. En cambios
pequeños ambas propuestas pueden estar en una misma ficha. Si una misma persona
puede validar las dos, se pide una decisión conjunta. Si hay revisores distintos,
se recogen las decisiones sobre las unidades exactas que componen el paquete y se
conservan las que sigan aplicando; el estado deja claras las pendientes.

Se admiten aceptación completa, solicitud de cambios y aceptación parcial delimitada.
Un «sí, apruebo esta propuesta» inequívoco se registra con su contexto; no se exige
copiar un hash. El silencio, una opinión favorable o aprobar un detalle no equivalen
a aceptar el conjunto. Los casos de aceptación de este documento describen el resultado
esperado; no son un plan de tareas ya autorizado.

Solo después se crea el plan ejecutable, trazado a la revisión aceptada. El usuario
puede aprobar ese plan y autorizar su implementación conjuntamente cuando ya lo tiene
delante. La aceptación de una propuesta que aún no contiene el plan no autoriza tareas
futuras desconocidas. Consultas, análisis de viabilidad y alternativas pueden preceder
a la validación, sin presentarse como compromiso de ejecución.

Si al planificar aparece una decisión que cambia la solución aprobada, se devuelve
esa parte a definición y se explica la diferencia. Una modificación fuera del contenido
normativo de una unidad puede conservar su vínculo si ese contenido y sus dependencias
siguen idénticos. Cambiar palabras de una unidad normativa requiere revisión localizada;
llamarlo editorial no demuestra equivalencia. Nunca se sustituye el contenido de una
aprobación antigua por el de un documento mutable más reciente.

En esta evolución del plugin se aplica el mismo criterio: el plan preliminar del
borrador anterior se retira de la propuesta vigente. El siguiente paso es validar
el [paquete funcional y técnico de v3](lks-sdd-v3-validation.md); la planificación
de mantenimiento se elaborará después de esa decisión.

### 13.1 Qué ve y qué decide cada persona

La ficha de revisión sigue este orden: situación actual, resultado propuesto, ejemplos
de aceptación, solución y cambios técnicos, consecuencias/exclusiones y decisión pedida.
Explica el efecto de aceptar y qué sigue pendiente. El resumen se contrasta contra el
detalle: no puede omitir una restricción, riesgo material o cambio que altere la decisión.

El responsable funcional revisa comportamiento y límites. El técnico revisa solución,
contratos, datos, compatibilidad y comprobación. Una misma persona puede validar ambos
si tiene esas funciones; no se obliga a un interlocutor de negocio a aprobar una elección
técnica que corresponde a otro. No se exige un cuestionario para demostrar comprensión:
la prueba de uso comprueba si la ficha permite explicar qué cambiará y qué queda fuera.

### 13.2 Unidades de aprobación y cambios parciales

Cada porción identifica sus unidades funcional y técnica y, cuando corresponda, su
contrato compartido. Una unidad tiene identidad, revisión, contenido exacto, dependencias
y función validadora. No exige un archivo por unidad. El paquete reúne esas referencias;
sus unidades pueden tener números de revisión distintos y conservar decisiones previas.

La condición de validación no es «todas las personas aceptaron el mismo número global»:
es que cada unidad necesaria tenga una decisión aplicable y que sus dependencias sean
compatibles. Una modificación de un contrato puede afectar una unidad cuyo texto no ha
cambiado. El análisis de impacto acompaña al paquete y no se confunde con aprobación.

| Cambio observado | Tratamiento de las decisiones |
|---|---|
| Progreso, localizador o presentación fuera del contenido normativo | Conservar la unidad y su decisión si se verifica igualdad y referencias válidas; no pedir otra aceptación. |
| Solución técnica interna sin cambio funcional ni de contrato | Nueva revisión técnica; mantener la unidad funcional idéntica cuando sus dependencias normativas sigan cubiertas. |
| API, permisos, datos, comportamiento o aceptación compartidos | Revisar las unidades afectadas y sus consumidores aunque parte de sus documentos no haya cambiado. |
| Texto normativo modificado o efecto incierto | Mostrar la diferencia y obtener revisión de la porción; el modelo no declara por sí solo una equivalencia aceptada. |

Ejemplo: la unidad funcional F1 define la búsqueda y la técnica T1 cómo implementarla.
Si T2 cambia solo la estructura interna, el paquete puede contener F1 aprobada y T2
pendiente. Si T2 cambia la búsqueda de coincidencia parcial a exacta, también afecta a
F1: conservar sus bytes no basta. La relación de dependencias recoge las obligaciones
compartidas; no se elimina un enlace para aparentar independencia. La propuesta técnica
define qué comprueba automáticamente el núcleo y qué valoración requiere una persona.

### 13.3 Recorrido completo de un cambio pequeño

Ejemplo ficticio, no es una petición real ni un plan de mantenimiento de este plugin.
Supone un proyecto con lista de proveedores ya cargada, tecnología y controles
confirmados, una persona con las funciones necesarias y aceptación final humana.

| Momento | Conversación y resultado propuestos |
|---|---|
| Petición | Usuario: «Añade búsqueda por nombre al listado, sin distinguir mayúsculas y manteniendo la lista completa al borrar el texto». |
| Ficha para validar | Plugin: «Hoy ves la lista completa. Propongo un campo Buscar por nombre que filtre coincidencias parciales sobre los proveedores ya cargados. Al vaciarlo reaparece la lista y si no hay coincidencias se muestra “No hay proveedores”. Reutilizaré el componente y los estilos actuales, sin cambiar API, base de datos ni dependencias. Comprobaremos coincidencia parcial, mayúsculas, borrado y cero resultados. Quedan fuera búsqueda en servidor, acentos y paginación nueva. Ahora validas este comportamiento y esta solución; después prepararé el plan». |
| Primera decisión | Usuario: «Valido esta propuesta». El plugin vincula la aceptación a la ficha exacta; no exige transcribir identificadores. |
| Plan posterior | Plugin: «El plan cubre el campo y filtrado, sus pruebas y los controles ya configurados. Después te presentaré el resultado para revisarlo. Puedes aprobar este plan y autorizar su implementación conjuntamente». Los artefactos afectados y criterios se muestran con el detalle proporcional disponible. |
| Segunda decisión | Usuario: «Apruebo el plan y autorizo su implementación». El plugin trabaja, registra y comprueba sin pedir permiso por cada tarea. |
| Resultado e intervención final | Plugin, solo si lo ha comprobado: «La búsqueda está implementada y las comprobaciones acordadas están completadas. Falta tu aceptación: revisa una búsqueda parcial, otra sin resultados y el borrado del texto». El usuario acepta o indica una diferencia. |

Dos decisiones habilitan la ejecución y una tercera acepta el resultado porque este
ejemplo lo exige. El plugin no pregunta de nuevo por Sonar, identidad o ramas ya
resueltos. Si descubre que la lista está paginada en servidor y la propuesta no cubre
el resultado pedido, explica ese hecho y devuelve la porción a revisión antes de
implementar una búsqueda incompleta; esa es una desviación justificada del presupuesto.

### 13.4 Recorrido de una petición con especialistas

Ejemplo ficticio: añadir alta de proveedores en un sistema existente que ya tiene
tecnología y equipo confirmados. El paquete se presenta antes de repartir tareas.

| Vista de revisión | Propuesta concreta del ejemplo |
|---|---|
| Funcional | Hoy se consultan proveedores, pero no se crean desde la aplicación. Se añade un formulario con nombre y NIF obligatorios; la creación válida aparece en la lista. El NIF duplicado informa del motivo sin crear otro proveedor. No se incluyen edición, importación ni nuevos permisos de alta. Se conservan las reglas de acceso vigentes. |
| Técnica compartida | Frontend usa un contrato de alta con respuestas diferenciadas para éxito, datos inválidos y duplicidad. Backend valida y usa persistencia transaccional; BBDD asegura la unicidad del NIF según la normalización acordada. Se reutiliza la pila confirmada. Si hay duplicados previos, se diagnostican y se requiere resolverlos antes de aplicar la restricción, sin borrarlos automáticamente. |
| Comprobación | Alta válida, datos incompletos, duplicidad incluso concurrente, acceso no autorizado, persistencia tras recargar y revisión del formulario. Sonar y Dependency-Check siguen la política de cada componente. |
| Decisión | Responsable funcional valida comportamiento y exclusiones. Responsables técnicos designados validan contrato, datos y solución de su ámbito. El paquete muestra qué unidad está aceptada y cuál necesita cambios. |

Después de las validaciones necesarias se prepara el plan con porciones de frontend,
backend y BBDD y comprobación conjunta. Frontend puede empezar con el contrato validado;
la prueba conjunta espera los resultados necesarios. Cada especialista recibe alcance,
revisión y dependencias. La autorización del plan se agrupa por autoridad competente.
Al completar sus porciones, los mensajes explican lo logrado y qué falta para el resultado
de usuario; terminar tres componentes no acredita por sí solo que funcionen juntos.

### 13.5 Relación con las capacidades actuales

La asignación a capacidades se mantiene dentro de las seis skills existentes:

| Skill | Responsabilidad propuesta en esta evolución |
|---|---|
| `lks-sdd-help` | Explicar el recorrido completo y su estado, configuración, responsables, pendientes y siguiente acción sin mutación. |
| `lks-sdd-define` | Definir/evolucionar proceso, petición, distribución del trabajo, criterios y controles; preparar decisiones, excepciones y relevos documentales. |
| `lks-sdd-adopt-existing` | Incorporar configuración e historia recuperable de proyectos existentes sin inventar intenciones o responsables. |
| `lks-sdd-assess-readiness` | Comprobar cobertura, identidad/función exigible, asignación, rama, dependencias y decisiones críticas antes de implementar. |
| `lks-sdd-implement` | Implementar, registrar contribuciones y continuidad, ejecutar/obtener análisis y corregir dentro de alcance. |
| `lks-sdd-verify` | Comprobar resultado exacto, vigencia de evidencias, revisiones y condiciones ordinarias o excepcionales de cierre e integración, conservando los resultados reales. |

La comprobación del flujo y la explicación didáctica de cada paso son comunes a todas
las skills. Cambiar de capacidad no inicia otro proceso ni elimina una autorización
vigente, una excepción delimitada o un pendiente.

Las pruebas futuras deben cubrir tanto recorridos satisfactorios como límites:
clones independientes, identidades ambiguas, cambios de política, relevos rechazados,
informes ajenos al código, caídas de herramientas y controles declarados no utilizados.
Los cien casos de aceptación siguen pendientes de ejecución. La validación
documental de esta propuesta no acredita esos comportamientos en el runtime.

## 14. Decisiones propuestas para la revisión conjunta

El alcance funcional está descrito para su revisión. Se proponen las siguientes
opciones concretas; el diseño se desarrolla en la propuesta técnica vinculada.
Su validación conjunta debe preceder a la planificación y al código.

| Decisión | Propuesta base | Concreción en el diseño técnico |
|---|---|---|
| Configuración y equipo | Política versionada por proyecto, miembros estables y funciones acumulables según reglas. | Tipos, campos, relaciones con AUTH/EXEC/CKPT/EVID y efectos sobre huellas. |
| Identidad del operador | Vinculación local reutilizable con procedencia y garantía explícitas; ambigüedad impide atribución formal. | Mecanismos realmente disponibles por host y operaciones que admiten identidad declarada. |
| Delegación parcial | TASK vinculada para trabajo con aceptación independiente; contribución para ayuda puntual. | Representación de aceptación, activación conjunta y recuperación de conflictos. |
| Flujo | Pasos configurables, agrupados o condicionados y trabajo en paralelo; revisiones proporcionales y responsables explícitos. | Correspondencia con estados vigentes y validación de dependencias/cobertura. |
| Evolución del proceso | Vigencia y aplicación explícita a trabajo nuevo o abierto, con correspondencia de pasos e historia conservada. | Efectos sobre huellas, autorizaciones y vistas cuando conviven versiones. |
| Excepciones | Vía concreta de solicitud, validación, aplicación y resolución; distinguir continuar, aplazar, omitir y cerrar con reservas. | Adaptación del método a este alcance, estados/relaciones y compatibilidad con las reservas actuales, sin alterar fuentes canónicas en esta propuesta. |
| Acompañamiento | Estado del recorrido completo y orientación al completar cada paso; lenguaje sencillo, recomendaciones fundamentadas y sin aprobaciones redundantes. | Representación compartida de estado y verificación de ejemplos de interacción en ambos hosts. |
| Agilidad | Ficha proporcional al cambio, decisiones agrupadas, cero confirmaciones redundantes y reutilización justificada. | Resolución incremental de contexto y observación de recorridos de uso, sin telemetría central ni controles por cada comando. |
| Eficiencia de contexto | Carga por versión y operación, contratos literales pertinentes, una copia por bloque y ampliación ante dudas. | Paquete derivado, invalidación por inventario/dependencias, límites de sobrecarga y medición de la tarea completa con calidad preservada. |
| Validación de propuesta | Revisión conjunta funcional/técnica exacta antes de planificar. | Instantánea, decisión y vínculos al plan; revalidación selectiva por cambio material. |
| Git e identidades | Rama por petición; UUIDv4 permanente y alias legible; referencias inequívocas sin renumeración obligatoria al integrar. | Generador, rutas, presentación, detección de colisiones y transición integral de lectores/escritores. |
| Controles | Sonar y Dependency-Check independientes, obligatorios al usarse salvo decisión informativa expresa; no uso documentado permitido. | Formato de política/evidencia y medios autorizados concretos por proyecto, sin construir integraciones de CI/CD. |
| Conservación | Evidencia recuperable, historia por adición y correspondencias explícitas para legado. | Ubicaciones, periodos, integridad y minimización de datos conforme al proyecto. |
| Adopción y compatibilidad | Destino propuesto v3.0.0; transición explícita 2.x → 3.x, sin migración automática ni atribución retrospectiva. | Método 3.0.0 y schema 3.0 propuestos; lectores de origen, mapa de conservación, corte, recuperación y continuidad selectiva. |

Los nombres de personas, destinos Git, umbrales, versiones de herramientas y requisitos
de separación de funciones son decisiones de cada proyecto consumidor. Se contempla
su configuración; no es necesario elegir valores corporativos universales para
comprender esta propuesta, ni se inventan para darla por implementable.

Tras validar la propuesta funcional y técnica se podrá materializar PLAN/TASK de
mantenimiento con sus criterios, dependencias y autorización. La redacción permanece en
`specs/proposed/`; no modifica `specs/canonical/`, no activa políticas o identidades en
consumidores y no añade skills, MCP, conectores, hooks, apps o agentes ejecutables.
