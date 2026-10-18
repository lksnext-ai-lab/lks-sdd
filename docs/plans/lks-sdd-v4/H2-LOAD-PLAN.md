# H2 — Plan de carga aislada, recuperación y comparación

**Resultado vigente:** [ejecución H2 0.2: corte P2, perfiles recuperados y cero casos](RESULTS-H2-02.md). AC-34 pendiente; no se inicia V4-06. Los estados anteriores se conservan como antecedentes.

**Estado operativo vigente (2026-10-16):** [carga A/B resuelta; aislamiento sin acreditar; recuperación de perfiles comprobada](RESULTS-H2-CONTINUATION.md). Ningún caso H2 iniciado, AC-34 pendiente. Se conserva estado nativo de Windows sin acreditar su reversión; no hay candidata activa. Los estados preparatorios e informes anteriores que siguen se conservan como antecedentes.

**Resultado posterior vigente:** [H2 inconcluso y perfiles recuperados](RESULTS-H2.md).
El usuario autorizó la ejecución del plan 0.3; la carga falló antes de abrir casos.
La secuencia siguiente conserva el plan aprobado como antecedente. No hay ahorro
acreditado ni instalación candidata activa.

Fecha: 2026-10-16. Revisión local: 0.3. Deriva del plan 0.4 y de la revisión
V4-05A aceptada. Estado al aprobar el plan: tiempo conciliado; ejecución aún no autorizada entonces.
No cambia las seis mejoras, los umbrales congelados ni las reservas finales.
La autorización vigente cubre planificar y preparar materiales/planes sin aplicarlos:
**no se ha registrado, instalado o activado ningún paquete ni iniciado H2**.

## 1. Paquetes exactos y superficie elegida

| Elemento | Identidad que debe conservarse |
|---|---|
| A, referencia | ZIP `lks-sdd-plugin-v3.4.3.zip` de `h1-reference.json`; SHA-256 `d528d56a4ba0cdd68e851ca77ba6cf28e567bc2bc8b553d01524b833b5ca5a34`. |
| B, candidata corregida | `v4-05a/review/candidate-corrected/lks-sdd-plugin-v3.4.3.zip`; SHA-256 `fc3305217a438e9a58e04250dbdbe48dddd115769980326f3be023f1ecbe8096`. |
| Runtime B | `28c7a5ffc6f25f1277f5b0125e2ee6d20238bb97360c3c0e483f2c4ec05e8f7b`; fuente `working-tree:6f45fa8293e075d48ce27d62d35fe7e1398c0f41937f6fe1863b26953e2e0148`. |
| Identidad estable | `lks-sdd@lks-sdd-development`, seis skills; B sigue siendo `development-unreleased` con versión fuente 3.4.3. El número coincidente no permite distinguir A/B. |
| Cliente propuesto | Binario incluido en OpenAI.Codex `26.1013.3656.0`, `codex-cli 0.163.0-alpha.10.2`; ruta completa en `h2-load-plan.json`. |
| Modelo | `gpt-6.1-sol`, esfuerzo `xhigh`, misma configuración efectiva en ambos brazos. |

Se revalidaron ambos ZIP por contenido. El cliente incluido en la aplicación ofrece
`plugin marketplace add`, `plugin add`, `plugin list`, `plugin remove` y `--no-daemon`.
Solo se consultó su ayuda. El cliente npm 0.125.0 encontrado inicialmente no ofrece
instalación y queda excluido. No hace falta actualizar Codex para preparar esta ruta.

