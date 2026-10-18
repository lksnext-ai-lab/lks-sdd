# H2 — Plan de aislamiento Windows, instrucciones y recuperación

**Resultado vigente:** [ejecución H2 0.2: corte P2, perfiles recuperados y cero casos](RESULTS-H2-02.md). AC-34 pendiente; no se inicia V4-06. Los estados anteriores se conservan como antecedentes.

Fecha: 2026-10-16, Europe/Madrid. Revisión **0.2 propuesta tras revisión crítica**. Complementa H2 0.3 y
el plan funcional 0.4; no modifica las seis mejoras ni el protocolo 1.0 congelado.
Preparar este documento no autoriza su ejecución. No se modifica el plugin ni se
abren casos, sesiones de inspección, instalaciones o inicializaciones en este bloque.

## Dictamen y presupuesto conciliado

La [revisión crítica de 0.1](REVIEW-H2-ISOLATION-0.1.md) confirma el encaje
aritmético, pero **no acredita todavía que el bloqueo de Windows pueda resolverse**.
Completar H2 significa obtener ambos recorridos comparables y recuperar sus efectos;
no garantiza superar los umbrales de ahorro. No se exige que el resultado sea favorable.

El turno de preparación 0.1 cerró en **330,674 s**, sustituyendo su reserva de 360 s.
H2 y su preparación acumulan **2.626,683 s = 43,77805 min** antes de esta revisión;
quedan **73,317 s** de los 45 min locales originales. Esta revisión tiene cota **4 min**
y también se carga; la ampliación local propuesta sigue pendiente, sin reiniciar bolsas.

La cuenta vigente contiene **36 turnos cerrados**, 51.340,945 s de calendario menos
10.903,592044 s de reposo profundo, descontados una sola vez: **40.437,352956 s**
cargados. Saldo global al comenzar esta revisión: **2.762,647044 s = 46,0441174 min**.

| Concepto futuro desde ese saldo | Reserva |
|---|---:|
| Esta revisión, incluidos documento y cierre | 4 min |
| Ejecución futura completa | 38 min |
| Margen común protegido para contingencia de recuperación/cierre | 3 min |
| Margen sin asignar tras esas reservas | 1,0441174 min |

Comprobación: 40.437,352956 + 240 + 2.280 + 180 = **43.137,352956 s = 11,982598 h**,
inferior a 43.200 s (12 h) por 62,647044 s. El margen de 3 min no permite prolongar
casos ni repetirlos. Sin consumirlo, quedarían 4,0441174 min tras todas las otras cotas.
La duración real de este turno reemplazará los 240 s al cerrar; nunca se suman ambos.
Antes de T0 recontar turnos posteriores, incluido el de validación si consume trabajo.
Admisión: saldo global ≥**41 min** para ejecución de 38 más margen de 3. Si no,
no instalar ni abrir casos. No presupuestar otros turnos de diagnóstico fuera del bloque.

La cota local H2 propuesta pasa a **85,77805 min acumulados** incluyendo esta
revisión completa y los 38 min futuros: **+40,77805 min sobre los 45 originales**.
Si los 3 min comunes se consumen en recuperar/cerrar H2, el máximo local sería
**88,77805 min**, extensión máxima **43,77805 min**. Es una reasignación explícita
pendiente de validación; se conserva el máximo global de 12 h. La solicitud de
revisión no se interpreta como autorización para instalar, aprovisionar o abrir casos.

Se mantienen las seis mejoras, cobertura, máximos humanos/M6 y Copilot al final.
Las dos plazas H2 ya están incluidas en 45/48 cargos conocidos y reservas; no se
crean otras. La cuenta observada no certifica consumos externos desconocidos ni
viabilidad del resto de 4.0: el margen restante no constituye financiación de esa release.

## Punto de partida: hechos y límites

La [continuación anterior](RESULTS-H2-CONTINUATION.md) resolvió la carga usando
marketplaces reproducibles con rutas relativas. A y B se instalaron, se contrastaron
sus seis skills y se revirtieron. Hoy se ha observado, mediante consultas de lectura:

