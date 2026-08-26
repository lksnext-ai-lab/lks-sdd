# Preguntas frecuentes

## ¿LKS-SDD es Spec-first, Spec-anchored o Spec-as-source?

Es **Spec-anchored**. La especificación no solo prepara el inicio: permanece versionada junto al código y conserva el contrato vigente durante definición, planificación, implementación y verificación. Si cambia el comportamiento, se revisan los artefactos afectados y una divergencia invalida las huellas o autorizaciones correspondientes hasta reconciliarla.

No es Spec-as-source. Codex puede generar o modificar código a partir de una especificación confirmada, pero LKS-SDD permite edición directa del código y exige revisión, gates y evidencia antes de declarar conformidad.

## ¿Qué aporta este enfoque en una empresa de servicios?

Permite mantener una documentación confiable y comprensible para contrastar alcance, reglas y aceptación con el cliente sin exigir que todo el desarrollo se genere mecánicamente. En proyectos existentes, la adopción parte del código para documentar el `as-is`, pero separa los hechos observados de las inferencias y de la intención que debe confirmar el cliente o el rol competente. Los borradores para cliente son vistas derivadas y revisables; la fuente canónica continúa en el repositorio.

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

No. LKS-SDD muestra por separado especificación, automatización, cobertura integral, porción seleccionada y autorización. Una `TASK-001` puede estar `ready` mientras su release sigue `partial`. Solo `ready-to-implement` con un `AUTH-###` vigente habilita preparar exactamente la porción autorizada; el apply conserva además preview y hash coincidente.

## ¿Cómo sé si toda una release está planificada?

`planning_completeness: complete` exige que todo el alcance activo, criterios y pruebas tengan tarea responsable, todas las fichas sean ejecutables, release/tablero/cobertura concuerden, el DAG no tenga ciclos y exista integración conjunta. La salida enumera cualquier hueco concreto. No se calcula a partir de un porcentaje ni de que exista una tarea lista.

## ¿Actualizar a 0.10.0 cambia mis documentos anteriores?

No. LKS-SDD 0.10.0 usa método 1.4.0 y esquema 1.4 para proyectos nuevos, pero no migra proyectos existentes al actualizar el plugin. Los proyectos 1.0, 1.1, 1.2 y 1.3 siguen validándose en compatibilidad. Llegar a 1.4 requiere migraciones explícitas de un salto con dry-run, backup, hash, autorización, validación y rollback. El salto histórico 1.2 → 1.3 sigue fijado a método 1.3.0/plugin 0.9.1; 1.3 → 1.4 añade tracking pendiente sin consultar Jira, crear issues ni interpretar el proyecto anterior como aprobación.

## ¿Qué permite reanudar sin recordar el chat?

El repositorio conserva la ejecución y su último `CKPT-###`: tareas, rama/revisión, archivos, entregables completos/parciales, aceptación, checks, evidencia, bloqueos, decisiones y siguiente acción. `continuity resume` compara esos hechos con el checkout y recomienda continuar, reconciliar o replanificar. Un checkpoint no equivale a commit ni verificación.

## ¿Cuándo se exige evidencia en la trazabilidad?

`preimplementation` exige relaciones desde cada requisito aplicable hasta aceptación, decisión o no aplicabilidad motivada, incremento y prueba. `verification` exige además evidencia ejecutada del mismo incremento. Una comprobación sin requisitos aplicables falla como alcance vacío en vez de producir un falso positivo.

## ¿Puedo usar LKS-SDD con un repositorio existente?

Sí. Es la ruta de entrada Spec-anchored para sistemas sin especificaciones confiables. `lks-sdd-adopt-existing` realiza primero un inventario estático de solo lectura y externo al repositorio. Después separa lo observado en el código de la intención confirmada y las contradicciones. La materialización solo continúa tras reconciliación, confirmación, baseline vigente, preview y autorización, y únicamente añade documentación LKS-SDD.

## ¿Funciona igual en GitHub Copilot o Claude?

No se garantiza. LKS-SDD se implementa y soporta como plugin para Codex. Los documentos y algunos validadores pueden ser reutilizables, pero Copilot, Claude u otros asistentes necesitarían su propia integración y pruebas antes de declarar compatibilidad o resultados equivalentes.

## ¿Qué archivo manda si el índice y un Markdown discrepan?

El Markdown canónico. `.lks-sdd/project.json` es un índice que debe corregirse de forma explícita, sin reescribir contenido humano. En 1.3 y 1.4, readiness y cobertura se derivan al consultar; el índice solo conserva referencias y huellas confirmadas, no una aprobación implícita.
