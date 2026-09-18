# Plan de implementación: consulta humana del proyecto

Fecha: 2026-09-17. Estado: **implementación local con verificación automatizada; distribución con fallo previo; aceptación humana pendiente**.

Este documento planifica una mejora del runtime y de las seis skills de LKS-SDD.
No es un PLAN/TASK canónico de un proyecto consumidor, no inicia una adopción y
no concede AUTH ni autorización de publicación. Los identificadores QREQ, Q y
QC son locales a este plan y no se materializarán como requisitos o tareas del
consumidor. Tras la entrega del plan, el usuario autorizó su implementación con
«implementalo». Esa autorización no incluye publicación, instalación activa ni
aceptación humana. El apartado 10 conserva la entrega documental original.

## 1. Resultado esperado y alcance confirmado

Un usuario podrá consultar requisitos, especificaciones, decisiones, tareas y
otra información del proyecto y recibir una explicación integrada, profesional,
neutra y comprensible, con enlaces a sus fuentes. La respuesta usará texto,
tablas, listas o diagramas según lo que ayude a comprender el asunto.

La documentación será la fuente principal. El código se consultará cuando sea
insuficiente para responder una cuestión sobre la implementación o cuando el
usuario lo solicite expresamente. Lo observado nunca se convertirá por inferencia
en un requisito aprobado. Los proyectos veteranos con documentación SDD parcial
forman parte de la primera entrega.

**Regla de producto:** explicar lo documentado, complementar cuando proceda con
lo observado, hacer visibles diferencias y límites, sin modificar el proyecto.

### Límites obligatorios

- No escribir documentación canónica, código, índice, estado, TASK, AUTH, EXEC,
  CKPT, EVID, locks, decisiones, incidencias ni huellas del consumidor.
- No ejecutar aplicación, tests, builds, contenedores, hooks o gestores de
  paquetes durante una consulta. Leer pruebas o evidencia existente no es ejecutarlas.
- No iniciar definición, adopción, reconciliación, migración, normalización,
  implementación ni documentación automática como efecto de una pregunta.
- No crear una séptima skill, MCP, conectores, hooks, apps, agentes ejecutables,
  servicio en segundo plano, API de modelos ni nueva dependencia de pago.
- No dar por inexistente una funcionalidad porque no esté documentada; no dar
  por pendiente una implementación porque no tenga una TASK registrada.
- No acceder a otros repositorios, submódulos, Jira, bases de datos, servicios
  remotos o producción sin delimitar y autorizar ese alcance por separado.
- No tocar `specs/canonical/` ni debilitar gates de implementación para facilitar
  una consulta. Leer parcialmente no equivale a declarar válido un contrato.
- No crear commits, tags, push, publicación, instalación o activación con este plan.

### Fuera de la primera entrega

Visor web, documentación narrativa persistida, exportaciones, indexación remota,
base vectorial, búsqueda en sistemas externos, diagnóstico en ejecución y
reconciliación automática. PDF, Word o imágenes enlazadas se identificarán como
fuentes no leídas si requieren un extractor no incluido; no se fingirá su contenido.
La extracción primaria cubre Markdown y texto local legible, más metadatos
estructurados que ya utiliza el plugin. El formato de respuesta visual no exige
generar imágenes: un diagrama sencillo debe poder proceder de relaciones trazadas.

## 2. Base revisada y compatibilidad

Hechos comprobados al elaborar el plan:

- [contract_engine.py](../../scripts/contract_engine.py) dispone de filas,
  relaciones, estados, archivos, líneas y hashes. Su selección activa por
  incremento no basta por sí sola para una consulta temática o de TASK.
- [planning_engine.py](../../scripts/planning_engine.py) distingue propiedad y
  contribución. No se usará únicamente la tarea propietaria para recuperar contexto.
- [experience_engine.py](../../scripts/experience_engine.py) ofrece vistas de
  progreso; no sustituye una consulta integrada de requisitos y especificación.
- [inspect_repository.py](../../skills/lks-sdd-adopt-existing/scripts/inspect_repository.py)
  y sus utilidades contienen límites de lectura estática aprovechables. Un
  inventario de archivos no prueba comportamiento ni intención de negocio.
- [render_client_view.py](../../scripts/render_client_view.py) produce una vista
  derivada mediante escritura autorizada; no será el camino de esta consulta.
- El [estudio de contexto](../proposals/context-compiler-study-2026-09-11/review.md)
  conserva contraejemplos de omisiones, raíces históricas e inflación de contexto.
  Se reutilizarán sus lecciones y casos, no se promoverá su selector experimental.
- El workspace contiene cambios previos de variantes tecnológicas. Se preservan;
  no se considerarán parte implementada de este plan ni se sobrescribirán.

La ampliación se diseñará como módulos auxiliares de lectura. Se reutilizarán
interfaces existentes antes de cambiar motores compartidos. Si una modificación
alcanza `CERTIFICATION_ENGINE_FILES`, se declarará su impacto y la recertificación
necesaria; no se cambiará el registro para evitarla. El schema consumidor seguirá
intacto salvo una decisión posterior explícita, no prevista para este MVP.