| Estado | Observado / tratamiento previsto |
|---|---|
| Plugin, catálogo y autenticación temporales | Entradas LKS y `auth.json` ausentes en A/B. Habrá que cargar y autenticar otra vez durante una ejecución autorizada. |
| Consumidores | Se conservan los dos consumidores preparados y el estado inicial. Revalidar antes de usarlos; no se ha ejecutado H2. |
| Windows | Existen las cuentas nativas Offline/Online y marcadores de setup en ambos perfiles. Existen cuatro reglas de firewall con nombres `codex_sandbox_offline_*`. El servicio de Codex es compartido. |
| Inicializadores | No hay proceso `codex-windows-sandbox-setup.exe` activo en la observación actual. No prueba finalización correcta de los refrescos anteriores. |
| ACL y recursos compartidos | No existe una baseline completa anterior al primer aprovisionamiento. No se puede prometer reversión a un Windows prístino ni atribuir cada recurso exclusivamente a H2. |
| Instrucciones en disco | A conserva **32** directorios de plugins remotos en caché; B, **9**. No equivalen a instrucciones disponibles o leídas. |
| Skills del sistema | Cinco por perfil: imagegen, openai-docs, review-agent, skill-creator, skill-installer; hashes iguales entre A/B. |
| AGENTS | Un archivo encontrado en cada cadena de ancestros del consumidor: el AGENTS generado del propio consumidor. No se observó AGENTS global dentro de sus CODEX_HOME. |
| Instrucciones realmente cargadas | No observadas en una sesión H2: no hubo primer mensaje de caso. Queda pendiente verificar descubrimiento efectivo y lecturas. |

Evidencia de lectura: `h2-plan/isolation-plan-observation.json`. Las cuentas, reglas
y marcadores son recursos residuales del producto, no prueba suficiente de aislamiento.

## Secuencia futura y cortes de tiempo

Reloj monotónico desde T0 de una futura ejecución admitida. Todas las cotas incluyen
esperas técnicas, accesos, fallos y comprobaciones. No hay reintentos automáticos.

| ID | Tarea y dependencia | Cota / corte absoluto | Evidencia para continuar |
|---|---|---|---|
| P0 | Admisión, baseline residual, supervisor y captura; inicio. | 3 min / T+3 | Saldo ≥41 min, huellas fijadas, receta de cancelación preparada con identificación de auxiliares propios y recibos previos de parada; captura probada con datos sintéticos, sin modelo ni solución S1. Si no cabe, R. |
| P1 | Carga/autenticación, política definitiva y catálogo; depende de P0. | 4 min / T+7 | Planes nuevos y recibos oficiales, paquetes exactos, configuración efectiva por cwd y capas administradas, red/canales auxiliares controlados, manifiesto de instrucciones de ambos perfiles. Toda carga y ajuste se hace antes de las sondas definitivas. |
| P2 | Setup y prueba de la configuración final; depende de P1. | 3 min / T+10 | Setup secuencial A/B, una llamada por perfil, ≤60 s cada una; finalización y sondas positivas/negativas correctas, A revalidado después de B. Ningún auxiliar propio pendiente. Falta de prueba en cualquier canal disponible: R. |
| A | S1 con prompt inicial y proceso nuevo; depende de P2. | 10 min / T+20 | W1 completa, cierre del turno, prueba real y evidencia de garantías. No se evalúa el ahorro para decidir si ejecutar B. |
| B | Transición, revalidación y S1 nuevo; depende de A cerrado y sin pérdida que invalide la pareja. | 10 min / T+30 | Control de aislamiento/instrucciones repetido, sin datos de A entregados; mismo prompt y captura íntegra. La transición se paga dentro de esta cota, nunca fuera del bloque. |
| R | Recuperación desde cualquier efecto, fallo o corte. | **6 min protegidos** / T+36 como máximo | Detención confirmada de auxiliares propios, rollback y logout, comparación de baseline y clasificación residual. Si algo es incierto, usar solo la contingencia común y registrar incidencia. |
| C | Comparación y resultado; depende de R. | **2 min protegidos** / T+38 | Dictamen de ejecución, comparabilidad, garantías, recuperación y ahorro por separado. Informe preparado en P0 para completar sin rehacer el análisis. |

Las cotas no son tiempos de servicio demostrados. Al admitir A deben quedar **28 min**
del bloque y el margen común de 3 min; al admitir B, **18 min** y ese margen intacto.
Desde T+30 se prohíbe trabajo de caso. Ante un fallo temprano, R/C empiezan antes;
los cortes no obligan a seguir consumiendo. R incluye cancelar los procesos del caso.
La contingencia es solo recuperación/cierre, no diagnóstico adicional o segundo intento.
Si no puede cancelarse un auxiliar propio elevado, no lanzar otro: R queda incompleta.
No se garantiza concluir H2 con éxito por haberlo admitido; se garantiza el criterio
para parar dentro de presupuesto y reportar el límite sin declarar controles superados.

## Política y comprobación de aislamiento

