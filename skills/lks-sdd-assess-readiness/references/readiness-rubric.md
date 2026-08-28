# Rúbrica de readiness por incremento

La evaluación no reduce el proyecto a un `ready` ambiguo. Explica simultáneamente `specification_readiness`, `automation_support`, `planning_completeness`, `selected_slice_readiness`, autorización, implementación, verificación y entrega. Su acción superior es `specification-required`, `planning-required`, `slice-required`, `automation-required`, `ready-for-implementation-authorization`, `ready-to-implement` o un bloqueo explicado. No usa puntuaciones opacas, no selecciona una pila y no autoriza implementación.

## Preparación de la especificación

`specification_readiness` evalúa si el incremento está suficientemente definido para un handoff. Sus condiciones bloqueantes son:

- El índice o un documento canónico obligatorio es inválido.
- El incremento no existe, no está `confirmed` o no declara alcance incluido y excluido.
- Un requisito vinculado no está confirmado o carece de criterio de aceptación observable.
- Falta una decisión técnica crítica o permanece como `proposal`.
- Datos, identidad, seguridad, privacidad o integraciones relevantes siguen indeterminados para el incremento; una no aplicabilidad necesita motivo.
- No hay estrategia o pruebas previstas vinculadas.
- Existe contradicción o punto abierto marcado como bloqueante para el incremento.
- La cadena requisito → criterio → decisión o no aplicabilidad motivada → incremento → prueba no es completa en fase `preimplementation`. `EVID-###` solo se exige al comprobar la fase `verification`.
- Una relación activa apunta a una fila inexistente, rechazada, sustituida o retirada. El historial se conserva para auditoría, pero no forma parte del contrato activo del incremento.
- En un incremento 0.6+, la aplicabilidad de interfaz está `pending`, falta su fila en `ART-INCREMENTS` o una no aplicabilidad carece de motivo.
- Un incremento con interfaz aplicable no tiene al menos una pantalla, un flujo y una dirección visual confirmados. Cada pantalla necesita entrada/salida, jerarquía, acciones secundarias, permisos/variantes, responsive, accesibilidad, contenido pendiente y los seis estados contractuales; cada flujo enlaza sus pantallas y la aceptación.
- Un cambio visual aplicable no tiene un `VIS-###` confirmado y validado por una persona. El asset debe ser PNG/JPG/JPEG local bajo `docs/lks-sdd/03-solution/ui-prototypes/`, con firma real y SHA-256 exacto; una propuesta no satisface readiness.
- `Visual mode` permanece `pending`, un cambio `new`/`material-change` no enlaza un prototipo confirmado, o `none` no justifica la ausencia real de cambio visual.
- `Visual mode=reuse` no enlaza un `VIS-###` confirmado, su archivo/hash/validación humana/ADR no son íntegros, la ADR no se comparte con la dirección y decisiones del incremento, o falta delimitar qué se reutiliza.
- En ruta `adopt-existing`, la baseline no está `materialized` o está `stale`.

## Pendientes no bloqueantes

Un punto explícitamente no bloqueante, con impacto y alcance independientes, puede producir `ready-with-non-blocking-pending`. La ausencia de evidencia no se presume no bloqueante.

## Preparación de entrega y porción seleccionada

En esquemas 1.2, 1.3 y 1.4, la preparación de la porción bloquea G2 si falta alguno de estos elementos:

- un `CHG-###` vigente y `confirmed` que cierre modelo de entrega, versionado, ramas o su no aplicabilidad, promoción, despliegue, recuperación y trigger de revisión;
- al menos un `ENV-###` confirmado cuando el gobierno está confirmado;
- un `PLAN-###` confirmado o activo cuyo modelo coincida con el gobierno;
- una `REL-###` planned/active/frozen para cada tarea seleccionada;
- una selección no vacía de `TASK-###` en `ready`, con ficha ejecutable completa, dependencias resueltas, owner, aceptación y gates;
- una `UNIT-###` y un `BIND-###` confirmados por tarea.

El gate evalúa la selección solicitada o, si no se indica, las tareas activas o `ready`. El backlog independiente no bloquea esa selección, pero sí puede demostrar que la release aún no está completamente planificada. El tablero y las fichas deben concordar; ciclos, referencias ausentes, progreso incoherente o un bloqueo sin problema abierto invalidan el contrato. Una dependencia TASK solo está resuelta en `done`; `cancelled` exige reconciliar el grafo.

## Completitud e integridad de planificación

`planning_completeness` usa `not-started`, `partial`, `complete` y `stale`. `planning_integrity` usa `valid` o `invalid`. Una selección TASK puede estar `ready` mientras la planificación total permanece `partial`; ambos hechos deben mostrarse juntos.

