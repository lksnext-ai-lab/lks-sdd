# Changelog

## 0.9.1 — 2026-08-23 — posicionamiento Spec-anchored

- Explicita LKS-SDD como metodología Spec-anchored: la especificación permanece como contrato vivo, versionado y confiable durante definición, planificación, implementación y verificación.
- Diferencia de forma didáctica Spec-first, Spec-anchored y Spec-as-source, sin presentar la generación de código como prueba de conformidad.
- Refuerza la adopción de repositorios existentes como construcción de una baseline documental desde evidencia del `as-is`, separada de la intención y aceptación que requieren confirmación humana.
- Explica el valor para empresas de servicios: documentación contrastable con el cliente y vistas derivadas con procedencia, clasificación y revisión, sin crear otra fuente canónica.
- Actualiza manifiesto, ayuda, onboarding, FAQ, arquitectura, capacidades, metadatos de interfaz y el caso de activación `ACT-019`; mantiene las seis skills, el método 1.3, el esquema 1.3 y los perfiles sin cambios funcionales.
- No requiere migración de proyectos consumidores y conserva la release como candidate; los canales humanos, semánticos y de piloto no ejecutados permanecen `not-run`.

## 0.9.0 — 2026-08-22 — planificación integral y continuidad autónoma

- Añade el contrato de método 1.3 y separa explícitamente readiness de especificación, soporte de automatización, completitud e integridad de planificación, readiness de la porción seleccionada, implementación, verificación y entrega.
- Emite un handoff orientado a acción cuando la especificación está cerrada, sin presentar una tarea `ready` como planificación completa ni usar un `ready` global ambiguo.
- Incorpora `ART-PLANNING` con objetivo, política `complete-before-implementation` o `incremental-authorized`, propiedad primaria de todo el contrato activo, contribuyentes, autorizaciones y cambios `PCH-###`.
- Deriva huecos concretos de requisitos, aceptación, pruebas y obligaciones activas; valida definiciones ejecutables, release, ausencia de propiedad duplicada, DAG acíclico, raíces, fronteras paralelas e integración conjunta.
- Mantiene el camino crítico como `undetermined` cuando no existen duraciones confirmadas y no inventa fechas, esfuerzo, velocidad, capacidad, avance, autoridad ni evidencia.
- Añade autorizaciones `AUTH-###` ligadas a tareas y fingerprints separados de especificación y planificación; persisten entre pausas y se invalidan ante divergencia, cambio de alcance o revocación.
- Añade ejecuciones `EXEC-###` y checkpoints `CKPT-###` versionables con revisión, rama, archivos y hashes observados, entregables, aceptación, gates, evidencia, bloqueos, siguiente acción y trabajo paralelo seguro.
- Endurece dependencias: `cancelled` ya no equivale a `done`. Reabrir una tarea terminada exige un `PCH-###` confirmado por fallo del contrato original; el alcance nuevo crea otra tarea.
- Impide iniciar una tarea 1.3 sin `EXEC-###` activa y marcarla `done` mediante referencias declarativas: revisión, build, artefacto, entorno y gates deben coincidir con una evidencia canónica `verified` enlazada a la ejecución.
- Añade comandos portables `planning` y `continuity`, integra el checkpoint inicial en la preparación autorizada y valida al reanudar si procede continuar, reconciliar o replanificar.
- Añade migración explícita y reversible `1.2 → 1.3`, que crea cobertura y continuidad pendientes sin inventar tareas, completitud, autorización, ejecución, checkpoint, avance o evidencia.
- Conserva el workflow histórico de tareas migradas, pero separa su readiness ejecutable: una tarea 1.2 antes `ready` queda visible como tal y bloqueada para ejecución hasta completar la definición 1.3.
- Actualiza las seis skills, ayudas, plantillas, esquemas, documentación, validadores, pruebas y escenarios, incluido el caso real de `prueba-calculadora` con especificación cerrada, `TASK-001` ready y release todavía parcial.
- Mantiene la release como candidate y los canales humanos, semánticos o de piloto no ejecutados como `not-run`; no instala ni activa el plugin al publicarlo.

