---
name: lks-sdd-implement
description: "Use with Codex. Implement or resume authorized tasks, handle dependent subtasks and keep progress and proportional verification in their existing plan."
---

# Implementar y continuar

Lee las [reglas y comandos v5](../../docs/V5.md). Resuelve `<plugin-root>` desde
la ubicación de esta skill; nunca supongas que coincide con el proyecto consumidor.
Si existe `.lks-sdd/distribution-lock.json`, usa su runtime exacto. El CLI comprueba
la integridad en cada operación; no repitas doctor aparte. Antes de editar documentos
directamente, ejecuta `python <runtime>/scripts/lks_sdd.py doctor --root <proyecto>`.
Un fallo de integridad se reconcilia; no se evita usando otro runtime.
Sin runtime fijado usa el plugin instalado. La consulta no instala nada.
Para un formato antiguo, solo adopción/migración convierte; no hagas escritura dual.

Identifica la tarea y el plan que cubren la petición. Registra autoridad humana ya disponible para implement/consolidate/deliver solo en su alcance real; registrar una identidad no la autentica. Si falta definición, complétala antes de cambiar código; una decisión crítica no resuelta bloquea su porción. Ejecuta el trabajo autorizado hasta completarlo. Actualiza el único plan con decisiones, progreso, bloqueos, resultados y siguiente acción. Usa check para comandos locales declarados; reutiliza resultados únicamente si siguen coincidiendo todas las entradas pertinentes, configuración, herramienta, política y entorno. Importa resultados nativos con origen, ejecución y huella de entradas. Una caída de CI/VPN/credenciales bloquea esa comprobación, no el trabajo independiente. No generes wrappers ni artefactos de control por transición. Al cambiar chat recupera context y status. Ante conflicto conserva cambios ajenos, concilia el contenido y actualiza la base explícitamente. Nunca repitas automáticamente una acción externa tras una interrupción.

Markdown es canónico; el índice es derivado. Carga tarea + plan + capacidades
aplicables, no todo el histórico. Actualiza el plan existente durante la ejecución.
Respeta las instrucciones del proyecto y la autoridad ya expresada por la persona.
No inventes decisiones, autenticación, pruebas, aceptación o métricas de tokens.
En Copilot aplica el mismo núcleo; las pruebas de otro host no acreditan aceptación
conversacional de este. Si el usuario pide imágenes, usa las herramientas disponibles
con su autorización; no introduzcas APIs de pago implícitas.

Una subdivisión dentro del alcance conserva la autoridad del padre; no reautorices por cambiar enlaces administrativos. Mantén criterion_links para delegar criterios con cobertura verificable. No repitas pruebas por cambiar referencias de autoridad. Respeta los controles aplicables del proyecto y los bloqueos explícitos. Los indicadores administrativos antiguos no obligan a reconstruir controles retirados.
