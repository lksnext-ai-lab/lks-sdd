# V4-02 — Referencia y viabilidad de medición

Fecha: 2026-10-15. Plan [0.2](PLAN.md), validado. Esta fase mide la base 3.4.3 y
prepara el protocolo. No compara una candidata 4.0 ni acredita ahorro todavía.
El dictamen y las decisiones de cierre están en [RESULTS-H1.md](RESULTS-H1.md).
Actualización de sesión de 2026-10-16: Codex es el host inicial, Copilot queda para el final,
los límites de presupuesto están aceptados y el usuario participará como P01.
Decisión posterior: [valoración humana diferida a uso real sostenido](DECISION-TECHNICAL-SCOPE.md).
La repetición cronometrada preparada se retiró sin iniciar; no condiciona AC-33.

## 1. Fuente fijada y evidencia recuperable

- Commit: `bf4d059c98826039097d606121ab6406d762fcc7` (3.4.3).
- Árbol fuente: 682 archivos versionados, 26.124.721 bytes sin comprimir.
- Archivo fuente congelado: 18.716.441 bytes; SHA-256
  `916245aad40a225c78632203ad1e1e0037f626633241483a5c689ddf076d550b`.
- Evidencia externa:
  `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015`.
- `provenance.json` identifica cuatro paquetes 3.4.3 existentes, sus tamaños y
  hashes: plugin, marketplace, Copilot y Copilot plugin. No se reconstruyen.
- El setup publicado usado solo para fixtures tiene SHA-256
  `1719e5f4e3b2a1db52c2ebde51901ef9bdad22f4c21a67f4d5c66293ac251d80`.
- `approved-plan-0.2/` conserva los tres documentos exactos antes de registrar su
  aprobación. El manifiesto identifica sus hashes. Se conserva así el contenido
  validado aunque posteriormente se actualicen estados y enlaces de seguimiento.

El registro local relaciona ese paquete con el mismo commit y tag 3.4.3; los hashes
se comprueban sobre los archivos existentes. No se afirma una nueva verificación
remota de la release, una instalación personal ni activación en conversación nueva.
La copia de fuente se usa para medir sin incorporar documentos nuevos al runtime.

El área reutiliza `management/operations`, con finalidad/responsable y 90 días de
retención de evidencia voluminosa satisfactoria según política central. No se crea
otra raíz, no se limpia evidencia durante esta tarea y no se modifican registros
de instalación. Los manifiestos ligeros del plan permanecen en el repositorio.

## 2. Qué se reproduce

[SCENARIOS.json](SCENARIOS.json) fija los siete casos, entradas funcionales,
obligaciones esperadas, variantes y límites de ejecución de esta fase. Se conserva
el inventario independiente de obligaciones y la revisión semántica del protocolo.
Una definición de caso no equivale a haber ejecutado su recorrido.

El auxiliar [measure_baseline.py](tools/measure_baseline.py) observa el CLI publicado
sobre un consumidor sintético con método/esquema actuales y runtime publicado fijado.
Reutiliza `IntegralTests`, el instalador existente solo en la fixture y las APIs de
reproducción. Captura stdin lógico JSON, stdout/stderr exactos, códigos, hashes y
tiempo de proceso completo. Comprueba que las consultas no modifiquen el consumidor.

La referencia incluye contexto pequeño, preparación con consultas actuales,
presentación compacta/detallada/exportada, prosa desconocida válida, raíz inválida
y recorrido técnico de corrección. La prueba del saludo se ejecuta realmente en
un subproceso y su resultado se guarda antes de registrar evidencia. El recorrido
no acredita comprensión, revisión independiente real ni aceptación humana.

Se excluye el setup de fixture de los tiempos individuales del CLI y se informa
por separado. Las muestras repetidas y los probes de opciones no se presentan
como el número mínimo de pasos de una tarea. Los archivos capturados no se vuelcan
íntegros al modelo: sus bytes son transporte potencial del CLI, no tokens del host.

Reproducción de la captura principal, con un directorio de salida nuevo:

```powershell
python -B -X utf8 docs/plans/lks-sdd-v4/tools/measure_baseline.py `
  --source C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/source `
  --runtime-bundle C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/setup-reference `
  --output C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/reproduction-new `
  --samples 3
```

Reproducción de rutas estáticas, ya realizada con el auxiliar existente:

```powershell
python -B -X utf8 C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/source/tests/measure_v3_instruction_context.py `
  --output C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/instruction-routes-new.json
