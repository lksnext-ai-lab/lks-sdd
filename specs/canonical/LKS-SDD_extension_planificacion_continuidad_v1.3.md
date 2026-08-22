# LKS-SDD · Extensión de planificación y continuidad 1.3

## Estado y alcance

Esta extensión candidata incorpora al contrato LKS-SDD la completitud de planificación, la autorización delimitada de implementación y la continuidad entre sesiones. Es aditiva respecto de 1.2 y no convierte una propuesta, una estimación ni una observación en decisión humana.

Los Markdown versionados de `docs/lks-sdd/` siguen siendo la fuente de verdad. `.lks-sdd/project.json` solo indexa punteros, fingerprints y ejecuciones observadas; nunca sustituye la definición, la cobertura, el historial o la evidencia.

## Estados ortogonales

Toda evaluación debe mostrar simultáneamente:

1. readiness de especificación del incremento;
2. soporte de arquitectura y automatización;
3. completitud de planificación del objetivo (`not-started`, `partial`, `complete` o `stale`);
4. integridad de planificación (`valid` o `invalid`);
5. readiness de la porción TASK seleccionada;
6. estado observado de implementación;
7. estado observado de verificación;
8. estado observado de entrega o despliegue.

Un estado `ready` de una tarea no implica que el incremento o la release estén completamente planificados. Las respuestas orientadas a acción no usan un `ready` global ambiguo: indican, por ejemplo, `planning-required`, `ready-for-implementation-authorization`, `resume-required`, `reconciliation-required` o `replanning-required`.

## Cierre de especificación y handoff

Cuando la especificación del alcance evaluado queda cerrada, la experiencia debe emitir automáticamente un resumen de transición que contenga:

- síntesis comprensible de alcance, requisitos, aceptación, decisiones, arquitectura, UX aplicable, datos, seguridad, privacidad, integraciones, calidad, gobierno y puntos abiertos;
- estado separado de cada fase;
- trabajo de planificación pendiente, trazado hasta IDs concretos cuando exista;
- siguiente paso recomendado;
- decisión humana requerida.

Si la planificación no está completa, la recomendación por defecto para `bounded-release` es completar y validar la planificación antes de implementar. La planificación incremental solo habilita una porción cuando una persona confirma y registra expresamente esa política y sus límites.

## Completitud de planificación

Un objetivo de release o incremento está `complete` únicamente cuando se cumplen todas estas condiciones:

- el objetivo, los incrementos incluidos y la política de planificación están declarados;
- todo elemento activo del contrato está asignado a una tarea primaria y, si corresponde, a contribuyentes delimitados;
- todos los requisitos, criterios de aceptación y pruebas activas aparecen en la definición ejecutable de su tarea primaria;
- todas las tareas del objetivo tienen objetivo, alcance incluido y excluido, requisitos, aceptación, pruebas, unidad, binding, capacidades, gates, dependencias, riesgos, rol responsable, entrada a revisión, definición de terminado y evidencia requerida;
- release, tablero, detalles y mapa de cobertura son consistentes;
- el grafo de dependencias existe, no contiene ciclos y no trata una dependencia cancelada como resuelta;
- están identificadas las raíces ejecutables, las posibilidades de paralelización y el punto de verificación conjunta;
- no hay huecos, propiedad primaria duplicada ni solapamientos contradictorios;
- los fingerprints confirmados de especificación y planificación coinciden con el contenido actual y la confirmación conserva el rol responsable sin inferir una persona o autoridad.

`partial` identifica los huecos concretos. `stale` indica que una huella confirmada dejó de corresponder al contrato actual. `invalid` se reserva para incoherencias estructurales o lógicas. No se inventan duración, esfuerzo, velocidad, capacidad, fechas o camino crítico: sin duraciones confirmadas solo se muestran el orden topológico, las fronteras paralelas y las cadenas estructurales más largas.

Una tarea puede permanecer en `backlog` y estar suficientemente definida. El estado de workflow y la suficiencia de definición son dimensiones distintas.

## Autorización de implementación

La autorización humana se registra en el contrato canónico con alcance, rol autorizante, fecha, decisión, tareas y fingerprints de especificación y planificación. Persiste al pausar y reanudar la misma ejecución mientras coincidan alcance y fingerprints. Una divergencia del repositorio, un cambio de contrato o una replanificación afectada la invalida y exige reconciliar o volver a autorizar.

Para `complete-before-implementation`, una autorización no es válida si la planificación del objetivo no está `complete`. Para `incremental-authorized`, puede delimitar tareas concretas `ready`, pero el resumen debe conservar visible que la planificación integral continúa `partial`.

## Ejecución, checkpoints y reanudación

Las tareas usan `backlog → ready → in-progress → in-review → done`, con `blocked` y `cancelled` explícitos. `done` exige aceptación y gates realmente superados, revisión, artefacto y evidencia atribuibles. Código escrito no equivale a código verificado.

Una ejecución autorizada crea y mantiene checkpoints versionables bajo `docs/lks-sdd/04-delivery/checkpoints/`. Cada checkpoint registra como mínimo:

- tarea o tareas activas, estado, rama, revisión de inicio y última revisión observada;
- fingerprints de especificación y planificación y autorización aplicable;
- archivos modificados y, cuando se declaren, sus hashes;
- entregables terminados y parciales;
- aceptación cubierta y pendiente;
- pruebas y gates pasados, fallidos o no ejecutados;
- evidencias, problemas, bloqueos y decisiones pendientes;
- siguiente acción segura y otras tareas independientes.

El plugin actualiza el checkpoint al iniciar, pausar, bloquear, enviar a revisión o terminar una tarea y cuando Codex interrumpe una ejecución autorizada. Esa actualización documental no autoriza commits, pushes, publicación ni despliegue.

Al reanudar se valida la correspondencia entre checkpoint, revisión, árbol, contrato y fingerprints. El resultado recomienda continuar, reconciliar o replanificar, sin marcar como terminado trabajo parcial ni repetir evidencia ya válida.

## Cambios y reapertura

Los cambios se registran sin reescribir historia. Un cambio identifica contrato y tareas afectados, conserva como huellas anterior y actual los `planning_fingerprint` exactos antes y después del cambio y recalcula cobertura y dependencias. Un PCH propuesto no altera el impacto confirmado ni permite reconfirmar el plan; para aplicarlo debe existir un PCH `confirmed` que enlace esas dos huellas exactas y una decisión humana. Solo se reabre una tarea terminada cuando falla el contrato original o su definición de terminado. Un alcance nuevo crea una nueva tarea; no se disfraza como incumplimiento retrospectivo.

## Compatibilidad y migración

Los proyectos 1.0, 1.1 y 1.2 siguen siendo legibles. En 1.2 la cobertura se deriva conservadoramente de los campos existentes y nunca se presume completa por ausencia de datos. La migración 1.2 → 1.3 es explícita, con preview, backup, hash, autorización y rollback. Añade el mapa de planificación y las tablas de ejecución con valores pendientes; no inventa tareas, cobertura, autorización, avance, evidencia ni checkpoints.

## Resúmenes obligatorios

Se emite un resumen orientado a acción al cerrar especificación, confirmar planificación, solicitar autorización, iniciar, terminar o bloquear una tarea, pausar, reanudar, completar una release y antes de verificar o promover. Cada resumen responde: dónde estamos, qué terminó, qué está en curso, qué falta, qué está bloqueado, cuál es el siguiente paso y qué decisión humana se necesita.
