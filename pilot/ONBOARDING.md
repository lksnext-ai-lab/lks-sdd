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
4. Elegir explícitamente la ruta greenfield, adopción o pila alternativa.
5. Recordar que la skill puede bloquear o proponer, pero no acredita la autoridad de la persona.

## Durante el piloto

- Registrar únicamente observaciones cerradas con aliases y métricas.
- No copiar conversaciones, código, documentos, URLs, capturas o nombres al almacén del piloto.
- Usar Issues solo para soporte saneado y el canal confidencial para seguridad.
- Detener la actividad ante exposición, escritura no autorizada, contaminación entre proyectos o pérdida de trazabilidad.

## Cierre

Agregar las observaciones, ejecutar el resumen y vincular una decisión go/no-go al reporte M4. Una decisión `go-conditioned` no equivale a stable; conserva acciones, responsables y fecha fuera del repositorio.
