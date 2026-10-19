# Actualización de LKS-SDD 4.0.2

Corrige el bloqueo de `author` al preparar cambios documentales con objetos
históricos válidos mayores de 4 MiB. La copia de validación usa el límite existente
de 64 MiB por fuente, comprueba su huella y agrupa los objetos temporales. El lector
mantiene el límite de 4 MiB por documento canónico y todos los controles de
integridad, rutas, permisos, aprobación y recuperación.

El cambio permite editar peticiones y revisar el estado editorial de TASK/PLAN
sin truncar objetos ni eliminar historia. Cancelar la ejecución, retirar un
contrato, integrar una rama y aceptar una entrega siguen siendo operaciones
distintas. No se cambian automáticamente sus estados ni se conceden aprobaciones.

Instalar 4.0.2 en Codex no actualiza los runtimes fijados de los proyectos.
Preparar y autorizar su actualización con el instalador oficial, comprobar
`runtime-doctor` y ejecutar desde la CLI de ese runtime. Resolver antes cualquier
diario pendiente con su runtime compatible. Conservar el paquete anterior para
recuperación; no retirar ni editar manualmente objetos o ZIP.

Se conservan las seis skills, schema 3.1, método 3.1.0, formatos y mantenimiento
por lotes de [4.0.1](UPGRADE-4.0.1.md). Las regresiones focales usan autoría pública
con objetos sueltos y compactados, rechazo de corrupción y de fuentes cambiadas.
No acreditan tiempos universales ni aceptación del consumidor real. Windows/H2
siguen pendientes y no forman parte de esta corrección.
