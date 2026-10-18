**Estado vigente de 0.7 validada:** V4-15 técnica, V4-16 y V4-18 cerradas con reservas explícitas; [resultado final](RESULTS-V4-19-20.md#v4-15-v4-16-y-v4-18--cierre-técnico-y-paquetes-finales-de-desarrollo). Desarrollo y paquetes preparados; aceptación completa, aprobación de versión e integración/gate estable separados. Windows/H2 pendientes; sin instalación ni publicación. Seis mejoras y presupuestos conservados.

**Resultado técnico anterior:** nueva serie ABBA completa: salida −26,7 %, flujo medido −44,9 %, llamadas −25 % y memoria válida; tiempo técnico +33,5 %, objetivo S8 no cumplido ([resultado](RESULTS-V4-17-SHARED-COMPARISON.md)). 54/54 plazas conocidas/reservadas, H2 protegida; Windows/H2 pendientes.

# LKS-SDD 4.0 — Aceptación, garantías y ahorro

**Antecedente — ejecución H2:** [ejecución H2 0.2: corte P2, perfiles recuperados y cero casos](RESULTS-H2-02.md). AC-34 pendiente; no se inicia V4-06. Los estados anteriores se conservan como antecedentes.

**Antecedente operativo (2026-10-16):** [carga A/B resuelta; aislamiento sin acreditar; recuperación de perfiles comprobada](RESULTS-H2-CONTINUATION.md). Ningún caso H2 iniciado, AC-34 pendiente. Se conserva estado nativo de Windows sin acreditar su reversión; no hay candidata activa. Los estados preparatorios e informes anteriores que siguen se conservan como antecedentes.

Plan: [revisión 0.4](PLAN.md). Actualización: 2026-10-16.
Estado: **AC-33 cerrado en alcance técnico Codex; V4-03/04/05 verificadas localmente;
V4-05A con porción técnica verificada, paquete provisional reproducible y AC-34 pendiente
de la pareja real H2. Sin aceptación final de 4.0**.
La revisión V4-05A ha sido validada. El [plan H2](H2-LOAD-PLAN.md) no acredita
carga, aislamiento efectivo o ahorro: esos canales siguen pendientes; únicamente
se han contrastado paquetes, superficie de comandos y límites para prepararlo.
V4-02A/B autorizadas después y verificadas: AC-37/38/39 `passed` en alcance preparatorio;
[resultados](RESULTS-V4-02AB.md) y [protocolo S8](S8-PROTOCOL.md). [Dictamen y pendientes](REVIEW-S1-S2.md).
Decisión posterior vigente: [evaluación humana diferida a uso real sostenido](DECISION-TECHNICAL-SCOPE.md).
Los criterios originales se conservan; su aplicación actual se dispone expresamente
en esa decisión. E5/AC-36 y la comprensión humana no observada no se marcan superados
ni bloquean la aceptación técnica. No se eliminan decisiones funcionales ni garantías.
Los resultados de 3.4.3 acreditan la referencia/viabilidad de AC-33 en el alcance
declarado; no acreditan los AC de implementación, comparación o aceptación de 4.0.
Se conservan literalmente AC-01–AC-36 y se precisan AC-37–AC-44 de la ampliación.
El cierre preparatorio está en v4-02ab-progress.json; el actual de V4-05A en v4-05a-progress.json;
AC-40/AC-41 cuentan con implementación y comprobaciones focales de V4-07A;
[resultados y límites vigentes](RESULTS-V4-07A.md). AC-40 conserva pendiente el
sobrecoste comparable; no se declara cerrada V4-07A. AC-42–AC-44 siguen `not-run`.
El [complemento S8](ADDENDUM-PERFORMANCE.md) amplía cobertura; la decisión posterior fija mejora temporal S8 ≥20 %;
no altera el protocolo 1.0 congelado ni las medianas/denominadores originales.

Actualización posterior de ejecución: V4-03/V4-04 cuentan con sus revisiones
locales; V4-05 dispone de [resultados y alcance](RESULTS-V4-05.md) y
[registro propio](v4-05-progress.json), con [revisión correctiva](REVIEW-V4-05.md).
Los antecedentes anteriores se conservan
como históricos; no significan aceptación global de 4.0.

## 1. Qué se acepta y qué se mide

Orden de evaluación: contrato y autoridad → calidad del resultado → continuidad y
compatibilidad → experiencia → ahorro. Una reducción de consumo que omita obligaciones,
oculte un fallo o amplíe permisos es un resultado rechazado, aunque ahorre tiempo.

Este protocolo es la aceptación específica de esta evolución. No crea telemetría
recurrente, infraestructura de CI ni otro gate permanente de publicación. Se conserva
[la puerta estable del repositorio](../../VALIDATION.md). El gate técnico de una
release y la aceptación de las mejoras de 4.0 se informan por separado.
Decisión posterior del usuario: Codex es el host inicial y Copilot se comprueba al
final. Los límites de 48 ejecuciones, 8 h de persona, 12 h de entorno y M6 de dos
variantes/cuatro horas están aceptados. La referencia humana preparada se retiró;
[HUMAN-EFFORT.md](HUMAN-EFFORT.md) conserva su historia, no una prueba pendiente.

## 2. Matriz de criterios de aceptación

Cada criterio tiene una tarea propietaria. Las demás pueden aportar evidencia sin
duplicar su contabilización. Se guardan resultados observados y límites: preparar un
test o una guía no cumple un criterio de ejecución. Las garantías G se definen en PLAN.
AC-14 y AC-21 verifican capacidades técnicas; AC-30 acepta su comportamiento observado
en host. AC-33 cierra referencia y viabilidad sin candidata; AC-27/AC-28 comparan la
candidata al final. AC-34 acredita solo el recorrido temprano, con paquete propio.
Ningún cierre técnico anterior exige aceptación futura de V4-17/V4-17A. La evidencia de
V4-01/V4-02 se registra en [RESULTS-H1.md](RESULTS-H1.md); los AC de implementación
y aceptación de la candidata siguen sin ejecutar. Cambiar la matriz no los acredita.

| ID | Criterio comprobable | Garantías / mejora | Propietaria | Evidencia mínima |
|---|---|---|---|---|
| AC-01 | Cada operación declara entradas, salida, efectos, límites de vigencia, errores, parada y recuperación; ejemplos válidos y negativos coherentes. | G1–G10 | V4-01 | Contrato revisado y correspondencias con núcleo. |
| AC-02 | Decisión explícita de compatibilidad: producto/método/schema/formatos separados; ningún escritor nuevo opera con una decisión crítica sin resolver. | G8, G9, G10 | V4-01 | Matriz de formatos/capacidades y decisión documentada. |
| AC-03 | Se conservan seis skills y sus objetivos; no se añaden servicios, conectores, hooks ni agentes ejecutables; las exclusiones del plan siguen fuera. | G8, G10 | V4-01 | Inventario y contrato estático; comprobación final en V4-15. |
| AC-04 | La salida ordinaria no repite un mismo fragmento como contenido y diagnóstico; límites, impedimentos y contenido necesario siguen disponibles de forma suficiente. | G1, G2, M1 | V4-03 | Comparación literal de fuentes y mensajes en casos acotados y grandes. |
| AC-05 | Modo compatible, modo mínimo, detalle y exportación tienen semántica consistente; igual contenido/operación conserva recibo y condiciones; truncamiento no permite una aprobación global. | G2, G3, G7, M1 | V4-03 | Matriz de opciones y regresiones de presentación/recibos. |
| AC-06 | Captura explícita y conservación programática permiten recuperar un caso después de cambiar/retirar fuentes; límites, material ausente, colisiones y reintentos se tratan sin pérdida silenciosa. | G6, G7, M1 | V4-04 | Exportación/inspección independiente con fuentes recuperables. |
| AC-07 | Diagnóstico no altera decisiones, cierres normativos ni contexto aplicable; consultas sin captura no escriben. No se oculta corrupción de registros canónicos anteriores. | G1, G3, G7, M1 | V4-04 | Snapshots de estado, recibos y fallos antes/después; casos corruptos. |
| AC-08 | La contabilidad incluye salida completa con diagnóstico y entradas transportadas; origen medido/estimado/declarado/ausente permanece identificable. | G7, M1 | V4-04 | Captura externa de bytes exactos y contraste de contadores. |
| AC-09 | Preparar trabajo reúne condiciones equivalentes a consultas individuales, sin mutar ni conceder permisos; raíz inválida o vacía nunca resulta suficiente. | G2, G3, G4, M2 | V4-05 | Comparación diferencial por operación/actor/porción. |
| AC-10 | La preparación usa una base coherente; cambios concurrentes se detectan en los límites correspondientes y se reevalúa antes de materializar. | G4, M2 | V4-05 | Inyección de cambios de fuente, política, rol y base. |
| AC-11 | Operaciones agrupadas conservan hechos y precondiciones por etapa; ninguna aprobación, recepción ajena, revisión independiente o aceptación se infiere del agrupamiento. | G3, G4, G5, M2 | V4-06 | Recorridos equivalentes y respuestas parciales/negativas. |
| AC-12 | Reintento exacto no duplica efectos; interrupción muestra lo realmente aplicado y permite continuar o recuperar sin sobrescribir trabajo posterior. | G6, M2 | V4-06 | Fallos inyectados en cada frontera material e idempotencia. |
| AC-13 | Registrar resultados exige evidencia de pruebas ejecutadas/observadas y del sujeto exacto; evidencia antigua, error o `not-run` no cierra controles obligatorios. | G3, G5, M2 | V4-06 | Pruebas fallidas/antiguas, cambio de sujeto y controles indisponibles. |
| AC-14 | Las capacidades de continuidad reconstruyen hechos, pendientes y fuentes con identidad y vigencia actuales; pruebas técnicas de pérdida de contexto/cambio de fuente no dependen de memoria del chat. | G1, G2, G3, G4, M2 | V4-07 | Pruebas técnicas de continuidad. La observación S6 se acepta por separado en AC-30. |
| AC-15 | Alcance se revisa junto con autoría o gobierno competente; inferencias son propuestas; fuentes mixtas, compartidas, desconocidas y cambios invalidan exclusiones injustificadas. | G2, G3, M3 | V4-08 | Autoría nueva y lote de legado con contraejemplos. |
| AC-16 | Se conservan todas las obligaciones aplicables de un inventario revisado independientemente del selector, incluidos tipos, condiciones, negaciones, globales e interfaces/dependencias entrantes. | G2, M3 | V4-09 | Corpus esperado, referencia completa y revisión semántica. |
| AC-17 | Nuevos documentos ajenos acreditados no aumentan el núcleo normativo por defecto; nuevos desconocidos o globales sí lo amplían. Adjuntos necesarios se recuperan/observan sin confundir texto con imagen. | G2, M3 | V4-09 | Escalado del corpus, clasificación revocada y adjuntos. |
| AC-18 | Corrección cubierta reutiliza acuerdos vigentes y pruebas afectadas; tarea cerrada/permiso vencido/rechazo conserva reapertura, nueva evidencia y aceptación aplicables. | G3, G4, G5, M5 | V4-10 | Defecto durante ejecución y posterior a cierre/rechazo. |
| AC-19 | Cambio del acuerdo o incertidumbre crítica escala; no se usa tamaño del diff como autorización ni se fusionan propuesta y plan por defecto. | G2, G3, M5 | V4-10 | Cambio breve de permisos/datos/contrato; falta de cobertura. |
| AC-20 | Cada regla retirada de una guía tiene destino comprobado; rutas ordinarias y excepcionales conservan instrucciones necesarias, sin política duplicada por host. | G2, G3, G8, M4 | V4-11 | Matriz de reglas y prueba de referencias/perfiles. |
| AC-21 | Las seis definiciones de skills y sus rutas referencian capacidades existentes e instrucciones pertinentes; los perfiles técnicos conservan fuentes de cambios de evento/continuidad y carga selectiva. | G2, G8, M4 | V4-11 | Referencias, medición estática y pruebas de perfiles/rutas. La conducta real del host se acepta en AC-30. |
| AC-22 | Perfil separa arranque, E/S, cálculo, render, diagnóstico y persistencia; revisión/configuración/procesos y muestras son recuperables. | M6 | V4-12 | Perfil reproducible y baseline de la misma funcionalidad. |
| AC-23 | Solo se incorpora optimización con beneficio absoluto útil del recorrido, superior al ruido y justificado por frecuencia/coste de mantenimiento; conserva resultados, rechazos, memoria e invalidación fresca. Presupuesto/corte permiten descartar sin cambios. | G3, G4, G6, M6 | V4-13 | Pares aislados, beneficio absoluto y frecuencia observada, complejidad/riesgo, contraejemplos y disposición de cada variante. |
| AC-24 | Comandos/salidas compatibles y ambos adaptadores conservan contratos declarados; cambio del plugin no altera consumidores ni simula activación. | G8, G9 | V4-14 | Matriz de compatibilidad y ejecuciones públicas. |
| AC-25 | Actualización explícita conserva historia, trabajo abierto y decisiones vigentes; rollback respeta capacidad del runtime y cambios posteriores. | G3, G6, G9 | V4-14 | Actualización/recuperación desde origen fijado y hashes. |
| AC-26 | Recorridos integrados positivos/adversos no presentan pérdida conocida de G1–G10 ni defectos materiales pendientes atribuibles a la candidata. | G1–G10 | V4-15 | Resultados, revisión de diff, contrato estático y limitaciones. |
| AC-27 | Comparación parte de baseline bien configurada y candidato exacto; incluye tarea completa, fallos, costes iniciales y recurrentes, sin excluir resultados desfavorables después de verlos. | Todas | V4-17 | Protocolo congelado, entradas/muestras y cálculo reproducible. |
| AC-28 | Ahorro en texto, operaciones, tiempo y tokens se informa por separado; tokens/coste facturado ausentes quedan sin medir y no se infieren de bytes. | Todas | V4-17 | Informe con método, unidad, cobertura, variación y resultados por host. |
| AC-29 | Paquetes de desarrollo reproducibles del mismo núcleo ejecutan las capacidades y contienen todos sus recursos; no se presentan como stable, instalados o aceptados por host. | G8, G9 | V4-16 | Checksums, manifiestos y pruebas desde extracciones limpias. |
| AC-30 | Observación real por host comprueba decisiones comprendidas, continuación autorizada, reanudación S6 y selección/recuperación de instrucciones sin cargas indiscriminadas. Solo cobertura real de ambos acredita ambos. | G2, G3, G4, G8 | V4-17 | Participantes/host/modelo/caso, resultados y obligaciones conservadas en el trabajo; cierra aquí aceptación de uso de AC-14/AC-21. |
| AC-31 | Objetivos de eficiencia confirmados antes de medir se evalúan junto con calidad; los casos no medidos/inconclusos permanecen visibles y no acreditan ahorro. | Todas | V4-17 | Dictamen por objetivo, escenario, host y candidato. |
| AC-32 | Informe final separa desarrollo, garantías, compatibilidad, eficiencia, uso humano y release; solo declara hechos acreditados. | G1–G10 | V4-18 | Matriz final con evidencia y decisiones pendientes. |
| AC-33 | Referencia 3.4.3 reproducible; prueba corta de métricas por host accesible, ausencias acreditadas y decisión explícita de alcance. Protocolo, responsables, umbrales, presupuesto y paradas quedan fijados antes de observar candidata. No requiere comparación con 4.0. | Todas | V4-02 | Fuentes/hashes, captura de referencia, matriz de viabilidad y valores operativos completos de la sección 4.1. |
| AC-34 | Primer S1 completo combina M1, preparación M2 e instrucciones M4 sobre paquete provisional; una pareja real en host previsto demuestra la utilidad temprana predefinida sin pérdida de garantías ni nueva fricción. | G1–G10, M1, M2, M4 | V4-05A | Pruebas técnicas de la porción, paquete/hashes, participante, resultado y comparación. No depende de paquete ni aceptación final. |
| AC-35 | Cada recorrido M5 tiene antes/después verificable frente a 3.4.3 bien usada: acciones, datos manuales, registros, decisiones y trabajo eliminado. Nuevo núcleo solo ante carencia reproducida; entregas M2/M4 se referencian sin duplicar reglas ni ahorro. | G2, G3, G4, G5, M5 | V4-10 | Tres recorridos y variantes de cierre/rechazo, causa fundamentada, solución elegida y pruebas técnicas. El beneficio humano final se acepta en AC-36. |
| AC-36 | Los casos con trabajo administrativo reducible identificados en V4-02 cumplen E5: ahorro activo mínimo predefinido, sin aumentar reconstrucción manual, ayuda, retrabajo o errores de comprensión/decisión. Casos sin coste reducible conservan cero y no acreditan reducción. Menos llamadas por sí solo no basta. | G2, G3, G5, M2, M4, M5 | V4-17 | Tiempos activos, datos reconstruidos, ayuda, comprensión y calidad emparejados por caso/host, con resolución, variación y límites. |

### Criterios incorporados en 0.3 y precisados en 0.4

| ID | Criterio comprobable | Garantías / mejora | Propietaria | Evidencia mínima |
|---|---|---|---|---|
| AC-37 | Plugin instalado, runtime fijado y código ejecutado identificados por versión/digest; diagnóstico 3.4.2→3.4.3 acotado y con disposición explícita, sin atribuir a 4.0 esa mejora. | G9, M6 | V4-02A | Procedencia, resultados/errores, costes, límites y correspondencia. Resuelto en caso representado, persiste o inconcluso; no prueba el consumidor exacto. |
| AC-38 | Fixture S8 válido y representativo, con tecnologías, decisiones heredadas/posteriores, globales, prosa incierta y dependencias; diferencias explícitas. Diagnóstico inconcluso no dispensa validar el fixture. | G1, G2, G3, M6 | V4-02A | Máximo dos tamaños y cuatro consultas acotadas; fuentes/hashes e inventario independiente, raíces Windows. Fixture inválido no permite verificar la tarea. |
| AC-39 | Umbral temporal S8 ≥20 % frente a 3.4.3 por decisión posterior; memoria, actividad/interrupción y cortes numéricos, motivados y comprobables antes de candidata. | G3, G6, M1, M2, M6 | V4-02B | S8-PROTOCOL completo, mapa A/B, decisión, cortes y reglas de fallo. Consulta/transiciones visibles sin SLA absoluto adicional; referencia pública de preparación observada; aceptación final pendiente. |
| AC-40 | Señales optativas cumplen límites de actividad/volumen/sobrecoste; stdout JSON y modo compatible preservados, sin porcentaje ficticio, escritura canónica por consulta ni saturación. | G1, G7, G8, M1 | V4-07A | Canales activados/desactivados, sin TTY/canal cerrado, bytes y coste integral. Heartbeat distinto de avance de cálculo. |
| AC-41 | Interrupción cooperativa conserva contrato, informa efectos técnicos/parciales y usa journal/puntos seguros existentes; reintento no duplica ni pierde cambios posteriores. No ejecuta cancelación de negocio ni afirma éxito. | G3, G4, G6, G7, M2 | V4-07A | Pruebas por fase y superficie declarada, límites de E/S explícitos, snapshots, recuperación/rollback y temporales largos. No prometer aborto instantáneo ni cero artefactos. |
| AC-42 | Dos parejas finales S8 AB/BA ejecutan preparación/inicio, implementación/prueba real, verificación, cierre e integración con obligaciones/efectos/resultados equivalentes y coste completo. | G1–G10, M2, M6 | V4-17A | Cuatro intentos públicos del paquete exacto; mapa de hitos A/B, cálculos internos y recuperación. Pareja temprana separada. No acredita publicación, percepción, estabilidad universal ni E4. |
| AC-43 | Dos parejas finales S8 válidas cumplen reducción mediana temporal ≥20 % y consistencia de S8-PROTOCOL, con resultado correcto y límites de memoria/actividad. Timeout o fallo propio no acredita mejora. | G3, G5, M6 | V4-17A | Referencia 3.4.3, tiempos completos y por fase sin perfilador, ambos pares AB/BA, recursos, errores y disposición. Solo invalida causa externa preregistrada; no repetir hasta éxito. |
| AC-44 | S8 conserva rechazos ante originales modificados/ausentes, revocación, cambios de política/base, evidencia inválida e interrupción; frescura entre consulta, preparación y aplicación. | G2, G3, G4, G5, G6 | V4-17A | Cobertura focal V4-06/07A/14/15 vinculada al candidato exacto y reutilización justificada, incluida Windows en fronteras afectadas; sin ready falso ni autoridad cacheada. |

AC-37/AC-38 cierran la investigación y representatividad, no acreditan que 3.4.3
resuelva el caso real. AC-39 cierra el contrato previo a S8 y su actividad/optimización;
AC-43 exige después los resultados. La decisión de release con reservas no
convierte ninguno de estos criterios fallidos/inconclusos en superado.

## 3. Escenarios y cobertura adversa

Usar repositorios temporales/sintéticos o copias expresamente autorizadas y saneadas.
El mismo escenario tiene requisitos, código inicial, datos, controles, herramientas,
límites y resultado esperado equivalentes en ambas versiones. Los casos de prueba
no contienen identidades operativas reales ni secretos.

| Escenario | Trabajo completo observado | Cobertura principal |
|---|---|---|
| S1 · Corrección cubierta | Detectar defecto en tarea autorizada, corregir, comprobar y registrar resultado; variante posterior a cierre. | M1, M2, M5; autoridad/evidencia vigentes. |
| S2 · Funcionalidad normal | Definir propuesta, validarla, planificar/autorizar, implementar, verificar y presentar resultado. | M1, M2, M4; no fusionar decisiones ni preguntar por cada comando. |
| S3 · Cambio transversal | Modificar interfaz/datos con consumidores dependientes y una restricción global. | M3, M5; escalado, contratos compartidos y calidad de integración. |
| S4 · Proyecto documental grande | Tarea pequeña entre funcionalidades ajenas acreditadas y prosa incierta; medir clasificación y trabajos sucesivos. | M1, M3, M6; ahorro amortizado y crecimiento conservador ante incertidumbre. |
| S5 · Trabajo en equipo | Encargo, recepción por destinatario, trabajo independiente y revisión/integración según política. | M2, M4; identidad, separación de funciones, alcance y base. |
| S6 · Reanudación | Reanudar tras conversación nueva/compactación, con una fuente cambiada y otra decisión vigente. | M2, M4; recarga literal, decisiones reutilizadas y cambio material detectado. |
| S7 · Límites y fallos | Reproducir bloqueo correcto, revocación, respuesta parcial, preview caducado, prueba antigua, corrupción e interrupción. | G1–G10; no buscar ahorro evitando comprobaciones. |
| S8 · Entrega en proyecto migrado | Caso suplementario de aprobaciones heredadas, tecnologías y obligaciones compartidas; desde inicio hasta integración nativa. | V4-02A/02B/07A/17A; equivalencia, mejora temporal ≥20 %, actividad e interrupción. No modifica SCENARIOS.json ni los primarios. |

S1, S2 y S4 son los escenarios primarios de eficiencia. S3, S5 y S6 observan coste
sin convertir su mayor garantía en un permiso para omitir trabajo. S7 verifica
rechazos y recuperación: una ejecución bloqueada correctamente no es una tarea de
producto completada ni un ahorro por terminar antes.
S8 reserva dos intentos tempranos y cuatro finales en dos parejas AB/BA, dentro de 48;
su aceptación no exige un piloto humano adicional ni se mezcla con las medianas
S1/S2/S4. La definición y las fronteras están en ADDENDUM-PERFORMANCE.md.

Para contexto, el corpus adverso incluye: raíz vacía/retirada; UID/alias ambiguos;
regla global nueva; obligación en prosa fuera de bloques; negación al final de
texto largo; declaración de alcance caducada o revocada; contribución entrante;
dos reglas parecidas con ámbitos diferentes; adjunto visual necesario y dependencia
compartida. Se revisa un inventario de obligaciones esperado independiente de los
algoritmos candidato y de referencia. Igualdad de hashes no demuestra por sí sola
comprensión ni corrección semántica del código.

## 4. Baseline y diseño de comparación

### 4.1 Congelar antes del cambio

V4-02 fija el commit y los paquetes reales 3.4.3, sus hashes y configuración, el
generador/versión de fixtures y el protocolo. No basta un nombre de versión. Para
mediciones intermedias conservar la revisión exacta de cada variante; no mezclar
tiempos de un runtime con bytes o calidad de otro.

**Comprobación de viabilidad:** ejecutar una prueba corta con la referencia en cada
host accesible antes de implementar producto. Para cada métrica registrar fuente,
exportación recuperable, unidad, ventana, resolución, categorías, disponibilidad y
responsable. Separar tokens del texto local, consumo completo y factura. Si un host
no está accesible, acreditar ese límite; no fingir la prueba. Verificar también
cómo se cargará el paquete provisional y qué autorización requerirá.

Si falta consumo completo, decidir en V4-02 entre resolver medición o aceptar un
alcance demostrable de transporte/trabajo administrativo, manteniendo el ahorro total
de tokens `not-measured`. La decisión se solicita solo si no existe en la autorización
de ejecución futura; esta revisión no la concede. Una cobertura limitada de hosts
deja su aceptación pendiente. No ampliar desarrollo con este alcance crítico ambiguo.

El registro V4-02 queda cumplimentado en [MEASUREMENT-PROTOCOL.md](MEASUREMENT-PROTOCOL.md)
y MEASUREMENT-PROTOCOL.json, revisión 1.0, antes de candidata. Cierre técnico AC-33;
los valores siguientes no acreditan ejecución de 4.0 ni percepción humana:

| Campo | Contenido requerido |
|---|---|
| Casos/hosts y personas | Codex gpt-6.1-sol/xhigh; S1/S2/S4 primarios y S3/S5/S6/S7 de cobertura. Agente prepara/captura/compara; usuario decide el contenido funcional. Copilot al final; percepción diferida. |
| Métrica temprana H2 | Pareja S1: B_out baja ≥10 % y ≥8.192 B, N_admin baja ≥1 y B_flow no crece; E0 y cero confirmaciones redundantes nuevas. |
| Umbrales finales | E1 ≥30 % de B_out; E2 ≥20 % de N_admin; E3 ≥15 % de tokens W1 comparables. Medianas por caso/host y después mediana de casos con peso igual. `delta_admin` diferido, sin superación. |
| Presupuesto de observación | Máximos compartidos: 48 ejecuciones/intentos, 8 h humanas y 12 h entorno; factura no medida. Ledger conserva costes/ausencias, sin reset ni saldo inventado; verificar capacidad antes de cada bloque futuro. |
| Presupuesto M6 | Máximo dos variantes y cuatro horas dentro de globales; corte previo al paquete final. Responsable: agente de mantenimiento. Descarte permitido sin cambios. |
| Beneficio útil M6 | `delta_util` ≥5 s técnicos por recorrido, mediana >2×MAD de diferencias; ≥5/6 parejas positivas y medianas positivas AB/BA. Sin regresión relevante de garantías/memoria. |
| Ampliación y parada | Host: una ampliación dirigida, hasta tres pares totales S1/S2/S4 si ruido/signos o agregado a ±5 puntos del umbral. M6: seis pares más como máximo, ≥10/12 positivos; solo con saldo. Si no cabe o persiste incertidumbre, inconcluso/descarte. |

Observación V4-02 de 2026-10-16: S1/S2 cerrados técnicamente; P01 confirma «No los
cronometré». Sus tiempos activos se registran como no medidos, no cero ni pendientes
de reconstrucción. Los contadores exactos de los turnos históricos tienen ventanas
mixtas de trabajo/estudio; no constituyen todavía una comparación de tarea completa.
La repetición propuesta se preparó sin ejecutar y se retiró. El usuario decidió
dejar la percepción humana para uso real sostenido: DECISION-TECHNICAL-SCOPE.md
resuelve expresamente esa limitación. Se conserva el texto de los AC y se difiere
su parte humana sin marcarla superada; los parámetros técnicos quedan fijados en
el protocolo 1.0. No se reutilizan los históricos mixtos como denominadores de ahorro.

Los valores se fijan con la referencia, antes de ver la candidata. No se rebajan
tras un resultado desfavorable. Un cambio posterior conserva protocolo original,
motivo, muestras previas y comienza una comparación identificada por separado.

La baseline principal usa 3.4.3 correctamente: `--compact` cuando aplica, lectura
selectiva, acuerdos vigentes reutilizados y checkpoints solo útiles. Si se dispone
de sesiones reales con uso ineficiente, informarlas como comparación adicional;
no usar una baseline deliberadamente verbosa para atribuir al código todo el ahorro.

Propuesta y autorización de escenario son equivalentes. No dar a la candidata un
plan ya preparado si la referencia tiene que elaborarlo. No eliminar del recorrido
de 4.0 la configuración/clasificación inicial que sí necesita.

### 4.2 Dos niveles de comparación

La especificación operativa vigente de ventanas, unidades, orden, ruido y límites
es MEASUREMENT-PROTOCOL.md/JSON 1.0; concreta esta sección antes de candidata.
El complemento S8 añade el criterio relativo del 20 % y reserva explícita sin modificar esos
archivos. Sus parámetros numéricos son entregable pendiente de V4-02B y deben
quedar congelados antes de medir S8 candidato o diseñar su actividad/optimización;
no se ajustan a resultados de la candidata ni bloquean M1/H2 independiente.

**Técnico determinista:** mismos bytes de entrada, reglas, controles y operaciones
equivalentes. Comparar semántica normativa, decisiones, fuentes, pruebas, efectos y
rechazos. Los nuevos campos diagnósticos se comparan por su contrato, no se exige
igualdad byte a byte de dos formatos intencionadamente distintos. Cualquier
normalización de UUID/tiempo/ruta temporal debe estar declarada previamente; no se
normalizan obligaciones, identidades lógicas, autoridad, errores o evidencia.

Para tiempo, seleccionar cuellos de botella y tamaños representativos dentro del
presupuesto, sin cruzar automáticamente todos los escenarios y tamaños. Ejecutar
secuencialmente seis pares por comparación M6 elegida: tres AB y tres BA, con procesos
nuevos y entorno comparable. A es referencia; B, candidata. Si el ruido impide
decidir, permitir una única ampliación de hasta seis pares dentro del presupuesto
predefinido; después, `inconclusive` y ninguna incorporación basada en esa mejora.
Separar calentamiento y caché del filesystem de los resultados medidos.
Esta serie M6 no es la aceptación S8 de dos parejas ni forma parte del compromiso
base 0.4: solo procede con capacidad real para cumplir el protocolo íntegro.
Registrar carga ajena y excluir una pareja solo por una regla de invalidez fijada
antes de medir, conservando su resultado y motivo. No ejecutar dos benchmarks
simultáneamente. Perfilado intensivo de memoria/CPU se hace en una pasada distinta.

Tamaños de partida: contrato pequeño, medio y grande, reutilizando fixtures de
aproximadamente 100, 500 y 1.500 elementos cuando sean representativos. Documentar
la relación entre tamaño y operaciones, no inflar artificialmente obligaciones.

**Uso real del host:** comparar por separado Codex y Copilot, manteniendo modelo,
configuración, herramientas y condiciones de caché observables. No atribuir a 4.0
una diferencia de modelo, host o política. Usar tareas equivalentes/restauradas,
orden contrabalanceado y anotar aprendizaje de la persona. No transferir soluciones
del primer intento al segundo como si fueran contexto inicial común.

La campaña es escalonada, con evidencia ligada a paquetes concretos:

1. **H2, utilidad temprana:** una pareja S1 en al menos un host previsto, con el
   paquete V4-05A. Son dos ejecuciones por host observado. Detecta problemas antes
   de ampliar capacidades; no acepta la versión final ni acredita ambos hosts.
2. **Piloto de la candidata final:** una pareja para cada S1, S2 y S4 en cada host.
   Primero Codex: seis ejecuciones; Copilot al final añade seis, doce en ambos.
   Registrar variación inicial,
   fricción y problemas; no certificar estabilidad con una única pareja por caso.
3. **Cobertura restante:** una pareja S3, S5 y S6 por host: seis ejecuciones Codex
   primero y seis Copilot al final. Las garantías y la cobertura adversa S7 siguen
   siendo exigibles; no se acredita Copilot por la evidencia Codex.
4. **Ampliación dirigida:** solo en casos preseleccionados con efecto cercano al
   umbral, signos contradictorios o ruido que impida decidir. Hasta tres parejas
   totales por caso primario/host, y siempre dentro del presupuesto restante.

Tope aceptado: **48 ejecuciones completas para toda la campaña**, incluyendo
referencia y candidata, H2, pilotos, intentos fallidos y repeticiones tras corrección;
no son 48 ejecuciones obligatorias ni 48 adicionales. La prueba corta de viabilidad
también consume tiempo/coste del presupuesto y cuenta como ejecución si completa una
tarea. Se aceptan 8 h de persona y 12 h de entorno. M6 tiene además límite de dos
variantes/cuatro horas dentro de los globales. El importe facturado sigue sin medirse.
Las 24 ejecuciones de cobertura final, H2 y repeticiones comparten ese límite. No
agotar la reserva en casos primarios antes de cubrir los restantes.
Reserva 0.4: 7 cargos conocidos + 2 H2 + 24 finales + 2 S8 tempranos + 4 S8 finales
y 4 plazas de contingencia = 43/48. El máximo teórico libre es 5, no saldo acreditado.
Una serie M6 adicional de 12 llevaría a 55: fuera del compromiso base, sin reducir
su protocolo, contingencia o cobertura para hacerla caber. Los componentes cuentan
horas y, si completan tarea, también intento. Las cuatro tareas tienen cotas iniciales
de 4 h; Windows reutilizado reserva 0,5 h dentro de compatibilidad. La viabilidad
integral de horas no está acreditada. Detalle en ADDENDUM-PERFORMANCE.md, §§7–10.

El orden se contrabalancea entre casos/participantes y, al ampliar un mismo caso,
entre parejas. Aprendizaje, rango y muestra real se informan; los resultados son
descriptivos, no una certificación estadística universal. Solo se reutiliza una
muestra si la revisión relevante, entradas, condiciones y protocolo siguen siendo
comparables y existe justificación revisada; nunca se cuentan dos veces sus costes.

**Parada:** un fallo de garantía detiene la variante afectada para corregir o retirar;
una prueba de ahorro nunca compensa ese fallo. Un resultado desfavorable claro se
registra como fallo, no activa repeticiones hasta obtener éxito. Agotar cualquiera
de los límites detiene la campaña y deja criterios sin resolver como `inconclusive`
o `not-run`. Ampliar presupuesto requiere decisión explícita, preservando resultados
y cobertura pendiente; no rebajar garantías ni marcar completa una aceptación parcial.
S7 se cubre principalmente con pruebas técnicas y observación focal de bloqueos.

Si la observación prevista no es viable, reducir alcance mediante decisión registrada
antes de interpretar resultados y declarar la cobertura limitada. Ausencia de acceso,
instalación de candidata no autorizada o métrica no disponible no se convierten en
`passed`; las pruebas técnicas independientes pueden continuar.

### 4.3 Regresión Windows y temporales largos

Se conserva la regresión real existente; V4-14 es propietaria, V4-15 consolida y
V4-16 verifica inclusión y equivalencia del paquete. Desarrolla AC-06/07/08/12/24/25/
26/29/41/44 sin cambiar los 36 originales ni añadir otra tarea/mejora.

- Ruta corta frente a ruta >260 caracteres, TEMP/TMP profundo y espacios/Unicode;
  registrar longitudes reales, runtime/volumen y salidas desde entrypoints públicos.
- Captura/exportación, preparación/aplicación, interrupción/reintento y recuperación
  preservan bytes lógicos, hashes, contrato y archivos ajenos; no anidan copias ni
  prolongan nombres con cada reintento. Limpieza solo de rutas propias verificadas.
- Mantener restricciones de enlaces/contención e integridad. Extracción parcial,
  recursos ausentes, fallo de importación o prueba omitida no equivalen a éxito.
- Reutilizar `test_windows_long_paths`, `path_utils` y `import_bootstrap`; no deducir
  soporte universal ni cambiar configuración global de Windows. La carpeta corta es
  una medida operativa, no evidencia de que la larga funciona.
- Cota documental inicial compartida: 30 min de compatibilidad dentro de 12 h,
  sin alterar timeouts ni checks del gate vigente. No ejecutada en esta revisión;
  corte agotado deja cobertura pendiente. No duplicar S8 por longitudes de ruta.

## 5. Contabilidad completa del coste

La unidad principal es una tarea funcional comparable terminada con la misma calidad,
desde su preparación hasta comprobación/presentación de resultado. La ventana incluye
reintentos, búsqueda, lecturas, ampliaciones, errores, correcciones, controles y
diagnóstico. Separar espera humana externa del trabajo administrativo activo.

| Métrica | Cómo observarla | Qué permite afirmar |
|---|---|---|
| Bytes y caracteres emitidos por el plugin | Capturar stdout final de cada llamada, incluidos sobres; registrar también entradas/salidas de herramientas realmente entregadas al agente. | Reducción de transporte del plugin, no factura del modelo. |
| Tokens de texto atribuible al plugin | Tokenizar el texto capturado con tokenizador y versión declarados, cuando se conozcan. | Medida local de ese texto; no equivale a entradas acumuladas/razonamiento/caché del host. |
| Consumo completo de tokens | Métrica del host por ejecución: entrada, entrada cacheada, salida y otras categorías solo si se exponen. | Comparación de consumo observado en esa cobertura. Ausentes: `not-measured`. |
| Coste facturado | Importe real atribuible a la ventana cuando se exponga; política y periodo comparables. | Ahorro económico observado. No inferirlo de suscripción, bytes o tokens estimados. |
| Operaciones administrativas | Llamadas de preparación, presentación, registro, recuperación y diagnóstico, separadas de herramientas que editan/prueban producto. | Reducción de coordinación; no reducción de controles por ocultarlos en una llamada. |
| Intervenciones humanas | Distinguir aclaración necesaria, decisión nueva, prueba manual y confirmación redundante respecto a una decisión vigente concreta. | Fricción eliminada sin retirar decisiones. No contar todos los mensajes como preguntas inútiles. |
| Trabajo administrativo activo | Medir minutos humanos dedicados a preparar, localizar, reconstruir y registrar información del proceso; separar desarrollar/probar producto y esperar. Anotar también datos/campos reconstruidos y solicitudes de ayuda para poder continuar. | Reducción de esfuerzo humano por caso; agrupar comandos no prueba este resultado. |
| Tiempo | Monotónico para CLI; marcas observadas para tarea y administración. Desglosar modelo, herramientas, diagnóstico, trabajo humano y esperas. | Latencia local/observada; causalidad limitada si cambia el entorno. |
| Memoria y almacenamiento | Pico de proceso/working set cuando se pueda, asignaciones separadas, bytes activos/temporales/históricos al terminar. | Coste de recursos, separado del contexto y de la factura. |
| Calidad | Criterios satisfechos, defectos, obligaciones omitidas, fallos de autoridad y retrabajo. | Condición necesaria de cualquier conclusión favorable. |

La evaluación de tiempo/esfuerzo/percepción humana y su cuestionario están diferidos
por la decisión de alcance de 2026-10-16. No se solicitan fichas ni cronómetros en
esta campaña técnica. Las reglas siguientes se conservan como protocolo histórico,
sin aplicación activa ni sustitución por inferencias de timestamps:

Para tiempo humano, usar intervalos observados con inicio/fin y clasificación
predefinida. Contar un dato reconstruido una vez por intervención y registrar causa;
separar ayuda de procedimiento de una aclaración funcional necesaria. La resolución
y variación deben permitir apreciar `delta_admin`; si no, el resultado es inconcluso.
No introducir un formulario por comando para medir la mejora: recoger evidencia en
la observación de prueba y consolidarla por tarea. Comprensión se evalúa con la
misma rúbrica de alcance, decisión, pruebas y pendientes en referencia y candidata.
Con P01 se utilizará cronometraje autoinformado por bloques y una ficha por caso.
Registrar resolución, tiempos mixtos/desconocidos e interrupciones. No inferir
actividad humana de los timestamps del chat ni presentar autoinforme como observación
independiente. La ficha y la rúbrica son coste del estudio separado del producto.

No sumar dos veces una operación compartida entre tareas. El coste de un intento
fallido se conserva; si después se completa, pertenece al coste acumulado de ese
resultado. Si no se completa, informar fracaso y coste, sin compararlo como una
solución barata. Mantener texto único y acumulado por separado.

La medición del transporte completo se realiza desde fuera del objeto medido para
evitar una autorreferencia de tamaño. Si se emite un contador interno, declarar qué
campos incluye; contrastarlo con la captura final. Los bytes guardados fuera del
modelo se cuentan en almacenamiento/tiempo y se añaden al transporte si luego se leen.

## 6. Objetivos propuestos y regla de aceptación

E1/E2/E3 son objetivos del plan validado; el beneficio útil técnico se fija con la
referencia V4-02 antes de observar candidata. La fricción/E5 se difiere a uso real
según DECISION-TECHNICAL-SCOPE.md; no condiciona el cierre técnico ni se acredita
con menos llamadas. El texto original de E5 se conserva debajo. No son resultados,
SLA ni nueva política corporativa. Si se cambian
después, conservar el criterio original y no usar el cambio para convertir un fallo
ya observado en éxito.

| Objetivo | Umbral propuesto | Aplicación y límite |
|---|---|---|
| E0 · Garantías y calidad | Cero pérdidas conocidas de G1–G10 y cero defectos materiales abiertos introducidos por la candidata en los casos ensayados. | Precondición de toda mejora. No demuestra ausencia universal de defectos. |
| E1 · Transporte | Reducción mediana de al menos 30 % del volumen acumulado emitido por el plugin en los casos primarios. | Comparación por host/modo cuando corresponda, sin perder contenido necesario. No prometer igual ahorro de tokens. |
| E2 · Coordinación del agente | Reducción mediana propuesta de al menos 20 % de llamadas administrativas en S1/S2 y cero confirmaciones redundantes introducidas. | Indicador de coordinación; no acredita menor tedio sin E5. Si la referencia ya tiene cero repeticiones, conservarlo, sin inventar un porcentaje. |
| E3 · Tokens de tarea completa | Reducción mediana de al menos 15 % en los casos primarios con métrica real comparable. | Si no existe métrica del host, queda sin medir. Puede probarse ahorro de transporte, pero no se acepta una afirmación de ahorro total de tokens. |
| E4 · Beneficio útil de M6 | Cada variante incorporada supera `delta_util` predefinido en beneficio absoluto del recorrido, por encima del ruido, con frecuencia observada y mantenimiento/riesgo proporcionados. Sin regresión reproducida de garantías, recorrido completo o memoria relevante. | Medir fase y recorrido; un 15 % local ya no es requisito ni prueba suficiente. Perfil, estimaciones de frecuencia y costes se separan. Si no compensa o se agota presupuesto, descartar sin bloquear mejoras independientes. |
| E5 · Fricción humana | En los casos S1/S2 con coste reducible identificado en V4-02, reducción mediana de minutos administrativos activos por caso/host de al menos `delta_admin`; no aumentar datos reconstruidos, ayuda procedimental, retrabajo ni errores de comprensión/decisión. | Exigir ahorro absoluto apreciable, además de llamadas. Si la referencia no tiene trabajo reducible, conservar cero; si ningún caso lo tiene, no se acredita reducción de tedio y debe resolverse ese alcance en V4-02. No sustituir casos después de ver la candidata. |

E0 es obligatorio en todas las comparaciones. E1/E2 son objetivos de transporte y
coordinación; E5 acredita la menor fricción. E3 solo acredita consumo real con su
cobertura observable y decisión de alcance previa. E4 condiciona cada variante M6,
no la existencia de una optimización. Informar diferencias absolutas además de
porcentajes; una mejora pequeña de un coste frecuente puede ser útil y una mejora
porcentual grande de un coste despreciable puede no justificar mantenimiento.
Para el caso añadido, AC-43 exige la mejora temporal ≥20 % del recorrido frente a
3.4.3, con calidad y límites técnicos intactos. Ahorrar ≥5 s en M6 no demuestra
ese objetivo S8. E4 puede cerrar con descarte de una
variante, pero la incidencia operativa sigue abierta hasta su disposición explícita.

Calcular para cada pareja comparable `reducción = 1 - coste_candidata / coste_referencia`.
Si la referencia es cero, informar diferencia absoluta. Presentar mediana de las
reducciones por caso/host, rango de muestras y agregación de los casos primarios con
peso igual declarado. No mezclar bytes con tokens ni promediar hosts para ocultar
que uno empeora. No sumar porcentajes de mejoras que actúan sobre el mismo coste.

Una regresión superior al 10 % en transporte/tokens/tiempo de un caso exige revisar
causa y repetir una comparación focal controlada; si se reproduce, corregir o
excluir la variante. Este umbral activa investigación, no autoriza empeorar un 9 %
ni perder garantías. Una variación menor pero reproducible también se documenta.
Cuando el ruido o la muestra no permitan decidir, usar `inconclusive` y fijar una
ampliación acotada; no repetir indefinidamente hasta obtener una cifra favorable.

En el uso real posterior, fuera de esta campaña, la comprensión podrá valorarse
con preguntas sobre el cambio, alcance, pruebas pendientes
y efectos de la decisión. Son observaciones específicas de aceptación, no otro paso
del flujo de desarrollo del producto. Un participante no se declara representante
de todos los equipos; la cualificación del resultado refleja la muestra real.

### Coste inicial y amortización

En S4 medir por separado clasificación/configuración inicial y mantenimiento de
clasificaciones tras cambios. Mostrar el coste del primer trabajo y del conjunto
de trabajos observados. Para cada unidad homogénea de coste:

`coste_nuevo(N) = coste_inicial + suma(costes_recurrentes_1..N)`.

Comparar contra la referencia para ese mismo N. Se puede estimar el punto de
amortización con ahorro recurrente observado positivo, declarando que es una
proyección; si no es positivo, no hay amortización demostrada. No justificar un
coste real actual con un número inventado de futuras tareas. Conservar la opción
de no clasificar masivamente documentación que no se va a reutilizar.

## 7. Informe, estados y trazabilidad

La evidencia se conserva fuera de los bytes del runtime medido. Reutilizar áreas
existentes de informes y temporales, con responsable y retención; no crear otra raíz
de soporte ni incluir diálogos sensibles en el repo. El repositorio conserva el
protocolo, fixtures pequeños y referencias/manifiestos necesarios para reproducir.

Cada muestra identifica: candidato y hashes, baseline, caso/revisión, host/modelo,
configuración, actor de prueba o participante observado, entradas/sujeto, comandos,
límites, calidad, tiempos/costes, evidencia y cualquier exclusión. Los resultados
humanos se recogerán en el uso real posterior; los actores sintéticos solo prueban
la mecánica de permisos y no acreditan identidad o aceptación humana.

Estados de una comprobación: `passed`, `failed`, `not-run`, `not-measured`,
`inconclusive` o `not-applicable` con fundamento. No convertir un estado ausente en
superado. Los reportes separan:

1. Garantías y calidad técnica.
2. Compatibilidad, actualización y recuperación.
3. Transporte, operaciones y rendimiento local.
4. Tokens/coste observado de tarea completa.
5. Comprensión y fricción reales por host.
6. Estado de candidata, release, instalación y activación.

Si E0 falla, la mejora afectada se rechaza. Si E1/E2 no se alcanzan, se documenta
qué hipótesis falló y se revisa antes de aceptar el objetivo técnico de eficiencia.
E5/AC-36 permanecen diferidos a uso real y no bloquean ese cierre técnico.
Menos llamadas sin E5 no permite declarar menor tedio. Si E3 no se puede medir,
aplicar la decisión de alcance de V4-02: se puede acreditar transporte y trabajo
administrativo, pero el ahorro total de tokens sigue `not-measured`; no redefinirlo
tras los resultados. Si desaparece una métrica antes disponible, registrar incidencia
y reevaluar la aceptación afectada. Si E4 no se alcanza,
no incorporar esa optimización; no bloquear mejoras independientes ya demostradas.

La observación de ambos hosts es exigible para afirmar mejora observada en ambos.
El usuario ha aplazado Copilot al final: sus comprobaciones no bloquean cerrar la
referencia Codex si se cumplen sus condiciones, pero conservan su estado pendiente
y el protocolo fijado. Antes de comparar Copilot se comprueban métricas/configuración
y se registra su referencia 3.4.3 sin adaptar casos a resultados de la candidata.
Una aceptación técnica o publicación autorizada con reservas no cambia los estados
de canales pendientes ni permite afirmar que toda la 4.0 ha sido aceptada.

## 8. Validaciones durante esta preparación documental

En el turno que prepara este plan solo corresponde comprobar coherencia de tareas,
dependencias, cobertura de criterios, enlaces y ausencia de modificaciones de
producto; ejecutar el contrato estático del plugin y revisar el diff. No ejecutar
implementaciones, benchmarks de la candidata inexistente, gate de release, builds,
instalaciones ni migraciones para validar la redacción del plan.

La evidencia de esa revisión documental se comunica al entregar los archivos;
no se usa como `passed` de ningún AC funcional de 4.0.

Actualización técnica: [Git/Windows V4-05](RESULTS-V4-05-GIT-WINDOWS.md) repite el
módulo completo y documenta las comprobaciones finales focales, las condiciones
soportadas y los límites del ahorro. No modifica los criterios congelados.

Actualización V4-05A: [resultados](RESULTS-V4-05A.md), [estado](v4-05a-progress.json)
y [continuación necesaria H2](V4-05A-HOST-HANDOFF.md). El S1 sintético final pasa
36/36 comprobaciones y se superan 14 regresiones distintas; siete artefactos finales
son reproducibles. Son evidencia técnica y de paquete. AC-34 conserva su texto y no
se marca superado sin la pareja real con instrucciones/runtime coherentes en Codex.
Los dos intentos completos nuevos se contabilizan; no se reemplazan umbrales ni
reservas de H2/final/S8 y no se acredita ahorro total de tokens o percepción humana.

Revisión posterior V4-05A: [dictamen y paquete vigentes](REVIEW-V4-05A.md).
Tres regresiones focales finales pasan, 14 observaciones auditadas por ID/contenido;
se conserva la evidencia anterior por identidad de scripts, sin repetir un S1 completo
ni Windows. Cero intentos completos adicionales; AC-34/H2 continúan pendientes y no
se instala el paquete ni se inicia V4-06.


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