La evidencia previa de [variantes](../validation/project-variants-2026-09-17.md)
registra un fallo de longitud de rutas en Copilot y un skip de symlink en Windows.
Son antecedentes, no resultados nuevos de este plan. Q10 comprobará su estado:
una distribución con ese fallo no podrá presentarse como validada. Resolverlo,
si exige cambios ajenos, necesitará un alcance separado y explícito.

## 3. Requisitos y cobertura

Los requisitos siguientes recogen las necesidades de la conversación; las
decisiones de arquitectura y nombres de módulos posteriores son propuestas.

| ID | Requisito de la primera entrega | Responsable primario | Comprobaciones |
|---|---|---|---|
| QREQ-01 | Cero cambios en archivos o estado del consumidor durante la consulta | Q02 | QC-14, QC-15, QC-22, QC-28 |
| QREQ-02 | Documentación como fuente principal; no leer código si resulta suficiente | Q04 | QC-01, QC-03, QC-05 |
| QREQ-03 | Ampliación selectiva al código por carencia concreta o petición expresa | Q05 | QC-02, QC-04, QC-05, QC-19 |
| QREQ-04 | Consultar proyectos veteranos con SDD parcial o fuentes sin IDs | Q03 | QC-06, QC-07, QC-20, QC-21 |
| QREQ-05 | Separar acuerdo, propuesta, observación, inferencia e información desconocida | Q06 | QC-04, QC-08, QC-10, QC-18 |
| QREQ-06 | Relacionar requisitos, especificación, tareas, decisiones, aceptación y evidencia | Q03 | QC-09, QC-12, QC-17, QC-18 |
| QREQ-07 | Conservar reglas fuera de tablas, excepciones y restricciones transversales | Q03 | QC-09, QC-10, QC-29 |
| QREQ-08 | Explicación profesional, neutra, clara y completa para el alcance preguntado | Q06 | QC-24, QC-25, QC-29, QC-32 |
| QREQ-09 | Elegir texto, lista, tabla o diagrama sin inventar relaciones ni imponer secciones vacías | Q06 | QC-24, QC-25 |
| QREQ-10 | Enlaces comprobables a las fuentes concretas y su versión revisada | Q02 | QC-11, QC-23, QC-25, QC-31 |
| QREQ-11 | Exponer contradicciones, cobertura parcial y límites sin resolverlos silenciosamente | Q04 | QC-08, QC-10, QC-13, QC-19, QC-21 |
| QREQ-12 | Consulta acotada y ágil, sin comprobaciones de ejecución ni lecturas redundantes | Q09 | QC-01, QC-13, QC-14, QC-26, QC-30 |
| QREQ-13 | Invocación natural a través de las skills existentes y CLI reproducible | Q08 | QC-27, QC-28, QC-32 |
| QREQ-14 | Proteger secretos, permisos, rutas, repositorio fijado e instrucciones del sistema | Q02 | QC-15, QC-16, QC-22, QC-28 |
| QREQ-15 | Preservar modo estricto, evidencia histórica y flujos actuales, incluidas variantes | Q10 | QC-27, QC-28, QC-30 |
| QREQ-16 | No tratar una consulta ni sus resultados como autorización para actuar | Q07 | QC-03, QC-14, QC-20, QC-27 |

Roles propuestos: mantenimiento del runtime, mantenimiento de skills, QA y
responsable de producto. La asignación de personas sigue pendiente. No se
inventan esfuerzo, fechas de entrega, capacidad ni un camino crítico temporal.

## 4. Contrato funcional propuesto

### 4.1 Modos y suficiencia

| Modo | Comportamiento | Uso del código |
|---|---|---|
| `docs-first` (predeterminado) | Interpretar pregunta, recuperar documentos, ampliar relaciones y evaluar carencias | Solo para preguntas concretas que lo requieran tras esa lectura |
| `docs-only` | Responder exclusivamente desde documentos y evidencia documental existente | Prohibido; la respuesta puede ser parcial |
| `compare` | Relacionar lo especificado con la implementación del alcance solicitado | Expreso, selectivo y estático |

«Qué debe hacerse» no se resolverá leyendo código cuando falte una decisión de
negocio. Podrá explicarse separadamente qué está implementado, pero el acuerdo
seguirá sin determinar. «Qué hace el código» activa una inspección expresa, con
documentación de contexto. «Qué hace producción» no se confirmará por una rama local.

La suficiencia se evaluará para las dimensiones necesarias de la pregunta:
comportamiento, reglas/excepciones, alcance, relaciones, tareas, aceptación o
estado. Solo se exigen las pertinentes, con motivos para las restantes. Una
carencia debe describir qué no puede responderse y qué fuente podría resolverlo.

El motor comprobará fuentes, modo y alcance; el asistente realizará el juicio
semántico. Un número de documentos, un grafo conectado o la ausencia de errores
de schema no certificarán suficiencia. Los límites técnicos y semánticos se
informarán por separado. La falta de confianza no se ocultará con una puntuación.

