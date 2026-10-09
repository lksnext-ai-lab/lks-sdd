# Revisión de los eventos de decisión del usuario

Fecha: 2026-10-08. Alcance: implementación local del plugin y referencias de sus
seis skills. Este análisis amplía el [plan de implementación](PLAN.md) a los
momentos de aclaración, revisión, autorización y aceptación del proyecto.

La mejora debe extenderse al resto del recorrido. La estructura concreta dependerá
de la decisión: aprobar un plan requiere tareas y límites de ejecución; aceptar
un resultado requiere pruebas y reservas; autorizar una excepción requiere conocer
el incumplimiento y sus consecuencias. Los siete apartados ya acordados se conservan
para las especificaciones.

## Cobertura de la revisión

Se han inspeccionado las 57 acciones declaradas en
[la CLI v3](../../../scripts/v3_cli.py), sus operaciones de decisión, el recorrido
[H1 a H7](../../V31-REVIEW.md), las referencias v3 de las seis skills y las guías
condicionales de descubrimiento, tecnología, interfaz, cliente y Jira. Las 33
familias siguientes agrupan esos eventos y sus variantes; no representan 33
confirmaciones que deba realizar una persona.

El examen es estático y contrasta instrucciones, datos, controles y salida prevista.
No acredita que se hayan observado todos los mensajes en Codex o Copilot. La
reproducción previa de `review` está recogida en el plan; los demás hallazgos de
este inventario son de código y documentación, no ensayos humanos ejecutados.

Se distingue entre:

- **Decisión:** hace falta una respuesta sobre contenido concreto, salvo que ya
  exista una decisión explícita vigente que lo cubra.
- **Aclaración:** se solicita información mínima para completar una decisión.
- **Condicional:** la intervención depende del proceso, de la persona, del alcance
  o de que exista una capacidad soportada.
- **Información:** describe una observación o continúa trabajo autorizado; no
  añade una firma ni transforma cada operación en una pregunta.
- **Histórico o externo:** se revisa su comunicación y su disponibilidad, sin
  reactivar escritores antiguos ni implementar una integración nueva.

## Hallazgos comunes

Los controles internos suelen conservar más información de la que presenta el
resumen: actor, alcance, estado, evidencias, huellas, dependencias y reservas.
[interventions](../../../scripts/v31_guidance.py) ya agrupa por persona y evita
firmas duplicadas, pero devuelve acciones, objetos, causas y referencias; no
construye una explicación completa del contenido que debe revisar esa persona.

El [preparador de operaciones](../../../scripts/v3_storage.py) utiliza un resumen
común con operación, número de archivos y «Autorizar estos cambios exactos».
Ese resumen es insuficiente para decidir y puede sugerir una confirmación técnica
adicional cuando la autorización de la sesión ya cubre el trabajo.

[Las reglas comunes](../../V3-COMMON.md) exigen mostrar contenido y efectos,
reutilizar decisiones vigentes y continuar lo autorizado. La mejora debe convertir
esas obligaciones en presentaciones específicas, conservando los controles de
autoridad. Un campo `statement` obligatorio no prueba que se haya mostrado una
explicación suficiente; tampoco convierte una operación automática en un trámite
humano nuevo.

El generador previsto inicialmente para especificaciones resulta demasiado estrecho
para otros eventos. Configuración y migración necesitan mostrar cambios propuestos
antes de disponer de un proyecto inicializado o completamente válido. Aceptación
necesita vincular código y evidencia; una excepción necesita vigencia y regla; un
relevo necesita emisor, destinatario y porción. Una única huella o plantilla genérica
no representa correctamente todas esas decisiones.

## Configuración y preparación del proyecto

Fuentes: [autoría y gobierno](../../../scripts/v3_authoring.py),
[colaboración](../../../scripts/v31_review.py), [política](../../../scripts/v3_policy.py),
[adopción](../../../scripts/v3_adoption.py), [cambio de runtime](../../../scripts/v3_current.py)
y [descubrimiento](../../../skills/lks-sdd-define/references/discovery-interview.md).

