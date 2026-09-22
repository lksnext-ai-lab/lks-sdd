# Continuidad SPEC → PLAN/TASK → implementación (método 2.1.0)

El schema Markdown sigue siendo `2.0`. La versión del método `2.1.0` activa estas
condiciones. Un consumidor fijado en `2.0.0` conserva el comportamiento previo hasta
una actualización explícita. El runtime anterior rechaza el método nuevo.

## Antes de modificar código

1. Identificar la petición material y el proyecto/branch/runtime fijado. Una
   consulta sigue siendo de solo lectura.
2. Reconciliar la petición con la SPEC y registrar o actualizar un `PCH-###`
   canónico (`change`, categoría `implementation-request`). Mantener una clave
   estable por punto material, su fuente resumida y sus referencias a requisitos,
   aceptación, tests, PLAN y TASK. No copiar todo un chat ni inventar decisiones.
3. Confirmar las obligaciones aplicables de la SPEC y comprobar que el PLAN las
   declara. Completar la asignación en TASKs con aceptación y tests. Una TASK ya
   existente puede servir; el simple enlace a la feature o a un requisito no
   cubre criterios nuevos. Una TASK cerrada y una EVID antigua se conservan; un
   nuevo alcance usa una TASK nueva. Una corrección del contrato original usa PROB
   y el flujo de corrección.
4. Ejecutar `decompose`, `readiness` y después AUTH/EXEC sobre la porción exacta.
   Un borrador de SPEC o PCH se puede guardar pero no habilita código. Cambios en
   prosa normativa común del PLAN, asignaciones o requisitos aplicables dejan
   obsoleta la autorización; progreso y tareas independientes no se convierten en
   autoridad nueva por sí solos.
   `v2 change <root> --id PCH-001 --json` consulta la correspondencia y los
   bloqueos sin escribir. `v2 decompose <root> --id PLAN-001 --json` y
   `v2 readiness <root> --task TASK-001 --json` usan el mismo análisis.
5. Antes de integrar, comparar el patch completo con una base de código y un
   contrato aprobado seleccionados independientemente del candidato.

El agente presenta el resultado solicitado, los documentos actualizados, las
TASKs reutilizadas o creadas, los huecos y la siguiente acción. Reutiliza
decisiones y autorizaciones vigentes; no pide repetir aprobaciones administrativas.
No selecciona una pila por conveniencia ni convierte desconocidos críticos en
decisiones.

## Registro PCH

El registro es un bloque Markdown canónico bajo
`docs/lks-sdd/00-control/changes/`, indexado en `.lks-sdd/project.json`.
Su `id` usa `PCH-###`, `state` es `draft`, `confirmed`, `cancelled` o
`superseded`, `nature` conserva la procedencia y `relations.affects` identifica
las features. `source_summary` resume el origen. `points` contiene objetos:

```json
{
  "key": "ACK",
  "summary": "Reconocer una solicitud válida",
  "requirements": ["FR-001"],
  "acceptance": ["AC-001"],
  "tests": ["TST-001"],
  "plans": ["PLAN-001"],
  "tasks": ["TASK-001"],
  "disposition": "planned"
}
```

Se permiten también `satisfied`, `deferred`, `excluded` y `unknown` como
disposiciones documentales; las tres primeras requieren motivo y `satisfied`
requiere IDs de evidencia. El análisis de ejecución exige `planned` para
las obligaciones implementables seleccionadas. `deferred` permite una porción
independiente solo bajo política `incremental-authorized`; el plan completo queda
`partial` y una dependencia diferida bloquea. `satisfied` y `excluded` quedan
visibles, pero no autorizan código por sí solos. Los enlaces son comprobaciones estructurales;
la confirmación humana de la interpretación sigue siendo necesaria.

El writer `v2 author` acepta varios documentos en una transacción revisable:
SPEC, PLAN, TASK y PCH. Mantiene UID y revisión; un cambio normativo incrementa
la revisión. El writer rechaza alterar el alcance normativo de una TASK activa o
cerrada. Use un cambio/replanificación documentados, no reescriba el cierre.

## Diagnóstico y actualización de método

```text
python <plugin-root>/scripts/lks_sdd.py v2 method-upgrade-diagnose <project-root> --json
python <plugin-root>/scripts/lks_sdd.py v2 method-upgrade <project-root> --json
python <plugin-root>/scripts/lks_sdd.py v2 method-upgrade <project-root> --apply --authorize <preview_hash> --json
```

El diagnóstico es de solo lectura. La actualización modifica únicamente el
índice de método en una transacción recuperable, conserva documentos, IDs,
historia y evidencia, y bloquea ejecuciones activas. Lista TASKs que necesitan
reconciliación PCH y autorizaciones antiguas; ninguna se interpreta como una
confirmación nueva. Después del corte, complete PCH/PLAN/TASK y autorice de nuevo
el trabajo afectado. No cambie `method_version` a mano.
En un proyecto con runtime fijado, actualice primero el paquete del proyecto por
su instalación revisada y después ejecute esta actualización de método. La
instalación personal de Codex o Copilot no cambia el lock de un consumidor.

## Guard de integración

```text
python <plugin-root>/scripts/lks_sdd.py v2 guard <candidate-root> \
  --base <trusted-code-base> --approved <approved-contract-root> \
  --strict --task TASK-001 --environment test --json
```

El modo `--strict` comprueba SPEC/PCH/PLAN/TASK, cobertura, huella, AUTH, EXEC,
baseline del EXEC y todo el diff de código frente a la base. Exige revisión
independiente exacta para cambios sensibles. Si varias TASKs seleccionadas
reclaman el mismo archivo, cada una debe declarar un patrón aplicable en
`joint_ownership`. La base de código, el contrato
aprobado y el candidato son tres raíces distintas. CI debe seleccionar el
verificador y las dos primeras desde referencias protegidas, y exigir el check
en la rama. Sin protección externa, el comando solo informa; no impide editar
archivos locales ni autentica actores o la semántica del negocio. El modo `guard`
sin `--strict` conserva su resultado estructural histórico.

## Continuidad entre tareas y hosts

Las instrucciones gestionadas de AGENTS.md y Copilot remiten al runtime fijado.
En una sesión nueva se leen índice, PCH, SPEC, PLAN/TASK, AUTH/EXEC/CKPT y diff
del checkout actual. El runtime fija datos y controles; el historial del chat no
es una fuente canónica. Una actualización del plugin personal no modifica por sí
sola el runtime fijado dentro de proyectos consumidores.