Estados del resultado propuestos: `answered`, `partial`, `needs-clarification`,
`blocked`. Describen la consulta, nunca readiness, aprobación ni estado de TASK.
Errores locales permiten explicar el resto sin aceptar IDs ambiguos. Una raíz
insegura, runtime alterado o falta de permiso bloquea la lectura afectada.

### 4.2 Flujo de lectura

1. Identificar asunto y alcance, respetando una selección explícita de documento,
   entidad, TASK o versión. Preguntar solo ante ambigüedad material, agrupando opciones.
2. Leer documentación SDD y fuentes documentales locales identificadas en el alcance.
   Las fuentes previas a SDD conservan su procedencia y autoridad conocida o desconocida.
3. Recuperar relaciones explícitas en ambos sentidos, prosa, reglas compartidas,
   tareas contribuyentes y decisiones. Usar coincidencias textuales como candidatos,
   no como relaciones confirmadas. No asumir que «sin enlace» significa «irrelevante».
4. Evaluar carencias concretas. Si procede, anunciar una sola vez qué se buscará
   en código y por qué; inspeccionar únicamente puntos pertinentes y sus dependencias.
5. Componer una respuesta con orígenes diferenciados, vínculos reales y límites.
6. Revalidar identidad de las fuentes utilizadas antes de entregar; ante cambios
   concurrentes, refrescar de forma acotada o declarar la respuesta parcial.

No se recorre todo un subsistema por compartir un prefijo. Los límites de lectura,
profundidad y tamaño son visibles; alcanzarlos no permite declarar completitud.
Una consulta parcial no requiere cerrar especificaciones ni materializar adopción.

### 4.3 Resultado estructurado y presentación

Propuesta de schema auxiliar `query-context` 1.0, sin cambios en `project.json`:

- Solicitud: tema/selector, intención, modo, raíces y alcance, versión seleccionada.
- Fuentes: ruta relativa segura, título, sección/líneas, hash, tipo, autoridad y
  vigencia conocidas; revisión Git y cambios locales cuando estén disponibles.
- Fragmentos: contenido literal necesario, fuente, naturaleza y estado; conservar
  tipos, negaciones, límites, excepciones y precedencias, no solo títulos o IDs.
- Relaciones: origen, destino, clase, procedencia y justificación de inclusión;
  separar relación declarada, relación observada en código e interpretación.
- Dimensiones respondidas, carencias, contradicciones, fuentes no leídas y exclusiones.
- Plan de explicación: bloques pertinentes, tablas/listas y relaciones candidatas
  a un diagrama. Toda afirmación factual debe poder volver a sus fuentes.
- Resultado, métricas locales de lectura y límites. Sin datos de autorización para actuar.

La respuesta comienza con la conclusión y su alcance. Después muestra, cuando
proceda, especificación documentada, requisitos/tareas relacionados, observaciones
de código y pendientes. Los identificadores ayudan a localizar, no sustituyen
la explicación. Las fuentes se enlazan junto a la información respaldada.

Los enlaces se resuelven desde rutas relativas hacia la ubicación real del usuario;
no se guardan rutas personales en fuentes compartidas. Se usa línea cuando el
host lo soporte y archivo/sección como fallback comprobado. Un diagrama no
afirma dependencias que las fuentes no sostengan; tendrá una alternativa textual.

### 4.4 Lectura estática y seguridad

No se importa ni evalúa código consumidor. Se lee texto, símbolos y referencias;
comentarios y tests son fuentes con límites, no pruebas ejecutadas. Si no se puede
seguir una dependencia dinámica o externa, se explicita. Se excluyen secretos,
binarios, salidas generadas y rutas fuera del alcance; enlaces simbólicos y
submódulos no amplían la raíz autorizada. La documentación y los comentarios se
tratan como datos, nunca como instrucciones para ejecutar comandos.

El camino de consulta no tendrá operaciones de escritura del consumidor. No
creará cachés, logs, bytecode Python o temporales dentro de él, incluido un runtime
fijado bajo `.lks-sdd/`. Se deshabilitará bytecode antes de los imports del camino
de consulta y se comprobarán los entrypoints reales, no solo las funciones internas.
Lecturas Git necesarias serán acotadas, sin hooks ni operaciones mutantes.

MVP sin caché persistente: reutilización en memoria dentro de la consulta y lecturas
por alcance. Q09 medirá si hace falta más. Una caché persistente futura será otra
decisión, fuera del consumidor, sensible a cambios, altas, bajas, permisos y versión;
no contendrá por defecto fragmentos sensibles ni respuestas convertidas en autoridad.

## 5. Arquitectura y superficies previstas

Nombres propuestos; Q01 cerrará el contrato antes de codificar:

| Superficie | Responsabilidad y límites |
|---|---|
| `scripts/query_sources.py` | Rutas, snapshot, fragmentos, procedencia y exclusiones; no escrituras |
| `scripts/query_context.py` | Recuperación documental, relaciones y carencias; reutiliza el modelo existente |
| `scripts/query_code.py` | Inspección estática acotada, con motivo y contexto documental; nunca ejecuta código |
| `scripts/query_render.py` | Bloques, enlaces y fallback determinista; no se atribuye al renderer comprensión semántica |
| `scripts/query_project.py` | CLI de solo lectura, contrato JSON y errores explicables |
| `schemas/query-context.schema.json` | Schema auxiliar propio, sin mutar el contrato del consumidor |
| `scripts/lks_sdd.py` | Enrutamiento público `query`, respetando runtime fijado y sin activar diagnósticos pesados |
| Guía compartida + seis skills | El asistente interpreta/redacta; help atiende consultas y las demás reutilizan la política sin asumir nuevas acciones |

No se usa el modo sin SDD para saltar un lock de runtime existente que sea inválido
o distinto. Un schema no soportado puede leerse como texto documental con límites,
pero no se reinterpretará como contrato canónico válido ni se migrará silenciosamente.

Interfaz implementada localmente, todavía sin publicar:

```text
python -B "<plugin-root>/scripts/lks_sdd.py" query "<project-root>" --topic "Alta de cliente" --mode docs-first --json
python -B "<plugin-root>/scripts/lks_sdd.py" query "<project-root>" --entity TASK-001 --mode docs-only --json
python -B "<plugin-root>/scripts/lks_sdd.py" query "<project-root>" --entity FR-001 --mode compare --code-path src/clientes --json
```

El comando retorna contexto verificable; no promete comprender lenguaje natural
por sí solo. La skill transforma la pregunta en selectores y redacta con las
fuentes devueltas, sin otro proveedor de IA. La ampliación a código en docs-first
debe portar una carencia explícita y la identidad del contexto documental; no
será un flag que permita saltarse su lectura. El diseño preciso se prueba en Q04/Q07.

## 6. Secuencia, dependencias y tareas

La tabla conserva la secuencia aprobada. Q01–Q08 tienen implementación local;
Q09 tiene evidencia automatizada; Q10 mantiene el fallo previo de distribución
y Q11 sigue pendiente de aceptación humana. El cierre detallado está en el apartado 11.
No se delega ni lanza trabajo paralelo por este documento; las dependencias describen
el orden técnico, no una atribución de evidencia humana.

| Fase | Tarea | Entregable principal | Dependencias |
|---|---|---|---|
| 1. Contrato y seguridad | Q01 | Contrato de consulta, ejemplos y corpus de aceptación | Ninguna |
| 1. Contrato y seguridad | Q02 | Lector seguro, snapshot y fuentes enlazables | Q01 |
| 2. Consulta documental | Q03 | Recuperación integrada de tablas, prosa y relaciones | Q02 |
| 2. Consulta documental | Q04 | Modos y evaluación explícita de carencias | Q01, Q03 |
| 3. Complemento y respuesta | Q05 | Inspección selectiva del código | Q02, Q04 |
| 3. Complemento y respuesta | Q06 | Respuesta estructurada, procedencia y presentación | Q03, Q04, Q05 |
| 4. Integración | Q07 | CLI y dispatcher de solo lectura | Q02, Q04, Q05, Q06 |
| 4. Integración | Q08 | Política compartida en las seis skills | Q06, Q07 |
| 5. Verificación y entrega | Q09 | Campaña adversarial y medidas de agilidad | Q07, Q08 |
| 5. Verificación y entrega | Q10 | Regresión y paquetes coherentes | Q09 |
| 5. Verificación y entrega | Q11 | Aceptación humana en hosts y cierre trazable | Q10 |

Las pruebas de cada módulo se crean junto con él; Q09 es integración y ampliación,
no el comienzo de las pruebas. Sin duraciones, esta tabla no es un camino crítico.

### Q01 — Contrato, límites y ejemplos de aceptación

- Objetivo: convertir esta propuesta en contratos comprobables antes de programar.
- Entrega: contrato auxiliar, criterios por intención, ejemplos con fuentes y
  oráculos de hechos obligatorios/prohibidos; clasificación de compatibilidad.
- Casos de referencia: documentación suficiente, mantenimiento parcial, funcionalidad
  histórica sin especificación, conflicto documento/código y petición normativa sin acuerdo.
- Incluir una respuesta tabular, una lista de reglas y un diagrama con alternativa textual.
- Rol propuesto: mantenimiento del producto; revisión por QA y usuario/desarrollador.
- Termina cuando no hay una decisión crítica implícita sobre lectura/escritura,
  fallback al código, soporte legado o identidad de fuentes. La selección de
  wording no se convierte en un gate por cada frase; se valida la política y ejemplos juntos.

### Q02 — Lectura segura y procedencia

- Objetivo: un único camino de lectura acotado con fuentes estables y verificables.
- Entrega: `query_sources`, contratos de fragmento, snapshots y generador de referencias.
- Incluir archivos con espacios/Unicode, líneas reales, fuentes mixtas y repo sin Git.
- Excluir secretos, escapes, symlinks/junctions y submódulos no autorizados; resistir
  cambios concurrentes y documentos con instrucciones maliciosas.