| Evento | Situación actual y carencia | Información que debe recibir la persona | Tratamiento y tarea |
|---|---|---|---|
| EV-01 Aclarar necesidad, alcance o aplicabilidad | La entrevista ya propone tandas breves y preguntas de impacto; un paso condicional puede quedar pendiente por falta de decisión. Falta conectarlos con la presentación común sin convertirlos en fichas extensas. | Dato que falta, por qué afecta a la aplicación o al trabajo, opciones reales y consecuencia de aplazarlo; incluir si una condición o exclusión aplica. | Aclaración breve; conservar entrevista adaptativa. PV-13 y perfil de aclaración. |
| EV-02 Identificar al interlocutor | La autoridad se comprueba con miembros declarados; Git o Windows no prueban identidad. Falta una pregunta uniforme cuando el dato es necesario. | Para qué actuación se necesita su identidad o función y qué información concreta falta. | Aclaración solo cuando proceda; no repetir por comando ni atribuirse la identidad anterior. PV-09. |
| EV-03 Configuración inicial | `init` recibe proceso, personas, controles, destino y declaración explícita. No entrega una ficha de decisión con sus efectos cotidianos. | Proyecto, forma de trabajo, responsables, revisiones, controles disponibles, ramas y consecuencias de la configuración. | Decisión de configuración; puede agruparse con adopción o migración si se presenta todo. PV-09. |
| EV-04 Elección técnica | `approve` admite finalidad tecnológica y la guía exige decisiones locales. Falta una comparación estable centrada en requisitos. | Problema, alternativas viables, recomendación razonada, componentes afectados, compatibilidad, costes o licencias conocidos y pendientes. | Decisión dentro de la especificación o ficha técnica acotada. No seleccionar pila por defecto. PV-13. |
| EV-05 Adopción de un sistema existente | `adopt` conserva observaciones, intención y cobertura parcial. No produce una comparación humana entre lo observado y lo que se desea conservar o cambiar. | Alcance inspeccionado, hechos, inferencias, comportamiento confirmado, lagunas y documentos que se crearán. | Decisión de intención y alcance; la inspección autorizada es información. PV-09. |
| EV-06 Migración y actualización del runtime | El corte conserva inventarios y recuperación, pero su resumen puede quedar en formatos, rutas y hashes. | Situación y destino, qué cambia, qué se conserva, tareas afectadas, decisiones que siguen vigentes, impedimentos y recuperación. | Decisión sobre un cambio concreto y agrupable con la configuración mostrada. PV-09. |
| EV-07 Cambiar proceso, equipo o controles | `governance` y `configure-collaboration` mantienen autoridad previa y alcance por petición. Falta una vista de antes y después y de consecuencias. | Cambio propuesto, motivo, personas y trabajos afectados, revisiones que se exigirán o dispensarán y decisiones que pueden perder vigencia. | Decisión de gobierno con autoridad previa; no presentar una rebaja de controles como ajuste técnico inocuo. PV-09. |

## Definición y planificación

Fuentes: [review](../../../scripts/v3_lifecycle.py),
[aprobaciones](../../../scripts/v3_approval.py), [revisión integral](../../../scripts/v31_review.py),
[planes](../../../scripts/v3_authoring.py), [equipo](../../../scripts/v3_team.py)
y [diseño visual](../../../skills/lks-sdd-define/references/frontend-design.md).

