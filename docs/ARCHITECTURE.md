# Arquitectura y alcance de la versión 0.10.0

## Decisión de producto

LKS-SDD es un plugin skills-only y Spec-anchored para desarrollar con Codex mediante Specification-Driven Development. Los Markdown versionados del proyecto consumidor son la fuente canónica y duradera; `.lks-sdd/project.json` indexa el contrato operativo, pero no sustituye decisiones, tareas ni evidencias.

La versión 0.10.0 conserva las seis skills, la arquitectura multiperfil y la cobertura, autorización y continuidad del método 1.3. Añade la implementación candidate de la propuesta 1.4 para elegir el backend de seguimiento y proyectar opcionalmente tareas en Jira. El contrato activo para proyectos nuevos es `method_version: 1.4.0` y `schema_version: 1.4`; 1.0–1.3 continúan validándose y solo evolucionan mediante migraciones explícitas de un salto. La propuesta metodológica permanece en `specs/proposed/`: no altera los hashes ni el estado de las siete fuentes canónicas.

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
| Arquitectura multiperfil | Familias, capabilities internas, perfiles cerrados, bindings, locks y certificaciones | `profiles/catalog.json`, `profiles/*`, `scripts/profile_registry.py` |
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

El motor heredado de 1.3 evalúa dos ejes simultáneos: una selección puede tener `TASK-###: ready` mientras la planificación de su incremento o release sigue `partial`. `ART-PLANNING` asigna cada elemento activo a una tarea primaria, permite contribuyentes sin duplicar responsabilidad y detecta requisitos, criterios y pruebas sin propietario, definiciones incompletas, cobertura incoherente, ciclos y dependencias canceladas. El contrato 1.4 conserva estas reglas y añade un eje independiente de tracking; nunca deriva completitud de Jira.

La implementación requiere además un `AUTH-###` vigente, ligado a incremento, release, selección TASK, política y huellas. La política recomendada es `complete-before-implementation`; `incremental-authorized` necesita una decisión humana expresa y conserva `partial` visible. Ni readiness ni confirmación del plan autorizan por sí solos cambios de código.

Al comenzar se registra un `EXEC-###` y un `CKPT-###` inicial. Los checkpoints posteriores conservan tarea activa, rama y revisión observadas, archivos modificados, entregables terminados y parciales, aceptación, checks, evidencias, problemas, decisiones y siguiente acción segura. Al reanudar se compara repositorio y checkpoint; una divergencia conduce a reconciliar o replanificar y nunca convierte código parcial o pruebas no ejecutadas en trabajo terminado.

## Tracking operativo y frontera Rovo

Antes de materializar tareas 1.4 se registra una decisión `TRK-###`:

| Modo | Autoridad | Dependencia externa | Comportamiento degradado |
|---|---|---|---|
| `repository-only` | Markdown LKS-SDD | Ninguna | Operación completa en local |
| `jira-hybrid` | Markdown LKS-SDD; Jira como proyección operacional | Peer Atlassian Rovo autorizado por separado | Conserva intención y estado local; no simula escritura remota |

`ART-TRACKING` contiene tres tablas cerradas: configuración y políticas del binding, mappings `TASK-### ↔ external_id` y recibos `SYNC-###`. La autoridad por campo está fijada por contrato, no por una matriz editable. `external_id` identifica el remoto; la key y URL Jira son atributos observados que solo pueden actualizarse dentro del proyecto y prefijo confirmados. Una key conservada en el historial no puede reutilizarse después con otra TASK o `external_id`, aunque el mapping vigente ya muestre una key posterior. Un cambio de prefijo por rename o movimiento queda fuera de soporte y falla de forma cerrada. Los campos operativos —assignee, sprint, posición o estado observado— no cambian `planning_fingerprint` ni invalidan AUTH. Un cambio remoto semántico se registra como conflicto o propuesta de cambio, nunca como actualización canónica automática. El mapping de workflows Jira no está automatizado en 0.10.0 y cualquier traducción no exacta falla de forma cerrada.

Las operaciones externas usan `SYNC-###`: intención determinista, preview saneado, autorización del hash exacto, ejecución por el peer y acuse local. `succeeded`, `failed`, `conflict` y `uncertain` son resultados distintos. Un timeout no autoriza repetir una creación hasta consultar y reconciliar el remoto. `Done` en Jira no produce `TASK: done`, `EVID-###`, G3 ni G4.

El manifiesto continúa `skills-only`: no declara dependencias no documentadas, MCP, app, hook ni cliente Jira. Rovo conserva su autenticación y permisos fuera de LKS-SDD; su salida se valida como entrada no confiable y se persiste sólo en la forma saneada necesaria para continuidad.

## Arquitectura multiperfil

