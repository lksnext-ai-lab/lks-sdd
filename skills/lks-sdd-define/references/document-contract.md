# Contrato documental mínimo

Cada Markdown canónico empieza con front matter validable: `artifact_id`, `artifact_type`, `schema_version`, `method_version`, `created_with_plugin_version`, `project_id`, `baseline_id`, `status`, `classification`, `audience`, `owners`, `source_of_truth` y `last_updated`.

Las inicializaciones nuevas de LKS-SDD 0.9.1 usan `method_version: 1.3.0` y `schema_version: 1.3`. Los documentos 1.0, 1.1 y 1.2 siguen siendo validables en compatibilidad; no se actualizan al instalar el plugin. Las migraciones son explícitas, reversibles y de un solo salto (`1.0 → 1.1 → 1.2 → 1.3`). El salto 1.2 → 1.3 conserva el cuerpo humano, añade cobertura y definición ejecutable como pendientes, e inicializa autorizaciones y ejecuciones vacías: nunca infiere tareas, confirmación, avance, checkpoints o evidencia.

El núcleo se materializa bajo `docs/lks-sdd/`:

- `00-control/project-status.md`, `scope-register.md`, `open-points.md`;
- `01-context/product-brief.md`, `constraints.md`;
- `02-requirements/functional-requirements.md`, `non-functional-requirements.md`, `technical-requirements.md`, `acceptance-criteria.md`;
- `03-solution/solution-overview.md`, `architecture.md`;
- `04-delivery/increments.md`, `delivery-governance.md`, `plans.md`, `planning-coverage.md`, `tasks.md`, `risks-dependencies.md`;
- `05-quality/quality-strategy.md`, `test-strategy.md`, `traceability.md`;
- `06-operation/deployment.md`.

Este núcleo contiene 21 Markdown. Cada `TASK-###` añade dinámicamente `04-delivery/tasks/TASK-###.md`, que debe concordar con su fila del tablero. Cada `CKPT-###` añade dinámicamente un documento bajo `04-delivery/checkpoints/`. `ART-GOVERNANCE` registra el modelo vigente, historial `CHG-###` y entornos `ENV-###`; `ART-PLANS` registra `PLAN-###` y `REL-###`; `ART-PLANNING` registra cobertura, confirmaciones, autorizaciones y cambios; `ART-ARCH` registra unidades desplegables; el índice enlaza perfiles mediante `BIND-###` y conserva `AUTH-###`/`EXEC-###` como índices de registros canónicos.

Las tablas estructurales usan encabezados estables definidos por el catálogo declarativo. Cada tabla declara el propietario de sus IDs, relaciones, cardinalidad, aplicabilidad y política de estados; las celdas de texto pueden redactarse libremente. La naturaleza de un elemento deriva de su artefacto o prefijo (`FR`, `ADR`, `RISK`, etc.) y su columna `State` expresa ciclo de vida. No use estados legacy como `fact`, `requirement` o `assumption` para duplicar esa naturaleza en 1.1; durante el preview de migración aparecen como casos de revisión humana que deben resolverse en el origen 1.0, no como confirmaciones automáticas aplicables.

Cada incremento declara alcance incluido y excluido, requisitos, criterios, decisiones y pruebas. Una matriz separada declara por incremento la aplicabilidad de datos, identidad, seguridad, privacidad e integraciones y enlaza los IDs de dominio correspondientes. Un `not-applicable` siempre incluye un motivo; no se utiliza para ocultar una decisión todavía abierta.

Los identificadores son estables y no se reutilizan: `OBJ`, `FR`, `NFR`, `TR`, `AC`, `ADR`, `INC`, `TEST`, `EVID`, `RISK`, `OPEN` y otros prefijos del contrato canónico.

Las referencias 1.1 aceptan un ID, listas separadas por coma o punto y coma y rangos inclusivos con `..`, por ejemplo `FR-001..FR-079`. No mezcle prefijos en un rango ni omita IDs intermedios. La forma `FR-001 a FR-079` y las listas separadas únicamente por espacios son legacy: solo se aceptan con aviso al validar proyectos 1.0.

`.lks-sdd/project.json` solo indexa versiones, ruta, fase, puerta, baseline, artefactos, bindings y referencias operativas a plan, tarea, gobierno, autorización y ejecución. No duplica requisitos, decisiones, bloqueos ni readiness. En 1.3, readiness y cobertura se derivan bajo demanda de los Markdown; el índice conserva fingerprints confirmados y referencias a autorización, ejecución y checkpoint, pero el contenido humano y la evidencia siguen en Markdown/archivos canónicos.

Los anexos de arquitectura, datos, integraciones, seguridad, UX, entrega, pruebas y operación se crean solo cuando resultan aplicables. Consulte [anexos condicionales](conditional-annexes.md) para sus rutas y plantillas; una no aplicabilidad se justifica en un artefacto existente y no se representa con un documento vacío.
