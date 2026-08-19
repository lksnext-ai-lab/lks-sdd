# Rollback del piloto M5

1. Detener nuevas instalaciones y marcar externamente el piloto como `withdrawn`.
2. Conservar de forma saneada la versión, checksum, motivo, alcance y evidencia de la retirada.
3. Desinstalar `v0.5.0` mediante el flujo de Codex aplicable al marketplace configurado.
4. Reinstalar la última candidate verificada `v0.4.0` desde su etiqueta y checksum, sin mover ninguna etiqueta existente.
5. No revertir automáticamente documentos o código de proyectos consumidores; revisar sus diffs y migraciones por separado.
6. Verificar que no queden marketplace temporales, paquetes, datos del piloto o sesiones activas fuera de la retención aprobada.
7. Registrar el resultado y decidir corrección, repetición o cierre.

El rollback de distribución no concede permiso para borrar evidencia, reescribir Git ni modificar proyectos consumidores.
