# Plan de implementación: distribución dual y relevo visual con Codex

Fecha del plan: 2026-09-10. Actualización: 2026-09-11, **implementación autorizada y en validación**.

La ejecución actual y sus límites se registran en [aceptación dual](../DUAL-HOST-ACCEPTANCE.md).
Se implementa la primera entrega P01–P10 con versión 1.1.0-rc.1 y contrato consumidor
1.5 intacto. P11 permanece separado; la autorización no incluye publicar, instalar
en cuentas activas, crear commits ni atribuir aceptación humana no ejecutada.

Ampliación autorizada el 2026-09-11: Copilot se entrega preferentemente como plugin
de agente instalable en su panel Plugins, no como VSIX. Se conserva la alternativa
de skills de proyecto, con migración explícita sin duplicados. La documentación
incluye un itinerario para principiantes compartido con help. Esta actualización
sustituye las menciones del plan inicial que limitaban Copilot a archivos de proyecto.

Base revisada: LKS-SDD 1.0.0, contrato consumidor schema 1.5 / método 1.5.0. Este es un plan de mantenimiento del producto, no una planificación TASK de un proyecto consumidor ni una autorización para implementar, instalar o publicar.

Complementa y actualiza la [propuesta técnica inicial](../proposals/2026-09-10-codex-copilot.md). La decisión de esta conversación sustituye su exigencia anterior de generar imágenes dentro de Copilot mediante un proveedor externo.

## 1. Decisiones confirmadas y límites

| Decisión confirmada por el usuario | Consecuencia de implementación |
|---|---|
| Un producto y repositorio, con distribución Codex y distribución GitHub Copilot en VS Code | Un núcleo, versiones coordinadas y adaptadores generados; no dos implementaciones del método |
| No dar soporte a la extensión Codex de VS Code | El destino Codex de esta entrega es la aplicación; Copilot utiliza VS Code en modo Agent |
| Las imágenes de prototipado se generan en Codex | No incorporar API de imágenes, claves adicionales, extensión generadora ni servidor MCP de imágenes |
| Copilot invita al usuario a continuar esa parte en Codex | Preparar un relevo durable y un mensaje listo para pegar, sin automatizar el cambio de aplicación |
| Volver a Copilot es opcional | Al terminar el prototipado, la persona puede permanecer en Codex o volver a Copilot |
| Si ya se trabaja en Codex, el proceso sigue normalmente, sin avisos de relevo | No preguntar por cambiar de herramienta, no mostrar mensajes sobre limitaciones de Copilot ni crear una ficha de relevo innecesaria |
| Distintas personas pueden compartir el mismo proyecto | Contexto, imágenes y decisiones transferibles mediante Git; cuentas, permisos y sesiones individuales |

«Sin decir nada» se aplica a la mecánica del relevo, no a ocultar un fallo, saltar una confirmación exigida o aprobar un diseño por silencio. Codex sigue presentando las propuestas y solicitando selección/correcciones como hace hoy. Si no dispone de generación de imágenes o de permisos, explica el impedimento y mantiene el pendiente; no busca una API de pago ni crea un bucle de invitaciones a Codex.

El objetivo es **equivalencia del proceso completo con relevo visual explícito**, no generación nativa de imágenes en Copilot. La aceptación no exigirá capacidades que se han descartado deliberadamente.

