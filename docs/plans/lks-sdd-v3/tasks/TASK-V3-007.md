# TASK-V3-007 · Ramas, sincronización e integración

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de integración Git**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-002](TASK-V3-002.md).
Dependencias para cerrar: [TASK-V3-006](TASK-V3-006.md), [TASK-V3-008](TASK-V3-008.md).

Requisitos de responsabilidad principal: REQ-EQT-013, REQ-EQT-014, REQ-EQT-015, REQ-EQT-018, REQ-EQT-020, REQ-EQT-026, REQ-EQT-063.
Casos de aceptación principales: AC-EQT-013, AC-EQT-016, AC-EQT-017, AC-EQT-018, AC-EQT-019, AC-EQT-025, AC-EQT-079, AC-EQT-080.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Frontera temprana de rama y sujeto
Entregar primero lectura de repo/base y vinculación de petición, para que 004 pueda
materializar documentos en la rama prevista. La sincronización de equipo e integración
completa se añaden después; no requieren crear otra tarea administrativa.
Registrar ese resultado como **base-git-local**, dependiente de 001/002, con funciones
reales y pruebas locales. Permite autoría en 004 y adopción en 011 sin depender del cierre
de toda 007; no afirma recepción remota, calidad ni integración de la petición.

Contemplar repositorio nuevo sin primer commit: representar la referencia naciente y
el inventario/sujeto observado sin inventar un SHA. Si falta Git o el destino necesario,
explicar la decisión mínima; no crear un commit para aparentar una base válida.
Preservar cambios locales ajenos. El sujeto de análisis incluye el contenido relevante
real, también cambios sin commit; una rama o HEAD no los representa por sí solos.

El cierre de esta tarea depende también de 008: la vigencia por composición/base no
puede acreditarse sin integrar el contrato real de análisis. Los conflictos semánticos
no estructurables se presentan como incertidumbre para revisión, no como “merge seguro”
por criterio automático.

## Encargo y límites
Vincular cada petición a rama, destino configurado y base antes de materializar su
documentación; permitir ramas de especialistas y excepciones delimitadas. Implementar
comprobación local de referencias e integración semántica observable, sin locks remotos.

## Entregables e interfaces
- Añadir `scripts/v3_git.py` y `v3_integration_guard.py`, aprovechando lectura Git y
  guard de `v2_integration_guard.py` sin confiar en la política candidata como autoridad.
- Distinguir alias repetido, mismo UID modificado, intención duplicada y contradicción
  de reglas/contratos compartidos. Preparar reconciliación con decisión por impacto.
- Referencias acordadas de política/equipo/petición, commits y fecha observados, estado
  de conectividad y de recepción. Actualizar al iniciar/reanudar y antes de cerrar/integrar,
  según medios autorizados; no realizar un fetch por comando ni merge implícito.
- Vínculo de evidencia con commit/árbol/artefacto; conservar correspondencias tras
  squash, rebase, cherry-pick o retirada de ramas.
- Preparar información SDD del PR/candidato y reevaluación por composición; ninguna
  aprobación de PR, push o protección remota se deriva del resultado.

## Aceptación y evidencia
Usar repositorios temporales con dos clones y remoto local de pruebas. Documentación
nueva queda ligada a su petición/rama real. Un destino distinto de main y una integración
parcial se conservan correctamente. Merge textual limpio con contradicción se detecta.
Cambio de base o composición invalida solo evidencia afectada. Reasignación local no
figura como recibida; al compartir/reanudar se registra la revisión observada.
Desconexión limita acciones conforme a política; proyecto individual local no necesita
remoto. Entregar grafos Git, inventarios, diff y diagnósticos reproducibles.

## Riesgos y revisión
Una carrera posterior solo se detecta en la siguiente comprobación: no prometer exclusión
distribuida. Revisión del integrador y gobierno. Lectura adicional: rama/trazabilidad
funcional, técnica §5.2 y actuales funciones de guard/integración.
