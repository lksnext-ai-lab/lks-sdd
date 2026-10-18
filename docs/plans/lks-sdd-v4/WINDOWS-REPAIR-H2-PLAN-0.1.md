# Reparación de Windows y H2 — plan realista con presupuesto adicional

Fecha: 2026-10-16, Europe/Madrid. Revisión **0.1 propuesta, sin ejecutar**.
Alcance: resolver o caracterizar el bloqueo del host, validar aislamiento/instrucciones
y completar una pareja H2 con recuperación. No modificar LKS-SDD ni continuar V4-06.
Las seis mejoras, cobertura y umbrales permanecen; no se declara financiada toda 4.0.

## Presupuesto solicitado

La recuperación operativa anterior cerró en **213,116 s**, dato que sustituye su
reserva de tres minutos y también registra el exceso. Son **42 turnos cerrados**:
53.537,498 s de calendario menos el descuento único de reposo de 10.903,592044 s
= **42.633,905956 s** cargados. Antes de este plan quedaban **566,094044 s** del
máximo de 12 h. Reservando **6 min para este plan y su cierre**, quedan
**206,094044 s = 3 min 26,094 s**. Al cerrar se sustituye la reserva por tiempo real.

Propongo **180 min futuros**, de los que 20 son contingencia protegida. Ampliar el
máximo global de **12 a 15 horas: +3 horas**. Después de reservar este plan, el
saldo nuevo sería 183 min 26,094 s; financiaría los 180 min y conservaría otros
3 min 26,094 s. El incremento matemático mínimo sería 176 min 33,906 s; redondear
a tres horas evita otra asignación sin margen. No se ejecuta nada con esta propuesta.

Esta estimación es una cota de trabajo, no una garantía de reparación de una causa
desconocida. Una espera de proveedor, descargas, reinicios o intervención de TI
puede alargar el calendario. Todo tiempo de trabajo/espera técnica efectivamente
consumido por este estudio se registra; no se excluye llamándolo mantenimiento.
No dejar una sesión activa esperando indefinidamente. Si una dependencia externa
impide avanzar, cerrar el bloque con el saldo real y replanificar antes de retomarlo.

## Tareas, responsables y dependencias

Responsables: agente para evidencia, fixture y comparación; administrador/soporte
Windows para permisos de sistema, traza privilegiada o cambios del host; P01 para
decisiones de alcance e intervenciones de acceso necesarias. No se presume que el
agente pueda autorizarse cambios de sistema o contactar a terceros.

| ID | Tarea / dependencia | Cota | Aceptación / salida |
|---|---|---:|---|
| W0 | Admisión, residual, baseline y cancelación; inicio. | 15 min | Saldo del bloque reservado, perfiles retirados preservados, cambios de sistema atribuibles y recuperación definida; supervisor/profiler con parada comprobable. Si no, no reproducir. |
| W1 | Una reproducción instrumentada sin plugin/login; depende W0. | 30 min | Separar aprovisionamiento, refresco y lanzamiento; registrar CPU, disco/archivo y espera del auxiliar, PID/tiempos/rutas saneadas. Hasta 5 min de observación del comando dentro de la cota, con cancelación y traza guardada. No repetir esperas ciegas. |
| W2 | Una corrección soportada elegida por la evidencia; depende W1. | 30 min | Identificar causa corregible o dependencia externa. Aplicar solo el cambio justificado y reversible; conservar antes/después. Si no hay evidencia o reparación soportada, detener sin cargar. |
| W3 | Cualificar sandbox y estabilidad; depende W2. | 15 min | Lectura/escritura propias, rechazo ajeno por todos los canales disponibles, protección del runtime y red con control positivo. Dos arranques secuenciales sin auxiliares huérfanos, sin reproducir el placeholder. Fallo: R. |
| L | Carga A/B y accesos aislados, catálogo y captura; depende W3. | 15 min | Gestor oficial con planes frescos, mismos ZIP fijados, seis skills LKS más sistema equivalente, ninguna instrucción ajena activa. Revalidar política final tras carga y antes de cada caso. Si no, R. |
| A | S1 real en CLI interactivo nuevo; depende L. | 15 min | Captura desde envío del prompt/arranque, recorrido y prueba reales, evidencia y turno cerrado. No evaluar ahorro para decidir ejecutar B. |
| B | Revalidación de transición y S1 nuevo; depende A completo y sin contaminación. | 15 min | Igual encargo y obligaciones, sin transferir solución de A, captura completa. Si no cierra, pareja inconclusa; sin repetir hasta pasar. |
| R | Recuperación desde cualquier efecto/fallo. | **15 min protegidos** | Parada de procesos/registro de traza, retirada oficial de plugin/catálogos, logout de archivos reales, configuración restituida y residual clasificado; incidente si un efecto queda desconocido. |
| C | Comparar, verificar y presentar; depende R. | **10 min protegidos** | Estado de H2, garantías, recuperación y ahorro separados; métricas recuperables y limitaciones. |
| RC | Contingencia común. | **20 min protegidos** | Solo recuperación, cierre o una corrección de configuración demostrada dentro de las tareas; no más casos, variantes o diagnóstico sin criterio. |

