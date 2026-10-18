# H2 0.2 — Preflight inconcluso, perfiles recuperados, cero casos

Fecha: 2026-10-16, Europe/Madrid. Ejecución y reasignación 38+3 min autorizadas
por P01. **H2 no se ha completado; AC-34 pendiente.** No se modifica el plugin
ni se inicia V4-06. El bloque se detuvo en la puerta P2, conforme al plan validado.

## Resultados por garantía

| Control | Evidencia y resultado |
|---|---|
| Admisión | 37 turnos cerrados, cargo conciliado 40.678,422956 s; saldo al inicio **2.521,577044 s = 42,0263 min**, suficiente para 38+3 min. |
| Carga A/B | Ambos paquetes exactos instalados mediante planes nuevos del gestor Recovery; verificaciones nativas completadas. Después se revirtieron. |
| Configuración final | `default_permissions=h2`, sin `sandbox_mode` antiguo efectivo; consulta por cwd con capas. No se declararon MCP ni hooks. |
| Catálogo de instrucciones | A/B: **11 skills habilitadas**, las seis LKS y cinco de sistema; cero errores. Las 32 identidades remotas ajenas se deshabilitaron solo en cada perfil temporal. No se borraron cachés ni se modificó la cuenta compartida. |
| Procedencia | Manifiestos con ruta, descripción, alcance, habilitación y SHA256 del cuerpo. Los cuerpos de las cinco skills del sistema coinciden. AGENTS del consumidor identificado y dentro del límite de 32 KiB; sin AGENTS global en esos CODEX_HOME. |
| Instrucciones de casos reales | **No observadas**: no hubo arranque ni primer mensaje de un caso. El catálogo preparatorio no se presenta como prueba de carga o lectura por un agente medido. |
| Aislamiento | **No acreditado.** La única sonda nativa A terminó su espera a los 60 s sin stdout/stderr. El refresco elevado seguía activo. No se abrió B ni se repitió setup. |
| Red | Control positivo del listener propio pasado desde host. La sonda de sandbox no llegó a ejecutar su comprobación; no se declara denegación de red probada. Listener cerrado. |
| Función y garantías de tarea | **No ejecutadas en H2.** Ambos app.py siguen iguales, devolviendo Adios. Sin prueba Hola, firma, cierre, integración o aceptación H2. |
| Ahorro | B_in/B_out/B_flow/N_admin/tokens **no medidos**; cero llamadas de modelo de caso y cero plazas completas nuevas. |

## Incidencia de Windows y corte aplicado

La configuración definitiva se preparó después de la carga. Se sustituyeron las
denegaciones de padres con hijos permitidos por rutas concretas disjuntas. El
cliente seleccionó `elevated` y registró MXC no disponible. Aun así, el refresco del
sandbox no devolvió un resultado dentro de la cota de 60 s.

Se detuvo el proceso invocador al vencer la espera; después se identificó el auxiliar
por su payload con CODEX_HOME del estudio y se detuvo **PID 6652**, sin terminar el
servicio compartido ni procesos ajenos. Se comprobó ausencia de inicializadores
pendientes. No se atribuye la causa a falta de aprobación humana, rutas largas,
contenido del plugin o una implementación concreta de ACL: no hay evidencia para
esa atribución. El log confirma un refresco nativo sin finalización observada.

El fallo invalida la admisión del primer caso. El saldo restante no se usó para
iniciar otro diagnóstico o reintento fuera del plan. Esto no es una medición de
rendimiento de LKS-SDD ni una regresión funcional demostrada.

## Recuperación comprobada y estado residual

| Brazo | Operación de instalación revertida | Operación de catálogo revertida |
|---|---|---|
| A | `6d2c718657e44f07a77217f1d6c041a5` | `ba9c037576cf4ef4baf7b0f739efc637` |
| B | `b614eacfd79f4273892696f79fb77a85` | `03456acce9e04362a48b761a6e4c9a37` |

Las cuatro operaciones terminaron con resultado correcto. Logout oficial en ambos
almacenamientos de archivo, `auth.json` ausente, y ninguna instalación/catalogación
LKS activa del estudio. Configuraciones temporales restauradas a sus hashes exactos
de entrada; canario propio retirado. Configuración habitual sin cambios.

Las seis ACL raíz muestreadas coinciden con P0. La metadata de cuentas nativas y
reglas de firewall relevantes también coincide con la baseline de este bloque.
Se conservan las cuentas Offline/Online, reglas y marcadores previos del producto.
**Esto no acredita reversión recursiva de ACL ni restauración de Windows al estado
anterior al estudio.** No existe una baseline completa para afirmarlo. No se
retiraron recursos compartidos ni se restablecieron permisos generales a ciegas.

231 archivos de fuentes protegidas del plugin coinciden byte a byte con la captura
de entrada. Se conservan paquetes inmutables, referencias, consumidores, solicitudes,
configuraciones y recibos privados. No son una candidata activa.

## Costes, errores conservados y conclusión

Se cargan preparación, accesos, cargas, esperas, errores, cancelación, recuperación
y reporte. La contingencia no se ha utilizado. El ledger contiene el snapshot del
bloque abierto y se sustituirá por su duración final al cerrar, sin sumarlos dos
veces ni volver a descontar reposo histórico. Los 38 minutos no se reinician por
el fallo. La cuenta de intentos conocida/reservada sigue 45/48, incluidas las dos
plazas H2 no abiertas. Se conservan seis mejoras, cobertura y Copilot al final;
el saldo no acredita viabilidad integral del resto de 4.0.

Se conservan tres errores de preparación: escape de rutas en una sustitución TOML
rechazada antes de escribir; literal Python de la sonda rechazado antes de ejecutar;
y una discrepancia de finales de línea al restaurar configuración, detectada por
hash y corregida hasta recuperar los bytes exactos. Sus costes no se excluyen.

**Conclusión:** carga e instrucciones preparatorias comprobadas; aislamiento y
sesiones H2 no acreditados. Recuperación de perfiles y comparaciones acotadas
comprobadas; recuperación completa del estado nativo no acreditada. AC-34 sigue
pendiente y no hay ahorro nuevo que presentar. Una continuación necesita resolver
la incidencia del cliente nativo y nueva admisión con el saldo real, sin repetir
autenticaciones o cargas a ciegas. No se inicia esa continuación en este bloque.

Evidencia privada:
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\h2-plan\h2-02`.
Incluye `results.json`, `resource-ledger.json`, `recovery-result.json`,
`isolation-probe-results.json`, manifiestos/configuración por brazo y recibos del
gestor. `diagnostic-sanitized.json` y `continuation-prompt.txt` permiten continuar
sin exportar perfiles, autenticación o secretos internos del producto.