Se conserva la generación integrada de Codex, sujeta a acceso y límites de la cuenta; no se promete uso ilimitado ni consumo de créditos de Copilot para ese paso. [Documentación oficial de generación de imágenes](https://learn.chatgpt.com/docs/image-generation).

Fuera de alcance: compartir cuentas o conversaciones, lanzar agentes en segundo plano para realizar el relevo, abrir aplicaciones mediante protocolos no comprobados, nuevas skills, ampliaciones automáticas de autoridad y cambios en `specs/canonical/`.

## 2. Alcance de entrega y orden

La primera entrega debe cubrir las seis skills y la funcionalidad vigente, con la excepción de superficie acordada para imágenes. No será un paquete que solo permita definir prototipos.

**Primera entrega: distribución dual y colaboración por relevo secuencial.** Un responsable de escritura por alcance documental/visual; el trabajo se transfiere de forma explícita entre herramientas o personas. Cada relevo se prueba en la misma carpeta y entre clones distintos. No requiere resolver previamente toda la concurrencia distribuida del producto.

**Iteración posterior propuesta: colaboración paralela avanzada.** IDs distribuidos, coordinación entre clones, índice por ejecución y reconciliación de ramas del plan inicial. Sigue incluida como evolución del producto, pero no es un requisito técnico del salto visual. Su activación y el cambio de contrato requieren una decisión de alcance separada; la primera entrega no se anunciará como certificada para escritores simultáneos sobre el estado compartido.

No se fija todavía una versión de release. Empaquetar para otro host y añadir metadatos auxiliares puede ser compatible; alterar IDs, schema o semántica existente puede exigir una versión mayor. P01 resolverá esa clasificación antes de cambiar contratos o anunciar numeración.

## 3. Comportamiento esperado por situación

| Situación | Comportamiento exigido |
|---|---|
| Codex, interfaz nueva o cambio material, brief suficiente e ImageGen disponible | Generar y revisar según el flujo actual; cero mensajes, preguntas o archivos de relevo |
| Codex recibe una ficha preparada desde Copilot | Validar proyecto, versión, alcance y referencias; continuar solo el prototipado solicitado |
| Copilot, interfaz nueva o cambio material, brief suficiente | Preparar relevo y mostrar una única invitación clara; no intentar generar imágenes por otra vía |
| Brief incompleto | Continuar la definición en la herramienta actual; preguntar por las decisiones que faltan antes de ofrecer el relevo |
| Reutilización de una baseline visual confirmada sin generación necesaria | Reutilizarla en cualquiera de las herramientas; no ofrecer un salto innecesario |
| Backend o cambio sin impacto visual | No introducir pasos de imágenes ni de relevo |
| Copilot retoma y faltan imágenes o aprobación | Mostrar exactamente qué falta; no cerrar la definición visual ni repetir el mismo aviso en cada turno |
| Cambio material posterior sobre la propuesta | Crear una nueva revisión/relevo cuando proceda; conservar resultados y decisiones anteriores |
| Host desconocido o versiones incompatibles | Diagnóstico acotado; no inferir Codex por encontrar `.codex-plugin` ni Copilot por encontrar `.github` |

La procedencia del host la aporta el adaptador cargado y se contrasta con sus capacidades. No se persiste un «editor del proyecto» compartido: dos personas pueden usar hosts distintos. Host y disponibilidad de herramienta son datos de enrutamiento, no autorización.

El relevo solo bloquea el cierre visual y los pasos que dependan de él. Puede continuar trabajo independiente permitido por el método; no bloquea artificialmente todo el proyecto. No sustituye las capturas de verificación de la aplicación: esas continúan en el host que verifica, con sus herramientas de navegador.

## 4. Contrato mínimo del relevo

### 4.1 Archivos y autoridad

Propuesta de ubicación: `.lks-sdd/handoffs/visual/<handoff-id>/`, versionada y transferible. Contendrá una solicitud Markdown y resultados asociados. Su schema auxiliar tendrá versión propia, distinta del schema de proyecto; la compatibilidad real deberá demostrarse con fixtures antes de mantener el número 1.5.

Estos documentos son coordinación operativa. Los requisitos, UX, VIS, ADR, pendientes y autorizaciones canónicos siguen en los Markdown actuales de `docs/lks-sdd/`; no se trasladan a un nuevo registro ni se duplican como decisiones alternativas. Una solicitud puede incluir un brief de generación delimitado y referencias a sus fuentes, pero nunca prevalece sobre un cambio confirmado del contrato.

Las imágenes permanecen en la ubicación actual: `docs/lks-sdd/03-solution/ui-prototypes/`, con PNG/JPEG, nombre estable, revisión, firma, dimensiones y SHA-256. La procedencia real sigue siendo ImageGen. No se renombra una captura, un SVG o un placeholder como salida generada.

Antes de una ejecución de implementación no se crean AUTH, EXEC o CKPT ficticios. El relevo de definición no es un checkpoint de ejecución. Si ya existe una ejecución afectada, se enlaza y se utiliza su protocolo actual de pausa/reanudación, sin ampliar su autorización.

### 4.2 Contenido de la solicitud

- ID propio de relevo sin colisión entre clones; no consumir un VIS hasta que exista el asset conforme al contrato actual.
- Versión de formato, producto/núcleo y contratos; identidad del proyecto e incremento y, solo si ya existen, TASK/EXEC relacionados.
- Tipo de trabajo: generar alternativas, editar una referencia o completar una propuesta; alcance incluido y excluido.
- Referencias relativas a pantallas, requisitos, criterios, decisiones, brief y assets de entrada; huellas de las entradas relevantes.
- Revisión Git observada cuando exista y huella de los archivos efectivos, también si hay cambios locales aún no confirmados.
- Estado operativo, responsable/rol, restricciones de clasificación y siguiente acción segura.
- Instrucción de entrada para Codex: leer la ficha, comprobar su vigencia, completar exclusivamente el prototipado y registrar el resultado sin asumir autorización de implementación.

No incluir rutas personales como requisito de reanudación, credenciales, historial de chats ni datos ajenos al alcance. El mensaje para pegar debe referir a los archivos; no copiar documentos confidenciales completos por comodidad.

### 4.3 Resultados y reanudación

El resultado enlaza solicitud/revisión, assets y hashes, VIS, decisión humana, alternativas descartadas y pendientes. Mantiene los estados `proposal`, `confirmed`, `rejected` o `superseded` que corresponden a los artefactos actuales. Una generación exitosa no implica aprobación; una aprobación visual no autoriza a implementar.

Estado de relevo orientativo: solicitado → en curso → pendiente de aprobación → completado. Cancelado o reconciliación requerida son salidas explícitas. Los rótulos definitivos se fijan en P01; no se añaden directamente a enums del schema 1.5. «Completado» se deriva de resultados y contrato válidos, no de una bandera que el agente pueda marcar para ignorar checks.

Al volver a Copilot, validar proyecto, versión, alcance, existencia y firma de archivos, hashes, referencias UX/VIS/ADR y aprobación. Comparar las entradas del brief con su versión preparada; separar los cambios esperados del resultado visual de cambios ajenos que invaliden la solicitud. No comparar ciegamente todo el árbol, pues las imágenes y su registro necesariamente lo modifican.

Si falta evidencia, hay conflicto o el brief cambió, informar y reconciliar. Con estado válido, recalcular readiness del alcance y ofrecer el siguiente paso normal. No regenerar imágenes aprobadas ni afirmar que una interfaz está implementada por disponer de un prototipo.

### 4.4 Robustez

- Operaciones locales con preview cuando escriben, autorización acotada, control de cambios concurrentes y recuperación sin sobrescribir modificaciones ajenas.
- Repetir preparación o lectura no duplica solicitudes, VIS, ADR ni avisos; una nueva revisión material sí crea historia diferenciada.
- No guardar el hecho «aviso mostrado» en una caché personal necesaria para continuar. El estado compartido explica la pausa; el chat solo controla la frecuencia de mensajes.
- No excluir toda `.lks-sdd/handoffs/` de las huellas por comodidad. P01/P07 deben separar metadatos administrativos de entradas sustantivas y demostrar que cambios en brief/imagen/decisión invalidan lo que corresponda.
- No cerrar ni borrar la solicitud anterior al actualizar el producto. Conservar el historial, sin reescribir EVID ni aprobaciones anteriores.
- Tras un fallo o cierre de aplicación, reanudar desde los archivos; no asumir que una operación terminó porque aparece en el último mensaje.

## 5. Experiencia de usuario que debemos implementar

Mensaje propuesto en Copilot, únicamente cuando toca generar imágenes:

> El brief está listo. Para generar y revisar estos prototipos, abre este mismo proyecto en la aplicación Codex. He preparado una ficha con el contexto y un mensaje para continuar allí. Al terminar podrás seguir en Codex o volver aquí.

El mensaje listo para copiar incluirá la ruta relativa real, no un ID de ejemplo. La invitación no crea una sesión ni abre una aplicación automáticamente.

Al recibir el relevo, Codex realiza los controles necesarios sin obligar a repetir la entrevista ya documentada. Una duda o contradicción real sí debe preguntarse. Si la generación ocurre en una sesión Codex nativa sin relevo, no se muestra ninguno de estos textos.

Al finalizar un relevo recibido, Codex puede indicar una sola vez:

> Los prototipos y la decisión visual están guardados. Puedes continuar aquí o volver a Copilot; el estado necesario está en el proyecto.

Si no existe aprobación, el mensaje expresa que sigue pendiente. No ofrecer un regreso obligatorio, ni detener una continuación que la persona ya haya solicitado y esté autorizada.

Al volver a Copilot, una solicitud normal de continuar dispara la lectura del estado y su validación; no se dependerá exclusivamente de un comando especial ni de seguir en el mismo chat. Help y consultas de estado siguen siendo de solo lectura.

## 6. Paquetes de implementación

Los IDs P01–P11 siguientes son paquetes de este plan, no TASK canónicas. Los archivos nuevos indicados son propuestas; no se presentan como existentes. No se asignan personas, fechas ni esfuerzos no acordados.

| Paquete | Objetivo, cambios y entregables | Dependencias | Criterio de terminado |
|---|---|---|---|
| P01 — Contratos e inventario | Especificación propuesta de distribución/relevo en `specs/proposed/`; mapa de F01–F25; formato de fichas; política de avisos, huellas y compatibilidad. Inventariar la CLI completa y todos sus subcomandos | Ninguna | Sin ambigüedad sobre Codex nativo, Copilot, autorización, reanudación y datos compartidos; decisión documentada sobre necesidad o no de evolución de schema |
| P02 — Núcleo portable | Manifiesto neutral y lock por proyecto; resolver runtime/instrucciones exactos. Adaptar `scripts/lks_sdd.py`, `scripts/doctor_project.py` y localizadores de recursos sin romper comandos actuales | P01 | Mismo núcleo byte a byte en ambos paquetes; dos proyectos con versiones distintas no mezclan workflows ni scripts |
| P03 — Adaptadores de las seis skills | Fuente común y generación Codex/Copilot; skills Copilot en `.github/skills/`; descripción e invocación implícita intactas; contexto de host explícito y sin séptima skill | P01, P02 | Todas las referencias se resuelven; ambos hosts enrutan los seis objetivos y Codex no muestra mensajes del otro adaptador |
| P04 — Instalación y actualización | Paquete consumidor con runtime fijado, instrucciones comunes y bloques gestionados. Preview, colisiones, hashes, retirada no destructiva y preservación de instrucciones ajenas | P02, P03 | Un clon nuevo puede usar la versión exacta; no requiere cachés del compañero ni comparte secretos; actualización no borra evidencia |
| P05 — Motor offline de relevo | Nuevo módulo propuesto `scripts/manage_visual_handoff.py`, schema auxiliar y plantilla; preparar/consultar/validar resultados con escritura delimitada. Exponer CLI solo tras implementar y probar la operación | P01, P02 | Relevo durable, idempotente, recuperable y legible sin chat; solicitud previa a implementación no crea EXEC/CKPT ficticios |
| P06 — Integración conversacional | Adaptar `lks-sdd-define` y su referencia `frontend-design.md`; contexto/readiness reconocen el pendiente; Codex consume relevo; Copilot valida retorno; guías de mensajes y prompts | P03, P05 | Ida y vuelta completa; generación nativa Codex sin avisos/archivos de relevo; retorno opcional y aprobación explícita preservada |
| P07 — Validación, huellas y seguridad de estado | Integrar validadores visuales existentes, readiness, status y selección explícita. Revisar `scripts/validate_project.py`, `scripts/experience_engine.py` y continuidad. No relajar Source=ImageGen ni PNG/JPEG | P05, P06 | Rechazo de assets falsos, deriva, ausencia de aprobación, rutas fuera de alcance y versión incompatible; sin cierres ni reutilización falsos |
| P08 — Resto de capacidades por host | Adaptar navegador, terminal, revisión de imágenes y peer Rovo; conservar controles Jira, evidencia, scopes, planificación, implementación, doctor y exportación cliente | P03, P04 | F01–F25 cubiertas conforme a la excepción visual aprobada; una capacidad ausente conserva su bloqueo real |
| P09 — Pruebas automáticas y de usuario | Nuevos tests de empaquetado/adaptador/relevo y adversariales; actualización de fixtures/evals y registro en `quality/test-suites.json`; ensayos reales con equipo mixto | P04–P08 | Matriz de la sección 8 ejecutada, resultados por canal y ausencia de regresiones; pruebas reales no sustituidas por mocks |
| P10 — Release dual y documentación | Evolucionar `scripts/build_candidate_package.py`, CI e inventario de assets; doble build; validación extraída; manuales de instalación, relevo, límites y rollback | P09 | RC de dos destinos desde el mismo commit, documentación coherente y evidencia exacta; publicación/instalación quedan sujetas a autorización separada |
| P11 — Colaboración paralela avanzada | Desarrollo posterior del contrato de IDs, ejecuciones, reservas y reconciliación entre clones; protección de writes Jira. Retomar riesgos descritos en la propuesta inicial | P01; integración después de P10 | Solo tras aprobar su alcance y ejecutar sus propios ensayos; no atribuir su garantía al relevo secuencial |

Dentro de P08, las pruebas con servicios remotos usarán cuentas/proyectos sintéticos autorizados. Configurar Rovo no queda autorizado por aprobar este plan. P05 no incluye un generador ni un cliente de API de imágenes; solo coordina documentos y valida archivos.

### Hitos de salida

1. **H1: contrato cerrado** — P01; comprobar con ejemplos los recorridos nativo, relevo y retorno antes de desarrollar.
2. **H2: paquetes funcionales** — P02–P04; ejecutar los comandos existentes desde ambos árboles y comprobar descubrimiento real de skills.
3. **H3: relevo visual completo** — P05–P07; misma persona, mismo directorio y nueva conversación, sin API adicional.
4. **H4: equipo mixto y cobertura** — P08–P09; otra persona y otro clon, más aceptación del resto de funcionalidades.
5. **H5: candidato distribuible** — P10; builds reproducibles y evidencia separada; todavía no publicación.

P05 puede desarrollarse junto con P03/P04 cuando P01/P02 estén cerrados. P08 puede avanzar después de disponer de los adaptadores; no debe esperar a generar imágenes para verificar capacidades independientes. Son dependencias de trabajo, no autorización para lanzar subagentes o escritores simultáneos en el checkout actual.

## 7. Conservación de la funcionalidad actual

La matriz F01–F25 de la propuesta inicial se mantiene como inventario de referencia con esta actualización de F04. La aceptación incluye parsers, opciones, JSON, códigos de salida y garantías, no solo los nombres de comandos.

| Cobertura | Obligación de la primera entrega |
|---|---|
| F01–F03, F05–F08 | Help, definición, adopción, perfiles/variantes y planificación siguen disponibles en ambos destinos |
| F04 | Codex genera directamente; Copilot prepara y recupera un relevo. La imagen y su confirmación tienen el mismo contrato final |
| F09–F12 | Tracking local/Jira, reporting y readiness preservan condiciones, autorizaciones y reconciliación; sin writes remotos por inferencia |
| F13–F17 | Catálogo completo, preparación, ejecución, tareas, continuidad y trazabilidad; colaboración secuencial segura y selección explícita |
| F18–F23 | Verificación por scopes, integración/persistencia reales, capturas, evidencia inmutable, entrega y vista cliente; prototipos no acreditan implementación |
| F24–F25 | Experiencia de usuario, doctor, rendimiento, herramientas de mantenedor, empaquetado y piloto con estados reales |

Se conservan los 23 perfiles del catálogo. Los 17 active requieren certificación exacta vigente; los 6 candidate no se promocionan por aparecer en el paquete Copilot. Si se modifican entradas de `CERTIFICATION_ENGINE_FILES` en `scripts/profile_registry.py`, recertificar los perfiles afectados, sin copiar observaciones anteriores como si fueran nuevas.

## 8. Pruebas de aceptación específicas

Todos estos escenarios están **not-run**. Se registrarán host/extensión/modelo/versiones, producto y digest, proyecto/base, pasos, archivos y resultados. La aceptación visual exige una generación integrada real en Codex, no un PNG de fixture presentado como generado.

| Caso | Escenario | Resultado obligatorio |
|---|---|---|
| V01 | Sesión Codex nativa: proyecto nuevo con brief listo | Generación y aprobación habituales; cero invitaciones, avisos o documentos de relevo |
| V02 | Codex nativo: edición visual material | Editar/generar según el contrato, sin preguntar por Copilot |
| V03 | Codex sin generación disponible, sin permisos o con error | Pendiente explicado; sin API alternativa, aprobación ficticia ni salto circular a Codex |
| V04 | Copilot con brief insuficiente | Completar definición antes de ofrecer el relevo |
| V05 | Copilot con brief listo | Solicitud durable y mensaje concreto para Codex; ninguna llamada a proveedor de imágenes |
| V06 | Repetición de continuar/status/help en Copilot | Sin duplicar solicitud ni avisar en cada turno; help/status no escriben |
| V07 | Codex abre la ficha en un chat nuevo | Recuperar el contexto desde archivos, sin entrevista repetida ni acceso al chat anterior |
| V08 | Generar alternativas, rechazar una, editar otra y aprobar | Historia visual preservada, nueva revisión y decisión humana exacta |
| V09 | Regreso a Copilot con imágenes aprobadas | Validar resultado, actualizar únicamente lo procedente y continuar el método |
| V10 | Regreso con imagen pendiente de selección | No cerrar la definición visual ni asumir aceptación |
| V11 | Usuario permanece en Codex tras el relevo | Continuación normal; no retorno obligatorio ni pausa impuesta |
| V12 | Relevo a otro desarrollador y clon mediante Git | Misma información y archivos accesibles; cuentas personales y ninguna dependencia de rutas del origen |
| V13 | Cambio relevante del brief durante el relevo | Detectar deriva y pedir reconciliación, sin aceptar una imagen de alcance anterior |
| V14 | Solo cambian assets y registros esperados del resultado | Admitir la devolución válida; no rechazarla por cualquier cambio global del árbol |
| V15 | Archivo ausente, corrupto, hash incorrecto o ruta ajena | Rechazar el resultado y conservar historia/pendiente |
| V16 | Aprobación inventada, ADR no confirmada o sin alcance | Rechazo; ninguna transición de readiness o implementación por la mera ficha |
| V17 | Backend, sin impacto visual o baseline reutilizable | Ningún relevo ni generación innecesarios |
| V18 | Varios incrementos/solicitudes, versión o proyecto distinto | Selección explícita y bloqueo de mezcla; no elegir la última solicitud por conveniencia |
| V19 | Cierre de aplicación, operación incompleta o repetición | Recuperación desde archivos, sin duplicar VIS/decisiones ni sobrescribir un resultado |
| V20 | Cambio material posterior a una aprobación | Nueva revisión/relevo; historial preservado y reevaluación de los pasos afectados |
| V21 | Nueva definición sin TASK/EXEC y ejecución ya iniciada | Ficha auxiliar en el primer caso; pausa/reanudación del alcance autorizado en el segundo |
| V22 | Mismo directorio secuencial, ramas distintas y sincronización incompleta | Primera modalidad válida; otras requieren transferencia/reconciliación; nunca dos escritores simultáneos |
| V23 | Instalación, actualización, retirada y dos versiones de producto | Adaptadores/runtime coherentes y cero pérdida de personalizaciones, fichas o imágenes |
| V24 | Verificación visual/funcional en Copilot después del prototipado | Revisar la aplicación real; una imagen generada no acredita código, accesibilidad, integración ni persistencia |

La prueba de equipo incluirá al menos tres desarrolladores, con una persona que trabaje habitualmente con Copilot y otra con Codex. El relevo no exige que todas tengan ambas licencias, pero quien genere imágenes debe disponer de acceso propio a Codex. Debe existir al menos un recorrido completo Copilot→Codex→Copilot y otro que termine permaneciendo en Codex.

Conservar además los casos generales T01–T30 de la propuesta inicial con las siguientes reglas: T18 se sustituye por V01–V24; los escenarios de concurrencia distribuida T10–T12/T20 y conversión de schema T27 se asignan a P11 cuando impliquen el contrato avanzado. No se declaran superados ni se ocultan: quedan explícitamente fuera de la primera entrega secuencial. T13 mantiene sus comprobaciones de concurrencia local y recuperación. El resto se adapta a los dos paquetes y se ejecuta según aplicabilidad documentada.

## 9. Verificación y condiciones de release

Aplicar [VALIDATION.md](../VALIDATION.md): seis skills, estructura del plugin, catálogo, contrato y fixtures; tiers fast/integration/package/profile; evals; benchmark de experiencia y harness de release. Los módulos nuevos deben pertenecer exactamente a un tier. Mantener los presupuestos existentes o someter cualquier cambio medido a revisión explícita.

El paquete Copilot tendrá su propia validación de estructura y recursos. El éxito del validador Codex no la sustituye. Comprobar la invocación natural y explícita en sesiones reales, con la matriz de versiones declarada y políticas corporativas representativas.

Generar plugin/marketplace Codex y paquete Copilot desde el mismo commit limpio; comparar núcleo/instrucciones comunes y reproducir los builds. Sustituir la lista rígida actual de cinco assets por un manifiesto de destinos/evidencias. Extraer y validar los paquetes en un consumidor aislado; no modificar la instalación activa para certificar.

Cierre de H5: sin regresiones Codex; todas las capacidades obligatorias de la primera entrega con evidencia; V01–V24 y pruebas generales aplicables superadas; dependencias externas probadas donde se declare soporte; canales no ejecutados visibles; autorización de release separada. La publicación, commit/tag, push, instalación y activación no son efectos automáticos de completar las pruebas.

## 10. Riesgos y decisiones técnicas pendientes

| Riesgo o pendiente | Resolución prevista |
|---|---|
| Confundir presencia de ambas carpetas de skills con host activo | Adaptador explícito; caso negativo de host desconocido |
| El plugin global y el runtime del proyecto tienen instrucciones distintas | Lock exacto de núcleo y workflow; diagnóstico sin descarga o actualización silenciosa |
| Metadatos nuevos rompen schema 1.5 o huellas | Spike de compatibilidad en P01; schema auxiliar y contrato propuesto antes de writes; no prometer compatibilidad por diseño solamente |
| Una ficha obsoleta consigue cerrar la UX | Releer fuentes y aprobación canónicas; checks de entradas/salidas separados |
| Relevo entre ramas pierde imágenes o decisiones no confirmadas en Git | Inventario y verificación de transferencia; sincronización según política, nunca push automático |
| Dos personas generan o numeran resultados sobre el mismo alcance | Responsable único en primera entrega; coordinación explícita; P11 para concurrencia distribuida |
| El usuario no dispone de Codex o no puede generar en ese momento | Pendiente visible y posibilidad de relevo a otro compañero autorizado; sin contratar API ni reducir exigencias silenciosamente |
| Prometer independencia total de Codex | Documentar que Copilot necesita el paso Codex para generar prototipos nuevos o editarlos |
| Cambios en motor invalidan certificaciones | Recertificación exacta antes de release; no promocionar candidates |

No queda pendiente elegir un proveedor de imágenes para Copilot: esa opción se ha descartado para este alcance. Quedan por cerrar el formato auxiliar, las reglas exactas de compatibilidad/huellas, la versión de release y la matriz real de hosts. P01 es el siguiente trabajo recomendado tras autorizar implementación.

## 11. Evidencia de elaboración del plan

Se han revisado el contrato visual vigente, la skill de definición, el dispatcher, validación de imágenes, readiness, huellas de verificación, inventario de suites, manifiesto y propuesta anterior. La normativa visual ya exige PNG/JPEG comprobables, procedencia ImageGen y aprobación humana; no hay que sustituirla por una promesa de generación nativa en Copilot.

Esta entrega solo modifica documentación de planificación. Comprobaciones ejecutadas sobre el producto existente y los dos documentos:

| Comprobación | Resultado | Límite |
|---|---|---|
| `quick_validate.py` sobre las seis skills | Seis válidas | No acredita su ejecución en Copilot |
| `validate_plugin.py .` | Correcta | Estructura de la distribución Codex actual |
| `validate_reference_profile.py --all --allow-unvalidated` | 23 perfiles estructuralmente válidos | No recertifica ni promociona perfiles |
| `validate_plugin_contract.py .` | Contrato 1.0.0 válido, M0–M5 y evolución schema 1.5 | No valida un contrato de relevo todavía no implementado |
| `validate_fixture_manifest.py .` | Correcta; 14 fixtures | No equivale a ejecutar los fixtures |
| Enlaces relativos de propuesta y plan | 21 enlaces, ninguno roto | Comprobación de existencia |
| Revisión documental y whitespace | 11 paquetes, 24 escenarios; sin errores de espacios finales; fuentes canónicas sin cambios | No acredita funcionalidades nuevas |

No se han repetido suites funcionales, harness ni certificaciones de release en esta entrega documental. Las pruebas V01–V24, la compatibilidad de host y la release dual siguen `not-run`. Estas comprobaciones no son evidencia de implementación ni de aceptación del nuevo flujo; los resultados anteriores del baseline permanecen identificados en la propuesta inicial.