- Rol propuesto: mantenimiento del runtime; revisión de seguridad y QA.
- Termina con QC-11, QC-14..16, QC-22..23 y QC-31 en funciones y launcher;
  comparación de bytes/rutas antes/después en fixtures instrumentadas. El snapshot
  de prueba completo no obliga a hashear todo el repo en cada consulta de usuario.

### Q03 — Contexto documental integrado

- Objetivo: responder desde la documentación sin exigir cobertura total ni IDs perfectos.
- Entrega: recuperación de entidades, prosa y relaciones; explicación de inclusiones,
  fuentes históricas y exclusiones; soporte de documentos locales previos a SDD.
- Incluir requisitos, reglas transversales, ADR, tareas principales y contribuyentes,
  criterios, tests y evidencia; no confundir historia ejecutada con salud actual.
- Reutilizar `ProjectModel` cuando sea aplicable; fallback textual limitado ante
  fuentes parciales, sin declarar válido un contrato que el validador rechaza.
- Rol propuesto: mantenimiento del runtime; revisión funcional por QA.
- Termina con QC-06..10, QC-12, QC-17..18, QC-20..21 y QC-29; ninguna obligación
  crítica del corpus puede desaparecer por estar en prosa o sin enlace explícito.

### Q04 — Política documental y decisión de ampliación

- Objetivo: usar código solo cuando la intención y las carencias lo justifican.
- Entrega: modos, dimensiones de suficiencia, motivos de ampliación y resultados parciales.
- Impedir que una decisión de negocio ausente se complete con código. No inferir
  necesidad de adopción, documentación integral o nueva TASK a partir de un vacío.
- Definir límite/continuación de búsqueda y una aclaración agrupada solo si cambia el alcance.
- Rol propuesto: mantenimiento del runtime y skills; revisión de producto.
- Termina con QC-01..08, QC-13, QC-19..21; docs suficientes y docs-only producen
  cero lecturas de contenido de implementación, comprobadas por instrumentación.

### Q05 — Observación selectiva de implementación

- Objetivo: localizar comportamiento no documentado sin ejecutar ni homologar código.
- Entrega: búsquedas acotadas de símbolos/rutas, fragmentos y dependencias relevantes,
  lectura de pruebas existentes y límites de configuraciones dinámicas/externas.
- Separar implementación observada, inferencia y evidencia de ejecución preexistente.
  Registrar revisión efectiva y cambios locales; no extrapolar a producción.
- Probar familias heterogéneas de código (Python, JS/TS y Java/SQL) sin prometer
  análisis semántico completo por lenguaje. Donde no alcance, devolver límites explícitos.
- Rol propuesto: mantenimiento del runtime; revisión técnica y QA.
- Termina con QC-02, QC-04..08, QC-14..16, QC-19, QC-22 y QC-26; se ve el motivo
  de cada ampliación y ninguna lectura amplía por sí sola la raíz autorizada.

### Q06 — Explicación, formatos y enlaces

- Objetivo: transformar el contexto en una respuesta útil sin alterar su significado.
- Entrega: bloques estructurados, render de referencia y reglas compartidas de redacción.
- Resumen claro primero; detalles necesarios, excepciones y fuentes a continuación;
  sin cuotas arbitrarias de palabras ni volcado obligatorio de todos los apartados.
- Tablas para correspondencias/comparaciones, listas para condiciones/pasos,
  diagramas para relaciones complejas justificadas; sin decoración obligatoria.
- Rol propuesto: mantenimiento de skills/runtime; revisión por desarrollador y producto.
- Termina con QC-08, QC-10..11, QC-18..19 y QC-23..25/29. Validar citas y
  cobertura automáticamente, fidelidad y comprensión con evaluación humana separada.

### Q07 — CLI pública e integración del runtime

- Objetivo: ofrecer una ruta reproducible sin alterar comandos o flujos actuales.
- Entrega: `query_project`, dispatcher, ayuda CLI, JSON válido y semántica de errores.
- Mantener runtime fijado, raíz segura, operación desde carpeta del consumidor y
  cero archivos auxiliares; planificar bien bytecode y dependencias importadas.
- No conectar con `materialize_adoption`, confirmación de planning, transición de
  TASK o escritura de evidencia; el resultado no otorga autoridad.
- Rol propuesto: mantenimiento del runtime; revisión de regresión.
- Termina con QC-01, QC-03, QC-14..16, QC-20..22 y QC-27..28; resultados parciales
  utilizables sin que eso rebaje la validación de implementación.

### Q08 — Comportamiento de las seis skills

- Objetivo: que una pregunta natural active la experiencia sin enseñar comandos al usuario.
- Entrega: una guía compartida y cambios mínimos, específicos y no solapados en
  help, define, adopt-existing, assess-readiness, implement y verify.
- Help mantiene la consulta de solo lectura. Las otras skills reutilizan la
  presentación y consulta pertinente, sin ampliar autorizaciones ni lanzarla en cada gate.
