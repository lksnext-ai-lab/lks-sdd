# H2 — Plan de aislamiento Windows, instrucciones y recuperación

Fecha: 2026-10-16, Europe/Madrid. Revisión **0.1 propuesta**. Complementa H2 0.3 y
el plan funcional 0.4; no modifica las seis mejoras ni el protocolo 1.0 congelado.
Preparar este documento no autoriza su ejecución. No se modifica el plugin ni se
abren casos, sesiones de inspección, instalaciones o inicializaciones en este bloque.

## Presupuesto conciliado y condición de viabilidad

El turno de continuación terminó con **1.500,051 s**. Sumado al primer bloque de
795,958 s, H2 consumió **2.296,009 s = 38,2668 min**. Su reserva original de 45 min
tiene **403,991 s = 6,7332 min** libres antes de esta preparación. Sustituye el
snapshot de 37,53 min del informe anterior; no se añade de nuevo aquel snapshot.

Los 35 turnos cerrados suman 51.010,271 s de calendario. Descontando una sola vez
los 10.903,592044 s de reposo profundo ya validados: **40.106,678956 s = 11,140744 h**
cargadas y **51,555351 min** globales antes de este plan. Esta preparación tiene una
cota de **6 min**, que también se carga a H2 y al máximo global. Al reservarla
completa quedan **45,555351 min globales**, sin inventar un nuevo descuento.

**No es viable completar H2 dentro de los 45 min locales originales.** Se propone
reasignar tiempo del saldo global a una ejecución futura de **38 min**, con las
mismas dos plazas H2 ya reservadas. Con la cota completa de preparación, H2 tendría
un máximo acumulado propuesto de **82,2668 min**: ampliación local explícita de
**37,2668 min**, no una nueva bolsa de 45 min. El máximo global sigue en 12 h;
quedarían al menos **7,555351 min comunes** al admitir esos 38 min, si no interviene
otro consumo. La ampliación local es una propuesta pendiente de validación, no una
autorización deducida del saldo global. Al cerrar este turno se sustituirá su reserva
de 6 min por su duración real. Antes de ejecutar se revalidarán ambos saldos.

Esta asignación prioriza H2. **No acredita que las tareas restantes de 4.0 quepan**
en ese margen. Mantiene seis mejoras, cobertura, 48 intentos, máximos humanos/M6 y
Copilot al final; lo que no quepa queda pendiente, sin recortar controles ni declarar
completa la release. Cuenta conocida/reservada: 45/48, incluidas las dos plazas H2.

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

| ID | Tarea y dependencias | Cota / corte acumulado | Criterio de aceptación o salida |
|---|---|---|---|
| I0 | Revalidar saldo, hashes/clientes, diarios y estado residual; sin dependencias. Capturar baseline acotada. | 2 min / T+2 | 38 min disponibles, ampliación local validada, sin auxiliares propios pendientes, baseline de perfiles/ACL/recursos compartidos disponible. Si no, no cargar. |
| I1 | Corregir la política de los perfiles y comprobar sandbox; depende de I0. Aprovisionamiento y sondas secuenciales. | 4 min / T+6 | Finalización nativa acreditada y todas las sondas permitidas/denegadas correctas en A y B. Timeout, resultado desconocido o fallo: cancelar y pasar a R. |
| I2 | Carga oficial, autenticación, catálogo efectivo de instrucciones y captura; depende de I1. | 4 min / T+10 | Paquetes exactos, seis skills LKS por brazo, exclusividad demostrada, herramientas/captura operativas y dos sesiones de caso aún sin iniciar. Si no, R. |
| A | S1 completo en Codex CLI interactivo nuevo; depende de I2. | 10 min / T+20 | Turno cerrado, resultado y prueba real, evidencia/verificación/cierre técnico y conservación diagnóstica exigidos. Si falla o vence cota, no continuar B como si hubiera pareja válida. |
| B | El mismo S1 en sesión nueva; depende de A completo y nueva comprobación de aislamiento/configuración. | 10 min / T+30 | Mismas obligaciones; ninguna transferencia de solución/resultados de A. Cualquier coste adicional entra en W1. |
| R | Recuperar efectos propios; depende de cualquier efecto, éxito o fallo. | **6 min protegidos** / T+36 | Cancelación confirmada, rollback oficial, logout local, huellas verificadas y estado residual clasificado. Incidencia si queda un efecto propio desconocido. |
| C | Extraer métricas y emitir resultado; depende de R y de evidencia disponible. | **2 min protegidos** / T+38 | Resultado AC-34 superado, fallido o inconcluso con razones; sin rellenar huecos ni prolongar el bloque. |

Los intervalos A/B son cotas, no estimaciones demostradas. Si las sesiones necesitan
más tiempo, H2 será inconcluso. No consumir R/C para completar un caso. Al admitir A
deben quedar al menos 28 min; al admitir B, 18 min. Los controles de transición se
pagan con el tiempo liberado de preparación o dentro de la cota B, antes de su W1.
Si no caben, no iniciar B. Si I1 termina antes pero I2 no cabe, recuperar.

## Política y comprobación de aislamiento

