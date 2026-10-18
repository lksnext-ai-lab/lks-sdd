# V4-01 — Contrato operativo y compatibilidad

**Enmienda física de diseño validada, todavía no implementada:** la
[revisión 0.7](REVISION-0.7.md) mantiene Markdown canónico, método, esquema y
referencias lógicas; sustituye pack/catálogo de 0.6 por ZIP estándar inmutable,
localizador en memoria y mantenimiento físico recuperable. Conserva diarios de
negocio 2.0/2.1; exige lector compatible antes de convertir. La tabla original
queda como antecedente, sin inferir capacidades nuevas en lectores antiguos.

Fecha: 2026-10-15. Plan [0.2](PLAN.md), validado por el usuario en esta conversación.
Alcance autorizado: ejecutar V4-01/V4-02 y presentar resultados antes de modificar
el plugin. Este contrato concreta el diseño; sus operaciones y opciones **todavía
no existen**. No acredita ejecución de 4.0 ni aprobación de resultados futuros.

## 1. Frontera y decisión de compatibilidad

Base: 3.4.3, commit `bf4d059c98826039097d606121ab6406d762fcc7`.
Se conserva método **3.1.0**, esquema canónico **3.1** y los seis objetivos de skill.
La nueva capa consulta o compone operaciones existentes. No cambia significado de
aprobaciones, estados, controles, permisos, correcciones o exclusiones de contexto.

Esta decisión de diseño se apoya en las capacidades actuales, no en una migración
ensayada con 4.0. La implementación debe demostrarla en AC-24/AC-25/AC-26. Una
carencia que requiera nuevo significado canónico reabre solo esa decisión antes
de escribir: la versión mayor del producto no autoriza a modificar el método.

| Elemento | Decisión V4-01 | Fundamento actual y comprobación futura |
|---|---|---|
| Producto | Objetivo 4.0.0, sin cambiar ahora manifiestos. | La base identifica 3.4.3; AC-03/AC-24 verifican distribución futura. |
| Markdown, proyecto, colaboración | Método 3.1.0, schemas 3.1 conservados. | `v3_schema`, `v3_current.require_current`; no se añaden campos normativos. |
| Almacenamiento existente | Conservar `lks-sdd-object/1`, `inventory/1`, `state/1`, `packet/1`, `usage/1` con el prefijo `lks-sdd-` en cada nombre. | Lista `v3_current.FORMATS`; objetos y transacciones siguen pasando sus validadores actuales. |
| Presentación y decisiones | Conservar recibos y guard de presentación vigente. | `v3_presentation_guard.required/reviewed/stamp`; ni un resumen ni un export prueban lectura o aprobación. |
| Operaciones nuevas | Adaptador sobre consultas/transiciones actuales, con versión de interfaz propia. | No escribir nuevos estados canónicos para representar una operación compuesta. |
| Diagnóstico nuevo | Captura externa, opcional y explícita; no es una base de autorización. | Se conservan `usage-record/report/export` existentes; no ignorar corrupción de sus registros canónicos. |
| Runtime del consumidor | Las nuevas operaciones requieren runtime que realmente las incluya. | Comprobar capacidad del paquete/runtime fijado; instalar el plugin no actualiza ese runtime. |
| Lectores anteriores | Mantener lectores soportados y bloqueo de escrituras no actuales. | No ofrecer escritura 4.0 sobre 1.5/2.0/3.0; preparación puede explicar la migración necesaria. |
| Recuperación | Rollback de transacciones/actualización según capacidad, nunca sustitución ciega por runtime viejo. | Journal actual, sujetos y cambios posteriores; AC-12/AC-25. |

Los nombres de capacidad `work-prepare/1`, `work-continue/1` y
`work-record-results/1` describen requisitos del nuevo adaptador. No se escriben
en el proyecto como permisos ni obligan a ampliar el formato del lock. La
distribución debe poder acreditar su presencia antes de ofrecerlas. Si esto exige
cambiar un formato técnico persistente, versionarlo y comprobar lectores antes
de incorporarlo, sin inferir compatibilidad por el número de versión del producto.