- Revisar frases de activación positiva/negativa, documentación de modos y diferencias
  entre explicación, propuesta de cambio y acción. Usar skill-creator al editar skills.
- Rol propuesto: mantenimiento de skills; revisión funcional.
- Termina con QC-03, QC-14, QC-24..28 y QC-32, quick validators y contrato del plugin.
  La validación estructural no acredita activación conversacional en ambos hosts.

### Q09 — Pruebas adversariales, suficiencia y agilidad

- Objetivo: buscar omisiones y falsas certezas, no solo respuestas bien formateadas.
- Entrega: campaña QC, métricas separadas de recuperación, redacción y ejecución
  operativa; resultados positivos/negativos conservados y fixtures reproducibles.
- Comparar lectura de referencia completa para el alcance con consulta selectiva,
  utilizando las mismas obligaciones esperadas; no igualar IDs cubiertos a fidelidad.
- Medir frío/repetición, archivos listados/leídos, bytes, ampliaciones y preguntas.
  Contar lecturas y expansión del asistente, no solo el JSON final.
- Rol propuesto: QA con revisión de mantenimiento y producto.
- Termina con todos los QC automatizables aplicables ejecutados, sin omisiones
  críticas del corpus, y límites de generalización/humanos visibles. No reajustar
  umbrales o eliminar casos únicamente para obtener verde.

### Q10 — Compatibilidad y distribución

- Objetivo: integrar sin romper variantes, modo estricto, locks ni consumidores existentes.
- Entrega: inventario de módulos en tiers/impact map, validaciones estructurales,
  regresiones y comprobación de módulos/recursos en los paquetes de ambos hosts.
- Revisar rutas Windows, reproducibilidad y uso desde runtime fijado. Separar el
  fallo previo de Copilot de regresiones nuevas; no borrar estudios para ocultarlo.
- Rol propuesto: mantenimiento del producto; revisión QA.
- Termina con validaciones aplicables de [VALIDATION.md](../VALIDATION.md), diff
  revisado y clasificación de cambios de motor. El harness de release, builds de
  release y commit limpio requieren la autorización y condiciones propias de release.
  Si faltan, la salida es validación de desarrollo, no una release acreditada.

### Q11 — Aceptación humana y cierre

- Objetivo: comprobar comprensión y navegación real, no solo formato JSON.
- Entrega: muestra de consultas evaluada en Codex y Copilot, incidencias y decisión
  de aceptación del alcance. Priorizar proyecto nuevo, legado parcial y conflicto.
- Comprobar apertura de enlaces, fallback de sección y diagramas en cada host.
  Usar entorno aislado autorizado; no actualizar instalaciones activas silenciosamente.
- Rol propuesto: responsable de producto y desarrollador usuario; asignación pendiente.
- Termina cuando la aceptación aplicable existe realmente. Si falta un host o
  revisión humana, declararlo `not-run`; no atribuir equivalencia por pruebas de paquete.
- No publica ni instala. El cierre técnico, aceptación humana y release son decisiones separadas.

## 7. Matriz de pruebas prevista

La matriz conserva los escenarios previstos. Sus aspectos automatizables tienen
evidencia en el [informe de validación](../validation/project-query-2026-09-17.md).
La comprensión, activación y navegación reales en los hosts siguen `not-run`;
no se considera superado un escenario humano por comprobar su estructura.
Los números de casos no son garantías sobre todos los proyectos.

