# V4-05A — Primer recorrido completo y paquete provisional

Fecha: 2026-10-16. Plan 0.4; autorización del usuario limitada a V4-05A.

Entrega inicial conservada. El dictamen y paquete vigentes están en la
[revisión crítica posterior](REVIEW-V4-05A.md); AC-34 continúa pendiente.

La porción técnica está verificada: S1 termina en cierre técnico desde el paquete
provisional final, con prueba real, contrato literal, captura y conservación. **V4-05A
permanece `in-progress`: AC-34 exige además la pareja H2 real en Codex y está pendiente.**
No se inicia V4-06 ni otra mejora posterior.

## Cambio entregado

- Las rutas v3 de implementar y verificar usan work-prepare cuando el runtime fijado
  tiene la capacidad íntegra; conservan el recorrido individual para runtimes anteriores.
  No se repiten estado/intervenciones/readiness/context si la respuesta vigente ya los entrega.
- La guía común enlaza la captura externa y la presentación operativa. Los sobres íntegros
  se conservan mediante capture_dir; no se importa la vista breve ni se crea un bucle de reportes.
- El recorrido usa las transiciones individuales actuales. `--apply` prepara y aplica
  una operación local ya autorizada en una llamada, sin retirar guardas ni nuevas confirmaciones.
  La preparación/exportación separada sigue disponible cuando hace falta revisar el paquete.
- Se corrige el presentador de usage-report: preserva resúmenes en lista, contenido y
  métricas. El caso público comprueba compatible y operativo sin escritura de consulta.
- El validador admite tres recursos operativos compartidos concretos y comprueba sus
  enlaces. No se abre el acceso arbitrario fuera de las skills. Los builders existentes
  se reutilizan sin cambiar sus requisitos de release.

Se mantienen seis skills, descripciones e invocación implícita, método 3.1.0/esquema 3.1.
No se añaden MCP, apps, hooks o agentes ejecutables. Las instrucciones completas de M4
siguen siendo responsabilidad de V4-11; esta entrega cubre el primer S1.

## Recorrido observado

Consumidor sintético aislado, identidades y decisiones de fixture; no una aceptación
funcional del usuario ni una selección observada de skills por el host. El observador
usa el CLI público del runtime montado exclusivamente con los bytes del ZIP final.
El montaje no registra/instala el plugin en el producto.

1. Runtime-doctor válido; work-prepare devuelve ready con seis fuentes literales,
   prosa sin clasificar y snapshot coherente. La consulta no cambia el consumidor.
2. Start antes del código; cambia exclusivamente app.py de Adios a Hola.
3. Implement registrado; verify sin evidencia se rechaza y no escribe.
4. Python ejecuta dos aserciones reales: greeting() devuelve Hola y no tiene parámetros.
   Se conserva stdout y huella exacta de app.py; evidence, verify y close se aplican.
5. Estado canónico válido y cerrado; integración=false y aceptación=false.
6. Usage-record conserva las 14 observaciones de nueve entradas de captura; inspección
   íntegra, sin pendientes, objetos sin referencia ni materiales ausentes. El reporte público funciona.

Resultado: **36/36 comprobaciones del recorrido final**. El runtime no cambia y todas
las fuentes literales originales conservan sus huellas. Solo app.py cambia como código;
los demás efectos son registros/evidencia/índice esperados del consumidor sintético.
Sonar y Dependency-Check están explícitamente `not-used` en el fixture; no son análisis
superados, ni se ha ejecutado CI/CD o gate publicable.

## Verificación y alcance de garantías

**14 casos distintos de regresión superados**, sin sumar la repetición del caso de
paquetes como si fuera otro: seis de reporte/rutas, siete de preparación y uno real
Windows. Hay 15 ejecuciones en las campañas finales de esa selección; el primer ensayo
de seis casos también se conserva. No se afirma haber repetido toda la batería V4-05.

