# Jira Cloud como proyección operativa opcional

Usa esta referencia únicamente para explicar el modo Jira de LKS-SDD. Esta skill no inspecciona herramientas, conexiones, cuentas, proyectos ni work items y no modifica el repositorio.

## Modelo soportado

LKS-SDD admite dos opciones de planificación:

- `repository-only`: `PLAN-###`, `REL-###`, `TASK-###` y el resto del contrato viven únicamente en Markdown versionado.
- `jira-hybrid`: el mismo Markdown sigue siendo autoritativo y Jira Cloud ofrece una proyección operativa de las tareas.

Jira-only no está soportado. Jira no sustituye alcance, aceptación, cobertura, dependencias, fingerprints, autorización, ejecuciones, checkpoints ni evidencia.

Dentro de `jira-hybrid` hay dos experiencias: `projection-only` mantiene las fichas de tarea; `milestone-reporting` añade comentarios de hitos y transiciones opcionales. El gate de coordinación puede ser `advisory` —opción recomendada para no bloquear el trabajo local— o `required-before-execution`. El reporting se puede pausar y reanudar sin abandonar el binding ni perder recibos.

Atlassian Rovo es un plugin compañero opcional e independiente. LKS-SDD no lo instala, conecta, autentica ni empaqueta. Su disponibilidad, autenticación, permisos de organización y permisos Jira pueden variar por usuario y superficie.

## Separación de decisiones

Explica siempre estas decisiones por separado:

1. Elegir `repository-only` o `jira-hybrid`.
2. Autorizar un preflight de solo lectura en Atlassian.
3. Confirmar sitio, proyecto, tipos, campos y correspondencia de workflow.
4. Confirmar el plan Markdown y sus fingerprints.
5. Revisar una proyección Jira concreta.
6. Autorizar una búsqueda/lectura Rovo del marker y la identidad.
7. Para un hito, revisar el comentario y la transición opcional como una unidad.
8. Persistir un `SYNC-###` separado por operación antes de autorizar la escritura.
9. Ejecutar y releer cada operación Jira.
10. Cerrar cada recibo por `sync_id` con el marker o status ID observado.

Ninguna de ellas implica automáticamente la siguiente. Una autorización de implementación o verificación tampoco autoriza una escritura Jira.

## Diagnóstico explicable

Si Jira no puede usarse, distingue sin inventar:

- plugin compañero no disponible;
- conexión o inicio de sesión pendiente;
- sitio o proyecto no visible;
- permiso de lectura, búsqueda o escritura insuficiente;
- metadatos de tipo, campo, enlace o transición incompatibles;
- mapping ausente o ambiguo;
- proyección parcial o resultado externo incierto;
- cambio remoto que requiere reconciliación.

Antes de que exista un mapping o recibo durable, ofrece confirmar `repository-only`, completar la configuración del compañero por separado o pausar. Si ya existe cualquier identidad externa o `SYNC-###`, 0.14.1 obliga a conservar el binding Jira o pausar: no ofrece `detach`/`rebind`, y una reconciliación posterior no habilita cambiar de modo o destino. No cambies de modo silenciosamente.

## Límites

- Soporte inicial: Jira Cloud mediante Atlassian Rovo.
- No prometas Jira Data Center, sincronización bidireccional, borrado, archivado, bulk transaccional, worklogs ni asignación automática.
- `preview-event` admite hitos significativos y nunca ruido de archivo, comando o chat. Una confirmación autoriza el preview, pero comentario y transición conservan recibos separados.
- Una transición requiere mapping local confirmado por Jira status ID y un transition ID observado en una lectura fresca; los nombres no bastan.
- Un estado Jira no demuestra readiness, implementación, verificación ni aprobación.
- Un plan no confirmado deja el tracking `not-assessed`; Jira no puede convertirlo en plan vigente.
- `preview-sync` procesa una sola `--task`. `create` exige una búsqueda del marker con `no-match`; `update`, una identidad/marker `matched`. `authorize-sync` persiste el recibo antes del write; `record-result` lo cierra por `--sync-id` y un éxito exige marker y fingerprint observados.
- `reconcile-result --anchor-sync-id <Last-operation-cerrado>` registra una lectura Rovo autorizada para resolver `uncertain`, `conflict` o un cambio de key con el mismo `external_id` y prefijo confirmado, incluso si el plan actual ha derivado. Si la huella observada coincide con el ancla pero no con el plan actual, queda `out-of-sync`; no ejecuta escrituras ni libera el binding.
- Un recibo remoto nunca modifica por sí solo `TASK-###`, AUTH, evidencia o `done` canónicos.
- No expongas identificadores internos de conexión, credenciales, tokens, account IDs ni datos de otros proyectos.
- No proyectes fichas `confidential`/`restricted`, secretos o datos personales detectables. Conserva solo URLs HTTPS sin credenciales, query ni fragmento.
- El contrato 1.5 puede validar offline `ART-TRACKING`, políticas `RPT-###`, workflow mappings, fingerprints y recibos `SYNC-###`; no presentes esa validación local como prueba de conexión, permisos o estado vivo de Jira.
