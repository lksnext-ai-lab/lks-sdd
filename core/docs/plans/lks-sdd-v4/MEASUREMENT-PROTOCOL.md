# V4-02 — Ventanas y umbrales técnicos congelados

Fecha: **2026-10-16**. Revisión **1.0**, anterior a cualquier candidata 4.0.
Completa el plan 0.2 y su [decisión de alcance](DECISION-TECHNICAL-SCOPE.md).
Valores legibles por máquina en [MEASUREMENT-PROTOCOL.json](MEASUREMENT-PROTOCOL.json).
No es un formato del runtime ni una política de release. No se implementa producto.

## 1. Alcance y referencia

A es **3.4.3**, commit `bf4d059c98826039097d606121ab6406d762fcc7`, con las fuentes,
paquetes y hashes de h1-reference.json. B será el paquete provisional exacto de
V4-05A en H2 y el candidato exacto de V4-16 en la comparación final. Para M6,
A será el candidato inmediatamente anterior a la optimización, también congelado;
no se atribuyen otra vez a M6 los cambios previos de M1/M2/M4.

Host inicial **Codex**, modelo **gpt-6.1-sol**, esfuerzo **xhigh**; versión del cliente,
herramientas, Python y entorno registrados por muestra. Copilot se comprobará al
final y se informará por separado, fijando su configuración antes de observarlo.
La percepción, cronómetro y cuestionarios humanos están **diferidos a uso real**.
Las decisiones funcionales exigibles conservan contenido, autoridad y trazabilidad.

Responsables: el agente de mantenimiento prepara/captura/compara; el usuario de
esta sesión recibe el dictamen y toma las decisiones funcionales o de autorización
que realmente correspondan. No se deducen identidades organizativas de P01.

Los resultados S1/S2 existentes acreditan funcionamiento y viabilidad de captura.
Sus tokens mixtos **no son denominadores de ahorro**. Las fixtures iniciales nuevas
conservadas en el área H1 pueden reutilizarse técnicamente con autorización futura;
los arranques humanos retirados no se reactivan. El cierre AC-33 congela un protocolo
viable, no exige que exista B ni declara realizadas sus comparaciones.

## 2. Ventanas comparables

| Ventana | Inicio y fin | Contabilidad |
|---|---|---|
| **W0 · Preparación del estudio** | Crear/restaurar fixture, comprobar hashes y preparar instrumentos, antes de abrir el caso al agente medido. | Tiempo, almacenamiento, fallos e intentos conservados aparte. No se mezclan con coste operativo. La configuración/clasificación que una versión necesite para resolver el trabajo sí pertenece a W1. |
| **W1 · Tarea completa en host** | **Primer mensaje del chat nuevo** que entrega el caso, incluido cualquier bootstrap, hasta cerrar el turno que presenta resultado técnico, pruebas y pendientes. | Todos los turnos intermedios, lecturas de skills/contrato, decisiones necesarias, herramientas, errores, recuperaciones y conservación diagnóstica configurada. Sin lectura previa de instrucciones aplicables para ocultar su coste. |
| **W2 · Recorrido técnico dentro de W1** | Primera operación necesaria para el caso hasta estado final/evidencia y conservación diagnóstica requeridos. | Transporte completo, entradas, invocaciones y procesos. Cambiar la cantidad de operaciones es una mejora posible; sus obligaciones/efectos deben seguir siendo equivalentes. |
| **W3 · Análisis del estudio** | Extraer contadores tras `task_complete`, revisar resultados y redactar el informe de mantenimiento. | Coste del estudio separado y conservado. Una tarea de W1 no se traslada a W3 para aparentar ahorro. Turnos mezclados se etiquetan como mixtos y no se reparten a ojo. |

Cada brazo usa un chat nuevo independiente, sin historia de la otra versión ni
acceso a su solución, plan elaborado o resultados. El caso inicial, los contratos,
política, roles lógicos, código y herramientas disponibles son equivalentes. No
dar a B un plan elaborado si A tiene que producirlo. No ejecutar ambos benchmarks
en paralelo. S4 incluye su clasificación/configuración inicial y mantenimiento;
se informa coste inicial y recurrente sin inventar una frecuencia de producción.