## 2. Interfaz común propuesta

Conservar todos los comandos y opciones existentes. Las acciones nuevas se exponen
en el CLI compartido `v3`, sin nuevas skills, servidores ni procesos residentes.

```text
python scripts/lks_sdd.py v3 work-prepare ROOT --input request.json --view operational --json
python scripts/lks_sdd.py v3 work-continue ROOT --input request.json --output packet.json
python scripts/lks_sdd.py v3 work-record-results ROOT --input request.json --output packet.json
```

`--view operational` es una opción nueva propuesta para salidas sin duplicación
diagnóstica. La modalidad compatible conserva los contratos actuales; no cambia
el default de consumidores anteriores. `--compact`, `--details`, `--output` y
`--json` deben tener precedencia explícita y una matriz de regresión. Un export
elegido explícitamente muestra una referencia corta, incluso al combinarlo con
modo compacto; no vuelve a emitir el cuerpo íntegro por otra rama de presentación.

Formatos nuevos de transporte, fuera del Markdown canónico:

- `lks-sdd-operation-request/1`: entrada de las acciones nuevas.
- `lks-sdd-operation-result/1`: estado, porción, condiciones y resultado operativo.
- `lks-sdd-diagnostic-run/1`: índice y observaciones de captura externa.

Cada request declara `version`, `operation_id`, `task`, `actor` cuando sea necesario
y parámetros propios. `operation_id` identifica un intento lógico; no concede
autoridad ni sustituye IDs canónicos. Reusar ID con parámetros distintos es error.
La raíz se recibe por CLI, se resuelve una sola vez y se comprueba antes de acceder
a materiales. Rechazar claves desconocidas y tipos erróneos en estos formatos.

La salida operativa contiene, como mínimo:

| Campo | Obligación |
|---|---|
| `version`, `operation_id`, `operation` | Versión y correlación, sin inferir confianza por su presencia. |
| `status` | `ready`, `completed`, `action-required`, `blocked` o `partial`; ninguno equivale a aceptación humana. |
| `task`, `actor`, `basis` | Identidades y base observada; actor ausente/desconocido impide afirmar preparación para ejecutar. |
| `conditions` | Condiciones satisfechas, faltantes y límite de vigencia; no un único booleano que oculte causas. |
| `contract` | Contenido literal suficiente, fuentes, adjuntos y exclusiones justificadas; el detalle diagnóstico no duplica sus textos. |
| `effects` | Etapas aplicadas, no aplicadas y sus recibos reales; vacío en consulta. |
| `next` | Siguiente acción y quién debe actuar cuando corresponda, sin maquinaria interna innecesaria. |
| `diagnostic_ref` | Referencia externa opcional; ausente con razón si no hubo captura. No acredita lectura. |

El contenido normativo necesario se entrega íntegro. Un límite técnico produce
`action-required` y una lectura/ampliación delimitada; nunca `ready` con contrato
vacío, truncado o sustituido por hashes. Preparar una decisión futura no la registra.

Los códigos propuestos de las acciones nuevas son 0 para consulta suficiente o
finalización, 2 para bloqueo/intervención necesaria y 3 para aplicación parcial.
Los códigos de comandos actuales se conservan. Errores de entrada, raíz o runtime
no generan escrituras normativas ni continúan por una ruta antigua de escritura.

## 3. Operaciones, entradas y efectos

