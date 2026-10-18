# Preparar trabajo en una consulta

## Recorrido completo provisional

Esta porción de desarrollo combina V4-03, V4-04 y V4-05; no es una release 4.0
publicada. Mantiene las seis skills y las transiciones individuales vigentes.

V4-06 añade [continuación y resultados compuestos](WORK-OPERATIONS.md). La
preparación devuelve `operation_bases[task_uid]` para construir esas peticiones
sin reconstruir por separado snapshot, rama, inventario y sujeto. Es información
observada, no autoridad. Si falta comprobar el alcance de los cambios, la consulta
puede indicarlo antes de que el escritor ordinario lo compruebe físicamente;
ningún campo de la base permite eludir esa comprobación ni otras condiciones.

1. Identifique operador, tarea cubierta, autoridad y runtime fijado. Compruebe la
   integridad/capacidad por su inventario y `runtime-doctor`; el número 3.4.3 o el
   nombre de un ZIP no identifica por sí solo esta candidata de desarrollo.
2. Si el runtime incluye `work-prepare/1`, prepare la petición tipada de abajo con
   `parameters.action` igual a `start` o `resume`. Use el CLI de ese runtime con
   `--view operational --capture-dir EXTERNAL`. Lea `contract.sources`, adjuntos,
   impedimentos y porción que puede continuar. El contrato sigue siendo literal;
   no use `--output` para sustituir su lectura por una referencia de archivo.
3. Registre start/resume mediante la operación vigente antes del código. La
   preparación no escribe ni reserva autoridad: cada aplicación revalida sus
   guardas. Para una operación local ya autorizada use `ACCION --input DATOS --apply`;
   el núcleo prepara y aplica con sus guardas actuales en esa invocación. Si hace
   falta revisar o conservar primero el paquete, use `--output` fuera del consumidor
   y luego `apply --input PACKET --authorize PREVIEW_HASH` sobre esos bytes. Conserve la
   decisión/presentación exigida cuando la operación la requiera; una consulta no
   concede permiso ni evita una recepción o revisión pendiente.
   Si falla la salida o la captura, revise `effects`, el recibo y el estado actual
   antes de repetir: el cambio puede estar aplicado. Recupere la transacción exacta
   si corresponde; no repita la acción de negocio para reconstruir su salida.
   Para una transacción ya completada, la recuperación necesita el hash y su recibo:
   `recover --authorize HASH --receipt RECEIPT`. Sin recibo se busca una transacción
   pendiente; su ausencia no implica que la aplicación anterior no se realizara.
4. Cambie solo el alcance autorizado y ejecute la prueba real. Registre implement,
   evidence con artefacto/sujeto exactos, verify y close con las operaciones
   existentes. Compruebe el estado final. El cierre técnico no integra ni acepta
   funcionalmente; no registre esos hechos sin sus decisiones y evidencia propias.
5. Use la misma captura externa durante las operaciones, incluidas las aplicaciones.
   En un hito autorizado, `usage-record` con `actor` y `capture_dir` conserva los
   lotes completos mediante un paquete único; `--apply` conserva las guardas habituales
   sin pedir otra confirmación ni ejecutar una segunda llamada ya cubierta.
   `usage-report` con ese `capture_dir` muestra resumen y prompt. La captura no
   observa lecturas del host ni tokens facturados. Su propio registro/reporte no
   requiere generar una cadena infinita de registros diagnósticos.
   En estas llamadas diagnósticas lea la ventana mediante el campo JSON `capture_dir`;
   no añada `--capture-dir` apuntando a esa misma ventana para capturar su propio reporte.

Si falta la capacidad en un runtime anterior, use las consultas individuales
interventions, readiness y context, añadiendo status cuando sea necesario. No pase
opciones nuevas a un CLI que no las admite. Un inventario corrupto, código mezclado
o contrato caducado bloquea la porción; no se resuelve cambiando de transporte.
Una respuesta compuesta vigente evita consultas duplicadas, pero no controles,
pruebas o relecturas necesarias tras cambios o pérdida de contexto.

