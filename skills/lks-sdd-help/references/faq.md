# Preguntas frecuentes

## ¿SDD significa escribir mucha documentación?

No. El detalle se ajusta al riesgo y al siguiente incremento. El objetivo es no perder decisiones, criterios y trazabilidad necesarios, no maximizar páginas.

## ¿El plugin decide la arquitectura?

No. Puede comparar y proponer. La persona confirma las decisiones y su autoridad formal, si existe, se registra por separado.

## ¿FastAPI, React, PostgreSQL y Keycloak son obligatorios?

No. Integran el perfil H0 implementable y verificable `WEB-FASTAPI-REACT-KEYCLOAK-PG`, pero el perfil sigue siendo candidato y debe seleccionarse mediante una decisión confirmada. Una alternativa puede documentarse con su justificación.

## ¿`ready` significa que Codex puede empezar?

No. Significa que no se conocen bloqueos para el alcance evaluado. La autorización humana para implementar es independiente; `lks-sdd-implement` exige además un preview y un hash coincidente antes de escribir.

## ¿Puedo usar LKS-SDD con un repositorio existente?

Sí. `lks-sdd-adopt-existing` realiza primero un inventario estático de solo lectura y externo al repositorio. La materialización solo continúa tras reconciliación, confirmación, baseline vigente, preview y autorización, y únicamente añade documentación LKS-SDD.

## ¿Funciona igual en GitHub Copilot o Claude?

No se garantiza. LKS-SDD se implementa y soporta como plugin para Codex. Los documentos y algunos validadores pueden ser reutilizables, pero Copilot, Claude u otros asistentes necesitarían su propia integración y pruebas antes de declarar compatibilidad o resultados equivalentes.

## ¿Qué archivo manda si el índice y un Markdown discrepan?

El Markdown canónico. `.lks-sdd/project.json` es un índice que debe corregirse de forma explícita, sin reescribir el contenido humano silenciosamente.
