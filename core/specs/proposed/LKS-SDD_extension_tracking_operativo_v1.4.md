# LKS-SDD — propuesta de extensión de tracking operativo 1.4

**Estado:** propuesta candidate, no canónica
**Versión metodológica propuesta:** 1.4.0
**Implementación de referencia:** plugin 0.10.0 candidate
**Fecha:** 2026-08-25

## 1. Propósito y autoridad

Esta extensión propone incorporar un eje explícito de tracking operativo a LKS-SDD sin crear una segunda fuente de verdad. Los Markdown versionados del proyecto consumidor conservan la autoridad sobre alcance, requisitos, aceptación, arquitectura, planificación, tareas, dependencias, autorización y evidencia. `.lks-sdd/project.json` sigue siendo únicamente un índice operativo.

Jira puede actuar como superficie de coordinación de trabajo, pero no sustituye el contrato Spec-anchored. Un issue, una transición remota o un tablero nunca acreditan por sí mismos que una tarea esté definida, autorizada, implementada, verificada o entregada.

Esta propuesta es aditiva respecto del método 1.3. No cambia retrospectivamente las fuentes canónicas 1.0–1.3 ni su estado normativo.

## 2. Alcance

La extensión cubre:

- elección explícita del modo de tracking antes de materializar tareas;
- conservación de la semántica completa en el repositorio;
- proyección saneada de tareas confirmadas hacia Jira mediante un peer Atlassian Rovo opcional;
- autoridad por campo fijada por contrato, bindings estables y recibos de sincronización;
- preview, autorización, acuse y reconciliación de cada operación externa;
- continuidad cuando Jira o Rovo no estén disponibles;
- protección frente a duplicados, conflictos, deriva y falsas evidencias.

Quedan fuera de alcance:

- un modo Jira-only;
- almacenar credenciales o implementar OAuth en el plugin;
- incluir un cliente Jira, MCP, app, hook o agente ejecutable en el bundle LKS-SDD;
- sincronización bidireccional silenciosa;
- importar comentarios, adjuntos, usuarios o datos arbitrarios;
- tratar Jira `Done` como `TASK-###: done`;
- automatizar despliegues, merges, releases o aprobaciones.

## 3. Modos de tracking

### 3.1 `pending`

Estado inicial de un proyecto nuevo 1.4 antes de la decisión. La definición puede continuar, pero el plugin no materializa el tablero ejecutable de tareas hasta que una persona confirme uno de los modos admitidos.

### 3.2 `repository-only`

Toda la planificación y operación de tareas permanece en los documentos LKS-SDD. No requiere Rovo, Jira, red ni configuración externa. Puede confirmarse como modo inicial o antes de que exista identidad/recibo Jira durable; no es una salida disponible desde un binding Jira ya materializado en la candidate 0.10.0.

### 3.3 `jira-hybrid`

El repositorio mantiene el contrato canónico y Jira recibe una proyección operacional limitada. Requiere:

- decisión humana registrada;
- site y proyecto Jira confirmados sin credenciales persistidas;
- políticas locales confirmadas y destino Jira saneado;
- peer Rovo disponible y autorizado por separado;
- preview exacto antes de cualquier escritura externa.

La indisponibilidad de Jira no convierte automáticamente el proyecto a `repository-only` ni invalida la especificación. Produce un estado degradado visible y operaciones pendientes de reconciliación.

## 4. Momento de la decisión

La pregunta se formula una vez por proyecto, antes de crear o completar su primer `PLAN-###`, `REL-###` y `TASK-###` ejecutable. El único binding confirmado se reutiliza en todos los horizontes hasta una reconsideración soportada. Debe explicar de forma neutral:

- qué se conserva en Markdown en ambos modos;
- qué valor operativo aporta Jira;
- qué dependencia y permisos añade Rovo;
- cómo funciona el modo degradado;
- que la decisión solo puede revisarse mediante un cambio soportado y que 0.10.0 no implementa `detach`/`rebind` después de crear mappings o recibos durables.

