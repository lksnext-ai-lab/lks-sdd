# Onboarding del piloto M5

## Antes de la sesión

- Confirmar alias `USR-*`, proyecto `PRJ-*`, ruta, entorno autorizado y ausencia de datos reales no permitidos.
- Verificar el ZIP de marketplace y su checksum contra `SHA256SUMS`.
- Confirmar soporte no sensible, canal confidencial, retención y rollback.
- Ejecutar `manage_pilot.py validate-config`; solo `ready` permite iniciar.

## Sesión inicial

1. Explicar SDD, el papel de los Markdown y la separación entre propuesta, decisión y autorización.
2. Instalar el bundle candidate de marketplace en el entorno Codex autorizado.
3. Abrir una tarea nueva y realizar primero una consulta de ayuda de solo lectura.
4. Elegir explícitamente la ruta greenfield, adopción o pila alternativa; confirmar el modelo de entrega y un perfil coherente por unidad desplegable.
5. Antes de materializar tareas, elegir `repository-only` o `jira-hybrid`. La segunda opción requiere un peer Rovo ya autorizado, preview exacto y un destino de prueba; no copie credenciales o payloads al repositorio.
6. Recordar que la skill puede bloquear o proponer, pero no acredita la autoridad de la persona; Jira `Done` tampoco acredita evidencia o cierre LKS-SDD.

## Durante el piloto

- Registrar únicamente observaciones cerradas con aliases y métricas; no copiar el contenido sustantivo de `TASK-###`, bloqueos o evidencias al almacén del piloto.
- No copiar conversaciones, código, documentos, URLs, sites, claves de issue, respuestas Rovo, capturas o nombres al almacén del piloto.
- Usar Issues solo para soporte saneado y el canal confidencial para seguridad.
- Detener la actividad ante exposición, escritura no autorizada, contaminación entre proyectos o pérdida de trazabilidad.

## Cierre

Agregar las observaciones, ejecutar el resumen y vincular una decisión go/no-go al reporte M4. Una decisión `go-conditioned` no equivale a stable; conserva acciones, responsables y fecha fuera del repositorio.
