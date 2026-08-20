# Contrato documental mínimo

Cada Markdown canónico empieza con front matter validable: `artifact_id`, `artifact_type`, `schema_version`, `method_version`, `created_with_plugin_version`, `project_id`, `baseline_id`, `status`, `classification`, `audience`, `owners`, `source_of_truth` y `last_updated`.

Las inicializaciones nuevas de LKS-SDD 0.7.0 usan `method_version: 1.1.0` y `schema_version: 1.1`. Los documentos 1.0 siguen siendo validables en modo de compatibilidad; no deben actualizarse campo a campo ni al instalar una versión nueva del plugin. La migración 1.0 → 1.1 requiere su propio preview. Si quedan entradas en `human_review_required`, se bloquea siempre antes de crear backup o escribir hasta resolver cada entrada en los Markdown canónicos 1.0 y repetir el preview con lista vacía; solo entonces admite backup externo, hash, autorización y validación. La `Identity` agregada se traslada aparte a tres dominios `pending`, sin referencias inferidas: el resultado valida, pero no supera readiness hasta resolverlos en 1.1.

El núcleo se materializa bajo `docs/lks-sdd/`:

- `00-control/project-status.md`, `scope-register.md`, `open-points.md`;
- `01-context/product-brief.md`, `constraints.md`;
- `02-requirements/functional-requirements.md`, `non-functional-requirements.md`, `technical-requirements.md`, `acceptance-criteria.md`;
- `03-solution/solution-overview.md`;
- `04-delivery/increments.md`, `risks-dependencies.md`;
- `05-quality/quality-strategy.md`, `traceability.md`.

Las tablas estructurales usan encabezados estables definidos por el catálogo declarativo. Cada tabla declara el propietario de sus IDs, relaciones, cardinalidad, aplicabilidad y política de estados; las celdas de texto pueden redactarse libremente. La naturaleza de un elemento deriva de su artefacto o prefijo (`FR`, `ADR`, `RISK`, etc.) y su columna `State` expresa ciclo de vida. No use estados legacy como `fact`, `requirement` o `assumption` para duplicar esa naturaleza en 1.1; durante el preview de migración aparecen como casos de revisión humana que deben resolverse en el origen 1.0, no como confirmaciones automáticas aplicables.

Cada incremento declara alcance incluido y excluido, requisitos, criterios, decisiones y pruebas. Una matriz separada declara por incremento la aplicabilidad de datos, identidad, seguridad, privacidad e integraciones y enlaza los IDs de dominio correspondientes. Un `not-applicable` siempre incluye un motivo; no se utiliza para ocultar una decisión todavía abierta.

Los identificadores son estables y no se reutilizan: `OBJ`, `FR`, `NFR`, `TR`, `AC`, `ADR`, `INC`, `TEST`, `EVID`, `RISK`, `OPEN` y otros prefijos del contrato canónico.

Las referencias 1.1 aceptan un ID, listas separadas por coma o punto y coma y rangos inclusivos con `..`, por ejemplo `FR-001..FR-079`. No mezcle prefijos en un rango ni omita IDs intermedios. La forma `FR-001 a FR-079` y las listas separadas únicamente por espacios son legacy: solo se aceptan con aviso al validar proyectos 1.0.

`.lks-sdd/project.json` solo indexa versiones, ruta, fase, puerta, baseline, artefactos y perfil. No duplica requisitos ni decisiones. En 1.1, readiness se deriva bajo demanda del contrato Markdown y no se persiste como aprobación en el índice; el campo legacy de proyectos 1.0 se interpreta únicamente en compatibilidad.

Los anexos de arquitectura, datos, integraciones, seguridad, UX, entrega, pruebas y operación se crean solo cuando resultan aplicables. Consulte [anexos condicionales](conditional-annexes.md) para sus rutas y plantillas; una no aplicabilidad se justifica en un artefacto existente y no se representa con un documento vacío.
