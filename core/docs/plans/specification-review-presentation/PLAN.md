# Plan de implementación de las presentaciones para decisiones del usuario

Fecha: 2026-10-08. Revisión: 3.
Estado: **implementación local autorizada y realizada; verificación y límites en [IMPLEMENTATION.md](IMPLEMENTATION.md)**.

El objetivo es que el usuario reciba información clara, suficiente y proporcionada
en todos los momentos de aclaración, revisión, autorización y aceptación de una
aplicación. Las especificaciones conservarán el detalle técnico por componente y
los siete apartados acordados. Los demás eventos tendrán una estructura propia
que explique el contenido, las consecuencias y el alcance de la decisión. Las
instrucciones se cargarán según el evento, conservando las reglas comunes y todo
el contrato necesario; la eficiencia se medirá sin sacrificar claridad ni calidad.

La revisión 2 incorporó el [análisis de los eventos de validación](VALIDATION-EVENTS.md):
57 acciones públicas v3, sus variantes y las decisiones documentadas en las skills,
agrupadas en 33 familias. Amplió la revisión 1 antes de su implementación y conservó
los identificadores PV-01 a PV-08. Añadió PV-09 a PV-13 y criterios específicos para
los demás eventos. La revisión 3 incorpora el [análisis de eficiencia del contexto](CONTEXT-EFFICIENCY.md),
revisa la organización propuesta y añade PV-14 y PV-15 y AC-31 a AC-40. La ruta del
plan se conserva para mantener los enlaces previos.

La petición «haz el plan de implementación» autoriza preparar este documento.
La petición posterior autoriza revisar los demás eventos e incluir las mejoras
necesarias en este plan. La última petición autoriza analizar la eficiencia del
contexto y proponer los cambios de skills y recursos que se justifiquen.
La petición posterior «impleméntalo todo» autoriza ejecutar las tareas del plan.
La cobertura y los estados de comprobación se registran en [IMPLEMENTATION.md](IMPLEMENTATION.md).
Publicación, instalación, migración de consumidores, commits
y push tienen autorización separada conforme a [AGENTS.md](../../../AGENTS.md).
Los identificadores PV son tareas de mantenimiento del plugin, no registros de un
proyecto consumidor ni asignaciones a personas reales.

## Base y alcance

La base inspeccionada es la rama `codex/document-storage-growth`, HEAD
`628d15c3d8759c6deb70d88bda9f045562c485a6`, con cambios locales anteriores en
almacenamiento, migración, recorridos y distribución. Ese SHA identifica el commit
de partida, no el contenido completo del árbol examinado. Al iniciar la ejecución
se revisará el estado vigente y se conservará el trabajo concurrente.

### Requisitos fijados por el usuario

- El mensaje de validación tendrá un título principal que describa la tarea o
  cambio de la aplicación y los siete títulos de segundo nivel acordados.
- Cada apartado contendrá información suficiente, con lenguaje claro y conciso.
- La comunicación estará centrada en la aplicación. Los términos y mecanismos
  administrativos internos del plugin quedarán fuera del mensaje de validación.
- La solución técnica explicará la afección en los componentes reales de la
  arquitectura y el diseño que se propone en cada uno, con detalle validable.
- La propuesta se ha revisado críticamente antes de preparar este plan.
- El resto de eventos de validación se ha analizado para incluir mejoras similares
  de estructura y contenido, adaptadas a lo que la persona necesita decidir.
- Se evaluará la eficiencia de gestión del contexto y la reorganización de skills
  y recursos cuando reduzca carga innecesaria o riesgo de interpretación errónea.

El diseño de implementación de este documento es una propuesta técnica para
cumplir esos requisitos. Los mecanismos internos elegidos no se atribuyen al usuario.

### Hechos observados

- [La guía de definición](../../../skills/lks-sdd-define/references/v3.md) enumera
  el contenido de la propuesta, pero no impone la presentación completa acordada.
- [review](../../../scripts/v3_lifecycle.py) devuelve descripciones, datos y
  referencias; no produce actualmente el mensaje con los siete apartados.
- [proposal_ready](../../../scripts/v3_approval.py) comprueba campos presentes,
  contenido mínimo y pendientes críticos. Es compartida por planificación y
  comprobaciones de vigencia, por lo que endurecerla sin distinguir operaciones
  podría afectar acuerdos anteriores.
- En una reproducción aislada realizada durante el análisis de esta conversación,
  `review` admitió `solution="Actualizar el servicio"`; un requisito relacionado
  figuró en el descriptor, pero su texto no apareció en la salida; y un pendiente
  crítico produjo una excepción en vez de una presentación del borrador. Esta
  observación orienta PV-01; no es evidencia de las pruebas de la implementación.
- [El contexto existente](../../../scripts/v3_context.py) ya contempla fuentes
  literales, adjuntos, relaciones y contenido sin clasificación. Se revisará su
  reutilización antes de introducir otro selector de obligaciones.
- [Las intervenciones](../../../scripts/v31_guidance.py) ya agrupan decisiones por
  persona, pero sus objetos y causas no sustituyen la explicación del plan, del
  encargo o del resultado. [El resumen técnico de operaciones](../../../scripts/v3_storage.py)
  tampoco distingue por sí solo una decisión ausente de una escritura ya autorizada.
- Las seis entradas de skills tienen entre 21 y 29 líneas; las referencias v3,
  entre 12 y 16. Las reglas comunes y el recorrido integral suman 12.208 caracteres
  y mezclan orientación transversal con procedimientos específicos. Las medidas
  estáticas y sus límites figuran en el análisis de contexto; no son tokens facturados.

### Trabajo incluido

Se cubren todas las familias de decisiones del inventario: configuración, adopción,
migración, definición, tecnología, visuales cuando procedan, observaciones, planes,
ejecución, encargos, relevos, pruebas humanas, integración, aceptación, correcciones,
excepciones, revocación, recuperación y acciones externas dentro de capacidades
disponibles. La implementación se integrará en el recorrido v3.1 vigente y en sus
adaptadores Codex y Copilot. Las decisiones compuestas conservarán sus efectos separados.

Se conservarán las seis skills y su invocación implícita, los Markdown canónicos,
la historia y las aprobaciones válidas. Las consultas serán de solo lectura.
Los eventos informativos mejorarán su explicación cuando sea necesario, sin
convertirse en validaciones nuevas. La entrevista breve seguirá siendo adaptativa.
Se incluye reorganizar instrucciones por familias, hacer explícitas sus dependencias,
mantener una fuente por regla y comprobar la continuidad tras cambios de evento o
compactación. Se medirá la tarea completa y se distinguirá ahorro de instrucciones
de suficiencia de los datos del proyecto.