| Evento | Situación actual y carencia | Información que debe recibir la persona | Tratamiento y tarea |
|---|---|---|---|
| EV-08 Validar especificaciones | Ya analizado: formato libre, detalle técnico insuficiente y referencias que no aportan todo el texto necesario. | Los siete apartados acordados, componentes reales, contratos, condiciones y efecto de validar. | Decisión o aclaración según preparación. PV-01 a PV-04. |
| EV-09 Seleccionar dirección visual | La guía exige mostrar alternativas y decisión explícita; los protocolos detallados conservados son dependientes del formato. | Imágenes accesibles, pantallas y estados cubiertos, diferencias, propuesta recomendada, restricciones y alcance de la selección. | Decisión condicional cuando exista interfaz y recorrido soportado; la selección visual no aprueba funcionalidad nueva. PV-13. |
| EV-10 Tratar observaciones de revisión | Hay comentarios, tratamiento incorporado o descartado y conformidad posterior del autor. El usuario necesita ver la objeción y el cambio correspondiente. | Observación, propuesta de tratamiento, motivo, antes y después, efecto en alcance y cuestiones abiertas. | Intervención existente; agrupar con la revisión cuando proceda. No pedir una segunda aceptación por registrar el comentario. PV-04 y PV-11. |
| EV-11 Conformidad de revisores y cierre de propuesta | `interventions` agrupa correctamente, pero presenta referencias y causas operativas. | Contenido exacto, cambios desde la revisión anterior, observaciones resueltas, reservas y qué decisión corresponde a esa persona. | Una conformidad por persona cuando sea requerida; cierre conjunto solo con condiciones cumplidas. PV-04. |
| EV-12 Aprobar el plan | El núcleo comprueba tareas y cobertura; falta una presentación detallada para revisarlo. | Objetivo, entregables, tareas y responsables, secuencia, contratos compartidos, dependencias, pruebas y pendientes. | Decisión sobre el plan ya preparado. PV-10. |
| EV-13 Autorizar ejecución | Puede agruparse con el plan y tareas propias. Una frase genérica puede confundir aprobación del diseño con permiso para actuar. | Porción que se ejecutará, entorno y ramas, límites, condiciones previas y acciones concretas cubiertas. | Aprobación y autorización distinguibles y agrupables; nunca autorizar resultados o planes futuros. PV-10. |
| EV-14 Revisar el encargo | `review-task` vincula persona, tarea y porción; puede estar cubierto por la respuesta al plan. Falta una ficha de trabajo completa. | Resultado esperado, alcance propio, interfaces, entradas y entregables, pruebas, dependencias y condiciones para comenzar. | Solo si falta revisión vigente; agrupar tareas de la misma persona. PV-10. |
| EV-15 Asignación y relevo | `assign` y `handoff` conservan ofertas, estado y alcance; su resumen no muestra el contenido que recibe el destinatario. | Emisor y destinatario, trabajo realizado, porción transferida, archivos o entregables, pendientes, dependencias y permiso existente. | Ofrecer y recibir son actos distintos. Recepción, revisión e inicio se agrupan únicamente cuando la respuesta los cubre. PV-10. |

## Ejecución y resultados

Fuentes: [transiciones](../../../scripts/v3_workflow.py),
[evidencia e integración](../../../scripts/v3_verification.py),
[correcciones](../../../scripts/v31_corrections.py) y
[orientación](../../../scripts/v31_guidance.py).

| Evento | Situación actual y carencia | Información que debe recibir la persona | Tratamiento y tarea |
|---|---|---|---|
| EV-16 Inicio y reanudación cubiertos | `start` y `resume` comprueban cobertura y permiten agrupación con recepción o revisión. Convertirlos en otra aprobación haría retroceder el diseño. | Trabajo que continúa, punto de partida, cambios relevantes e impedimentos reales. | Resumen y continuación automática dentro del permiso; solo preguntar por una decisión ausente. PV-05 y PV-10. |
| EV-17 Pausar, cancelar o reabrir | Existen transiciones y motivos, con autoridad diferenciada. Falta explicar el efecto de una decisión material sobre trabajo y dependencias. | Motivo, porción afectada, trabajo conservado, dependencias afectadas y siguiente posibilidad de continuación. | Decisión cuando no esté cubierta; una pausa técnica ante un bloqueo no exige una firma nueva. PV-10. |
| EV-18 Pruebas manuales y revisión independiente | `evidence` distingue procedencia y resultado; `verify` y `close` exigen condiciones. Falta una presentación orientada a lo que la persona debe comprobar. | Candidato y entorno, criterio, pasos o medio de observación, resultado esperado y observado, evidencia y límites. | Intervención humana solo cuando sea necesaria. Registrar pruebas automáticas o cerrar una tarea acreditada no añade aceptación funcional. PV-11. |
| EV-19 Hallazgos y riesgo durante implementación | Los controles ya están decididos; `checkpoint` puede registrar riesgo o falso positivo sin cambiar calidad. Falta separar explicar un hallazgo de autorizar una excepción. | Hallazgo, evidencia, impacto, propuesta de tratamiento y efecto real sobre el trabajo. | Continuar correcciones cubiertas; cambios de política o excepciones usan su decisión propia. PV-11 y PV-12. |
| EV-20 Validación técnica de integración | `integrate` contrasta base, candidato, pruebas y cambios compartidos. No existe un informe común legible del conjunto que se acepta técnicamente. | Componentes e interfaces integrados, base y candidato, compatibilidad, pruebas conjuntas, fallos, reservas y cambios pendientes. | Decisión técnica con evidencia; no equivale a merge ni aprobación remota del PR. PV-11. |
| EV-21 Aceptación funcional | `accept` acredita el candidato y mantiene reservas; puede agruparse con integración. Falta una relación visible de resultados frente a criterios. | Qué se entregó, cómo acceder al resultado, criterios con resultado y evidencia, limitaciones y alcance exacto de aceptar. | Decisión del resultado observado. Respetar el orden del proyecto y distinguirla de la integración aunque una persona confirme ambas. PV-11. |
| EV-22 Rechazo del resultado | `reject-result` recoge esperado, observado y artefacto. La devolución debe poder expresarse directamente, sin exigir la ficha técnica al usuario. | Diferencia concreta, ejemplo o evidencia disponible, alcance afectado y siguiente tratamiento propuesto. | Registrar el rechazo explícito; pedir solo lo que falte. La carencia de un artefacto registrable no convierte el rechazo en aceptación. PV-11. |
| EV-23 Definir la corrección | `define-correction` diferencia defecto, cambio de acuerdo, nueva necesidad o causa externa. Falta explicar las consecuencias de esa clasificación. | Acuerdo original, desviación, clasificación propuesta con razón, corrección, aceptación y necesidad de revisar alcance o plan. | Decisión delimitada; confirmar el defecto no autoriza una funcionalidad adicional. PV-11. |
| EV-24 Resolver el defecto | `resolve-defect` exige evidencia posterior y vigente. Puede confundirse con aceptación final o generar una firma redundante. | Corrección aplicada, pruebas posteriores, resultado y comprobaciones o aceptación restantes. | Reutilizar decisión y evidencia competentes; la resolución no sustituye la nueva aceptación del resultado cuando corresponda. PV-11. |