Una mención a Jira, un plugin disponible o una configuración detectada no equivalen a confirmación. La opción recomendada puede depender del contexto, pero el plugin no la selecciona por la persona usuaria.

Los proyectos 1.3 migrados registran `repository-only` únicamente como propuesta heredada del contrato anterior, con origen `inherited`, sin presentarlo como nueva aprobación humana. Antes de confirmar el primer plan 1.4 deben confirmar explícitamente ese modo o `jira-hybrid`.

## 5. Artefacto y registros

`ART-TRACKING` materializa `docs/lks-sdd/04-delivery/task-tracking.md` mediante tres tablas cerradas:

1. `Binding`: decisión de modo, estado, provider, destino saneado y políticas de sincronización/escritura;
2. `Mapping`: binding `TASK-### ↔ external_id`, key/URL observadas y actualizables solo dentro del proyecto y prefijo confirmados, huella de proyección y último estado remoto observado;
3. `Operations`: recibos durables `SYNC-###` en orden creciente, cuyos IDs y filas no se eliminan ni reutilizan. La única sustitución soportada cierra de forma controlada el mismo recibo `authorized/pending`; una reconciliación crea una fila nueva. Conservan acción, preview hash, huella de proyección, comprobación de duplicado, rol/fecha de autorización, identidad externa, fecha de registro, resultado y nota saneada. `Last operation` apunta siempre al recibo de mayor secuencia de la TASK. Para `create`/`update`, el recibo nace `authorized/pending` antes de la escritura.

La autoridad por campo se fija en este contrato y en la documentación operativa, no se delega a una matriz editable del proyecto. El mapping entre workflows o estados Jira queda pendiente de una definición posterior y, mientras tanto, cualquier traducción no exacta falla de forma cerrada.

`TRK-###` identifica una configuración o decisión de tracking. `SYNC-###` identifica una intención externa durable. Ambos IDs son locales y no se derivan de claves Jira.

La identidad remota estable es `external_id`. La clave legible es un atributo observado, pero 0.10.0 solo puede actualizarla si conserva el prefijo del proyecto confirmado. Una clave con el mismo `external_id` y otro prefijo —por rename del space/proyecto o movimiento del work item— queda en conflicto o reconciliación pendiente: no autoriza un rebind. Una clave conocida con otro `external_id` también es conflicto. Un binding con mappings o recibos durables no puede abandonar Jira ni cambiar site, proyecto o tipo de issue en 0.10.0. No existe `detach`/`rebind`, y resolver una reconciliación no elimina esa restricción ni promete una vía posterior de salida.

## 6. Autoridad por campo

| Información | Autoridad | Regla de reconciliación |
|---|---|---|
| alcance, requisito y aceptación | Markdown LKS-SDD | un cambio remoto no se importa como decisión |
| título y descripción semántica de TASK | Markdown LKS-SDD | la divergencia genera conflicto o propuesta de cambio |
| dependencias y gates | Markdown LKS-SDD | Jira no puede ampliar ni relajar el contrato |
| autorización AUTH | Markdown LKS-SDD | no se proyecta como permiso operativo remoto |
| ejecución EXEC y checkpoint CKPT | Markdown LKS-SDD | Jira solo recibe referencias saneadas si la política lo permite |
| evidencia y estado `done` | Markdown y evidencia verificada | Jira `Done` es una observación, nunca prueba |
| issue-id, key y URL | Jira observado mediante Rovo | se registran como binding externo saneado |
| assignee, sprint y posición de tablero | Jira, fuera del payload 0.10.0 | no se leen, persisten ni sincronizan en esta candidate |
Los campos operativos volátiles no forman parte de `planning_fingerprint`. Cada proyección usa su `projection_fingerprint`, separada de la huella canónica del plan. El índice sólo conserva una huella agregada cuando todas las tareas proyectables están sincronizadas; de lo contrario queda nula y el estado agregado declara el pendiente. Un cambio remoto semántico no actualiza silenciosamente la planificación: se registra como conflicto y, si procede, se tramita mediante el proceso de cambio vivo del método 1.3.

