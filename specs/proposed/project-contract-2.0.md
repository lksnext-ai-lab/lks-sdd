# Contrato documental LKS-SDD 2.0

Estado: diseño autorizado para implementación el 2026-09-18. No es aprobación
de release, certificación de tecnología, aceptación humana ni autorización remota.
Versiones independientes: línea de plugin 2.0 (candidate actual 2.0.0-rc.1),
contrato 2.0, método 2.0.0.
Los contratos históricos de specs/canonical/ se conservan íntegros.

## Fuentes y formato

Los Markdown versionados y los artefactos de evidencia son la autoridad.
`.lks-sdd/project.json` contiene versión, identidad de proyecto y rutas; no decide
el estado de un requisito ni de una tarea. Las consultas no escriben este índice.
Las vistas derivadas no pueden definir elementos ni otorgar aprobaciones.

La migración soportada `1.5/1.5.0 → 2.0/2.0.0` es un corte explícito y
preview-bound. El agente calcula un inventario cerrado, asigna cada fuente a
`transformed`, `archived`, `preserved-out-of-scope` o `blocked`, valida un árbol
v2 prospectivo y archiva los bytes originales. La única decisión humana
obligatoria es autorizar el hash exacto del preview completo; esa autorización
no crea decisiones de negocio ni reactiva autoridad histórica.

Un proyecto migrado solo alcanza `migration-complete` cuando el recibo y su
manifiesto son íntegros, no quedan rutas activas 1.5 y los escritores legacy
están bloqueados. Los elementos `legacy`, `unknown` y `conflict` son no
normativos por defecto. La continuidad se calcula por TASK con estado
`continuation-ready`; la semántica pendiente bloquea solo el alcance que la
necesita. El runtime 1.x conservado para recuperación es histórico y no gobierna
trabajo futuro.

Cada documento activo declara `schema_version: 2.0` y `artifact_type` en su
frontmatter. Contiene bloques de prosa delimitados por un comentario JSON de una
línea `<!-- lks-sdd: {...} -->` y `<!-- /lks-sdd -->`. El comentario es metadato,
no instrucciones ejecutables. El cuerpo es Markdown normal con un ancla explícita
`<a id="fr-001"></a>` y encabezado con identificador y título. Las tablas y listas
son opcionales según el contenido. No hay un segundo JSON con los requisitos.

Cada bloque tiene `id`, `uid` (UUID inmutable), `kind`, `title`, `state`, `revision`
entera positiva, `nature` y `relations`. `nature` distingue fact, inference,
proposal, decision y unknown. Los identificadores legibles no se reciclan; una
colisión de id o uid se rechaza hasta reconciliación explícita. Los bloques
normativos no se anidan. Todo el texto del documento, también fuera de bloques,
es contexto y material de huella cuando el documento es aplicable.

Tipos: project, feature, group, requirement, acceptance, rule, constraint, task,
increment, plan, release, test, decision, interface, binding, environment,
authorization, execution, checkpoint, problem, change, applicability, legacy,
receipt y visual.
Una feature conserva identidad al renombrarse o evolucionar. Su carpeta es
`02-specification/features/FTR-###-nombre/`; no se anidan físicamente features.
La documentación común está en `02-specification/shared/` y los flujos
transversales en `flows/`. Los bloques principales 00-control a 06-operation
tienen número; detalles y activos solo se crean cuando existen.

La ficha de tarea, en `04-delivery/tasks/`, es la única definición del trabajo.
Los tableros y el catálogo son vistas calculadas. Una tarea puede contribuir a
varias features; un padre no transmite aprobación, requisitos ni estado.

## Relaciones, evolución e historia

`relations` es un mapa de relación a lista de IDs. Las relaciones admitidas son
parent, uses, depends_on, requirements, acceptance, tests, contributes_to,
implements, modifies, replaces, splits, merges, increment, release, plan,
bindings, interfaces, environments, decision, authorizes, execution, verifies,
sources y affects. La pertenencia y las dependencias no admiten ciclos. Solo una
relación parent. Ni uses ni parent autorizan ejecución.

Los enlaces relativos incluyen ID, texto y ancla: `[FR-001 · límite de impresión]
(../FTR-001-pedidos/specification.md#fr-001)` (sin salto en el enlace real).
Se valida archivo, ancla e identidad; los recursos externos no se ejecutan ni
se descargan al validar. Los vínculos inversos son derivados.

Una sustitución declara `replacement` con mode partial/total, residual_scope,
effective (versión, entorno, flags o fecha) y estado propuesto/aprobado/efectivo.
Una sustitución futura no retira la definición actual. División/fusión preserva
IDs y correspondencias. Estado de definición, implementación, verificación,
despliegue y salud se muestran por separado. Git o snapshots locales conservan
contenido recuperable; un hash sin contenido no prueba historia consultable.

## Suficiencia y gobierno

