# Cobertura auditable de M0–M1

## Hechos verificados

- El plugin es skills-only y declara únicamente ayuda, definición y readiness.
- Codex es el entorno objetivo soportado; la compatibilidad con otros asistentes no se infiere ni se declara sin pruebas específicas.
- Las tres fuentes de `specs/canonical/` se preservan por hash y no se editan desde la implementación.
- El inicializador crea el núcleo documental de una aplicación nueva, ofrece dry-run, conserva archivos existentes, se reanuda de forma idempotente y deriva repositorios con código a la ruta de adopción no implementada.
- Los Markdown conservan el contenido sustantivo; `.lks-sdd/project.json` solo indexa artefactos, bloqueos, perfil y readiness.
- Readiness evalúa un incremento, localiza bloqueos, conserva pendientes independientes y nunca autoriza implementación.
- La ayuda valida contexto en solo lectura y cubre explicación breve, onboarding, comparación Work–Codex, estado, ejemplos, FAQ y troubleshooting.

## Correspondencia con las épicas M1

| Épica | Implementación M1 | Evidencia principal |
|---|---|---|
| EP-00 Repositorio y gobierno | README, CHANGELOG, GOVERNANCE, SECURITY, contribución y estado explícito de licencia; responsables nominales conservados como pendientes. | `README.md`, `CONTRIBUTING.md`, `LICENSE.md`, `GOVERNANCE.md`, `SECURITY.md` |
| EP-01 Esqueleto | Manifest válido, identidad `lks-sdd`, tres skills reales y ausencia comprobada de MCP, apps, hooks, agentes raíz o entrypoints de backlog. | `.codex-plugin/plugin.json`, `scripts/validate_plugin_contract.py` |
| EP-02 Contrato documental | Núcleo de 14 artefactos, anexos condicionales empaquetados, catálogos, esquemas de proyecto/front matter/perfil/lock y validación de rutas, tipos, tablas, IDs y referencias. | `schemas/`, `skills/lks-sdd-define/assets/templates/`, `scripts/validate_project.py` |
| EP-03 Definición | Activación natural, clasificación semántica, entrevista adaptativa, pila no automática, inicialización segura y actualización quirúrgica guiada por artefacto. | `skills/lks-sdd-define/` y tests de inicialización, colisión, reanudación y alternativa |
| EP-04 Readiness | Rúbrica, validador, tres resultados explicables, bloqueo localizado y no autorización. | `skills/lks-sdd-assess-readiness/` y fixtures de insuficiencia, alternativa y bloqueo independiente |
| EP-13 Ayuda | Respuesta breve, onboarding, ayuda contextual con siete partes, ciclo de vida, ejemplos, FAQ, troubleshooting y realidad de producto versionada. | `skills/lks-sdd-help/` y fixture de ayuda de solo lectura |

## Decisiones de alcance aplicadas

- M1 termina antes de implementación y verificación de código.
- No se crean carpetas ni SKILL.md vacíos para `lks-sdd-adopt-existing`, `lks-sdd-implement` o `lks-sdd-verify`.
- Los esquemas de perfil son contratos preparatorios; no existe un perfil ejecutable, homologado o seleccionado automáticamente.
- Los anexos son recursos disponibles, pero solo se materializan con aplicabilidad confirmada. Los entregables para cliente continúan en M3.
- La incompatibilidad de versiones se bloquea; no existe una versión anterior publicada que requiera migración automática en M1.

## Pendientes externos o de hitos posteriores

- Propietario del método, mantenedores, responsables de perfiles, seguridad, publicación y soporte.
- Licencia definitiva y política corporativa aprobada.
- Marketplace de desarrollo, instalación, piloto y publicación.
- Integraciones independientes para Copilot, Claude u otros asistentes, si se aprueban en el futuro.
- Perfil H0 y sus locks probados (M2).
- Implementación y verificación de incrementos (M2).
- Adopción automatizada de repositorios, migraciones entre versiones publicadas y vistas de cliente (M3).

Estos pendientes están declarados; ninguno se presenta como capacidad disponible ni se resuelve inventando una aprobación.