El catálogo usa cuatro niveles deliberadamente distintos:

1. Una **familia** clasifica una arquitectura; no es seleccionable.
2. Una **capability** reutiliza restricciones, scaffold y gates; no acredita compatibilidad por sí sola.
3. Un **perfil de referencia** define una composición exacta y cerrada; es la única unidad certificable y seleccionable.
4. Un **binding** liga ese perfil y su lock a una unidad desplegable concreta del proyecto.

Un perfil solo se presenta como `supported` cuando su lifecycle es `active` y existe una certificación completa que coincide exactamente con los hashes actuales de descriptor, capabilities, scaffold, driver, composición, gates y motor de certificación. Un lock aporta identidad y reproducibilidad; la evidencia del gate de composición demuestra que esa mezcla concreta fue probada. Si cualquiera de esos bytes cambia, el soporte deja de ser válido hasta volver a certificar.

El catálogo 0.10.0 conserva diez perfiles en seis familias; esta evolución no modifica sus bytes, locks ni certificaciones:

| Perfil | Arquitectura | Estado de producto |
|---|---|---|
| `WEB-REACT-VITE-STATIC` | SPA React/Vite estática | active; requiere certificación exacta vigente |
| `WEB-ANGULAR-STATIC` | SPA Angular estática | active; requiere certificación exacta vigente |
| `API-FASTAPI-STATELESS-OCI` | API-only sin estado en OCI | active; requiere certificación exacta vigente |
| `API-FASTAPI-KEYCLOAK-PG-OCI` | API-only con OIDC y PostgreSQL | active; requiere certificación exacta vigente |
| `WEB-NEXTJS-SSR-NODE` | SSR/hidratación con Next.js | active; requiere certificación exacta vigente |
| `WEB-FASTAPI-REACT-KEYCLOAK-PG` | Sistema web React, API, OIDC y PostgreSQL | active; requiere certificación exacta vigente |
| `WEB-ANGULAR-SSR-NODE` | SSR/hidratación con Angular | candidate; documentable, no soportado aún |
| `SYS-WEB-ANGULAR-FASTAPI-KEYCLOAK-PG` | Sistema web Angular, API, OIDC y PostgreSQL | candidate; documentable, no soportado aún |
| `MSG-PYTHON-RABBITMQ-WORKER-OCI` | Worker event-driven RabbitMQ | candidate; documentable, no soportado aún |
| `STR-PYTHON-KAFKA-PROCESSOR-OCI` | Procesador event-driven Kafka | candidate; documentable, no soportado aún |

Los perfiles candidate contienen contrato, scaffold, locks y gates diseñados, pero no se promocionan a active ni a `supported` sin ejecutar y registrar su gate completo. Esta distinción evita prometer soporte por el mero hecho de que una tecnología figure en el catálogo.

## Gates y evidencia

- **G2** autoriza preparar una tarea lista con gobierno, arquitectura, binding y lock coherentes.
- **G3** ejecuta los gates obligatorios de cada perfil y el gate de composición exacta.
- **G4** acredita promoción o entrega con revisión/árbol Git, build, digest de artefacto inmutable, entorno, smoke/observabilidad, autorización y recuperación.

La revisión verificada no puede quedar en `null`: la evidencia 1.2 distingue commit o revisión de workspace, `tree_id`, hash del listado del árbol, build y digests. La promoción humana, merge o despliegue siguen requiriendo la autoridad definida por el proyecto; una ejecución técnica no los autoriza implícitamente.

## Límites vigentes

Codex es el único runtime soportado contractualmente. ImageGen y el peer Atlassian Rovo son capacidades condicionales: su disponibilidad no equivale a aprobación ni demuestra el workflow completo. La adopción estática no demuestra comportamiento productivo. Los perfiles candidate no son automatización soportada. Los canales semánticos, humanos, de activación, revisión documental, interoperabilidad real Rovo/Jira y piloto sin observaciones reales permanecen `not-run`; candidate puede mantenerlos opcionales, pero `stable` no.

La implementación no añade MCP, cliente Jira, conectores propios, hooks, apps ni agentes ejecutables. Tampoco inventa dominio, selecciona tecnología o tracker, decide ramas, aprueba merges, publica, instala o despliega por cuenta de una persona autorizada.

## Evolución posterior

La versión SemVer `0.10.0` y el schema candidate 1.4 no equivalen a M6, a interoperabilidad Rovo/Jira verificada ni a política corporativa aprobada. La eventual incorporación canónica de la propuesta 1.4 requiere una decisión metodológica separada. La siguiente evolución de perfiles debe partir de demanda real y cerrar descriptor, lock, scaffold, gates por capability, gate de composición, evals y certificación exacta antes de modificar su estado.
