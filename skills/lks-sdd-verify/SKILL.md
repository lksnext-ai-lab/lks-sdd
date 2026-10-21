---
name: lks-sdd-verify
description: "Use with Codex. Verify implementation against observable criteria, consolidate functional specifications and close with distinct delivery facts."
---

# Verificar y consolidar

Lee las [reglas y comandos v5](../../docs/V5.md). Resuelve `<plugin-root>` desde
la ubicación de esta skill; nunca supongas que coincide con el proyecto consumidor.
Si existe `.lks-sdd/distribution-lock.json`, usa su runtime exacto. El CLI comprueba
la integridad en cada operación; no repitas doctor aparte. Antes de editar documentos
directamente, ejecuta `python <runtime>/scripts/lks_sdd.py doctor --root <proyecto>`.
Un fallo de integridad se reconcilia; no se evita usando otro runtime.
Sin runtime fijado usa el plugin instalado. La consulta no instala nada.
Para un formato antiguo, solo adopción/migración convierte; no hagas escritura dual.

Contrasta cada criterio con implementación y evidencia. Ejecuta o importa solo las comprobaciones pertinentes que faltan o están invalidadas. Corrige hallazgos dentro del alcance autorizado; pruebas pasadas no equivalen a aceptación humana. Consolida el comportamiento final en las capacidades y cierra con close, que comprueba bases y resultados y retira solo temporales propios sin modificar. El plan conserva decisiones y resultados útiles; no añadas un informe obligatorio separado. Registra implementation, verification, integration, publication, deployment y acceptance con evidencia o not-run/unknown. Entregar o desplegar no dispara una regresión completa salvo política explícita del proyecto; delivery registra el hecho, no ejecuta el despliegue. No publiques, instales, hagas commit/push ni contactes terceros fuera de autorización humana explícita.

Markdown es canónico; el índice es derivado. Carga tarea + plan + capacidades
aplicables, no todo el histórico. Actualiza el plan existente durante la ejecución.
Respeta las instrucciones del proyecto y la autoridad ya expresada por la persona.
No inventes decisiones, autenticación, pruebas, aceptación o métricas de tokens.
En Copilot aplica el mismo núcleo; las pruebas de otro host no acreditan aceptación
conversacional de este. Si el usuario pide imágenes, usa las herramientas disponibles
con su autorización; no introduzcas APIs de pago implícitas.

El cierre del padre debe cubrir todos sus criterios, también cuando hay subtareas; usa criterion_links sin duplicar resultados. Con delegación completa, reutiliza los controles comunes vigentes de los hijos sin repetirlos en el padre. La vigencia de CI usa la fecha original de ejecución, nunca la importación. Close conserva los hechos de entrega ya registrados; aporta solo cambios y mantén unknown cuando falte evidencia. Close y delivery aplican los mismos controles de entrega. Evalúa crecimiento documental total por conocimiento útil, no tamaño por documento.