## Excepciones y operaciones transversales

Fuentes: [excepciones](../../../scripts/v3_workflow.py),
[dispensas de revisión](../../../scripts/v31_review.py),
[revocación y reconciliación](../../../scripts/v3_lifecycle.py),
[recuperación](../../../scripts/v3_storage.py),
[vistas de cliente](../../../skills/lks-sdd-verify/references/client-view-rules.md),
[Jira](../../../skills/lks-sdd-help/references/jira-companion.md),
[escritores históricos](../../../scripts/v2_cli.py) y
[retención](../../../scripts/v2_retention.py).

| Evento | Situación actual y carencia | Información que debe recibir la persona | Tratamiento y tarea |
|---|---|---|---|
| EV-25 Excepción o continuación con reservas | Hay motivos, reglas, alcance y vencimiento; un resumen genérico oculta qué incumplimiento se admite. | Condición no satisfecha, evidencia, riesgo o efecto, alternativas, alcance, responsable y vencimiento exacto. | Decisión competente y delimitada; conserva el fallo y las revisiones ausentes. Solicitar una excepción no la concede. PV-12. |
| EV-26 Revocar una decisión | `revoke` conserva el original, pero falta explicar las consecuencias antes de una revocación nueva. | Decisión vigente que se retira, motivo, alcance, dependencias y trabajo que dejará de estar habilitado. | Decisión explícita; una petición inequívoca ya autoriza su registro. PV-12. |
| EV-27 Reconciliar continuidad y cambios materiales | Migración y ramas antiguas exponen correspondencias y diferencias. Falta una síntesis orientada a lo conservado y a lo que requiere nueva decisión. | Antes y después, identidades conservadas, discrepancias, trabajo reutilizable, permisos y decisiones pendientes. | Reconciliar hechos no concede permiso retroactivo. Cambios de producto vuelven a especificación y plan. PV-09. |
| EV-28 Aplicar, recuperar o revertir una operación | `apply`, `recover` y `rollback` vinculan cambios exactos. La preparación técnica no debe multiplicar las preguntas. | Para recuperación o reversión material: operación, resultado parcial, archivos afectados, estado final previsto, recuperación posible y conflictos posteriores. | `apply` reutiliza autorización vigente. Solo una alternativa o efecto no cubierto necesita otra decisión. PV-12. |
| EV-29 Publicar, instalar, enviar o abrir una PR | Las instrucciones exigen autorización específica; H7 prepara información sin publicar. No hay ficha uniforme de destino y efectos externos. | Resultado exacto, destino y audiencia, contenido que saldrá del entorno, cambios externos y acciones incluidas en el permiso. | Decisión de sesión cuando falte; no implementar clientes o integraciones nuevos. PV-12. |
| EV-30 Revisar un entregable para cliente | La guía ya delimita fuentes, audiencia y exclusiones, pero su presentación puede confundirse con aceptación funcional o envío. | Documento o vista real, destinatarios, contenido, limitaciones y qué se valida: contenido, preparación o envío. | Revisión condicional de contenido; entrega externa separada salvo autorización conjunta concreta. PV-13. |
| EV-31 Configurar o escribir en Jira | Hay decisiones específicas de modo, destino, correspondencias, plan y escritura. Parte del recorrido es histórico y no tiene operación v3 equivalente. | Sitio y proyecto, registros afectados, cambios exactos, comprobación de duplicados, efectos y resultado incierto cuando proceda. | Adaptar comunicación del recorrido realmente disponible. No reactivar comandos v2 bloqueados ni inventar soporte v3. PV-13. |
| EV-32 Archivar o restaurar información operativa | La retención documentada tiene preview y autorización, pero el escritor v2 ordinario está bloqueado por la entrada pública actual. | Datos afectados, elegibilidad, información que permanece, reversibilidad, dependencias y conflictos. | Inventariar y aclarar disponibilidad; no desarrollar ni activar retención nueva. Recuperación soportada usa EV-28. PV-13. |
| EV-33 Diagnósticos, registros y entrega preparada | Consultas, registros técnicos y H7 pueden aparecer como operaciones que necesitan permiso por su resumen común. | Qué se completó, evidencia, límites, impedimento real y siguiente acción. | Información; continuar lo ya autorizado. No añadir firma por cada hito, fichero o registro. PV-05 y PV-07. |

