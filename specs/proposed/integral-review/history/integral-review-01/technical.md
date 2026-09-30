# Propuesta técnica: controles de revisión integral

Paquete **integral-review-01**, 2026-09-29. Estado: **propuesto, no implementado**.
[Revisión del paquete](REVIEW.md) · [Comportamiento funcional](functional.md).

## 1. Base observada y diferencias

Base inspeccionada: plugin 3.0.0, commit
`0124fdb4927e04b2fbc773e36d2073e7e962a544`. Esta inspección acredita los mecanismos
existentes, no pruebas del comportamiento nuevo.

| Fuente actual | Hecho observado | Extensión propuesta |
|---|---|---|
| `scripts/v3_approval.py` | Aprobación por contenido exacto, cobertura de plan y tarea de integración para planes con varias tareas. | Conformidades por revisor designado, objeciones y cierre del paquete integral. |
| `scripts/v3_team.py` | Propietario, asignaciones y relevos con recepción explícita. El propietario inicial no depende de una recepción adicional. | Revisión del encargo independiente de la asignación, aplicable también al propietario inicial. |
| `scripts/v3_workflow.py` | Transiciones, autorización, dependencias, calidad, evidencia y revisión independiente. | Condiciones de revisión vigente, bloqueos correctivos y comprobación de designaciones. |
| `scripts/v3_verification.py` | Evidencias y registro de integración/aceptación positivas sobre candidato concreto. | Resultados negativos explícitos y ciclo correctivo conectado al candidato. |
| `scripts/v3_policy.py` | Permisos por roles, proceso configurable y autoridad vigente. | Responsabilidades nominativas por petición además de los permisos generales. |
| `scripts/v3_guidance.py` | Estado, preparación, trazabilidad y recomendaciones. | Próximo participante, causa concreta, ciclo correctivo y vistas compactas de revisión. |
| `scripts/v3_contract.py`, `v3_schema.py`, `v3_cli.py` | Formato 3.0 fijado y núcleo compartido. | Despacho explícito 3.0/3.1 y validación de las nuevas estructuras sin ignorarlas. |

## 2. Arquitectura y límites

Se mantienen las seis skills, la CLI local compartida entre Codex y Copilot, Python,
Markdown canónico e índice reconstruible. Las skills traducen la conversación y
presentan decisiones; el núcleo comprueba autoridad, contenido, dependencias y
transiciones antes de producir/aplicar cambios. Las garantías no dependen solo del
prompt ni pueden eludirse llamando directamente a una operación antigua.

No se añaden servicios, bases de datos, hooks, MCP, conectores, agentes ejecutables
ni notificaciones. La información vive en el repo y se comparte por sus medios
habituales. No hay bloqueo distribuido ni conocimiento automático de otros clones.
La identidad sigue siendo declarada: se controlan permisos documentales sobre el
operador identificado, no se promete autenticación corporativa.

La división técnica recomendada es un módulo de revisión para sus predicados y
eventos, otro para correcciones, y ampliaciones acotadas de los módulos existentes.
Esto describe responsabilidades arquitectónicas; no asigna tareas de implementación.

## 3. Modelo documental

Reutilizar los tipos existentes y añadir finalidades tipadas, no una entidad por
mensaje. Los campos de control tendrán schemas específicos; el `data` genérico
actual no será suficiente para admitir nuevas decisiones sin validarlas.

