# Arquitectura y alcance de la versión 0.2.0

## Entorno de ejecución

LKS-SDD se implementa como plugin de desarrollo SDD para Codex. Codex es el único entorno soportado contractualmente; la posible reutilización de Markdown, esquemas o scripts en ChatGPT Work, GitHub Copilot, Claude u otros asistentes no implica compatibilidad del plugin. La matriz y los criterios de portabilidad se mantienen en `docs/COMPATIBILITY.md`.

## Implementado en M0–M2

- Plugin único `lks-sdd`, basado exclusivamente en skills y recursos locales.
- Ayuda didáctica y contextual de solo lectura.
- Definición de aplicaciones nuevas mediante Markdown estructurado e inicialización aditiva.
- Evaluación explicable de preparación por incremento, sin autorización implícita.
- Esquemas para `.lks-sdd/project.json`, front matter, catálogos, perfil y lock.
- Núcleo de catorce artefactos y plantillas de anexos que solo se materializan cuando son aplicables.
- Perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, con versiones y contenedores fijados, scaffold de referencia, CI y gate reproducible.
- Preparación aditiva y autorizada del scaffold solo para un incremento listo y un perfil H0 validado.
- Verificación planificada y ejecutable que diferencia `passed`, `failed`, `not-run` y limitaciones.
- Validadores locales; solo el gate técnico explícito ejecuta herramientas externas y tráfico de descarga o health checks.
- Fixtures y evals de proyecto nuevo, información insuficiente, alternativa tecnológica, bloqueo independiente y ayuda.

## Límite de capacidad

El plugin detecta la ruta de adopción de un repositorio existente, pero M2 todavía no la inspecciona ni materializa. La implementación no inventa comportamiento de negocio: prepara la frontera técnica H0 y solo continúa cuando las decisiones y el incremento están confirmados. La verificación no convierte una comprobación no ejecutada en superada.

## Backlog explícito

### `lks-sdd-adopt-existing`

Pendiente: preflight, inventario estático estricto, reconciliación, detección de deriva, dry-run y materialización documental aditiva autorizada. Hasta implementarla, un repositorio con código se deriva de forma segura y no se modifica.

## Evolución posterior

M3 aborda adopción, migración de contrato y vistas derivadas para cliente en el mismo entorno objetivo. MCP, conectores, hooks, apps, agentes y adaptaciones a otros asistentes solo se estudiarán si aparece una necesidad demostrada y mediante una decisión posterior.