Mantener el cliente exacto **0.163.0-alpha.10.2**, modelo **gpt-6.1-sol/xhigh**,
Windows nativo, procesos nuevos `--no-daemon` y CODEX_HOME/TEMP/TMP propios. No
actualizar cliente, cambiar a WSL, incorporar MCP ni cambiar el modelo para salvar
el experimento. MXC se observó no disponible; no se presupone su disponibilidad.
La vía propuesta sigue siendo `elevated`. `unelevated` no satisface la denegación
de lectura requerida. [Documentación oficial de Windows](https://learn.chatgpt.com/docs/windows/windows-sandbox).

I1 debe resolver la configuración efectiva desde el directorio real de cada
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
I1 falla; no degradar la garantía.

Sondas sin modelo y sin resolver greeting(), con canarios sintéticos y códigos de
salida: lectura propia; escritura/retirada de un canario en consumidor y temporal
propios; lectura de las instrucciones/runtime propios; lectura y escritura del otro
brazo denegadas; escritura en runtime/.git y lectura de instrucciones/credenciales
habituales denegadas. Nunca leer credenciales reales: usar canario protegido con
la misma política. Comprobar tanto shell como el mecanismo directo de archivos
cuando exista en el host, usando interfaces disponibles sin turno de modelo.
Comprobar además red de subprocesos denegada mediante un destino de prueba
controlado, sin datos operativos; la conectividad del host con el modelo se mantiene
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
La preparación del supervisor forma parte de I1: si no cabe o no es verificable,
el plan termina en recuperación. No se prescribe un bucle de reparación.

## Instrucciones: almacenadas, disponibles y leídas

I2 generará un manifiesto por brazo con cuatro columnas: origen/ruta/hash, estado
habilitado, anunciado a la sesión y lectura de cuerpo observada. Incluirá capas de
configuración, AGENTS de todos los ancestros y overrides, catálogo de skills, plugins
y reglas del host. No inferir carga a partir de presencia en caché.

Usar `config/read` con cwd e includeLayers, y `skills/list` con cwd y forceReload,
conforme al esquema local ya conservado. Estos métodos preparatorios no ejecutan
un turno del caso. Deshabilitar fuentes ajenas únicamente en cada perfil temporal,
con configuración oficial reversible; no borrar cachés ni deshabilitar plugins de
la cuenta globalmente. Los flags `apps=false`/`remote_plugin=false` anteriores no
se aceptan por sí solos como evidencia de exclusividad.

Aceptar solo las seis skills LKS del brazo correspondiente y las instrucciones
comunes inevitables del sistema, enumeradas y equivalentes. Los cinco cuerpos de
skills del sistema son hoy iguales; verificar también nombre, descripción, versión
y habilitación efectiva. Cualquier plugin ajeno activo o instrucción adicional sin
explicación bloquea I2. Si el host impone una fuente común que no puede retirarse,
documentar su equivalencia y alcance; no presentarlo como exclusividad LKS absoluta.
No corregir la asimetría copiando cachés de A a B.

La inspección previa la realiza mantenimiento, en un contexto separado que no se
reutiliza como sesión medida. Los agentes A/B no reciben bodies, análisis, guías de
solución ni el historial de esta conversación fuera de W1. Al abrir cada caso se
registra el contexto/catálogo que el host exponga y las lecturas realmente observadas.
Si el producto no permite observar un elemento, indicar el límite. Si no puede
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

W0 separa preparación del estudio; W1 empieza en el primer mensaje de cada caso e
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

En I0 guardar una baseline acotada de la configuración habitual y temporal,
operaciones, cuentas/SID, reglas relevantes y ACL de las rutas del estudio y de los
límites protegidos. No exportar contraseñas, tokens, `.sandbox-secrets`, datos de
cuentas ajenas o el perfil completo. I0 compara con el residual conocido; no lo
rebautiza como estado original de Windows.

R cerrará sesiones propias, cancelará auxiliares propios y verificará su salida;
revertirá primero instalaciones y luego catálogos usando los IDs nuevos y el mismo
CODEX_HOME; hará logout oficial por archivo y comprobará ausencia de auth.json.
Verificará huella habitual y estado de instrucciones activas. Preservará paquetes
referenciados, consumidores y diagnósticos. Una operación incierta se consulta antes
de repetirla. No se borran cachés oficiales, cuentas o reglas compartidas para
simular limpieza.

La recuperación aceptable distingue: (1) perfiles y autenticación recuperados,
(2) cambios propios de esta ejecución restituidos a la baseline I0, y (3) recursos
nativos previos compartidos que se conservan con propietario y motivo. No promete
eliminar todo el aprovisionamiento histórico. Un cambio nuevo desconocido en un
recurso compartido o un auxiliar persistente deja R incompleta e incidencia abierta;
no se acreditará recuperación completa ni H2 conforme si compromete una garantía.
Conservar diagnóstico portable saneado y continuación breve al fallar; sin adjuntar
perfiles, archivos de autenticación o secretos internos.

## Decisiones pendientes y validación de este plan

La decisión pendiente es la **reasignación local explícita** de hasta 37,2668 min
desde el saldo global, manteniendo 12 h y sin prometer terminar toda la release.
No hace falta repetir la elección de CLI/modelo ni medir esfuerzo humano. Durante
una futura ejecución harán falta los dos accesos retirados y, si Windows lo exige,
atender una solicitud de administrador; sus tiempos entran en las cotas.

Este plan ofrece una vía acotada y condiciones comprobables; no garantiza que la
causa del refresco pueda resolverse en cuatro minutos. Si no se supera I1/I2 se
recupera y se presenta H2 inconcluso sin ejecutar casos. No cambiar plataforma,
umbrales o cobertura dentro del bloque para hacerlo pasar.

Validación documental: sumar 2+4+4+10+10+6+2=38; dependencias lineales con R desde
cualquier efecto; mismas dos plazas; hashes congelados; separación entre ejecución
propuesta y hechos observados; saldo actualizado en `isolation-plan-budget.json`.
No se modifican fuentes del plugin ni se ejecutan los casos con esta preparación.
