# Arquitectura y alcance de la versión 0.8.0

## Decisión de producto

LKS-SDD es un plugin skills-only para desarrollar con Codex mediante Specification-Driven Development. Los Markdown versionados del proyecto consumidor son la fuente canónica; `.lks-sdd/project.json` indexa el contrato operativo, pero no sustituye decisiones, tareas ni evidencias.

La versión 0.8.0 conserva las seis skills y añade una capa transversal de gobierno de entrega, planificación profesional y arquitectura multiperfil. El contrato activo para proyectos nuevos es `method_version: 1.2.0` y `schema_version: 1.2`. Los contratos 1.0 y 1.1 continúan validándose en compatibilidad y solo evolucionan mediante migraciones explícitas de un salto.

## Capas del producto

| Capa | Responsabilidad | Fuente principal |
|---|---|---|
| Método y contrato | Estados, identificadores, tablas, trazabilidad, gates y reglas de cambio | `specs/canonical/`, `schemas/`, `scripts/contract_engine.py` |
| Definición y adopción | Descubrir intención o reconciliar una implementación existente sin inventar decisiones | `skills/lks-sdd-define/`, `skills/lks-sdd-adopt-existing/` |
| Gobierno de entrega | Modelo de evolución, versionado, Git, CI/CD, entornos, promoción, despliegue y recuperación | `delivery-governance.md`, `deployment.md`, `scripts/delivery_engine.py` |
| Planificación | Horizontes `PLAN-###`, entregas `REL-###`, unidades `UNIT-###` y tareas `TASK-###` | `plans.md`, `tasks.md`, `task-detail.md`, `scripts/manage_tasks.py` |
| Arquitectura multiperfil | Familias, capabilities internas, perfiles cerrados, bindings, locks y certificaciones | `profiles/catalog.json`, `profiles/*`, `scripts/profile_registry.py` |
| Ejecución | Readiness, preparación aditiva, implementación acotada y rollback | `lks-sdd-assess-readiness`, `lks-sdd-implement` |
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

## Planificación y seguimiento

La estructura `PLAN-### → REL-### → TASK-###` evita tanto un backlog plano como tablas interminables. Cada `PLAN` representa un horizonte —normalmente una versión mayor, etapa o ventana de mantenimiento— y contiene releases manejables. El tablero de tareas ofrece lectura visual mediante símbolos y estados, mientras cada tarea mantiene su definición independiente con:

- objetivo, alcance incluido y excluido;
- trazabilidad a requisitos, aceptación, decisiones, riesgos e incremento;
- unidad desplegable, binding de perfil y release destino;
- dependencias, estimación, responsable lógico y criterios de entrada/salida;
- plan de implementación, pruebas y gates aplicables;
- problemas `PROB-###`, bloqueos, evidencias, revisión Git, build, artefacto y entorno.

Las transiciones se validan mediante una máquina de estados y se aplican con preview, hash de autorización y escritura atómica. `done` no se infiere de una casilla: exige criterios, gates y evidencias verificables. El tablero es una vista canónica de seguimiento; el detalle de tarea conserva la información necesaria para ejecutar y auditar el trabajo.

## Arquitectura multiperfil

El catálogo usa cuatro niveles deliberadamente distintos:

1. Una **familia** clasifica una arquitectura; no es seleccionable.
2. Una **capability** reutiliza restricciones, scaffold y gates; no acredita compatibilidad por sí sola.
3. Un **perfil de referencia** define una composición exacta y cerrada; es la única unidad certificable y seleccionable.
4. Un **binding** liga ese perfil y su lock a una unidad desplegable concreta del proyecto.

Un perfil solo se presenta como `supported` cuando su lifecycle es `active` y existe una certificación completa que coincide exactamente con los hashes actuales de descriptor, capabilities, scaffold, driver, composición, gates y motor de certificación. Un lock aporta identidad y reproducibilidad; la evidencia del gate de composición demuestra que esa mezcla concreta fue probada. Si cualquiera de esos bytes cambia, el soporte deja de ser válido hasta volver a certificar.

El catálogo 0.8.0 incluye diez perfiles en seis familias:

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

Codex es el único runtime soportado contractualmente. ImageGen es condicional y una propuesta visual no equivale a aprobación. La adopción estática no demuestra comportamiento productivo. Los perfiles candidate no son automatización soportada. Los canales semánticos, humanos, de activación, revisión documental y piloto sin observaciones reales permanecen `not-run`; candidate puede mantenerlos opcionales, pero `stable` no.

La implementación no añade MCP, conectores, hooks, apps ni agentes ejecutables. Tampoco inventa dominio, selecciona tecnología, decide ramas, aprueba merges, publica, instala o despliega por cuenta de una persona autorizada.

## Evolución posterior

La versión SemVer `0.8.0` no equivale a M6 ni a una política corporativa aprobada. La siguiente evolución de perfiles debe partir de demanda real y cerrar descriptor, lock, scaffold, gates por capability, gate de composición, evals y certificación exacta antes de modificar su estado. Los cambios del propio método seguirán siendo aditivos y migrables, con trazabilidad de transición.
