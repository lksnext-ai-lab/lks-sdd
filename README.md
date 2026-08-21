# LKS-SDD para Codex

LKS-SDD es un plugin corporativo para desarrollar aplicaciones web con Codex mediante Specification-Driven Development (SDD). El plugin contiene el método, las plantillas, las reglas, los validadores y la ayuda; Codex los aplica sobre el repositorio de cada aplicación, que conserva su propia documentación, código, evidencias y estado.

## Entorno objetivo y compatibilidad

Codex es el entorno objetivo y el único soportado contractualmente por esta implementación. El manifiesto `.codex-plugin`, el descubrimiento e invocación de skills, los metadatos `agents/openai.yaml` y el modelo de trabajo sobre el repositorio se diseñan y validan para Codex.

Los Markdown, esquemas JSON y algunos scripts Python pueden resultar reutilizables en otros entornos, pero eso no convierte el plugin en agnóstico. No se garantiza el mismo descubrimiento, comportamiento, control de permisos ni calidad de resultado en GitHub Copilot, Claude u otros asistentes. Cualquier compatibilidad con ellos deberá diseñarse, implementarse y probarse como un alcance independiente. Véase [Compatibilidad y entorno objetivo](docs/COMPATIBILITY.md).

La versión `0.8.0` conserva M0–M5 y las seis skills: ayuda, definición, adopción, readiness, implementación y verificación. Añade el contrato 1.2 de gobierno de entrega, arquitectura multiperfil y planificación/seguimiento profesional. Los proyectos nuevos usan `method_version: 1.2.0` y `schema_version: 1.2`; 1.0 y 1.1 permanecen validables en compatibilidad y solo cambian mediante migraciones explícitas de un salto. La release continúa como candidate: los canales humanos y de piloto no ejecutados siguen `not-run`; M6 y la promoción a `stable` permanecen pendientes. El plugin no contiene MCP, conectores, hooks, apps ni agentes ejecutables.

## Principios operativos

- Los Markdown versionados de cada aplicación son la fuente de verdad; `.lks-sdd/project.json` es solo el índice operativo.
- LKS-SDD propone, pregunta y explica. La persona usuaria decide y confirma.
- Una idea breve no se interpreta como un producto genérico: primero se aclaran dominio, usuarios, propósito y contexto mediante preguntas de alto impacto.
- Hechos, inferencias, propuestas, decisiones y pendientes se conservan como tipos distintos.
- Los bloques de definición se resumen como suficientes, parciales, desconocidos, no aplicables o bloqueados, sin porcentajes de madurez engañosos.
- Ninguna tecnología se selecciona automáticamente. Familias y capabilities son reutilizables, pero solo un perfil de referencia cerrado, certificado y ligado a una unidad desplegable puede declararse soportado.
- Antes de G2 se confirma el modelo de entrega (`bounded-release`, `continuous-evolution` o `maintenance-stream`), versionado, Git/ramas, entornos, CI/CD, promoción, despliegue y recuperación. Los cambios posteriores se registran, no reescriben el historial.
- El trabajo se planifica como `PLAN-###` → `REL-###` → `TASK-###`; el tablero facilita el seguimiento visual y cada tarea conserva una definición independiente y verificable.
- ImageGen se usa solo con un brief visual suficiente y capacidad disponible; una imagen propuesta no equivale a diseño confirmado ni sustituye requisitos o accesibilidad.
- La baseline normativa incluida es candidata. Sus `MUST`, `SHOULD` y `MAY` no equivalen a política corporativa aprobada.
- Una consulta de ayuda no modifica archivos. Una evaluación de readiness no autoriza implementación.
- La preparación de la especificación (`specification_readiness`) y el soporte de automatización (`automation_support`) se informan por separado. Una pila puede estar suficientemente especificada y no disponer de automatización implementable en este plugin.
- La trazabilidad previa a implementar exige requisito, aceptación, decisión o no aplicabilidad motivada, incremento y prueba. También resuelve el contrato activo del incremento: una relación activa a un elemento inexistente, no confirmado o histórico deja el preflight incompleto con diagnósticos `LKS-ACTIVE-*`. Esta puerta comprueba el handoff estructural, no sustituye la evaluación completa de readiness. La fase de verificación exige además evidencia ejecutada; una comprobación de alcance vacío nunca se presenta como válida. El plan puede anticiparse para una implementación `in-progress` del mismo incremento, pero ejecutar checks o registrar evidencia requiere `implementation.status: completed` y coherencia con el perfil seleccionado.
- No se genera código cuando faltan decisiones críticas para el incremento afectado.