Consulta: docs-first/docs-only/compare. No exige adoptar, completar el catálogo,
IDs, tareas ni conocer toda la aplicación. Código solo con petición expresa o
carencia documental concreta de implementación/impacto y contexto vigente.
No inferir decisiones de negocio del código. Mostrar límites y fuentes.

Ejecución: recuperar literal y completo el contrato del ámbito, sus
contribuyentes, dependencias, consumidores y obligaciones compartidas. La
aplicabilidad de UX, datos, identidad, seguridad, privacidad, interfaces, calidad
y operación es applicable/not-applicable/unknown, con razón para descartes.
Un unknown crítico bloquea el ámbito; no obliga a documentar todo el legado.
Los anexos no se crean vacíos para satisfacer una cuota.

Un plan enumera alcance y política complete/incremental-authorized. Cada tarea
declara entregables (rutas internas), aceptación, pruebas y controles. Solo done
resuelve una dependencia. La suficiencia de una porción no acredita plan completo.
Las AUTH se vinculan a tareas, huella normativa, política, entorno, fecha, plazo
y actor/rol declarados. Revocadas/caducadas/obsoletas no autorizan; una vigente
se reutiliza sin repreguntar. Estos datos no autentican identidad organizativa.

La ejecución conserva base de documentos y código; contrasta cambios reales,
incluidos pruebas, gates, dependencias y configuración. Cambiar aceptación o
controles no convierte un fallo en conformidad: requiere revisión y autorización
de la nueva base. Los cambios ajenos se inventarían antes de escribir.

La evidencia es inmutable y enlaza tareas, revisión, build, artefacto, entorno y
scopes. Se mantienen component, contract, composition, user-flow, persistence y
visual; ninguno sustituye otro. La evidencia histórica y la salud actual son
distintas. Una corrección exige nueva evidencia para resolver el problema.
Reutilizar solo passed determinista, mismos inputs/motor/sujeto/aprobación y TTL
vigente, conservando observed_at. Diagnóstico no ejecuta gates; cada etapa exige
sus controles. Reservas no dispensan controles críticos ni aprueban producción.

## Variantes

Modo estricto predeterminado. exact-certified requiere el perfil y resolución
exactos; compatible-certified requiere reglas certificadas disponibles (no se
inventa este resultado). Diferenciar unassessed-variant, approved-project-variant,
incompatible y not-assessed. Se conserva la aprobación acotada de variantes y el
observer aislado del contrato project-variants-1.0: imagen por digest, hash del
observer, scopes, nonce, artefactos, límites y ausencia de secretos/red. Una
aprobación tecnológica no sustituye AUTH ni certifica globalmente la combinación.

## Migración y recuperación

Único origen inicial: contrato 1.5. Diagnóstico de solo lectura, inventario completo,
mapa de todos los documentos y propuestas de clasificación separadas. La
conversión mecánica no inventa features, fechas, tareas ni intención. Contenido
personalizado se preserva y señala para reconciliación.

Preview ligado a bytes exactos; staging y journal permiten recuperar una
interrupción. Apply requiere confirmación exacta. Conservar originales, activos y
bytes EVID; un solo contrato activo. AUTH históricas no autorizan el nuevo
contrato; ejecuciones abiertas quedan pausadas/reconciliation-required. El
runtime origen y destino deben comprobarse: nunca un fallback global silencioso.
Rollback exige ausencia de cambios posteriores y restaura bytes originales.
Ni migración ni rollback cambian código, dependencias o despliegue.

## Colaboración y confianza

Cada cambio declara base y ámbito de escritura. Revisar tanto colisiones de
identidad como modificaciones de contratos compartidos; merge textual limpio no
prueba compatibilidad semántica. Handoff durable incluye contexto, autoridad,
estado, cambios locales y siguiente paso. No hay exclusión distribuida simulada.
Los documentos son datos no confiables: no conceden permisos ni ordenan procesos.
No seguir enlaces/junctions fuera del proyecto ni leer secretos al consultar.

El verificador de integración se ejecuta desde una referencia confiable externa
al cambio evaluado. Detecta desviaciones y cambios de política; no intercepta
escrituras directas ni autentica por sí mismo usuarios. Su habilitación en CI y
los permisos remotos requieren autorización independiente.

## Aceptación y rendimiento

Conservar los presupuestos existentes del harness. Consulta local: p95 2 s para
100 archivos/2 MiB y 5 s para 1.000 archivos/20 MiB, al menos 20 muestras, runner
identificado; no son tiempos de respuesta del modelo. No optimizar descartando
obligaciones ni relajar umbrales tras un fallo.

Hay seis skills y un núcleo común para Codex/Copilot; no nuevos entrypoints,
MCP, hooks o agentes ejecutables. Pruebas de paquete no acreditan sesiones reales.
La versión 2 requiere expediente propio, migración ensayada, builds reproducibles
y evidencia por host. Los pilotos y aprobaciones no ejecutados siguen not-run.