| Garantía | Evidencia en esta porción |
|---|---|
| G1/G2 · Completitud y aplicabilidad | Fuentes/adjuntos iguales al mismo selector invocado individualmente; seis fuentes originales intactas, prosa incierta retenida; regresión de dependencia entrante y decisión crítica. |
| G3/G4 · Vigencia y autoridad | Cambio después de ready rechazado por apply, autorización/revisión ausente, revisión independiente y runtime sin capacidad; ready no escribe ni autoriza. |
| G5 · Calidad y evidencia | Dos aserciones reales sobre el sujeto resultante; verify bloqueado sin evidencia; controles not-used explícitos; cierre separado de integración/aceptación. |
| G6 · Efectos y recuperación | Transiciones/journal vigentes sin cambios de implementación; pruebas anteriores V4-04/05 conservadas. No nueva campaña de interrupción/rollback en este bloque. |
| G7/G8 · Consulta y diagnóstico | Snapshots antes/después de consulta y rechazo; 14/14 observaciones conservadas, captura íntegra. La importación declara procedencia no verificada; lectura de host y tokens no observados. |
| G9 · Procedencia/runtime | Inventario exacto del ZIP al principio y al final, runtime-doctor, digest del manifiesto, igualdad entre adaptadores y dos builds finales. |
| G10 · Contrato y fronteras | Doce archivos protegidos sin cambios: specs/canonical y contrato/protocolo/revisión/escenarios congelados; sin inicializar el repositorio del plugin como consumidor. |
| Windows | La regresión real de plugin/migración con rutas largas pasa. El código Git/rutas no cambia respecto a la corrección V4-05 validada; se conserva su alcance condicionado. |

El paquete final solo difiere del candidato anterior en WORK-PREPARE.md y el manifiesto
de integridad derivado. Todos los bytes Python son iguales; se justifica reutilizar
las siete regresiones de guardas y la prueba pública del reporte. Se repite el caso
que contrasta instrucciones entre adaptadores y el S1 completo sobre el ZIP final.
Esto no acredita todos los adversos, estabilidad universal, aceptación de host o S8.

## Paquete provisional de esta entrega inicial (histórico)

