# Rollback del piloto M5

1. Detener nuevas instalaciones y marcar externamente el piloto como `withdrawn`.
2. Conservar de forma saneada la versión, checksum, motivo, alcance y evidencia de la retirada.
3. Recuperar la distribución candidate anterior `v0.6.1` desde su etiqueta inmutable y verificar ZIP, manifiesto y checksum antes de usarla.
4. Consultar `codex plugin marketplace --help` en la versión instalada. En el CLI 0.125.0 comprobado para esta release no existen subcomandos `install`, `uninstall`, `activate` ni `deactivate`; la CLI solo administra fuentes mediante `add`, `upgrade` y `remove`.
5. Sustituir de forma controlada la fuente local ya configurada por la distribución verificada 0.6.1 y ejecutar `codex plugin marketplace upgrade lks-sdd-development`. Si es necesario volver a registrar esa fuente, usar `codex plugin marketplace remove lks-sdd-development` y después `codex plugin marketplace add "<marketplace-root>"`. Complete la selección o retirada del plugin en la superficie de Codex disponible, sin atribuir esa acción a la CLI.
6. Confirmar que Codex resuelve la versión 0.6.1, reiniciar la aplicación y abrir una tarea nueva para recargar metadatos y skills.
7. No revertir automáticamente documentos o código de proyectos consumidores; revisar sus diffs y migraciones por separado.
8. Verificar que no queden marketplace temporales, paquetes, datos del piloto o sesiones activas fuera de la retención aprobada.
9. Registrar el resultado y decidir corrección, repetición o cierre.

El rollback de distribución no concede permiso para borrar evidencia, reescribir Git ni modificar proyectos consumidores. Si un proyecto se migró del contrato 1.0 al 1.1, su reversión se decide y valida por separado a partir del backup autorizado; no se deduce del cambio o recarga de la distribución 0.6.1.
