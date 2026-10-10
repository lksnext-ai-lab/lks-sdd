# Seguimiento y revisión de la implementación

Fecha: 2026-10-10. Base: 6f11fbf8352677bed2d19c1b2bc5990d78fc1fd0.
Rama: `codex/plugin-improvement-feedback`. [Plan](PLAN.md): revisión 2,
autorizada por la petición de implementación completa y revisión durante el trabajo.

La capacidad completa se revisó como **3.4.0-rc.1** y se promueve a **3.4.0**,
sin cambiar schema 3.1/método 3.1.0. El responsable respondió «Autorizado. Adelante»
a aprobar la versión y crear/integrar el commit local para gate/build. La decisión
real queda en [la aprobación propia](../../../quality/release-approval-v3.4.0.json).
El gate y los assets se acreditan después, mediante evidencia del mismo SHA.

## Cierre por tarea

| Tarea | Estado técnico | Resultado y revisión contra el objetivo |
|---|---|---|
| IMR-01 | Implementada | Tres schemas cerrados, procedencia, etapas, identidad, límites y UF-01–07. Tres escenarios definidos en fixtures y protocolo. No añade autoridad, host obligatorio ni razonamiento privado. |
| IMR-02 | Implementada | Un observador compartido en API/CLI; query/prepared/applied/failed/declared. Conserva preview_hash y diario, diferencia salida compacta/detallada/archivo y no atribuye recepción al host. Bloqueo previo devuelve reporte/prompt transitorio. |
| IMR-03 | Implementada | Lotes en el mismo journal del hito, objetos inmutables y reenvío idempotente. Referencias/IDs/intervalos/budgets validados. Fuentes grandes y binarios siguen exportables tras retirarlos. Reportes quedan fuera de bases semánticas; guards frescos permanecen. |
| IMR-04 | Implementada | Siete reglas con hecho/hipótesis, impacto, destinatario, prioridad motivada, componente, siguiente acción y criterio. Firma estable, ocurrencias y disposición motivada; resolver exige versión/cambio/evidencia. Correlación no confirma omisión, inutilidad ni ahorro. |
| IMR-05 | Implementada | Resumen de seis líneas, detalle regenerable, huecos y prompt autónomo. Consultas de solo lectura, páginas y casos focales. Entrada importada delimitada como datos; reporte sin disparador explica su cobertura limitada. |
| IMR-06 | Implementada | Export preview ligado a bytes exactos; publicación local completa en destino externo nuevo, sin sobrescritura. Inspector/exportador independiente del consumidor. Inventario, hashes, transformaciones, requisitos de material y selector aislado; nunca ejecuta adjuntos. |
| IMR-07 | Implementada | Las seis skills recogen desde el inicio, agrupan en hitos autorizados, presentan el reporte y reanudan el run con huecos explícitos. Guía completa bajo demanda; sin nuevos entrypoints, preguntas de aprobación o checkpoints por consulta. |
| IMR-08 | Implementada | Capacidad técnica lks-sdd-usage/1 y catálogo cerrado de módulos/schemas/guías. Núcleo completo en layouts Codex/Copilot. Lectores antiguos admitidos; persistencia nueva requiere corte explícito, sin activación ni migración automática. |
| IMR-09 | Validación de desarrollo | Regresiones de reglas, procedencia, continuidad, diario, autoridad, presentación, calidad, runtime y distribución; tres paquetes en proceso limpio y medición focal. La aceptación humana queda not-run. |
| IMR-10 | Completada | Diff revisado, contrato congelado, 3.4.0 coherente, aprobación propia real, changelog, [guía dual de actualización/rollback](../../UPGRADE-3.4.0.md), [protocolo](../../USAGE-FEEDBACK.md) y [ejemplo observado](EXAMPLE.md). |
| IMR-11 | Autorizada; cierre externo por SHA | Commit final e integración local en main, gate stable limpio, build único y assets del mismo SHA. El cierre real y los hashes se registran en release-completion.json/CLOSURE.md junto al conjunto final externo, después de las comprobaciones. |