Suma base: **160 min**, contingencia **20**, total **180**. Los casos reciben
15 min frente a diez anteriores; recuperación/informe reciben 25 min frente a ocho.
Son límites con holgura, no tiempos observados de éxito de H2. Desde que empiece A
deben quedar al menos **55 min base** para A/B/R/C y la contingencia intacta; antes
de B, **40 min base** y esa contingencia. Si el diagnóstico consume sus cotas sin
reparar, no se empiezan casos con el tiempo sobrante de sus reservas.

## Qué investigar y cómo elegir la solución

La evidencia actual no demuestra un fallo del plugin ni una causa concreta del
refresco. El ensayo mínimo mezcló aproximadamente 25 s de aprovisionamiento con
unos 20 s de refresco; no valida una comparación de diez frente a 109 reglas.
`auth.json` fue un directorio vacío y nunca un archivo de credenciales observado.

En W1 usar logs del producto y una traza Windows acotada para distinguir CPU en
cálculo/recorrido, I/O de permisos/rutas, reparse points, espera o restricción de
política. WPR permite capturar CPU, hilos y disco; antes de usarlo comprobar presencia,
permisos y sesiones ETW ajenas. No detener trazas de otros. Si faltan herramientas,
instalarlas o añadirlas no es un paso automático: consumiría la cota y necesita
alcance autorizado. Las trazas pueden contener rutas/procesos privados; conservarlas
locales y compartir solo una extracción saneada autorizada.
[Diagnóstico básico con WPR](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/recording-for-basic-system-diagnosis).

W2 elegirá **una** vía según la evidencia:

- Configuración/objetivos de ACL: comprobar tipo y existencia antes de generar
  reglas. Para una prueba sin login, usar un directorio de canario existente;
  no crear un auth.json ficticio, ni denegar ese archivo inexistente y asumir que
  el cliente lo tratará como archivo. En el caso autenticado, fijar protección
  sobre el archivo real antes del preflight definitivo. No reducir las garantías.
- Estado nativo o política de Windows: intervención soportada por el responsable
  del host, con baseline y recuperación adecuadas a su alcance. No borrar cuentas,
  reglas, cachés ni marcadores privados para forzar un resultado. La retirada del
  placeholder previamente rechazada sigue fuera de ejecución mientras no se resuelva
  el bloqueo por un canal autorizado; conservarlo es compatible con perfiles retirados.
- Defecto del cliente o capacidad del sistema: presentar evidencia a soporte o
  proponer un cliente/host corregido. No parchear LKS-SDD para compensarlo ni
  incorporar un binario distinto silenciosamente. Cambiar cliente exige validar
  configuración y volver a medir A/B en el mismo cliente nuevo.