## Perfiles de presentación propuestos

Todos los mensajes de decisión tendrán un título principal concreto. Los títulos
de segundo nivel y el contenido obligatorio serán propios del perfil. La lista
es cerrada y declarativa; no añade un lenguaje de automatización ni nuevos agentes.
Los títulos siguientes son la propuesta funcional que PV-01 concretará en ejemplos.

| Perfil | Eventos | Títulos de segundo nivel y contenido esencial |
|---|---|---|
| Aclaración breve | EV-01, EV-02 y datos ausentes | Qué falta decidir; Opciones y efecto. Una pregunta breve puede condensarse sin desplegar una ficha extensa. |
| Configuración y cambios de organización | EV-03, EV-07 | Objetivo; Configuración propuesta; Personas y responsabilidades; Controles y condiciones; Cambios respecto a la situación actual; Impacto y pendientes. |
| Adopción | EV-05 | Alcance revisado; Comportamiento observado; Intención que se propone confirmar; Diferencias y desconocidos; Documentación que se incorporará; Decisiones pendientes. |
| Migración y reconciliación | EV-06, EV-27 | Situación actual y destino; Cambios previstos; Información y acuerdos que se conservan; Trabajo afectado; Comprobaciones y recuperación; Decisiones pendientes. |
| Especificaciones | EV-08, EV-11 | Los siete títulos acordados en el plan, con solución técnica por componente. Añadir cambios y reservas en los apartados pertinentes. |
| Decisión técnica | EV-04 | Necesidad; Alternativas; Solución recomendada; Componentes y contratos afectados; Consecuencias y comprobación; Decisiones pendientes. Puede integrarse en la solución técnica de la especificación. |
| Dirección visual | EV-09 | Pantallas y estados; Propuestas visuales; Diferencias y recomendación; Alcance de la selección; Pendientes. Mostrar los assets reales. |
| Observaciones y corrección | EV-10, EV-22, EV-23 | Acuerdo o resultado esperado; Diferencia observada; Tratamiento propuesto; Cambios y alcance; Comprobación; Pendientes. |
| Plan y autorización | EV-12, EV-13 | Objetivo y entregables; Tareas y responsables; Orden y dependencias; Criterios y pruebas; Alcance de la ejecución; Riesgos y pendientes. |
| Encargo y relevo | EV-14, EV-15 | Resultado esperado; Alcance y responsabilidades; Estado recibido y entregables; Contratos y dependencias; Pruebas y condiciones de inicio; Pendientes. |
| Verificación y hallazgos | EV-18, EV-19 | Resultado que se comprueba; Criterios y pruebas; Evidencia observada; Fallos y límites; Tratamiento y siguiente acción. |
| Integración técnica | EV-20 | Resultado integrado; Componentes y compatibilidad; Comprobaciones del conjunto; Incidencias y reservas; Alcance de la conformidad; Pendientes. |
| Aceptación funcional | EV-21, EV-24 | Resultado entregado; Acceso y revisión; Cumplimiento de criterios; Limitaciones y reservas; Alcance de la aceptación; Pendientes. La resolución de una corrección explica qué aceptación sigue pendiente. |
| Excepción | EV-25 | Condición pendiente; Motivo y alternativas; Alcance de la excepción; Consecuencias y medidas; Responsable y vencimiento; Efecto de la decisión. |
| Cambio de continuidad o revocación | EV-17, EV-26 | Situación actual; Cambio solicitado; Trabajo y decisiones afectados; Consecuencias; Continuación y pendientes. |
| Recuperación | EV-28, EV-32 cuando esté soportado | Operación y estado observado; Cambios que se aplicarán o revertirán; Información conservada; Riesgos y conflictos; Comprobación del resultado; Pendientes. |
| Entrega o acción externa | EV-29, EV-30, EV-31 disponible | Contenido y resultado; Destino y audiencia; Cambios o envío previstos; Comprobaciones y límites; Alcance del permiso; Pendientes. |
| Avance informativo | EV-16, EV-33 y trabajo cubierto | Resumen proporcional de resultado, impedimentos y siguiente paso. Sin nueva solicitud de validación. |

