# Refresco nativo de Windows — diagnóstico y solución propuesta

**Revisión posterior vigente:** [incumplimiento de cota, recuperación y saldo recalculado](REVIEW-H2-MINIMAL-RECOVERY.md). El ensayo mínimo cerró en 358,500 s; H2 sigue inconcluso y no es admisible con el saldo actual. Recuperación operativa propuesta; estado nativo y retirada física pendientes.

Fecha: 2026-10-16. Análisis de lectura tras H2 0.2; no se instalan paquetes,
autentican perfiles, inicializa sandbox ni ejecutan casos. Plugin sin cambios.

## Hechos e interpretación

Los logs separan un aprovisionamiento inicial completado, con cuentas/firewall,
de refrescos posteriores que no registran finalización. La última sonda A venció
a los 60 s sin salida del comando; el auxiliar continuaba activo y fue detenido.
Su recibo conserva 67,5625 s de CPU acumulados hasta la parada. Esto es compatible
con trabajo sostenido de procesamiento/permisos; no identifica la función interna
responsable ni demuestra un bucle infinito, recursión o un defecto concreto.

La matriz preparatoria tenía **116 reglas, 109 denegaciones**, 100 de ellas sobre
materiales anteriores del estudio. No tenía globs. La mayor ruta de una regla
tenía 117 caracteres; no hay error de ruta larga en esos logs. Esto no certifica
las longitudes internas de temporales ni descarta otros problemas de Windows.

Los logs consultados no contienen error 1385 ni rechazo UAC; no se atribuye el
bloqueo a P01. La ausencia de esos mensajes tampoco descarta una restricción
administrada. Las reglas efectivas no mezclaban sandbox antiguo, el catálogo
preparatorio era equivalente y no había MCP/hooks configurados. No hay evidencia
que atribuya la espera a código LKS-SDD o al caso funcional, que nunca comenzó.

## Solución concreta que propongo validar

**Separar el área mínima de ejecución del archivo histórico del estudio y consolidar
las denegaciones**, conservando las fronteras del experimento. Ataca la complejidad
observada; es una hipótesis de reparación, no una solución ya verificada.

Ubicación propuesta, todavía no creada:
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\h2-min`.
Reutiliza la operación de soporte existente. Finalidad: fixture y perfiles mínimos;
responsable: mantenimiento H2; conservación: mismos paquetes/referencias y política
de la incidencia, sin limpieza de originales o cachés oficiales.

1. Preparar dos directorios sintéticos vacíos para sondas y dos CODEX_HOME nuevos,
   con configuración mínima equivalente. No copiar cachés, autenticación o
   `.sandbox-secrets` de los perfiles previos. No mover ni borrar aquellos perfiles.
2. Denegar como un solo subárbol el área histórica `v4-05a`, que ya no contiene
   ninguna raíz permitida del ensayo mínimo. Denegar el otro brazo, el checkout,
   perfiles habituales y todo `extensions` para comandos del caso. Las instrucciones
   necesarias del futuro caso estarán en el runtime propio y la caché nativa propia,
   situados fuera de esos subárboles; el instalador host conserva su acceso oficial.
3. Mantener `:root=read` solo porque el cliente elevado lo exigió, escritura en
   consumidor/temporal propios y lectura protegida de runtime/.git. Mantener red
   deshabilitada. Fijar denegaciones de credenciales y caché ajena sin reaperturas
   de hijos de un padre denegado. Derivar y comprobar la matriz concreta antes de
   ejecutarla; no prometer una cantidad final de reglas sin verificación.
4. **Antes de cualquier carga o acceso**, realizar una única comprobación del
   sandbox mínimo: operación propia permitida, ajena denegada, red con control
   positivo y finalización/cancelación del auxiliar verificables. Cota propuesta
   de desbloqueo: 3 min completos, con espera nativa máxima de 60 s y cancelación
   incluida. No es una reserva admitida ni una instrucción para ejecutarla ahora.
5. Solo si pasa se podría plantear la carga oficial y los accesos. Tras ellos,
   volver a validar la configuración final y el catálogo efectivo, y registrar
   instrucciones en el arranque real. El éxito del ensayo vacío no acredita H2.

Si el perfil mínimo vuelve a atascarse, se rechaza esta hipótesis y se conserva
el diagnóstico. No seguir reduciendo permisos, cambiar a acceso total o usar
`unelevated`: no mantiene las denegaciones de lectura exigidas. No manipular
marcadores ni estado ACL privado para fingir que el refresco está completado.
No desinstalar las cuentas/reglas compartidas para forzar una reparación.

La documentación oficial distingue aprovisionamiento, permisos y restricciones
administradas, y recomienda aportar logs/build para investigar fallos persistentes;
no permite identificar este atasco concreto a partir de los mensajes disponibles.
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox),
[alcance de los permisos](https://learn.chatgpt.com/docs/permissions).

## Presupuesto y decisión técnica

H2 0.2 cerró en **687,160 s**. La cuenta conocida contiene 38 turnos cerrados:
**41.365,582956 s cargados**, descontando una sola vez el reposo ya acreditado.
Saldo al iniciar este análisis: **1.834,417044 s = 30,5736174 min**.
Se acota este análisis y su cierre a **5 min**, dejando al reservarlos **25,5736174 min**.
La duración real reemplazará la cota cuando el turno cierre.

La pareja con las cotas vigentes exige **10+10+6+2 = 28 min**, incluso antes de
reparar, cargar y autenticar. Tras reservar este análisis, faltan al menos
2,4263826 min; un desbloqueo adicional de 3 min eleva el déficit a 5,4263826 min,
sin contar carga/accesos. **No hay admisión presupuestaria para completar H2 con
esas cotas dentro de las 12 horas.** El saldo global no reinicia los 38+3 min previos.

La propuesta es concreta para probar el desbloqueo, pero **no afirmo que desbloquee
ni que permita completar H2 dentro del saldo actual**. No recomiendo otra carga o
autenticación como siguiente paso. Si se priorizara una prueba mínima, solo podría
acreditar reparación del host, quedando H2 pendiente; no sustituye la pareja ni
valida ahorro. Reducir ahora A/B o recuperación para hacer cuadrar una tabla no
está respaldado por tiempos reales de casos y no es parte de esta propuesta.

Se mantienen seis mejoras, cobertura, umbrales, 12 horas y Copilot al final. No se
inicia V4-06 ni se propone modificar el plugin para resolver una dependencia del host.
