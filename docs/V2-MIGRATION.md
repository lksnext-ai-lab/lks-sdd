# Migrar un proyecto a contrato 2.0

Migrar documentos no actualiza la aplicación, no verifica código ni concede
autoridad para reanudar trabajo. La primera ruta soportada es 1.5/1.5.0 → 2.0/2.0.0.
No convertir esquemas desconocidos mediante cambios de encabezado.

1. Trabajar sobre copia o rama revisada, conservando cambios locales y evidencias.
2. Ejecutar `v2 migration-diagnose <proyecto> --json` desde el runtime destino.
   No escribe. Informa schema, integridad del runtime origen, inventario y ejecuciones.
3. Ejecutar `v2 migration-preview <proyecto> --json`. Si el origen tiene runtime
   fijado, el agente usa automáticamente el runtime v2 empaquetado cuando su
   `package-integrity.json` es íntegro; si no está disponible, añadir
   `--target-runtime <runtime-v2-verificado>` explícito.
4. Revisar mapa documento/elemento, originales archivados, personalizaciones,
   la nueva declaración tecnológica local y pendientes semánticos. La conversión
   no inventa límites de funcionalidades ni decisiones tecnológicas.
5. Aplicar exactamente ese preview mediante `v2 migrate <proyecto> --apply
   --authorize <hash>` y los mismos argumentos. Cambios de origen invalidan el hash.
6. Validar el resultado. Reconciliar aplicabilidad, TASK, bindings, interfaces,
   planificación, gobierno y autorización antes de implementar.

El agente cierra técnicamente la migración en la misma aplicación del preview:
el índice v2 queda en estado `migration-complete`, los escritores legacy quedan
bloqueados y el recibo contiene un manifiesto de conservación cerrado. El usuario
solo valida el preview completo y autoriza su hash exacto; esa autorización no
inventa decisiones de negocio ni convierte una incertidumbre en aprobación.

El manifiesto asigna cada fuente del inventario a una disposición:
`transformed`, `archived`, `preserved-out-of-scope` o `blocked`. Una migración con
fuentes sin disposición no puede llegar a preview. El inventario está acotado,
rechaza secretos, Git, enlaces/symlinks, repositorios anidados y documentos
Markdown no UTF-8; los enlaces internos se cierran y los adjuntos binarios se
conservan por hash y bytes. El recibo liga el mapa completo mediante un
`closed_source_snapshot` y un `conservation_fingerprint`; ambos se vuelven a
comprobar en cada consulta de estado.

Los originales se conservan en `docs/lks-sdd/00-control/history/`; las evidencias
permanecen byte a byte. Las decisiones anteriores se conservan como hechos
históricos, sin que una AUTH antigua autorice el nuevo contrato. No hay reasignación
automática de todas las filas a features: esa clasificación requiere comprensión
del producto y aprobación.

La conversión incluye los registros no tecnológicos que en 1.5 solo estaban en el
índice: bindings genéricos y ejecuciones se convierten en Markdown con el registro
original y reconciliación pendiente. AUTH queda revocada y EXEC/CKPT requieren
revisión; sus IDs y relaciones se conservan.

La migración genera directamente
`03-solution/technology-declaration.md`. Solo deriva observaciones de documentos
del consumidor y manifiestos estáticos locales acotados; no consulta catálogos ni
ejecuta detectores. Las fuentes tecnológicas 1.x retiradas se archivan como
procedencia histórica y no se copian como bindings, decisiones ni autorizaciones
v2 activas. Un componente observado no es una tecnología confirmada.

La declaración distingue `observed`, `proposed`, `confirmed`, `unknown` y
`transition`. La migración deja una transición y cualquier incertidumbre crítica
explícitas. La conversión técnica puede quedar registrada, pero una tecnología
crítica ambigua bloquea la preparación y continuación de la TASK afectada hasta
confirmación humana. Los unknown no críticos siguen visibles sin conceder
preparación.

Una interrupción deja `.lks-sdd/transaction.json`. `v2 recover --apply --authorize
<hash>` completa la transacción exacta; `v2 rollback --apply --authorize <hash>`
revierte la interrumpida. Las operaciones terminadas se conservan en el único
almacén técnico `.lks-sdd/transactions.json`; para restaurar una de ellas, añadir
`--receipt .lks-sdd/transactions.json`. Las versiones anteriores que dejaron
`.lks-sdd/transactions/<hash>.json` siguen siendo legibles y se consolidan al
recuperarlas. Cualquier divergencia con trabajo posterior bloquea la restauración
y preserva los archivos. No borrar el journal para forzarla.

La garantía es recuperación registrada y comprobada, no atomicidad simultánea de
todos los archivos. Mientras haya transacción pendiente no iniciar otra mutación.
La instalación activa del plugin, publicación y migración de otros proyectos
requieren sus propias autorizaciones.

## Corte limpio y continuidad selectiva

`v2 migration-status` comprueba que no quedan documentos activos 1.5, que existe
el recibo y que el estado del índice es `migration-complete`. Si detecta mezcla,
bloquea las escrituras v2 y conserva el diagnóstico para corregirlo; no devuelve
`already-v2` solo por leer `schema_version=2.0`.

La migración conserva datos históricos como `legacy`, estados `unknown` o
`conflict`, y `reconciliation-required`. Esos registros no forman parte del
contexto normativo ni conceden autoridad; una referencia explícita solo permite
localizarlos como antecedente para la reconciliación.
`v2 migration-continuation --task TASK-###` calcula si una TASK concreta puede
continuar. Solo se bloquea el alcance afectado por semántica pendiente; una TASK
independiente no hereda automáticamente el bloqueo de otra.

### Registros históricos y ejecución v2 vigente

Una ejecución v2 activa está exclusivamente en uno de estos estados:
`in-progress`, `in-review`, `paused` o `blocked`. Los dos últimos siguen en el
ciclo de trabajo y por ello impiden iniciar otra ejecución normativa para el mismo
ámbito. `reconciliation-required`, `completed` y `cancelled` no son ejecuciones
activas. En particular, un `EXEC` histórico en
`reconciliation-required` no puede autorizar, reanudar, producir checkpoints,
generar evidencia ni aceptar resultados.

El runtime selecciona una ejecución vigente por la relación normativa
`implements`, dentro del `--task` solicitado. Una relación histórica `affects`
permanece como antecedente auditable, pero no convierte el registro en la
ejecución de esa TASK. Dos ejecuciones normativas activas para el mismo ámbito
siguen bloqueando la operación: el runtime no escoge una arbitrariamente.

No edite, cancele ni borre manualmente los documentos históricos para continuar.
Permanecen visibles en `catalog`, `status`, snapshots e informes de migración. Para
resolver su significado use `migration-continuation`, `correct` o `replan`, que
conservan los recibos y snapshots correspondientes.

Un runtime 1.x conservado para rollback queda marcado como histórico y nunca
gobierna trabajo futuro. Para un proyecto sin runtime gestionado se realiza la
conversión documental, pero la instalación/activación de un runtime se mantiene
como operación separada y explícita.

Después de la migración, la reducción de ruido operativo es independiente y
explícita: `retention-status` diagnostica sin mutar; `retention-compact` archiva
solo AUTH/EXEC/CKPT/PROB/REC cerrados y sin referencias activas, y
`retention-restore` los devuelve verificando sus hashes. No se compactan los
documentos normativos ni las EVID, y la migración nunca elimina silenciosamente
archivos de un consumidor existente.
