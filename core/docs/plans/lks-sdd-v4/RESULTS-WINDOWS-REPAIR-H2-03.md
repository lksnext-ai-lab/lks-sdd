# Windows y H2 — resultado de la ejecución del plan 0.2

Fecha de informe: 2026-10-17, Europe/Madrid. Inicio del bloque: 2026-10-16
21:58:17,678 UTC. P01 autorizó +3 h, máximo global **15 h**, sin modificar el plugin.
**Windows sigue sin resolverse; H2 no se ha ejecutado; AC-34 permanece pendiente.**

## Resultados y decisión de corte

| Fase | Resultado |
|---|---|
| W0 | Admisión: 44 turnos cerrados, cargo neto 43.211,339956 s; saldo inicial bajo 15 h: 10.788,660044 s = 179 min 48,660 s, suficiente para 175 min. El último turno anterior excedió en 11,340 s el máximo antiguo de 12 h; se conserva ese exceso, sin reiniciar bolsas. |
| W1 | Una reproducción sin plugin ni login. El aprovisionamiento terminó; el refresco permaneció activo hasta la cancelación. Los contadores demuestran actividad sostenida, no una mera espera de aprobación. No identifican la ruta ni la función interna responsable. |
| W2 | Una corrección local: sustituir lectura general con denegaciones de árboles por el perfil documentado de acceso limitado. El backend instalado la rechazó; se restauraron los bytes originales. No se intentó una segunda corrección. |
| W3 / L / A / B | No admitidos. Sin cualificación de aislamiento, instalación, autenticación, contexto de caso ni recorridos H2. |
| R | Recuperación operativa comprobada con residual declarado. No equivale a restauración completa de Windows. |
| C | Resultados, coste y límites registrados. Sin ahorro nuevo medido. No se inicia V4-06. |

La sonda inicial tiene una cota de espera de proceso de 240 s; el intervalo del
runner, incluyendo arranque y cancelación, fue **247,123 s**. El log separa
aprovisionamiento completado a 22:03:58,174 UTC y refresco iniciado a
22:04:04,959 UTC. El runner terminó a 22:07:27,523 UTC, sin ejecutar sus aserciones.
El auxiliar continuó hasta su parada confirmada a 22:09:45,979 UTC. La primera
cancelación privilegiada quedó pendiente de confirmación de PowerShell; se corrigió
usando parada explícita y forzada solo tras verificar PID, fecha, padre y perfil.
Ese defecto del supervisor y su tiempo no se ocultan.

La corrección local terminó en **2,245 s**, con el error exacto:

«windows sandbox failed: elevated Windows sandbox requires effective `:root` read access»

