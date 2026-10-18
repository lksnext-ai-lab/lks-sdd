# H2 — Carga resuelta; aislamiento sin acreditar; casos sin ejecutar

Fecha: 2026-10-16. Continuación autorizada dentro del saldo de los **45 minutos
acumulados de H2**, sin modificar el plugin. Sustituye el estado operativo de
[la primera ejecución](RESULTS-H2.md), que se conserva como antecedente.
**AC-34 sigue pendiente. V4-06 no se inicia.**

## Resultado comprobado

| Aspecto | Resultado | Alcance de la evidencia |
|---|---|---|
| Fallo gestor/Codex | Resuelto para A y B. | Instalación oficial completada en ambos perfiles y retirada posterior verificada. |
| Contenido cargado | Seis skills por brazo; contenido contrastado por el gestor con el paquete exacto. | A publicado y B provisional conservan su identidad y sus bytes; compartir versión 3.4.3 no los hace equivalentes. |
| Consumidores | Preparados desde el mismo estado inicial, con sus runtimes correspondientes. | `app.py` sigue devolviendo Adios en ambos; no se ejecutó el encargo H2. |
| Aislamiento nativo de Windows | No acreditado. | La inicialización y las sondas no produjeron una prueba completa de lectura propia permitida y ajena denegada. |
| Pareja AB / ahorro / garantías funcionales | No ejecutados ni medidos. | No hay W1/W2 comparables, llamadas a modelo de los casos, resultado Hola o cierre técnico H2. |
| Recuperación de perfiles | Comprobada en el alcance descrito abajo. | Plugin/catálogo retirados, autenticación temporal ausente y configuración habitual conservada. |

## Causa del fallo de carga y solución aplicada

El catálogo temporal apuntaba a una copia del plugin mediante una ruta absoluta
externa. El CLI enumeraba el catálogo, pero `plugin/read` del app-server respondía
que no encontraba `lks-sdd` dentro de ese marketplace. La misma consulta con el
marketplace reproducible y su entrada relativa `./plugins/lks-sdd` sí resolvió el
plugin. Es un defecto del montaje de la prueba; no demuestra un fallo del runtime
LKS-SDD ni justifica modificar el gestor o el plugin.

Se sustituyó el montaje por los bundles marketplace existentes. Antes de instalar
se contrastó el núcleo de cada bundle con su ZIP de plugin fijado. Se generaron
planes nuevos autorizados, separados de los antiguos planes de solo revisión, y se
aplicaron mediante el gestor estable en modo Recovery y el CODEX_HOME de cada brazo.
El gestor completó ambas instalaciones y comprobó el contenido de la caché nativa.
No se editaron manualmente esas cachés ni el código del gestor o del plugin.

| Brazo | Bundle marketplace canónico conservado | Instalación completada y después revertida |
|---|---|---|
| A | `C:\AI-Workspace\extensions\lks-sdd\packages\3.4.3\3401a5958d8dce0b` | `8e21d392c7414bdb9a57df8c33297314` |
| B | `C:\AI-Workspace\extensions\lks-sdd\packages\3.4.3\330113f5741eba24` | `9d10ee639c2b48c6a8cf452d9567ff32` |

Los SHA256 de los ZIP fijados siguen siendo:

- A: `d528d56a4ba0cdd68e851ca77ba6cf28e567bc2bc8b553d01524b833b5ca5a34`.
- B: `fc3305217a438e9a58e04250dbdbe48dddd115769980326f3be023f1ecbe8096`.

## Bloqueo posterior y revisión crítica

P01 completó ambos accesos y confirmó haber atendido las solicitudes de permisos
o administrador. Esto acredita su intervención, no la finalización del aislamiento.
Los registros locales muestran MXC no disponible, selección del sandbox elevado y
aprovisionamiento inicial realizado; después quedaron procesos de refresco activos.
`windowsSandbox/setupStart` confirmó el inicio, sin observarse su notificación final
satisfactoria. Las sondas no devolvieron la pareja completa de resultados exigida.
No se concluye que faltara una aprobación del usuario ni se atribuye el bloqueo a
las rutas largas: la causa interna del refresco sigue sin determinarse.

La preparación tuvo errores que deben conservarse y corregirse antes de repetir:

1. El primer perfil mínimo fue rechazado porque este cliente exige lectura efectiva
   de `:root` para ese sandbox. La configuración posterior tampoco llegó a probarse.
2. Varios límites externos terminaron la espera del proceso invocador, pero dejaron
   auxiliares de inicialización trabajando. Se acumularon refrescos. Es un defecto
   de la preparación de esta prueba: un timeout no garantiza cancelación del árbol.
   Se detuvieron únicamente los procesos cuyo payload identificaba los perfiles H2.
3. Las reglas propuestas incluyen denegaciones de directorios padres con permisos
   más concretos de hijos. Su efecto real en esta implementación no está validado;
   no deben reutilizarse como aislamiento demostrado. Conviene ensayar primero
   reglas sin solapamientos y una sola inicialización cada vez.
