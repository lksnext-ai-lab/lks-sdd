---
name: lks-sdd-assess-readiness
description: "Use with Codex. Assess whether a defined task has enough current decisions, authority and dependencies to proceed; do not execute it."
---

# Evaluar preparación

Lee las [reglas y comandos v5](../../docs/V5.md). Resuelve `<plugin-root>` desde
la ubicación de esta skill; nunca supongas que coincide con el proyecto consumidor.
Si existe `.lks-sdd/distribution-lock.json`, usa su runtime exacto. El CLI comprueba
la integridad en cada operación; no repitas doctor aparte. Antes de editar documentos
directamente, ejecuta `python <runtime>/scripts/lks_sdd.py doctor --root <proyecto>`.
Un fallo de integridad se reconcilia; no se evita usando otro runtime.
Sin runtime fijado usa el plugin instalado. La consulta no instala nada.
Para un formato antiguo, solo adopción/migración convierte; no hagas escritura dual.

Lee tarea, plan y capacidades aplicables. Evalúa criterios, enfoque, decisiones críticas, autoridad de la conversación o registrada, dependencias y entorno necesario. Distingue falta documental reparable de una decisión humana pendiente. Indica qué porción puede avanzar y qué bloqueo concreto afecta a otra. Registra la evaluación en el plan solo cuando se solicita mantenerlo; no generes certificados ni recibos. La suficiencia del plan no acredita que las pruebas hayan pasado. No repitas aprobaciones vigentes.

En proyectos migrados, los estados y comentarios antiguos son antecedentes, no
órdenes de reconstruir controles retirados. Evalúa solo el trabajo que se pretende
retomar. No abras una campaña de configuración o reverificación de todo el histórico.
Aplica la política a las rutas pertinentes; conserva separados los bloqueos reales,
las incertidumbres y la ausencia de configuración ejecutable.

Markdown es canónico; el índice es derivado. Carga tarea + plan + capacidades
aplicables, no todo el histórico. Actualiza el plan existente durante la ejecución.
Respeta las instrucciones del proyecto y la autoridad ya expresada por la persona.
No inventes decisiones, autenticación, pruebas, aceptación o métricas de tokens.
En Copilot aplica el mismo núcleo; las pruebas de otro host no acreditan aceptación
conversacional de este. Si el usuario pide imágenes, usa las herramientas disponibles
con su autorización; no introduzcas APIs de pago implícitas.
