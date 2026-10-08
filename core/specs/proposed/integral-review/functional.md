# Propuesta funcional: revisión integral y desarrollo coordinado

Paquete **integral-review-02**, 2026-09-29. Estado: **validado para implementación local; ver evidencia en docs/plans/integral-review**.
[Revisión del paquete](REVIEW.md) · [Diseño técnico](technical.md).

## 1. Objetivo y alcance

Convertir el reparto de trabajo acordado en un recorrido claro y comprobable:
petición → propuesta integral revisada → cierre → planificación detallada →
revisión del encargo → implementación y verificación → validación del conjunto → PR.

El usuario ha pedido revisión transversal por los especialistas, cierre y
planificación centralizados, tareas asignadas que los técnicos revisan antes de
ejecutar, y definición de correcciones si el resultado conjunto no es aceptable.
El usuario ha confirmado la definición de hitos. Los mecanismos de adaptación que
se describen a continuación son propuestas pendientes de validar.

Se conservan los criterios ya expresados: proyectos individuales o de equipo;
configuración evolutiva; excepciones validadas; trazabilidad en el repositorio;
lenguaje didáctico; agilidad y uso proporcionado del contexto; Sonar y
Dependency-Check durante la implementación según la política del proyecto.

Quedan fuera: orquestación CI/CD, despliegues, conectores, notificaciones externas,
autenticación corporativa, agentes ejecutables y automatización de aprobación o
merge del PR. Se prepara la información de entrega y se puede registrar un PR
observado, pero no se publica nada por cerrar el recorrido SDD.

## 2. Participantes y responsabilidad

| Participante | Responsabilidad |
|---|---|
| Responsable de la petición | Recoge la necesidad, prepara la propuesta con el agente, coordina aportaciones, consolida el acuerdo, cierra la propuesta y genera/aprueba el plan si dispone de esos permisos. |
| Especialistas designados | Revisan la solución integral desde su experiencia, plantean inquietudes y cambios, y revisan, ejecutan y verifican las tareas que reciben. |
| Responsable de validación del conjunto | Comprueba el resultado integrado frente a lo acordado, registra aceptación o correcciones y prepara la entrega al proceso del PR. |

Son responsabilidades, no tres personas obligatorias. El responsable de la petición
puede validar el conjunto; un especialista puede contribuir en varios ámbitos. En
un proyecto individual la misma persona puede asumir todo, salvo que se configure
revisión independiente. El agente ayuda a analizar, redactar y ejecutar; no inventa
la conformidad de personas ni se registra como sustituto de su decisión.

El proyecto establece permisos; cada petición identifica a sus responsables y
revisores mediante identidades estables. El nombre de una especialidad no acredita
autoridad. La identidad declarada del operador mantiene ese grado de garantía.

## 3. Recorrido de una petición

### F1. Definir la petición y preparar la propuesta

El responsable concreta objetivo, comportamiento, reglas, alcance incluido y
excluido, restricciones y criterios de aceptación. La propuesta técnica explica la
solución global, sus componentes, interfaces, datos, impactos y decisiones críticas.
Puede construirse con ayuda de especialistas antes de abrir la revisión formal.

Se identifica la rama de trabajo, su base y destino. La petición y sus elementos
mantienen identidad permanente entre ramas. La propuesta puede tener varias piezas
documentales, pero se presenta como un paquete coherente, no como encargos aislados.

Salida: una propuesta concreta lista para evaluar; no un plan de tareas anticipado.

### F2. Revisar conjuntamente la propuesta integral

El responsable propone qué especialistas deben intervenir según los ámbitos afectados.
El plugin recomienda participantes a partir del proyecto y de impactos observados;
no inventa personas ni presume que siempre intervienen tres departamentos. La lista
de revisores obligatorios y opcionales se confirma para la petición.

La configuración vigente se reutiliza: si determina inequívocamente los participantes,
se muestra su aplicación y se continúa sin volver a aprobar la lista. Solo una
designación nueva, ambigua o modificada necesita decisión. Se cuentan personas por
su identidad estable, no etiquetas de rol: quien cubre Backend y BBDD emite una
conformidad integral, con ambos ámbitos visibles.

Cada revisor accede al conjunto y puede aportar cambios funcionales o técnicos,
incluidos los que afecten a otras especialidades. La revisión no se restringe a
los archivos que vaya a implementar. Puede realizarse en distintos chats y momentos.