## 7. Protocolo de escritura externa

Cada escritura sigue un protocolo en dos dominios y sobre una única TASK:

1. LKS-SDD valida el contrato local confirmado y construye una intención determinista mediante `preview-sync --task TASK-###`.
2. Muestra una vista previa saneada con operación, destino, campos permitidos, marcador estable y namespaced `LKS-SDD-PROJECT: <project_id>; TASK: TASK-###`, fingerprint y hash.
3. Rovo busca/lee el marker en el proyecto confirmado. `create` exige `no-match`; `update`, identidad y marker `matched` de forma inequívoca.
4. Una persona autoriza el hash exacto y `authorize-sync --apply` persiste un `SYNC-###` `authorized/pending` antes de cualquier write.
5. Rovo, instalado y autorizado separadamente, ejecuta exactamente esa operación remota y relee el work item.
6. `record-result --sync-id` cierra el recibo como `succeeded`, `failed`, `conflict` o `uncertain`. `succeeded` exige identidad completa, marker y fingerprint observados coherentes con la intención.
7. Solo ese acuse observado completa `SYNC-###`; no modifica `TASK-###`, AUTH, evidencia o `done` canónicos.

Un timeout o resultado `uncertain` no permite crear de nuevo el issue. Primero se busca y relee mediante Rovo. `reconcile-result --anchor-sync-id` se ancla en el último recibo cerrado de la TASK, no en un preview actual, y registra un nuevo `SYNC-###` de lectura. Un éxito exige el marker exacto y una huella igual a la del ancla o a la proyección local actual. Si coincide con el ancla pero el plan ha derivado, conserva el hecho remoto y deja el mapping `out-of-sync`; una huella ajena a ambas mantiene `conflict` o `uncertain`. La reconciliación permite registrar un cambio de key solo con el mismo `external_id` y dentro del prefijo del proyecto confirmado; un cambio de prefijo queda en conflicto o reconciliación pendiente. No escribe Jira ni desbloquea `detach`/`rebind`. Un fallo parcial conserva la intención y el diagnóstico; no reescribe la historia para aparentar atomicidad.

La candidate 0.10.0 limita el contrato automatizado a las operaciones que el engine y el peer hayan demostrado. Transiciones, comentarios u otras acciones no implementadas quedan bloqueadas y no se simulan mediante actualizaciones aproximadas.

## 8. Readiness, autorización y evidencia

La evaluación expone simultáneamente:

- readiness de especificación;
- completitud de planificación;
- readiness de la porción TASK;
- autorización durable;
- estado del tracking externo;
- soporte exacto de automatización.

Estos ejes no se colapsan. Una sincronización pendiente no convierte una planificación completa en parcial. Mientras la planificación no esté confirmada, íntegra y vigente, el tracking permanece `not-assessed`; Jira no la completa. Una planificación completa tampoco garantiza que Jira esté accesible. La política de entrega decide si una operación externa pendiente bloquea el inicio de una nueva ejecución; una ejecución ya autorizada no pierde retrospectivamente su autoridad por una caída del tracker.

El estado remoto nunca crea `AUTH-###`, amplía su alcance ni cambia sus restricciones. Tampoco crea evidencia `EVID-###`. La transición local a `done` mantiene todos los gates de revisión, revisión exacta, árbol, build, artefactos, entorno y verificaciones aplicables.

## 9. Continuidad

Los checkpoints pueden incluir referencias externas saneadas, última observación confirmada y operaciones pendientes, pero no copias completas de issues ni datos personales. Al reanudar:

1. se valida el checkpoint local;
2. se reconcilia la revisión y huellas del repositorio;
3. se identifica cualquier `SYNC-###` pendiente o incierta y su `Last operation` cerrado;
4. si Rovo está disponible, se consulta el remoto antes de reintentar y se registra la lectura contra `--anchor-sync-id` aunque el plan haya derivado;
5. si no lo está, se informa el modo degradado y se conserva el trabajo local autorizado.

