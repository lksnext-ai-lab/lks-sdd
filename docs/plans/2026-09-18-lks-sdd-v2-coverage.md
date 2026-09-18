# LKS-SDD 2: cobertura de mejoras y escenarios de aceptación

Fecha: 2026-09-18. Estado: alcance aprobado; seguimiento de implementación en
[expediente v2](../validation/v2-implementation.md).
Complemento obligatorio del [plan de implementación](2026-09-18-lks-sdd-v2-implementation.md).

Esta matriz permite revisar la cobertura en ambos sentidos: propuesta → tarea →
escenario y tarea → motivo. Contiene 67 mejoras, 48 tareas y 60 escenarios.
Cada mejora tiene una tarea principal y contribuyentes; no asigna responsables
reales ni sustituye la autorización del usuario. Los estados de familia conservados
abajo no son resultados unitarios: cada canal se acredita por separado en el expediente.

## 1. Procedencia de las mejoras

Los códigos S identifican bloques de la conversación, no requisitos canónicos
ya aprobados. La versión 2 y las recomendaciones D01–D07 fueron aprobadas por el
usuario para implementar. No se hereda aceptación de ninguna release anterior.

| Fuente | Necesidad / propuesta consolidada |
|---|---|
| S00 | Brief original: variantes tecnológicas aprobables, observers seguros y verificación ágil/proporcional |
| S01 | Consulta humana, documentación primero, código condicionado, fuentes enlazadas y lenguaje profesional |
| S02 | Proyecto/funcionalidades/tareas, anidación, evolución, catálogo histórico y solicitudes extensas |
| S03 | Comportamiento durante todo el ciclo, legado, casos especiales, colaboración, continuidad y seis skills |
| S04 | Revisión crítica del guardrail: contexto suficiente, autoridad, diff real, autoconformidad y límites del host |
| S05 | Rediseño general v2: documentación híbrida, núcleo común, instrucciones, protección, validación y distribución |
| S06 | Corrección de estructura: 02-specification numerada, carpeta por FTR, subcarpetas útiles y jerarquía lógica |
| S07 | Relaciones navegables en Markdown, IDs/anclas, rutas relativas y validación del destino |
| S08 | Migrador oficial, transformación sin pérdida, decisiones semánticas, staging, recuperación y convivencia |
| S09 | Decisión de versión 2 y petición de plan completo revisado sin omisiones |

Fuentes de repositorio y situación de partida: sección 2 del plan. El brief aportado
se usa como requisito del producto; la autorización procede de la petición posterior
del usuario de implementar el plan completo.
No se persisten rutas personales al adjunto ni datos de consumidores reales.

## 2. Matriz mejora → tarea → prueba

La tarea principal es responsable de cerrar la mejora; sus contribuyentes no crean
otra fuente canónica. La ejecución de cada caso debe comprobar sus obligaciones
semánticas, no únicamente que exista una fila con su ID.