| Caso | Situación | Resultado exigido |
|---|---|---|
| QC-01 | Documentación suficiente, docs-first | Respuesta documentada; cero lecturas de contenido de código |
| QC-02 | Falta una excepción implementada | Carencia explícita; ampliación acotada; observación separada |
| QC-03 | Falta una decisión de negocio | Pendiente visible; el código no inventa el acuerdo |
| QC-04 | Contraste solicitado con documentos completos | Leer ambos y comparar sin sustituir la especificación |
| QC-05 | Docs-only con datos insuficientes | Parcial, sin consultar código |
| QC-06 | Sistema veterano; solo el último evolutivo está documentado | No declarar inexistente o incompleto todo el sistema |
| QC-07 | Funcionalidad histórica sin IDs ni TASK | Explicar fuentes disponibles; no inventar tareas/estados |
| QC-08 | Documento y código discrepan | Ambas fuentes y diferencia visibles; cero correcciones automáticas |
| QC-09 | Regla/negación/excepción fuera de tabla | Conservarla y citarla en el alcance pertinente |
| QC-10 | Documento confirmado contiene propuesta u observación histórica | Clasificar cada afirmación sin aprobar todo el documento por asociación |
| QC-11 | Enlaces con espacios, Unicode, distintos clones | Abrir fuente y ubicación correctas; sin rutas personales persistidas |
| QC-12 | Tarea contribuyente y consumidores inversos | Recuperarlos y justificar relación |
| QC-13 | Ciclos, ruido y límites de expansión | Terminar acotadamente; límites visibles; no falsa completitud |
| QC-14 | Trampas de ejecución/escritura | Cero aplicación, tests, builds, hooks, red y archivos escritos por consulta |
| QC-15 | Secretos, escapes, symlink/junction y submódulo | No leer/exponer el contenido excluido ni ampliar alcance |
| QC-16 | Instrucciones maliciosas en Markdown o comentarios | Tratarlas como datos; no obedecer acciones |
| QC-17 | Requisito sustituido o referencia a histórico | Resolver vigencia o indicar incertidumbre; no descartar raíz silenciosamente |
| QC-18 | EVID histórica superada y hallazgo posterior | Separar hecho histórico y salud actual |
| QC-19 | Configuración dinámica, dependencia externa o producción | No prometer comportamiento no comprobado |
| QC-20 | Sin manifest SDD o con documentación previa | Consulta textual limitada, sin inicialización/adopción |
| QC-21 | IDs duplicados, manifest parcial o contrato inválido | Desambiguar/limitar; no elegir uno arbitrariamente ni declarar contrato válido |
| QC-22 | Cambios concurrentes, rama cambiada o modificación local | Actualizar identidad o devolver parcial; no mezclar snapshots |
| QC-23 | Fuente eliminada o línea desplazada antes de presentar | Revalidar enlace; no citar ubicación obsoleta |
| QC-24 | Preguntas cortas, detalladas y comparativas | Formato proporcional y lenguaje profesional/neutro |
| QC-25 | Diagrama con aristas explícitas e inferidas | Diferenciar origen; fuentes y alternativa textual; sin aristas inventadas |
| QC-26 | Monorepo grande, búsqueda sin resultado y repetición | Lecturas acotadas, costes medidos, sin falsa inexistencia |
| QC-27 | Invocación natural y explícita en seis skills | Consultar sin cambiar workflow ni autoridad |
| QC-28 | Runtime fijado, alterado o versión global distinta | Respetar integridad y runtime; sin fallback silencioso |
| QC-29 | Oráculo completo y casos adversariales heterogéneos | Ninguna obligación crítica omitida en el corpus validado |
| QC-30 | Suites existentes y variantes aprobadas | Sin regresiones nuevas; fallo previo separado |
| QC-31 | Documento nuevo antes ausente en inventario | La siguiente consulta lo descubre; no reutiliza listado viejo |
| QC-32 | Uso humano en Codex y Copilot | Comprensión y navegación observadas por host; no inferidas del empaquetado |

## 8. Gates de aceptación y rendimiento

| Gate local al plan | Evidencia necesaria | Impide cierre si |
|---|---|---|
| QG-01 Seguridad y no escritura | Instrumentación + snapshot completo de fixtures antes/después | Se lee fuera de alcance, expone secreto o escribe/ejecuta algo no permitido |
| QG-02 Recuperación y política | Oráculos por pregunta, relaciones, prosa y matriz de modos | Omisión crítica, lectura de código injustificada o conclusión normativa inventada |
| QG-03 Fuentes y presentación | Resolución de citas, estados, versiones, revisión de respuestas | Fuente errónea, contradicción oculta o diagrama engañoso |
| QG-04 Agilidad y compatibilidad | Benchmark local + suites y validadores del plugin | Regresión nueva o límites recortados silenciosamente |
| QG-05 Aceptación de uso | Sesiones humanas y enlaces comprobados por host | Se pretende declarar un host/canal superado sin ejecución real |

### Medición propuesta para Q01/Q09

- Fixtures pequeña/media/grande con tamaños publicados, además de legado con mucho
  código y poca especificación. Objetivos iniciales para el motor local: p95 de
  recuperación documental <= 2 s en 100 archivos/2 MiB de texto y <= 5 s en
  1.000 archivos/20 MiB, en runner y versión Python registrados. Son objetivos
  propuestos, no medidas actuales ni promesas de latencia del modelo.
- Medir al menos 20 consultas representativas por tamaño, separando arranque frío,
  repetición en sesión y ampliación a código. Publicar mediana, p95, máximos y límites.
- Medir aparte tiempo total de respuesta del asistente y número de ampliaciones.
  No afirmar ahorro de coste/tokens facturados a partir de bytes de contexto.
- Docs suficientes/docs-only: cero lecturas de implementación. Todos los modos:
  cero ejecuciones del consumidor y cero escrituras. Repetición sin cambio en una
  sesión: reutilizar lecturas compatibles sin omitir descubrimiento de fuentes nuevas.
- Mantener los presupuestos de [performance-policy.json](../../quality/performance-policy.json).
  Si un objetivo propuesto no se alcanza, optimizar o revisar explícitamente el
  objetivo con evidencia; no cambiar límites para dar por pasada una prueba.

Se comprueba la corrección antes que la reducción de contexto. La revisión humana
valora comprensión y fidelidad; no se sustituye por una comparación literal de textos.

## 9. Validación, entrega y decisiones pendientes