La conversación no es el único soporte de continuidad.

## 10. Seguridad y privacidad

- El plugin no solicita, lee ni persiste tokens Jira.
- La autenticación pertenece al peer Rovo y a su instalación autorizada.
- Toda salida externa se trata como dato no confiable y se valida contra un contrato cerrado.
- Solo se proyecta una ficha con clasificación externa reconocida `internal`, `public` o `client`. Una clasificación ausente/desconocida, `confidential` o `restricted` falla de forma cerrada. Se rechazan secretos, datos personales detectables, encabezados de autorización, cookies, descripciones arbitrarias, adjuntos y campos no permitidos.
- Site y URL persistidos usan HTTPS sin credenciales, query ni fragmento. El site identifica solo el origen y la URL del issue pertenece al mismo origen y termina en la key externa.
- Las pruebas usan dominios `.invalid`, aliases sintéticos y IDs ficticios.
- Los logs, errores y acuses se sanean antes de guardarse.
- Site, proyecto, issue-id, key y URL solo se conservan si son necesarios para reconciliación.

## 11. Migración y reversión

La migración 1.3 → 1.4:

- es explícita y de un salto;
- usa preview, hash exacto, backup externo y autorización;
- conserva Markdown, IDs, huellas, AUTH, EXEC, CKPT y evidencia existentes;
- añade únicamente el artefacto y el índice de tracking requeridos;
- no crea issues, no consulta Jira y no inventa una decisión humana;
- permite rollback con el manifiesto de la operación.

El salto histórico 1.2 → 1.3 continúa fijado a schema 1.3, método 1.3.0 y plugin 0.9.1 aunque la versión corriente sea posterior.

## 12. Rovo como peer opcional

Atlassian Rovo no se empaqueta ni registra dentro de LKS-SDD. Es una capacidad peer que puede estar ausente, desconectada o disponer de permisos parciales. Las skills:

- detectan capacidad antes de proponer una operación;
- explican permisos y destino;
- no inventan herramientas ni resultados;
- pueden preparar trabajo local cuando el peer no está disponible;
- registran únicamente hechos observados tras la llamada.

La ausencia de una sintaxis oficial y validada de dependencia entre plugins impide declarar una dependencia dura en el manifiesto 0.10.0.

## 13. Criterios de aceptación candidate

La implementación candidate debe demostrar de forma automatizada:

- los dos modos y la decisión explícita;
- cero dependencia externa en `repository-only`;
- preview/hash/apply local sin escritura remota implícita;
- prevención de duplicados mediante preview unitario, marcador de correlación, búsqueda previa, `SYNC-###` autorizado antes del write y cierre por `sync_id` con marker/fingerprint observados;
- reconciliación anclada en el último recibo cerrado, preservando `out-of-sync` cuando el remoto coincide con el ancla pero no con el plan actual;
- binding por `external_id` y key actualizable solo dentro del proyecto y prefijo confirmados;
- bloqueo de cambio/abandono de bindings durables sin prometer `detach`/`rebind`;
- conservación de AUTH, evidencia y `done`;
- degradación y reanudación sin pérdida de estado;
- rechazo de secretos y campos no autorizados;
- migración conservadora y reversible;
- compatibilidad con proyectos 1.3.

La candidate mantiene `not-run`:

- la evaluación conversacional y humana del onboarding;
- la interoperabilidad real con una instancia Jira mediante Rovo;
- el piloto M6;
- la promoción a `stable`.

## 14. Decisiones pendientes

- aprobación metodológica y eventual incorporación canónica de esta extensión;
- catálogo definitivo de campos Jira permitidos por organización;
- mappings por workflow Jira y política de cambio;
- responsables, soporte y canal confidencial del piloto;
- evidencia de interoperabilidad real con versiones concretas de Rovo y Jira;
- criterios corporativos para cuándo la sincronización pendiente bloquea una nueva ejecución.