| Mejora | Fuente | Contenido incluido | Principal | Contribuyentes | Casos |
|---|---|---|---|---|---|
| R001 | S05 | Contrato del producto, registros de trabajo/evidencia y vistas derivados con autoridad separada. | T005 | T010 | C001, C003 |
| R002 | S06 | Bloques numerados y 02-specification/features/FTR-###/specification.md; detalles/assets solo cuando aportan contenido. | T013 | T016 | C001, C004 |
| R003 | S05 | Formato humano híbrido: prosa, listas, tablas y diagramas según necesidad; metadatos mínimos. | T006 | T021 | C001, C002 |
| R004 | S05 | Una fuente canónica por obligación/dato; índices y vistas reconstruibles sin duplicar requisitos. | T005 | T013 | C003, C016 |
| R005 | S05 | Ficha funcional con finalidad, alcance, comportamiento, reglas/excepciones, requisitos, aceptación, relaciones y evolución. | T013 | T015 | C001, C009 |
| R006 | S05 | Ficha TASK legible como fuente del trabajo; tablero derivado y responsabilidades compartidas. | T013 | T018 | C016, C025 |
| R007 | S05 | Obligaciones por etapa y riesgo en lugar de crear 22 documentos vacíos; no aplicabilidad justificada. | T005 | T015 | C004, C040 |
| R008 | S02 | Identidad estable de feature distinta de definición, incremento, release y tarea; sin equivalencias uno a uno. | T004 | T014 | C006, C016 |
| R009 | S02 | Agrupaciones distintas de funcionalidades; padre principal opcional, sin herencia de aprobación/estado/requisitos. | T014 | T004 | C005 |
| R010 | S02 | Relaciones tipadas de pertenencia, uso y dependencia; capacidades reutilizadas sin duplicación física. | T004 | T011 | C005, C011 |
| R011 | S02 | Sustituciones parciales/totales con alcance residual y efectividad; una propuesta futura no retira lo actual. | T014 | T017 | C007, C008 |
| R012 | S02 | División, fusión, retirada y cancelación preservan correspondencias e IDs históricos. | T014 | T027 | C008 |
| R013 | S03 | Distinguir corrección, evolución y refactorización por comportamiento/datos/interfaces, permitiendo combinaciones. | T024 | T014 | C010 |
| R014 | S02 | Descomposición de peticiones extensas y cobertura bidireccional; reutilizar INC/PCH/PLAN/REL/TASK sin otro gestor. | T014 | T022 | C009 |
| R015 | S02 | Catálogo ligero e historia derivados con cobertura parcial visible y exportación solo explícita. | T017 | T018 | C012, C013 |
| R016 | S04 | Separar propuesta, aprobación, implementación, verificación, despliegue y salud por definición/revisión/entorno. | T018 | T027 | C012, C032 |
| R017 | S02 | Definiciones y evidencia histórica recuperables; no basta hash ni enlace al documento actual. | T017 | T033 | C013, C045 |
| R018 | S07 | Enlaces Markdown relativos con ID y significado, destinos precisos y anclas estables. | T016 | T006 | C014 |
| R019 | S07 | Validar archivo/ancla/identidad, movimientos y enlaces históricos; relaciones inversas derivadas sin doble mantenimiento. | T016 | T017 | C015, C013 |
| R020 | S01 | Consulta docs-first/docs-only de solo lectura; documentación suficiente evita leer implementación. | T019 | T008 | C017, C021 |
| R021 | S01 | Código solo por carencia de implementación o solicitud expresa; compare acotado y nunca decide negocio. | T019 | T020 | C018, C019 |
| R022 | S01 | Respuesta profesional, neutra, no pedante, integrada y proporcional, sin exigir IDs ni volcar JSON/tablas originales. | T021 | T045 | C017, C056 |
| R023 | S01 | Fuentes por afirmación; distinguir hechos, inferencias, propuestas, decisiones, desconocidos y contradicciones. | T021 | T011 | C003, C019 |
| R024 | S05 | Modelo común normalizado con lectores versionados y sin nueva autoridad persistente. | T010 | T011 | C001, C046 |
| R025 | S04 | Contexto de consulta distinto del contrato completo de ejecución; no compactar excepciones ni obligaciones críticas. | T020 | T012 | C002, C011 |
| R026 | S03 | Incluir contribuyentes, consumidores, reglas transversales y dependencias no explícitas cuando son pertinentes. | T020 | T011 | C011, C016 |
| R027 | S04 | Huellas cubren prosa normativa, relaciones y activos; exclusión determinista de vistas y datos no contractuales. | T012 | T023 | C002, C024, C026 |
| R028 | S03 | Respetar raíz, runtime fijado e integridad; nada de fallback global silencioso o permisos por documentos. | T010 | T039 | C046, C051 |
| R029 | S03 | Readiness y plan completo separados; propietarios, DAG, integración y política incremental explícita; cancelled no es done. | T022 | T025 | C025, C030 |
| R030 | S04 | Autorización delimitada vigente, reutilizable y revocable; aprobación de plan/tecnología no implica ejecución. | T023 | T029 | C027, C037 |
| R031 | S03 | Continuidad durable, pausa/reanudación/replanificación y siguiente paso seguro sin depender del chat. | T027 | T036 | C049 |
| R032 | S04 | Contrastar diff real, impedir autoconformidad de código/especificación/pruebas y preservar cambios ajenos. | T024 | T041 | C028, C029 |
| R033 | S04 | Verificación desde aceptación acordada, casos negativos, regresión e integración; revisión humana según riesgo. | T025 | T043 | C028, C030 |
| R034 | S03 | Evidencia tipada de componente, contrato, composición, flujo, persistencia y visual ligada al resultado exacto. | T025 | T015 | C030, C031, C059 |
| R035 | S03 | EVID histórica inmutable, salud actual y re-verificación separadas; no reescribir fallos o aprobación pasada. | T027 | T033 | C032, C045 |
| R036 | S00 | Comprobaciones proporcionales: diagnóstico, desarrollo, integración y campaña de release según política. | T025 | T028 | C034, C039 |
| R037 | S00 | Caché segura de evidencia determinista, TTL e invalidación relevante; no rejuvenecer ni repetir sin motivo. | T026 | T044 | C033, C057 |
| R038 | S00 | Compatibilidad por niveles y diferencias explicadas; desconocido no es incompatible; compatible-certified exige reglas certificadas. | T028 | T003 | C035, C036 |
| R039 | S00 | Aprobación durable de variante con todos sus inputs, riesgos, scopes, referencias, responsable, etapa y caducidad. | T029 | T023 | C035, C037 |
| R040 | S00 | Observers/adapters declarados, hash/schema/scopes/aislamiento/artefactos, experimental frente a aprobado y sin sustitución silenciosa. | T030 | T008 | C038 |
| R041 | S00 | Certificación, aprobación, verificación, estado TASK y entrega separados; cierre con reservas solo bajo política y gates críticos pasados. | T030 | T027 | C039 |
| R042 | S00 | Modo estricto predeterminado, perfiles/locks/EVID preservados; recertificar entradas afectadas, nunca atribuir certificación global a variante. | T028 | T047 | C036, C039, C058 |
| R043 | S03 | Adopción acotada: suficiencia del cambio frente a cobertura global parcial, sin código ni historia inventada. | T031 | T015 | C020, C040 |
| R044 | S03 | Identidad/alias estables y colisiones entre usuarios/clones resueltas con una política explícita. | T034 | T004 | C047 |
| R045 | S03 | Revisión de contratos compartidos, cambios de base y conflictos semánticos aunque Git fusione limpio. | T035 | T024 | C048 |
| R046 | S03 | Trabajo independiente y relevo seguros; no prometer locks distribuidos ni delegación/agentes autónomos nuevos. | T036 | T035 | C048, C049 |
| R047 | S03 | Seis skills con objetivos no solapados, política común, límites y transición entre etapas proporcional a la intención. | T038 | T037 | C050 |
| R048 | S05 | Metadatos e invocación implícita; AGENTS breve gestionado con permiso; sin séptima skill, MCP, apps, hooks o agentes ejecutables. | T039 | T037 | C051 |
| R049 | S05 | Documentación interna en cinco conjuntos, contrato vigente inequívoco y reglas enlazadas a controles/pruebas. | T040 | T003 | C054 |
| R050 | S08 | Migrador oficial: diagnóstico de schema/runtime, inventario, personalizaciones, errores previos y ejecuciones abiertas. | T032 | T046 | C041, C042, C046 |
| R051 | S08 | Conversión mecánica separada de decisiones semánticas; mapa completo, IDs/contenido conservados y pendientes de clasificación. | T032 | T014 | C041, C042 |
| R052 | S08 | Preview exacto, staging, aplicación recuperable, registro, idempotencia y rollback protegido contra cambios posteriores. | T033 | T008 | C043, C044 |
| R053 | S08 | Preservar evidencia/historia/bytes, pausar ejecuciones y reconciliar autoridad; migrar no verifica ni autoautoriza. | T033 | T027 | C045 |
| R054 | S08 | Compatibilidad sin migración automática, lectura declarada, primera ruta schema 1.5 y diagnóstico para orígenes desconocidos. | T046 | T010 | C046 |
| R055 | S08 | Transición explícita del runtime fijado, un solo contrato activo y recibo con mapa/verificaciones/pendientes/recuperación. | T033 | T046 | C043, C045, C046 |
| R056 | S04 | Confidencialidad, límites de lectura/escritura y fuentes no confiables; preservar personalizaciones y no filtrar datos entre proyectos. | T008 | T011 | C021, C022, C029, C055 |
| R057 | S04 | Contrato de guardrail, verificador de integración confiable y límites honestos; habilitar CI/permisos externos solo con autorización aparte. | T041 | T024 | C052 |
| R058 | S05 | Conservar gobierno de entrega, modelos/versionado, Jira opcional, recibos e interoperabilidad sin autoridad remota implícita. | T042 | T022 | C053, C060 |
| R059 | S05 | Paridad del núcleo y aceptación real de Codex/Copilot, navegación y varios usuarios, con evidencia independiente por host. | T045 | T039 | C056 |
| R060 | S09 | Matriz adversarial heterogénea y trazabilidad mejora→tarea→prueba; conservar contraejemplos y limitar afirmaciones de cobertura. | T043 | T001, T002, T007, T008 | C001, C028, C043, C048, C055 |
| R061 | S00 | Agilidad medible: preguntas agrupadas necesarias, cero aprobaciones repetidas válidas, ejecuciones proporcionales y coste total observado. | T044 | T009 | C034, C037, C050, C057 |
| R062 | S05 | Paquetes reproducibles, Windows, instalación aislada y aprobación nueva; commit/push/publicación/instalación/activación separados. | T047 | T048 | C058 |
| R063 | S09 | Versión 2 del plugin acordada; contrato/método versionados por separado y alcance sin aplazamientos silenciosos. | T003 | T048 | C046, C054 |
| R064 | S01 | Aprendizaje progresivo, resumen management, detalle a demanda y bloqueos accionables sin jerga ni arquitectura interna obligatoria. | T021 | T040 | C050, C056 |
| R065 | S05 | Conservar suficiencia de UX, datos, identidad, seguridad, privacidad, interfaces, calidad y operación; prototipo no equivale a aceptación. | T015 | T025 | C004, C059 |
| R066 | S03 | Cambios cancelados, hotfix, rollback, flags y versiones mantenidas con vigencia/entorno explícitos y sin eludir autorizaciones. | T042 | T027 | C008, C060 |
| R067 | S01 | Búsqueda acotada con límites visibles, ampliación progresiva, descubrimiento de fuentes nuevas y snapshots consistentes. | T011 | T012, T021 | C023, C024 |

