# Contrato documental mínimo

Cada Markdown canónico empieza con front matter validable: `artifact_id`, `artifact_type`, `schema_version`, `method_version`, `created_with_plugin_version`, `project_id`, `baseline_id`, `status`, `classification`, `audience`, `owners`, `source_of_truth` y `last_updated`.

El núcleo se materializa bajo `docs/lks-sdd/`:

- `00-control/project-status.md`, `scope-register.md`, `open-points.md`;
- `01-context/product-brief.md`, `constraints.md`;
- `02-requirements/functional-requirements.md`, `non-functional-requirements.md`, `technical-requirements.md`, `acceptance-criteria.md`;
- `03-solution/solution-overview.md`;
- `04-delivery/increments.md`, `risks-dependencies.md`;
- `05-quality/quality-strategy.md`, `traceability.md`.

Las tablas estructurales usan encabezados estables definidos por las plantillas. Las celdas de texto pueden redactarse libremente. Estados documentales: `draft`, `proposed`, `confirmed`, `superseded`, `retired`. Estados de elementos: `fact`, `requirement`, `proposal`, `decision`, `assumption`, `open`, `blocked`, `not-applicable`, además de `planned` para pruebas.

Cada incremento declara alcance incluido y excluido, requisitos, criterios, decisiones, datos, identidad, integraciones y pruebas. Un `not-applicable` siempre incluye un motivo; no se utiliza para ocultar una decisión todavía abierta.

Los identificadores son estables y no se reutilizan: `OBJ`, `FR`, `NFR`, `TR`, `AC`, `ADR`, `INC`, `TEST`, `EVID`, `RISK`, `OPEN` y otros prefijos del contrato canónico.

`.lks-sdd/project.json` solo indexa versiones, ruta, fase, puerta, baseline, artefactos, bloqueos, perfil y readiness. No duplica requisitos ni decisiones.

Los anexos de arquitectura, datos, integraciones, seguridad, UX, entrega, pruebas y operación se crean solo cuando resultan aplicables. Consulte [anexos condicionales](conditional-annexes.md) para sus rutas y plantillas; una no aplicabilidad se justifica en un artefacto existente y no se representa con un documento vacío.