Quedan fuera nuevas interfaces gráficas, servicios, MCP, conectores, hooks, apps,
agentes ejecutables, una nueva pila tecnológica y cambios en `specs/canonical/`.
Se excluyen mensajes sin relación con estas decisiones, el selector experimental
de contexto, el desarrollo en consumidores reales y la reactivación o migración
funcional de capacidades históricas bloqueadas. Los casos de cliente, Jira,
visuales y retención se tratarán según su disponibilidad real, sin inventar APIs.

## Comportamiento que debe recibir el usuario

La presentación completa de especificaciones seguirá esta estructura, con exactamente un título
principal y estos siete títulos de segundo nivel, en este orden:

```markdown
# Nombre concreto del cambio en la aplicación

## Objetivo

## Alcance incluido y excluido

## Comportamiento esperado

## Solución técnica

## Impacto

## Criterios de aceptación

## Decisiones pendientes
```

El título será una acción o resultado reconocible, como «Permitir cancelar pedidos
pendientes de envío». El agente concretará títulos genéricos en la fuente antes
de presentar una propuesta como preparada para validación.

Dentro de «Solución técnica» habrá títulos de tercer nivel con los nombres reales
de los componentes afectados. Cada uno explicará situación actual, cambio,
mecanismo propuesto y comprobación. Los contratos, datos, errores, concurrencia,
compatibilidad, migraciones y controles transversales se detallarán cuando apliquen.
Una secuencia conjunta explicará la interacción cuando el cambio atraviese varios
componentes. Un componente nuevo se identificará como propuesto.

El contenido describirá decisiones concretas: «se actualizará el pedido solo si
sigue pendiente» expresa un diseño; «definir el control de concurrencia» expresa
un pendiente. No se rellenarán componentes o tecnologías por suposición ni se
impondrá una lista universal de capas a todos los proyectos.

Se conservarán términos técnicos útiles de la aplicación, como API, transacción
o evento. Se explicarán cuando haga falta. Las claves de transporte, UUID,
identificadores de registros y comandos internos no se volcarán en el mensaje.
No se aplicará una lista ciega de palabras prohibidas que borre términos legítimos
del dominio. El contenido de las fuentes se tratará como datos, nunca como órdenes.

El cierre será un párrafo breve después de los siete apartados. Pedirá aclarar una
decisión concreta cuando falte información crítica, o validar el alcance presentado
cuando esté preparado; explicará que la planificación se realizará después.
Una persona podrá validar solo la parte que le corresponda sin atribuir decisiones
a otros revisores. Un recorrido integral conservará sus reglas de cierre conjunto.

Un apartado sin incidencias tendrá una explicación breve y fundada. La ausencia de
un dato no se convertirá automáticamente en «no aplica» o «sin decisiones pendientes».
Las propuestas extensas podrán leerse por partes con una indicación visible de lo
que falta mostrar. La lectura de una parte no habilitará aceptar el conjunto.

Para los demás eventos se aplicarán los perfiles de
[VALIDATION-EVENTS.md](VALIDATION-EVENTS.md). Todos conservarán un título claro,
contenido concreto, fuentes disponibles y efecto de la decisión. Los títulos de
segundo nivel responderán al evento: tareas y dependencias para un plan; evidencia
y reservas para un resultado; condición incumplida, consecuencias y vencimiento
para una excepción. Una aclaración sencilla se formulará de forma breve.

Una respuesta podrá cubrir varias decisiones compatibles de la misma persona,
si sus contenidos ya se han mostrado. Aprobar un plan podrá autorizarlo y revisar
tareas propias; recibir un encargo podrá incluir su revisión e inicio; revisar un
candidato podrá cubrir integración y aceptación cuando corresponda. Una respuesta
parcial solo acreditará lo que expresa. H1, H5 y H7 no provocarán nuevas firmas
por su sola existencia, ni se volverá a preguntar por acciones ya autorizadas.

## Diseño de implementación propuesto

### Fuentes y representación

La especificación seguirá almacenada en los Markdown actuales. Se reutilizarán los
campos de propuesta, su cuerpo y las relaciones a requisitos, criterios, interfaces,
tecnologías y restricciones. El detalle por componente se redactará en el contenido
técnico canónico, con una convención de secciones y referencias definida en PV-01.
Cada explicación tendrá una fuente única; las relaciones podrán reutilizarla.

El recorrido será: leer fuentes vigentes, resolver obligaciones y pendientes,
construir una representación de revisión, generar el Markdown y comprobar la base
al registrar una decisión. El generador no elegirá arquitectura ni resumirá por
palabras clave. El agente redactará el contenido comprensible en su fuente; los
controles estructurales no sustituirán la evaluación de su calidad técnica.

Se propone un módulo compartido `scripts/v3_decision_presentation.py` con funciones
separadas para reunir contenido, analizar la intervención necesaria y producir el
mensaje. Contendrá adaptadores acotados para los perfiles del inventario; no será
un motor de ejecución ni un registro extensible de órdenes arbitrarias.

Se añadirá `decision-view` como consulta de solo lectura con tipos de entrada
cerrados: evento soportado, objetos o cambios propuestos y actor cuando sea necesario
para determinar la decisión que le corresponde. `review` conservará su uso actual
para especificaciones y reutilizará el mismo módulo. El nuevo comando estará en
la lista de consultas de `v3_current.py`; no añadirá una skill ni ejecutará cambios.
Las capacidades históricas no disponibles devolverán una explicación de ese límite.

Los adaptadores admitirán fuentes distintas según el evento: propuesta vigente;
plan y tareas; oferta de relevo; candidato y pruebas; excepción; o cambios concretos
de configuración y migración. Será posible mostrar una propuesta de configuración
antes de inicializar el proyecto. No se fabricará una declaración de aprobación
para satisfacer una función que exige `statement` al preparar un registro de decisión.

La salida de `review` añadirá una presentación sin retirar las claves actuales de
respuestas válidas. `decision-view` utilizará el contrato común siguiente, cuyo
contenido se restringirá por perfil:

| Dato interno | Contenido y uso |
|---|---|
| Versión de presentación | Identifica el formato de la salida; no migra el método ni el schema del proyecto. |
| Tipo de evento y título | Perfil reconocido y cambio u objeto concreto que la persona debe revisar. |
| Secciones | Bloques trazados a fuentes y obligatorios para el perfil. Las especificaciones conservan exactamente sus siete apartados. |
| Componentes e interacción | Vista derivada del contenido técnico canónico, con detalle y aplicabilidad. |
| Fuentes y correspondencias | Revisión, localizador y huella de las fuentes usadas por cada bloque. Se mantienen fuera del cuerpo visible. |
| Recursos de instrucciones | Referencias cerradas a las guías necesarias del runtime fijado, con familia y motivo; separadas del contenido del proyecto y del mensaje visible. No acreditan que se hayan leído. |
| Intervención e incidencias | Distingue aclaración, decisión pendiente, acción ya autorizada, información y bloqueo; informa de lo que falta y de quién puede decidir. |
| Base presentada | Alcance y huellas suficientes para detectar cambios antes de registrar una decisión. |
| Markdown | Mensaje final con la estructura acordada y enlaces de texto comprensible al detalle. |