## 3. Cobertura inversa de tareas

Todas las tareas del plan tienen una finalidad cubierta. Las tareas de QA,
documentación, referencia inicial y release son parte de la entrega, no trabajo
funcional añadido al consumidor.

| Tarea | Paquete | Mejoras a las que contribuye |
|---|---|---|
| T001 | P00 | R060 |
| T002 | P00 | R060 |
| T003 | P00 | R038, R049, R063 |
| T004 | P01 | R008, R009, R010, R044 |
| T005 | P01 | R001, R004, R007 |
| T006 | P01 | R003, R018 |
| T007 | P02 | R060 |
| T008 | P02 | R020, R040, R052, R056, R060 |
| T009 | P02 | R061 |
| T010 | P03 | R001, R024, R028, R054 |
| T011 | P03 | R010, R023, R024, R026, R056, R067 |
| T012 | P03 | R025, R027, R067 |
| T013 | P04 | R002, R004, R005, R006 |
| T014 | P04 | R008, R009, R011, R012, R013, R014, R051 |
| T015 | P04 | R005, R007, R034, R043, R065 |
| T016 | P05 | R002, R018, R019 |
| T017 | P05 | R011, R015, R017, R019 |
| T018 | P05 | R006, R015, R016 |
| T019 | P06 | R020, R021 |
| T020 | P06 | R021, R025, R026 |
| T021 | P06 | R003, R022, R023, R064, R067 |
| T022 | P07 | R014, R029, R058 |
| T023 | P07 | R027, R030, R039 |
| T024 | P07 | R013, R032, R045, R057 |
| T025 | P08 | R029, R033, R034, R036, R065 |
| T026 | P08 | R037 |
| T027 | P08 | R012, R016, R031, R035, R041, R053, R066 |
| T028 | P09 | R036, R038, R042 |
| T029 | P09 | R030, R039 |
| T030 | P09 | R040, R041 |
| T031 | P10 | R043 |
| T032 | P10 | R050, R051 |
| T033 | P10 | R017, R035, R052, R053, R055 |
| T034 | P11 | R044 |
| T035 | P11 | R045, R046 |
| T036 | P11 | R031, R046 |
| T037 | P12 | R047, R048 |
| T038 | P12 | R047 |
| T039 | P12 | R028, R048, R059 |
| T040 | P13 | R049, R064 |
| T041 | P13 | R032, R057 |
| T042 | P13 | R058, R066 |
| T043 | P14 | R033, R060 |
| T044 | P14 | R037, R061 |
| T045 | P14 | R022, R059 |
| T046 | P15 | R050, R054, R055 |
| T047 | P15 | R042, R062 |
| T048 | P15 | R062, R063 |