Se permiten diferencias declaradas de versión, rutas/UUID/fechas y formas de
salida intencionadas. No se normalizan obligaciones, decisiones, errores, sujetos
ni evidencia. Los hashes de los originales se conservan; cualquier normalización
se utiliza solo en una copia semántica, nunca para reducir los bytes medidos.

**Perfil diagnóstico primario: activado en ambos brazos.** A conserva observaciones
con los mecanismos 3.4.3 y B con los suyos, con igual cobertura exigida. Se cuentan
colección, registros terminales necesarios, captura/exportación y relecturas que
el recorrido requiera. La consulta de diagnóstico para el estudio puede ir a W3
en ambos brazos. El fallo conocido del renderer A y cualquier recuperación necesaria
se conservan, sin arreglar A ni usar una API más barata como si fuera el mismo CLI.
Un perfil sin diagnóstico sería secundario y separado, sin sustituir al primario.

## 3. Métricas y unidades

- **B_out:** bytes UTF-8 reales de stdout y stderr del plugin, más los adjuntos o
  archivos del plugin cuando se lean/entreguen al agente, en cada entrega. Un archivo
  solo guardado cuenta en almacenamiento/tiempo; si se relee se añade al transporte.
  No medir únicamente el cuerpo compacto omitiendo sobres. El filtrado del auxiliar
  no reduce los bytes originales emitidos por el plugin.
- **B_in:** bytes reales enviados al plugin, incluidas observaciones conservadas,
  recibos, adjuntos y entradas de recuperación. **B_flow = B_out + B_in**. Registrar
  aparte el texto realmente reenviado al modelo; no duplicarlo dentro de B_out.
- **N_admin:** invocaciones públicas del plugin para preparar, presentar, registrar,
  recuperar, verificar estado y diagnosticar, incluidas mutaciones/fallos/reintentos.
  Un auxiliar que lance tres comandos cuenta tres; agruparlos en una llamada de
  herramienta no los convierte en uno. Informar también etapas internas/guards;
  no eliminar controles para reducir el contador. Edición y pruebas del producto
  se registran aparte como trabajo funcional.
- **Tokens W1:** suma deduplicada por respuesta/turno cerrado, contrastada con cada
  contador final. Total = entrada + salida; caché y razonamiento son subconjuntos.
  Todos los turnos W1 deben estar disponibles; sin desglose comparable o con turno
  mezclado no separable, E3 queda `not-measured`/`inconclusive`. No usar caracteres/4.
  Misma política observable de caché; registrar sus categorías, sin exigir tasas de
  acierto idénticas ni inferir factura. Si cambia modelo/configuración, no mezclar.
- **T_machine:** tiempo monotónico del recorrido técnico secuencial: procesos CLI,
  pruebas y E/S necesarias, incluidos arranques y diagnóstico. Excluye inferencia del
  modelo y espera de decisiones humanas. Es una métrica del recorrido **técnico**,
  no tiempo total de desarrollo ni esfuerzo humano. No restar tiempos de API y CLI
  de fronteras diferentes. La duración W1 de reloj se informa descriptivamente.

## 4. Umbrales fijados

