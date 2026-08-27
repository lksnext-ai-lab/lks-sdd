---
artifact_id: ART-PLANNING
artifact_type: planning-coverage
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.14.0"
project_id: "{{PROJECT_ID}}"
baseline_id: "{{BASELINE_ID}}"
status: draft
classification: internal
audience:
  - delivery-team
owners:
  - pending-assignment
source_of_truth: true
last_updated: "{{DATE}}"
---

# Cobertura y continuidad de la planificación

## Objetivos de planificación

| Target | Type | State | Objective | Increments | Planning policy | Decision | Integration task | Review trigger |
|---|---|---|---|---|---|---|---|---|
| REL-001 | release | proposed | pending: confirm release objective | pending: confirm increments | complete-before-implementation | not-applicable: method default | pending: define joint verification task | scope, contract or dependency change |

`complete-before-implementation` es la política por defecto. `incremental-authorized` exige una decisión humana `ADR-###` que delimite tareas y mantenga visible la cobertura pendiente.

## Propiedad de cobertura

| Target | Increment | Contract items | Primary task | Contributing tasks | Responsibility | Rationale |
|---|---|---|---|---|---|---|

Cada elemento activo del contrato tiene exactamente una tarea primaria. Los contribuyentes son opcionales y no diluyen la responsabilidad de aceptación. Se admiten listas y rangos inclusivos `..`.

## Autorizaciones de implementación

| ID | State | Target | Increment | Release | Tasks | Specification fingerprint | Planning fingerprint | Authorized by role | Authorized on | Decision | Constraints |
|---|---|---|---|---|---|---|---|---|---|---|---|

Una autorización solo es vigente mientras coincidan alcance y fingerprints. No infiera personas ni autoridad; registre el rol y la decisión confirmados.

## Cambios de planificación

| ID | State | Classification | Affected contract | Affected tasks | Previous fingerprint | Current fingerprint | Decision | Reason |
|---|---|---|---|---|---|---|---|---|

Use `original-contract-failure` para reabrir una tarea terminada que incumple su contrato original y `new-scope` para crear una tarea nueva. Conserve siempre fingerprints e historial previos.

La completitud se deriva de este mapa, las tareas y el contrato activo. No escriba porcentajes, fechas, esfuerzo, velocidad, capacidad, avance ni evidencia no observados.
