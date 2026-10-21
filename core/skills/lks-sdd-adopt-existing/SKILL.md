---
name: lks-sdd-adopt-existing
description: "Use with Codex. Adopt existing project knowledge or perform an explicitly requested complete migration to the v5 document model."
---

# Adoptar o migrar

Lee las [reglas y comandos v5](../../docs/V5.md). Resuelve `<plugin-root>` desde
la ubicación de esta skill; nunca supongas que coincide con el proyecto consumidor.
Si existe `.lks-sdd/distribution-lock.json`, usa su runtime exacto. El CLI comprueba
la integridad en cada operación; no repitas doctor aparte. Antes de editar documentos
directamente, ejecuta `python <runtime>/scripts/lks_sdd.py doctor --root <proyecto>`.
Un fallo de integridad se reconcilia; no se evita usando otro runtime.
Sin runtime fijado usa el plugin instalado. La consulta no instala nada.
Para un formato antiguo, solo adopción/migración convierte; no hagas escritura dual.

Inspecciona el repositorio sin inferir aceptación a partir de código existente. En una adopción nueva registra capacidades, evidencia, lagunas y decisiones tecnológicas observadas; una petición de consulta no autoriza inicialización. Para formatos anteriores usa migration-preview, revisa agrupaciones funcionales, referencias, decisiones, tareas, controles vigentes y retirada definitiva. La autorización explícita de migrar cubre la aplicación del preview concreto si respeta el alcance; no pidas aprobación por archivo. Aplica con migration-apply --preview HASH. Ante interrupción usa migration-resume para terminar hacia v5. La migración no tiene rollback ni conserva backups por precaución; retira la preparación temporal al terminar. Revisa las tareas afectadas por contradicciones; no inventes su resolución. No borres cachés globales ni runtimes compartidos. Comprueba validate y doctor, continuidad de criterios y controles y ausencia de dependencias operativas antiguas. Evalúa el conjunto documental y su valor: elimina control y trazabilidad sin utilidad, sin imponer límites de tamaño a las especificaciones.

Entrega el único `docs/informe-conversion-sdd-v5.md` generado tras la conversión.
Explica archivos y bytes antes/después, qué se retira y qué bloqueos declara el origen.
No llames pendientes funcionales a indicadores del método antiguo ni a configuración
ausente de pruebas. No reconstruyas checkpoints, observers o recibos retirados.
No conviertas propuestas y solicitudes históricas en nuevas tareas ni reabras trabajos
terminados. Prepara los controles al retomar el alcance pertinente, respetando sus rutas
de aplicabilidad y sin presentar pruebas históricas como resultados actuales.
No crees expedientes por archivo ni presentes una reducción de bytes como aceptación.

Markdown es canónico; el índice es derivado. Carga tarea + plan + capacidades
aplicables, no todo el histórico. Actualiza el plan existente durante la ejecución.
Respeta las instrucciones del proyecto y la autoridad ya expresada por la persona.
No inventes decisiones, autenticación, pruebas, aceptación o métricas de tokens.
En Copilot aplica el mismo núcleo; las pruebas de otro host no acreditan aceptación
conversacional de este. Si el usuario pide imágenes, usa las herramientas disponibles
con su autorización; no introduzcas APIs de pago implícitas.