La base presentada dependerá del evento. Un plan incluirá tareas y límites de
ejecución; un relevo incluirá destinatario, porción y estado; un resultado incluirá
candidato y evidencia; una excepción incluirá regla, efecto y vencimiento; un envío
incluirá contenido y destino. No se sustituirán esas bases por la huella genérica
de la propuesta. El alcance individual, las agrupaciones y las decisiones ya
vigentes procederán de los predicados del núcleo, sin otro motor de autoridad.

La correspondencia de bloques con fuentes permite comprobar procedencia; no prueba
por sí sola equivalencia semántica. Una fuente contradictoria o una obligación sin
correspondencia requerirá aclaración. No se eliminarán condiciones para cumplir un
límite arbitrario de palabras. Los límites reales de lectura o salida se comunicarán
y bloquearán la aprobación completa mientras falte contenido necesario.

Se reutilizarán lectores, referencias a objetos e inventarios vigentes. La vista se
generará bajo demanda, sin guardar una copia de la propuesta ni crear un registro
por cada consulta. La deduplicación conservará cada condición distinta y su ámbito.

### Organización y carga de instrucciones

Se aplicará la organización de [CONTEXT-EFFICIENCY.md](CONTEXT-EFFICIENCY.md):
seis entradas breves, núcleo compartido de garantías, familias de decisión y
detalles condicionados. `USER-DECISIONS.md` será un índice breve con reglas comunes;
los perfiles completos vivirán en `docs/decision-guides/`, agrupados inicialmente
en nueve recursos coherentes. No se creará una skill ni un archivo por evento.

El catálogo finito de perfiles enlazará esos recursos y sus dependencias. La misma
correspondencia se usará para `instruction_refs` y para validar el índice documental.
El índice también permitirá seleccionar la guía antes de ejecutar una consulta,
sin depender de un proyecto inicializado o de una propuesta lista para aprobar.
La selección dependerá de acción, finalidad, objetos y condiciones observadas.
Las decisiones compuestas reunirán sus recursos sin repetirlos; una condición nueva
ampliará la lectura. Una combinación desconocida se aclarará sin inferir permiso.

Las reglas comunes de autoridad, vigencia, suficiencia y efectos externos seguirán
disponibles. Solo se moverán los procedimientos específicos, con una matriz que
identifique el destino de cada regla y la condición de carga. `V31-REVIEW.md`
conservará orientación y agrupaciones; `V3-OPERATIONS.md`, la referencia única de
campos consultable por bloques completos. Los llamadores tendrán enlaces directos.

Estas instrucciones pertenecen al runtime fijado y no a los documentos del
consumidor. Su selección no sustituye la lectura literal de obligaciones, adjuntos
y dependencias del proyecto, ni activa el selector reducido de `v3_context.py`.
Tras compactación, chat nuevo o cambio de fuentes, se releerá lo necesario. Solo se
evitan relecturas cuando el contenido íntegro sigue disponible y vigente en ese chat.

La comprobación medirá instrucciones y trabajo total, con igual funcionalidad y
controles. Se distinguirán estimaciones, consumo observado y coste no disponible.
La reducción de errores seguirá siendo una hipótesis hasta observar comportamiento;
las comprobaciones de enlaces y catálogo no acreditan comprensión del agente.

### Presentación de borradores y controles de decisión

La lectura de una propuesta incompleta no dependerá de superar el control de
aprobación. `review` podrá mostrar el contenido disponible y sus pendientes.
Los errores de integridad del proyecto seguirán siendo errores; no se convertirán
en una revisión aparentemente completa.

El mismo análisis de preparación se reutilizará al intentar registrar nuevas
aprobaciones o conformidades positivas. Se cubrirán `approve`, `review-proposal`
y `close-proposal`, incluidas sus formas agrupadas, y los puntos de decisión que
correspondan a PV-09 a PV-13. Se comprobará la suficiencia propia de cada evento,
sin exigir los campos de especificación a una aceptación de resultado o a un relevo.
Un comentario, un rechazo o una petición de cambios seguirán siendo posibles aun
cuando el contenido positivo no esté listo para aprobación.

Las decisiones positivas se asociarán al alcance y a la base efectivamente
presentada. Si cambia una obligación, interfaz o condición relevante, será necesario
revisar la versión nueva antes de aprobar. La referencia técnica a lo presentado se
incorporará al registro de decisión existente, sin una segunda confirmación humana
ni un documento duplicado. Un hash acredita correspondencia de contenido, no que
una persona haya visto o comprendido el mensaje.

Las rutas de consulta de estado y próximas intervenciones también deberán tolerar
borradores incompletos. Se mantendrán los límites de autoridad y alcance de las
aprobaciones parciales, las revisiones integrales y las excepciones existentes.
Cambiar el nombre de una operación o usar una composición no eludirá los controles.

No se exigirá un nuevo registro de presentación por cada transición técnica. Si la
decisión explícita y vigente de la sesión cubre la acción y su contenido, se reutiliza.
Una petición de cambios o un rechazo se registrará con la evidencia disponible;
los datos que falten se pedirán sin reinterpretar la respuesta como aprobación.

### Compatibilidad e historia

Se separarán los controles de una decisión nueva de la evaluación de acuerdos ya
registrados. No se añadirán requisitos de presentación retroactivos a la función
compartida de vigencia. Una aprobación anterior válida seguirá siendo reutilizable;
un cambio material seguirá invalidando las decisiones afectadas según el contrato.

Los datos antiguos se podrán consultar, indicando las carencias reales sin generar
una falsa solución técnica. Para una nueva aprobación sobre contenido insuficiente,
la definición deberá completarse. La presentación por sí sola no alterará las
huellas de la especificación ni fabricará una nueva revisión.

PV-01 fijará el contrato exacto de entrada y salida, el ámbito de las comprobaciones
nuevas y cómo reconocer los registros que incorporan la base presentada. PV-06
probará lectores y runtime fijado. Si se descubre que una garantía exige cambiar
el contrato documental o migrar datos, se presentará ese cambio concreto antes de
implementarlo; este plan no autoriza una migración implícita.

La garantía corresponde al runtime que incorpore el cambio. Los runtimes anteriores
no la adquieren por cambiar la documentación o instalar una versión global. Se
preparará la distribución sin activar instalaciones ni seleccionar una release.

## Tareas y dependencias

