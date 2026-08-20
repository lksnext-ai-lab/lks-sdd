# LKS-SDD para Codex

LKS-SDD es un plugin corporativo para desarrollar aplicaciones web con Codex mediante Specification-Driven Development (SDD). El plugin contiene el método, las plantillas, las reglas, los validadores y la ayuda; Codex los aplica sobre el repositorio de cada aplicación, que conserva su propia documentación, código, evidencias y estado.

## Entorno objetivo y compatibilidad

Codex es el entorno objetivo y el único soportado contractualmente por esta implementación. El manifiesto `.codex-plugin`, el descubrimiento e invocación de skills, los metadatos `agents/openai.yaml` y el modelo de trabajo sobre el repositorio se diseñan y validan para Codex.

Los Markdown, esquemas JSON y algunos scripts Python pueden resultar reutilizables en otros entornos, pero eso no convierte el plugin en agnóstico. No se garantiza el mismo descubrimiento, comportamiento, control de permisos ni calidad de resultado en GitHub Copilot, Claude u otros asistentes. Cualquier compatibilidad con ellos deberá diseñarse, implementarse y probarse como un alcance independiente. Véase [Compatibilidad y entorno objetivo](docs/COMPATIBILITY.md).

La versión `0.6.1` conserva M0–M5 y las seis skills previstas: ayuda, definición, adopción de existentes, readiness, implementación y verificación. Mantiene la evolución compatible de la definición incorporada en 0.6.0: encuadre inicial más curioso, snapshots sencillos de cobertura y, cuando existe frontend, especificación de pantallas, flujos, interacción y un ciclo visual condicional con ImageGen. Clasifica el plugin como `Developer Tools`. Mantiene el perfil H0, migración, vistas cliente, harness de calidad, bundle de marketplace y la infraestructura de piloto M5. El piloto real, M6 y la promoción a `stable` permanecen pendientes. El plugin no contiene MCP, conectores, hooks, apps ni agentes especializados ejecutables.

## Principios operativos

- Los Markdown versionados de cada aplicación son la fuente de verdad; `.lks-sdd/project.json` es solo el índice operativo.
- LKS-SDD propone, pregunta y explica. La persona usuaria decide y confirma.
- Una idea breve no se interpreta como un producto genérico: primero se aclaran dominio, usuarios, propósito y contexto mediante preguntas de alto impacto.
- Hechos, inferencias, propuestas, decisiones y pendientes se conservan como tipos distintos.
- Los bloques de definición se resumen como suficientes, parciales, desconocidos, no aplicables o bloqueados, sin porcentajes de madurez engañosos.
- FastAPI, React, PostgreSQL y Keycloak son una preferencia que debe justificarse y confirmarse, nunca una selección automática.
- ImageGen se usa solo con un brief visual suficiente y capacidad disponible; una imagen propuesta no equivale a diseño confirmado ni sustituye requisitos o accesibilidad.
- La baseline normativa incluida es candidata. Sus `MUST`, `SHOULD` y `MAY` no equivalen a política corporativa aprobada.
- Una consulta de ayuda no modifica archivos. Una evaluación de readiness no autoriza implementación.
- No se genera código cuando faltan decisiones críticas para el incremento afectado.

## Estructura

- `.codex-plugin/plugin.json`: manifiesto del plugin.
- `skills/`: seis workflows M1–M3 descubribles.
- `profiles/`: perfil H0 probado, lock exacto, guía y scaffold reproducible.
- `schemas/`: contratos del índice, front matter, catálogos, perfil y lock.
- `scripts/`: validación, trazabilidad, gates técnicos, migración y vistas derivadas.
- `templates/client/`: plantilla profesional para borradores derivados, nunca fuente canónica.
- `specs/canonical/`: tres fuentes originales preservadas por hash y la extensión aditiva de definición visual v0.1.
- `tests/`: fixtures declarativos y evals deterministas de invariantes.
- `quality/`: catálogo M4, corpus de activación, fixtures bloqueados y baselines de comparación.
- `pilot/`: ejemplo bloqueado, plan y rollback para el piloto controlado M5.
- `distribution/`: plantilla estándar del marketplace de desarrollo generado externamente.
- `docs/ARCHITECTURE.md`: arquitectura de la versión 0.6.1, M0–M5 y límites aún vigentes.
- `docs/COMPATIBILITY.md`: entorno Codex soportado y límites de portabilidad.
- `docs/M1-COVERAGE.md`: correspondencia auditable entre M0–M1, implementación y pendientes.
- `docs/M2-COVERAGE.md`: correspondencia auditable entre perfil H0, implementación y verificación.
- `docs/M3-COVERAGE.md`: correspondencia auditable entre adopción, migración y vistas cliente.
- `docs/M4-COVERAGE.md`: correspondencia auditable entre EP-10 y el harness integrado.
- `docs/M5-COVERAGE.md`: correspondencia auditable entre EP-12 y la infraestructura de piloto.
- `docs/V0.6-DEFINITION-UX-COVERAGE.md`: cobertura de la evolución compatible de entrevista, estado de definición y diseño visual.
- `docs/QUALITY-HARNESS.md`: ejecución, evidencia y semántica de las puertas candidate/stable.
- `docs/DISTRIBUTION.md`: empaquetado, instalación controlada y retirada.
- `docs/RELEASING.md`: política de versiones, etiquetas y releases técnicas de GitHub.

## Validación local

Los comandos reproducibles y sus códigos de salida están documentados en `docs/VALIDATION.md`. La validación contractual es local; el gate técnico completo descarga las imágenes y dependencias bloqueadas y requiere Docker.

Este repositorio publica releases técnicas y genera un marketplace candidate para evaluación controlada, pero no instala globalmente el plugin ni representa una distribución corporativa estable. La licencia definitiva, los responsables nominales, el SLA y la promoción a stable requieren decisiones separadas. `LICENSE.md` registra esta restricción sin inventar una licencia y `CONTRIBUTING.md` define el contrato de cambio.