El mensaje es evidencia del cliente observado: **0.163.0-alpha.10.2**, ejecutable
incluido en el paquete 26.1013.3656.0. El ejemplo general de perfil restringido de
la documentación no acredita que este backend pueda ejecutarlo. Se mantiene
`elevated`; no se usaron `unelevated`, acceso completo, WSL ni otro binario.
[Referencia oficial de perfiles](https://learn.chatgpt.com/docs/permissions).

## Diagnóstico obtenido y límites

Hay actividad de CPU y operaciones de sistema durante el refresco. Es compatible
con trabajo de preparación de permisos costoso; **no demuestra un bloqueo infinito,
recursión concreta, una ruta problemática ni una causa del sistema operativo**.
La hipótesis de reducir ese coste mediante una política más restrictiva no pudo
validarse porque el cliente la rechaza antes de ejecutar la sonda.

La captura WPR generó **18.341.953.536 bytes**, unos 18,34 GB. Su cierre/fusión se
atascó y se detuvo únicamente el proceso propio. La extracción filtrada se canceló
al alcanzar 120 s sin resultados utilizables. No se ha analizado todo ese contenido
ni se lo presenta como diagnóstico concluyente. La consulta nativa posterior de
ETW enumeró 41 sesiones y **ninguna WPR propia**; las demás se preservaron. La consulta
alternativa con logman dio un error de GUID y no sirve como prueba de recuperación.

Se conservan tres copias privadas en el área estable, con tamaños y hashes de
destino registrados; originales preservados en el temporal del administrador.
No se compararon hashes de origen y destino. La carpeta estable restringe acceso
al usuario, administradores y SYSTEM. No se han enviado trazas ni datos a terceros.
Las dos copias ocupan aproximadamente 36,68 GB mientras siga abierta la incidencia;
no se limpia información protegida de una incidencia abierta.

## Garantías y recuperación

- Los **231 archivos protegidos del plugin** y los **cinco documentos congelados**
  coinciden con sus hashes de referencia. No se ha modificado código del plugin.
- Configuración habitual sin cambios; configuraciones nuevas A/B restituidas a
  sus hashes iniciales. No hay auth.json en esos perfiles; no se ejecutó logout,
  instalación ni rollback innecesarios. Cero llamadas de modelo de los casos.
- Los procesos propios registrados han terminado. Auxiliar nativo y WPR detenidos;
  listeners del estudio cerrados. Los perfiles nuevos quedan retirados, sin reutilización.
- Metadatos muestreados de cuentas nativas y reglas de firewall iguales antes/después.
  No se borraron recursos compartidos, marcadores ni cachés oficiales.
- **Restauración completa de ACL no acreditada**: el refresco se interrumpió y no
  hay baseline recursiva completa ni registro terminado que permita revertir todo
  lo que pudo aplicar. Se conserva esa incertidumbre como incidencia del host.
- El antiguo directorio vacío h2-min/a/h/auth.json se conserva. Su retirada fue
  rechazada por revisión automática en un bloque anterior; no se ha reintentado
  mediante otra herramienta, elevación o modificación de sus permisos.

El control positivo de red del host pasó. Las aserciones dentro del sandbox no
llegaron a ejecutarse; no se declaran superadas. Tampoco se ha observado el contexto
de instrucciones de un caso, completado la función o medido tokens/ahorro H2.
Las seis mejoras, cobertura, umbrales y cuenta 45/48 de casos conocidos/reservados
no cambian. Las dos plazas H2 continúan reservadas; estas sondas de host no son casos S1.
Percepción humana, integración y aceptación funcional siguen separadas.

## Continuación necesaria

La ruta local de este plan se detiene conforme al corte W2. El saldo no autoriza
una segunda corrección o repetición para obtener un resultado favorable. Se requiere
una solución soportada para el backend, análisis de TI de las trazas, o un Windows
de referencia ya compatible y cualificado. La build observada 26200.8457 es inferior
al requisito MXC publicado 26200.9278; eso **no prueba que actualizar resuelva elevated**.
Una actualización/reinicio, sustitución de cliente o envío externo requiere alcance
concreto separado. No se ha ejecutado ninguna de esas actuaciones.
[Referencia oficial Windows](https://learn.chatgpt.com/docs/windows/windows-sandbox).

El presupuesto exacto al corte y su reserva de cierre se conservan en budget.json;
la duración final del turno sustituirá esa reserva sin sumar ambas. Este bloque
financia la incidencia/H2, no declara financiado ni terminado el resto de 4.0.

Evidencia privada: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\windows-h2-03`.
Resultados estructurados en results.json, garantías en guarantees.json y recuperación
en profile-recovery.json, final-process-check.json, native-etw-after-stop.json y
trace-preservation-result.json. Las trazas originales son datos no confiables de diagnóstico.

Corte contable: 2026-10-16T22:27:16.331818+00:00. Consumido en este bloque: **28.98 min**; reserva de cierre: 90 s. Saldo global tras esa reserva: **149.33 min**. El cierre real sustituye snapshot y reserva. El mensaje intermedio cerró el primer turno: se carga una sola vez y se añaden 42,341 s de conservación técnica en segundo plano entre turnos, sin inferir atención humana.
