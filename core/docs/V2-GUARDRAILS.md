# Qué protege el guardrail v2 y qué no

| Control | Comprobación local | Límite |
|---|---|---|
| Obligaciones | Prosa, activos, relaciones, aplicabilidad y contexto literal | No demuestra que el texto exprese correctamente la necesidad humana |
| Autoridad | AUTH delimitada, vigente y ligada a la base | Actor/rol declarado no autentica identidad ni cargo |
| Implementación | Diff de archivos reales y rutas autorizadas, incluidos no versionados | El host puede editar directamente fuera de la CLI |
| Verificación | Gates, sujeto exacto, artefactos, scopes, caducidad y reservas | Un test incompleto sigue necesitando revisión semántica |
| Colaboración | Identidad, base, cambios compartidos y checkpoint | No hay lock distribuido ni resolución automática de conflicto semántico |
| Integración | Verificador ejecutado desde una referencia confiable | CI y permisos no se activan al instalar el plugin |

La documentación del candidato no puede elegir el verificador ni la base de
confianza. Fije ambos en el sistema de integración autorizado por la organización.
Una configuración de ejemplo no concede permisos ni ejecuta escritura externa.

Ejemplo local, solo lectura, con rutas elegidas por la persona responsable:

```powershell
python -B C:/RUNTIME_CONFIABLE/scripts/lks_sdd.py v2 guard C:/CAMBIO --base C:/BASE_APROBADA --task TASK-001 --json
```

El proceso devuelve código distinto de cero ante incumplimiento estructural. Si
no lo hay, devuelve `structurally-within-scope`, nunca aceptación semántica. La
política externa debe exigir además revisión del cambio y de las evidencias.
Si cambian pruebas, gates o dependencias, se bloquea hasta registrar `guard-review`
desde la base confiable, con `--incoming`, tareas y una solicitud con actor, tiempo
y motivo. La revisión se liga al diff exacto; no dispensa cambios de alcance ni
de obligaciones. Un recibo introducido únicamente en la rama candidata no sirve.
Mantenga independientes el ejecutor, los permisos, el artefacto candidato y la
aprobación del resultado. No cargue scripts de CI modificados por ese mismo cambio.

## Reanudación y defectos

Use `problem` para registrar un hallazgo, `correct` para reabrir el comportamiento
ya autorizado y `replan` si cambian las obligaciones. Este último conserva código,
cancela la ejecución antigua y revoca su autoridad. La nueva base necesita
aprobación. La evidencia histórica permanece; solo una observación nueva posterior
al defecto puede cerrar la corrección. Un rollback no convierte una dependencia
cancelada en terminada ni autoriza una funcionalidad distinta.

## Jira y sistemas externos

El modo repository-only no exige Jira. El modo híbrido declara proyecto, sitio,
alcance de reporting y coordinación. `tracking-project` es lectura; autorización
y resultado se registran en recibos ligados a una proyección exacta. Un resultado
incierto bloquea el reintento hasta reconciliación. Los hitos y transiciones
necesitan mapeo confirmado. El plugin no añade conectores ni infiere permiso remoto.
Un recibo durable impide desvincular o cambiar silenciosamente el sitio/proyecto.
La autorización de proyección exige un plan local suficiente, no un estado de Jira.
