# Troubleshooting

## La skill no se activa

Describa el objetivo o invoque de forma explícita la skill correspondiente: `$lks-sdd-help`, `$lks-sdd-define`, `$lks-sdd-adopt-existing`, `$lks-sdd-assess-readiness`, `$lks-sdd-implement` o `$lks-sdd-verify`. Compruebe que el plugin está disponible en Codex. La activación implícita ayuda, pero no es una garantía contractual.

## No se encuentra el proyecto

Confirme la raíz. Un proyecto ChatGPT no concede acceso directo a una carpeta; un proyecto local, CLI o IDE puede usar una raíz distinta. No inicialice hasta descartar que exista una aplicación previa.

## El índice es inválido

Ejecute la validación en modo de lectura y revise cada diagnóstico. El proyecto debe declarar schema 1.5/método 1.5.0; cualquier otro contrato se rechaza sin escritura. No reconstruya decisiones desde el índice ni interprete una actualización del runtime como autorización para modificar el proyecto.

## Readiness está bloqueado

Revise primero qué eje falla. `specification_readiness` comprueba alcance y aceptación; `planning_completeness`, cobertura total e integridad; `selected_slice_readiness`, tareas/dependencias; `automation_support`, perfiles y locks; autorización, las huellas exactas. Una especificación lista con plan parcial o automatización no soportada conserva esos hechos sin cambiar de pila. Un backlog independiente puede no bloquear la porción, pero sí mantener la release como parcial.

## TASK-001 está lista pero la release no

Es un resultado válido, no una contradicción. Revise `planning ... assess --json`: mostrará IDs sin propietario y `planning_completeness: partial`. Complete y confirme el plan como opción recomendada, o documente una ADR `incremental-authorized`; no presente la porción como release completa.

## Reanudar recomienda reconciliar o replanificar

`continuity resume` ha detectado una divergencia de checkout, archivo, huella o autorización. No repita trabajo ni marque la tarea terminada. Compare el checkpoint, reconcilie cambios observados o registre un `PCH-###` confirmado que enlace los `planning_fingerprint` anterior y actual, y recalcule cobertura. Un PCH propuesto no valida el cambio. Solo `continue-recommended` permite seguir directamente.

## El perfil aparece en el catálogo pero sigue `unsupported`

Es correcto cuando `lifecycle=candidate`, el lock no está validado o la composición exacta no está certificada. Consulte `automation_coverage` para distinguir si existe preparación, gates locales, interoperabilidad externa o evidencia de entrega pendiente. No lo resuma como soporte parcial y no cambie el proveedor confirmado: `API-FASTAPI-ENTRA-PG-OCI` no puede satisfacerse con el perfil Keycloak activo.

Estar catalogado o tener scaffold no basta. Compruebe lifecycle, `certification-evidence.json`, hashes de descriptor/driver/scaffold/motor, todos los gates de capacidad, gate de composición y lock consumidor del `BIND-###`. Un candidato permanece documentable y analizable, pero no implementable automáticamente.

## El tablero de tareas no valida

Ejecute `tasks <project-root> validate` o `board`. Compruebe que fila y ficha coinciden, estado/progreso/salud son coherentes, dependencias no forman ciclos y cada bloqueo tiene un `PROB-###` abierto. Use `tasks transition --preview` y luego el hash autorizado; no edite solo una de las dos representaciones.

## La trazabilidad pasa sin comprobar nada

Eso no es válido en 0.15.0: si existen requisitos aplicables y no se comprueba ninguno, el resultado señala alcance vacío. Use `--phase preimplementation` antes de implementar y `--phase verification` cuando deba existir evidencia ejecutada.

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

## Status muestra un bloqueo histórico o de producción

Use `status --view audit --json` para comprobar el estado del problema. Solo `active` aplicable puede aparecer en management; `resolved`, `superseded` e `historical` deben conservarse únicamente en audit. Un problema exclusivo de producción se agrupa como futuro cuando la operación actual es local. Corrija el lifecycle canónico; no borre el historial ni normalice otro proyecto.

## Una caché parece corrupta o el sujeto técnico es ambiguo

Desactive o elimine la caché derivada y recalcule. La caché nunca es autoridad. Si no puede demostrarse que todos los cambios pertenecen a rutas administrativas explícitamente excluidas, invalide la reutilización y repita los gates afectados.
