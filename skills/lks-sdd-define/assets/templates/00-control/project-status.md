---
artifact_id: ART-STATUS
artifact_type: project-status
schema_version: "1.0"
method_version: "1.0.0"
created_with_plugin_version: "0.1.0"
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

# Estado del proyecto

| Ruta | Fase | Puerta | Incremento activo | Readiness | Próximo paso |
|---|---|---|---|---|---|
| new | definition | G0 | none | not-assessed | Completar encuadre inicial: dominio, usuario, tarea y resultado |

## Cobertura cualitativa para el siguiente paso

| Dimensión | Estado | Alcance | Información disponible | Falta profundizar | Impacto |
|---|---|---|---|---|---|
| Contexto profesional, problema y valor | unknown | project | No confirmado durante la inicialización | Dominio, proceso, problema, tarea o decisión y resultado esperado | Impide confirmar el propósito y el valor |
| Stakeholders, usuarios y uso | unknown | project | No confirmado durante la inicialización | Perfiles, necesidades y situación de uso | Impide priorizar experiencia y requisitos |
| Alcance | unknown | project | No confirmado durante la inicialización | Incluido, excluido, supuestos y límites | Expone a ampliación silenciosa |
| Funcional, entradas y reglas | unknown | project | No confirmado durante la inicialización | Entradas, reglas, fuentes, excepciones, requisitos y aceptación | Impide especificar comportamiento comprobable |
| Experiencia e interfaz | unknown | project | Aplicabilidad no confirmada | Determinar si hay frontend y, si aplica, definir UX y prototipado | Puede bloquear el diseño del incremento |
| Calidad | unknown | project | No confirmado durante la inicialización | Cualidades medibles y pruebas proporcionales | Impide evaluar suficiencia no funcional |
| Restricciones | unknown | project | No confirmado durante la inicialización | Condicionantes con impacto | Puede invalidar propuestas posteriores |
| Datos | unknown | project | No confirmado durante la inicialización | Clasificación, ciclo de vida y migración o no aplicabilidad | Puede bloquear arquitectura y cumplimiento |
| Identidad, seguridad y privacidad | unknown | project | No confirmado durante la inicialización | Necesidades y decisiones o no aplicabilidad | Puede bloquear el incremento según riesgo |
| Integraciones | unknown | project | No confirmado durante la inicialización | Sistemas, contratos y fallos o no aplicabilidad | Puede bloquear comportamiento extremo a extremo |
| Solución y tecnología | unknown | project | No se ha seleccionado una pila | Alternativas, encaje, riesgos y decisión | Impide fijar baseline técnica |
| Entrega | unknown | project | No hay incremento activo | Alcance vertical, dependencias y riesgos | Impide evaluar readiness |
| Operación | unknown | project | Aplicabilidad no confirmada | Despliegue, observabilidad y continuidad | Puede dejar requisitos operativos sin tratar |

Estados admitidos: `unknown`, `partial`, `sufficient` o `not-applicable: motivo`. No calcule un porcentaje global; cada estado se refiere al alcance indicado.

La inicialización no confirma decisiones ni autoriza generación de código.