La ejecución propuesta es secuencial. Un implementador puede realizar todas las
tareas técnicas; las comprobaciones humanas corresponden a participantes disponibles
y autorizados. No se crean agentes ni se asignan personas por inferencia.

Las dependencias de contrato exigen una definición revisada; las de implementación
exigen que exista el resultado; las de verificación exigen sus pruebas superadas.
Todas las tareas comienzan en **pendiente**.

| Tarea | Resultado | Dependencia | Criterios principales |
|---|---|---|---|
| PV-01 | Contrato común, catálogo de eventos, reglas de carga y casos de referencia | Plan autorizado | AC-01 a AC-04, AC-10, AC-12, AC-16 a AC-18, AC-30 a AC-33 |
| PV-02 | Lectura completa y presentación de pendientes | PV-01, contrato | AC-05, AC-06, AC-11, AC-13 |
| PV-03 | Generador común y perfil de especificaciones | PV-02, implementación verificada | AC-01 a AC-05, AC-11 a AC-13, AC-29, AC-30, AC-34 |
| PV-04 | Decisiones nuevas vinculadas al contenido presentado | PV-03, implementación verificada | AC-07 a AC-10 |
| PV-05 | Integración de todos los perfiles en las seis skills | PV-04 y PV-09 a PV-14, implementación | AC-02, AC-06, AC-07, AC-14, AC-17, AC-18, AC-30, AC-31, AC-36 |
| PV-06 | Compatibilidad de distribución y runtime | PV-05, implementación | AC-10, AC-14, AC-28, AC-38 |
| PV-07 | Verificación conjunta y revisión del cambio | PV-02 a PV-06 y PV-09 a PV-14, verificación | AC-01 a AC-14 y AC-16 a AC-38 |
| PV-08 | Observación del mensaje y contexto real en ambos hosts | PV-07, PV-15 y entorno autorizado | AC-15, AC-17, AC-18, AC-30, AC-36, AC-39, AC-40 |
| PV-09 | Configuración, adopción, migración y reconciliación | PV-03, implementación verificada | AC-19, AC-20, AC-27, AC-29 |
| PV-10 | Plan, autorización, encargo, relevo y continuidad | PV-04, implementación verificada | AC-17, AC-18, AC-21, AC-22, AC-27 |
| PV-11 | Verificación, integración, aceptación y correcciones | PV-04, implementación verificada | AC-23 a AC-25, AC-27 |
| PV-12 | Excepciones, revocación, recuperación y permiso externo | PV-04, implementación verificada | AC-17, AC-26 a AC-29 |
| PV-13 | Aclaraciones y decisiones técnicas, visuales o condicionales | PV-03, implementación verificada | AC-02, AC-03, AC-28, AC-30 |
| PV-14 | Recursos por familias y selección explícita de instrucciones | PV-03 y PV-09 a PV-13, implementación | AC-31 a AC-38 |
| PV-15 | Comparación técnica de carga y protocolo de comportamiento | PV-07, verificación | AC-39, AC-40; parte observada se completa en PV-08 |

### Contrato de presentación y ejemplos

PV-01 definirá `docs/USER-DECISIONS.md` como índice breve y referencia de reglas
comunes de presentación. Fijará la correspondencia única entre perfiles y recursos
de `docs/decision-guides/`, su contenido mínimo, fuentes, efectos y dependencias.
El formato de especificaciones y su detalle técnico tendrán una fuente completa
en la familia correspondiente, sin cargar los otros perfiles para usarla.
Concretará los tipos de entrada de `decision-view`, la correspondencia con las
fuentes y el contrato derivado. Reutilizará tipos y lectores existentes; no añadirá
una segunda especificación en JSON. El inventario EV servirá de cobertura y
se actualizará cuando cambie la superficie de operaciones. Se recogerá la medición
inicial, las reglas que deben permanecer comunes y el destino propuesto de las que
se trasladen. La estructura se revisará antes de añadir todos los perfiles.

Se prepararán casos sintéticos pequeños de cambio aislado, cambio entre componentes,
arquitectura desconocida, propuesta extensa, revisión parcial, plan, resultado,
excepción y configuración anterior a la inicialización. El resultado
esperado incluirá obligaciones concretas y una explicación técnica suficiente.
Se repetirá la reproducción de los tres problemas observados para conservar una
base comprobable. Las personas y los proyectos de prueba serán ficticios.

Salida: contrato de entrada y salida concreto, ejemplos y matriz de casos que
permitan implementar PV-02 a PV-04 sin decidir requisitos funcionales adicionales.
Los ejemplos se mantendrán en la guía o en fixtures, evitando archivos redundantes.

### Lectura de obligaciones y pendientes

PV-02 trabajará en `scripts/v3_lifecycle.py`, el nuevo módulo y, únicamente cuando
sea necesario, las utilidades reutilizables de `scripts/v3_context.py`. Revisará
las llamadas de consulta en `scripts/v3_guidance.py` y `scripts/v31_guidance.py`.

La consulta leerá descripción, datos, obligaciones relacionadas, reglas globales,
interfaces y adjuntos necesarios. Ampliará las fuentes cuando el ámbito sea incierto.
Separará fuentes de negocio y técnica de los metadatos de gobierno que deben
permanecer internos. Una relación ausente no demostrará que algo no aplica.

Se evitará llamar a predicados de aprobación como requisito previo para mostrar
un borrador. Las incidencias conservarán su causa y el alcance afectado. Las
consultas no crearán checkpoints, decisiones, copias ni cambios en el índice.

Salida: representación completa con fuentes, pendientes y alcance de revisión;
pruebas de permisos enlazados, excepciones, relaciones entrantes y falta de datos.

### Generación del mensaje

PV-03 implementará el generador en `scripts/v3_decision_presentation.py`, añadirá
su resultado a `review` y conectará `decision-view` en `scripts/v3_cli.py` y
`scripts/v3_current.py`. Los encabezados, su orden y el cierre de cada perfil serán
comunes a ambos hosts. La información técnica se organizará por componente real.
El catálogo de perfiles contendrá referencias de instrucciones propias del runtime;
la salida las separará del texto visible y de las fuentes del proyecto. PV-14
completará su selección para las familias restantes y sus decisiones compuestas.

Se preservarán números, negaciones, condiciones, tipos, límites, alternativas y
excepciones. Los títulos y enlaces recibidos se tratarán de forma que no puedan
romper la estructura Markdown. Las instrucciones incrustadas en una fuente no
alterarán el comportamiento del agente. El diagnóstico de vocabulario no borrará
silenciosamente una cláusula necesaria para decidir.

Salida: Markdown determinista para las mismas fuentes y contrato de presentación,
con correspondencia de sus bloques. Una propuesta incompleta tendrá una presentación
útil para aclararla y no una solicitud de aceptación global.

### Registro de decisiones y conservación de acuerdos