## 4. Escenarios de aceptación

Los C son familias de escenarios, no el número final de tests unitarios. Cada una
requiere variantes positivas y negativas pertinentes. Los fixtures serán sintéticos;
se incorporarán copias anonimizadas reales solo con autorización. No declarar
cobertura universal por pasar esta matriz.

Canales: A = automatizable; S = revisión semántica; H = sesión humana/host;
D = ejecución aislada Docker/navegador cuando corresponda; E = control externo
habilitado únicamente con autorización. La simulación de E no acredita el sistema
real. Toda combinación conserva resultados separados y evidencia de su alcance.

| Caso | Situación | Resultado exigido | Tarea de referencia | Canal | Estado v2 |
|---|---|---|---|---|---|
| C001 | Proyecto nuevo v2 con documentos híbridos | Prosa, tablas, bloques y activos se leen con IDs y autoridad correctos; validación estructural y lectura humana independientes. | T013 | A + S | not-run |
| C002 | Excepción, negación o límite fuera de tabla | El contrato y su huella incluyen la obligación; cambiarla invalida el contexto sin omitirla por compactación. | T012 | A + S | not-run |
| C003 | IDs duplicados, referencias huérfanas o autoridad contradictoria | No seleccionar una interpretación por fecha, nombre o coincidencia con código; diagnóstico localizado. | T011 | A + S | not-run |
| C004 | Anexo no aplicable, pendiente o ausente | Distinguir los tres casos; no crear vacío ni usar no aplicable para ocultar una decisión. | T015 | A + S | not-run |
| C005 | Jerarquía, agrupación, usos múltiples y ciclos | Padre principal opcional y agrupación no ejecutable; sin herencia implícita; relaciones tipadas y ciclos indebidos rechazados. | T014 | A + S | not-run |
| C006 | Evolución manteniendo propósito | Conservar identidad y asociar nueva definición e incremento; renombrar o reagrupar no cambia comportamiento. | T014 | A + S | not-run |
| C007 | Sustitución parcial con versiones simultáneas | Conservar alcance residual y fechas/contextos efectivos; propuesta futura no retira comportamiento desplegado. | T017 | A + S | not-run |
| C008 | Sustitución total, división, fusión y cancelación | Correspondencias e historia recuperables; no reciclar IDs ni convertir cancelación en implementación. | T014 | A + S | not-run |
| C009 | Solicitud extensa con varias funcionalidades | Cobertura bidireccional petición↔definición↔plan; tareas compartidas válidas, sin alcance añadido. | T014 | A + S | not-run |
| C010 | Bug, evolución y refactorización combinados | Clasificar intención y cambios de comportamiento/datos/interfaces; no inventar contrato original ni omitir impactos técnicos. | T024 | A + S | not-run |
| C011 | Cambio transversal y obligación sin enlace explícito | Recuperar consumidores y restricciones relevantes; incertidumbre crítica amplía o bloquea; trabajo independiente no se bloquea sin motivo. | T020 | A + S | not-run |
| C012 | Catálogo con futuro aprobado y pasado verificado | Separar estados por definición y contexto; no declarar completado por contar tareas ni hacer del catálogo autoridad. | T018 | A + S | not-run |
| C013 | Consulta histórica con y sin objetos Git/snapshot | Recuperar fuente exacta disponible sin checkout/fetch; si falta, declarar el hueco; no citar archivo actual como histórico. | T017 | A + S | not-run |
| C014 | Enlace relativo, ID, espacios, Unicode y clones | Abrir el elemento correcto en los hosts ensayados; mantener texto comprensible e ID; sin rutas personales en documentos compartidos. | T016 | A + H | not-run |
| C015 | Destino de enlace incorrecto, movido o fuera de raíz | Validar ID y ancla, registrar redirección/mapeo autorizado al mover; no leer rutas no autorizadas ni ejecutar contenido. | T016 | A + S | not-run |
| C016 | Una tarea contribuye a varias funcionalidades | Ficha única y tablero derivado; contexto incluye responsabilidad principal y contribuyente sin doble edición de estados. | T013 | A + S | not-run |
| C017 | Consulta docs-first suficiente y docs-only incompleta | Cero lecturas de implementación; respuesta documentada o límite explícito, sin diagnóstico pesado ni adopción. | T019 | A + S | not-run |
| C018 | Carencia de implementación o compare explícito | Ampliación acotada con motivo y snapshot vigente; observación separada de acuerdo y de ejecución real. | T019 | A + S | not-run |
| C019 | Decisión de negocio no documentada | No sustituirla por comportamiento del código; mantener pendiente y preguntar solo si afecta a la acción. | T021 | A + S | not-run |
| C020 | Legado sin manifest, FTR o tareas históricas | Usar fuentes disponibles, declarar cobertura parcial y no inventar inexistencia, tareas, fechas o aprobaciones. | T031 | A + S | not-run |
| C021 | Trampas de escritura o ejecución durante consulta | Cero archivos, bytecode, logs, cachés persistentes, hooks, builds, pruebas, servicios y red del consumidor. | T019 | A + S | not-run |
| C022 | Secretos, symlink/junction, submódulo y escape de raíz | No ampliar alcance ni exponer contenido sensible; documentar límites de detección y aislamiento entre proyectos. | T011 | A + S | not-run |
| C023 | Monorepo, ruido, búsqueda vacía y límites | Coste acotado y ampliación progresiva; truncamiento no se presenta como completitud ni ausencia como inexistencia. | T021 | A + S | not-run |
| C024 | Fuentes cambian durante lectura; aparece documento nuevo | No mezclar snapshots; revalidar, reintentar acotadamente o informar; redescubrir nuevas fuentes. | T012 | A + S | not-run |
| C025 | Plan parcial y porción lista con dependencia cancelada | Separar ejes; admitir solo política incremental confirmada; cancelled no satisface done. | T022 | A + S | not-run |
| C026 | Cambio de prosa contractual o vista regenerada tras AUTH | El primero se detecta; la segunda no invalida por sí sola; exclusiones deterministas, no juicio libre del agente. | T023 | A + S | not-run |
| C027 | AUTH ausente, revocada, obsoleta o con rol declarado | Rechazar acción no autorizada y reutilizar la válida; un hash o actor textual no se presenta como autenticación externa. | T023 | A + S | not-run |
| C028 | Código fuera de alcance y aceptación/prueba debilitadas | Comparar con baseline aprobada; no autocertificar el conjunto modificado; revisión específica de gates y verificadores. | T024 | A + S | not-run |
| C029 | Worktree sucio y personalizaciones locales | Preservar cambios ajenos, secretos/configuración personal y límites; no sobrescribir para conseguir validación. | T024 | A + S | not-run |
| C030 | Componentes pasan, pero integración o persistencia fallan | No cerrar alcance conjunto con evidencia inferior, mocks de dominio o capturas sin comunicación/persistencia real. | T025 | A + D + S | not-run |
| C031 | EVID de revisión/build/artefacto/entorno distintos | Rechazar reutilización y cierre; evidencia visual e interfaces corresponden al sujeto exacto. | T025 | A + D + S | not-run |
| C032 | EVID histórica correcta y defecto posterior | Mantener evidencia inmutable, cambiar salud actual y gestionar corrección/re-verificación sin reescribir el pasado. | T027 | A + S | not-run |
| C033 | Caché caducada, inputs cambiados o gate no determinista | No reutilizar; conservar edad original; distinguir executed/reused/omitted, sin rejuvenecer al emitir otra EVID. | T026 | A + S | not-run |
| C034 | Diagnóstico y desarrollo frente a integración/release | No ejecutar trabajo pesado innecesario; ejecutar los controles exigidos por riesgo/etapa; omisión crítica nunca passed. | T025 | A + S | not-run |
| C035 | Variante válida con versiones/dependencias/composición distintas | Diagnosticar, aprobar una vez y verificar el alcance; no convertirla en certificación global ni cambiar stack. | T028 | A + S | not-run |
| C036 | Combinación desconocida y contradicción técnica real | Distinguirlas; compatible-certified solo con reglas certificadas que lo soporten; allow-unvalidated/force no aprueban. | T028 | A + S | not-run |
| C037 | Aprobación tecnológica expira o cambian inputs aprobados | Revisar solo cuando stack, observer, alcance, etapa, entorno o política relevante cambien; no repetir por código ordinario sin cambio tecnológico. | T029 | A + S | not-run |
| C038 | Observer falso, alterado, experimental o intento de escape | Hash, imagen/comando, nonce, schema, scopes y artefactos comprobados; aislamiento real; stdout passed no basta ni escribe estados canónicos. | T030 | A + D + S | not-run |
| C039 | Cierre de variante con reservas y promoción de entorno | Cerrar solo con política, aprobación vigente y gates críticos pasados; desarrollo no aprueba release/producción. | T030 | A + S | not-run |
| C040 | Adopción acotada con legado amplio y dependencia desconocida | Conservar cobertura global parcial; exigir suficiencia del ámbito y dependencias; no exigir documentar todo ni ignorar un bloqueo crítico. | T031 | A + S | not-run |
| C041 | Migración 1.5 válida con vínculos, decisiones y activos | Mapa completo de origen/destino, mismos IDs y obligaciones; original preservado; enlaces correctos y v2 válida. | T032 | A + S | not-run |
| C042 | Migración con prosa personalizada, conflicto o feature ambigua | Conservar todo contenido y procedencia; separar transformación mecánica de propuesta semántica; clasificación pendiente sin inventar. | T032 | A + S | not-run |
| C043 | Interrupción, cambio de origen y repetición de migración | Staging/journal recuperables; preview obsoleto rechazado; repetir no duplica contenido; runtime/índice/documentos coherentes. | T033 | A + S | not-run |
| C044 | Rollback con trabajo posterior | Detectar divergencia y no borrar cambios posteriores; restauración exacta cuando procede y conflicto explicado cuando no. | T033 | A + S | not-run |
| C045 | Migración con AUTH, EXEC, CKPT, TASK done y EVID | Pausar/reconciliar; conservar historia/bytes EVID; no autoautorizar ni declarar nueva verificación; no dos contratos activos. | T033 | A + S | not-run |
| C046 | Instalación v2 con proyecto fijado a v1 y schema desconocido | No convertir ni escribir; respetar runtime fijado; lectura compatible declarada y migración solo por ruta dedicada autorizada. | T046 | A + S | not-run |
| C047 | Dos clones crean identidades/alias coincidentes | Detectar y resolver mediante política confirmada; conservar referencias e historia, sin renumeración silenciosa. | T034 | A + S | not-run |
| C048 | Merge limpio de dos cambios semánticamente incompatibles | Reconciliar contrato compartido y verificar integración; locks locales no se presentan como coordinación distribuida. | T035 | A + S | not-run |
| C049 | Pausa, nuevo chat/usuario, bloqueo, cancelación y reapertura | Releer fuentes/revisión/autoridad; continuar solo cuando corresponde; checkpoint no es commit ni autorización. | T036 | A + S | not-run |
| C050 | Intenciones naturales y explícitas de las seis skills | Routing correcto, límites de acción, preguntas agrupadas necesarias y reutilización de decisiones; explicación no implementa. | T038 | A + H | not-run |
| C051 | Metadatos, AGENTS personalizado y adaptadores | Invocación implícita, seis entradas, núcleo fijado, bloques gestionados con permiso; cero agentes ejecutables/hook/MCP nuevos. | T039 | A + H | not-run |
| C052 | Control CI con cambios en política/tests y permisos amplios | Verificador usa referencia confiable, distingue revisión semántica y autenticación; no proclama bloqueo de escrituras directas del host. | T041 | A + S; E aparte | not-run |
| C053 | Jira remoto Done, recibo incierto y tracking local | Conservar autoridad canónica; no otorgar AUTH/EVID/cierre ni repetir operación externa incierta; repository-only completo. | T042 | A + S; E aparte | not-run |
| C054 | Guías vigentes e instrucciones históricas contradictorias | Fuente normativa actual inequívoca, ejemplos y CLI concordantes, fuentes canónicas antiguas intactas. | T040 | A + S | not-run |
| C055 | Prompt injection en documentos/código/enlaces | Tratarlo como datos; no ampliar autoridad, leer secretos ni ejecutar órdenes incrustadas. | T008 | A + S | not-run |
| C056 | Codex/Copilot reales, varios usuarios y navegación | Resultados por host con versiones/escenarios/evidencia; no inferir paridad desde paquetes ni imágenes generadas como aceptación. | T045 | A + H | not-run |
| C057 | Rendimiento frío/caliente y repetición | Presupuestos predefinidos y medición total incluyendo relecturas/preguntas/procesos; calidad primero, sin ajustar umbrales para aprobar. | T044 | A | not-run |
| C058 | Dos builds, extracción Windows y activación | Mismos bytes desde mismo origen limpio, rutas compatibles y seis skills; publicación/instalación/activación separadas y autorizadas. | T047 | A | not-run |
| C059 | UX nueva/modificada, accesibilidad y prototipos | Brief, estados, flujos y aceptación explícitos; material generado sigue propuesto; revisión visual separada de integración/persistencia. | T015 | A + D + H | not-run |
| C060 | Hotfix, rollback, flags y varias versiones mantenidas | Delimitar versión/entorno/activación y riesgos; no borrar historia ni aprobar despliegue; aceptación operacional separada. | T042 | A + S | not-run |

