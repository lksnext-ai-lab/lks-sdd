# Troubleshooting

## La skill no se activa

Describa el objetivo o invoque de forma explícita la skill correspondiente: `$lks-sdd-help`, `$lks-sdd-define`, `$lks-sdd-adopt-existing`, `$lks-sdd-assess-readiness`, `$lks-sdd-implement` o `$lks-sdd-verify`. Compruebe que el plugin está disponible en Codex. La activación implícita ayuda, pero no es una garantía contractual.

## No se encuentra el proyecto

Confirme la raíz. Un proyecto ChatGPT no concede acceso directo a una carpeta; un proyecto local, CLI o IDE puede usar una raíz distinta. No inicialice hasta descartar que exista una aplicación previa.

## El índice es inválido

Ejecute la validación en modo de lectura y revise cada diagnóstico. Un proyecto 1.2 aplica gobierno, arquitectura, planes y tareas estrictos; 1.0/1.1 se validan en compatibilidad. No reconstruya decisiones desde el índice ni use la actualización como autorización de migración.

## Readiness está bloqueado

Revise primero qué eje falla. `specification_readiness` comprueba alcance y aceptación; `delivery_readiness`, gobierno/plan/release/tareas/dependencias; `automation_support`, cada perfil exacto, certificación y lock. Una especificación lista con automatización no soportada no debe cambiar de pila automáticamente. Un backlog independiente no bloquea la selección TASK.

## El perfil aparece en el catálogo pero sigue `unsupported`

Estar catalogado o tener scaffold no basta. Compruebe lifecycle, `certification-evidence.json`, hashes de descriptor/driver/scaffold/motor, todos los gates de capacidad, gate de composición y lock consumidor del `BIND-###`. Un candidato permanece documentable y analizable, pero no implementable automáticamente.

## El tablero de tareas no valida

Ejecute `tasks <project-root> validate` o `board`. Compruebe que fila y ficha coinciden, estado/progreso/salud son coherentes, dependencias no forman ciclos y cada bloqueo tiene un `PROB-###` abierto. Use `tasks transition --preview` y luego el hash autorizado; no edite solo una de las dos representaciones.

## La migración devuelve `human_review_required`

No repita el mismo comando con `--apply`: la operación se rechazará siempre antes de crear el backup o escribir. Resuelva cada entrada mostrada en los Markdown canónicos 1.0, valide el proyecto y repita el dry-run hasta obtener una lista vacía. Revisar o aceptar la lista no sustituye esa corrección explícita. La `Identity` agregada es distinta: el migrador la convierte en tres filas `pending` con motivo y no la muestra en `human_review_required`; tras aplicar, resuelva identidad, seguridad y privacidad en 1.1 para desbloquear readiness.

## La trazabilidad pasa sin comprobar nada

Eso no es válido en 0.8.0: si existen requisitos aplicables y no se comprueba ninguno, el resultado señala alcance vacío. Use `--phase preimplementation` antes de implementar y `--phase verification` cuando deba existir evidencia ejecutada.

## La ejecución de verificación se bloquea aunque el plan existe

Un plan puede anticipar checks mientras la implementación del mismo incremento está `in-progress`. Ejecutarlos o registrar `EVID-###` requiere que `.lks-sdd/project.json` conserve ese incremento, marque `implementation.status` como `completed`, mantenga las mismas `task_ids` y `profile_bindings`, y que cada lock consumidor coincida con la certificación exacta del perfil ligado. Corrija el registro de implementación; no fuerce los checks ni cree evidencia manual para eludir la puerta.

## El comando busca scripts en el proyecto consumidor

Resuelva `<plugin-root>` como la instalación que contiene `.codex-plugin/plugin.json` y ejecute `python "<plugin-root>/scripts/lks_sdd.py" <comando> "<project-root>"`. No copie una ruta personal ni presuponga que la raíz actual es la del plugin.

## Se detecta una aplicación existente

Detenga la ruta `new` y continúe con `lks-sdd-adopt-existing`. El primer inventario debe ser estático y de solo lectura; no materialice hasta confirmar alcance, cobertura, reconciliación, baseline vigente y preview.

## Falta una capacidad de Work o Codex

Revise [realidad del producto](product-reality.md), permisos y configuración. Declare la limitación y use un fallback conservador: fuentes adjuntas, Markdown exportados o una raíz local confirmada. No atribuya el problema a la persona usuaria.

## Se actualizó el plugin pero la tarea sigue mostrando la versión anterior

Publicar una release, refrescar un marketplace y cargar una instalación activa son estados distintos. Confirme la versión resuelta por la superficie instalada y, después de una actualización autorizada, reinicie Codex y abra una tarea nueva para recargar metadatos y skills. Esto no migra los proyectos consumidores.