PV-04 modificará los puntos de decisión nuevos de `scripts/v3_authoring.py` y
`scripts/v31_review.py`, con utilidades en `scripts/v3_approval.py` si son necesarias.
Los predicados históricos permanecerán diferenciados de la preparación nueva.

Se volverán a comprobar fuentes, alcance y preparación antes de una conformidad
positiva. La decisión incluirá la base presentada usando los mecanismos de
transacción y recuperación existentes. Se comprobarán intentos directos por CLI,
decisiones agrupadas, reintentos, revisores diferentes y cierres con excepciones.
Una dispensa conservará sus reservas y no acreditará una revisión ausente.

Salida: no se podrá registrar una nueva aprobación del alcance incompleto mediante
una ruta alternativa. Una decisión vigente se reutilizará sin exigir otra firma
por un cambio exclusivamente de presentación.

### Instrucciones compartidas y continuidad

PV-05 actualizará `docs/V3-COMMON.md`, `docs/V3-OPERATIONS.md`, `docs/V31-REVIEW.md`
y las referencias v3 de las seis skills, usando la organización de PV-14.
`define` y `help` presentarán el contenido
generado; `assess-readiness` explicará impedimentos; `implement` presentará encargos,
relevos y excepciones cuando procedan; `verify` presentará resultados y correcciones;
`adopt-existing` utilizará los perfiles de adopción, migración y reconciliación.

La documentación distinguirá consultar, aclarar y validar. Exigirá conservar los
apartados y las restricciones del mensaje, mostrar lo necesario antes de pedir una
decisión y reutilizar respuestas explícitas ya recibidas. No añadirá confirmaciones
por registro ni exigirá al usuario copiar hashes, comandos o identificadores.
Cada enlace indicará cuándo debe leerse su recurso. Se conservará la separación
entre versiones y se comprobará la continuidad tras cambio de evento, chat nuevo
o compactación. Las entradas de host no provocarán carga duplicada de skills.

Salida: una única regla de presentación aplicada desde todos los accesos relevantes,
sin nuevas skills ni cambios de objetivo que solapen sus descripciones.

### Distribución y compatibilidad

PV-06 revisará `distribution/dual.json`, `scripts/dual_distribution.py`,
`scripts/validate_plugin_contract.py` y `tests/test_v3_distribution.py`. Incluirá
los nuevos módulos y referencias en ambos paquetes y comprobará la igualdad del
núcleo y la resolución de enlaces desde el runtime fijado.
La lista cerrada de referencias compartidas admitirá los nuevos recursos exactos
y verificará sus dependencias transitivas y anclas. La reorganización no abrirá
rutas arbitrarias fuera de la skill ni resolverá recursos contra otra versión.

Se ensayará en proyectos temporales la actualización soportada y la recuperación,
con el almacenamiento documental vigente. Las aprobaciones antiguas no recibirán
contenido ni fechas inventados. Se actualizará `docs/COMPATIBILITY.md` si hace falta
explicar límites reales. No se publicará ni instalará en consumidores del usuario.

Salida: paquetes reproducibles que contienen las mismas reglas y pueden ejecutar
la consulta y los controles nuevos en las configuraciones declaradas.

### Verificación del conjunto

PV-07 integrará las pruebas nuevas en `tests/test_v3_decision_presentation.py` y
ampliará casos de comportamiento en `tests/test_v31_review.py` y
`tests/test_v3_workflow.py` donde corresponda. Comprobará también que la planificación
y la ejecución cubiertas continúan funcionando tras reutilizar aprobaciones.
Se añadirá `tests/test_v3_instruction_routing.py` para el catálogo, la selección,
las composiciones, la conservación de reglas y la integridad de recursos, sin
confundir estas pruebas con evaluación semántica del agente.

Se ejecutarán las comprobaciones focales indicadas abajo, el contrato del plugin y
la revisión del diff. La evidencia técnica se registrará junto al avance de las
tareas, conservando fallos y correcciones relevantes. No se copiará todo el historial
de salidas ni se añadirá una batería permanente de publicación.

Salida: evidencia reproducible del recorrido completo y sus límites. PV-07 no
cierra la observación humana de PV-08.

### Observación de la experiencia real

PV-08 ampliará los casos de `docs/V3-HOST-ACCEPTANCE.md` y realizará una observación
acotada en Codex y Copilot cuando existan entornos y participantes autorizados.
Se observarán recorridos completos de una persona y de un equipo: configuración,
especificación, plan y autorización, encargo o relevo, resultado y corrección.
Se incluirán un pendiente crítico, una excepción y una decisión ya cubierta que
deba continuar sin preguntas nuevas. Las variantes condicionales se observarán
solo en capacidades realmente disponibles, indicando las que no se hayan probado.

Se revisará el mensaje realmente mostrado: títulos, lenguaje, integridad, detalle
técnico, decisión solicitada y ausencia de confirmaciones repetidas. La persona
deberá poder identificar qué cambia, qué queda fuera y qué falta por decidir.
No se impondrá un cuestionario adicional al flujo ordinario de validación.
Se aplicará el protocolo de PV-15 para observar selección de recursos, cambios de
evento y recuperación tras compactación. Se registrarán omisiones, preguntas
innecesarias, ampliaciones y lecturas repetidas, junto al consumo que el host permita
observar. No se declarará eficiencia operativa por una reducción estática de texto.

Salida: observaciones por host y evento con candidato, contexto y resultado. Si un
host, recorrido o participante no está disponible, su caso permanecerá `not-run`;
no se simulará ni se extrapolará el éxito de un perfil a los demás.

### Configuración y adopción del proyecto

PV-09 construirá los perfiles de EV-02, EV-03, EV-05, EV-06, EV-07 y EV-27.
Los adaptadores utilizarán `scripts/v3_authoring.py`, `scripts/v31_review.py`,
`scripts/v3_adoption.py`, `scripts/v3_current.py`, `scripts/v3_migration.py` y
`scripts/v3_lifecycle.py`. El generador mostrará personas declaradas, controles,
antes y después, alcance documental, conservación de acuerdos y recuperación.

La vista de una configuración propuesta deberá funcionar antes de crear el índice.
En migraciones con errores explicará únicamente lo que las fuentes permiten
conocer, manteniendo los bloqueos de integridad. No elegirá identidad, proceso,
tecnología ni controles para completar la ficha. Las decisiones compatibles de
configuración y conversión podrán agruparse con sus efectos explícitos.

Salida: presentación suficiente de cambios concretos sin fabricar aprobación,
sin modificar el proyecto al consultar y sin presentar una actualización global
del plugin como actualización automática del runtime de un consumidor.

### Planificación y distribución del trabajo

