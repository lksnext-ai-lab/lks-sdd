# Arquitectura y alcance de la versión 0.15.0

## Decisión de producto

LKS-SDD es un plugin skills-only y Spec-anchored para desarrollar con Codex mediante Specification-Driven Development. Los Markdown versionados del proyecto consumidor son la fuente canónica y duradera; `.lks-sdd/project.json` indexa el contrato operativo, pero no sustituye decisiones, tareas ni evidencias.

La versión 0.15.0 conserva las seis skills, la arquitectura multiperfil y el contrato 1.5 de tracking y reporting. La orquestación de verificación es estrictamente task-aware: solo selecciona bindings y gates de las TASK solicitadas, calcula la aplicabilidad visual sobre esa selección y mantiene la revisión visual completa para una release que entregue interfaz. Separa también la identidad estable del build, la identidad de la ejecución diagnóstica y la evidencia de entrega G4; esta última se materializa y completa después de conocer revisión, árbol, build y digests. CKPT y PROB se interpretan por su estructura canónica, no por coincidencias textuales. El único contrato de proyecto soportado es `method_version: 1.5.0` y `schema_version: 1.5`; `plugin_version` conserva la procedencia de materialización. Los perfiles OIDC simulados siguen siendo exclusivamente no productivos, los perfiles Microsoft Entra siguen candidate y no existe composición dinámica. Las propuestas permanecen en `specs/proposed/`: no alteran los hashes ni el estado de las siete fuentes canónicas.

La ejecución de calidad se organiza en cuatro tiers mutuamente excluyentes (`fast`, `integration`, `package` y `profile`), con selección conservadora por impacto, procesos aislados, progreso visible y presupuestos bloqueantes. Docker `execute` es una fase separada; `all` compone los cuatro tiers sin duplicar tests.

## Ancla documental y flujos de entrada

La especificación no es un documento de arranque ni una transcripción exhaustiva del código. Es el contrato comprensible contra el que se comparan intención, implementación y evidencia mientras el producto evoluciona. LKS-SDD permite editar código directamente, pero una modificación funcional que afecte al contrato obliga a actualizar o reconciliar los artefactos afectados y a renovar las huellas y autorizaciones que hayan quedado obsoletas.

| Ruta | Evidencia inicial | Construcción del ancla | Límite de autoridad |
|---|---|---|---|
| Aplicación nueva | Necesidad, restricciones y decisiones confirmadas | Definición versionada antes de planificar e implementar | Una propuesta no se convierte en decisión sin confirmación |
| Repositorio existente | Código, configuración y estructura observables mediante inspección estática | Baseline `as-is`, reconciliación con intención confirmada y contrato evolutivo | El código demuestra lo que existe, no lo que el cliente desea o aprueba |

Las vistas para cliente son artefactos derivados del contrato confirmado, con procedencia, clasificación y revisión humana. Facilitan contrastar alcance, reglas y aceptación sin crear otra fuente de verdad. La implementación puede generarse o modificarse con ayuda de Codex a partir del contrato, pero LKS-SDD no es Spec-as-source: el código no se considera correcto por haber sido generado y la especificación no sustituye la verificación.

## Capas del producto

| Capa | Responsabilidad | Fuente principal |
|---|---|---|
| Método y contrato | Estados, identificadores, tablas, trazabilidad, gates y reglas de cambio | `specs/canonical/`, `schemas/`, `scripts/contract_engine.py` |
| Definición y adopción | Descubrir intención o reconciliar una implementación existente sin inventar decisiones | `skills/lks-sdd-define/`, `skills/lks-sdd-adopt-existing/` |
| Gobierno de entrega | Modelo de evolución, versionado, Git, CI/CD, entornos, promoción, despliegue y recuperación | `delivery-governance.md`, `deployment.md`, `scripts/delivery_engine.py` |
| Planificación | Horizontes, releases, tareas, cobertura primaria/contribuyente, DAG, huecos e integración conjunta | `plans.md`, `planning-coverage.md`, `tasks.md`, `scripts/planning_engine.py` |
| Tracking operativo | Elección de modo, políticas cerradas, bindings, vistas previas, recibos y reconciliación externa | `task-tracking.md`, `scripts/task_tracking_engine.py`, `scripts/manage_task_tracking.py` |
| Arquitectura multiperfil | Familias, capabilities internas, perfiles cerrados, bindings, locks, certificaciones y diagnóstico de cobertura | `profiles/catalog.json`, `profiles/*`, `scripts/profile_registry.py`, `scripts/automation_coverage.py` |
| Ejecución | Readiness por porción, autorización persistida, preparación aditiva, implementación acotada y rollback | `lks-sdd-assess-readiness`, `lks-sdd-implement`, `scripts/manage_planning.py` |
| Continuidad | Ejecución durable, checkpoints observables y reconciliación al reanudar | `EXEC-###`, `CKPT-###`, `scripts/manage_continuity.py` |
| Evidencia | Gates G3/G4, revisión Git, árbol, build, artefactos, entorno y autorización | `lks-sdd-verify`, `scripts/delivery_engine.py` |
| Calidad y distribución | Tests, evals, candidate/stable, piloto y bundle reproducible | `tests/`, `quality/`, `pilot/`, `distribution/` |