Durante implementación: tests localizados por tarea, un tier por módulo, evals
con casos congelados y contraejemplos añadidos sin reescribir resultados anteriores.
Al integrar: puerta de estructura y contrato de [VALIDATION.md](../VALIDATION.md),
CLI pública, flujos de estado/planificación/implementación/verificación, variantes,
paquetes y benchmark. Antes de release: harness integral y autorización de release
propios, desde checkout limpio; no repetirlo automáticamente en cada consulta.

| Decisión pendiente | Recomendación del plan | Momento |
|---|---|---|
| Autorizar la implementación | Resuelto: el usuario indicó «implementalo»; se mantienen los límites del plan | 2026-09-17 |
| Contrato de CLI, límites de lectura y umbrales finales | Resuelto en la guía y schema auxiliares; límites visibles y objetivos 2 s/5 s conservados | Q01/Q09 |
| Ejemplos y rúbrica de respuesta humana | Validar un lote representativo, no pedir aprobación por cada formato | Q01 y aceptación Q11 |
| Personas/revisores y disponibilidad de hosts | Asignar roles reales; conservar no ejecutado lo que no pueda probarse | Antes de Q11 |
| Versión y destino de release | Decidir tras impacto/compatibilidad; no inferir versión o publicación | Antes de preparar release |
| Fallo previo de rutas Copilot | Confirmado: 125 > 110; corrección separada pendiente, sin declarar distribución válida | Q10, antes de declarar distribución válida |

Estas decisiones no impiden redactar el plan ni requieren inicializar un proyecto
consumidor. Tampoco se convierten en aprobaciones por ausencia de respuesta.

### Definición de terminado

La implementación técnica estará terminada cuando Q01–Q10 tengan entregables y
evidencia aplicable, se cubran QREQ-01..16 y no haya fallos críticos nuevos sin
resolver. La aceptación de producto exige además Q11; una limitación de host se
declara, no se disimula. Publicación, instalación y activación quedan fuera de
esta definición y requieren autorizaciones separadas.

El cierre incluirá cambios realizados, pruebas ejecutadas y no ejecutadas,
resultados de rendimiento, límites conocidos, estado de ambos hosts y siguiente
acción segura. Los documentos y pruebas previstos en este plan no se consideran
creados ni superados por figurar aquí.

## 10. Entrega documental original (anterior a la implementación)

Esta entrega añade únicamente este archivo. No implementa la consulta, modifica
skills, actualiza el runtime ni registra aprobaciones. Se revisan integridad de
referencias, cobertura QREQ/Q/QC, dependencias sin ciclos y preservación de los
cambios anteriores. La ejecución de la funcionalidad propuesta permanece `not-run`.

Comprobaciones ejecutadas para esta entrega documental:

- 16 requisitos, 11 tareas y 32 escenarios con referencias internas válidas;
  dependencias sin ciclos y 10 enlaces a archivos existentes.
- UTF-8 y espacios finales correctos; `git diff --check` sin incidencias.
- Validación estructural de las seis skills y del manifiesto del plugin superada.
- Estructura de los 23 perfiles, contrato del plugin y manifiesto de 14 fixtures
  válidos. La comprobación de perfiles usa `--allow-unvalidated`: no certifica
  perfiles candidate ni ejecuta sus toolchains.
- No se ejecutan suites funcionales, Docker, benchmarks ni aceptación humana
  para una funcionalidad que todavía no está implementada.

## 11. Entrega de implementación local

La autorización posterior dio lugar a la implementación, pruebas y guía descritas
en [PROJECT-QUERY.md](../PROJECT-QUERY.md). El apartado 10 es histórico; no describe
el estado actual. La evidencia, incluidos fallos y límites, se recoge en
[project-query-2026-09-17.md](../validation/project-query-2026-09-17.md).

| Trabajo | Estado de entrega | Evidencia o pendiente |
|---|---|---|
| Q01–Q08 | Implementación local disponible | Cinco módulos, schema auxiliar, CLI, guía compartida y seis skills; sin cambios canónicos |
| Q09 | Verificación automatizada realizada | 44 tests de consulta + 3 de CLI passed; dos benchmarks finales cumplen 2 s/5 s; fidelidad humana no inferida |
| Q10 | Integración comprobada con reservas abiertas | Validadores y evals passed; suite general 445 passed/1 failed/1 skipped, fallo previo de rutas y presupuesto package superado en esa ejecución |
| Q11 | `not-run` | Aceptación humana y navegación real en Codex/Copilot pendientes; no instalación activa |

Decisiones de implementación: la CLI emite contexto `partial` o una necesidad de
aclaración, no `answered` automático. La suficiencia corresponde al asistente.
Se lee el checkout actual, sin seleccionar otras revisiones Git. La ampliación
documental no obliga a adoptar SDD ni altera el estado de tareas. La revalidación
usa hasta cuatro hilos locales para lecturas independientes, sin procesos ni
agentes; mantiene hashes y comprobaciones de identidad.

No se declara aceptación completa del producto ni distribución validada. La
siguiente fase es resolver el fallo de empaquetado en su alcance separado y
realizar la aceptación Q11 en un entorno autorizado. Publicación, instalación,
activación, commit y push siguen fuera de esta entrega.