```

No se ejecutan dos mediciones temporales simultáneamente. Las lecturas estáticas
y el diseño documental pueden realizarse durante la captura, sin atribuir a estas
muestras descriptivas una diferencia causal de rendimiento entre versiones.

## 3. Resultados y límites

El [manifiesto ligero](h1-reference.json) identifica hashes, mediciones e intentos
conservados. La captura principal terminó con 18 llamadas al CLI, Python 3.14.0 y
runtime publicado 3.4.3, esquema 3.1, digest
`e7183606c626c72c7b25c3a7d47e563df14ed385bea69afb047da6cbb414521f`.
No se presenta esta medición de componentes como referencia completa de S1–S7.

| Componente | Muestras | Bytes stdout | Incremento al agregar diagnóstico | Tiempo CLI observado |
|---|---|---|---|---|
| Contexto pequeño | 3 | Mediana 20.136 B | 7.046 B, 34,99 % del total | Mediana 6,36 s; rango 4,79–6,99 s. |
| Contexto con prosa desconocida válida | 3 | Mediana 62.961 B | 28.512 B, 45,29 % del total | Mediana 11,70 s; rango 10,06–12,86 s. |
| Decisión compacta | 1 | 12.350 B | Incluido en el total; ver captura. | 22,04 s; no es una mediana. |
| Decisión detallada | 1 | 44.659 B | Incluido en el total; ver captura. | 12,26 s; el orden/ruido impide inferir causalidad. |
| Exportación + compacto | 1 | 12.869 B y archivo de 30.445 B | El stdout no contiene la referencia `output` al destino. | 17,66 s. |

El incremento se calcula retirando `usage` y serializando con la misma indentación;
incluye el sobre y su puntuación. No todo ese incremento es duplicación prescindible.
Estos porcentajes no son ahorro realizado, ahorro garantizado ni tokens de tarea.
La combinación `--output --compact` confirma la necesidad de AC-05: existe archivo
exportado, pero el stdout vuelve a mostrar la vista en lugar de una referencia corta.

**Recorrido técnico S1 sobre tarea ya autorizada:** nueve llamadas seleccionadas de
preparación/contexto, inicio, implementación, registro de evidencia, verificación y
cierre; 100.086 B de stdout y 3.019 B de entradas JSON; suma observada de 184,57 s de
procesos CLI. La aserción real del saludo pasó y la tarea sintética terminó `closed`.
Ninguna consulta modificó el consumidor. La raíz inexistente quedó bloqueada.
No incluye aceptación funcional humana, conservación diagnóstica, trabajo del modelo
ni tiempo humano; por eso no es un coste completo de tarea en el host.

El setup de fixture costó 114,42 s y se informa separado. La ventana aproximada del
observador hasta escribir su resultado fue 535,34 s: incluye snapshots, comprobaciones,
repeticiones y probes ajenos al flujo mínimo. No atribuir esa ventana al plugin ni
restarla de otra versión como si fuera latencia funcional comparable. Los tiempos
son descriptivos de este entorno, no benchmark causal ni SLA.

**Conservación diagnóstica, calibración adicional con auxiliar existente:**
`tests/measure_usage_feedback.py` produjo `usage-conservation/measurement.json`.
Conservó dos observaciones en una mutación, diez objetos nuevos/10.152 B; preparar
0,629 s, aplicar 1,136 s, reporte 0,111 s y preparar/publicar exportación 0,147/0,193 s.
El contenido literal comparado permaneció igual; dos casos se reprodujeron en frío
y un bloqueo temprano quedó inspeccionable. La importación en proceso separado
conservó `unverified-import`, sin promover declaraciones a mediciones.

Esta calibración usa la fixture de API existente, con distinta preparación y frontera
de runtime que el recorrido CLI fijado. No restar sus tiempos para atribuir una
diferencia a arranque o a validación del runtime. No es una segunda campaña de host.

Se conservan cuatro intentos en `attempts.json` y las capturas disponibles: los tres
primeros fallaron por invocación del auxiliar sin dispatcher `v3`, fixture sin runtime
fijado y prosa de fixture sin cabecera de esquema, respectivamente. Los guards del
núcleo rechazaron correctamente los dos últimos casos. Se corrigió el auxiliar,
conservando entradas/stdout/stderr, sin tocar el plugin. Todos los intentos suman
723.465 B capturados de stdout; no se eliminan del coste de preparación ni se mezclan
fixtures inválidas con la muestra principal. Las causas son resúmenes del observador
de las trazas de herramienta; no se inventan logs originales del proceso auxiliar.

**Rutas estáticas de instrucciones:** doce escenarios; 10.065–18.990 caracteres y
3–6 archivos por ruta seleccionada. Esto confirma que 3.4.3 ya carga progresivamente.
La comparación interna con cargar todas las guías describe una alternativa más
verbosa, no una mejora de 4.0 ni la referencia principal para atribuir ahorro.

**Coste humano de las mediciones de componentes:** sin participante observado. No hay minutos
administrativos, resolución del observador o retrabajo humano medidos. Las decisiones
de fixtures son mecanismos sintéticos; no se convierten en firmas ni comprensión real.

**Cobertura funcional:** las capturas son componentes de S1/S4/S7 y rutas estáticas.
La campaña completa S1–S7 en hosts sigue pendiente. S3/S5/S6 tienen definición,
pero no referencia observada de tarea completa en esta fase. Posteriormente se
completaron S1/S2 del piloto Codex, con revisión y límites en REVIEW-S1-S2.md;
no se convierten en una comparación controlada. Tampoco se ha ejecutado
la campaña final de 12 + 12 ejecuciones de una candidata inexistente.

## 4. Viabilidad por métrica y host

| Métrica | Codex en este equipo | Copilot | Cobertura y siguiente comprobación |
|---|---|---|---|
| Salida exacta del CLI, entradas JSON y archivos | Disponible y capturada con herramienta externa. | El mismo núcleo es medible por CLI; host real sin observar. | No incluye automáticamente cada byte que el host reenvía al modelo. |
| Tiempo del proceso CLI | Disponible con reloj monotónico. | Núcleo medible; host real sin observar. | Separar proceso, preparación, modelo, persona y esperas. |
| Tokens del texto local | No medidos: no se ha confirmado tokenizador/mapeo del modelo. | No medidos. | No usar caracteres/4 como tokenización real. |
| Tokens reales del host | Registros `token_usage_record` por respuesta y turno, contrastados con `turn_token_usage`; 48 respuestas de un turno cerrado suman exactamente su total. | Aplazado por decisión del usuario; sin prueba ejecutada. | No mezclar estos registros con `token_count` acumulado ni sumar caché/razonamiento dos veces. |
| Tokens de tarea funcional completa | Ventanas históricas mixtas consolidadas: S1 1.584.190; cinco turnos S2 11.487.304, incluido estudio y parte de la contabilidad S1. Coste funcional aislado desconocido. | No medidos. | Cuenta por turno validada; falta ventana comparable/controlada, no acceso a los contadores Codex. |
| Factura atribuible a la tarea | No disponible en la evidencia observada. | No observada. | No inferir importe de tokens o límites de cuenta. |
| Tiempo/esfuerzo/percepción humanos | Históricos no medidos; evaluación diferida por el usuario a uso real sostenido. P01 declara uso habitual. | Percepción no observada. | Fuera del cierre técnico actual; `delta_admin` diferido, sin atribuir cero ni superación. |

La prueba corta de disponibilidad en el host Codex usa los registros reales de esta
conversación y un comando sintético ejecutado desde sus herramientas. Solo exporta
contadores numéricos y metadatos de modelo/tiempo; no copia prompts ni credenciales.
La ventana incluye preparación y llamadas del agente, no una funcionalidad aislada.
Puede acreditar que la métrica existe en esta sesión; no una cifra por tarea ni ahorro.
Cached input ya pertenece a input y reasoning output a output: no sumarlos dos veces.

La extracción por turno se ha validado con el auxiliar
[capture_codex_turn.py](tools/capture_codex_turn.py): 48 respuestas únicas de un turno
preparatorio cerrado coinciden exactamente con el contador final, con modelo/esfuerzo
consistentes, sin exportar transcripciones. La evidencia es
`codex-closed-turn-validation.json` en el área externa y su referencia queda en
[v4-02-progress.json](v4-02-progress.json). Es una observación del formato interno
actual, no un contrato público garantizado: se vuelve a comprobar antes de cada campaña.

La [revisión de S1/S2](REVIEW-S1-S2.md) asocia sus turnos cerrados y contrasta los
contadores, sin fingir aislamiento del trabajo funcional. Falta contexto inicial y
ventana comparables para una evaluación causal. El turno preparatorio de calibración
no se añade a esos casos ni demuestra ahorro. Copilot se comprueba al final; su aplazamiento no
bloquea la preparación ni aceptación específica de Codex y no acredita ambos hosts.

## 5. Protocolo operativo y valores fijados

Se mantienen E0 y los objetivos E1/E2/E3 del plan validado: garantías, 30 % de texto,
20 % de llamadas administrativas y 15 % de tokens reales cuando sean comparables.
Son objetivos, no resultados ni ahorro facturado. La fricción humana E5 y el beneficio
útil E4 no se sustituyen por esos porcentajes.

Valores fijados antes de candidata en [MEASUREMENT-PROTOCOL.md](MEASUREMENT-PROTOCOL.md) y su JSON 1.0. Son parámetros y método, no resultados de eficiencia:

| Elemento | Propuesta o resultado | Estado |
|---|---|---|
| Host inicial | Codex; Copilot aplazado a la comprobación final. | Aceptado por el usuario. Copilot permanece sin observar. |
| Interlocutor de validación de esta evaluación | Los resultados se presentan al usuario que ha validado el plan y los límites; el agente coordina las mediciones. | Interlocutor actual identificado por la sesión; no se infiere identidad organizativa ni rol en consumidores reales. |
| Participantes | P01 intervino en S1/S2 y declara uso habitual. | Sin sesión humana de evaluación pendiente: decisión de diferir percepción a uso real. S5 conserva su alcance técnico propio. |
| Ventana de tokens | W1: primer mensaje del chat nuevo, incluido bootstrap/instrucciones, hasta turno cerrado del resultado técnico. Todos los turnos, errores y decisiones; configuración equivalente. | Fijada; históricos mixtos solo acreditan viabilidad. Sin ventana válida, E3 sin medir. |
| H2 temprano | Pareja S1: B_out baja ≥10 % y ≥8.192 B; N_admin baja ≥1; B_flow no aumenta. E0 y decisiones necesarias conservadas. | Fijado; requisitos conjuntos, sin acreditar percepción humana. |
| Campaña | Codex primero: seis ejecuciones del piloto final y seis de cobertura restante; Copilot al final añade seis y seis. H2 y repeticiones comparten el máximo global de 48. | Límite aceptado; reservar cobertura pendiente y contar reintentos sin duplicar muestras reutilizadas. |
| Límites de tiempo | 8 horas de persona y 12 de entorno para la campaña; límites, no previsión de duración. | Aceptados por el usuario; se conserva toda preparación y no se inventa un saldo exacto no medido. |
| M6 | Máximo dos variantes y cuatro horas de estudio; corte anterior a incorporar variantes a la candidata, dentro de los límites globales. | Aceptado; puede terminar con descarte. |
| `delta_admin` | Evaluación diferida a uso real sostenido por decisión del usuario. | Fuera del cierre técnico actual, no cero ni superado. |
| `delta_util` | Mediana de ahorro técnico ≥5 s, >2×MAD de diferencias emparejadas, ≥5/6 parejas positivas y medianas AB/BA positivas; sin regresión relevante pendiente. | Fijado antes de variante. Seis pares, candidato previo como A; ampliación única hasta otros seis solo con saldo, con ≥10/12 positivos. Descarte/inconcluso si no compensa. |
| Coste económico | Sin cifra acreditada. No contratar APIs ni servicios para instrumentar. | Facturación `not-measured`; cualquier gasto nuevo conserva su autorización propia. |

Los techos aceptados no son estimaciones empíricas ni autorización para implementar. Si no
se puede cubrir un caso dentro del presupuesto elegido, se conserva como pendiente.
Cambiar alcance o recursos tras resultados no transforma un fallo en éxito.

## 6. Cierre de V4-02

Referencia fuente, mediciones de componentes y resultados técnicos S1/S2 disponibles;
la [revisión crítica](REVIEW-S1-S2.md) contrasta evidencias, incidencias y contadores.
Alcance Codex, límites y aplazamiento de la valoración humana están decididos.
AC-33 queda **verificado y cerrado en el alcance técnico Codex** con el protocolo
1.0: ventanas W0/W1/W2/W3, H2, E1/E2/E3, `delta_util`, ruido, recursos, responsables
y paradas fijados antes de candidata. La repetición
humana se preparó y retiró sin ejecutar; no se exigen cronómetro, ficha o `delta_admin`
para cerrar la fase técnica, conforme a DECISION-TECHNICAL-SCOPE.md. No se acredita
E5 ni menor tedio. Copilot se mantiene como
canal aplazado y no bloquea el cierre específico de V4-02 para Codex.
No se cambia el plugin para resolverlos ni se registra una aceptación humana ficticia.

El cierre acredita referencia/viabilidad/protocolo, no una comparación 4.0 ejecutada
ni saldo histórico exacto. La ruta de carga de candidata y su autorización posterior
están fijadas en MEASUREMENT-PROTOCOL.md; no se instala ni activa ahora.
