# Resúmenes de transición

Cada resumen responde, en lenguaje comprensible y sin volcar IDs innecesarios: dónde estamos; qué terminó; qué está en curso; qué falta; qué está bloqueado; siguiente paso recomendado; y decisión humana necesaria. Los estados se derivan del repositorio y nunca de la memoria del chat.

## Cierre de especificación con planificación parcial

> **Dónde estamos:** la especificación funcional y técnica de `INC-001` está cerrada. La arquitectura y la automatización del perfil confirmado están soportadas.
>
> **Completado:** alcance, requisitos, aceptación, fórmulas, UX, datos, privacidad, seguridad, recuperación, pruebas y gobierno de entrega están confirmados; no quedan bloqueos de especificación.
>
> **Estado de fases:** especificación `ready`; automatización `supported`; `TASK-001` `ready`; planificación de `REL-001` `partial`; implementación, verificación y entrega `not-started`.
>
> **Falta:** navegación completa, las familias y fichas restantes, unidades, monedas, seis idiomas, configuración, historial, privacidad, recuperación, calidad integral y compatibilidad todavía no tienen tarea responsable; sus criterios y pruebas asociados permanecen sin asignar.
>
> **Siguiente paso recomendado:** completar y validar la planificación integral de la release 0.1.0 antes de implementar.
>
> **Decisión humana:** confirmar que prepare la descomposición completa; autorizar solo la siguiente porción manteniendo la release como parcial; o pausar con este estado.

## Planificación completa antes de autorizar

> **Dónde estamos:** `INC-001` y `REL-001` tienen planificación `complete` e integridad `valid`.
>
> **Completado:** todo el alcance activo, aceptación y pruebas tiene una tarea primaria; las fichas son ejecutables; el DAG no tiene ciclos; `TASK-001` y `TASK-002` forman la primera frontera paralela; `TASK-009` concentra la integración conjunta.
>
> **Falta:** la implementación no ha comenzado y no existe una autorización vigente.
>
> **Siguiente paso recomendado:** revisar la selección inicial y registrar una autorización delimitada.
>
> **Decisión humana:** autorizar o rechazar `TASK-001` y `TASK-002` con las huellas mostradas. No se proponen fechas ni esfuerzo porque no están confirmados.

## Pausa o bloqueo

> **Dónde estamos:** `EXEC-001` queda pausada en `TASK-004`; `TASK-001..003` están `done`, `TASK-005` está bloqueada y `TASK-006` permanece independiente y `ready`.
>
> **Completado:** se registran entregables, criterios satisfechos y evidencia real. **Parcial:** se enumeran archivos y comportamiento incompleto de `TASK-004`. **No ejecutado:** los gates pendientes siguen `not-run`.
>
> **Bloqueo:** `PROB-002` depende de una decisión externa. El checkpoint `CKPT-006` fija rama, revisión observada, árbol, archivos y siguiente acción segura.
>
> **Siguiente paso recomendado:** reanudar `TASK-004` si el checkout coincide; mientras tanto puede avanzar `TASK-006` dentro de su autorización.
>
> **Decisión humana:** resolver `OPEN-014` o cambiar explícitamente la prioridad.

## Reanudación con divergencia

> **Dónde estamos:** el repositorio ya no coincide con `CKPT-006`; cambiaron la revisión y dos archivos registrados.
>
> **Conservado:** tareas terminadas, evidencia y decisiones anteriores siguen trazables. No se repiten ni se marcan de nuevo.
>
> **Riesgo:** no puede determinarse todavía si los cambios son compatibles con la tarea parcial; la autorización no se amplía por inferencia.
>
> **Siguiente paso recomendado:** reconciliar el checkout con el checkpoint. Si cambió el contrato activo, registrar `PCH-###` y replanificar solo lo afectado.
>
> **Decisión humana:** confirmar la reconciliación propuesta o el cambio de alcance.

## Antes de verificar o promover

> **Dónde estamos:** todas las tareas planificadas están `done`, la cobertura continúa `complete` y la verificación conjunta de release está pendiente.
>
> **Completado:** se listan revisión, build, artefactos y checks realmente superados. **Pendiente:** integración conjunta, smoke, observabilidad, recuperación o autorización de promoción que no tengan evidencia siguen visibles.
>
> **Siguiente paso recomendado:** ejecutar la verificación conjunta; solo después solicitar la decisión de entrega.
>
> **Decisión humana:** autorizar la verificación o, con evidencia completa, la promoción. Terminar tareas no autoriza despliegue.