| Elemento | Datos nuevos propuestos y significado |
|---|---|
| Política | `collaboration`: exigencia de revisión integral, revisión del encargo, reglas de selección de participantes, permisos de cierre y excepciones admitidas. |
| Petición | `coordination`: UID del responsable, validador técnico y funcional; revisores designados, ámbito informativo y carácter obligatorio/opcional; referencia a política vigente para esa petición. |
| `decision`, finalidad `review-roster` | Confirma la lista de revisión y responsables sobre una revisión concreta; cambios posteriores quedan registrados. |
| `problem`, finalidad `review-comment` | Observación, autor, objetivo, base examinada, severidad, explicación y propuesta. No se borra al resolver. |
| `decision`, finalidad `comment-resolution` | Tratamiento incorporado/descartado, motivo, autor competente y evidencia/revisión relacionada; una objeción requiere conformidad posterior de su autor o excepción. |
| `decision`, finalidad `proposal-review` | Revisor, paquete y digest exactos, resultado conforme/requiere cambios y referencias a observaciones. |
| `decision`, finalidad `proposal-closure` | Cierre del responsable, digest integral, conformidades utilizadas y excepciones. Habilita la aprobación normativa de la propuesta en la misma operación atómica. |
| `decision`, finalidad `task-review` | Técnico, tarea, porción recibida, encargo exacto, asignación/relevo y resultado conforme/requiere aclaración. |
| Recibo/decisión de integración/aceptación | Resultado positivo o negativo explícito, candidato, pruebas, persona designada, reservas y defectos relacionados. |
| `problem`, finalidad `development-defect` | Fallo observado, origen integración/aceptación/externo, esperado/real, evidencia y candidato rechazado. |
| `change`, finalidad `correction-definition` | Definición correctiva, clasificación, requisitos originales o revisados, tareas afectadas, criterio de comprobación y alcance confirmado. |
| Recibo, finalidad `delivery-preparation` | Manifiesto del candidato aceptado y referencias necesarias para preparar PR; no acredita una acción remota. |

Todos conservan UUID permanente, revisiones, autoría, fecha y relaciones resolubles.
Los alias legibles no determinan identidad. Cada evento operativo se registra con
su propósito validado y no puede introducirse con `author` para eludir su guardia.
No se duplican cuerpos completos en cada evento: se referencian fuentes históricas
recuperables, junto a sus hashes y resultados.

Al activar el nuevo recorrido coordinado se proponen `proposal_review_required: true`
y `task_review_required: true` dentro de `collaboration`, y aceptación después de
integración. No se activa por instalar el plugin. El proyecto puede desactivar un
control con decisión y motivo de gobierno; el estado mostrará «no requerido por la
política», nunca «revisión superada». La aprobación de la propuesta y la autorización
del trabajo siguen siendo necesarias. En el recorrido individual se pueden mantener
ambas revisiones y agruparlas con cierre/inicio para evitar confirmaciones repetidas.
La independencia de revisión existente se configura por separado.

## 4. Semántica de revisión y vigencia

### Propuesta integral

La base de una revisión incluye todas las unidades funcionales/técnicas del paquete,
sus requisitos, criterios, interfaces, restricciones y decisiones tecnológicas
aplicables. Incluye la lista de participantes y política que determinan el cierre.
Se reutiliza el mecanismo de descriptor y su cobertura transitiva.

Un revisor emite una decisión sobre esa base concreta. Para cerrar se exige una
conformidad vigente de cada revisor obligatorio, autoridad actual del responsable,
ausencia de decisiones críticas pendientes y resolución de objeciones. Una decisión
de otro actor autorizado genéricamente no sustituye la del revisor designado.

Una aportación no invalida por sí sola todas las decisiones: una objeción abierta
bloquea el cierre; si se cambia contenido normativo, el nuevo digest requiere nuevas
conformidades del paquete integral. Se presenta el cambio y su impacto, conservando
el acceso al conjunto. No se reutiliza una revisión previa mediante una equivalencia
semántica decidida por el modelo. Solo metadatos expresamente no normativos pueden
cambiar sin alterar la base. Las propuestas de peticiones independientes no caducan.

Cambiar revisores o responsables requiere el permiso y la decisión correspondientes;
no permite retirar un disidente para aparentar unanimidad. Debe explicar motivo,
observaciones abiertas y tratamiento de su responsabilidad. Las bajas se conservan
como historia. Para una conformidad todavía pendiente, el sustituto revisa y firma
por sí mismo; una baja no fabrica esa conformidad.

### Tarea y relevo

La base de revisión del encargo comprende definición, criterios, pruebas,
dependencias contractuales, obligaciones de propuesta, reglas aplicables del plan
y porción de responsabilidad. Reutilizar `task_basis` con una referencia explícita
a asignación/relevo y ámbito. El resultado de ejecución de una dependencia no
invalida la revisión del encargo si su contrato no cambia; se comprueba aparte al
empezar. No incluir el código mutable en esta base: cada edición de implementación
no debe exigir aceptar de nuevo la definición de la tarea.