Los perfiles podrán componerse solo para decisiones compatibles de la misma persona
sobre contenidos ya presentados. Se evitará repetir apartados y se explicarán los
efectos separados. Ejemplos admitidos por el recorrido actual: propuesta y cierre;
plan, ejecución y tareas propias; recepción, revisión e inicio; integración y
aceptación. Una respuesta parcial conservará únicamente lo que cubra expresamente.

## Cobertura de las acciones públicas v3

La siguiente tabla permite comprobar que ninguna acción inventariada queda sin
clasificación. Las variantes que cambian el efecto se han descrito en las familias.

| Acciones | Familias y tratamiento |
|---|---|
| `init`, `governance`, `configure-collaboration` | EV-02, EV-03, EV-06, EV-07. Configuración o cambios explícitos. |
| `adopt-inspect`, `adopt` | EV-05. Inspección informativa y decisión de intención. |
| `migration-diagnose`, `migration-preview`, `migration-continuation`, `old-branch`, `migration-reconcile` | EV-06, EV-27. Diagnóstico, cambio propuesto y reconciliación sin autorización retroactiva. |
| `review`, `review-proposal`, `close-proposal` | EV-08, EV-11. Contenido de especificación y decisiones de revisión. |
| `review-comment`, `resolve-comment` | EV-10. Observación y tratamiento. |
| `approve`, `authorize-plan` | EV-04, EV-08, EV-12, EV-13. Finalidad, alcance y efectos explícitos. |
| `review-task`, `assign`, `handoff` | EV-14, EV-15. Encargo, oferta y recepción. |
| `start`, `resume`, `pause`, `cancel`, `reopen` | EV-16, EV-17. Continuidad o decisión material según cobertura. |
| `implement`, `verify`, `close`, `evidence` | EV-18, EV-33. Hechos y transiciones acreditadas; revisión humana solo cuando corresponde. |
| `analysis`, `analysis-run`, `analysis-findings`, `checkpoint` | EV-19, EV-33. Observación, ejecución de control autorizado y tratamiento; una anotación no concede dispensa. |
| `integrate`, `accept` | EV-20, EV-21. Conformidad técnica y aceptación funcional. |
| `reject-result`, `define-correction`, `resolve-defect` | EV-22, EV-23, EV-24. Rechazo, alcance correctivo y evidencia de resolución. |
| `exception`, `propose-exception`, `review-exception`, `revoke` | EV-25, EV-26. Solicitud, decisión delimitada o revocación. |
| `apply`, `recover`, `rollback` | EV-28. Materialización cubierta o decisión concreta de recuperación. |
| `prepare-delivery` | EV-29, EV-33. Preparación informativa; no publica. |
| `validate`, `status`, `trace`, `context`, `readiness`, `interventions`, `catalog`, `history`, `state-history`, `reindex`, `author` | EV-33. Consulta o registro ya cubierto; una carencia material remite a su familia. `state-history` puede exportar un archivo: informa de ese efecto sin inventar aceptación. |

