# V4-05A — Continuación necesaria para AC-34

**Resultado vigente:** [ejecución H2 0.2: corte P2, perfiles recuperados y cero casos](RESULTS-H2-02.md). AC-34 pendiente; no se inicia V4-06. Los estados anteriores se conservan como antecedentes.

**Estado operativo vigente (2026-10-16):** [carga A/B resuelta; aislamiento sin acreditar; recuperación de perfiles comprobada](RESULTS-H2-CONTINUATION.md). Ningún caso H2 iniciado, AC-34 pendiente. Se conserva estado nativo de Windows sin acreditar su reversión; no hay candidata activa. Los estados preparatorios e informes anteriores que siguen se conservan como antecedentes.

Fecha: 2026-10-16. Estado: preparado documentalmente; carga y pareja H2 `not-run`.
No autoriza instalar, registrar, activar, publicar ni crear nuevas conversaciones.

La revisión V4-05A está aceptada. El [plan concreto de carga, recuperación y H2](H2-LOAD-PLAN.md)
y su [estado legible por máquina](h2-load-plan.json) sustituyen las decisiones
genéricas de esta ficha: cliente incluido en la aplicación comprobado por ayuda,
perfiles aislados propuestos, carga real sin probar y admisión de recursos pendiente.
No se ha aplicado ninguna carga. El protocolo 1.0 y sus umbrales permanecen iguales.

La [porción técnica](RESULTS-V4-05A.md) y su [revisión vigente](REVIEW-V4-05A.md) pasan; no sustituye la pareja real prevista
en el [protocolo congelado](MEASUREMENT-PROTOCOL.md). Las instrucciones del agente
de mantenimiento y un observador del CLI no prueban selección/lectura por Codex.

## Paquete y referencia que deben contrastarse

- A: fuente 3.4.3 del commit `bf4d059c98826039097d606121ab6406d762fcc7`, identificada
  en h1-reference.json. El ZIP Codex existente tiene SHA-256
  `d528d56a4ba0cdd68e851ca77ba6cf28e567bc2bc8b553d01524b833b5ca5a34`.
- B: carpeta externa
  `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\review\candidate-corrected`.
  ZIP Codex SHA-256 `fc3305217a438e9a58e04250dbdbe48dddd115769980326f3be023f1ecbe8096`;
  runtime `28c7a5ffc6f25f1277f5b0125e2ee6d20238bb97360c3c0e483f2c4ec05e8f7b`.
- B es `development-unreleased`, con versión fuente 3.4.3. La coincidencia del
  número no sustituye estos hashes ni acredita una instalación candidata.
- `final-s1/consumer-initial.zip` y sus huellas conservan el estado inicial del
  ensayo sintético. No son dos consumidores H2 ya preparados: aún deben montarse
  A/B con contrato, controles, decisiones, roles, código y herramientas equivalentes.

## Decisiones pendientes antes de ejecutar

1. Autorizar separadamente carga temporal/aislada de B y su recuperación. Comprobar
   primero la superficie soportada por el cliente actual y preparar el plan concreto
   del gestor sin aplicarlo. Mantener identidades existentes y el paquete A recuperable;
   no introducir otra identidad de plugin ni duplicar skills de proyecto/plugin.
2. Acordar la apertura de dos chats nuevos de caso, A y B en ese orden. No crear
   otros chats ni lanzar agentes por inferencia de esta ficha. P01 será participante
   real; no inferir su actuación o una aceptación funcional de los datos del fixture.
3. Admitir el bloque en el ledger con sus dos plazas H2 ya reservadas y horas de
   preparación/recuperación. Los dos ensayos técnicos adicionales dejan el compromiso
   aritmético en 45/48; las tres plazas teóricas libres no certifican saldo global.
   No ampliar máximos, reducir cobertura o convertir históricos desconocidos en cero.

La autorización actual de V4-05A cubre preparación técnica y paquete. AGENTS.md
exige autorización explícita separada para instalar. El protocolo exige además
instrucciones y runtime de la misma candidata: no vale runtime B con skills A.

## Ejecución posterior, una vez autorizada y preparada la carga