4. Los perfiles también contienen material de plugins de la cuenta. Desactivar
   opciones en configuración y obtener seis skills LKS no acredita exclusividad de
   instrucciones. Falta observar qué instrucciones descubre una sesión nueva.

Al quedar sin margen para ejecutar A y B completos manteniendo la recuperación y
el reporte protegidos, se detuvo la preparación antes del primer mensaje de caso.
No se sustituyó la prueba por un recorrido programado ni se relajó el aislamiento.

## Recuperación y sus límites

- Rollback oficial del plugin A y B, seguido del rollback de cada catálogo correcto:
  `304fc649512544809064e91418dbf464` y `b0c8e071f7134979bac6316e81c43f98`.
  Las cuatro operaciones terminaron correctamente; las entradas LKS de instalación
  y marketplace están ausentes de ambas configuraciones temporales.
- Logout oficial limitado al almacenamiento de archivo de cada CODEX_HOME;
  `auth.json` ausente en ambos. No se copiaron ni exportaron credenciales.
- Detención de las sondas y auxiliares propios identificados. El servicio nativo
  compartido de Codex y los procesos ajenos se preservaron.
- Configuración habitual: SHA256 igual al capturado antes de la carga. No se afirma
  restauración completa del sistema operativo a partir de esa única huella.
- La inicialización de Windows sí creó o configuró recursos nativos. Su estado
  residual, registros y perfiles se conservan; no se borraron cuentas, reglas,
  ACL ni secretos internos del producto. **No se acredita reversión del
  aprovisionamiento nativo de Windows.** Hay que revisar ese estado antes de otra
  inicialización; la recuperación de plugin/catálogo/autenticación es distinta.
- Los paquetes inmutables, referencias del estudio, consumidores y evidencia se
  conservan por la política de soporte. No constituyen una instalación activa.

## Integridad, presupuesto y conclusiones

La validación estática del contrato del plugin ha pasado. Los cinco archivos
congelados del protocolo conservan sus hashes. Se contrastaron 231 archivos
protegidos de fuentes con el paquete B: 227 idénticos byte a byte y cuatro con
diferencias únicamente de finales de línea, sin diferencias de texto. No se
modificaron fuentes, contratos, skills o tests del plugin en este bloque.
No se repitieron la batería de release, el ensayo Windows ni las garantías de tarea:
esta actuación operativa y documental no los sustituye.

Se cargan preparación, autenticación, fallos, esperas, recuperación y reporte. El
turno anterior consumió **795,958 s**, dejando **1.904,042 s** de los 45 minutos.
El inicio real de esta continuación, registrado a las **20:04:26,003 UTC**, corrige
la estimación inicial de 20:04:30; el corte es **20:36:10,045 UTC**. No se reinicia la
reserva ni se vuelve a descontar la suspensión histórica. El ledger enlazado abajo
registra el consumo al emitir el resultado y deberá sustituir la parte abierta por
la duración final del turno cuando esta exista.

Snapshot de presupuesto a las **20:28:41 UTC**: continuación **24.27 min**; H2 acumulado **37.53/45 min**; saldo de esa reserva **7.47 min**. Cargo global conocido ajustado **11.1285/12 h**, con **52.29 min** globales al snapshot. El cierre y el reporte posterior al snapshot también se cargarán; estos saldos no son autorizaciones para otro bloque.

**Cero casos completos nuevos**; las dos plazas H2 continúan reservadas dentro de
45/48 cargos conocidos y reservas. Permanecen las seis mejoras, la cobertura, las
12 horas globales y Copilot al final. No se certifica que el resto de la release
quepa en el saldo restante.

El arreglo de carga queda demostrado y es reutilizable. H2 y AC-34 permanecen
inconclusos: no hay ahorro acreditado ni evidencia nueva contra la funcionalidad
del plugin. Antes de reanudar hace falta resolver y probar el aislamiento de
Windows fuera de W1, comprobar la exclusividad de instrucciones y reservar la
pareja completa más recuperación dentro del saldo real. No se abre otra sesión
ni se solicita de nuevo autenticación en este bloque.

Evidencia privada conservada en
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\h2-plan\continuation`:
`rpc-explicit-read.json`, `rpc-original-relative-marketplace.json`, recibos por
brazo de instalación/rollback, `fixture-results.json`, sondas, resultados de parada,
`recovery-result.json`, `frozen-input-validation.json` y `resource-ledger.json`.
Los perfiles pueden contener estado interno sensible del producto: no forman parte
de un paquete distribuible del reporte.

Plan posterior de preparación: [aislamiento, instrucciones y recuperación H2 0.1](H2-ISOLATION-PLAN.md). Propuesto, sin ejecutar; requiere validar la reasignación local dentro del máximo global.