## Comprobaciones y correcciones revisadas

Las suites nuevas usan fixtures temporales, actores explícitamente sintéticos y
proyectos Git reales. Comprueban estados/bytes y comportamiento observable; no
registran identidades reales ni ejecutan un piloto.

Última consolidación: **30/30** comprobaciones de diagnóstico/routing, **2/2**
focales posteriores de excepción/diagnóstico incompleto y **2/2** de prosa extensa,
adjuntos retirados y cuerpo histórico recuperado tras cambiar su revisión; fixtures **13 válidos**,
contrato estático **válido**, sintaxis/schemas y diff sin errores. Las cinco
regresiones focales de eficiencia/runtime reparadas pasaron; el recorrido de
orientación reparado pasó sin modificar su comparación normativa.
Los logs negativos y reparaciones se conservan fuera del checkout en el directorio
temporal `lks-sdd-usage-implementation-cfe2c6bc99614e83aeb8c1b2e5a48a49`.
Son evidencia de desarrollo y no el informe stable del futuro commit.
El bundle de revisión validó checksums de cinco ZIP, contrato en extracciones
plugin/marketplace y estructura nativa Copilot. Sus dos núcleos son idénticos en
bytes; las seis inspecciones (tres casos por host) pasaron. Este bundle precede
al ajuste focal de conservación histórica/prosa, comprobado después por sus
regresiones, y no se ofrece como conjunto final de release.

| Grupo | Evidencia revisada |
|---|---|
| Observaciones | Integridad de fragmentos, presupuestos, colisiones, llamadas distintas, solapamientos/revisiones, datos de negocio anidados intactos e importaciones sin elevar certeza. |
| Hallazgos | Positivos y contraejemplos UF-01–07; reenvío no es relectura; nueva decisión no es repetición; descarte/resolución mantienen ocurrencias y exigen motivos/evidencia. |
| Reportes | Determinismo, resumen/prompt desde primer intento, componentes/criterios utilizables, ausencia de disparadores y fuentes con apariencia de instrucciones tratadas como datos. |
| Exportación | Caso incompleto y preparado, corrupción, manipulación del preview/manifest, interrupción, destinos existentes, rutas/enlaces/archivos desconocidos, redacción con hashes anterior/transformado y dependencias externas pendientes. |
| Recorrido v3 | Consultas sin escrituras, lote/hito con un journal, reanudación/vinculación, rechazo de preview antiguo, decisión/cuerpo/receipt idénticos, fuente larga/binaria retirada aún recuperable y referencia corrupta rechazada. |
| CLI y distribución | Runtime nativo actual, bloqueo previo/init con lote diferido, usage-record sin recursión, transportes compact/details/output, preparación/aplicación relacionadas y plugins extraídos de ambos hosts ejecutando inspección/reproducción. |
| Regresiones existentes | Workflow, revisión integral, equipo, gobierno/calidad, integración, presentación y cinco recorridos de eficiencia/runtime actual, incluidos corte/rollback y presupuesto. Conservan estados normativos y autoridad. |

La revisión encontró y corrigió cuatro problemas antes del cierre:

1. Refactorizar el envoltorio del CLI perdía la ruta del guard de presentación;
   se repuso la resolución del evento real. Pasaron las regresiones de autoridad,
   configuración, cutover y ejecución pública que inicialmente lo detectaron.
2. El hash de un objeto de observaciones se sobrescribía con el de un fragmento;
   se separaron las variables. Pasaron conservación/reanudación, CLI, exportación
   y los tres casos que inicialmente fallaron por fuente modificada.
3. La comparación anterior de respuestas completas incluía IDs/tiempos diagnósticos
   nuevos. Las dos pruebas afectadas ahora comprueban el sobre por separado y
   siguen exigiendo igualdad exacta de **todo** el cuerpo normativo y del receipt.
