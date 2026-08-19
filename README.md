# LKS-SDD para Codex

LKS-SDD es un plugin corporativo para desarrollar aplicaciones web con Codex mediante Specification-Driven Development (SDD). El plugin contiene el método, las plantillas, las reglas, los validadores y la ayuda; Codex los aplica sobre el repositorio de cada aplicación, que conserva su propia documentación, código, evidencias y estado.

## Entorno objetivo y compatibilidad

Codex es el entorno objetivo y el único soportado contractualmente por esta implementación. El manifiesto `.codex-plugin`, el descubrimiento e invocación de skills, los metadatos `agents/openai.yaml` y el modelo de trabajo sobre el repositorio se diseñan y validan para Codex.

Los Markdown, esquemas JSON y algunos scripts Python pueden resultar reutilizables en otros entornos, pero eso no convierte el plugin en agnóstico. No se garantiza el mismo descubrimiento, comportamiento, control de permisos ni calidad de resultado en GitHub Copilot, Claude u otros asistentes. Cualquier compatibilidad con ellos deberá diseñarse, implementarse y probarse como un alcance independiente. Véase [Compatibilidad y entorno objetivo](docs/COMPATIBILITY.md).

Esta entrega implementa el incremento M0–M1 de la versión `0.1.0`: `lks-sdd-help`, `lks-sdd-define` y `lks-sdd-assess-readiness`. No implementa todavía `lks-sdd-adopt-existing`, `lks-sdd-implement` ni `lks-sdd-verify`; tampoco contiene MCP, conectores, hooks, apps, agentes especializados ejecutables ni scaffolds de aplicación. Los `agents/openai.yaml` de cada skill son únicamente metadatos de interfaz e invocación.

## Principios operativos

- Los Markdown versionados de cada aplicación son la fuente de verdad; `.lks-sdd/project.json` es solo el índice operativo.
- LKS-SDD propone, pregunta y explica. La persona usuaria decide y confirma.
- Hechos, inferencias, propuestas, decisiones y pendientes se conservan como tipos distintos.
- FastAPI, React, PostgreSQL y Keycloak son una preferencia que debe justificarse y confirmarse, nunca una selección automática.
- La baseline normativa incluida es candidata. Sus `MUST`, `SHOULD` y `MAY` no equivalen a política corporativa aprobada.
- Una consulta de ayuda no modifica archivos. Una evaluación de readiness no autoriza implementación.
- No se genera código cuando faltan decisiones críticas para el incremento afectado.

## Estructura

- `.codex-plugin/plugin.json`: manifiesto del plugin.
- `skills/`: tres workflows M1 descubribles.
- `schemas/`: contratos del índice, front matter, catálogos y futuros perfil/lock sin perfil ejecutable.
- `scripts/`: validación local del plugin y de proyectos consumidores.
- `specs/canonical/`: copias exactas de las tres fuentes canónicas del incremento.
- `tests/`: fixtures declarativos y evals deterministas de invariantes.
- `docs/ARCHITECTURE.md`: límites de M1 y backlog de las tres skills posteriores.
- `docs/COMPATIBILITY.md`: entorno Codex soportado y límites de portabilidad.
- `docs/M1-COVERAGE.md`: correspondencia auditable entre M0–M1, implementación y pendientes.

## Validación local

Los comandos reproducibles y sus códigos de salida están documentados en `docs/VALIDATION.md`. La suite no requiere red ni dependencias Python externas.

Este repositorio no publica ni instala el plugin. La distribución corporativa, la licencia definitiva, los responsables nominales y el marketplace quedan fuera de este incremento y requieren decisiones separadas. `LICENSE.md` registra esta restricción sin inventar una licencia y `CONTRIBUTING.md` define el contrato de cambio.