- Verificar A y B por contenido, runtime-doctor e instrucciones cargadas, conservando
  las pruebas. Registrar modelo/configuración reales; el protocolo fija Codex,
  gpt-6.1-sol/xhigh. Una divergencia debe resolverse antes de comparar, no ocultarse.
- Restaurar el mismo estado inicial; raíces de longitud comparable y nombres
  acotados en el área existente. No cambiar TEMP/TMP o configuración Git global.
- En cada chat nuevo, empezar W1 antes de bootstrap o lecturas pertinentes. Petición
  funcional S1: corregir greeting() para devolver Hola, sin parámetros, solo app.py;
  comprobar resultado, conservar evidencia y llegar a cierre técnico. Integración y
  aceptación funcional permanecen separadas. Identificar el operador lógico del
  fixture de forma explícita; no derivarlo de Windows, Git o el chat anterior.
- A usa las instrucciones/operaciones 3.4.3 correctamente; B la ruta mínima entregada.
  No forzar consultas redundantes en A ni omitir comprobaciones/diagnóstico en B.
  No transferir la solución/lecturas del primer chat al segundo como contexto inicial.
- Conservar todo stdout/stderr/input, entregas/lecturas reales y errores antes de
  analizar. Si falla el render del reporte A, retener el fallo y documentar el fallback
  con su límite y coste; no reparar silenciosamente A ni excluirlo por desfavorable.
- Terminar W1 al cerrar el turno de resultado técnico y pendientes. Extraer contadores
  después, como W3; no trasladar trabajo necesario del caso a esa ventana. Los tokens
  actuales de mantenimiento son mezcla de estudio y no sirven como denominador.

## Dictamen conjunto, sin modificar umbrales

| Condición H2 | Aceptación |
|---|---|
| Garantías | Mismas obligaciones/resultado y cero pérdidas conocidas o defecto material abierto. |
| Salida B_out | Reducción ≥10 % y al menos 8.192 B, incluyendo entregas efectivas. |
| Coordinación | Al menos una invocación administrativa menos, contando fallos/reintentos/diagnóstico. |
| Flujo B_flow | B_in + B_out no aumenta; entradas parciales no acreditan este resultado. |
| Confirmaciones | Cero confirmaciones redundantes nuevas; reutilizar decisiones vigentes. |
| Tokens | Solo datos reales comparables de W1; ausencia visible, sin ahorro total supuesto. |

Todas las condiciones tempranas deben cumplirse conjuntamente. Resultado descriptivo
de una pareja, sin extrapolación estadística. Si no se cumplen, corregir la porción
o dejarla inconclusa conservando costes; no ampliar M3/M5/M6 ni continuar a V4-06
por disponer únicamente de pruebas técnicas. Las repeticiones requieren capacidad y
las reglas congeladas; no se repite hasta obtener éxito.

La percepción/esfuerzo humano sigue diferida al uso real sostenido: sin nuevas fichas,
cronometraje o cuestionarios. Copilot queda para el final y S8 conserva su aceptación
temporal independiente de al menos el 20 %.


Actualización H2 0.3: [conciliación temporal](TIME-RECONCILIATION.md) completada.
Se conserva calendario bruto y se corrige solo reposo profundo Windows acreditado:
cargo observado 10,411149 h; reservando 10 min de auditoría quedan 85,331034 min.
[H2 concreto](H2-CONCRETE-LOAD.md) propone reservar 45 min; margen común restante
40,331034 min. No acredita viabilidad integral o históricos externos. Se mantienen
las seis mejoras, toda la cobertura y 45/48 plazas conocidas/reservadas. Los planes
siguen sin aplicar; no hay instalación, H2 ejecutado o aceptación AC-34.


Resultado de ejecución autorizada H2: [inconcluso y recuperado](RESULTS-H2.md).
A: copia/registro de paquete y catálogo, instalación fallida; catálogo revertido.
B: no cargado. Credenciales temporales retiradas; configuración habitual intacta.
Cero casos y cero plazas nuevas; sin métricas comparables ni aceptación AC-34.
La reserva de 45 min es acumulada y no se reinicia para corregir la ruta de carga.