## Estructura

- `.codex-plugin/plugin.json`: manifiesto del plugin.
- `skills/`: seis workflows de producto descubribles: ayuda, definición, adopción, readiness, implementación y verificación.
- `profiles/`: catálogo de familias/capabilities, perfiles cerrados, drivers, scaffolds, locks y certificaciones exactas.
- `schemas/`: contratos 1.0/1.1/1.2 del índice, front matter, documentos, perfiles, drivers, locks y certificaciones.
- `scripts/`: validación, trazabilidad, gobierno de entrega, tablero TASK, registro multiperfil, gates, migración y vistas derivadas.
- `templates/client/`: plantilla profesional para borradores derivados, nunca fuente canónica.
- `specs/canonical/`: tres fuentes originales preservadas por hash y tres extensiones aditivas: definición visual 0.6, contrato/handoff 1.1 y gobierno/entrega/perfiles/tareas 1.2.
- `tests/`: fixtures declarativos y evals deterministas de invariantes.
- `quality/`: catálogo M4, corpus de activación, fixtures bloqueados y baselines de comparación.
- `pilot/`: ejemplo bloqueado, plan y rollback para el piloto controlado M5.
- `distribution/`: plantilla estándar del marketplace de desarrollo generado externamente.
- `docs/ARCHITECTURE.md`: arquitectura de la versión 0.8.0, M0–M5 y límites aún vigentes.
- `docs/COMPATIBILITY.md`: entorno Codex soportado y límites de portabilidad.
- `docs/M1-COVERAGE.md`: correspondencia auditable entre M0–M1, implementación y pendientes.
- `docs/M2-COVERAGE.md`: fotografía histórica del primer perfil H0, implementación y verificación en 0.2.0.
- `docs/M3-COVERAGE.md`: correspondencia auditable entre adopción, migración y vistas cliente.
- `docs/M4-COVERAGE.md`: correspondencia auditable entre EP-10 y el harness integrado.
- `docs/M5-COVERAGE.md`: correspondencia auditable entre EP-12 y la infraestructura de piloto.
- `docs/V0.6-DEFINITION-UX-COVERAGE.md`: cobertura de la evolución compatible de entrevista, estado de definición y diseño visual.
- `docs/V0.7-CONTRACT-HANDOFF-COVERAGE.md`: cobertura del contrato documental 1.1, compatibilidad 1.0 y handoff por incremento.
- `docs/V0.8-DELIVERY-MULTIPROFILE-COVERAGE.md`: cobertura de gobierno, planificación TASK, perfiles exactos, gates y evidencia de entrega.
- `docs/QUALITY-HARNESS.md`: ejecución, evidencia y semántica de las puertas candidate/stable.
- `docs/DISTRIBUTION.md`: empaquetado, instalación controlada y retirada.
- `docs/RELEASING.md`: política de versiones, etiquetas y releases técnicas de GitHub.

## Validación local

Los comandos reproducibles y sus códigos de salida están documentados en `docs/VALIDATION.md`. La validación contractual es local; el gate técnico completo descarga las imágenes y dependencias bloqueadas y requiere Docker.

Para operar sobre un proyecto consumidor, resuelva `<plugin-root>` como la carpeta instalada que contiene `.codex-plugin/plugin.json`; no busque `scripts/` dentro del proyecto consumidor. El dispatcher portable mantiene separados ambos roots:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>"
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation
```

Use `--phase verification` cuando deba exigir `EVID-###` ejecutada. Las migraciones son explícitas y de un salto. `1.0 → 1.1` conserva su cierre seguro ante `human_review_required`; `1.1 → 1.2` crea gobierno, arquitectura, planes y tareas como pendientes sin inventar decisiones. Cada apply exige backup externo, hash de autorización y validación posterior. Actualizar el plugin no migra proyectos.

Este repositorio publica releases técnicas y genera un marketplace candidate para evaluación controlada, pero no instala globalmente el plugin ni representa una distribución corporativa estable. La licencia definitiva, los responsables nominales, el SLA y la promoción a stable requieren decisiones separadas. `LICENSE.md` registra esta restricción sin inventar una licencia y `CONTRIBUTING.md` define el contrato de cambio.