## 0.8.0 — 2026-08-21 — gobierno de entrega y arquitectura multiperfil

- Añade el contrato de método 1.2 para definir antes de G2 el modelo de entrega, versionado, Git/ramas, CI/CD, entornos, promoción, despliegue, observabilidad y recuperación, sin imponer una estrategia única.
- Modela `bounded-release`, `continuous-evolution` y `maintenance-stream`, y registra cambios posteriores como transiciones `CHG-###` trazables que no reescriben el historial.
- Incorpora planificación por horizontes `PLAN-###`, releases `REL-###` y tareas `TASK-###`, con tablero visual, detalle independiente, dependencias, problemas `PROB-###`, gates y evidencias.
- Añade transiciones de tarea validadas mediante preview, hash de autorización y escritura atómica; completar una tarea exige evidencia, revisión, build, digest y entorno.
- Sustituye el acoplamiento operativo a H0 por un registro multiperfil con familias, capabilities internas, perfiles cerrados, drivers genéricos, bindings por unidad desplegable y locks 2.0.
- Incorpora diez perfiles de referencia: React y Angular estáticos, dos variantes API-only, Next.js SSR, Angular SSR, sistemas web completos React y Angular, worker RabbitMQ y procesador Kafka.
- Declara seis perfiles active y cuatro candidate; solo un active con certificación exacta vigente puede ser `supported`. Un lock identifica la composición, pero no acredita compatibilidad sin gates por capability y gate end-to-end de la composición.
- Añade scaffolds, gates y certificaciones ligadas por hash a descriptor, capabilities, driver, scaffold, composición y motor; cualquier deriva invalida el soporte hasta recertificar.
- Aísla `node_modules` y `.venv` de los gates Docker en volúmenes Linux efímeros con limpieza registrada, evitando que el rendimiento de bind mounts Windows haga fallar de forma intermitente Vitest o mypy; el harness identifica además el check interno que provoca un fallo.
- Generaliza readiness, preparación y verificación a múltiples bindings y tareas, y exige que G3/G4 queden ligados a revisión Git, tree ID/hash, build, digest de artefacto y entorno.
- Añade la migración explícita y reversible `1.1 → 1.2`, que crea gobierno, arquitectura, planes, tareas y bindings pendientes sin inventar decisiones ni evidencias.
- Amplía el harness con FX-22–FX-27 y crea un corpus conversacional 0.8 independiente, todavía `not-run`; el corpus 0.7 queda histórico y no acredita esta línea de producto.
- Actualiza las seis skills, prompts, ayudas, esquemas, plantillas, documentación, metadata, validadores, tests y nota de release; mantiene los canales humanos y de piloto no ejecutados como `not-run`.

## 0.7.0 — 2026-08-20 — contrato documental y handoff fiable