## Fronteras de versión y operaciones externas

[La entrada pública v2](../../../scripts/v2_cli.py) bloquea las escrituras ordinarias
y remite al recorrido actual; conserva consultas y recuperación. Los comandos y
documentos antiguos de aprobación de entrega, reservas, revisiones de merge,
tracking, visuales y retención se han agrupado con sus familias equivalentes.
Su existencia en el árbol no demuestra disponibilidad en v3.

| Variantes históricas inventariadas | Familia equivalente o tratamiento |
|---|---|
| `planning`, `authorize`, `prepare`, cambios de feature y descomposición | EV-08, EV-12 y EV-13; lectura y reconciliación de planes, sin continuar escrituras antiguas. |
| `review-diff`, `guard-review`, `merge-preview` | EV-20 y EV-27; explicar diferencias semánticas y acuerdos afectados. Un diff o diagnóstico no acredita conformidad. |
| `accept-result`, `continue-with-reservations` | EV-21 y EV-25; resultado concreto, reserva y consecuencias para dependencias. |
| `problem`, `correct`, `replan`, `revoke` | EV-22, EV-23 y EV-26; problema, corrección, cambio de plan y revocación. |
| `authorize-delivery`, `delivery`, `client-view` | EV-29, EV-30 y EV-33; distinguir contenido, permiso de acción externa y observación de entrega. |
| `method-upgrade`, `migrate`, `recover`, `rollback` | EV-06, EV-27 y EV-28; conversión o recuperación soportada y alcance exacto. |
| `tracking-project`, `tracking-authorize`, `tracking-result`, `tracking-reconcile`, `tracking-milestone` | EV-31 y EV-33; propuesta, permiso externo, resultado real y reconciliación de incertidumbre. |
| `visual-request`, `visual-accept`, `visual-cancel`, `visual-observe` y relevo visual 1.5 | EV-09, EV-17 y EV-33; selección visual humana frente a coordinación y observación técnica. |
| `retention-compact`, `retention-restore` | EV-32; explicar el límite de la entrada pública antes de ofrecer una escritura. |
| Consultas, checks y registros de continuidad restantes | EV-33; información y conservación de la evidencia, sin firma añadida. |

La mejora debe mostrar con claridad esa frontera, conservar lectura e historia y
reutilizar las reglas de presentación cuando el recorrido sea soportado. Portar una
capacidad histórica, crear una integración externa o cambiar un contrato de proyecto
exige un alcance distinto; este inventario no lo autoriza.

Las operaciones de publicación del propio plugin y sus aprobaciones de release
pertenecen al mantenimiento de este repositorio. Se conservan sus controles de
[VALIDATION.md](../../VALIDATION.md); no se convierten en hitos adicionales de las
aplicaciones consumidoras.

## Incorporación recomendada al plan

Se recomienda ampliar la revisión 1 del plan con un núcleo común de presentación y
los perfiles anteriores. PV-01 a PV-08 conservarán su identidad, ampliando su
integración y pruebas. PV-09 a PV-13 cubrirán configuración y adopción; planes y
encargos; evidencia y resultados; excepciones y operaciones transversales; y
decisiones condicionales o documentadas en recorridos históricos.

La prioridad funcional es especificaciones, plan y resultado, seguida de los eventos
que los condicionan. Las operaciones informativas deben mejorar su claridad cuando
proceda, manteniendo cero preguntas adicionales por registros técnicos. Las pruebas
deberán medir tanto la información omitida como las confirmaciones innecesarias.

La revisión 3 del plan añade la [organización del contexto](CONTEXT-EFFICIENCY.md):
estos perfiles se distribuirán por familias y se cargarán según el evento y sus
condiciones. El inventario completo sirve para comprobar cobertura, no como lectura
obligatoria para cada decisión. PV-14 y PV-15 cubren organización y comparación;
las reglas comunes y el contrato necesario del proyecto se conservan.