| Criterio | Valor y regla |
|---|---|
| **E0, siempre** | Cero pérdidas conocidas de G1–G10 y cero defectos materiales nuevos pendientes en los casos ensayados. Contrato, autoridad, sujeto y evidencias equivalentes. El ahorro no compensa un fallo. |
| **H2 / AC-34 técnico** | En la pareja S1: **B_out baja al menos 10 % y 8.192 B**, **N_admin baja al menos una invocación**, y **B_flow no aumenta**. Cero confirmaciones redundantes nuevas respecto a decisiones vigentes; mismas obligaciones y resultado. Todos los requisitos se cumplen conjuntamente. No exige todavía E1/E2/E3 finales ni acredita percepción humana. |
| **E1 final** | Mediana de reducción de B_out **≥30 %** en S1/S2/S4, con peso igual por caso y resultados por host separados. |
| **E2 final** | Mediana de reducción de N_admin **≥20 %** en S1/S2; cero confirmaciones redundantes introducidas. No acredita minutos ni tedio. |
| **E3 final, si medible** | Mediana de reducción de tokens W1 **≥15 %** en S1/S2/S4, con ventanas válidas. Ausente/incomparable: sin afirmación de ahorro total de tokens, visible en el dictamen técnico. No se sustituye por E1. |
| **M6 / E4: `delta_util`** | Mediana del ahorro de T_machine **≥5,0 s por recorrido completo**, **mayor que 2×MAD de las diferencias emparejadas**, **al menos 5/6 parejas con ahorro positivo** y mediana positiva tanto en AB como BA. Igualdad funcional, controles frescos y memoria/almacenamiento sin regresión relevante no resuelta. Si no compensa, descarte sin cambios. |
| **Regresión** | Aumento **>10 %** en transporte/tokens/tiempo de cualquier caso activa investigación y comparación focal dentro del presupuesto. Si se reproduce, corregir o retirar la variante. También se documentan regresiones menores reproducibles; el umbral no concede un margen de empeoramiento. |

H2 deja atrás el antiguo «más de cero»: sobre los 100.086 B observados del recorrido
CLI pequeño, 10 % son unos 10 kB. El suelo de 8 KiB impide aceptar cambios mínimos
de metadatos como utilidad; la llamada eliminada prueba una mejora M2 y B_flow evita
desplazar volumen a las entradas. Ese dato antiguo es orientación de escala, **no
el denominador del nuevo perfil completo**, que incluye conservación diagnóstica.

Los cinco segundos M6 son un **corte de utilidad de ingeniería**, no una estimación
de lo que se ahorrará ni una variación ya medida. Equivalen a aproximadamente 2,7 %
de los 184,57 s técnicos observados, pero la comparación M6 usa su propio candidato
previo. La regla MAD añade un control de ruido real de la serie; no se deduce del
rango de tres consultas ni constituye certificación estadística. No se exige una
optimización pequeña solo por cumplir un porcentaje de una fase.

## 5. Cálculo, ruido y muestras

Por pareja y métrica positiva: `r = 1 - B/A`; también informar `A-B` absoluto. Si
A=0, no hay porcentaje: diferencia absoluta y ninguna ganancia porcentual inventada.
Primero calcular la mediana de r de cada caso/host; después la mediana de las de los
casos primarios, **peso igual**. Con dos casos, mediana es la media de sus dos valores
centrales. No ponderar por tamaño ni combinar hosts para ocultar un empeoramiento.

H2 usa una pareja S1, resultado descriptivo temprano. La campaña final mantiene una
pareja S1/S2/S4 por host y la cobertura S3/S5/S6/S7 prevista. Orden inicial Codex:
S1 AB, S2 BA, S4 AB; cobertura S3 BA, S5 AB, S6 BA; Copilot invierte el orden. Al
ampliar un caso se alterna respecto a su pareja anterior. Aprendizaje se documenta,
sin encuestas ni valoración de percepción en esta fase.

Si el agregado relevante queda a **±5 puntos porcentuales del umbral**, hay signos
contradictorios o ruido, puede hacerse una sola ampliación dirigida, hasta **tres
parejas totales por caso/host**, únicamente con saldo disponible y conservando todas
las muestras. La elegibilidad queda limitada a S1/S2/S4 y la comparación focal de
una regresión; no repetir un fallo claro hasta conseguir éxito. Agotar saldo o
seguir sin comparabilidad/consistencia deja resultado `inconclusive`.

