---
name: lks-sdd-define
description: "Use with Codex. Define requested behavior, capability boundaries, acceptance criteria and one evolving task plan before implementation."
---

# Definir y planificar

Lee las [reglas y comandos v5](../../docs/V5.md). Resuelve `<plugin-root>` desde
la ubicación de esta skill; nunca supongas que coincide con el proyecto consumidor.
Si existe `.lks-sdd/distribution-lock.json`, usa su runtime exacto. El CLI comprueba
la integridad en cada operación; no repitas doctor aparte. Antes de editar documentos
directamente, ejecuta `python <runtime>/scripts/lks_sdd.py doctor --root <proyecto>`.
Un fallo de integridad se reconcilia; no se evita usando otro runtime.
Sin runtime fijado usa el plugin instalado. La consulta no instala nada.
Para un formato antiguo, solo adopción/migración convierte; no hagas escritura dual.

Contrasta la petición con las capacidades aplicables. Registra hechos, propuestas, decisiones y pendientes por separado. Define comportamiento y criterios observables en tarea.md y el enfoque técnico, comprobaciones proporcionales, dependencias, responsable y siguiente paso en plan.md. Reutiliza una capacidad existente cuando cubra el mismo comportamiento; reglas transversales se escriben una vez. Para tareas complejas registra subtareas con un par de documentos cada una, manteniendo sus relaciones. No selecciones una pila preferente ni implementes una decisión crítica pendiente. La autorización ya expresada en este chat puede registrarse con su alcance exacto; no solicites una ratificación por crear el plan.

Markdown es canónico; el índice es derivado. Carga tarea + plan + capacidades
aplicables, no todo el histórico. Actualiza el plan existente durante la ejecución.
Respeta las instrucciones del proyecto y la autoridad ya expresada por la persona.
No inventes decisiones, autenticación, pruebas, aceptación o métricas de tokens.
En Copilot aplica el mismo núcleo; las pruebas de otro host no acreditan aceptación
conversacional de este. Si el usuario pide imágenes, usa las herramientas disponibles
con su autorización; no introduzcas APIs de pago implícitas.
