# V4-02A/V4-02B — Resultados y pendientes

Fecha: 2026-10-16. Plan 0.4 validado y ambas tareas autorizadas por el usuario.
Alcance ejecutado: preparación/diagnóstico sintético y contrato de aceptación.
**No se ha modificado el plugin ni el consumidor del equipo.**

## 1. Resultado y estado

| Tarea / criterio | Estado | Evidencia y límite |
|---|---|---|
| V4-02A | `verified`, investigación acotada | Cuatro consultas y disposición trazable; resolución del consumidor real inconclusa. |
| AC-37 | `passed` en alcance diagnóstico | Identidades, resultados/errores, costes y límites registrados; no equivale a incidencia resuelta. |
| AC-38 | `passed` | Dos casos válidos y 26 comprobaciones estructurales superadas. |
| V4-02B / AC-39 | `verified` / `passed` preparatorio | Umbral del 20 %, contrato congelado e instrumentos ejercitados; aceptación 4.0 pendiente. |

El primer preflight quedó bloqueado por un `pytest` ajeno, PID 40628. Tras su
finalización se ejecutaron las cuatro consultas autorizadas con vigilancia nativa.
Se obtienen **tres resultados terminales válidos**. La consulta final 3.4.2 alcanzó
120 s y quedó invalidada para tiempo por otro proceso Python aparecido durante
ella. No se ha terminado ningún proceso ajeno ni repetido la muestra. La cota de
cuatro consultas está agotada. La investigación puede cerrar con esta incertidumbre
conforme al plan; no se transforma el timeout en resolución ni en ahorro demostrado.

| Caso / runtime | Resultado público | Tiempo observado | CPU principal / job | Pico comprometido job | Validez temporal |
|---|---|---:|---:|---:|---|
| Pequeño 3.4.2 | `allowed`, sin causas | 8,731 s | 2,875 / 3,109 s | 62,8 MiB | Válida, una muestra |
| Pequeño 3.4.3 | `allowed`, sin causas | 10,024 s | 3,406 / 3,672 s | 65,0 MiB | Válida, una muestra |
| Objetivo 3.4.3 | `allowed`, sin causas | 11,042 s | 4,938 / 5,281 s | 68,4 MiB | Válida, una muestra |
| Objetivo 3.4.2 | Timeout, sin resultado terminal | 120,137 s hasta corte | No disponible | No disponible | Invalidada por concurrencia sobrevenida |

Todos los consumidores conservan exactamente sus archivos durante las consultas.
`state=in-progress` en readiness es el estado de destino evaluado, no una transición
persistida; el fixture continúa en backlog. Los resultados semánticos completos del
pequeño coinciden: solo varían IDs de observación, versión y tiempos diagnósticos,
con normalización explícita y originales conservados. No se descartan fuentes ni reglas.

El pequeño 3.4.3 es **14,8 % más lento** en esta pareja. Se activa la revisión del
umbral del 10 %: CPU y pico de memoria también suben; el núcleo observado contiene
631 archivos frente a 556. Arranque, integridad y carga son contribuyentes plausibles,
sin atribución causal demostrada por una muestra. Se conserva y se asigna el análisis
del coste completo pequeño a V4-12/V4-17. No se repite hasta obtener éxito ni se
afirma que 3.4.3 acelere todos los casos.

La preparación objetivo 3.4.3 termina en una muestra válida de 11,04 s. Es evidencia
útil de disponibilidad del recorrido de preparación representado; **no demuestra**
qué habría tardado 3.4.2 aislada, resolución del consumidor exacto, ahorro del 20 %
de 4.0 ni finalización completa de S8. El timeout contaminado no admite porcentaje
ni límite inferior de la latencia aislada. AC-42/43 permanecen `not-run`.

Resultados y recursos: [diagnosis.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/diagnosis.json>),
[comparación semántica](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/semantic-comparison.json>) y
[revisión del caso pequeño](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/small-cost-review.json>).

## 2. Versiones y procedencia

- Cache instalado observado: **3.4.3**. Los siete archivos fuente comprobados
  coinciden por SHA-256 con el commit de referencia `bf4d059c98826039097d606121ab6406d762fcc7`.
- El reporte del equipo ejecutaba `3.4.2-b70010c9f8a6`; ese pin se conserva como
  hecho comunicado. No se ha leído ni actualizado su consumidor.
- Los runtimes sintéticos se ensamblan desde las referencias Git exactas 3.4.2 y
  3.4.3, con identidades propias del estudio; no se presentan como el paquete
  publicado ni como instalación/activación real.
- Ambos consumidores sintéticos terminan fijados en 3.4.3 y pasan `runtime_doctor`.
  El pequeño conserva además la copia 3.4.2 usada para el contador diferencial.

Procedencia, commits, hashes y pins efectivos:
[versions.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/versions.json>) y
[pinned-runtime-validation.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/pinned-runtime-validation.json>).

## 3. Casos representados y validez

| Rasgo | Pequeño | Objetivo |
|---|---:|---:|
| Elementos del modelo | 33 | 338 |
| Tecnologías | 4 | 35 |
| Requisitos compartidos con dependencias reales | 4 | 256 |
| Reglas globales enlazadas | 2 | 24 |
| Interfaces sin ámbito acreditado / entrantes | 2 / 2 | 2 / 2 |
| Originales v2 recuperables | 2 | 2 |

Ambos usan método 3.1.0/formato 3.1, propuesta revisada, plan aprobado/autorizado,
asignación actual y tarea en backlog. Las tecnologías alternan confirmación heredada
y decisión actual. La prosa incierta, reglas globales y contribuciones entrantes
permanecen en el contexto. Las obligaciones esperadas y sus hashes literales se
generan desde las entradas del fixture, independientemente del selector comprobado.