- Unifica el análisis de artefactos, tablas, estados y referencias para que validación, ayuda, trazabilidad y readiness consuman el mismo contrato documental normalizado.
- Endurece las referencias individuales, listas y rangos inclusivos `..`: evita expansiones parciales silenciosas y admite las formas legacy `a` o separadas por espacios solo en compatibilidad, con aviso.
- Separa relaciones activas de elementos históricos y calcula fingerprints distintos para integridad documental e inputs activos de implementación.
- Añade una matriz de aplicabilidad por dominio para datos, identidad, seguridad, privacidad e integraciones sin forzar un único estado agregado.
- Hace fallar de forma explícita la trazabilidad vacía o incompleta, incorpora un preflight de handoff y separa readiness funcional de soporte automatizado sin convertir limitaciones del perfil en defectos de la especificación.
- Añade diagnósticos estructurados, localizados y agrupados por causa raíz, manteniendo una vista textual compatible para los consumidores existentes.
- Añade la migración explícita 1.0 → 1.1 con dry-run y cierre seguro: cualquier entrada de `human_review_required` bloquea siempre la aplicación antes de crear backup o escribir hasta resolver el Markdown 1.0 de origen y repetir el preview. La dimensión agregada `Identity` se traslada sin inferencias a tres aplicabilidades `pending` con motivo; permite completar la migración si no existen otras revisiones, pero bloquea readiness hasta resolverse en 1.1.
- Incorpora fixtures y regresiones del recorrido real de la calculadora para cubrir el handoff `define → validate → help → traceability → readiness → prepare → verify-plan` que no representaban los happy paths anteriores.
- Cierra la puerta de verificación sobre el registro real de implementación: el plan anticipatorio solo admite el mismo incremento en `in-progress` o `completed`, y la ejecución o el registro de evidencia exigen `implementation.status=completed` y un perfil coherente antes de invocar checks o escribir archivos.
- Endurece la atestación y el empaquetado candidate: el harness captura antes de ejecutar checks la concordancia exacta entre `HEAD`, índice y bytes reales, y rechaza cualquier archivo no versionado preexistente, incluso ignorado; el builder revalida el esquema, hashes comprometidos, inventarios, evidencias, métricas y comparación del reporte antes de leer los bytes del commit e incluirlo en `SHA256SUMS`.
- Mantiene la release como candidate: los canales sin evidencia continúan `not-run`; el harness aún no importa resultados de `definition-conversation`, por lo que `stable` permanece bloqueado aunque se aporten observaciones de activación y revisión documental.

## 0.6.1 — 2026-08-20 — clasificación para desarrollo

- Reclasifica el plugin y su entrada de marketplace de `Productivity` a `Developer Tools`, de acuerdo con su finalidad de definición, implementación y verificación de software.
- Mantiene sin cambios el método, el esquema, las seis skills, los gates, los perfiles bloqueados y los contratos de proyectos consumidores.
- Conserva el estado de release candidate y no presenta como ejecutados los canales semánticos, humanos o de piloto pendientes.

## 0.6.0 — 2026-08-20 — definición guiada y diseño visual

- Refuerza el encuadre inicial para que una idea breve no se convierta silenciosamente en un producto genérico: mantiene tandas pequeñas de preguntas de alto impacto, opciones neutrales y supuestos explícitos.
- Añade snapshots compactos de cobertura al cerrar bloques relevantes, diferenciando información suficiente, parcial, desconocida, no aplicable y bloqueada sin porcentajes de madurez.
- Amplía el anexo condicional de UX con inventario, detalle y estados por pantalla, flujos enlazados, interacción, dirección visual y trazabilidad hacia requisitos y criterios.
- Define un ciclo de prototipado condicional con ImageGen: `Visual mode` explícito, brief suficiente, de una a tres propuestas PNG/JPG, validación humana estructurada, reutilización trazable, activos versionados, hashes y fallback explícito.
- Endurece gates contra rebajas de versión aisladas, PNG/JPEG ficticios, contratos de pantalla incompletos y evidencia visual no ligada a la implementación, UX, baseline, viewport y capturas exactos.
- Corrige FX-01 para que la entrevista adaptativa no se presente como evidencia automatizada y añade los escenarios FX-20 y FX-21 como evaluación semántica/humana todavía `not-run`.
- Mantiene Codex como único runtime soportado, ChatGPT Work como apoyo auxiliar y las seis skills existentes sin MCP, conectores, hooks, apps ni agentes añadidos.
- Actualiza el contrato, la documentación, el empaquetado y la infraestructura de piloto a la candidate 0.6.0 sin ejecutar M6, el piloto real ni la promoción a `stable`.

## 0.5.0 — 2026-08-20 — infraestructura de piloto M5