Para M6 se ejecutan **seis parejas secuenciales: AB, BA, AB, BA, AB, BA**, procesos
nuevos y fixture restaurada. `d_i = T_Ai - T_Bi`; `m = mediana(d_i)`;
`MAD = mediana(|d_i - m|)`. Se exige m≥5, m>2×MAD, al menos cinco d_i>0 y medianas
por orden positivas. No se limpian cachés del sistema para favorecer un brazo ni
se confunde proceso nuevo con filesystem frío. Calentamiento/perfil se registran
aparte y no se usan como muestras de aceptación.

La única ampliación M6 permitida sigue siendo hasta otras seis parejas, dentro de
horas/ejecuciones restantes y sin repetir fallos claros. Con doce parejas se exige
al menos **10/12** positivas, además de las mismas reglas de mediana/MAD/orden. Si
no cabe, no se amplía: queda inconcluso y la variante no se incorpora por rendimiento.
Se perfila CPU/memoria en pasada distinta, sin contaminar los tiempos comparados.

Muestra inválida solo por causa acreditada ajena al comportamiento comparado:
fixture/configuración/versión equivocada, captura irrecuperable, contaminación de
otro caso o interrupción externa identificada. Se guarda resultado, causa y coste.
Un guard bloqueado correctamente, un timeout por lentitud, un defecto de B, un fallo
del reporte A o un resultado desfavorable **no se eliminan como ruido**. Corregir
una variante crea revisión y comparación nuevas, manteniendo el intento anterior.

## 6. Recursos, carga futura y cierre

Se mantienen **48 ejecuciones/intentos, 8 h humanas y 12 h de entorno**; M6 máximo
**dos variantes/cuatro horas**, dentro de los globales. El ledger acredita siete
plazas cargadas conservadoramente: cuatro intentos iniciales de referencia, dos
casos históricos completados y un fallo de preparación. No certifica un saldo
exacto; las horas humanas históricas siguen desconocidas, sin volver a pedirlas.

Prioridad de reserva futura: **2 ejecuciones H2 + 24 de cobertura final de ambos
hosts = 26**. Con las siete conocidas, el margen teórico superior es **15** de 48,
antes de reconciliar otros consumos. Una comparación M6 de seis pares que complete
tareas consume **12 plazas**, dejando como máximo tres. Por tanto no se prometen
dos series M6 completas, su ampliación ni todas las repeticiones. Las dos variantes
son un techo de estudio: perfilar/descartar puede dejar solo una o ninguna para la
serie completa. Los microbenchmarks que no completen tareas consumen horas/coste,
sin convertir llamadas o pruebas unitarias en ejecuciones completas. No se sacrifica
la cobertura pendiente para agotar una optimización opcional.

Antes de cada bloque se comprueba capacidad real restante, se reserva el bloque
completo y se registra consumo. Si faltan recursos, parar e informar pendiente;
no ampliar límites ni reinterpretar desconocidos como cero. El cierre de V4-02
fija máximos/método, **no certifica saldo histórico ni autoriza arrancar bloques**.

Ruta de carga futura: paquete provisional externo y reproducible del mismo núcleo,
contrato del bundle comprobado y runtime del consumidor preparado con el instalador
común ya probado. Para medir M4 en host deben estar cargadas las instrucciones de
esa misma candidata, sin duplicar skills de proyecto/plugin. Registro, instalación,
activación y chat nuevo siguen la ruta documentada en docs/DISTRIBUTION.md, cuya
disponibilidad se comprobará entonces con la versión real del cliente y autorización
separada. Runtime B con skills A no es una prueba H2 completa. Ahora no se carga,
registra ni instala nada y no se presenta esa activación como ensayada.

Con este protocolo, AC-33 puede cerrarse **en el alcance técnico Codex**: referencia
reproducible, viabilidad acreditada, ventanas, parámetros, responsables, límites y
paradas fijados antes de candidata. E5/AC-36 siguen diferidos; Copilot no observado,
factura ausente y comparaciones 4.0 no ejecutadas permanecen visibles. No se declara
ahorro, aceptación humana, implementación ni autorización para V4-03.