La captura tiene destino externo explícito y límites de volumen/recuperación:
[guía diagnóstica](DIAGNOSTIC-CAPTURE.md). La presentación conserva el modo
[compatible](CLI-PRESENTATION.md); ningún modo convierte `not-run` en superado.

## Petición y garantías de preparación

`v3 work-prepare` compone estado, intervenciones, readiness y contrato literal.
Es una consulta de método 3.1: no inicia tareas, registra decisiones, aplica paquetes
ni actualiza el runtime. Instalar un plugin tampoco actualiza el runtime fijado.
La capacidad y sus componentes deben coincidir con el runtime íntegro fijado; no
se deduce su presencia del número de versión del plugin o del esquema.

```text
python PINNED/scripts/lks_sdd.py v3 work-prepare ROOT --input request.json --view operational --json
```

```json
{
  "format": "lks-sdd-operation-request/1",
  "version": 1,
  "operation_id": "auto",
  "task": "TASK-UID",
  "actor": "MEMBER-UID",
  "parameters": {"action": "start", "reference": false}
}
```

Se rechazan campos/versiones/tipos desconocidos. `actor` ausente impide `ready`.
`action` admite las transiciones de tarea vigentes; su valor por defecto es `start`.
`reference: true` conserva la referencia contractual completa del selector actual.
`parameters.tasks` permite añadir hasta 19 tareas explícitas de la misma petición
para comprobar porciones independientes. No se buscan ni autorizan otras tareas.
Un alias ambiguo, raíz retirada o selección contradictoria bloquea la preparación.

`auto` solicita una correlación derivada del hash de raíz, tarea, actor y parámetros
normalizados. La respuesta devuelve `wp-<sha256>`. Reutilizar ese ID concreto con
otros parámetros se rechaza, incluso en otro proceso, sin crear un registro por
consulta. El ID no representa una aprobación ni congela la base; reconsultar puede
producir otras condiciones vigentes. No se cachean autorizaciones entre llamadas.

La respuesta `lks-sdd-operation-result/1` contiene estado, identidades, `basis`,
condiciones, estado del trabajo, preparación por tarea, intervenciones y `contract`.
El contrato aparece una sola vez con sus textos, metadatos, reglas globales, prosa
incierta, dependencias, adjuntos y exclusiones justificadas. No se reemplaza por hashes.
El recorrido de intervenciones tiene los límites/páginas existentes, expresamente
indicados; esas páginas no recortan el contrato ni acreditan tareas no seleccionadas.

`ready` significa preparación informativa suficiente para la transición solicitada;
`action-required` conserva condiciones pendientes y `partial` identifica expresamente
las tareas preparadas y bloqueadas. Un adjunto que exige observación sigue pendiente,
sin inferir que se ha visto por haber entregado sus bytes. Errores de identidad,
runtime, contrato o base producen `blocked`; un resultado vacío nunca resulta `ready`.
Los códigos son 0 (`ready`), 2 (bloqueo/intervención) y 3 (`partial`). `--apply` se
rechaza: la transición posterior usa sus presentaciones, preview y guardas habituales.

Una evaluación comparte el modelo inmutable y los cálculos vigentes; se presenta un
único recorrido de intervenciones. Antes de responder se contrastan pertenencia documental,
huellas, adjuntos, inventario de código, rama/HEAD, runtime, presencia/huella del índice derivado y vigencias. El índice puede faltar:
la fuente canónica sigue siendo Markdown y esta consulta no lo reconstruye. Si se
observa un cambio se retira toda porción preparada. La instantánea no es un bloqueo
distribuido ni una autorización reutilizable: antes de materializar hay que reevaluar
las condiciones y aplicar los guards frescos del mecanismo existente.

`evaluation_metrics` cuenta las entradas instrumentadas del núcleo: carga física de
modelo, ámbitos de cálculo, estado, readiness, hechos de tarea/petición, selector,
intervenciones, evaluador de transición y llamadas Git, más los límites propios de
vigencia. Los contadores incluyen cálculos internos repetidos; no son solo llamadas
CLI ni una medida completa de CPU. Su ámbito termina antes de preparar el sobre de
uso, captura y entrega del host. Estas fases se contabilizan aparte. No acreditan
tokens facturados, recepción del host ni ahorro total.