## Gobierno adaptable del ciclo de vida

Cada proyecto debe confirmar antes de G2 uno de estos modelos, sin convertirlo en una plantilla rígida:

| Modelo | Uso principal | Unidad de planificación y entrega |
|---|---|---|
| `bounded-release` | Producto con alcance inicial y versión publicable objetivo | Hitos y releases acotadas |
| `continuous-evolution` | Desarrollo agile con incrementos continuos | Horizonte móvil y entregas frecuentes |
| `maintenance-stream` | Correctivos y evolutivos sobre un producto vivo | Flujo de cambios con prioridad, riesgo y urgencia |

El mismo contrato documenta versionado de producto, política de compatibilidad, estrategia Git, protección y revisión de ramas, CI/CD, entornos, promoción, despliegue, migraciones, observabilidad y recuperación. Un cambio de modelo durante la vida del proyecto se registra como `CHG-###` con origen, impacto, transición, fecha efectiva y decisión; no reescribe la historia ni invalida automáticamente evidencias anteriores.

## Planificación, autorización y seguimiento

La estructura `PLAN-### → REL-### → TASK-###` evita tanto un backlog plano como tablas interminables. Cada `PLAN` representa un horizonte —normalmente una versión mayor, etapa o ventana de mantenimiento— y contiene releases manejables. El tablero Markdown de tareas ofrece una lectura visual canónica mediante símbolos y estados, mientras cada tarea mantiene su definición independiente con:

- objetivo, alcance incluido y excluido;
- trazabilidad a requisitos, aceptación, decisiones, riesgos e incremento;
- unidad desplegable, binding de perfil y release destino;
- dependencias, estimación, responsable lógico y criterios de entrada/salida;
- plan de implementación, pruebas y gates aplicables;
- problemas `PROB-###`, bloqueos, evidencias, revisión Git, build, artefacto y entorno.

Las transiciones se validan mediante una máquina de estados y se aplican con preview, hash de autorización y escritura atómica. `done` no se infiere de una casilla: exige criterios, gates y evidencias verificables. El tablero es una vista canónica de seguimiento; el detalle de tarea conserva la información necesaria para ejecutar y auditar el trabajo.

El motor de planificación evalúa dos ejes simultáneos: una selección puede tener `TASK-###: ready` mientras la planificación de su incremento o release sigue `partial`. `ART-PLANNING` asigna cada elemento activo a una tarea primaria, permite contribuyentes sin duplicar responsabilidad y detecta requisitos, criterios y pruebas sin propietario, definiciones incompletas, cobertura incoherente, ciclos y dependencias canceladas. El contrato 1.5 añade ejes independientes de tracking y reporting y nunca deriva completitud de Jira.

La implementación requiere además un `AUTH-###` vigente, ligado a incremento, release, selección TASK, política y huellas. La política recomendada es `complete-before-implementation`; `incremental-authorized` necesita una decisión humana expresa y conserva `partial` visible. Ni readiness ni confirmación del plan autorizan por sí solos cambios de código.

Al comenzar se registra un `EXEC-###` y un `CKPT-###` inicial. Los checkpoints posteriores conservan tarea activa, rama y revisión observadas, archivos modificados, entregables terminados y parciales, aceptación, checks, evidencias, problemas, decisiones y siguiente acción segura. Al reanudar se compara repositorio y checkpoint; una divergencia conduce a reconciliar o replanificar y nunca convierte código parcial o pruebas no ejecutadas en trabajo terminado.

## Tracking operativo y frontera Rovo

Antes de materializar tareas 1.4 se registra una decisión `TRK-###`:

