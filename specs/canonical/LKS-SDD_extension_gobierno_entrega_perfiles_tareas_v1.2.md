# LKS-SDD — Extensión canónica 1.2: gobierno de entrega, perfiles y tareas

## 1. Estado y propósito

- **Estado:** contrato canónico aditivo aprobado para implementación en LKS-SDD 0.8.0.
- **Ámbito:** proyectos nuevos, proyectos adoptados y migraciones explícitas a esquema 1.2.
- **No modifica:** las fuentes canónicas históricas ni el significado de sus gates.
- **Objetivo:** hacer operable el paso de especificación a entrega en arquitecturas y tecnologías diferentes, sin prometer soporte para combinaciones no certificadas.

Esta extensión separa hechos observados, decisiones humanas, propuestas del método, estado derivado y evidencia ejecutada. Un dato propuesto o derivado nunca sustituye la autoridad de una ADR ni una comprobación realmente ejecutada.

## 2. Gobierno de entrega antes de G2

Todo proyecto 1.2 debe definir antes de G2 un gobierno de entrega confirmado y trazable mediante `CHG-###` y una `ADR-###`. La decisión debe cerrar, para el alcance aplicable:

1. modelo de evolución del producto;
2. versionado de producto, API, datos y artefactos;
3. estrategia de ramas, merge, revisiones y protección;
4. integración continua y gates obligatorios;
5. roles de entorno y orden de promoción;
6. construcción y promoción de artefactos inmutables;
7. autorización, despliegue, verificación posterior y recuperación;
8. disparadores y fecha de revisión del propio gobierno.

El método no impone una estrategia Git universal. La decisión debe seleccionar y justificar la variante adecuada al proyecto. El índice operativo conserva solo la selección necesaria para automatizar; el Markdown conserva la decisión y su contexto.

### 2.1 Modelos admitidos

| Modelo | Uso característico | Horizonte | Tratamiento de versión y flujo |
|---|---|---|---|
| `bounded-release` | Producto con alcance de entrega y publicación acotados | Una o varias releases planificadas | Baseline y cierre de release explícitos; pueden existir ramas de release si se justifican |
| `continuous-evolution` | Producto ágil con evolutivos continuos | Roadmap o release train revisable | Integración frecuente, incrementos pequeños y promoción continua bajo gates |
| `maintenance-stream` | Correctivos y mejoras evolutivas de un producto existente | Streams soportados por versión | Compatibilidad, backports, severidad, ventanas y versiones mantenidas explícitas |

Una transición de modelo es una operación normal de gobierno: añade un nuevo `CHG-###`, indica vigencia, ADR, impacto, plan de transición y condiciones de rollback. No reescribe decisiones, tareas, releases ni evidencias históricas.

## 3. Entornos, artefactos y evidencia de entrega

Los entornos se identifican como `ENV-###` y se definen por rol, no mediante una lista fija. Desarrollo, CI, preview, integración, aceptación, preproducción y producción solo se materializan cuando son aplicables.

G3 debe ligar la verificación a:

- revisión Git exacta o huella determinista del workspace cuando Git no aplique;
- tree hash;
- identificador de build;
- digest `sha256` de cada artefacto relevante;
- perfil y lock exactos por unidad;
- gates ejecutados y evidencia `EVID-###`.

G4 requiere evidencia externa estructurada de promoción, autorización, smoke, observabilidad y recuperación para una `REL-###` y un `ENV-###`. Un despliegue no ejecutado permanece `not-run`; el plugin no autoriza merge, promoción ni despliegue por sí mismo.

## 4. Planificación y seguimiento profesional

### 4.1 Horizontes

`PLAN-###` delimita un horizonte mayor, release train o stream de mantenimiento. Cada tablero corresponde a un plan o versión mayor para evitar saturación visual. `REL-###` representa una unidad de entrega dentro del plan y contiene versión, stream o rama, entornos, tareas, revisión, artefactos y evidencia.

### 4.2 Tablero y definición independiente

Toda tarea de desarrollo usa `TASK-###` y tiene:

- una fila compacta en `ART-TASKS` para lectura y seguimiento rápido;
- una definición independiente en `04-delivery/tasks/TASK-###.md`;
- vínculos a plan, release, incremento, unidad desplegable y binding de perfil;
- objetivo, alcance incluido y excluido, requisitos, aceptación, capacidades y gates;
- dependencias, responsable, estado, salud, progreso, bloqueos y problemas;
- rama, revisiones, build, entorno, resultados y evidencia cuando existan;
- historial de transiciones con motivo y autoridad.

Estados de workflow: `backlog`, `ready`, `in-progress`, `in-review`, `done`, `blocked`, `cancelled`.

