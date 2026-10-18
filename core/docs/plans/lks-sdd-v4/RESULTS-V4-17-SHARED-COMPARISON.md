# V4-17 — Comparación ABBA con cargas compartidas

Fecha del cliente: 2026-10-18. **Resultado mixto: menos transporte y llamadas,
memoria dentro del límite, pero mayor tiempo técnico. No se alcanza la mejora
≥20 % de S8.** Las cuatro ejecuciones terminan sin errores funcionales, sin
repeticiones ni descartes. No se implementan cambios posteriores a esta prueba.

| Ejecución | Versión | Tiempo completo, s | Pico del job, MiB | Llamadas públicas |
|---|---|---:|---:|---:|
| 1-A | Referencia 3.4.3 | 268.881 | 110.87 | 12 |
| 2-B | Candidata corregida | 353.252 | 110.77 | 9 |
| 3-B | Candidata corregida | 399.582 | 110.93 | 9 |
| 4-A | Referencia 3.4.3 | 294.714 | 111.00 | 12 |

Tiempo desde arranque hasta fin del coordinador, con sus CLI descendientes,
prueba real, cierre, integración sin aceptación y conservación diagnóstica.
Mismo caso de 338 elementos, 35 tecnologías y originales, base confiable y decisiones
sin renovar. Procesos nuevos, sin forzar caché física fría. TEMP/TMP local de 299
caracteres. El coordinador de negocio es idéntico al anterior.

| Pareja | Aumento temporal de B | Cambio de memoria | Reducción stdout/stderr | Reducción input JSON + stdout/stderr |
|---|---:|---:|---:|---:|
| 1-A / 2-B | 31.38 % | -0.09 % | 26.76 % | 44.92 % |
| 4-A / 3-B | 35.58 % | -0.06 % | 26.69 % | 44.86 % |

- Mediana de reducciones temporales: **-33.48 %**,
  equivalente a **33.48 % más tiempo**. Ambas parejas
  son desfavorables, frente a la exigencia de ambas positivas y mediana ≥20 %.
- CPU acumulada del job también aumenta: **34.23 % / 33.57 %**.
  Es otra observación desfavorable, no una prueba de causalidad ni de frecuencia
  de CPU constante. Se acepta la variabilidad del equipo; no se usa para borrar
  estos resultados ni para atribuir todo el exceso al plugin o a las otras cargas.
- Salida mediana **−26.72 %**; flujo delimitado
  input JSON + stdout/stderr **−44.89 %**.
  La referencia emite unos 887 kB por recorrido; B unos 650 kB. El input preparado
  baja de unos 299 kB a 3,5 kB. No incluye todo transporte del host, lectura interna,
  coste del modelo, consumo humano ni tokens facturados; esas métricas siguen null.
- Llamadas públicas **12 → 9 (−25 %)**. No acredita por sí solo esfuerzo humano
  menor ni aceptación real de Codex/Copilot.
- Memoria: alrededor de 111 MiB, cocientes **0.999119 /
  0.999402**, ambos ≤1,10 y todos ≤512 MiB. En esta candidata
  queda resuelta la regresión relativa observada en el paquete anterior; no se
  presenta como una reducción importante frente a 3.4.3.

## Garantías y límites

Los cuatro recorridos conservan literales requeridos y prosa no clasificada,
originales canónicos, runtime fijado, guardas, prueba real greeting=Hola sin
parámetros, evidencia, hechos de cierre e integración nativa sin aceptación.
Capturas completas y conservación comprobadas, sin journal pendiente. Los 19
checks de cada A y los 26 de cada B pasan; describen este caso sintético.
La cadencia de actividad pasa: primera señal máxima 0.612 s,
intervalo máximo 1.569 s y cola máxima 1.618 s.
El sobrecoste optativo de AC-40 sigue sin acreditarse; no se ha vuelto a ensayar.

La configuración fue la misma para A/B: planificación normal, sin afinidad forzada
ni HighQoS/Above Normal, sin calentamiento añadido ni controles de estabilidad.
No se detuvieron cargas, no se alteró el plan de energía, no hubo acceso de host,
reparación Windows o instalación activa. La observación de Python ajenos no bloqueó
las muestras; no se observaron identidades ajenas en las capturas de admisión/final.
Esto no demuestra reposo del equipo ni ausencia de cargas Node/Docker/otras.
Las dos parejas permiten una decisión descriptiva, sin intervalo de confianza
fiable o garantía de generalización.

La preparación reutilizó los paquetes reproducibles y verificó por hash las copias
del caso ya validado. Se interrumpió su validación completa redundante, sin iniciar
casos, y se completó mediante copias verificadas. Una copia B parcial solo se
actualizó al coincidir con los bytes originales conocidos. La validación pública
se mantuvo dentro de cada recorrido. Preflight nativo de ambos runtimes válido,
con cero operaciones públicas y cero escrituras de consumidor; no se cuenta como S8.

## Decisión propuesta a partir de estos datos

Conservar las mejoras verificadas de transporte, llamadas y memoria. **No cerrar
AC-43 ni presentar 4.0 como optimización temporal conseguida.** La investigación
siguiente debe concentrarse en costes concretos, sin nueva campaña por ruido:

- Inicio compuesto: 42,75 / 52,65 s en B frente a 18,15 / 28,83 s en A.
- Preparación/registro de resultados: 129,73 / 150,25 s frente a 111,36 / 105,95 s.
- Presentación de integración: 27,61 / 19,40 s frente a 3,85 / 4,03 s. Es una
  superficie útil para aislar coste de captura/presentación, sin atribuirle todavía
  todo el exceso. El resto de regresiones >10 % permanece en comparison.json.

No se cambia el plugin ni se ejecutan más pruebas después de esta serie. Corresponde
al usuario decidir si prioriza corregir latencia para mantener el objetivo temporal
o acepta expresamente el compromiso funcional/transporte con el rendimiento actual.
La decisión anterior de aceptar variabilidad no equivalía a aceptar una regresión.

## Identidad, presupuesto y evidencia

Runtime: `a76207a25976bfac2c45be78d7f49bfae2800a9e34fcfd819debd9295e5899af`.
Fuente: `working-tree:6cff8652abd37bb359ed60d860d48f8fd8a0101116b7c0a573a94a351a7ed767`. Desarrollo no publicado; base visible 3.4.3,
no una versión estable 4.0 instalada. Cinco archivos ZIP comprobados y dos builds
reproducibles, con núcleo compartido idéntico. Ningún paquete anterior se sobrescribe.

Cuatro plazas adicionales autorizadas y utilizadas, sin reintentos. Registro
conocido/reservado **54/54**, cero plazas S8 libres, dos H2 protegidas. La serie
consume **22.58 min** de la reserva de 45 min; suma de jobs medidos
**21.94 min**. No se inventa saldo global de horas.
Windows y H2 siguen pendientes. Sin instalación, publicación, commit o push.

Evidencia: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-17\performance\shared-comparison`:
predeclared.json, authorization.json, package-binding.json, runtime-preflight.json,
cuatro result-*.json, originales stdout/stderr, capturas, results.json,
comparison.json, summary.json y completion-receipt.json. Se preservan también los
resultados anteriores; no se combinan campañas de candidatas diferentes.
