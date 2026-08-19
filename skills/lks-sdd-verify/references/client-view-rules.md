# Reglas para vistas de cliente

Una vista de cliente es derivada y nunca sustituye los Markdown canónicos. Solo puede incluir fuentes con estado `confirmed` y clasificación `client` o `public`.

Debe excluir secretos, vulnerabilidades no tratadas, notas internas, inferencias no confirmadas, valoraciones personales, costes o contratos no autorizados y cualquier contenido de otro proyecto. El entregable registra proyecto, baseline, fuentes, versiones, audiencia, fecha y limitaciones, y requiere revisión humana antes de su entrega.

Use `python scripts/render_client_view.py <project-root> --source <ruta>... --output <ruta> --dry-run` para previsualizar. La escritura requiere `--apply --authorize --preview-hash <hash>` y nunca sobrescribe un archivo existente.
