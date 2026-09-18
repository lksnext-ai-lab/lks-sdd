# Migrar un proyecto a contrato 2.0

Migrar documentos no actualiza la aplicación, no verifica código ni concede
autoridad para reanudar trabajo. La primera ruta soportada es 1.5/1.5.0 → 2.0/2.0.0.
No convertir esquemas desconocidos mediante cambios de encabezado.

1. Trabajar sobre copia o rama revisada, conservando cambios locales y evidencias.
2. Ejecutar `v2 migration-diagnose <proyecto> --json` desde el runtime destino.
   No escribe. Informa schema, integridad del runtime origen, inventario y ejecuciones.
3. Ejecutar `v2 migration-preview <proyecto> --json`. Si el origen tiene runtime
   fijado, añadir `--target-runtime <runtime-v2-verificado>` explícito.
4. Revisar mapa documento/elemento, originales archivados, personalizaciones y
   pendientes semánticos. La conversión no inventa límites de funcionalidades.
5. Aplicar exactamente ese preview mediante `v2 migrate <proyecto> --apply
   --authorize <hash>` y los mismos argumentos. Cambios de origen invalidan el hash.
6. Validar el resultado. Reconciliar aplicabilidad, TASK, bindings, interfaces,
   planificación, gobierno y autorización antes de implementar.

Los originales se conservan en `docs/lks-sdd/00-control/history/`; las evidencias
permanecen byte a byte. Las decisiones anteriores se conservan como hechos
históricos, sin que una AUTH antigua autorice el nuevo contrato. No hay reasignación
automática de todas las filas a features: esa clasificación requiere comprensión
del producto y aprobación.

La conversión incluye los registros que en 1.5 solo estaban en el índice:
bindings y ejecuciones se convierten en Markdown con el registro original y
reconciliación pendiente. AUTH queda revocada y EXEC/CKPT requieren revisión;
sus IDs y relaciones se conservan. Los metadatos originales, perfiles y locks
se preservan, sin convertir sus estados históricos en aprobaciones v2.

Una interrupción deja `.lks-sdd/transaction.json`. `v2 recover --apply --authorize
<hash>` completa la transacción exacta; `v2 rollback --apply --authorize <hash>`
revierte la interrumpida. Para una operación terminada, añadir `--receipt
.lks-sdd/transactions/<hash>.json`. Cualquier divergencia con trabajo posterior
bloquea la restauración y preserva los archivos. No borrar el journal para forzarla.

La garantía es recuperación registrada y comprobada, no atomicidad simultánea de
todos los archivos. Mientras haya transacción pendiente no iniciar otra mutación.
La instalación activa del plugin, publicación y migración de otros proyectos
requieren sus propias autorizaciones.