Sin captura ni output expresos, no se escriben archivos. `--output` conserva el
resultado completo fuera del consumidor. `--capture-dir` reutiliza la captura
externa V4-04: conserva también los literales/adjuntos anidados y el fixture
documental, con los mismos límites, procedencia y recuperación. La referencia del
CLI se vincula a `diagnostic_ref`; un fallo diagnóstico no cambia el resultado de
preparación. Una captura no acredita observación humana ni concede permiso.

Las [operaciones de continuación y resultados](WORK-OPERATIONS.md) requieren sus
capacidades compatibles en el runtime fijado. Esta preparación no acredita H2,
instalación, publicación ni aceptación conversacional de Codex/Copilot.

La revisión de V4-05 comprueba también transacciones pendientes antes y al terminar
el contraste físico. La declaración del runtime se captura antes de validar el
método y se vuelve a contrastar después de la última validación del runtime.
`basis.source_snapshot` corresponde al contrato final, incluidas las fuentes
históricas recuperadas durante la evaluación; `basis.checked_at` indica cuándo
terminó ese contraste. Estos límites no eliminan cambios posteriores ni la
obligación de reevaluar antes de aplicar.

En Windows, el helper Git conserva el recorrido anterior para raíces cortas. Para
un checkout largo usa alias 8.3 existentes y comprobados, un directorio de proceso
corto y los directorios Git/checkout explícitos; no mueve el proyecto ni crea enlaces.
Acepta `.git` como directorio o archivo de referencia y conserva el prefijo de los
consumidores anidados. La identidad y la propiedad del checkout y sus metadatos se
comprueban en cada invocación, antes de ejecutar Git. La propiedad de archivos no
identifica al operador funcional ni concede permisos LKS-SDD.

La compatibilidad larga requiere alias 8.3 disponibles y propiedad del usuario del
proceso. La comprobación es conservadora: no importa excepciones `safe.directory`
para aceptar otro propietario. Las condiciones Git `includeIf gitdir` se bloquean
explícitamente porque el alias puede cambiar su coincidencia. Se mantienen los
includes ordinarios y se resuelven las rutas relativas de exclusiones, atributos y
hooks frente al checkout original. Un fetch largo necesita URL absoluta configurada;
no se interpreta una URL relativa desde otro directorio. Si no puede conservarse
esa configuración, se requiere un checkout corto; no se omiten reglas ni se cambia
configuración global. Estas restricciones no afectan el recorrido corto anterior.

La lectura adicional de configuración para el recorrido largo se cuenta como otra
invocación Git; `git_commands` incluye sus lanzamientos internos y los que agotan su
espera. Las verificaciones de alias y propietario no son una medida de tokens ni de
coste total. Antes de materializar siguen siendo obligatorias las guardas vigentes.

Las variables de entorno que redirigen repositorio, árbol, índice, objetos o
configuración requieren una invocación limpia o una raíz corta para este recorrido.
No se aceptan rutas de configuración de entorno relativas. Un repositorio bare no
se convierte en checkout y core.worktree debe identificar el checkout solicitado.
Las referencias .git preservan los espacios significativos de la ruta; los errores
de configuración conservan el diagnóstico nativo acotado. La batería final separa
estos negativos de la consulta normal soportada.

## Continuidad al retomar una tarea

La respuesta incluye `continuity` (`lks-sdd-work-continuity/1`), una vista derivada
del mismo resultado comprobado: tareas seleccionadas, estado, fuentes, operador
aportado, paradas y siguiente acción. Sus referencias remiten al contrato literal,
los adjuntos y las intervenciones completos; no los sustituyen. El propietario
no se convierte en operador implícito y `authority_granted` siempre es `false`.
Una base bloqueada no publica una vista actual. Cambiar operador, fuente, runtime,
rama o evidencia exige preparar de nuevo; consultar no crea checkpoints ni escribe
registros canónicos. No se añade otro comando ni se hereda identidad del chat.