4. La recogida recargaba innecesariamente el modelo de una consulta ya validada.
   Se reutiliza su evaluación de solo lectura; mutaciones mantienen cargas frescas.
   La medición focal y la prueba de freshness confirman el contrato conservado.

Además se revisaron integridad de cada referencia aun con bytes cacheados,
reenvío tras conservar un hueco transitorio y fallo de render/recogida sin ocultar
la excepción original ni cambiar la respuesta de calidad. No se descartó evidencia
negativa ni se relajaron guards para conseguir resultados positivos.
La conservación recupera prosa por su revisión física y cuerpos históricos por
su digest normativo, sin sustituirlos por la revisión actual. Los fixtures de estas
dos regresiones mantienen encabezados válidos y la política/coordinación conservada.

## Tres casos autónomos y medición focal

`python -B -X utf8 tests/measure_usage_feedback.py --output <destino-nuevo-externo>`
genera casos, reporte/prompt, manifests, evidencia de inspección/reproducción y
measurement.json fuera del checkout. Un subproceso solo recibe el paquete y el
runtime conocido; no recibe el directorio del consumidor ni el chat.

| Caso | Resultado técnico | Límite |
|---|---|---|
| Repetición | Investigable; selector reproduce exactamente los hashes esperados. Dos llamadas reales, un reenvío idempotente y fuentes únicas. | Repetición no acredita trabajo innecesario ni ahorro. |
| Contexto tardío/corrección | Investigable; reproducciones de selecciones antes/después, defecto y comprobación conservados. | Cambian las raíces del caso sintético; aplicabilidad inicial y causa siguen pendientes. No prueba un defecto causal del plugin. |
| Bloqueo previo | Investigable con entrada/error/entorno esperado; cero escrituras en origen inválido. | Reproducción de código y aceptación del host not-run. |

La comparación focal exige igualdad literal de fuentes, adjuntos, raíces, scope,
suficiencia y digest de selección. Mide dos consultas de control y dos observadas
con un calentamiento no medido. Separa recogida, conservación, reporte y exportación.
En una ejecución de desarrollo: control 0.687 s / observadas 0.714 s para dos
consultas; preparación del sobre 0.0031 s. Un lote añadió una operación de
conservación y 10 objetos / 10347 bytes. Preparación/aplicación de conservación:
1.187/1.699 s; reporte 0.198 s; preparación/exportación 0.312/0.228 s.
Estas cifras son un fixture Windows, con variabilidad de disco y sin significación
estadística; no estiman tiempo humano, tokens facturados ni ahorro general.

## Matriz de aceptación

Los estados siguientes acreditan desarrollo técnico; los canales humanos y el
cierre stable tienen evidencia y condiciones separadas.