La revisión debe proceder del destinatario actual, también cuando es el propietario
inicial. Para un relevo parcial se revisa la porción recibida y sus contratos comunes;
no se atribuye al receptor la revisión de toda la tarea. La ejecución solo puede
afectar a su alcance permitido. Un relevo aceptado y una revisión del encargo pueden
registrarse juntos, pero tienen significados verificables por separado.

## 5. Condiciones de avance

| Operación | Condiciones nuevas, además de las actuales |
|---|---|
| Cerrar/aprobar propuesta | Responsable designado y habilitado, paquete completo, revisiones obligatorias vigentes, observaciones resueltas o excepción competente. |
| Crear/aprobar plan | Cierre vigente de la propuesta que cubre ese plan; mantiene cobertura, dependencias e integración existentes. |
| Iniciar/reanudar/implementar | Revisión vigente del encargo y de la porción del actor; ausencia de un bloqueo correctivo incompatible; autorización y asignación actuales. |
| Verificar/cerrar tarea | Evidencia vigente, criterios y calidad; independencia cuando corresponda; defectos bloqueantes sin resolver impiden el cierre positivo. |
| Registrar integración positiva | Validador técnico designado, tareas cerradas, pruebas del conjunto y candidato exacto; no hay correcciones bloqueantes abiertas. |
| Registrar aceptación positiva | Validador funcional designado, integración vigente del mismo resultado y criterio funcional confirmado; sin rechazo/corrección bloqueante pendientes. |
| Preparar entrega | Aceptación vigente, referencia Git/candidato actual y reservas visibles. No implica PR ni merge. |

Un resultado negativo de integración/aceptación requiere identidad, autoridad,
candidato observado y explicación/evidencia del fallo, pero no superar las
condiciones de un resultado positivo. Así puede registrarse un fallo de la tarea
de integración antes de que todas las tareas estén cerradas.

Estos predicados se comparten entre operaciones, readiness y status. La escritura
manual de estados o una aprobación genérica no satisfacen los hechos requeridos.
La política heredada 3.0 mantiene su comportamiento; la política nueva activa estos
controles explícitamente. Ningún rol general omite una designación específica.

## 6. Operaciones y experiencia conversacional

Nombres orientativos de CLI, sujetos al diseño final de la interfaz; no son nuevos
entrypoints de skills ni comandos que el usuario tenga que aprender.

- `review`: ampliar la consulta para presentar paquete, cambios, participantes,
  observaciones pendientes y decisiones que se solicitan. No escribe.
- `review-comment` y `resolve-comment`: registrar observación/tratamiento, con base
  exacta y actor. La resolución sola no finge la conformidad del autor.
- `review-proposal`: registrar conforme/requiere cambios de un revisor designado.
- `close-proposal`: comprobar revisiones y registrar cierre/aprobación atómicos.
- `review-task`: registrar conformidad o aclaración solicitada sobre uno o varios
  encargos identificados; se puede agrupar con aceptación de relevo e inicio.
- `integrate` y `accept`: incorporar resultado negativo y sus defectos; el positivo
  mantiene comprobaciones y vigencia, además de las nuevas designaciones.
- `define-correction`: preparar/confirmar definición y clasificación, enlazando
  defecto, requisitos y tareas; no autoriza ejecución por sí misma.
- `resolve-defect`: comprobar evidencia correctiva y confirmar la resolución
  competente sin borrar el fallo ni sustituir la aceptación final.
- `prepare-delivery`: producir resumen/manifiesto local; adjuntar URL de PR solo
  si está observada y se ha solicitado registrarla.

El núcleo ofrece una composición transaccional pequeña de operaciones compatibles,
no un lenguaje general de automatización. Valida cada paso sobre el estado resultante
del anterior y aplica todo o nada con el mecanismo existente de preview/aplicación.
Una autorización que cubre varias tareas identifica exactamente cuáles. Reintentar
un mismo paquete aplicado devuelve su recibo, sin duplicar decisiones.

No se envían mensajes a otros chats ni se activan otros agentes. El siguiente
participante encuentra su trabajo mediante consultas al repo sincronizado.