PV-10 cubrirá EV-12 a EV-17 con `scripts/v3_authoring.py`, `scripts/v3_team.py`,
`scripts/v3_workflow.py` y `scripts/v31_guidance.py`. El plan mostrará entregables,
tareas, responsables, orden, dependencias y pruebas; la autorización precisará
porción, entorno y límites. Se distinguirá aprobar el plan de autorizar su ejecución.

Los encargos y relevos mostrarán estado recibido, trabajo propio, contratos,
pendientes y dependencias. Se conservarán la aceptación del destinatario y el
alcance parcial. La revisión de tareas propias incluida en una decisión vigente
no se volverá a pedir. Iniciar o reanudar dentro de la cobertura será un avance
informativo. Cancelar, pausar o reabrir mostrará sus efectos cuando exija una
decisión material; registrar una pausa técnica autorizada no creará otro trámite.

Salida: mensajes concretos y agrupados por persona, con comprobaciones de ofertas
obsoletas, respuesta parcial, cambio de destinatario y tareas propias ya revisadas.

### Comprobación y aceptación de resultados

PV-11 cubrirá EV-10 y EV-18 a EV-24 usando `scripts/v3_verification.py`,
`scripts/v31_corrections.py`, `scripts/v3_workflow.py`, `scripts/v3_quality.py` y
`scripts/v31_guidance.py`. La presentación de resultados identificará candidato,
entorno, acceso al resultado, criterios, pruebas, evidencia y reservas.

La verificación manual explicará qué observar. La integración mostrará contratos
entre componentes y compatibilidad; la aceptación funcional mostrará el resultado
frente a criterios. Una respuesta podrá cubrir ambas si corresponde a la misma
persona y al mismo candidato, respetando el orden del proyecto y registrando
ambos efectos. No se confundirá preparación de entrega con aprobación del PR.

Los rechazos conservarán esperado y observado, la evidencia disponible y lo que
falte registrar. Las correcciones distinguirán defecto, cambio de acuerdo, nueva
necesidad y causa externa. Resolver un defecto explicará las pruebas posteriores
y la aceptación que siga pendiente. No se ampliará el encargo por aceptar su
clasificación ni se pedirá otra firma para importar una prueba ya ejecutada.

Salida: recorrido desde prueba o rechazo hasta aceptación con contenido visible,
evidencia vigente, reservas explícitas y respuestas negativas preservadas.

### Excepciones y efectos operativos

PV-12 cubrirá EV-25, EV-26, EV-28 y EV-29 mediante adaptadores del generador sobre
`scripts/v3_workflow.py`, `scripts/v31_review.py`, `scripts/v3_lifecycle.py`,
`scripts/v3_storage.py` y `scripts/v31_corrections.py`.

Una excepción explicará incumplimiento, alternativas, consecuencias, medidas,
responsable y vencimiento; conservará los controles no dispensables y el resultado
real. Revocar explicará el permiso que se retira y las dependencias afectadas.
Recuperar o revertir mostrará el estado parcial, los cambios concretos y los
conflictos posteriores; reutilizará la autorización aplicable.

El resumen de una operación dejará de sugerir que toda escritura requiere una
nueva pregunta. Las acciones externas presentarán contenido, destino, audiencia y
efectos antes de solicitar un permiso ausente. Preparar una PR o un entregable
seguirá siendo distinto de publicarlo; no se añadirán clientes remotos.

Salida: intervenciones proporcionadas a sus consecuencias, con pruebas de permisos
vigentes, expirados, respuestas parciales y recuperación sin sobrescribir trabajo posterior.

### Decisiones condicionales y recorridos conservados

PV-13 cubrirá EV-01, EV-04, EV-09, EV-30, EV-31 y EV-32. Revisará las referencias
de descubrimiento, tecnología, frontend, vistas de cliente y Jira, además de la
compatibilidad en `scripts/lks_sdd.py`, `scripts/v2_cli.py` y documentación aplicable.

La entrevista conservará preguntas breves y útiles. Una decisión técnica comparará
alternativas según requisitos. La selección visual mostrará assets reales y su
alcance. Un entregable para cliente mostrará contenido y audiencia, conservando
clasificación y permisos. Jira y retención expondrán solo las capacidades realmente
soportadas; los escritores históricos bloqueados seguirán bloqueados.

Salida: perfiles documentados, conectados donde exista recorrido y claramente
declarados como no disponibles donde falte soporte. No se implementarán nuevas
integraciones, almacenamiento ni migraciones de funcionalidades antiguas.

### Recursos de instrucciones y carga por evento

PV-14 realizará la reorganización definida en PV-01 y detallada en
[CONTEXT-EFFICIENCY.md](CONTEXT-EFFICIENCY.md). Materializará las guías por familias,
trasladará los procedimientos específicos y mantendrá las garantías comunes.
Revisará cada llamador y la matriz de traslado de reglas para evitar pérdidas,
duplicación o referencias a procedimientos de otra versión.

El catálogo de perfiles de `scripts/v3_decision_presentation.py` resolverá recursos
por acción, finalidad y condiciones observadas, incluyendo decisiones agrupadas.
La salida `instruction_refs` contendrá exclusivamente rutas del runtime fijado,
motivo y revisión/huella. Los documentos del consumidor no podrán elegir archivos
de instrucciones. Una combinación ambigua no devolverá una suficiencia ficticia.

Los recursos opcionales solo se cargarán al cumplirse su condición. Ante una
dependencia incierta se ampliará la lectura o se aclarará lo que falta. La solución
no añadirá almacenamiento de sesiones, un nuevo selector de requisitos, búsqueda
semántica ni telemetría. La lectura normativa de `v3_context.py` se conserva.

Salida: mapa único de perfiles a recursos y dependencias, guías coherentes y
selección comprobable. PV-05 conectará estos recursos desde las seis skills y
PV-06 comprobará su distribución y resolución efectiva.

### Comparación de carga y preparación de la observación

PV-15 preparará una medición focal reproducible con fuentes y runtime identificados.
Se propone `tests/measure_v3_instruction_context.py` como herramienta de desarrollo
temporal o invocable bajo demanda, fuera de la puerta de publicación.
Comparará el flujo actual, la funcionalidad nueva con lectura conjunta de sus guías
y la misma funcionalidad con selección por familias. El control de lectura conjunta
solo sirve al experimento; no se distribuye como un segundo recorrido mantenido.

Medirá caracteres, archivos, saltos, repeticiones y, cuando sea posible con método
identificado, tokens. El protocolo de PV-08 añadirá consumo de la tarea completa,
ampliaciones, reintentos, correcciones y comportamiento real. El ahorro de instrucciones
se separará de datos del proyecto, salidas y coste facturado no disponible.

Los casos y límites están definidos en el análisis. La suficiencia y los resultados
no pueden empeorar en los casos evaluados; no se recortan obligaciones para conseguir
una cifra. Cuando la división no compense, se reajustará la agrupación. Las medidas
y resultados negativos se conservarán en un informe focal de implementación, sin
crear documentos por consulta ni una batería permanente de publicación.