## 5. Casos compuestos obligatorios

Además de probar las familias por separado, ejecutar al menos estas combinaciones:

| Combinación | Familias | Riesgo que debe quedar demostrado |
|---|---|---|
| Legado parcial + cambio transversal + regla sin enlace | C011, C020, C040 | No aprobar el cambio con contexto insuficiente ni exigir documentar todo el sistema |
| Sustitución parcial + dos versiones + despliegue retrasado | C007, C012, C060 | No retirar anticipadamente el comportamiento anterior |
| Tarea contribuyente + pausa + cambio de regla compartida | C016, C026, C049 | No reanudar con contexto o autorización obsoletos |
| Variante + observer alterado + caché previa válida | C033, C037, C038 | No reutilizar una aprobación o evidencia que ya no cubre la ejecución |
| Migración + ejecución abierta + interrupción + trabajo posterior | C043, C044, C045 | Recuperación segura sin borrar trabajo ni fabricar nueva autoridad |
| Dos clones + alias coincidente + merge textual limpio | C047, C048, C049 | Identidad y semántica coherentes sin fingir bloqueo distribuido |
| Consulta histórica + enlace movido + fuente ausente | C013, C015, C024 | No citar la versión actual como si fuera la fuente histórica |
| Código incorrecto + especificación y prueba debilitadas | C026, C028, C052 | No convertir la autoconformidad en resultado verificado |
| Nuevo frontend + observer de variante + ausencia de aceptación visual | C030, C038, C039, C059 | No cerrar por imagen generada, stdout o componente aislado |
| Actualizar plugin + proyecto antiguo + consulta natural | C017, C046, C050, C051 | Ninguna migración/instalación/reescritura implícita del consumidor |