| Operación | Entrada propia | Salida y efectos permitidos | Parada y recuperación |
|---|---|---|---|
| `work-prepare` | Tarea inequívoca, actor actual para evaluar ejecución y acción pretendida; referencia completa opcional. | Reúne estado, intervenciones, readiness y contexto literal sobre una evaluación coherente. Solo lectura del consumidor. | Bloquea raíz vacía/retirada, identidad insuficiente o runtime incompatible; informa porción independiente. No persiste una autorización reutilizable. |
| `work-continue` | Tarea, actor, razón y objetivo `start` o `resume`, con base esperada. | Prepara la transición técnica vigente y permite aplicarla por los mecanismos de preview/apply existentes. | Si falta recepción, revisión, autorización o decisión nueva, devuelve intervención necesaria. Nueva base exige nuevo preview. |
| `work-record-results` | Tarea, actor, razón, objetivo máximo y referencias a resultados/evidencia real del sujeto exacto. | Registra únicamente las etapas elegibles entre implementación, evidencia, verificación y cierre; conserva cada hecho y sus controles. No ejecuta pruebas ni código del JSON. | Se detiene en la primera etapa no acreditada; muestra lo aplicado y lo pendiente. No integra ni acepta funcionalmente el resultado. |
| Vista de continuidad | Tarea y actor actual, derivada dentro de `work-prepare`. | Reconstruye estado, pendientes y lectura necesaria desde fuentes. No crea checkpoints por consultar. | Chat nuevo, compactación o fuente cambiada requieren recuperar contenido e identidad; no retomar con autoridad heredada. |
| Captura diagnóstica | `--capture-dir` externo explícito y ventana `run_id`; materiales dentro de límites admitidos. | Escribe solo el directorio seleccionado; índice, observaciones y objetos recuperables. Sin esa opción, no hay captura implícita. | Error se distingue de fallo normativo. No declarar conservado lo que falta; reintento por identidad/contenido y rechazo de colisiones. |
| Conservación/exportación | Ventana, destino y límites; hitos ya autorizados para registros actuales. | Conserva lotes programáticamente sin reconstrucción manual del agente; reutiliza formatos/operaciones existentes. | Fuente retirada exige bytes conservados; hash solo no basta. Procedencia importada conserva su grado de confianza. |

En la primera versión del adaptador, `work-continue` no recoge decisiones humanas
nuevas mediante flags implícitos. Recepciones/revisiones ausentes utilizan el
recorrido vigente de presentación y respuesta explícita. Una respuesta ya vigente
puede reutilizarse si el núcleo la considera suficiente; no se vuelve a preguntar.
La composición no firma por otra persona ni evita revisión independiente.

Ejemplo positivo de preparación: tarea vigente y autorizada, actor asignado y
contrato suficiente producen `ready`, `effects: []` y siguiente acción técnica.
Ejemplo negativo: un UID retirado o ambiguo produce bloqueo y causas, nunca selección
de otra tarea por aproximación. Mismo contenido en modos distintos conserva el recibo
de decisión vigente; no se exige igualdad binaria entre sobres técnicos diferentes.

Ejemplo positivo de resultados: el archivo corregido y una prueba realmente ejecutada
sobre ese sujeto permiten registrar evidencia y avanzar hasta el objetivo cubierto.
Ejemplo negativo: reporte antiguo, `not-run`, cambio fuera de alcance o validador
independiente ausente detienen la etapa correspondiente. El estado final real se
conserva aunque la operación no alcance su objetivo máximo.

## 4. Vigencia, concurrencia e idempotencia

La preparación es una instantánea informativa. Antes de cada aplicación material
se releen autoridad, política, rama/base, fuente, sujeto y evidencia, con los guards
existentes. No basta que coincida el contrato si cambió la asignación o hubo revocación.
No se promete un bloqueo distribuido entre clones ni atomicidad de herramientas externas.

La primera composición de resultados usa etapas delimitadas y transacciones actuales,
sin inventar una transacción única que abarque pruebas o ediciones. Cada etapa declara
inputs, base, efecto esperado y recibo. Un intento interrumpido continúa únicamente
desde hechos acreditados, no desde una lista de pasos supuestamente completados.