Mantener el cliente exacto **0.163.0-alpha.10.2**, modelo **gpt-6.1-sol/xhigh**,
Windows nativo, procesos nuevos `--no-daemon` y CODEX_HOME/TEMP/TMP propios. No
actualizar cliente, cambiar a WSL, incorporar MCP ni cambiar el modelo para salvar
el experimento. MXC se observó no disponible; no se presupone su disponibilidad.
La vía propuesta sigue siendo `elevated`. `unelevated` no satisface la denegación
de lectura requerida. [Documentación oficial de Windows](https://learn.chatgpt.com/docs/windows/windows-sandbox).

P2 debe resolver la configuración efectiva desde el directorio real de cada
consumidor, incluidas capas administradas. No mezclar `sandbox_mode`/`--sandbox`
con los perfiles de permisos. La precedencia de esas opciones puede anular el
perfil. [Documentación oficial de permisos](https://learn.chatgpt.com/docs/permissions).

La política operativa propuesta tendrá lectura base de `:root` porque este cliente
la exigió, escritura solo en el consumidor propio y temporales propios, y red de
subprocesos deshabilitada. Eso **no constituye aislamiento total de todo el disco**:
se exige aislar los límites concretos de la prueba. Debe prohibir:

- El otro brazo completo, sus perfiles, temporales, resultados y consumidor.
- El repositorio fuente y los paquetes de la otra variante, y los informes de
  mantenimiento que puedan transferir resultados/soluciones.
- Perfiles habituales de Codex/agents, sus instrucciones y credenciales; archivos
  `auth.json` y secretos internos del perfil propio para los comandos del caso.
- Escritura en runtime, skills, paquetes/caché de instrucciones y `.git`; el agente
  puede modificar documentación/evidencia de su consumidor conforme al contrato.

Sustituir denegaciones amplias de padres que contienen destinos permitidos por
rutas concretas sin solapamientos: no denegar todo `h2-plan` ni todo `extensions`
y pretender reabrir hijos necesarios. No añadir globs recursivos o permisos sobre
todo el perfil de usuario para corregir un rechazo. Resolver rutas reales/enlaces
antes de admitirlas. No cambiar los permisos de los recursos compartidos sin
atribución y recuperación demostrables. Si el cliente no puede aplicar esta matriz,
P2 falla; no degradar la garantía.

Dos puertas independientes: las sondas del sandbox controlan comandos y lecturas,
pero no prueban por sí solas el descubrimiento que hace el host antes de ejecutarlos.
La puerta de instrucciones exige procedencia/configuración y evidencia de arranque
del mismo TUI; un listado de skills no sustituye esa evidencia.

Sondas sin modelo y sin resolver greeting(), con canarios sintéticos y códigos de
salida: lectura propia; escritura/retirada de un canario en consumidor y temporal
propios; lectura de las instrucciones/runtime propios; lectura y escritura del otro
brazo denegadas; escritura en runtime/.git y lectura de instrucciones/credenciales
habituales denegadas. Incluir rutas originales y alias resueltos de paquetes/ZIP,
fuentes y resultados del otro brazo; un inventario incompleto bloquea P2. Nunca leer credenciales reales: usar canario protegido con
la misma política. Comprobar tanto shell como el mecanismo directo de archivos
cuando exista en el host, usando interfaces disponibles sin turno de modelo.
Comprobar red con un listener efímero propio, datos sintéticos, conexión permitida
desde el host como control positivo y rechazo desde sandbox. Crear/cerrar el listener
dentro de P0/P2 y R. Un fallo de DNS o de un destino no disponible no demuestra
denegación. Si una prueba equivalente documentada no cabe, P2 falla; la conectividad del host con el modelo se mantiene
separada. Una denegación de acceso a credenciales no significa que
el proceso host no pueda autenticarse por su vía oficial.

Repetir las sondas en A tras aprovisionar B y antes de sus casos: las cuentas
Windows son compartidas y no se ha demostrado independencia entre refrescos.
Solo una inicialización activa cada vez. Para cada brazo, una invocación soportada
de setup como máximo, hasta 60 s; guardar respuesta **y finalización**, no solo
`started=true`. Usar la API ya soportada por este binario, con su esquema local;
no usar `codex sandbox setup` si el help de ese cliente no lo ofrece.

Un supervisor acotado deberá conservar PID, hora de creación, padre y perfil
identificado. Ante timeout, cancelar y esperar la salida de los auxiliares propios,
incluidos los elevados; matar el padre no basta. Si no puede confirmar su salida,
no iniciar otro. No terminar el servicio compartido ni procesos de otras sesiones.
La preparación del supervisor forma parte de P0: si no cabe o no es verificable,
el plan termina en recuperación. No se prescribe un bucle de reparación.

## Instrucciones: almacenadas, disponibles y leídas

P1 generará un manifiesto por brazo con cuatro columnas: origen/ruta/hash, estado
habilitado, anunciado a la sesión y lectura de cuerpo observada. Incluirá capas de
configuración, AGENTS de todos los ancestros y overrides, catálogo de skills, plugins
y reglas del host. No inferir carga a partir de presencia en caché.

Resolver AGENTS global del CODEX_HOME y desde raíz Git a cwd, prioridad de overrides,
`project_doc_fallback_filenames` y `project_doc_max_bytes`: comprobar que no se ha
truncado contenido contractual. La lista anterior de ancestros en disco no prueba
qué archivos incorpora el host. [Descubrimiento oficial de AGENTS](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Usar `config/read` con cwd e includeLayers, y `skills/list` con cwd y forceReload,
conforme al esquema local ya conservado. Estos métodos preparatorios no ejecutan
un turno del caso. Comprobar también herramientas, MCP, hooks y canales auxiliares efectivos:
no añadirlos y no aceptar una vía fuera del límite declarado. Deshabilitar fuentes
ajenas únicamente en cada perfil temporal,
con configuración oficial reversible; no borrar cachés ni deshabilitar plugins de
la cuenta globalmente. Los flags `apps=false`/`remote_plugin=false` anteriores no
se aceptan por sí solos como evidencia de exclusividad.

Aceptar solo las seis skills LKS del brazo correspondiente y las instrucciones
comunes inevitables del sistema, enumeradas y equivalentes. Los cinco cuerpos de
skills del sistema son hoy iguales; verificar también nombre, descripción, versión
y habilitación efectiva. Cualquier plugin ajeno activo o instrucción adicional sin
explicación bloquea P1. Si el host impone una fuente común que no puede retirarse,
documentar su equivalencia y alcance; no presentarlo como exclusividad LKS absoluta.
No corregir la asimetría copiando cachés de A a B.

La inspección previa la realiza mantenimiento, en un contexto separado que no se
reutiliza como sesión medida. Los agentes A/B no reciben bodies, análisis, guías de
solución ni el historial de esta conversación fuera de W1. Al abrir cada caso se
registra el contexto/catálogo que el host exponga y las lecturas realmente observadas.
No pedir al agente que repita su contexto para certificarlo: una declaración no
es una prueba independiente y contaminaría W1. Usar logs TUI/rollout y contexto
que el producto registre, sin exportar secretos; registrar también límites de
observabilidad de instrucciones internas del producto. Si no permite observar un
elemento necesario para establecer equivalencia o exclusión, la puerta falla. Si no puede
demostrarse equivalencia/exclusión suficiente, no acreditar la comparación.

## Ejecución, métricas y garantías congeladas

Reutilizar el estado inicial preservado y las identidades sintéticas aprobadas;
revalidar código, contratos, autoridad, documentos e índice. A usa runtime
`3.4.3-e7183606c626`; B `3.4.3-28c7a5ffc6f2`. Marketplaces relativos correctos:
A `3401a5958d8dce0b`, B `330113f5741eba24`, bajo el área inmutable ya registrada.
Reinstalar solo mediante el gestor verificado Recovery con planes frescos y
precondiciones; no repetir planes revertidos ni cambiar sus journals.

Un S1 por brazo, orden AB, prompt funcional idéntico: devolver Hola con greeting()
sin parámetros y cambio de código limitado a app.py, prueba real y recorrido técnico
autorizado con evidencia. No imponer a A el flujo de B. Conservar el fallo conocido
del renderer A si aparece, junto con su recuperación y coste.

W0 separa preparación del estudio. Activar captura y registrar el envío del prompt
inicial **antes de crear el proceso TUI nuevo que lleva ese prompt**. Así no existe
una sesión medida abierta y leyendo AGENTS fuera de ventana. W1 empieza en ese
envío e incluye el arranque íntegro; es la concreción de la frontera congelada, sin
mover bootstrap a W0. W1
incluye bootstrap, instrucciones, clasificación/configuración necesarias para la
candidata, consultas, errores, recuperación y toda la captura/conservación diagnóstica
exigida. W2 queda dentro de W1; W3 solo extrae y analiza tras el cierre. Una inspección
de mantenimiento no sustituye trabajo que el agente necesite en W1. Antes de A,
validar que la captura puede recuperar stdout/stderr, entradas, entregas y contadores
sin perder las fronteras. Captura insuficiente bloquea la admisión, sin corregir
después mediante estimaciones.

AC-34 exige conjuntamente B_out −10 % y al menos 8.192 bytes, N_admin −1 o más,
B_flow sin crecimiento, cero confirmaciones redundantes nuevas y E0 sin pérdidas
conocidas ni defectos materiales abiertos. Probar Hola y firma sin parámetros,
revisar diff de código y conservar evidencia/autoridad/guardas/verificación/cierre.
Integración y aceptación funcional siguen separadas. Tokens solo de W1 cerrada,
comparables y completos; si faltan, no medidos. No convertir bytes a tokens.
No repetir hasta obtener éxito; todo fallo cuenta en tiempo y, al abrir un caso,
en la plaza correspondiente aunque no termine. La percepción humana sigue diferida.

## Recuperación y estado residual de salida

En P0 guardar una baseline acotada de la configuración habitual y temporal,
operaciones, cuentas/SID, reglas relevantes y ACL de las rutas del estudio y de los
límites protegidos. No exportar contraseñas, tokens, `.sandbox-secrets`, datos de
cuentas ajenas o el perfil completo. P0 compara con el residual conocido; no lo
rebautiza como estado original de Windows.

R cerrará sesiones propias, cancelará auxiliares propios y verificará su salida;
revertirá primero instalaciones y luego catálogos usando los IDs nuevos y el mismo
CODEX_HOME; hará logout oficial por archivo y comprobará ausencia de auth.json.
Verificará huella habitual y estado de instrucciones activas. Preservará paquetes
referenciados, consumidores y diagnósticos. Una operación incierta se consulta antes
de repetirla. No se borran cachés oficiales, cuentas o reglas compartidas para
simular limpieza.

La recuperación aceptable distingue: (1) perfiles y autenticación recuperados,
(2) cambios propios de esta ejecución restituidos a la baseline P0, y (3) recursos
nativos previos compartidos que se conservan con propietario y motivo. No promete
eliminar todo el aprovisionamiento histórico. Un cambio nuevo desconocido en un
recurso compartido o un auxiliar persistente deja R incompleta e incidencia abierta;
no se acreditará recuperación completa ni H2 conforme si compromete una garantía.
Conservar diagnóstico portable saneado y continuación breve al fallar; sin adjuntar
perfiles, archivos de autenticación o secretos internos.

## Dictamen, decisiones pendientes y aceptación

La reasignación local anterior de 37,2668 min queda sustituida por la cuenta de esta
revisión: máximo 40,77805 min adicionales, o 43,77805 min si se consume toda la
contingencia en H2. Sigue pendiente de validación. No se pide repetir CLI/modelo.
Los accesos retirados y cualquier solicitud de Windows se atienden dentro de P1/P2;
si la espera no cabe, cancelar y recuperar. No inferir que las aprobaciones de P01
anteriores acreditan finalización del setup.

La comprobación documental permite afirmar que **la ruta completa cabe en las 12 h
observadas**, con los supuestos de duración y admisión indicados. **No permite
certificar que Windows superará P2 o que A/B finalizarán en diez minutos.** Esa
viabilidad queda pendiente de evidencia operativa, no de otro ajuste de tabla.
No se compromete una reparación de causa desconocida en tres minutos. Reutilizar
los recibos anteriores; ningún bucle de diagnóstico, cambios de plataforma/modelo,
limpieza general, actualización de cliente o eliminación de garantías para pasar.

Cierre con dos recorridos completos y recuperación acreditada permite un dictamen
H2 positivo o negativo de ahorro. Superar AC-34 requiere además todos sus umbrales.
Si un recorrido o captura queda incompleto, H2 es inconcluso; si se demuestra pérdida
material de garantías, no se disfraza como mera falta de medición. A/B, aislamiento,
instrucciones y recuperación conservan resultados separados. No avanzar a V4-06.

Aceptación documental 0.2: suma 3+4+3+10+10+6+2=38; saldo recalculado con turno
0.1 cerrado; reserva de esta revisión y contingencia sin doble cómputo; configuración
final comprobada después de cargar; evidencia separada de sandbox e instrucciones;
W1 cubre bootstrap; cancelación y residual atribuibles; protocolo/hash/paquetes sin
cambios. Estado y cálculo en `h2-isolation-plan.json` e
`h2-plan/isolation-review-budget.json`. Preparar este plan no ejecuta estos pasos.