Salida: comparación técnica y protocolo listo para PV-08. La reducción real de
errores y el ahorro observado por host quedan pendientes hasta esa observación.

## Criterios de aceptación

| Criterio | Resultado exigido | Comprobación prevista |
|---|---|---|
| AC-01 | En especificaciones, un título principal concreto y exactamente los siete títulos de segundo nivel acordados; componentes con títulos de tercer nivel. | Análisis del Markdown real generado, incluidos títulos con caracteres especiales. |
| AC-02 | Lenguaje del proyecto, sin claves o identificadores administrativos expuestos; términos técnicos útiles conservados. | Casos de contaminación de metadatos y revisión semántica del mensaje. |
| AC-03 | Componentes y tecnología sustentados en fuentes o identificados como propuestas; incertidumbre explícita. | Casos con arquitectura real, nueva, incompleta y contradictoria. |
| AC-04 | Diseño concreto por componente e interacción coherente; no basta una descripción genérica con los títulos correctos. | Caso negativo de solución genérica, controles de detalle y revisión técnica de contratos y secuencia. |
| AC-05 | Restricciones, permisos, criterios y excepciones aplicables aparecen en la revisión sin alterar su significado. | Casos con obligaciones enlazadas, prosa relevante, límites numéricos y negaciones; contraste semántico. |
| AC-06 | Un borrador incompleto se puede consultar y explicar sin escrituras, manteniendo bloqueada la decisión positiva afectada. | Huellas del proyecto antes y después; consultas de review, status e interventions y rechazo de aprobación. |
| AC-07 | Alcance, revisor y efecto de aceptar quedan claros; una lectura parcial o una conformidad ajena no aprueba el conjunto. | Casos de revisión parcial, propuestas funcional y técnica separadas y cierre integral. |
| AC-08 | Una decisión nueva se vincula a la versión presentada y detecta cambios materiales posteriores. | Cambio entre presentación y decisión, incluido un requisito relacionado. |
| AC-09 | Las rutas directas, agrupadas y de excepción conservan preparación, autoridad y reservas aplicables. | Invocaciones directas y reintentos con contenido incompleto y revisores distintos. |
| AC-10 | Las aprobaciones anteriores válidas conservan su efecto; un cambio de formato no produce una invalidación artificial. | Recorrido histórico con planificación y continuación; cambio material que sí exige revisión. |
| AC-11 | Las consultas repetidas no crean copias, eventos ni variaciones del mensaje con fuentes idénticas. | Repetición, comparación de salida y comprobación de ausencia de escrituras. |
| AC-12 | Información ausente, contradictoria o malformada no se convierte en hechos ni desaparece al formatear. | Referencias rotas, apartados vacíos, Markdown adverso e instrucciones incrustadas tratadas como datos. |
| AC-13 | Una propuesta extensa conserva obligaciones y explicita cualquier parte todavía no mostrada. | Caso extenso con restricción al final y comprobación de que no habilita aprobación global prematura. |
| AC-14 | Ambos paquetes incorporan el mismo núcleo y las referencias necesarias, respetando el runtime fijado y seis skills. | Pruebas de distribución, compatibilidad e integridad desde paquetes temporales. |
| AC-15 | En ambos hosts el mensaje real permite comprender y revisar el cambio con el formato y lenguaje acordados. | Observación humana registrada por host; estado independiente de las pruebas técnicas. |
| AC-16 | Todas las acciones y variantes del inventario tienen perfil, tratamiento informativo o limitación explícita. | Correspondencia entre superficie de CLI, familias EV y casos; el nuevo decision-view también se clasifica. |
| AC-17 | Un hito o registro técnico no añade una pregunta cuando la cobertura vigente permite continuar. | Recorrido individual y reintentos con contador de intervenciones necesarias; H1, H5 y H7 no generan firmas por sí solos. |
| AC-18 | Las decisiones compatibles se agrupan por persona y contenido presentado; una respuesta parcial no aprueba efectos restantes. | Plan y autorización con tareas propias; recepción e inicio; integración y aceptación, con variantes parciales. |
| AC-19 | Configuración y cambios de gobierno muestran personas, controles, diferencias y trabajos afectados sin inferir autoridad. | Alta, cambio de revisor, independencia imposible y modificación de controles. |
| AC-20 | Adopción y migración distinguen observación, intención, conversión y recuperación, conservando acuerdos existentes. | Caso sin SDD, actualización de runtime y discrepancia tras migración. |
| AC-21 | El plan y el permiso de ejecutar presentan tareas, dependencias, pruebas, entorno y límites concretos. | Plan aprobado sin ejecución, autorización conjunta y cambio de una dependencia. |
| AC-22 | Encargo, oferta y recepción muestran porción, estado y responsabilidades y respetan a la persona destinataria. | Relevo parcial, oferta obsoleta, cambio de responsable y revisión propia ya cubierta. |
| AC-23 | Pruebas humanas y hallazgos muestran esperado, observado, procedencia y límites; registrar evidencia no concede aceptación. | Prueba manual, informe externo, prueba fallida y revisión independiente. |
| AC-24 | Integración y aceptación se refieren al candidato observado y mantienen reservas y orden del proceso. | Personas iguales y distintas, orden previo o posterior y candidato que cambia antes de aceptar. |
| AC-25 | Rechazo, clasificación y corrección conservan el desacuerdo y no amplían automáticamente el alcance autorizado. | Evidencia incompleta, defecto frente a nueva petición, corrección y nueva aceptación pendiente. |
| AC-26 | Excepciones y revocaciones explican efectos, límites, reservas y vigencia sin convertir un fallo en éxito. | Excepción expirada, regla no dispensable y revocación con trabajo dependiente. |
| AC-27 | La vigencia de cada evento usa su base específica, incluyendo destinatario, candidato, evidencia, configuración o destino según corresponda. | Cambios entre presentación y respuesta en cada familia de base; conservación de historia y decisiones vigentes. |
| AC-28 | Una acción externa o histórica declara destino, disponibilidad y permiso; no reactiva escritores ni inventa funciones. | Preparar frente a publicar, revisar frente a enviar y rutas v2 bloqueadas de Jira o retención. |
| AC-29 | Se puede explicar una configuración antes de inicializar y una recuperación incompleta sin fabricar decisiones ni escribir. | Consultas sin índice, con propuesta incompleta y con operación interrumpida. |
| AC-30 | El tamaño y los apartados corresponden al tipo de decisión y conservan la claridad del mensaje. | Aclaración breve, plan, excepción y resultado; no se imponen los siete apartados de especificaciones a todos los eventos. |
| AC-31 | Se conservan seis skills breves, objetivos distintos e invocación implícita; el evento no carga todos los perfiles. | Inspección de entradas y recorridos simples; sin skill por evento ni doble carga de entradas de host. |
| AC-32 | Cada evento y variante tiene una selección explícita de familia, dependencias y condiciones de ampliación. | Correspondencia de 57 acciones y 33 familias, más decision-view; finalidad de approve y variantes compuestas. |
| AC-33 | La división conserva todas las reglas necesarias y el contrato literal del proyecto; no activa el selector reducido. | Matriz de traslado, excepciones y condiciones al final, prosa sin clasificar y contraste con contexto completo. |
| AC-34 | Los recursos de instrucciones proceden de un catálogo cerrado del runtime fijado y se separan de datos y mensaje visible. | Rutas manipuladas, fuentes con instrucciones incrustadas, otro runtime y salida de decision-view. |
| AC-35 | Las decisiones compuestas reúnen sus guías completas sin duplicarlas y amplían la lectura ante condiciones nuevas. | Plan y tareas propias; relevo e inicio; integración y aceptación; aparición de rechazo o excepción. |
| AC-36 | El agente recupera las fuentes necesarias tras chat nuevo, compactación o cambio de contexto; hashes y marcas no sustituyen lectura. | Instrucciones y escenarios de continuación; observación real en PV-08. |
| AC-37 | Una ruta desconocida, ambigua o incompleta no habilita una decisión positiva mediante un perfil genérico. | Evento desconocido, finalidad ausente, recurso perdido, dependencia no clasificada y aclaración posible. |
| AC-38 | Ambos paquetes contienen todas las guías necesarias, con enlaces y anclas resolubles desde su runtime. | Extracción temporal, cierre transitivo de referencias, lista compartida acotada y separación de versiones. |
| AC-39 | Se comparan carga y trabajo total con igual funcionalidad, procedencia y límites de medida explícitos. | Informe de PV-15 y observación de PV-08; separar caracteres, tokens estimados/observados y coste no disponible. |
| AC-40 | En los casos evaluados no empeoran suficiencia, decisiones ni calidad; las rutas simples reducen instrucciones frente a leer todas las guías. | Comparación técnica y semántica con contenido completo, omisiones críticas, errores, reintentos y preguntas; reajustar agrupaciones si no compensa. |