| Modo | Autoridad | Dependencia externa | Comportamiento degradado |
|---|---|---|---|
| `repository-only` | Markdown LKS-SDD | Ninguna | Operación completa en local |
| `jira-hybrid` | Markdown LKS-SDD; Jira como proyección operacional | Peer Atlassian Rovo autorizado por separado | Conserva intención y estado local; no simula escritura remota |

`ART-TRACKING` contiene el binding y sus mappings/recibos de proyección. En 1.5 añade `RPT-###`, mappings explícitos de estados locales a Jira status IDs y recibos de hitos. La autoridad por campo está fijada por contrato, no por una matriz editable. `external_id` identifica el remoto; key y URL son atributos observados dentro del proyecto confirmado. Los campos operativos no cambian `planning_fingerprint` ni invalidan AUTH. Un cambio remoto semántico se registra como conflicto, nunca como actualización canónica. El workflow solo se traduce mediante IDs confirmados y transiciones observadas; cualquier mapping ambiguo falla cerrado.

Las operaciones externas usan `SYNC-###`: intención determinista, preview saneado, autorización del hash exacto, ejecución por el peer y acuse local. `succeeded`, `failed`, `conflict` y `uncertain` son resultados distintos. Un timeout no autoriza repetir una creación hasta consultar y reconciliar el remoto. `Done` en Jira no produce `TASK: done`, `EVID-###`, G3 ni G4.

El manifiesto continúa `skills-only`: no declara dependencias no documentadas, MCP, app, hook ni cliente Jira. Rovo conserva su autenticación y permisos fuera de LKS-SDD; su salida se valida como entrada no confiable y se persiste sólo en la forma saneada necesaria para continuidad.

## Arquitectura multiperfil

El catálogo usa cuatro niveles deliberadamente distintos:

1. Una **familia** clasifica una arquitectura; no es seleccionable.
2. Una **capability** reutiliza restricciones, scaffold y gates; no acredita compatibilidad por sí sola.
3. Un **perfil de referencia** define una composición exacta y cerrada; es la única unidad certificable y seleccionable.
4. Un **binding** liga ese perfil y su lock a una unidad desplegable concreta del proyecto.

Un perfil solo se presenta como `supported` cuando su lifecycle es `active` y existe una certificación completa que coincide exactamente con los hashes actuales de descriptor, capabilities, scaffold, driver, composición, gates y motor de certificación. Un lock aporta identidad y reproducibilidad; la evidencia del gate de composición demuestra que esa mezcla concreta fue probada. Si cualquiera de esos bytes cambia, el soporte deja de ser válido hasta volver a certificar. `automation_coverage` explica dimensiones disponibles o pendientes, pero no introduce soporte parcial ni cambia esta puerta.

La versión 0.15.0 contiene catorce perfiles en seis familias: conserva los perfiles existentes, añade dos perfiles OIDC simulados `active` para uso no productivo y mantiene los dos perfiles Entra como `candidate` junto a los cuatro candidates anteriores:

| Perfil | Arquitectura | Estado de producto |
|---|---|---|
| `WEB-REACT-VITE-STATIC` | SPA React/Vite estática | active; requiere certificación exacta vigente |
| `WEB-ANGULAR-STATIC` | SPA Angular estática | active; requiere certificación exacta vigente |
| `API-FASTAPI-STATELESS-OCI` | API-only sin estado en OCI | active; requiere certificación exacta vigente |
| `API-FASTAPI-KEYCLOAK-PG-OCI` | API-only con OIDC y PostgreSQL | active; requiere certificación exacta vigente |
| `API-FASTAPI-SIMULATED-OIDC-PG-OCI` | API-only FastAPI con OIDC simulado, PostgreSQL y OCI | active; solo no productivo, certificación exacta vigente |
| `API-FASTAPI-ENTRA-PG-OCI` | API-only FastAPI con Microsoft Entra, PostgreSQL y OCI | candidate; cobertura local definida, no soportado aún |
| `WEB-REACT-VITE-SIMULATED-OIDC-STATIC` | SPA React/Vite estática con OIDC simulado y PKCE | active; solo no productivo, certificación exacta vigente |
| `WEB-REACT-VITE-ENTRA-STATIC` | SPA React/Vite estática con Microsoft Entra y PKCE | candidate; cobertura local definida, no soportado aún |
| `WEB-NEXTJS-SSR-NODE` | SSR/hidratación con Next.js | active; requiere certificación exacta vigente |
| `WEB-FASTAPI-REACT-KEYCLOAK-PG` | Sistema web React, API, OIDC y PostgreSQL | active; requiere certificación exacta vigente |
| `WEB-ANGULAR-SSR-NODE` | SSR/hidratación con Angular | candidate; documentable, no soportado aún |
| `SYS-WEB-ANGULAR-FASTAPI-KEYCLOAK-PG` | Sistema web Angular, API, OIDC y PostgreSQL | candidate; documentable, no soportado aún |
| `MSG-PYTHON-RABBITMQ-WORKER-OCI` | Worker event-driven RabbitMQ | candidate; documentable, no soportado aún |
| `STR-PYTHON-KAFKA-PROCESSOR-OCI` | Procesador event-driven Kafka | candidate; documentable, no soportado aún |

