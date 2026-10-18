# Prueba mínima de aislamiento H2

**Cierre operativo posterior:** [perfiles retirados y residual conservado](RESULTS-H2-OPERATIONAL-CLOSURE.md). La incidencia de Windows sigue abierta; H2/AC-34 inconclusos, sin nuevas pruebas, cargas o accesos.

**Revisión posterior vigente:** [incumplimiento de cota, recuperación y saldo recalculado](REVIEW-H2-MINIMAL-RECOVERY.md). El ensayo mínimo cerró en 358,500 s; H2 sigue inconcluso y no es admisible con el saldo actual. Recuperación operativa propuesta; estado nativo y retirada física pendientes.

2026-10-16. Resultado inconcluso: A agotó la espera sin salida del comando; B no iniciado. Reducir a diez denegaciones no desbloqueó la prueba dentro de cota. No se cargó plugin, invocó login ni ejecutó modelo.

El listener de control pasó desde host y se cerró. El auxiliar nativo propio fue identificado y detenido; el recibo final confirmó cero auxiliares propios pendientes. La configuración habitual y metadata de cuentas/firewall coinciden con la entrada. No se acredita reversión recursiva de ACL ni restauración completa del sistema.

Se detectó una ruta auth.json inesperada. La comprobación de atributos y contenido confirmó **directorio vacío**, sin enlaces, no archivo de credenciales. Dos logout oficiales fallaron con acceso denegado al tratar esa ruta como archivo. No se leyeron credenciales. La creación durante la sonda es consistente con la materialización de un objetivo de denegación inexistente por el setup nativo; no demuestra la causa de toda la espera.

La revisión automática rechazó retirar ese directorio con el único motivo `blocked by policy`. Se conserva el placeholder y no se probó otro mecanismo de borrado. Recuperación completa no acreditada; perfiles, canarios y estado nativo retenidos como evidencia, sin instalación activa de LKS ni autenticación observada.

**El máximo de tres minutos se excedió** durante la recuperación de esta anomalía. Al registrar: 282.71 s; saldo global conocido 21.44 min. Todo se carga; el cierre del turno sustituirá esta parte abierta. No se presenta como ensayo dentro de presupuesto ni como H2 completado.

H2/AC-34 pendientes. Sin métricas de ahorro, sin casos completos nuevos y sin tareas posteriores. Evidencia privada: C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\h2-min; state.json, results.json, recovery-result.json, recibos, salidas y metadata antes/después.
