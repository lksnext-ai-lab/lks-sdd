# Revisar una entrega o acción externa

Muestre contenido y resultado, destino y audiencia, cambios/envío previstos,
comprobaciones y límites, alcance del permiso y pendientes. La persona debe poder
revisar el contenido exacto y el destinatario antes de autorizar el efecto externo.
Respete la clasificación interna o de cliente; preparar una vista no autoriza enviarla.

`prepare-delivery` prepara información del resultado aceptado y no publica el PR.
No repita una aceptación vigente ni convierta ese resumen en otra firma SDD.
Publicar, enviar, instalar, hacer commit/push o abrir un PR requiere permiso de la
sesión que cubra contenido y destino; reutilice el existente sin ampliarlo.

`decision-view` puede explicar `external-action` o `client-view`, pero no ejecuta
la acción. Para Jira distinga modo, proyecto/destino, contenido propuesto, permiso
de escritura y resultado observado. No invente un conector, respuesta remota ni una
sincronización. Si el runtime solo conserva una ruta histórica, declare su límite.
Una aprobación de entrega no acredita despliegue, CI/CD ni aceptación remota de PR.
