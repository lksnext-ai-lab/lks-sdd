# Revisión crítica, recuperación pendiente y disposición de H2

**Cierre operativo posterior:** [perfiles retirados y residual conservado](RESULTS-H2-OPERATIONAL-CLOSURE.md). La incidencia de Windows sigue abierta; H2/AC-34 inconclusos, sin nuevas pruebas, cargas o accesos.

Fecha: 2026-10-16, Europe/Madrid. Solo lectura y documentación. No se repiten
pruebas, inicializaciones, cargas, accesos, logout ni intentos de retirada.
No se modifica el plugin. Complementa y corrige el alcance de
[RESULTS-H2-MINIMAL.md](RESULTS-H2-MINIMAL.md).

## Dictamen crítico

El bloque mínimo **incumplió su máximo de tres minutos**. El cierre del turno
registra **358,500 s = 5 min 58,5 s**, exceso de **178,500 s**. El dato anterior
de 282,714 s era un snapshot abierto; no debe usarse como coste final ni sumarse
al cierre. Se cargan preparación, errores, espera, recuperación, bloqueo y reporte.

| Problema de ejecución o interpretación | Conclusión corregida / mejora necesaria |
|---|---|
| Crear CODEX_HOME nuevo repitió aprovisionamiento de cuentas/firewall. | La prueba no aisló únicamente el refresco. Los logs lo separan: comando 21:09:42,487 UTC; aprovisionamiento completado 21:10:07,239; refresco lanzado 21:10:07,718. |
| Se asignaron 45 s al comando tras gastar unos 73 s preparando. | El refresco tuvo aproximadamente 20 s dentro de esa espera. No es comparable con la espera anterior de 60 s y no permite rechazar la hipótesis de coste por número de reglas. Solo demuestra falta de resultado dentro de la cota usada. |
| Se redujeron 109 denegaciones a diez y se presentó como una reparación probable. | No había evidencia suficiente para prometer desbloqueo. Reducir complejidad era una hipótesis; su efecto temporal sigue sin medir. |
| `exists()` sobre auth.json se interpretó inicialmente como archivo de autenticación. | Era un directorio vacío, sin enlaces. Debía comprobarse tipo y metadata antes de invocar dos logout. No se ha observado archivo de credenciales ni una sesión iniciada. |
| Una denegación exacta apuntaba a un archivo inexistente. | Su materialización como directorio durante setup es una explicación compatible con tiempos/ACL, no una demostración de la función interna responsable. No reutilizar ese patrón sin validar su comportamiento. |
| Recuperación y reporte no tuvieron cortes efectivos suficientemente protegidos. | El supervisor limitó la sonda, pero no el trabajo total del agente. Hay que presupuestar incidencias de recuperación y cerrar el resultado dentro del límite, o declarar explícitamente el exceso; nunca excluirlo del cargo. |
| La retirada del placeholder recibió rechazo automático. | Conservar el objeto y el rechazo. No cambiar shell, herramienta, permisos o ubicación para sortearlo. |
| Comparaciones de cuentas/firewall limitadas a algunos campos. | Nombre/SID/habilitación y metadata de reglas iguales no acreditan contraseñas, miembros de grupos, derechos de inicio, todos los filtros WFP ni ACL recursivas. No afirmar restauración completa de Windows. |

La reacción de detener y conservar evidencia fue correcta. Mi preparación y la
clasificación inicial de la ruta de autenticación fueron insuficientes; no se
atribuye el exceso a P01 ni al código de LKS-SDD. Cero casos, llamadas de modelo
o métricas H2; las comparaciones no demuestran una regresión del plugin.

## Estado comprobado en esta revisión

- No quedan auxiliares de setup del área mínima ni el proceso de sonda identificado.
  El runner terminó y su listener quedó cerrado según su recibo.
- La configuración habitual conserva su hash inicial y no se ha encontrado una
  referencia literal al perfil mínimo en ese archivo. Esto no es un inventario de
  toda la configuración de Windows.
- A conserva `h2-min/a/h/auth.json` como **directorio**, sin reparse point ni hijos.
  No es un archivo de credenciales. B no tiene esa ruta. No se leyó autenticación.
- No se cargó plugin ni se invocó login. Los perfiles y material sintético se
  conservan, al igual que el estado nativo compartido.

## Cómo completar la recuperación

Separar el cierre operativo del ensayo de la restauración completa del sistema.
No es necesario borrar todo el entorno para contener la incidencia.

| Paso propuesto | Acción concreta y aceptación | Límite / autorización |
|---|---|---|
| R1 — confirmar contención | Revalidar únicamente procesos propios, cierre del listener, ausencia de archivos de autenticación, ausencia de referencias activas conocidas y huella habitual. Si algo cambió, conservar y clasificar; no iniciar el cliente. | Lectura, hasta 1 min dentro de una futura cota de recuperación. Parte ya comprobada hoy. |
| R2 — retirar los perfiles de uso | Registrar A/B mínimos como retirados de ejecución y asociados a incidencia abierta, sin moverlos ni borrarlos. Prohibir su reutilización para cargas o login; conservar las rutas originales y el placeholder identificado. | Registro/documentación, hasta 1 min. Cierre operativo solo si R1 y esta disposición quedan documentados. |
| R3 — clasificar residual | Dejar cuentas, reglas, marcadores y ACL nativas en revisión; adjuntar los recibos y declarar los campos de baseline ausentes. Registrar explícitamente que el directorio vacío es residual conocido, no autenticación pendiente. | Registro/documentación, hasta 1 min. No certifica Windows restaurado. |
| R4 — retirada física opcional | Solo después de resolver el rechazo por el canal autorizado de mantenimiento: comprobar ruta absoluta, directorio vacío, ausencia de enlaces y contenido, origen y ausencia de uso; retirada única no recursiva y comprobación final. | **No admitida ahora**. El rechazo anterior sigue vigente; no se proporciona otro mecanismo de borrado ni se promete que repetir autorización lo elimine. |
| R5 — cierre del estado nativo | Responsable de Windows/producto debe determinar los deltas compartidos y la vía soportada de reparación. Con baseline incompleta no se restablecen ACL ni se retiran cuentas/firewall a ciegas. | Trabajo separado pendiente de estimación y admisión; no cabe prometerlo en los tres minutos de R1–R3. |