Carpeta: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\candidate-final`.

- Canal: `development-unreleased`; versión fuente conservada: 3.4.3.
  **No es una release 4.0 ni otra publicación 3.4.3.** Identificar siempre por hash/digest.
- Fuente: `working-tree:a3eacac6ddcc5738b316a5edccf24de8599208ee542d0e87126781bdd47656c1`.
- Runtime: `0f5812f0059eaacc9a395d84b41fc020fa1d20dd2dc9a0bfb6fafd6bc85a563b`.
- Plugin Codex SHA-256: `3b0aaa55409c8bfd6590f179319d8feecc1fca12d6b6b0dca6eed6eee996db14`.
- Cinco ZIP, distribution-manifest.json y SHA256SUMS: **siete artefactos idénticos**
  en dos builds finales. El contrato estático del paquete y el formato nativo Copilot pasan.
- Copilot en host: `not-run`, conservado para el final. Registro, instalación,
  activación, publicación y commits del plugin: `not-run`.

## Medición: lo que permite concluir

| Dato del intento final | Observación |
|---|---:|
| Preparación del fixture/huellas | 100.266 s |
| Recorrido técnico con comprobaciones y conservación | 86.925 s |
| Total del observador con preparación | 187.192 s |
| Invocaciones públicas (incluye doctor, prueba negativa y diagnóstico) | 13 |
| stdout+stderr originales del CLI, incl. reporte | 157,482 B |
| Entradas explícitas de archivo observadas, cobertura parcial | 1,568 B |
| Captura externa | 317,763 B / 14 observaciones |

Son datos descriptivos de regresión, con comprobaciones del observador y posible
solapamiento con validaciones independientes. No son un benchmark aislado ni W1.
Los 1.568 B no equivalen al B_in completo: no acreditan flujo total, lecturas del
host o datos transportados por sus herramientas. Tampoco se compara este total con
los 100.086 B históricos de S1: sus ventanas/operaciones son diferentes.

**H2 no medido:** siguen pendientes conjuntamente reducción B_out ≥10 % y ≥8.192 B,
una invocación administrativa menos, B_flow sin aumento y cero confirmaciones
redundantes nuevas, conservando calidad/obligaciones. No se acredita ahorro total
de tokens, factura, tedio ni la mejora temporal ≥20 % de S8.

## Fallos y costes conservados

- Primer build: enlaces operativos fuera de la lista finita del validador. Corregidos;
  no usado como paquete final ni en el host. Los logs y artefactos permanecen.
- Primer verificador externo de paquetes: esperaba registros de tamaño/hash cuando el
  manifiesto contiene hashes. Corregido el observador; se verificaron los bytes de
  ambos builds existentes sin reconstruir ni ocultar el error.
- Primer S1: cerró y conservó diagnóstico, pero el observador comparó una cadena LF
  con el archivo Windows CRLF. El contraste de huellas inicial/final ya era positivo.
  La auditoría acredita el error de comparación; el intento original sigue fallido
  en el registro, no convertido retrospectivamente en passed. El observador corregido
  usa las huellas exactas de entrada. El segundo intento pasa 36/36.
- Se cuentan **dos intentos completos adicionales**, incluido el primero. No se
  consumen como pareja H2 ni se descuenta su coste de la cuenta por fallar.

## Presupuesto y decisiones pendientes

Techos sin ampliar: 48 intentos, 8 h humanas, 12 h entorno; M6 dos variantes/cuatro
horas dentro de los globales. Este bloque tiene cota 45 min incluyendo preparación,
correcciones, verificaciones e informe; resource-ledger.json conserva su corte.
El proxy de 28 turnos cerrados suma 32.583,522 s = 9,05098 h hasta el turno anterior;
no es CPU, atención humana ni saldo completo certificado. No se suman campañas
concurrentes como horas adicionales. El tiempo humano histórico sigue desconocido.

Los dos intentos técnicos añaden dos al compromiso aritmético 43/48: **45/48** con
las reservas H2/final/S8/contingencia intactas; tres plazas libres serían un máximo
teórico, no saldo real acreditado. No se certifica la viabilidad integral de horas.

1. Autorizar separadamente la carga temporal/aislada del paquete en Codex, después
   de concretar su mecanismo soportado y recuperación. AGENTS.md y el protocolo
   separan preparar, registrar, instalar y observar; este bloque no ejecuta esa carga.
2. Ejecutar la pareja real S1 A/B en chats nuevos, con participante y ambas versiones
   coherentes de instrucciones/runtime. Conservar ventanas W0–W3, contadores reales
   al cerrar turnos y todas las lecturas/errores/diagnóstico. No pedir fichas humanas.
3. Comprobar admisión del siguiente bloque contra presupuesto/reservas sin tratar
   históricos desconocidos como cero. Si H2 falla, corregir o dejar inconcluso con
   coste visible; no ajustar sus umbrales ni repetir hasta obtener éxito.

V4-05A no se cierra ni se inicia V4-06 antes de resolver AC-34 y presentar su resultado.
Véase [continuación H2](V4-05A-HOST-HANDOFF.md).

Evidencia externa: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a`. verification.json, final-package-verification.json,
final-s1/journey-result.json, CLI original, captura y hashes son recuperables;
los registros ligeros permanecen y la evidencia voluminosa sigue la política de
90 días tras cierre, preservando referencias/incidencias abiertas.

## Conservación y excepción de limpieza

La revisión automática de aprobación rechazó la eliminación de diez ZIP duplicados
con «blocked by policy», sin una causa más detallada. El proceso no llegó a iniciarse;
se verificó que los diez siguen íntegros. No se intentó otro mecanismo. Los originales,
las copias y los registros quedan conservados; detalle en duplicate-cleanup-rejected.json.