La cobertura estructural no demuestra comprensión ni corrección del diseño. Los
criterios mixtos requieren tanto su prueba automatizable como el contraste del
contenido; una comprobación de longitud o una casilla declarada no los satisface.

## Comprobaciones y evidencia

Para este plan documental se ejecutará el contrato del plugin y se revisarán el
contenido añadido, sus enlaces y el diff, conforme a [VALIDATION.md](../../VALIDATION.md).
No se ejecuta un gate de release para entregar un plan.

Durante PV-07 se ejecutarán, desde la raíz del repositorio:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v3_decision_presentation
python -B -X utf8 tests/run_unit_tests.py --module test_v3_instruction_routing
python -B -X utf8 tests/run_unit_tests.py --module test_v31_review --module test_v3_workflow
python -B -X utf8 tests/run_unit_tests.py --module test_v3_governance_quality --module test_v3_integration
python -B -X utf8 tests/run_unit_tests.py --module test_v3_distribution
python -B -X utf8 scripts/validate_plugin_contract.py .
git diff --check
```

Los dos primeros módulos se crearán durante la implementación. Se añadirán regresiones de
migración, almacenamiento o integración únicamente si se modifican sus contratos
o aparece un riesgo concreto que esas pruebas deban resolver. Se revisará el
contenido de archivos nuevos además del diff de archivos ya seguidos por Git.

La evidencia de cada tarea registrará alcance, resultado observado, prueba y
limitaciones. Los estados de implementación, verificación técnica, observación de
host y publicación se mantendrán separados. Una release posterior tendrá su propia
autorización y las comprobaciones completas de `docs/VALIDATION.md`.

## Orden de ejecución y puntos de revisión

1. Autorizar el plan y comprobar el estado actual de los archivos afectados.
2. Cerrar el contrato interno, las reglas de carga y los casos de PV-01; recoger
   la medida inicial y resolver diferencias materiales antes de programarlas.
3. Implementar y comprobar PV-02 a PV-04, desde la lectura del borrador hasta el
   registro de una decisión nueva y la reutilización de una anterior.
4. Implementar los perfiles y adaptadores de PV-09 a PV-13. Revisar que cada
   familia distingue información, aclaración, decisión y permiso ya vigente.
5. Completar la organización y selección de recursos con PV-14 e integrar sus
   instrucciones y distribución mediante PV-05 y PV-06.
6. Completar la verificación técnica conjunta de PV-07 y la comparación de carga
   y protocolo de PV-15.
7. Ejecutar PV-08 en las superficies autorizadas, observando presentación y contexto,
   y conservar cualquier pendiente.

Las revisiones de contrato y evidencia son hitos de trabajo. Una decisión vigente
se reutilizará; solo se solicitará otra cuando aparezca una elección material no
cubierta. La ejecución no delegará trabajo ni creará agentes automáticamente.

## Estado de preparación

| Elemento | Estado al preparar el plan |
|---|---|
| Requisitos de presentación y detalle técnico | Recogidos de las instrucciones del usuario. |
| Inventario de eventos | 57 acciones públicas v3 y variantes, más recorridos condicionales; 33 familias analizadas en VALIDATION-EVENTS.md. |
| Eficiencia del contexto | Analizada estáticamente; organización, medidas y límites propuestos en CONTEXT-EFFICIENCY.md. |
| Plan local | Ampliado en revisión 3, con quince tareas y cuarenta criterios de aceptación. |
| Ejecución de PV-01 a PV-15 | Autorizada y desarrollada; cobertura técnica y observación humana separadas en IMPLEMENTATION.md. |
| Validación inicial del contrato del repositorio | Superada el 2026-10-08 antes de añadir este plan. |
| Validación documental de la revisión 1 | Superada el 2026-10-08: contrato, enlaces, cobertura de ocho tareas y quince criterios, contenido y diff. |
| Validación documental de la revisión 2 | Superada el 2026-10-08: contrato, enlaces, espacios y cobertura de 57/57 acciones, 33 familias, trece tareas y treinta criterios. |
| Validación documental de la revisión 3 | Superada el 2026-10-08: contrato, enlaces, espacios y diff; 57/57 acciones y 33 familias cubiertas, quince tareas sin ciclos de dependencia y cuarenta criterios. |
| Ahorro y reducción de errores | No medidos en hosts; no se declara una mejora de consumo ni calidad ya conseguida. |
| Observación real de Codex y Copilot | No ejecutada para esta mejora. |
| Publicación o actualización de consumidores | Fuera de esta petición. |
