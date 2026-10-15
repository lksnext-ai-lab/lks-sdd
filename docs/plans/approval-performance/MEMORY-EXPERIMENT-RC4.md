# Experimento de memoria rc.4: rechazado

Se probaron de forma independiente la compactación de `Element` y la reutilización
del diccionario de elementos para el índice UID. Ninguna cumple la condición
autorizada de reducir memoria sin introducir regresiones de CPU o velocidad.

- El índice UID conserva la equivalencia, pero empeora las cuatro parejas de
  consultas: medianas de CPU +23,88 % y duración +23,17 %. No se integra ni se combina.
- `Element` compacto, con copia superficial compatible, reduce las asignaciones
  vivas del perfil de 1.500 elementos un 1,46 % (44.978 bytes). Sin embargo, la
  confirmación del CLI reproduce pérdidas en `validate` (+10,65 % CPU; +9,18 %
  duración) y `start:prepare` (+13,23 % CPU; +11,62 % duración), en las cuatro
  parejas. Los lotes largos también muestran regresiones. La mejora del total del
  ciclo no compensa estas pérdidas conforme al criterio autorizado.

Se restaura el runtime y la metadata de versión de rc.3 con sus bytes exactos,
conservando las correcciones previas, los tests nuevos y la evidencia del
experimento. Los ZIP y el patch rc.4 quedan congelados como candidata experimental
rechazada. No hay nueva candidata aceptable, publicación, instalación, commit,
push ni integración en otra rama.

Las 66 pruebas de la candidata y los recorridos técnicos de ambos paquetes pasan;
la decisión negativa se debe al rendimiento. La activación conversacional del
host, el piloto y los tokens facturados no se acreditan. No se añaden instrucciones
ni llamadas al modelo en las propuestas.

La evidencia local se conserva en `tests/reports/rc4-final-report.md`,
`tests/reports/rc4-closure.json`, el manifiesto de rc.4 y su archivo de evidencia.
Incluye las series excluidas, los pares completos, las diferencias de respuestas,
las huellas de herramientas/paquetes y la restauración de los 12 archivos propios
del experimento. Este resultado no acredita rc.3 para publicación ni sustituye
la puerta estable.
