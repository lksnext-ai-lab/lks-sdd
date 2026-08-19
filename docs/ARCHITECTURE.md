# Arquitectura y alcance de la versión 0.1.0

## Entorno de ejecución

LKS-SDD se implementa como plugin de desarrollo SDD para Codex. Codex es el único entorno soportado contractualmente; la posible reutilización de Markdown, esquemas o scripts en ChatGPT Work, GitHub Copilot, Claude u otros asistentes no implica compatibilidad del plugin. La matriz y los criterios de portabilidad se mantienen en `docs/COMPATIBILITY.md`.

## Implementado en M0–M1

- Plugin único `lks-sdd`, basado exclusivamente en skills y recursos locales.
- Ayuda didáctica y contextual de solo lectura.
- Definición de aplicaciones nuevas mediante Markdown estructurado e inicialización aditiva.
- Evaluación explicable de preparación por incremento, sin autorización implícita.
- Esquemas para `.lks-sdd/project.json`, front matter, catálogos y contratos preparatorios de perfil/lock sin perfil ejecutable.
- Núcleo de catorce artefactos y plantillas de anexos que solo se materializan cuando son aplicables.
- Validadores locales, sin red ni dependencias externas.
- Fixtures y evals de proyecto nuevo, información insuficiente, alternativa tecnológica, bloqueo independiente y ayuda.

## Límite de capacidad

El plugin puede explicar la ruta de adopción de un repositorio existente y `lks-sdd-define` debe detectarla, pero M1 no materializa esa adopción. Tampoco genera aplicaciones FastAPI/React, implementa incrementos ni verifica código. Ninguna documentación presenta esas capacidades como disponibles.

## Backlog explícito

### `lks-sdd-adopt-existing`

Pendiente: preflight, inventario estático estricto, reconciliación, detección de deriva, dry-run y materialización documental aditiva autorizada. Hasta implementarla, un repositorio con código se deriva de forma segura y no se modifica.

### `lks-sdd-implement`

Pendiente: validar la puerta, aplicar un perfil confirmado, implementar un incremento vertical, mantener trazabilidad y pruebas. No se creará código antes de disponer de un perfil probado y de decisiones críticas confirmadas.

### `lks-sdd-verify`

Pendiente: comprobaciones por perfil, evidencias, limitaciones y clasificación verificable. Nunca se equiparará «no ejecutado» con «superado».

## Evolución posterior

M2 debe cerrar y probar el perfil de referencia para Codex antes de implementar o verificar aplicaciones. M3 aborda adopción y vistas de cliente en el mismo entorno objetivo. MCP, conectores, hooks, apps, agentes y adaptaciones a otros asistentes solo se estudiarán si aparece una necesidad demostrada y mediante una decisión posterior.