| Criterio | Comprobación / estado |
|---|---|
| AC-01 | Resumen/prompt de implementación y API/CLI bloqueada desde primer intento; comprobado. |
| AC-02 | Procedencia/etapas/transportes; host_received unobserved; comprobado. |
| AC-03 | Métodos/unidades/cobertura/ausencias por métrica; comprobado. |
| AC-04 | Reenvío idempotente, colisión rechazada e IDs de llamadas distintas; comprobado. |
| AC-05 | Invocación compartida y unión por fuente/revisión; comprobado. |
| AC-06 | Revisión, huecos, etapas y resultado de journal separados; comprobado. |
| AC-07 | Objetos de texto grande/binario exportados después de borrar origen; comprobado. |
| AC-08 | Catálogo reanudado por run/request e historia provisional conservada; comprobado. |
| AC-09 | Fuentes normativas y cuerpo/receipt de decisión intactos; comprobado. |
| AC-10 | Queries/previews sin escrituras y mismo reporte determinista; comprobado. |
| AC-11 | Contraejemplos de relectura/scope y cautelas causales; comprobado. |
| AC-12 | Campos de hecho/hipótesis/prioridad/acción/criterio por hallazgo; comprobado. |
| AC-13 | Antes/después/defecto/check y causa pendiente en caso autónomo; comprobado. |
| AC-14 | UF-01 y prompt con entrada/componente/criterio de contraste; comprobado. |
| AC-15 | Ventana/hitos/stages preservados; calidad/aceptación independientes; comprobado técnicamente. |
| AC-16 | Tres paquetes investigables sin chat/consumidor; comprobado. |
| AC-17 | Selector en subproceso aislado y estados investigable/reproducido distintos; comprobado. |
| AC-18 | Redacción conserva hashes y degrada readiness; comprobado. |
| AC-19 | Material corrupto/ausente/rutas/enlaces/formatos inválidos rechazados; comprobado. |
| AC-20 | Diagnóstico incompleto no cambia resultado; lote/journal corrupto bloquea; comprobado. |
| AC-21 | Lectura anterior y corte/rollback explícito a nueva capacidad; comprobado. |
| AC-22 | Recorrido y seis skills en ambas extracciones nativas; comprobado en desarrollo. |
| AC-23 | Comparación focal y un lote con fuentes únicas; comprobado. |
| AC-24 | 3.4.0 coherente y aprobación propia real del 2026-10-10; comprobado. |
| AC-25 | Layouts/inventarios de desarrollo comprobados; assets finales del mismo SHA pendientes. |
| AC-26 | Guía dual con comandos locales/oficiales y recuperación; preparada y revisada. Activación real not-run. |
| AC-27 | Gate/build del commit final limpio pendientes. |
| AC-28 | Error anterior a runtime/tarea exportable y sin escritura; comprobado. |
| AC-29 | Etapas y archivo/display exactos; recepción del host ausente; comprobado. |
| AC-30 | Siete reglas, contraejemplos y disposición con evidencia; comprobado. |
| AC-31 | Importación normalizada sin certeza automática; intervalos/revisiones; comprobado. |
| AC-32 | Observador no recursivo y coste separado del resultado lógico; comprobado. |
| AC-33 | Exactitud de preview/manifest y exportación completa/nueva; comprobado. |
| AC-34 | Tres casos mínimos y ausencia material impide ready; comprobado. |
| AC-35 | Diagnóstico mantiene bases semánticas y presentación; preview antiguo rechaza cambio; comprobado. |
| AC-36 | Límites por lote/run/referencias/paquete antes de expansión; exceso explícito; comprobado. |

## Alcance y cierre de release

No se modificó `specs/canonical/`. Se mantienen las seis skills y su invocación
implícita. No se añadieron MCP, conectores, hooks, apps ni agentes ejecutables.
El Markdown consumidor sigue canónico; el índice y la tecnología no se autodeciden.
Los datos diagnósticos no son aceptación, evidencia de producto ni autorización.

La ruta final autorizada es **gate/build stable local, offline**, para preparar
assets del commit limpio integrado. No se presenta como preflight de origin/main.
La decisión real y promoción coherente a 3.4.0 ya están registradas. El cierre
fija el commit, integra main y ejecuta la puerta
vigente (aprobación, fixtures/contrato, 14 humos y Windows), construir una vez y
validar checksums, extracciones y el diagnóstico desde sus bytes exactos.
La evidencia final quedará fuera del checkout para no invalidar ese SHA limpio.

Este documento se fija antes del commit/gate/build y no anticipa sus resultados.
El registro final externo release-completion.json/CLOSURE.md acredita el estado
efectivo de IMR-11 y AC-25/27 con SHA, gate, extracciones, checksums y pruebas
desde los paquetes exactos. Se conserva fuera del checkout para no modificar ni
reconstruir los assets del SHA ya comprobado.
Publicación/referencias remotas, instalación/activación, migración de consumidores,
aceptación conversacional Codex/Copilot, piloto y comprensión humana: **not-run**.
Los paquetes de revisión y el ejemplo sintético no sustituyen esos estados.
