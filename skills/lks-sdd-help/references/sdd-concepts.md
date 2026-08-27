# Conceptos esenciales

- **SDD:** desarrollo guiado por especificaciones versionadas, revisables y verificables. Reduce la distancia entre lo acordado, lo implementado y lo demostrado.
- **Spec-first:** la especificación aclara el trabajo antes de programar, pero puede quedar como antecedente y no mantenerse durante toda la vida del producto.
- **Spec-anchored:** la especificación permanece como contrato vivo y confiable junto al código. Los cambios funcionales mantienen o reconcilian especificación, planificación, implementación y evidencia; una divergencia es un estado visible, no una actualización silenciosa de la verdad.
- **Spec-as-source:** la especificación es suficientemente ejecutable para generar de ella la mayor parte del código. Editar la especificación, más que el código derivado, es la vía principal de cambio.
- **LKS-SDD:** adaptación corporativa y Spec-anchored de SDD empaquetada como plugin para Codex. El método vive en el plugin; el estado y conocimiento de cada aplicación viven en su repositorio. Permite generar o modificar código desde el contrato confirmado, pero no presupone generación total ni confunde generación con conformidad verificada.
- **Plugin:** paquete distribuible de Codex que agrupa workflows y recursos. Esta versión solo contiene skills.
- **Skill:** workflow que se descubre por intención o se invoca por nombre. Explica cómo alcanzar un resultado y qué límites respetar.
- **Proyecto:** contexto de trabajo de una aplicación. No sustituye al repositorio.
- **Repositorio:** fuente versionada de documentación, código y evidencias.
- **Baseline adoptada:** reconstrucción documental gobernable de un sistema existente. El código observado aporta hechos sobre el `as-is`; la intención, las prioridades y el comportamiento deseado necesitan confirmación humana.
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

Para una empresa de servicios, el ancla documental ofrece un lenguaje contrastable con el cliente sin frenar la evolución del código. Una vista para cliente se deriva de fuentes confirmadas, conserva procedencia y requiere revisión; no sustituye a los Markdown canónicos ni convierte una inferencia técnica en acuerdo.

Los proyectos nuevos de 0.13.0 usan método 1.5.0 y esquema 1.5. Los esquemas 1.0, 1.1, 1.2, 1.3, 1.4 y 1.5 permanecen soportados en compatibilidad y su migración nunca se deduce de una actualización. El salto histórico 1.2 → 1.3 conserva método 1.3.0/plugin 0.9.1.