P01 valida medir en **Codex CLI interactivo usando el binario de la aplicación**.
Esto observa el host Codex; no acredita la interfaz gráfica de escritorio. La
[documentación de evaluación de OpenAI](https://developers.openai.com/cookbook/examples/partners/harness_aware_plugin_evals/harness_aware_plugin_evals)
describe un CODEX_HOME explícito y permisos de acceso para separar un ensayo.
La [referencia de comandos](https://learn.chatgpt.com/docs/developer-commands)
documenta las operaciones de plugins. La ayuda local confirma su presencia, pero
la carga y el aislamiento efectivos siguen sin probarse.

## 2. Aislamiento y preparación reversible

Reutilizar únicamente
`C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\h2-plan`.
Responsable: agente de mantenimiento; propietario de las decisiones: P01.
Subcarpetas preparadas: `r/a` y `r/b`, con `s` (paquete extraído), `h` (CODEX_HOME
vacío) y `m` (catálogo sin registrar). Consumidores `c` y temporales `t` pendientes.
No se crea otro worktree ni una nueva raíz de soporte.

- Pasar CODEX_HOME únicamente en el entorno de cada proceso hijo. Iniciar ambos
  con `--no-daemon`; no reutilizar el servidor compartido, sesiones o contexto del
  perfil habitual. No modificar variables persistentes, configuración personal,
  marketplace habitual, instalación activa, cachés oficiales ni identidad del plugin.
- Preparar un catálogo local por perfil, con la misma identidad y contenido A/B
  respectivamente; no registrar B como nueva publicación 3.4.3. El índice privado
  debe identificar la candidata por hash y finalidad temporal, sin redirigir la
  fuente personal habitual a B. No copiar skills a la vez al proyecto y al plugin.
- CODEX_HOME separa configuración, pero **no prueba por sí solo aislamiento de
  lecturas**. Revisar herencia desde padres, `.agents`, skills personales y fuentes
  implícitas. Configurar permisos soportados que permitan el consumidor propio,
  herramientas y plugin propio, y bloqueen el otro brazo, respuestas, repositorio
  de mantenimiento y perfiles personales. Comprobar acceso permitido/denegado sin
  abrir el caso al modelo; si no es posible demostrarlo, parar antes de W1.
- Resolver login en el perfil aislado, con la misma cuenta y capacidad de modelo.
  P01 hará el inicio de sesión si lo requiere el cliente. No copiar credenciales
  existentes, pedir claves ni incluir autenticación en informes/copias ZIP. El
  [almacenamiento de autenticación](https://learn.chatgpt.com/docs/auth) debe quedar
  acotado al perfil; no cerrar sesión ni modificar credenciales compartidas.
- Restaurar desde `final-s1/consumer-initial.zip`, sin reutilizar el consumidor ya
  resuelto. Verificar contrato, aprobaciones, autoridad lógica, controles, pruebas,
  prosa no clasificada y adjuntos equivalentes. Montar el runtime A o B correspondiente
  con el instalador común; diferencias permitidas: runtime/instrucciones y rutas
  neutralizadas en la comparación. Un requisito funcional propio de B va a W1.
- Verificar previamente longitud máxima de todas las rutas previstas, incluidas
  extracción, caché, Git y temporales; nombres cortos y raíces simétricas. Mantener
  mitigaciones Git verificadas, sin cambiar Git/TEMP/TMP globales. Temporal de proceso
  solo cuando esté soportado y sea equivalente. No improvisar otra raíz ni una
  migración si aparece de nuevo el problema de Windows: parar y conservar evidencia.

El gestor estable devolvió `Manager file set changed; use -Recovery`.
La ayuda y `plan --help` funcionan con `extensions.ps1 -Recovery`, sin reparación.
Se usará exclusivamente esa vía verificada para preparar el plan con precondiciones;
no se ejecutará `-RepairCurrent` ni código de la copia alterada. Antes de aplicar,
comprobar que el plan apunta al CODEX_HOME hijo y al paquete correcto. Si la vía de
recuperación no permite este destino, **no instalar manualmente para sortearlo**:
dejar la carga pendiente y presentar una incidencia separada del gestor.

## 3. Tareas, dependencias y aceptación

| ID | Tarea | Depende de | Criterio de aceptación / evidencia |
|---|---|---|---|
| H2-P0 | Admitir recursos y alcance de host | Este plan y decisión de P01 | Reserva de bloque y horas conciliadas; dos plazas H2 existentes; aceptación de CLI interactivo. Sin saldo acreditado, no arrancar. |
| H2-P1 | Preparar dos perfiles, catálogos, consumidores y plan del gestor | P0 y autorización separada de carga temporal | Huellas A/B, equivalencia funcional, rutas previstas, permisos y recuperación identificados; journal privado y precondiciones, sin alterar la instalación habitual. |
| H2-P2 | Registrar/cargar A y B en sus perfiles | P1; precondiciones vigentes | Operación oficial/gestor y recibos; `plugin list --json`, origen real y seis skills por perfil. Comparar bytes instalados y runtime con su paquete; versión 3.4.3 sola insuficiente. |
| H2-P3 | Comprobar separación y capacidad de captura | P2 | Configuración/cliente/modelo equivalentes, runtime-doctor, acceso propio sí/ajeno no, sin skills duplicadas. Instrumentos sin llamadas al modelo ni lecturas previas de instrucciones por el agente medido. Si falla, recuperar, sin iniciar casos. |
| H2-A | Ejecutar S1 en chat nuevo A | P3 | W1 íntegra; resultado real Hola/no parámetros/solo app.py; prueba, diagnóstico y cierre técnico con pendientes separados. Se conserva cualquier fallo y coste. |
| H2-B | Ejecutar S1 en chat nuevo B | A terminado o interrumpido y separación intacta | Mismo encargo y estado inicial, sin solución/transcripción A en contexto B; trazas de selección y lecturas de instrucciones B durante W1. |
| H2-R | Aislar/retirar cargas temporales y comprobar recuperación | Cualquier carga o fallo | Detener solo procesos propios, exportar evidencia sin secretos, retirada oficial o cuarentena del perfil propio y comparación con estado habitual inicial. Nada borrado de cachés manualmente. |
| H2-C | Comparar y emitir dictamen AC-34 | A/B, captura cerrada y R | Métricas completas, garantías y diferencias; estados passed/failed/inconclusive/not-run explícitos; ninguna tarea posterior iniciada por inferencia. |

P1–P3 son W0: no acreditan selección o comprensión por el modelo. La comprobación
de lectura real pertenece a A/B; listados/metadatos y declaración del agente no la
sustituyen. Guardar el manifiesto de turnos y hashes en evidencia privada. No se
crearán chats desde esta conversación sin la autorización futura que los incluya.

## 4. Ejecución H2 y ahorro sin perder garantías

Una pareja S1, orden **AB**, dos chats nuevos, P01 habitual. Mensaje funcional igual:
«Corrige greeting() para que devuelva “Hola” en lugar de “Adios”, manteniendo la
función sin parámetros y limitando el cambio de código a app.py. Comprueba el
resultado y completa el recorrido técnico autorizado conservando su evidencia».
Entregar en ambos el mismo identificador de tarea, actor lógico y autorización ya
válida del fixture; no fabricar decisiones humanas o identidades de organización.
La documentación/diagnóstico exigidos por el proceso no amplían el código permitido.

Seguir [MEASUREMENT-PROTOCOL.md](MEASUREMENT-PROTOCOL.md), sin reabrirlo:

- W1 empieza con el primer mensaje de cada caso, antes de bootstrap y lectura de
  instrucciones aplicables; termina al cerrar el turno que entrega resultado,
  comprobaciones y pendientes. W2 contiene el recorrido técnico completo dentro de
  W1. W3 extrae contadores y analiza después. Preparación/recuperación cuestan y se
  informan aparte, sin ocultar trabajo operativo en W0/W3.
- A recibe sus instrucciones correctas; no forzar consultas redundantes para
  favorecer B. B utiliza la presentación mínima sin saltarse contratos, guardas,
  decisiones vigentes, diagnóstico o prueba real. Si falla el reporte A, conservar
  su error y fallback con coste y limitación; no reparar A ni excluir el fallo.
- Capturar todo stdout/stderr, entregas efectivas, entradas, lecturas y errores,
  reintentos, recibos y recuperaciones. B_out incluye salidas y archivos realmente
  entregados; B_in todos los materiales efectivamente entrados, sin contar solo un
  descriptor. Almacenamiento sin entregar no equivale a tokens ni transporte.
  N_admin cuenta cada invocación pública, aunque varias compartan una herramienta.
- Conservar observaciones completas y su procedencia. Tras fallo de presentación
  posterior a aplicación, consultar efectos/recibo/estado antes de repetir;
  recuperar la operación exacta. No duplicar transiciones para obtener un recibo.
- Verificar: contrato y obligaciones literales íntegros, prosa incierta/adjuntos,
  autoridad y guardas, resultado funcional y prueba ejecutada antes de verificar y
  cerrar. Integración, publicación y aceptación funcional continúan pendientes.
- Tokens: solo suma deduplicada de turnos W1 cerrados y comparables; cached/reasoning
  son subconjuntos. Si faltan, marcar no medido, sin estimación por caracteres ni
  ahorro de factura. Comprobar trazas de lectura frente a los bytes del paquete;
  presentar las lagunas, sin llamar lectura a un listado o declaración.

| Condición conjunta H2 | Aceptación |
|---|---|
| Garantías E0 | Cero pérdidas conocidas y cero defecto material abierto; equivalencia de obligaciones, controles y resultado. |
| B_out | Reducción ≥10 % y ≥8.192 bytes. |
| N_admin | Al menos una invocación menos, incluyendo fallos y recuperación. |
| B_flow = B_out + B_in | No aumenta; entradas incompletas impiden acreditar este criterio. |
| Confirmaciones | Cero confirmaciones redundantes nuevas. |
| Interpretación | Una pareja descriptiva, sin extrapolación estadística; no prueba ahorro global de tokens, percepción humana, Copilot ni mejora S8 ≥20 %. |

Un fallo propio, timeout o resultado desfavorable cuenta y se conserva; no repetir
hasta éxito. Contaminación, pin incorrecto o captura irrecuperable se clasifican con
las reglas de invalidez congeladas, conservando costes. Una carencia de tokens no
invalida por sí sola H2; una carencia de B_in sí deja el ahorro de flujo inconcluso.

## 5. Recuperación, paradas y conservación

Antes de cargar: manifiesto de configuración habitual relevante, identidad/origen
del plugin activo y precondiciones; copias privadas solo de lo que vaya a cambiar,
sin autenticación. Mantener A y B inmutables. La recuperación ordinaria consiste
en cerrar los procesos aislados y retirar únicamente sus registros/cargas mediante
el gestor y comandos oficiales. No hay que reinstalar A en el perfil habitual si
este no se ha modificado. Ensayar la reversibilidad del perfil aislado antes de W1,
sin consumir un caso completo ni acceder al modelo.

Si cambia el perfil habitual inesperadamente: parar ambos brazos, conservar el
journal y contrastar cambios concurrentes. Restaurar solo cambios propios con
precondiciones vigentes; nunca sobrescribir una configuración global completa.
Si no es demostrable, mantenerlo pendiente y presentar recuperación concreta.
No ejecutar retirada global, borrar cachés, cerrar sesiones compartidas ni intentar
otra vía de eliminación rechazada anteriormente por la política automática.

Parar ante fallo de aislamiento, paquete diferente, instrucciones mezcladas,
imposibilidad de conservar evidencia, defecto material o corte de presupuesto.
Antes de W1: cero casos completos, pero W0 se carga. Desde el inicio de cada caso:
se carga su plaza incluso si falla/queda parcial. Si A agota su corte, no iniciar B
sin capacidad para completarlo y recuperar; pareja inconclusa, sin prórroga tácita.

Conservar evidencias satisfactorias grandes hasta 90 días tras cierre y temporales
de incidencia al menos 14 días tras su resolución, sujetos a referencias/pins y
política central. Credenciales quedan fuera del paquete de evidencia. No se limpia
nada en este bloque de planificación.

## 6. Presupuesto, operaciones concretas y decisiones vigentes

La [conciliación temporal 0.3](TIME-RECONCILIATION.md) y la [operación concreta](H2-CONCRETE-LOAD.md)
sustituyen el bloqueo temporal 0.2. Windows acredita reposo profundo: el cargo
observado corregido es 10,411149 h, sin descontar actividad intermedia ni esperas
técnicas. Reservando 10 min para esta conciliación quedan 85,331034 min conocidos.
H2 reserva provisionalmente 45 min y deja 40,331034 min compartidos para el resto.
No se certifican históricos externos ni la viabilidad integral de la release.

Las seis mejoras, cobertura, umbrales y 45/48 plazas conocidas/reservadas siguen
iguales; las dos H2 ya están incluidas. No hay una bolsa por fase adicional al saldo
común. Mantener las tareas pendientes si no pueden reservarse, sin rebajar criterios.

P01 ya valida CLI y prioridad H2. No se solicita valoración humana. Los dos planes
reales del gestor siguen sin aplicar; no se ha registrado versión, instalado o
iniciado H2. La carga requiere autorización separada y revalidación técnica de saldo,
contenido, cliente y aislamiento. AC-34 y el cierre de V4-05A siguen pendientes.

Plan posterior de preparación: [aislamiento, instrucciones y recuperación H2 0.1](H2-ISOLATION-PLAN.md). Propuesto, sin ejecutar; requiere validar la reasignación local dentro del máximo global.