## 7. Correcciones y resultado vigente

Un rechazo crea un evento de fallo y una definición correctiva en borrador en una
operación recuperable. Si hay varios fallos, permite varias correcciones vinculadas.
El rechazo bloquea la entrega del candidato aunque aún falte concretar la corrección.

El responsable confirma la clasificación: incumplimiento, cambio de acuerdo, nueva
necesidad o problema externo. Si la autorización y definición de la tarea ya cubren
la corrección, puede reabrirse sin volver a aprobar el mismo alcance. Añadir tareas,
cambiar contratos o ampliar alcance requiere reconciliar el plan y sus autorizaciones;
si cambia la solución/función, primero la propuesta.

El grafo correctivo conserva defecto → definición → requisito/versión → tarea →
evidencia → resolución → nueva validación. Resolver el defecto no acepta el resultado
completo. La aceptación solo vale para el candidato acreditado y después de resolver
los bloqueos. Si hay decisiones concurrentes contradictorias, se exige reconciliación
explícita; no gana el último timestamp ni una aceptación histórica encontrada al azar.

Extender `result_current`, `request_facts` y `task_authority` según estas relaciones.
Los controles de calidad conservan sujeto, configuración y vigencia actuales; no se
relanzan análisis cubiertos sin cambios ni se reutilizan sobre entradas diferentes.
Un problema externo puede dejar un bloqueo de entrega externo visible sin afirmar
que la aceptación funcional previa era falsa ni convertir el plugin en un pipeline.

## 8. Concurrencia, excepciones y conservación

Las escrituras verifican base documental y Git observadas antes de aplicar. Una
conformidad sobre un paquete anterior no habilita el nuevo. Eventos en ramas distintas
mantienen UUID; conflictos de responsabilidad, cierre o resolución se reconcilian
con autoridad y motivo. No hay garantía de exclusión entre clones desconectados.

Las excepciones actuales centradas en tareas deben admitir como sujeto una petición
para dispensar revisión/cierre cuando la política lo permita. Se exige regla,
transición, motivo, efecto, emisor competente, sujeto/revisión y vencimiento. Se
preservan las firmas ausentes y reservas; la excepción no registra una conformidad
ficticia. La regla offline del proyecto sigue aplicándose.

Se reutilizan preview, comprobación de base, recibos y recuperación de `v3_storage`.
Los eventos operativos pasan por sus servicios; `author` no puede crear cierres,
conformidades o resoluciones disfrazados de documentos ordinarios. El estado derivado
se reconstruye únicamente desde documentos válidos y no desde etiquetas editadas.

## 9. Compatibilidad y adopción propuesta

Proponer formato documental **3.1**, método **3.1.0**, manteniendo la familia del
producto v3. La versión de publicación del plugin se fija al planificar la release;
no se cambia en este paquete. El nuevo formato evita que un runtime 3.0 ignore
campos de control que antes no interpretaba.

El nuevo runtime leerá explícitamente 3.0 y 3.1, incluidos sus históricos. El despacho
rechazará formatos desconocidos sin intentar un escritor v2. Un runtime 3.0 seguirá
operando solo sus proyectos compatibles. Instalar una versión nueva o consultar un
proyecto no lo actualiza ni activa este recorrido.

La adopción 3.0 → 3.1 presenta un preview con runtime requerido, política,
participantes y efecto por petición abierta. El usuario puede activar el recorrido
solo para nuevas peticiones y conservar las abiertas con política anterior. Si una
petición abierta lo adopta, se identifican las confirmaciones pendientes para su
siguiente paso; no se inventan revisiones ni se conceden permisos retroactivos.

Las migraciones 2.x existentes se conservan. La activación del nuevo recorrido será
un paso explícito posterior a una migración soportada, sin añadir aquí otro lector
de legado. La actualización de formato conserva identidades, evidencia e historia.
El rollback vuelve a la instantánea previa solo si no hay cambios posteriores; con
eventos nuevos se requiere recuperación hacia adelante, nunca descartarlos.

## 10. Uso eficiente del contexto