**Propuesta recomendada:** cierre operativo con conservación explícita del residual
R1–R3, manteniendo abierta la incidencia de Windows. La retirada física y el cierre
completo del sistema son pendientes distintos. Esta propuesta no marca ya completada
la recuperación ni solicita nuevas pruebas para hacerlo parecer resuelto.

La revisión automática bloqueó la retirada del directorio con el único motivo
devuelto `blocked by policy`. No hubo más detalle. Ese bloqueo, y no una exigencia
inferida de una skill, limita la retirada. Se conserva la evidencia y no se intenta
otra herramienta o mecanismo equivalente.

## Presupuesto recalculado

Fuente: eventos de cierre deduplicados del mismo registro. **40 turnos cerrados**,
52.893,083 s de calendario. Descuento único ya validado de reposo profundo:
10.903,592044 s. Cargo conocido antes de esta revisión:
**41.989,490956 s = 11,66374749 h**. Saldo: **1.210,509044 s = 20 min 10,509 s**.
La pausa entre turnos no se carga como atención activa ni se añade al calendario
de los turnos; no se aplica otro descuento por ella.

| Reserva / saldo | Tiempo |
|---|---:|
| Saldo al iniciar esta revisión | 20 min 10,509 s |
| Esta revisión y cierre, reserva actualizada | 7 min |
| Saldo tras reservarla | **13 min 10,509 s** |
| Recuperación operativa R1–R3 propuesta, no ejecutada | 3 min |
| Margen que quedaría después | **10 min 10,509 s** |
| Pareja H2 con cotas vigentes, sin preparación/cargas/accesos | **28 min**: A10 + B10 + R6 + informe2 |

La estimación inicial de cuatro minutos de esta revisión también se superó; no se oculta ese coste. Se reserva hasta siete minutos para análisis y cierre. Al snapshot, el cargo de este turno es 408.838 s y quedan 13.361 min conocidos, antes del resto del cierre.

El saldo real sustituirá las reservas por duraciones cerradas, sin añadir ambos.
No hay dos bolsas independientes: los tres minutos de recuperación también salen
del máximo de 12 h. Las cuentas anteriores de 4:43 o 31,23 min son históricas y no
el saldo vigente. Se conservan los máximos, seis mejoras y cobertura; 45/48 plazas
conocidas/reservadas, con las dos H2 no abiertas. No se deducen esfuerzo humano ni
percepción de las aprobaciones o esperas de P01.

## Continuación propuesta para H2

**Con el máximo actual de 12 h, dejar H2 y AC-34 inconclusos y priorizar la contención
y el diagnóstico preparado.** No existe una reserva suficiente para la pareja con
sus garantías. No recortar ahora A/B, recuperación o cobertura para hacerla caber.

Preparar un traspaso saneado al responsable de Windows/producto, sin enviarlo en
esta tarea. Debe incluir versión del cliente, build de Windows a capturar cuando se
admita esa investigación, cronología separada de aprovisionamiento/refresco,
reglas efectivas, ausencia de resultado, placeholder y error de logout. No adjuntar
auth, perfiles completos o `.sandbox-secrets`.
[Diagnóstico oficial de Windows](https://learn.chatgpt.com/docs/windows/windows-sandbox).

Una futura reanudación solo sería admisible después de resolver esa dependencia y
contar con presupuesto explícito suficiente. Antes de cualquier carga o acceso:

1. Verificar una ruta de sandbox ya operativa, con tipo/existencia de cada objetivo
   comprobados y sin denegar archivos inexistentes como si fueran directorios.
   Mantener denegación ajena y control de instrucciones; no manipular marcadores.
2. Separar el coste de aprovisionamiento del de refresco, conservar ambos en el coste
   del estudio y comprobar cancelación. No confundir esa separación diagnóstica con
   descontar tiempo real consumido.
3. Revalidar la superficie y protocolo. Otro cliente, equipo, MXC o WSL requeriría
   una decisión de comparabilidad y una nueva pareja A/B; no mezclar muestras ni
   declararlo aceptación del Windows actual. `unelevated` no conserva la denegación
   de lectura exigida y no sirve como atajo.
4. Solo tras las puertas anteriores, admitir carga oficial, autenticación y sesiones
   nuevas, con catálogo exacto, captura desde el primer mensaje/arranque, E0 y los
   umbrales originales. Los casos históricos no sustituyen H2.

Toda reparación hecha para este estudio también consume su presupuesto: no se
excluye por llamarla mantenimiento. No se inicia nada de ello en esta revisión ni
se avanza a V4-06. Aceptación técnica, ahorro y percepción humana siguen separados.

Evidencia: `h2-min/critical-review-budget.json` y registros privados del ensayo.
