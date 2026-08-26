# Contrato de planificación híbrida con Jira Cloud

Aplica este contrato solo cuando el usuario haya elegido `jira-hybrid`. El Markdown versionado del proyecto sigue siendo autoritativo y Jira es una proyección operativa. No ofrezcas ni materialices un modo Jira-only.

## Elección y autoridad

Antes de crear el primer plan de tareas del proyecto, confirma una de estas opciones:

1. `repository-only`.
2. `jira-hybrid` con Atlassian Rovo como compañero opcional.
3. Pausar sin decidir.

Registra la decisión mediante un `ADR-###` confirmado que nombre expresamente `tracking` y el modo exacto `repository-only` o `jira-hybrid`; una ADR confirmada sobre arquitectura, entrega u otro asunto no sirve como sustituto semántico. Configura el único binding `TRK-###` de proyecto en `ART-TRACKING` con preview, `mutation_hash` y apply autorizado. Reutiliza esa elección en todos los horizontes del proyecto hasta que la persona pida reconsiderarla explícitamente; no crees un binding por plan, release o incremento. `.lks-sdd/project.json` indexa ese contrato; no debe recibir credenciales ni convertirse en la fuente sustantiva del binding.

La elección de `jira-hybrid` no autoriza llamadas externas. Pide autorización específica antes del preflight de solo lectura y otra autorización después de mostrar cada preview de escritura.

## Preflight de solo lectura

Usa exclusivamente capacidades procedentes de Atlassian Rovo. Si su procedencia es ambigua o falta una capacidad necesaria, detente; no uses una herramienta parecida de otro plugin.

Con autorización de lectura vigente:

1. Obtén los sitios Atlassian accesibles y exige elección humana si hay más de uno.
2. Obtén los proyectos Jira visibles y exige elección humana del proyecto.
3. Lee los tipos de work item disponibles para ese proyecto.
4. Lee los campos de creación requeridos para el tipo propuesto.
5. Limita esta fase a metadatos del destino. La búsqueda del marker de una TASK se hace después de confirmar el plan y generar su preview exacto, inmediatamente antes de `authorize-sync`.

No selecciones automáticamente el primer sitio, proyecto, tipo, campo, usuario, estado o enlace. No consultes identidad ni busques account IDs salvo que el usuario haya pedido expresamente una asignación concreta.

Presenta como binding propuesto: sitio, clave de proyecto, tipo de work item, `Sync policy=required-before-execution` y `Write policy=preview-and-confirm`. Confírmalo localmente mediante el hash exacto antes de cualquier escritura Jira. Si el proyecto necesita varios tipos o una correspondencia de workflow que el binding 1.4 no expresa, déjalo como limitación y no inventes una configuración paralela. Desde que exista cualquier external ID o recibo `SYNC-###`, 0.10.0 bloquea abandonar Jira o cambiar site, proyecto o tipo; no ofrece `detach`/`rebind`, tampoco después de reconciliar.

La clave de proyecto debe coincidir con Jira Cloud: al menos 2 caracteres, inicio en mayúscula y solo mayúsculas o números. No normalices silenciosamente una entrada inválida y confirma mediante Rovo que existe y es accesible. Si Jira renombra el space/proyecto o mueve el work item y cambia el prefijo de su key, 0.10.0 lo trata como conflicto o reconciliación pendiente; no puede actualizar el binding ni aceptar ese rekey como si siguiera en el proyecto confirmado.

## Materialización local primero

Materializa y valida primero `PLAN-###`, `REL-###`, `ART-PLANNING`, `ART-TRACKING`, el tablero y cada detalle `TASK-###`. Confirma los fingerprints de planificación con el workflow local vigente. Mientras el plan no esté confirmado, íntegro y vigente, el tracking queda `not-assessed` y `preview-sync` no genera una intención; Jira no suple esa confirmación. La confirmación del plan y la configuración del binding no autorizan Jira.

La proyección Jira puede gobernar inicialmente solo:

- resumen con prefijo estable `[TASK-###]`;
- descripción con objetivo, alcance, aceptación, dependencias y ruta relativa del detalle canónico;
- marcador estable y namespaced `LKS-SDD-PROJECT: <project_id>; TASK: TASK-###` y fingerprint de proyección;
- contexto de plan, release, incremento, unidad y binding de perfil;
- sitio, proyecto y tipo del destino confirmado.