Una aportación registra autor, objeto afectado, motivo y tratamiento propuesto. Se
distinguen sugerencias y objeciones que impiden la conformidad. El responsable las
consolida con resultado: incorporada, descartada con justificación o pendiente.
Las aportaciones no son tareas de implementación ni aprobaciones por sí mismas.

Cada revisor obligatorio emite sobre el paquete vigente «conforme» o «requiere
cambios». Su conformidad puede incluir la aceptación del tratamiento de sus
observaciones, evitando una firma por comentario. Si mantiene una objeción, el
responsable debe resolverla con él, cambiar el alcance o tramitar una excepción
competente y explícita. No puede borrar la objeción para cerrar la propuesta.

### F3. Cerrar la propuesta y planificar

El responsable recibe una vista con el contenido exacto, conformidades, cambios y
pendientes. Puede cerrar cuando todos los revisores obligatorios están conformes,
no quedan decisiones críticas y las excepciones aplicables son visibles y vigentes.
Un revisor opcional no bloquea por silencio; una objeción suya que identifique una
decisión crítica debe analizarse y resolverse, no ignorarse por su condición opcional.

El cierre aprueba esa propuesta funcional y técnica. Solo después se elabora el
plan detallado, con el responsable como coordinador y el agente como apoyo. Los
especialistas pueden contribuir al detalle. El responsable no tiene que inventar
soluciones técnicas pendientes para poder planificar.

Cada tarea incluye: objetivo, requisitos cubiertos, trabajo concreto, límites,
responsable, dependencias e interfaces, criterios de aceptación y pruebas previstas.
Se incluye una tarea explícita de integración cuando existen varias tareas. Su
alcance contempla escenarios completos y regresiones pertinentes, no solo juntar
código. El plan debe cubrir todo el alcance aprobado y evitar responsabilidad
principal duplicada sobre la misma obligación.

Se aprueba el plan y se autoriza su ejecución. Ambas decisiones pueden agruparse en
una respuesta; no se confunden con la aprobación anterior de la propuesta.

### F4. Revisar el encargo recibido

Antes de iniciar, cada técnico confirma que entiende su tarea, dispone del contexto
necesario y considera ejecutables su solución, dependencias y comprobaciones.
El plugin muestra el detalle de la tarea y la propuesta relevante, manteniendo
accesible el conjunto. Si solicita aclaración, solo se detiene el trabajo afectado.

La revisión puede agruparse con aceptar la asignación y empezar: «Acepto estas dos
tareas, su definición está clara; comienza la primera». Se conservan los hechos
separados sin exigir tres turnos. Ser propietario inicial no permite saltarse la
revisión si el proyecto la exige. Asumir una tarea no acredita haber validado su
contenido; la confirmación debe ser explícita.

Si el propio técnico ya aprobó el plan y el detalle exacto de sus tareas, el plugin
reutiliza esa decisión como revisión de sus encargos cuando su alcance explícito
la cubre. La presentación del plan informa de este efecto. No pide que acepte de
nuevo lo mismo ni crea una oferta de asignación a sí mismo. Haber redactado el plan,
por sí solo, no equivale a haberlo aprobado o revisado.

Un cambio en requisitos o solución vuelve a la propuesta; un ajuste de ejecución
dentro de lo aprobado se reconcilia en el plan/tarea. El destinatario no cambia por
su cuenta el contrato aceptado. Otro compañero puede asumir toda o parte de la tarea
con alcance y relevo registrados; revisará el encargo concreto que recibe.

### F5. Implementar, verificar y cerrar tareas

Cada técnico ejecuta las tareas autorizadas y disponibles según sus dependencias.
No se exige esperar a que todos los compañeros hayan revisado sus encargos cuando
una tarea independiente ya puede avanzar. Se conservan trazabilidad de cambios,
participantes y evidencias sobre el resultado exacto.

Sonar y Dependency-Check se deciden por separado: obligatorio, informativo o no uso
motivado. Se ejecutan/consultan con medios existentes durante la implementación;
se corrigen hallazgos del alcance y se repiten las comprobaciones afectadas. Un
error o falta de acceso no equivale a no utilización ni a resultado satisfactorio.

El técnico verifica su implementación si el proyecto lo permite. Con revisión
independiente, verifica otra persona habilitada. La tarea se cierra cuando cumple
sus criterios, evidencias y controles; las reservas aprobadas permanecen visibles.

### F6. Validar el conjunto

Se ejecutan las pruebas de integración definidas en el plan. La persona designada
revisa el desarrollo concreto, el cierre de las partes, sus evidencias y el
comportamiento completo frente a los requisitos.