Hay una pista adicional de compatibilidad: la build observada es **26200.8457**;
la documentación oficial sitúa MXC en 25H2 a partir de **26200.9278**. Es coherente
con el MXC no disponible del log, pero **no explica el atasco de elevated** ni
demuestra que una actualización sea la solución. Actualizar Windows, descargar y
reiniciar requiere decisión separada y una ventana de mantenimiento; no se promete
que quepa en W2. Si la reparación requiere ese trabajo o respuesta de proveedor,
se detiene la vía local y se preserva el saldo para la continuación.
[Windows sandbox y compatibilidad](https://learn.chatgpt.com/docs/windows/windows-sandbox).

No elegir `unelevated` como atajo porque no conserva las denegaciones requeridas.
Un Windows de referencia ya operativo puede ser alternativa, si se proporciona
y autoriza: cualificarlo y ejecutar la pareja completa allí, informando que no
acredita reparación ni aceptación del equipo actual. WSL u otro sistema exigirían
revisión del protocolo y no sustituirían evidencia Windows; no están en la ruta base.

## Garantías, medición y cierre

El controlador de tiempo debe separar cota de cada operación y cota del bloque,
reservar R/C antes de lanzar una reproducción y registrar salidas/efectos antes de
reintentar. Clasificar archivo/directorio/enlace antes de tratar autenticación;
verificar credenciales sin leer su contenido. Ante rechazo automático, conservar
y parar esa acción; no probar mecanismos equivalentes. La contención ya realizada
no equivale a restauración completa del estado nativo.

Mantener gpt-6.1-sol/xhigh y la superficie Codex CLI interactiva. Versiones cliente,
política, herramientas y entorno equivalentes entre A/B; toda diferencia declarada.
Inspección preparatoria separada, ningún cuerpo aplicable precargado al agente del
caso fuera de W1. Capturar el contexto anunciado y lecturas observadas en sesión,
sin pedir autodeclaraciones como prueba independiente ni exportar secretos.

H2/AC-34: ambos recorridos completos, E0 sin pérdidas conocidas ni defectos materiales,
B_out baja ≥10 % y ≥8.192 bytes, N_admin baja ≥1, B_flow no crece y cero nuevas
confirmaciones redundantes. Costes de bootstrap, errores y diagnóstico requerido
pertenecen a W1. Tokens solo reales de ventanas completas; ausentes = no medidos.
El cierre de la pareja puede rechazar ahorro; no se repite hasta obtenerlo.
Integración, aceptación funcional y percepción humana siguen separadas.

Se consumen las dos plazas H2 ya reservadas, incluso si un caso abierto falla.
La cualificación del host se registra separada sin ocultar tiempo; no son intentos
de tarea mientras no se inicie S1. Una segunda pareja o cambio de host/cliente tras
abrir casos requiere reconciliar el máximo de 48 antes de admitirla.

El resultado final será: reparación y H2 acreditados; pareja completada con ahorro
rechazado; o incidencia externa y H2 inconcluso. No se garantiza reparación por
aprobar tres horas. Si aparece dependencia externa, no gastar las reservas de
recuperación ni prometer fecha; conservar traspaso saneado y decisiones pendientes.

## Decisiones para una futura ejecución

Validar +3 h hasta máximo global 15 h y alcance exclusivo Windows/H2. Confirmar un
responsable con autoridad sobre Windows para trazas o reparación; el usuario puede
serlo, pero no se infiere por accesos anteriores. Autorizar por separado cualquier
actualización/reinicio o envío de diagnóstico a terceros cuando exista propuesta
concreta. No hace falta repetir modelo, prioridades, seis mejoras ni cuestionarios
humanos. Accesos aislados solo en L, después de cualificar el host.

Presupuesto y comprobación documental en `h2-min/windows-repair-plan-budget.json`.
La planificación actual no autoriza ni ejecuta las tareas de esta tabla.