## 6. Organización prevista de las pruebas

Nombres orientativos de módulos nuevos, no archivos existentes ni decisiones de
implementación cerradas. Reutilizar suites actuales donde cubran el mismo contrato,
conservar expectativas históricas y registrar cada módulo en un único tier.

| Grupo propuesto | Familias principales | Tipo |
|---|---|---|
| test_v2_document_contract | C001–C016 | Lectores, estructura, identidad, reglas, enlaces e historia |
| test_v2_query_context | C017–C024 | Consulta, suficiencia, snapshots y coste de lectura |
| test_v2_lifecycle | C025–C034, C049 | Planificación, autoridad, diff, evidencia y continuidad |
| test_v2_project_variants | C035–C039 | Diagnóstico, aprobación, observer y política de cierre |
| test_v2_adoption_migration | C040–C046 | Adopción, conversión, recuperación y runtime |
| test_v2_collaboration | C047–C048 | Colisiones y conflictos semánticos |
| test_v2_skills_hosts | C050–C051, C056 | Routing, metadatos y protocolo de aceptación real |
| test_v2_delivery_controls | C052–C054, C059–C060 | CI, tracking, docs, UX y gobierno de entrega |
| test_v2_untrusted_inputs | C055 | Instrucciones hostiles y aislamiento de autoridad |
| test_v2_experience | C057 | Agilidad y presupuesto operativo |
| test_v2_distribution | C058 | Paquetes, Windows y reproducibilidad |