Se conservan dos comprobaciones: integración técnica y aceptación funcional. Pueden
resolverse por la misma persona con permisos y evidencia adecuados, incluso con
una respuesta que mencione ambas. La aceptación funcional no sustituye las pruebas
técnicas, y una prueba técnica superada no implica aceptación del usuario.

Si falla una prueba de integración, se registra el fallo aunque esa tarea aún no
pueda cerrarse. Si falla la aceptación funcional, se registra el rechazo del
candidato ya integrado. Ninguno de los dos fallos necesita fingir un hito superado
para poder documentar la corrección.

Salida positiva: desarrollo integrado y aceptado, listo para preparar la entrega
al PR. Si cambia después el resultado, se reevalúa la vigencia de las evidencias y
de la aceptación; no se entrega otro candidato utilizando una aceptación antigua.

### F7. Preparar el PR y mantener la trazabilidad

Se prepara un resumen reutilizable con petición, alcance, cambios, tareas,
validaciones, evidencia, ramas/base y reservas. «Listo para PR» describe preparación
SDD; no afirma que el PR exista, esté aprobado o se haya fusionado.

Crear/enviar el PR sigue requiriendo una herramienta disponible y autorización de
sesión. Se puede registrar su URL y revisión observadas. Las decisiones remotas y
CI/CD pertenecen al proceso del repositorio. Un problema comunicado desde allí se
vincula a la petición mediante el mismo recorrido correctivo, sin conector automático.

## 4. Correcciones tras un resultado no aceptable

El plugin prepara una definición de corrección vinculada al candidato rechazado:
qué requisito se incumple, comportamiento esperado y observado, evidencia o pasos
de reproducción, impacto, criterio de corrección y tareas afectadas. Lo desconocido
se marca pendiente. El responsable confirma la clasificación y alcance; el agente
no autoriza automáticamente trabajo nuevo al registrar un fallo.

| Situación | Recorrido |
|---|---|
| Incumplimiento de un requisito ya aprobado. | Conservar el requisito; reabrir tarea y autorización vigentes si cubren la corrección, o incorporar tarea correctiva al plan y autorizar lo nuevo. |
| Ambigüedad o cambio de comportamiento/solución acordados. | Revisar la propuesta afectada, obtener sus conformidades y cierre, y actualizar/aprobar el plan antes de ejecutar. |
| Necesidad nueva e independiente. | Crear una petición relacionada; el responsable decide expresamente si afecta a la aceptación de la petición original. |
| Fallo de pipeline o infraestructura ajeno al desarrollo. | Registrar vínculo, evidencia y responsable externo conocido; no inventar una corrección de aplicación ni operar CI/CD. |

Se repiten las pruebas afectadas, las de integración pertinentes y la aceptación del
nuevo resultado. Un problema bloqueante se resuelve con evidencia y conformidad
competente, o mediante una excepción permitida; no desaparece por cambiar su título.
No se duplican requisitos ni se reinicia toda la petición para una corrección local.

## 5. Configuración, cambios y excepciones

- Configuración mínima reutilizable: responsable de petición, responsable de
  validación, criterio de selección de revisores, revisión del encargo, revisión
  independiente y controles de calidad. La lista concreta se fija por petición.
- Recorrido individual: una persona puede confirmar revisión y cierre conjuntamente;
  no se crean compañeros ficticios ni se exige una revisión independiente implícita.
- El responsable de cierre/planificación puede delegarse con motivo y vigencia.
  Una sustitución conserva decisiones históricas; nunca firma por el anterior.
- Cambios de proceso: se versionan y se decide qué peticiones abiertas los adoptan.
  Las no seleccionadas mantienen sus reglas, comprobando la autoridad actual.
- Una excepción identifica regla, sujeto, motivo, efecto, validador competente,
  transición y vencimiento. Puede dispensar una participación cuando el proyecto
  lo permita; no suplanta una firma ni convierte un fallo en éxito. No omite
  identidad, autorización, integridad documental ni evidencia veraz.
- Las confirmaciones vigentes se reutilizan. Un cambio material del paquete integral
  requiere nueva conformidad de sus revisores obligatorios, con diferencias claras;
  no afecta a peticiones independientes. En tareas, se revalida solo el encargo cuyo
  contenido, responsable o dependencias contractuales hayan cambiado.

## 6. Acompañamiento y agilidad