- Añade un marketplace de desarrollo empaquetado con la estructura local estándar de Codex.
- Genera bundles reproducibles del plugin y marketplace, manifiesto por archivo y `SHA256SUMS`, bloqueando enlaces y patrones de secretos.
- Añade configuración, observaciones cerradas, almacenamiento externo, agregación anónima y decisión go/no-go para un piloto de 3–5 proyectos y 5–8 participantes.
- Establece GitHub Issues como soporte no sensible y separa el canal confidencial de seguridad.
- Documenta onboarding, privacidad, retención, distribución y rollback sin modificar automáticamente proyectos consumidores.
- Mantiene el piloto real como pendiente: la plantilla preparada no permite arrancar hasta asignar muestra, aliases, responsables, seguridad y checksum.

## 0.4.0 — 2026-08-19 — calidad de producto M4

- Integra el catálogo completo FX-01–FX-19 y un corpus etiquetado de activación específico para Codex.
- Añade inventario cerrado y hashes SHA-256 para fixtures exclusivamente sintéticos.
- Añade un runner reproducible con canales `candidate` y `stable`, umbrales calculables y fallos críticos destacados.
- Compara métricas comunes con la baseline versionada `v0.3.0` sin ocultar datos no comparables.
- Incorpora contratos para observaciones saneadas y revisiones documentales humanas, manteniendo `not-run` cuando no existe evidencia.

## 0.3.0 — 2026-08-19 — release M0–M3

- Implementa la sexta skill, `lks-sdd-adopt-existing`, con inspección estática, informe externo, reconciliación, detección de deriva y materialización aditiva autorizada.
- Añade ocho artefactos canónicos `as-is` y conserva separados hechos, observaciones, inferencias, intención, contradicciones y desconocidos.
- Añade validación integral, comprobación de trazabilidad y migración `0.9` → `1.0` con preview, backup externo y rollback protegido.
- Añade borradores derivados para cliente con selección por estado/clasificación, procedencia, bloqueo sensible, colisiones y aprobación pendiente.
- Completa la integración opcional de PostgreSQL y Keycloak desde la skill de verificación.
- Endurece previews y escrituras transaccionales frente a deriva, colisiones, symlinks, junctions, backups corruptos y evidencias inconsistentes.
- Publica el primer hito versionado del repositorio como `v0.3.0`, candidato para revisión y piloto con Codex, sin convertirlo en política corporativa aprobada.

## 0.2.0 — 2026-08-19 — desarrollo local, no publicado

- Añade el perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, locks exactos y scaffold reproducible.
- Valida backend, frontend, PostgreSQL y Keycloak dentro de sus runtimes bloqueados y mediante comprobaciones HTTP integradas.
- Implementa preparación segura, dry-run, hash de autorización, protección de colisiones y rollback para incrementos listos.
- Implementa planificación y ejecución de verificaciones sin confundir resultados no ejecutados con éxitos.
- Integra la aptitud del perfil H0 en la puerta de readiness y mantiene la selección tecnológica como decisión humana confirmada.

## 0.1.0 — 2026-08-19 — desarrollo local, no publicado

- Crea el manifiesto skills-only y el gobierno inicial.
- Incorpora las tres especificaciones canónicas sin alterar los originales.
- Implementa ayuda, definición y evaluación de readiness.
- Añade esquemas, validadores, inicialización segura de proyectos nuevos y evals reproducibles.
- Mantiene propuestas, decisiones y texto de bloqueos en Markdown; el índice conserva solo referencias operativas.
- Completa anexos condicionales, onboarding, comparación Work–Codex, FAQ, troubleshooting y ayuda contextual en siete partes.
- Endurece la validación del núcleo exacto, tablas, perfil seleccionado y bloqueos por alcance.
- Registra adopción de existentes, implementación y verificación como backlog no disponible.
- Define Codex como entorno objetivo soportado y documenta que Copilot, Claude y otros asistentes no tienen compatibilidad verificada.