- Cargar al entrar la operación, política aplicable y estado compacto de la petición;
  ampliar con los documentos necesarios. Mantener seis descripciones breves y sin
  solapamiento; reglas nuevas en referencias cargadas cuando esta política se usa.
- La revisión integral accede a todas las obligaciones de la propuesta. Un resumen o
  un hash ayudan a localizar, pero no sustituyen su contenido ni acreditan lectura.
  Si no cabe con seguridad, dividir la revisión en lecturas sucesivas conservando
  la base exacta antes de emitir la conformidad integral.
- Para ejecutar una tarea, cargar su encargo, obligaciones aplicables, contratos,
  decisiones y dependencias. No cargar por defecto el historial de todos los revisores.
- Consultas paginadas con pendientes abiertos primero; informe completo y decisiones
  históricas recuperables por UID/revisión. No generar un archivo por intercambio.
- El núcleo puede recorrer el grafo necesario localmente; el coste de esa validación
  no exige inyectar todo el grafo y todas las evidencias en el contexto del modelo.
- Las cachés son derivadas y se invalidan por hashes de fuentes/política. No sustituir
  el contexto normativo por el selector experimental actual ni afirmar ahorros sin
  mediciones y comprobación de suficiencia. Calidad y cobertura prevalecen.

`status` devolverá primero resumen de fases, responsables y cantidades pendientes;
los detalles de tareas/comentarios se paginarán antes de serializarlos. No basta
paginar peticiones y devolver dentro de cada una todas sus tareas. `readiness` de
petición, además del actual de tarea, explicará exactamente qué condición impide
cerrar propuesta, integrar, aceptar o preparar entrega.

## 11. Verificación prevista e impacto

Esta sección define cómo se comprobará la propuesta cuando se implemente; no acredita
pruebas ejecutadas ni es un plan de tareas.

| Área del diseño | Criterios funcionales que debe demostrar |
|---|---|
| Paquete integral, participantes, comentarios y cierre. | AC-IR-01, AC-IR-02, AC-IR-03, AC-IR-06. |
| Revisión de tarea, asignación y ejecución. | AC-IR-04, AC-IR-05, AC-IR-06, AC-IR-07. |
| Fallo, corrección, vigencia y nueva aceptación. | AC-IR-08, AC-IR-09, AC-IR-10, AC-IR-18. |
| Política, permisos nominativos, excepciones y concurrencia. | AC-IR-11, AC-IR-12, AC-IR-15. |
| Guidance, skills y selección de contexto. | AC-IR-13, AC-IR-14. |
| Formatos, runtime fijado y adopción. | AC-IR-16. |
| Calidad y preparación de entrega. | AC-IR-07, AC-IR-17, AC-IR-18. |

Las pruebas deberán incluir: cierre sin una firma; firma sobre otro digest; objeción
descartada sin conformidad; bypass por `approve`, `author` o edición de estado;
propietario inicial sin revisión; revisión de otra persona; relevo parcial;
revocación/baja; firma duplicada; cambio de contrato y código; rechazo seguido de
aceptación antigua; corrección dentro/fuera del alcance; concurrencia y reintentos;
rollback con cambios posteriores; proyecto individual y proyecto 3.0 conservado.

La validación conversacional de Codex y Copilot debe comprobar que explican la
decisión concreta y no registran firmas ajenas. Las pruebas del núcleo no acreditan
esa experiencia real. Las comprobaciones de publicación seguirán la política
vigente de `docs/VALIDATION.md`, sin crear una campaña global por cada operación.

Riesgos principales: imponer revisiones repetidas, invalidar demasiado contexto,
mezclar roles genéricos con designaciones, y aceptar evidencia de otro candidato.
Se contienen con composición de decisiones, bases diferenciadas por propuesta y
tarea, predicados compartidos y referencias exactas. No se promete autenticación,
bloqueo entre clones ni adopción automática.

## 12. Decisiones pendientes

Todos los comportamientos y elecciones técnicas anteriores están propuestos para
validación conjunta. No queda una decisión crítica sustituida por «a decidir durante
la implementación». Tras validar se concretarán los nombres definitivos de CLI,
la descomposición de módulos/pruebas y la versión de release en el plan, sin alterar
el alcance aprobado. Cualquier cambio material volverá a esta propuesta.