En cada hito y consulta, el plugin explica: petición y fase, trabajo completado,
pendientes concretos, persona que debe intervenir y acción siguiente. Distingue
falta de decisión, falta de permiso y fallo técnico. Recomienda con razones del
proyecto y evita pedir otra vez decisiones que siguen siendo válidas.

Ejemplo: «La propuesta ya tiene la conformidad de Frontend y Backend. Falta la
revisión de datos: debe confirmar cómo se guarda el historial. Después podrás
cerrar la propuesta y preparar el plan. No hay tareas de implementación autorizadas».

Ejemplo: «Tu tarea está revisada y autorizada. Puedes empezar. La tarea de datos
sigue pendiente de aclaración, pero no bloquea este trabajo según el plan».

No se exige un chat por fase, un documento por comentario ni una aprobación por
registro. Los eventos se generan desde decisiones expresadas en lenguaje natural,
con aplicación agrupada cuando procede. Un chat nuevo recupera hechos del repo;
no supone que otras conversaciones o clones ya estén sincronizados.

### 6.1 Hitos e intervenciones son conceptos distintos

Un **hito** es un resultado exigido por el proceso. Un **evento** es el registro que
acredita un hecho o una decisión. Una **intervención** es lo que se pide a una persona.
No hay correspondencia uno a uno: una intervención puede acreditar varios hitos y
un hito técnico puede acreditarse con ejecución y evidencia sin otra confirmación.

| Hito | Condición y acreditación | Cuándo interviene una persona |
|---|---|---|
| H1. Propuesta preparada | Necesidad, solución, alcance y aceptación concretos, sin decisiones críticas ocultas. | Aporta información o resuelve dudas; no se añade una firma de «borrador preparado». |
| H2. Propuesta validada y cerrada | Conformidades obligatorias y cierre competente sobre el paquete exacto. | Cada persona requerida decide una vez; si revisa y cierra, ambas decisiones se presentan juntas. |
| H3. Plan aprobado y ejecución autorizada | Plan concreto completo, tareas, responsables, dependencias y pruebas. | Una intervención puede aprobar y autorizar, además de revisar las tareas propias expresamente incluidas. |
| H4. Encargo revisado, por tarea o porción | Conformidad vigente del ejecutor sobre el detalle recibido. | Solo si falta una decisión que ya lo cubra; una persona puede revisar varias tareas juntas. |
| H5. Tareas implementadas, verificadas y cerradas | Evidencia y controles suficientes para cada transición. | Solo pruebas o revisiones humanas requeridas, incidencias o decisiones pendientes; no para confirmar cada escritura de estado. |
| H6. Conjunto integrado y aceptado | Pruebas técnicas del conjunto y aceptación funcional del mismo candidato. | El validador confirma lo que le corresponde; si es la misma persona, se presenta una revisión final conjunta con ambas acreditaciones. |
| H7. Entrega al PR preparada | Resumen y referencias del resultado aceptado, con reservas visibles. | No requiere otra aceptación SDD; crear/publicar el PR necesita la autorización externa que corresponda, reutilizando la ya existente. |

Los subresultados de H5 y H6 siguen siendo distinguibles. Agrupar su presentación
no convierte «implementado» en «verificado» ni pruebas superadas en aceptación
funcional. Cada hito muestra si está pendiente, disponible, completado, dispensado
con excepción o no requerido por política, y la fuente que justifica ese estado.
Estas son etiquetas de presentación; no se edita el estado para acreditar el hecho.

### 6.2 Adaptación obligatoria a las personas del proyecto

Antes de pedir una intervención, LKS-SDD debe:

1. Resolver quién ocupa cada responsabilidad con la configuración y designaciones
   vigentes, usando identidades estables. No inferir equivalencia por nombre/cuenta.
2. Identificar qué condiciones ya tienen decisión o evidencia válida.
3. Agrupar las decisiones pendientes de la misma persona cuando tienen contenido
   disponible, permisos compatibles y ningún requisito de independencia contrario.
4. Mostrar claramente qué se valida y qué permite avanzar esa respuesta.
5. Registrar los resultados aplicables, explicar el avance conjunto y continuar
   con las acciones ya autorizadas. No pedir confirmación para actualizar registros.

Esta adaptación se aplica por defecto; no exige que cada proyecto programe su propia
agrupación. Los roles no generan nuevas personas ni multiplican confirmaciones. Una
persona puede pedir ver las decisiones por separado sin cambiar el proceso.