Una planificación 1.3 o 1.4 es `complete` únicamente cuando:

- el objetivo, incremento, release y política están declarados;
- cada elemento activo aplicable del incremento tiene una única tarea primaria y, si procede, contribuyentes delimitados;
- requisitos, criterios de aceptación y pruebas aparecen también en la definición ejecutable responsable;
- todas las tareas registradas tienen objetivo, alcance incluido/excluido, entregables, unidad/binding, gates, dependencias, paralelización, riesgos/bloqueos, rol, revisión, DoD y evidencia exigida;
- release, tablero, fichas y mapa de cobertura concuerdan;
- el grafo no contiene ciclos, referencias ausentes ni dependencias canceladas tratadas como resueltas;
- existen raíces ejecutables, fronteras paralelas y una responsabilidad explícita de integración/verificación conjunta;
- no existen huecos ni dos propietarios primarios contradictorios;
- las huellas de especificación y planificación confirmadas coinciden con el contenido actual.

La salida enumera IDs sin propietario, tareas incompletas, solapamientos, dependencias, orden topológico y fronteras. Sin duraciones confirmadas informa `critical_path: undetermined`; no inventa esfuerzo, fechas, velocidad o capacidad. En 1.2 la cobertura puede derivarse para diagnóstico, pero nunca se confirma como completa sin migrar a 1.3 y materializar el mapa.

## Autorización

Una planificación `complete` permite pedir autorización, no implementar. `ready-for-implementation-authorization` exige además una porción `ready` y automatización soportada. `ready-to-implement` solo aparece cuando un `AUTH-###` autorizado coincide exactamente en incremento, release, tareas, política y ambas huellas vigentes. Un cambio aplicable vuelve esa autorización `stale`; la evaluación no la actualiza ni la sustituye.

La política recomendada es `complete-before-implementation`. Una planificación `partial` solo puede autorizar una porción si existe una ADR humana `incremental-authorized`; el resumen debe seguir mostrando que la release completa no está planificada.

## Soporte de automatización

`automation_support` informa únicamente `selection-required`, `supported` o `unsupported` por cada `BIND-###`. `automation_coverage` añade un diagnóstico ortogonal por binding: `catalog_fit`, preparación, implementación, verificación local, interoperabilidad externa, evidencia de entrega, capabilities declaradas/bloqueadas, bloqueos de cualificación y siguiente paso. No existe el estado `partially-supported`: un perfil candidate continúa `unsupported` aunque tenga scaffold y gates definidos. La especificación puede quedar `ready` mientras la automatización está bloqueada; esto describe hechos distintos. El estado combinado permanece `blocked` hasta que todos los bindings de la selección sean soportados, pero la skill no cambia la conclusión funcional ni selecciona otro perfil.

`supported` exige una composición cerrada `active`: entrada de catálogo, descriptor, driver genérico de preparación/verificación, scaffold, lock 2.0, capabilities y gates exactos, gate de composición passed y `certification-evidence.json` ligado por hash al motor y a todos esos bytes. Declaraciones como `validated: true`, una familia, una lista de tecnologías o un lock sin certificación no bastan. Los perfiles `candidate` se pueden definir y analizar, pero bloquean implementación automática.

Antes de `prepare`, readiness valida cada lock empaquetado. La ausencia del lock consumidor `.lks-sdd/profiles/BIND-###.lock.json` es válida porque `prepare` planifica su copia; si ya existe, debe ser un archivo regular idéntico byte a byte. `{}`, divergencia, directorio o enlace bloquean. La huella activa incorpora todos los hashes esperados y la composición exacta, de modo que su materialización posterior no cambia el contrato aprobado.

## Revisión semántica

El validador comprueba estructura, estados, identificadores y referencias. La skill debe revisar además claridad, atomicidad, verificabilidad, riesgos, contradicciones y suficiencia contextual. Debe explicar cada bloqueo y el cambio o decisión mínima que lo resolvería, sin editar durante la evaluación.

`checked_files`, `active_contract_fingerprint`, `profile_lock` y `document_fingerprint` son parte del resultado contractual. La huella activa representa únicamente los Markdown, relaciones, lock exacto y assets confirmados que alimentan el incremento; la huella documental también detecta cambios históricos. Un cambio de input activo invalida el preview de implementación. Una edición exclusivamente histórica sigue siendo visible para auditoría sin convertirse por ello en alcance implementable.

Readiness 0.15 evalúa únicamente proyectos schema 1.5/método 1.5.0. Un contrato anterior se informa como incompatible y no se migra ni reescribe durante la evaluación.