Estados de salud: `on-track`, `at-risk`, `blocked`, `unknown`.

Reglas mínimas:

- `ready` exige definición ejecutable completa, dependencias resueltas, gobierno confirmado, binding confirmado y perfil soportado;
- `blocked` exige un bloqueo visible y condición de resolución;
- `in-progress` e `in-review` usan progreso entre 1 y 99;
- `done` exige progreso 100 y evidencia ligada a revisión, artefacto, entorno y gate;
- no se admiten ciclos ni dependencias inexistentes;
- tablero, detalle e índice deben permanecer coherentes y sus cambios autorizados usan preview hash.

## 5. Arquitectura tecnológica multiperfil

### 5.1 Jerarquía

El catálogo distingue tres conceptos:

1. **Familia:** clasificación no seleccionable de una forma arquitectónica.
2. **Capacidad:** unidad interna reutilizable de scaffold, restricciones y checks. No es unidad de homologación.
3. **Perfil de referencia:** composición cerrada, versionada y acotada. Es la única unidad seleccionable y la única que puede declararse `supported`.

Una aplicación puede tener varias `UNIT-###`. Cada unidad se liga mediante un `BIND-###` a un perfil cerrado y un lock independiente. El perfil de sistema se usa solo cuando la composición representa realmente un único sistema de referencia; no sustituye bindings por desplegable cuando estos tienen ciclos de vida separados.

### 5.2 Condición estricta de soporte

Un perfil es `supported` únicamente si se cumplen simultáneamente:

- descriptor válido y lifecycle `active`;
- driver de preparación y verificación resoluble;
- scaffold reproducible y dependencias bloqueadas;
- capacidades y gates obligatorios completos;
- lock cuyos hashes coinciden con descriptor, capacidades, configuración, fuentes y driver;
- gate de composición end-to-end superado para el hash exacto de esa composición;
- certificación vigente del perfil.

Un lock aporta identidad y reproducibilidad, pero no demuestra compatibilidad. Los gates de capacidades son necesarios, pero no sustituyen el gate de composición. Un perfil `candidate` puede documentarse y evaluarse estructuralmente, pero nunca debe producir `automation_support=supported`.

La composición dinámica arbitraria en el proyecto consumidor queda fuera del contrato 1.2. Las nuevas combinaciones se preparan y certifican en una release del plugin antes de promoverse a `active`.

### 5.3 Perfiles de referencia iniciales

El catálogo 1.2 debe incluir perfiles cerrados equivalentes para:

- React + Vite estático;
- Angular estático;
- API-only stateless con artefacto OCI;
- API-only con OIDC y PostgreSQL;
- Next.js SSR;
- Angular SSR;
- sistema web Angular + API + OIDC + PostgreSQL;
- sistema web completo React + FastAPI + Keycloak + PostgreSQL;
- worker event-driven con RabbitMQ;
- procesador de streaming con Kafka.

RabbitMQ y Kafka no son alias de una única arquitectura event-driven: sus contratos operativos, semántica, topología y gates se mantienen en perfiles diferentes.

## 6. Gates composables

- **G2 — preparación:** contrato documental, gobierno, plan/tarea, binding, soporte estricto, lock y scaffold sin colisiones.
- **G3 — verificación:** gates requeridos por capacidad y composición exacta, aceptación, revisión/tree, build y digests.
- **G4 — entrega:** promoción del mismo artefacto, autorización, entorno, smoke, observabilidad y recuperación con evidencia.

El driver declara cada check con ID estable, fase, comando, directorio, timeout, obligatoriedad y necesidad de contenedores. Un check omitido, bloqueado o no ejecutado nunca cuenta como superado.

## 7. Evolución de contrato

- Proyectos nuevos y adopciones materializadas usan método 1.2.0 y esquema 1.2.
- Los esquemas 1.0 y 1.1 siguen validándose en compatibilidad.
- La migración 1.1 → 1.2 es explícita, de un salto, con dry-run, hash, backup externo, autorización, validación y rollback.
- La migración crea gobierno, planes, tablero y fronteras de unidad en estado propuesto; no confirma modelos, ramas, entornos, perfiles ni tareas por inferencia.
- Los registros derivados de implementación o verificación 1.1 que no puedan vincularse a tarea, revisión, build y artefacto no se elevan artificialmente a evidencia 1.2.

## 8. Límites

Esta extensión no selecciona una tecnología preferente, no homologa una tecnología por nombre, no aprueba una ADR, no crea ramas, no hace merge, no despliega y no convierte una ejecución local en aprobación de entrega. Tampoco añade una séptima skill, MCP, conector, hook, app o agente ejecutable.