Reintentar el mismo paquete con su hash conserva la idempotencia que hoy ofrece
`v3_storage.apply` (`previously-applied`). Para varias etapas, el manifiesto externo
es una ayuda de localización; cada recibo, contenido y estado se valida con el núcleo.
No deducir que un estado coincidente acredita que este intento produjo el efecto.
La correlación de etapas debe quedar demostrada en AC-12 antes de habilitar aplicación
compuesta. Si los registros actuales no bastan, detener esa capacidad y presentar
el cambio técnico mínimo, sin rebajar el contrato de reintento ni añadir autoridad.

Ante cambio concurrente se conserva lo aplicado, se rechaza la base obsoleta y se
prepara la porción restante sobre una base nueva. Rollback requiere el mecanismo
vigente y nunca sobrescribe trabajo posterior para simular un resultado atómico.

## 5. Captura, procedencia y ciclo de vida

La captura se configura con destino explícito fuera del consumidor, usando un área
de evidencia existente. No modificar reglas de exclusión del consumidor para alojarla.
Una ventana agrupa procesos y llamadas, pero no autentica al operador ni a su productor.
Índice y objetos tienen límites de cantidad/tamaño, hashes y escritura recuperable;
no sobrescribir una ventana existente con contenido conflictivo. Las cifras concretas
de los validadores actuales se conservan como máximo inicial: 1 MiB/1.000 observaciones
por lote, 20.000 observaciones y 64 MiB por ventana, 64 KiB por fragmento y 10.000
archivos/64 MiB por exportación. V4-04 no los amplía sin justificarlo. Una fuente
mayor exige conservarla mediante materiales admitidos o declarar captura incompleta;
ningún límite diagnóstico autoriza truncar el contexto normativo operativo.

Un objeto guardado desde el runtime conserva sus bytes, procedencia y versión. Al
importarlo en otro proceso, un hash no prueba que una declaración sea una medición:
mantener la degradación de confianza de `v3_usage.imported`. No añadir claves de firma,
servicios ni prometer autenticación nueva. La medición externa controlada de V4-02
es evidencia del observador, con su cobertura declarada, no un permiso del consumidor.

Captura deshabilitada: entregar resultado operativo suficiente y declarar que el
diagnóstico completo no se ha conservado; la modalidad compatible sigue disponible.
Error al capturar después de una etapa aplicada: informar ambos hechos y recuperar
solo la captura pendiente; no fingir que el fallo deshizo el cambio normativo.
Corrupción de registros diagnósticos canónicos anteriores sigue siendo un fallo de
integridad del núcleo, no un aviso descartable de la nueva captura externa.

Esta ejecución usa `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015`:
finalidad, responsable y retención se registran en `provenance.json`. La evidencia
voluminosa satisfactoria tiene 90 días según política central; manifiestos ligeros
permanecen. No se modifica esa política ni se inicia limpieza o instalación.

## 6. Alcance, instrucciones, mantenimiento y cálculo

M3 reutiliza `proposal_units`, relaciones y declaraciones de prosa actuales, revisadas
por autoridad competente. Empezar por autoría nueva y un lote acotado de legado.
No cambiar la vigencia de aprobaciones para ahorrar: hoy las declaraciones de prosa
dependen también del digest del proyecto (`v3_scope.prose_scopes`). Una modificación
de gobierno puede invalidar su acreditación global. Una invalidación más fina que
no sea demostrable con el contrato actual requiere decisión separada; la primera
entrega mantiene la vía conservadora y mide su coste.

M4 asigna cada regla a núcleo, instrucción de juicio o referencia. La porción H2
se adapta primero; después se completan las seis skills con invocación implícita.
No retirar comprobaciones del núcleo por haberlas escrito en una guía, ni suponer
que un control estructural decide suficiencia semántica o comprensión humana.

M5 conserva las clases existentes y prueba su aportación con tres recorridos:

| Caso | Base 3.4.3 | Mejora que debe demostrar V4-10 |
|---|---|---|
| Defecto dentro de encargo vigente | Se conserva autorización; editar código no reabre por sí solo el encargo. Nuevas pruebas/aceptación siguen siendo exigibles. | Menos búsqueda y reconstrucción para comprobar cobertura y registrar resultado, usando M2/M4. No crear una aprobación que ya existe. |
| Cambio del acuerdo | Se clasifica `agreement-change`; validar contenido afectado y después plan/permiso. | Mostrar diferencia y fuentes suficientes sin repetir acuerdos vigentes ajenos; conservar decisiones separadas. |
| Capacidad nueva/transversal | `new-request` o recorrido completo aplicable; incertidumbre exige ampliar. | Orientación directa hacia la nueva definición, sin vueltas por un recorrido abreviado insuficiente. |

Tarea cerrada, rechazo o permiso vencido se ensayan aparte: la clasificación no es
autorización de reapertura. Una carencia de instrucciones se corrige allí; nuevo
comportamiento del núcleo requiere reproducción y comparación antes/después.

M6 permite reutilización dentro de evaluación inmutable y conserva lecturas/guards
frescos al aplicar. No introduce caché persistente de permisos. Beneficio absoluto,
frecuencia observada, complejidad y presupuesto determinan incorporación o descarte.

## 7. Matriz de garantías y responsabilidades

| Garantía | Componente que la hace cumplir | Juicio/instrucción que se mantiene | Comprobación exigible |
|---|---|---|---|
| G1 | `v3_contract`, `v3_storage`, `v3_current` | Fuentes Markdown frente a vistas derivadas. | Índice regenerable; captura no cambia decisiones. |
| G2 | `v3_scope`, `v3_context`, `v3_decision_presentation` | Suficiencia semántica, incertidumbre y adjuntos. | Inventario independiente, negativos y revisión del código producido. |
| G3 | `v3_approval`, `v31_review`, `v3_presentation_guard` | Mostrar contenido y vincular respuesta real. | Ninguna etapa compuesta concede nuevas decisiones. |
| G4 | `v3_policy`, `v3_git`, `v3_team`, guards de storage | Identidad actual, autoridad y límites entre clones. | Revocación, reasignación, rama y fuente cambiadas. |
| G5 | `v3_quality`, `v3_verification`, `v3_workflow` | Explicar reservas y medios de prueba reales. | Sujetos/evidencia actuales; errores y `not-run` no superan controles. |
| G6 | `v3_storage`, journal y recibos existentes | Explicar aplicación parcial/recuperación. | Reintentos e interrupciones; preservar cambios posteriores. |
| G7 | `v3_cli`, `v3_usage`, captura externa delimitada | Destino explícito, procedencia y retención. | Consulta sin escritura; importación no promueve confianza. |
| G8 | Seis skills y builders/adaptadores existentes | Selección implícita pertinente por host. | Mismo núcleo; uso real de cada host acreditado aparte. |
| G9 | `v3_current`, `runtime_doctor`, distribución/migración | Instalación y actualización del runtime diferenciadas. | Orígenes soportados y recuperación de actualización. |
| G10 | Validadores de contrato/rutas y fuentes canónicas | Datos del proyecto no son órdenes. | Fuentes canónicas intactas, entrada rechazada y diff revisado. |

## 8. Verificación de V4-01 y límite del resultado

AC-01: interfaces, efectos, paradas, vigencia y ejemplos definidos en secciones 2–5.
AC-02: decisión de compatibilidad y límites documentados en secciones 1/4/6; no se
autoriza un escritor que necesite decisiones críticas no resueltas.
AC-03: seis skills y mismos objetivos; ningún servidor, hook, conector, agente o
entrypoint vacío añadido. El contrato estático se ejecuta al entregar esta fase.

El resultado es verificación documental de V4-01 sobre la base actual. Los AC de
implementación, actualización, idempotencia compuesta y aceptación humana de 4.0
siguen sin ejecutar. Los puntos que necesitan elección del usuario o evidencia
externa se presentan en [RESULTS-H1.md](RESULTS-H1.md), sin extender su autorización.
