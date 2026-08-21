# Contrato de implementación

## Entrada obligatoria

- índice y Markdown válidos;
- incremento `INC-###` confirmado y selección no vacía de `TASK-###` ready, con `specification_readiness` y `delivery_readiness` favorables;
- autorización explícita para implementar;
- gobierno de entrega confirmado, `PLAN-###`/`REL-###` aplicables y dependencias resueltas;
- `UNIT-###` y `BIND-###` seleccionados mediante ADR confirmada;
- `automation_support: supported` y lock exacto certificado para cada binding;
- baseline materializada y vigente cuando la ruta sea `adopt-existing`;
- checkout y cambios locales inventariados antes de editar.
- aplicabilidad de interfaz resuelta para incrementos 0.6+ y, cuando sea aplicable, contrato UX confirmado con prototipo visual validado o una no aplicabilidad visual motivada.

## Control de alcance

Codex traduce cada criterio de aceptación en cambios y pruebas concretos. No añade funcionalidades «útiles», refactorizaciones transversales, migraciones destructivas, integraciones o dependencias que no sean necesarias para el incremento. Un bloqueo localizado detiene solo la parte dependiente.

Cada driver materializa su scaffold bajo `unit_path` de forma aditiva y sin colisiones. Puede haber varios bindings en un sistema; los límites técnicos reproducibles no aportan comportamiento de negocio. Nombres, modelos, endpoints, mensajes, eventos y pantallas proceden de requisitos confirmados.

El resultado de readiness aporta `checked_files`, `active_contract_fingerprint`, `profile_lock`, `document_fingerprint` y la vista compatible `input_fingerprint`. El hash del preview se vincula a la huella del contrato activo; cualquier cambio posterior en un input Markdown, relación, lock o imagen confirmada de ese incremento invalida el apply. Las filas históricas permanecen en la huella documental para auditoría, pero no se convierten en inputs activos. Las imágenes no se duplican en `.lks-sdd/project.json`: se consumen desde sus enlaces canónicos y se verifican por contenido.

En el dry-run, cada `.lks-sdd/profiles/BIND-###.lock.json` puede no existir: el plan incluye la copia byte a byte del lock certificado y la huella activa ya contiene su SHA-256. Si un destino idéntico existe se conserva; si difiere, contiene `{}`, es un directorio o enlace, la preparación falla cerrada. El preview también fija inventario, revisión inicial, paths por unidad, fuentes, colisiones y archivos a crear. El apply exige autorización y hash vigente y revierte el conjunto si la validación posterior falla.

La preparación también incluye en el mismo preview las filas y fichas de las tareas seleccionadas. Un apply correcto cambia de forma atómica cada tarea `ready` a `in-progress`, eleva su progreso inicial sin fingir finalización, registra rama, revisión de inicio, fecha, actor e historial y después actualiza el índice. `--actor` y `--date` permiten declarar esos dos datos; si se omiten se usan `codex` y la fecha local. Si una ficha, el tablero o `project.json` cambian tras el preview, el apply se rechaza y debe repetirse.

Que `specification_readiness` sea favorable no basta si `delivery_readiness` o `automation_support` están bloqueados. Esta skill resuelve drivers por binding; no compone perfiles dinámicos, no sustituye una pila alternativa, no considera un candidato un defecto funcional y no selecciona un perfil automáticamente.

Para frontend, Codex implementa contra pantallas, flujos, interacciones, accesibilidad, dirección visual y `VIS-###` confirmados. Si la realidad técnica exige desviarse del contrato visual, detiene esa parte y solicita una decisión documentada; no convierte la desviación en aprobación implícita.

## Salida

- código y configuración acotados;
- tests con identificadores trazables;
- documentación actualizada quirúrgicamente;
- tablero y fichas TASK sincronizados, con estado, salud, progreso y bloqueos visibles;
- lista de comandos ejecutados y no ejecutados;
- desviaciones o cambios de alcance visibles;
- evidencia pendiente de verificación independiente.

La implementación no declara por sí misma conformidad, seguridad, accesibilidad, rendimiento ni preparación para entrega.

El índice conserva `implementation.status: in-progress` mientras quede trabajo seleccionado y usa `blocked` si no puede continuar. Registra `increment`, `task_ids`, `profile_bindings`, hashes de locks, rama, revisión inicial y paths modificados. Solo cuando código, documentación, pruebas y handoff estén completos puede cambiar a `completed`. El plan de verificación puede consultarse durante `in-progress`, pero ejecutar o registrar evidencia falla cerrado hasta `completed`. La transición TASK a `done` exige revisión verificada, build, digest de artefacto, entorno, gates y `EVID-###`; no se deduce de `implementation.status`.

La invocación portable resuelve el dispatcher desde la instalación del plugin, no desde el proyecto consumidor:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" implement "<project-root>" --increment INC-001 --task TASK-001 --dry-run
python "<plugin-root>/scripts/lks_sdd.py" implement "<project-root>" --increment INC-001 --task TASK-001 --date 2026-08-21 --actor codex --apply --authorize --preview-hash <hash>
python "<plugin-root>/scripts/lks_sdd.py" tasks "<project-root>" board
```
