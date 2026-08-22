# Conceptos esenciales

- **SDD:** desarrollo guiado por especificaciones versionadas, revisables y verificables. Reduce la distancia entre lo acordado, lo implementado y lo demostrado.
- **LKS-SDD:** adaptación corporativa de SDD empaquetada como plugin para Codex. El método vive en el plugin; el estado y conocimiento de cada aplicación viven en su repositorio.
- **Plugin:** paquete distribuible de Codex que agrupa workflows y recursos. Esta versión solo contiene skills.
- **Skill:** workflow que se descubre por intención o se invoca por nombre. Explica cómo alcanzar un resultado y qué límites respetar.
- **Proyecto:** contexto de trabajo de una aplicación. No sustituye al repositorio.
- **Repositorio:** fuente versionada de documentación, código y evidencias.
- **Baseline:** estado de referencia identificado y vigente.
- **Puerta:** conjunto de condiciones comprobables para decidir si un alcance puede avanzar.
- **Familia:** agrupación no seleccionable de perfiles con una forma arquitectónica común.
- **Capability:** unidad reutilizable de constraints, preparación y gates; no es unidad de homologación.
- **Perfil:** composición tecnológica cerrada y acotada; solo un perfil exacto puede certificarse y seleccionarse mediante `BIND-###`.
- **Unidad desplegable:** frontera `UNIT-###` con runtime, interfaces y ownership propios.
- **Gobierno de entrega:** decisión `CHG-###` vigente sobre modelo de trabajo, versionado, Git, entornos, promoción, despliegue y recuperación.
- **Plan, release y tarea:** jerarquía `PLAN-###` → `REL-###` → `TASK-###` para planificación y seguimiento ejecutable.
- **Completitud de planificación:** cobertura de todo el alcance activo, aceptación y pruebas por tareas ejecutables, con integridad de release y DAG; no equivale al readiness de una tarea.
- **Autorización:** decisión `AUTH-###` que delimita incremento, release, tareas, política y huellas vigentes; no se deduce de readiness.
- **Ejecución y checkpoint:** `EXEC-###` identifica una ejecución autorizada y `CKPT-###` conserva su estado observable para reanudar sin depender del chat.
- **Preparación de especificación:** suficiencia funcional del incremento documentado; se informa como `specification_readiness`.
- **Soporte de automatización:** capacidad del plugin para preparar y verificar la pila confirmada; se informa como `automation_support` y no cambia la decisión tecnológica.
- **Huella documental:** hash de la instantánea completa, incluido el historial conservado.
- **Huella de contrato activo:** hash de los inputs confirmados y aplicables a un incremento; excluye filas rechazadas, sustituidas o retiradas.

LKS-SDD distingue hecho, objetivo, requisito, restricción, propuesta, decisión, supuesto, punto abierto, riesgo y evidencia. Una propuesta no se transforma en decisión sin confirmación explícita.

Los proyectos nuevos de 0.9.0 usan método 1.3.0 y esquema 1.3. Los esquemas 1.0, 1.1 y 1.2 permanecen soportados en compatibilidad y su migración nunca se deduce de una actualización.
