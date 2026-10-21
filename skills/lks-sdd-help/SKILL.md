---
name: lks-sdd-help
description: "Use with Codex. Understand LKS-SDD and read a project or task status without modifying it."
---

# Consultar y reanudar

Lee las [reglas y comandos v5](../../docs/V5.md). Resuelve `<plugin-root>` desde
la ubicación de esta skill; nunca supongas que coincide con el proyecto consumidor.
Si existe `.lks-sdd/distribution-lock.json`, usa su runtime exacto. El CLI comprueba
la integridad en cada operación; no repitas doctor aparte. Antes de editar documentos
directamente, ejecuta `python <runtime>/scripts/lks_sdd.py doctor --root <proyecto>`.
Un fallo de integridad se reconcilia; no se evita usando otro runtime.
Sin runtime fijado usa el plugin instalado. La consulta no instala nada.
Para un formato antiguo, solo adopción/migración convierte; no hagas escritura dual.

Lee el contexto del proyecto; si se identifica una tarea usa `context --task ID` y `status --task ID`. Explica comportamiento, estado, decisiones y siguiente acción con referencias a los Markdown. La consulta no inicializa ni migra. En un proyecto antiguo explica la ruta de migración; conserva su lectura sin ejecutar el motor antiguo.

Markdown es canónico; el índice es derivado. Carga tarea + plan + capacidades
aplicables, no todo el histórico. Actualiza el plan existente durante la ejecución.
Respeta las instrucciones del proyecto y la autoridad ya expresada por la persona.
No inventes decisiones, autenticación, pruebas, aceptación o métricas de tokens.
En Copilot aplica el mismo núcleo; las pruebas de otro host no acreditan aceptación
conversacional de este. Si el usuario pide imágenes, usa las herramientas disponibles
con su autorización; no introduzcas APIs de pago implícitas.