La aceptación humana y la habilitación externa tienen registros propios; los
módulos automáticos solo validan sus contratos/fixtures cuando no hay ejecución real.

## 7. Revisión de cobertura y no regresión

Lista de comprobación del plan:

- [x] Brief original de variantes descompuesto; se incluyen observers, aislamiento,
  schemas, revisión, caducidad, reservas, caché y certificación separada.
- [x] Consulta documental humana, contraste con código y legado parcial incluidos.
- [x] Organización numerada y subcarpetas coherentes con la última propuesta.
- [x] Identidad funcional, jerarquía lógica, evolución, sustituciones y solicitudes
  extensas tienen tareas y pruebas; la historia exige fuentes recuperables.
- [x] Referencias Markdown incluidas en parser, validación, portabilidad y migración.
- [x] Documento híbrido y prosa normativa protegidos por contexto y huellas.
- [x] Contexto primario/contribuyente y obligaciones transversales incluidos.
- [x] Autorización, continuidad, diff real, pruebas debilitadas y evidencia exacta incluidos.
- [x] Migración oficial completa incluida en la entrega, no relegada a una versión futura.
- [x] Concurrencia, identidad entre clones y conflictos sin choque textual incluidos.
- [x] Seis skills, instrucciones compartidas, AGENTS y metadatos cubiertos.
- [x] UX/accesibilidad, datos, seguridad, interfaces, operación y Jira opcional preservados.
- [x] Guardrail externo incluido como contrato/verificador/ejemplos, no configuración remota implícita.
- [x] Rendimiento y pruebas por host separados de tests estructurales y de paquete.
- [x] Compatibilidad, runtime fijado, instalación, publicación y activación diferenciados.
- [x] 67 mejoras, 48 tareas y 60 escenarios relacionados sin huérfanos; se comprueba el DAG.

Estas marcas significan «incluido y revisado en la planificación». No significan
implementación, prueba passed, aprobación de ejecución ni aceptación de release.
La revisión cubre las propuestas identificadas S00–S09; una nueva necesidad
posterior requiere actualizar explícitamente el plan y su matriz.

## 8. Registro de resultados futuro

Al ejecutar el plan, cada escenario registrará fixture, origen exacto, inputs,
resultado esperado y observado, evidencias, canal y limitaciones. Los hallazgos
crearán correcciones vinculadas sin borrar el resultado previo. Un incumplimiento
crítico bloquea el cierre del ámbito afectado y del claim de release correspondiente.

No se crean aprobaciones, identidades reales, porcentajes de avance o resultados
de pruebas como efecto de redactar esta matriz.