Los perfiles candidate contienen contrato, scaffold, locks y gates diseñados, pero no se promocionan a active ni a `supported` sin ejecutar y registrar su gate completo. Los candidates Entra mantienen además la interoperabilidad real `not-run`: metadata, claims y PKCE sintéticos no prueban un tenant, registros de aplicación, consent, conditional access o renovación reales. Esta distinción evita prometer soporte por el mero hecho de que una tecnología figure en el catálogo.

Los perfiles OIDC simulados modelan el límite de confianza y el flujo Authorization Code con PKCE S256 mediante un emisor efímero controlado, discovery/JWKS, tokens RS256 y claims sintéticos estables. Solo aceptan una allowlist explícita de entornos no productivos y el issuer dedicado `/__test__/oidc`; HTTP queda en loopback y HTTPS habilita topologías browser-reachable de integración o aceptación-preproducción. Producción, ausencia o etiquetas desconocidas fallan de forma cerrada. Su certificación demuestra el contrato local no productivo y cada binding por separado, no la interoperabilidad de Microsoft Entra, la composición frontend/backend ni la equivalencia operacional con un proveedor externo.

## Gates y evidencia

- **G2** autoriza preparar una tarea lista con gobierno, arquitectura, binding y lock coherentes.
- **G3** ejecuta los gates obligatorios de cada perfil y el gate de composición exacta.
- **G4** acredita promoción o entrega con revisión/árbol Git, build, digest de artefacto inmutable, entorno, smoke/observabilidad, autorización y recuperación.

La revisión verificada no puede quedar en `null`: la evidencia 1.2 distingue commit o revisión de workspace, `tree_id`, hash del listado del árbol, build y digests. La promoción humana, merge o despliegue siguen requiriendo la autoridad definida por el proyecto; una ejecución técnica no los autoriza implícitamente.

## Límites vigentes

Codex es el único runtime soportado contractualmente. ImageGen y el peer Atlassian Rovo son capacidades condicionales: su disponibilidad no equivale a aprobación ni demuestra el workflow completo. La adopción estática no demuestra comportamiento productivo. Los perfiles candidate no son automatización soportada. Los canales semánticos, humanos, de activación, revisión documental, interoperabilidad real Entra y Rovo/Jira y piloto sin observaciones reales permanecen `not-run`; candidate puede mantenerlos opcionales, pero `stable` no.

La implementación no añade MCP, cliente Jira, conectores propios, hooks, apps ni agentes ejecutables. Tampoco inventa dominio, selecciona tecnología o tracker, decide ramas, aprueba merges, publica, instala o despliega por cuenta de una persona autorizada.

## Evolución posterior

La versión SemVer `0.15.0` y el schema candidate 1.5 no equivalen a M6, a interoperabilidad Entra o Rovo/Jira verificada ni a política corporativa aprobada. La eventual incorporación canónica de las propuestas 1.4/1.5 requiere una decisión metodológica separada. La promoción de los candidates Entra o un futuro perfil de sistema debe partir de evidencia real y cerrar descriptor, lock, scaffold, gates por capability, gate de composición, evals y certificación exacta antes de modificar su estado.

## Capa de experiencia 0.15

`experience_engine.py` deriva una proyección humana sin modificar Markdown: management es compacta, developer añade diagnóstico e instrumentación y audit conserva el modelo completo. `work_task.py` orquesta las transacciones existentes como hitos compuestos; no es una vía alternativa a autorización, validación o rollback. `doctor_project.py` es un preflight mínimo y nunca ejecuta la suite interna. `verification_subject` separa entradas técnicas/contractuales de outputs administrativos derivados y falla cerrado ante rutas ambiguas.
