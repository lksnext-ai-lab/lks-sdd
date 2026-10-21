# Preparar, distribuir e instalar LKS-SDD 5

La preparación no registra ni instala. `python scripts/prepare_v5_candidate.py`
crea paquetes deterministas en `dist/v5-prepared`, con hash del contenido actual,
manifest y estado explícito `local-preparation`. No equivale a una release estable
ligada a un commit limpio y aprobado.

Codex usa el bundle marketplace con `.agents/plugins/marketplace.json` y
`plugins/lks-sdd`. Copilot usa `lks-sdd-copilot-plugin-v5.0.0.zip`, con `plugin.json`
y las seis skills. El payload de proyecto fija el mismo núcleo por hash. Mantén la
identidad `lks-sdd`; no generes plugins duplicados para actualizarlo.

Publicación y registro en el marketplace requieren la autorización correspondiente.
La instalación se realiza mediante los mecanismos oficiales del host y se verifica
en una conversación nueva. No copies directamente archivos a las caches del host.
Una actualización del plugin no migra consumidores automáticamente.

Para un proyecto anterior sigue [la migración integral](V5.md): preview exacto,
revisión del contenido, aplicación explícita, validación e informe de conversión.
La migración es definitiva; una interrupción se reanuda hacia v5. Los paquetes preparados
pueden ensayarse en fixtures/copias controladas sin instalar en un proyecto activo.

El gate estable conserva la exigencia de checkout limpio, aprobación explícita de
versión, integridad, smoke funcional y rutas largas Windows. No uses un paquete
local sin commit como evidencia de aprobación estable o publicación.