No se agrupan decisiones sobre contenido futuro: aprobar una propuesta puede permitir
preparar el plan, pero no aprobar un plan aún no presentado. Tampoco se anticipa la
aceptación funcional del código que todavía no existe. Si falta una condición, el
plugin continúa lo independiente y solicita solo la intervención necesaria.

### 6.3 Recorridos de referencia

| Configuración real | Intervenciones esperadas en el recorrido normal |
|---|---|
| Una persona, sin revisión independiente | Tres momentos de decisión: propuesta integral y cierre; plan detallado, autorización y revisión de tareas propias; resultado integrado y aceptación funcional. Implementar, comprobar y preparar la entrega continúan dentro de la autorización vigente. |
| Responsable y un técnico que cubre varias especialidades | El técnico revisa una vez la propuesta integral. El responsable cierra y posteriormente aprueba el plan concreto. El técnico revisa conjuntamente sus tareas y ejecuta. El responsable acepta el conjunto apoyándose en la evidencia técnica. No se crean firmas distintas para Frontend, Backend y BBDD si son la misma persona. |
| Responsable que también implementa, más otros técnicos | Su revisión y cierre se agrupan si ambos están disponibles; su aprobación del plan cubre sus propios encargos explícitos. Los demás técnicos revisan los suyos; una revisión no acredita la de otra persona. |
| Varias personas con ámbitos distintos | Cada revisor obligatorio emite su conformidad integral y cada ejecutor revisa sus encargos, agrupados por persona. Las dependencias permiten ejecutar lo preparado sin esperar a todo el equipo. |
| Proyecto con revisión independiente | La persona revisora debe ser distinta de quien implementó, según la regla configurada. Si solo hay una persona disponible, se explica la incompatibilidad y se propone incorporar un revisor o cambiar explícitamente la política; no se rebaja el control automáticamente. |

Los tres momentos del caso individual son un criterio del recorrido normal, no un
límite que permita omitir aclaraciones, pruebas manuales necesarias, cambios de
alcance o permisos externos. Tampoco se vuelven a preguntar si ya existe una respuesta
explícita vigente sobre el contenido exacto. Configurar el proyecto ocurre aparte
y se reutiliza; no se repite por petición.

Ejemplo individual: «Validas la propuesta funcional y técnica completa. Como eres
responsable y revisor, esta decisión también cierra la propuesta. Después prepararé
el plan para que revises sus tareas concretas».

Ejemplo de plan individual: «Al aprobar este plan y autorizarlo, confirmas también
el detalle de las tareas A y B que ejecutarás tú. Empezaré A; B esperará al resultado
que necesita de A». Si el usuario aprueba solo el plan y reserva la ejecución, se
conserva esa separación; no se extiende su respuesta.

### 6.4 Guía continua sin interrupciones administrativas

El estado del proyecto muestra un mapa compacto de H1–H7 con el estado por petición,
la fase actual y las próximas intervenciones agrupadas por persona. El detalle por
tarea conserva H4/H5, dependencias y correcciones sin saturar el resumen.

Al completar varios hitos en una misma intervención se comunica un único avance,
con lo completado, lo pendiente y el siguiente paso. Si el siguiente trabajo ya
está autorizado, se anuncia y se realiza; no termina el turno con una pregunta
administrativa. Solo se solicita entrada si falta una decisión, información,
autoridad, evidencia humana o resolución de un impedimento real.

El sistema explica por qué agrupa: «No necesitas aceptar otra vez esta tarea: su
definición está cubierta por tu aprobación del plan». También explica por qué no
puede hacerlo: «La revisión debe realizarla otra persona porque este proyecto exige
independencia». Un cambio de miembros recalcula únicamente las intervenciones
pendientes o afectadas, conservando los hechos históricos acreditados.

## 7. Criterios de aceptación del cambio propuesto

Los identificadores AC-IR son locales a este paquete, no tareas de implementación.