Assignee, sprint, prioridad, estimación, fechas, componentes y campos personalizados quedan fuera del payload inicial. Incorporarlos exigiría una evolución explícita del contrato, no una escritura ad hoc. Solo se proyecta una ficha con clasificación reconocida `internal`, `public` o `client`; una clasificación ausente/desconocida, `confidential` o `restricted` falla de forma cerrada. El motor también bloquea secretos y datos personales detectables; no rebajes la clasificación ni copies contenido para eludir el guard. Site y URL deben ser HTTPS sin credenciales, query ni fragmento.

Registra únicamente recibos saneados en `ART-TRACKING`. La tabla Mapping admite `unlinked`, `pending`, `synced`, `out-of-sync`, `conflict`, `failed` o `reconciliation-required`; la tabla Operations usa `SYNC-###` y conserva acción, preview hash y resultado. No edites esas tablas a mano cuando el comando local de tracking pueda aplicar el resultado de forma atómica.

## Preview y autorización externa

Ejecuta `preview-sync` con exactamente una `--task`. Antes de escribir, presenta esa única operación exacta y acotada:

- `create`, `update`, `noop` o `blocked-reconciliation` para esa TASK;
- `TASK-###` y destino Jira;
- campos y valores que se escribirán;
- fingerprint local de origen;
- operaciones omitidas y limitaciones;
- `preview_hash` exacto, dirección `outbound-only` y `external_write_authorized=false`;
- una escritura real máxima, excluyendo `noop`;
- ausencia de borrados y archivados.

Después del preview, busca el marker exacto mediante Rovo en el proyecto confirmado. `create` exige cero coincidencias y `authorize-sync --duplicate-check no-match`; `update` exige que la identidad mapeada y el marker formen una coincidencia inequívoca y `--duplicate-check matched`. Una coincidencia múltiple, destino distinto o identidad ambigua bloquea. Una modificación del plan, binding, mapping o payload invalida el hash y exige empezar de nuevo.

`authorize-sync --task TASK-### --preview-hash <hash> --authorized-by-role <rol> --authorized-on <fecha> --duplicate-check <resultado> --apply` persiste primero un `SYNC-###` `authorized/pending`. Solo su respuesta con `external_write_authorized=true` autoriza después una creación o actualización Rovo. No escribas antes de que ese recibo durable exista.

## Ejecución recuperable

Procesa una tarea cada vez:

1. Reutiliza un mapping confirmado cuando exista y valida que apunte al destino elegido.
2. Genera el preview de una TASK, busca/lee el marker mediante Rovo y persiste `authorize-sync` como se indica arriba.
3. Ejecuta únicamente la operación `create` o `update` de ese `SYNC-###`; no continúes con otra TASK.
4. Relee el work item y comprueba mismo site/proyecto, `external_id`, key/URL, marker `LKS-SDD-PROJECT: <project_id>; TASK: TASK-###` y fingerprint de proyección.
5. Cierra el recibo existente con `record-result --sync-id SYNC-### --result <resultado> --date <fecha> --apply`. Para `succeeded`, incluye el `--observed-correlation-marker` namespaced exacto del preview, `--observed-projection-fingerprint <sha256>`, ID, key y URL observados.
6. Conserva las dependencias en Markdown y en la descripción proyectada. La creación de enlaces Jira queda fuera de la proyección determinista inicial y no se ejecuta sin soporte posterior de preview y recibo.

Si una creación o actualización puede haber ocurrido pero el resultado es incierto, no la repitas a ciegas. Cierra el `sync_id` como `uncertain` y realiza únicamente una lectura Rovo autorizada. `reconcile-result --anchor-sync-id <Last-operation-cerrado>` registra esa observación como un nuevo `SYNC-###` de acción `reconcile`; puede resolver `uncertain`/`conflict` o un cambio de key si conserva el mismo `external_id`, el prefijo del proyecto confirmado y el marker. No exige que el plan siga proyectable: una huella igual al ancla pero distinta de la proyección actual deja el mapping `out-of-sync`. No ejecuta un write ni habilita cambiar/abandonar el binding. Ante cualquier ambigüedad, conserva `conflict` o `uncertain`.

No borres, archives, reasignes, añadas worklogs ni sobrescribas campos no gobernados. Un fallo o recibo Jira no altera la validez del plan Markdown ya confirmado ni cambia el estado canónico de la TASK.