El primer montaje fue rechazado por obligaciones sin tarea: se corrigió el plan
sintético añadiendo cobertura explícita. Se conserva esa incidencia de preparación;
no se relajó el validador del plugin ni se consumió una tarea funcional completa.

**Correspondencia con el reporte:** reproduce la combinación causal de 35 tecnologías,
aprobaciones heredadas/posteriores y dependencias compartidas. No reproduce las
769 fuentes/7.499.762 caracteres seleccionados ni la historia y topología exactas
del equipo. La tarea funcional es el saludo del generador existente, simplificación
de la tarea operativa de entrega del reporte. Su validez técnica no acredita la
reproducción exacta ni una garantía de latencia para el consumidor original.

Casos, inventario y resultado:
[min/fixture.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/min/fixture.json>),
[target/fixture.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/target/fixture.json>) y
[fixture-validation.json](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/fixture-validation.json>).

## 4. Contadores y conclusiones permitidas

| Trabajo instrumentado, caso pequeño | 3.4.2 | 3.4.3 |
|---|---:|---:|
| Reconstrucciones de descriptores | 95 | 1 |
| Recorridos de pertenencias | 97 | 1 |
| Lecturas de rutas originales | 18 | 2 |
| Parseos de originales | 18 | 2 |

Los hechos evaluados del pequeño son iguales; se conservan las tecnologías aprobadas
y las obligaciones esperadas. En el objetivo 3.4.3 también se observa una construcción
de descriptores y dos lecturas/parseos de originales, con todas las comprobaciones válidas.

El trabajo instrumentado combina selección de contexto, aprobaciones individuales
y facts_for; la pasada actual añade comprobación de estado. No son contadores de
un recorrido público completo. La evaluación moderna comparte su ámbito inmutable;
no se cachea autoridad entre comandos. Los contadores apoyan que la corrección
existente reduce trabajo repetido; no permiten afirmar ahorro de latencia, tokens
ni resolución del caso real. No se atribuye nada de ello a 4.0.

La pasada opcional de comprobación/contadores suma **5.861 s de 30 s**.
Sus tiempos son coste instrumentado, no muestras de aceptación, y se han obtenido
sin alegar aislamiento temporal. [Comparación](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/counter-comparison.json>).

## 5. Decisión del 20 % y contrato de V4-02B

El usuario considera suficiente una mejora de al menos 20 %. Se registra en
[S8-PROTOCOL.md](S8-PROTOCOL.md) y [su registro numérico](S8-PROTOCOL.json):
reducción del tiempo técnico completo frente a 3.4.3, dos parejas finales AB/BA,
garantías intactas, fases visibles, memoria y actividad/interrupción acotadas.

Es una decisión posterior al plan 0.4: reemplaza el máximo absoluto de latencia de
producto pendiente, sin convertir el corte experimental en SLA. Se precisan AC-39/43
y se conserva la revisión aprobada en el ZIP. E1/E2/E3/E4 y protocolo 1.0 no cambian;
la valoración humana sigue diferida y Copilot al final. No falta otra decisión
funcional sobre ese porcentaje. Se ha ejercitado la instrumentación pública con
referencia aislada terminal; AC-39 cierra el contrato preparatorio, mientras que
el recorrido completo y la aceptación de la candidata siguen siendo futuros.

## 6. Windows, recursos y próximos pasos

Las rutas máximas de estos consumidores son **213/216 caracteres**. Se evita anidar
temporales y se mantienen hashes, helpers e integridad. Esto no ejecuta ni supera
la regresión >260 caracteres; sigue asignada a V4-14/15/16.

Cero tareas completas iniciadas: permanecen siete cargos históricos conocidos y
43 plazas conocidas/reservadas, con saldo real no certificado. Se conservan 48
intentos, 8 h humanas, 12 h de entorno y M6 dos variantes/cuatro horas compartidas.
El registro de turnos cerrados observado al inicio suma 4,8535 h como proxy histórico,
sin incluir este turno ni costes fuera de cobertura. No equivale a saldo de entorno
o tiempo humano. [Observación](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/budget-observation.json>).

El ledger del bloque registra sus tiempos y cotas, incluida preparación, errores,
capturas e informe, sin doble imputación de pasadas. El tiempo humano no se reconstruye.

En el cierre observado, V4-02A consume **18 min 52 s de 45 min**; V4-02B,
**11 min 49 s de 15 min** hasta el checkpoint, con margen para esta entrega.
Se incluyen preparación, corrección del montaje e informe.
[Ledger del bloque](<C:/AI-Workspace/management/operations/lks-sdd-v4-h1-20261015/s8/resource-ledger.json>).

Las cuatro consultas están consumidas: cualquier nueva comparación 3.4.2 requiere
disposición previa de alcance/capacidad; no forma parte de este cierre. No es necesario
repetirla para usar 3.4.3 como referencia de 4.0. No se requiere cronometraje humano. La adopción
y comprobación del consumidor real por el equipo se mantienen como evidencia externa
necesaria para resolver su incidencia, aunque mejore el sintético.

La implementación del plugin permanece sin autorización. El cierre preparatorio
V4-02A/B queda en [v4-02ab-progress.json](v4-02ab-progress.json). V4-03 puede proponerse
como siguiente porción independiente; V4-06 mantendrá su ensayo temprano S8. Pendientes:
resolver el caso real con el equipo, explicar el sobrecoste pequeño antes de afirmar
mejora general, comprobar capacidad restante y medir la candidata futura. No se
infiere aceptación final de 4.0 de este cierre.
