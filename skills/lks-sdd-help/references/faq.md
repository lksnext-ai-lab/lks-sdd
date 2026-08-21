# Preguntas frecuentes

## ¿SDD significa escribir mucha documentación?

No. El detalle se ajusta al riesgo y al siguiente incremento. El objetivo es no perder decisiones, criterios y trazabilidad necesarios, no maximizar páginas.

## ¿El plugin decide la arquitectura?

No. Puede comparar y proponer. La persona confirma las decisiones y su autoridad formal, si existe, se registra por separado.

## ¿FastAPI, React, PostgreSQL y Keycloak son obligatorios?

No. Son una composición de referencia entre varias. El catálogo incluye perfiles cerrados para React/Vite, Angular, API, SSR y web completa, y candidatos event-driven. Cada unidad desplegable selecciona un perfil exacto por ADR; una familia o combinación ad hoc no queda soportada por compartir tecnologías.

## ¿Qué diferencia hay entre capability, perfil y lock?

Una capability reutiliza preparación y gates. Un perfil fija una composición exacta y es la unidad mínima de certificación. El lock identifica bytes y versiones resueltos, pero no demuestra por sí solo que la composición funcione: necesita todos los gates y el gate de integración exacto.

## ¿Cómo se gestionan proyectos cerrados, agile y mantenimiento?

Con un modelo explícito: `bounded-release`, `continuous-evolution` o `maintenance-stream`. Cada uno concreta versionado, ramas, releases/streams, entornos, despliegue y recuperación. Si cambia la forma de trabajo, se añade un `CHG-###` con fecha efectiva y transición; no se reescribe el historial.

## ¿Cómo se siguen las tareas?

`ART-TASKS` ofrece una vista rápida por horizonte mayor con estado, salud, progreso, dependencias y bloqueos. Cada `TASK-###` tiene una ficha independiente con definición, aceptación, gates, owner, revisión, build, artefacto, entorno, evidencia e historial. `tasks board` deriva la vista y `tasks transition` aplica cambios mediante preview, hash y autorización.

## ¿`ready` significa que Codex puede empezar?

No. `specification_readiness` indica si no se conocen bloqueos funcionales para el alcance, mientras `automation_support` comprueba si la pila confirmada tiene soporte implementable. El estado combinado puede seguir bloqueado aunque la especificación esté lista. La autorización humana es independiente; `lks-sdd-implement` exige además un preview y un hash coincidente antes de escribir.

## ¿Actualizar a 0.8.0 cambia mis documentos anteriores?

No. Los proyectos 1.0 y 1.1 siguen validándose en compatibilidad. Llegar a 1.2 requiere migraciones explícitas de un salto con dry-run, backup, hash, autorización, validación y rollback. El salto 1.1 → 1.2 crea gobierno, planes y tareas pendientes; no interpreta el proyecto anterior como aprobación.

## ¿Cuándo se exige evidencia en la trazabilidad?

`preimplementation` exige relaciones desde cada requisito aplicable hasta aceptación, decisión o no aplicabilidad motivada, incremento y prueba. `verification` exige además evidencia ejecutada del mismo incremento. Una comprobación sin requisitos aplicables falla como alcance vacío en vez de producir un falso positivo.

## ¿Puedo usar LKS-SDD con un repositorio existente?

Sí. `lks-sdd-adopt-existing` realiza primero un inventario estático de solo lectura y externo al repositorio. La materialización solo continúa tras reconciliación, confirmación, baseline vigente, preview y autorización, y únicamente añade documentación LKS-SDD.

## ¿Funciona igual en GitHub Copilot o Claude?

No se garantiza. LKS-SDD se implementa y soporta como plugin para Codex. Los documentos y algunos validadores pueden ser reutilizables, pero Copilot, Claude u otros asistentes necesitarían su propia integración y pruebas antes de declarar compatibilidad o resultados equivalentes.

## ¿Qué archivo manda si el índice y un Markdown discrepan?

El Markdown canónico. `.lks-sdd/project.json` es un índice que debe corregirse de forma explícita, sin reescribir contenido humano. En esquema 1.2, readiness, bloqueos y tablero se derivan al consultar y no se persisten como aprobación.
