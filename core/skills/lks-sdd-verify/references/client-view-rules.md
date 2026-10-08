# Reglas para vistas de cliente

Una vista de cliente es derivada y nunca sustituye los Markdown canónicos. Solo puede incluir fuentes con estado `confirmed` y clasificación `client` o `public`.

Debe excluir secretos, vulnerabilidades no tratadas, notas internas, inferencias no confirmadas, valoraciones personales, costes o contratos no autorizados y cualquier contenido de otro proyecto. El entregable registra proyecto, baseline, fuentes, versiones, audiencia, fecha y limitaciones, y requiere revisión humana antes de su entrega.

Use `python "<plugin-root>/scripts/lks_sdd.py" client-view "<project-root>" --audience <audiencia> --purpose <propósito> --dry-run` para previsualizar. `<plugin-root>` es la instalación que contiene `.codex-plugin/plugin.json`, no el proyecto consumidor. El comando selecciona las fuentes elegibles desde el índice canónico, bloquea indicadores sensibles y no acepta una lista manual que eluda la clasificación. La escritura requiere `--apply --authorize --preview-hash <hash>` y nunca sobrescribe un archivo existente con contenido distinto.