| ID | Resultado observable esperado |
|---|---|
| AC-IR-01 | Un especialista puede aportar una objeción a cualquier parte de la propuesta integral y se conserva su tratamiento. |
| AC-IR-02 | El cierre se impide si falta una conformidad obligatoria vigente o queda una objeción bloqueante sin resolución/excepción competente. |
| AC-IR-03 | El responsable cierra una versión concreta y solo después genera un plan que cubre requisitos, pruebas e integración. |
| AC-IR-04 | Una tarea asignada, incluso a su propietario inicial, no empieza sin revisión del encargo exigida por la política. |
| AC-IR-05 | El destinatario puede aceptar asignación, revisar varias tareas explícitas y empezar una en una sola respuesta, sin decisiones implícitas. |
| AC-IR-06 | Un cambio de propuesta invalida la conformidad correspondiente; un cambio de tarea o relevo exige revisar el nuevo encargo sin reiniciar tareas independientes. |
| AC-IR-07 | El técnico verifica su tarea salvo revisión independiente; no se integra por tener código escrito si faltan verificaciones o calidad aplicable. |
| AC-IR-08 | Un fallo de integración o rechazo funcional registra evidencia y corrección pendiente sin necesitar una integración/aceptación positiva ficticia. |
| AC-IR-09 | Un defecto conserva el requisito original; un cambio del acuerdo exige propuesta/plan actualizados. Ningún fallo concede permiso para ampliar alcance. |
| AC-IR-10 | Tras corregir, se acredita el nuevo candidato y se repite la aceptación; un rechazo bloqueante no queda oculto por una aceptación antigua. |
| AC-IR-11 | Un proyecto individual completa el recorrido sin perfiles ficticios, reuniones ni controles independientes no configurados. |
| AC-IR-12 | Cambios de proceso, bajas, sustituciones y excepciones preservan historia y autoridad, y muestran las reservas. |
| AC-IR-13 | Una consulta o hito explica dónde se está, qué falta, quién actúa y cómo avanzar; una consulta no modifica documentos. |
| AC-IR-14 | Sin modificar el contrato, la operación lee contexto suficiente sin cargar por defecto conversaciones, informes e historial completos. |
| AC-IR-15 | Colisiones de alias, cambios concurrentes o base desactualizada no mezclan identidades ni permiten aplicar decisiones sobre otra versión. |
| AC-IR-16 | Proyectos 3.0 permanecen operativos con su runtime; la adopción del nuevo recorrido es explícita y no inventa revisiones históricas. |
| AC-IR-17 | Sonar/Dependency-Check conservan sus modos, resultados reales y vigencia; las excepciones no convierten not-run/error en passed. |
| AC-IR-18 | El resumen de entrega distingue preparación SDD, PR observado, aprobación remota y despliegue; no activa CI/CD ni publica por sí mismo. |
| AC-IR-19 | Una identidad con tres especialidades produce una sola intervención de revisión integral, con sus ámbitos visibles y sin firmas duplicadas por rol. |
| AC-IR-20 | En el caso individual sin incidencias, se completan H1–H7 con los tres momentos de decisión descritos, sin solicitudes administrativas por hito ni autoasignaciones ficticias. |
| AC-IR-21 | Una aprobación explícita del detalle de tareas propias acredita H4 sin nueva pregunta; autoría, silencio o aprobación de otra persona no lo acreditan. |
| AC-IR-22 | La agrupación no aprueba planes no presentados, candidatos futuros ni decisiones reservadas; no omite una revisión independiente. |
| AC-IR-23 | El mismo estado produce la misma lista de intervenciones pendientes en CLI, readiness y skills; se explican las agrupaciones y separaciones. |
| AC-IR-24 | Tras una decisión agrupada se muestra un avance conjunto y se continúa lo autorizado, sin terminar el turno para confirmar registros o transiciones técnicas acreditadas. |
| AC-IR-25 | Cambiar miembros, abrir otro chat o reintentar no duplica decisiones válidas; cambios materiales invalidan solo su cobertura conforme a la revisión integral o tarea correspondiente. |
| AC-IR-26 | Un proyecto de una persona con independencia exigida muestra un impedimento explícito y no inventa un segundo revisor ni desactiva la regla. |

## 8. Ejemplo completo

En una petición de vacaciones, la responsable define solicitud, aprobación y saldo.
Frontend advierte que debe mostrarse el estado pendiente; Backend plantea cómo evitar
aprobaciones simultáneas; BBDD propone conservar un historial. Las aportaciones
actualizan una misma propuesta funcional y técnica. Todos los revisores obligatorios
confirman esa versión y la responsable la cierra.

La responsable genera tareas de interfaz, servicio, datos e integración. Los técnicos
revisan sus encargos, resuelven dudas y ejecutan según dependencias. Verifican cada
parte con las pruebas y controles del proyecto. La tarea de integración comprueba el
recorrido completo.

La responsable detecta que una solicitud rechazada descuenta saldo. El requisito
original decía que solo lo descontaría una solicitud aprobada: se documenta ese
incumplimiento y se corrige la tarea afectada, sin inventar una nueva funcionalidad.
Tras repetir las pruebas y validar el candidato corregido, acepta y prepara el PR.
