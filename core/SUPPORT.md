# Soporte de LKS-SDD

## Canal no sensible

Las incidencias técnicas, dudas de uso y feedback del piloto se registran en [GitHub Issues](https://github.com/lksnext-ai-lab/lks-sdd/issues). Use las plantillas disponibles y no incluya código de cliente, nombres de personas, URLs internas, capturas, prompts, secretos, credenciales ni datos personales.

El canal existe para la fase candidate; todavía no ofrece SLA ni sustituye los canales corporativos de soporte que se designen antes de stable.

Para incidencias del modo `jira-hybrid`, indique únicamente la versión del plugin, la operación local (`configure`, `preview-sync`, `preview-event`, autorización, resultado o reconciliación), el tipo de resultado y un código sintético. No copie site, proyecto, issue key, URL interna, payload, marcador real, fingerprint, comentario, respuesta Rovo, `SYNC-###` real ni identidad de usuario. La disponibilidad, conexión y permisos de Atlassian Rovo pertenecen a ese peer y no convierten a LKS-SDD en soporte de la cuenta Jira.

## Seguridad y privacidad

No comunique vulnerabilidades o incidentes sensibles mediante una issue ordinaria. Siga `SECURITY.md` y el canal confidencial aportado en la configuración externa del piloto. Mientras ese canal y su responsable no estén configurados, el piloto permanece bloqueado para arrancar.

## Información útil y permitida

- versión del plugin y sistema operativo;
- skill o script afectado;
- resultado esperado y resultado observado, sin contenido de cliente;
- código de error y pasos reproducibles con datos sintéticos;
- referencia saneada a evidencia controlada.

## Límites candidate 0.15.0

- La interoperabilidad real Rovo/Jira permanece `not-run` hasta un piloto autorizado.
- No existe soporte Jira-only ni sincronización bidireccional silenciosa.
- Una TASK `confidential` o `restricted`, un secreto o dato personal detectable y una URL con credenciales, query o fragmento se bloquean antes de persistir o proyectar; no reduzca la clasificación ni sanee ocultando el riesgo para obtener soporte.
- Un binding con mappings o recibos durables no se puede abandonar ni cambiar de destino: 0.15.0 no ofrece `detach`/`rebind`, incluso después de reconciliar una operación.
- Los perfiles Microsoft Entra siguen candidate: `automation_coverage` no equivale a soporte, la interoperabilidad real permanece `not-run` y Keycloak no es un fallback equivalente.
- Los perfiles OIDC simulados solo son soportados en entornos no productivos permitidos; `external_interoperability` es `not-applicable` y producción falla de forma cerrada.
- Comentarios y transiciones solo se ejecutan para hitos soportados, con preview y recibos; si Rovo no expone la capacidad exacta, fallan de forma cerrada.
- No existe SLA ni soporte de producción.
