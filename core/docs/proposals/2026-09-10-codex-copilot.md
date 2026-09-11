# Propuesta técnica: LKS-SDD para Codex y GitHub Copilot en equipos

Fecha: 2026-09-10. Estado: **propuesta para revisión; no implementada ni certificada**.

Actualización de alcance confirmada: la generación visual en Copilot se resuelve mediante relevo guiado a la aplicación Codex, con retorno opcional. En Codex nativo no se añaden avisos ni pasos de relevo. El [plan de implementación vigente](../plans/2026-09-10-codex-copilot-implementation.md) concreta esta decisión, el orden de entrega y las pruebas; prevalece sobre la planificación preliminar de este documento. La colaboración paralela avanzada se separa de la primera entrega secuencial.

Base inspeccionada: LKS-SDD `1.0.0`, commit `e9daf7b60247f6acdafddc5cdb3269e433116719`, contrato de proyecto schema `1.5` / método `1.5.0`. La propuesta se añade como documento independiente. No modifica los contratos canónicos, las instalaciones ni los proyectos consumidores.

## 1. Objetivo y decisiones de alcance

Mantener un único producto y repositorio de LKS-SDD que genere en cada release dos distribuciones: plugin para la aplicación Codex y Agent Skills para GitHub Copilot en VS Code. Los desarrolladores deben poder trabajar sobre un mismo proyecto Git, alternar herramientas y personas, y conservar especificaciones, decisiones, tareas, autorizaciones, checkpoints y evidencias compatibles.

Confirmado en esta conversación: un repositorio del producto, dos destinos, versión común y exclusión de la extensión Codex de VS Code. El resto de las decisiones técnicas de este documento son propuestas. Como hipótesis de diseño, «compartir entre desarrolladores» incluye tanto relevo secuencial como tareas independientes en paralelo; se explicita una alternativa más pequeña si solo se necesita el relevo.

Se propone como primera plataforma de aceptación Windows con PowerShell, aplicación Codex y VS Code con Copilot en modo Agent, ejecutando localmente sobre clones o worktrees. Los contenedores Linux de los perfiles continúan formando parte de sus pruebas. Copilot cloud agent, Copilot CLI, otras extensiones y otros sistemas anfitriones requieren matrices futuras; no se deduce su soporte del estándar de skills.

«Mismo proyecto» significa el mismo repositorio y contrato versionado. Cada desarrollador trabaja en su propia copia; el modelo no depende de compartir una carpeta de red ni sesiones de chat. El servidor Git consumidor puede ser GitHub o GitLab: utilizar Copilot no convierte Jira o GitHub Issues en requisito del método.

La aceptación exige equivalencia de reglas y resultados verificables del proceso completo, con la excepción de superficie acordada: Copilot delega la generación de imágenes en Codex mediante relevo. No exige textos de respuesta idénticos ni código generado byte a byte por modelos distintos. Tampoco convierte los perfiles candidate o interoperabilidades todavía no demostradas en capacidades soportadas.

## 2. Diagnóstico del producto actual

| Hecho observado | Evidencia local | Consecuencia para la implementación |
|---|---|---|
| Hay seis skills; el manifiesto y sus metadatos están orientados a Codex | [Manifiesto](../../.codex-plugin/plugin.json), [skills](../../skills/) | Generar metadatos por destino desde instrucciones sustantivas únicas |
| La CLI pública expone 22 comandos | [Dispatcher](../../scripts/lks_sdd.py) | Conservar toda la API funcional, sus parámetros, códigos de salida y garantías |
| El runtime busca recursos por posición relativa y las skills localizan `.codex-plugin/plugin.json` | [Preparación](../../skills/lks-sdd-implement/scripts/prepare_increment.py), [doctor](../../scripts/doctor_project.py) | Introducir identidad neutral del runtime y resolución determinista; copiar solo SKILL.md no sirve |
| El catálogo contiene 23 perfiles: 17 active y 6 candidate | [Catálogo](../../profiles/catalog.json) | Empaquetar el catálogo completo; active sigue exigiendo certificación exacta vigente |
| La certificación incluye hashes de scripts del motor y de las skills | `CERTIFICATION_ENGINE_FILES` en [profile_registry.py](../../scripts/profile_registry.py) | Un refactor puede invalidar certificaciones aunque parezca solo empaquetado |
| Existen varias ejecuciones y selección por TASK/EXEC en verificación | [Continuidad](../../scripts/manage_continuity.py), `_run_v12` en [verificación](../../skills/lks-sdd-verify/scripts/run_verification.py) | Reutilizar lo existente; completar las rutas que todavía dependen de una proyección global |
| La preparación actual actualiza `active_increment`, `active_tasks` e `implementation` | [prepare_increment.py](../../skills/lks-sdd-implement/scripts/prepare_increment.py) | Evitar que la última tarea iniciada sea la selección implícita de otro desarrollador |
| EXEC/CKPT/EVID se asignan a partir de los IDs visibles localmente | `_next_indexed_id`, `_next_checkpoint_id`, `_next_evidence_id` en [preparación](../../skills/lks-sdd-implement/scripts/prepare_increment.py), [continuidad](../../scripts/manage_continuity.py), [work](../../scripts/work_task.py) | Dos clones del mismo commit pueden proponer el mismo identificador para hechos distintos |
| Hay preview/hash, creación exclusiva, comprobación de bytes y rollback | `_write_transaction` y `_apply_checkpoint` en las fuentes anteriores | Protegen operaciones locales; no acreditan coordinación distribuida entre clones |
| `verification_subject` incorpora entradas del proyecto y versión del plugin | [experience_engine.py](../../scripts/experience_engine.py) | Acordar qué entradas son comunes a ambos hosts; no excluir indiscriminadamente configuración o herramientas |
| Jira tiene motor offline y operaciones por un peer Rovo externo | [Integración Jira](../JIRA-ROVO-INTEGRATION.md) | Conservar intención, autorización y recibos; adaptar la identificación del peer por superficie |
| Generar prototipos con ImageGen es condicional a su disponibilidad | [Contrato visual](../../skills/lks-sdd-define/references/frontend-design.md) | Diseñar generación y revisión en Copilot; un fallback pendiente no prueba paridad visual |
| La release exige exactamente cinco assets y validadores específicos de Codex | [Builder](../../scripts/build_candidate_package.py), [CI](../../.github/workflows/quality.yml) | Evolucionar conjuntamente builder, schemas, inventario de assets, tests y pipeline |

Inferencia técnica: la base compartida permite reutilizar gran parte del motor, pero la distribución Copilot y el trabajo distribuido requieren ingeniería adicional. La inspección estática identifica riesgos y puntos de cambio; no constituye una prueba ejecutada de fallos concurrentes.

Algunos documentos mantienen títulos o cifras históricos, aunque el catálogo y el manifiesto ya son 1.0.0. El inventario de compatibilidad nuevo se debe generar desde código, catálogo y contratos vigentes, con trazabilidad de cualquier discrepancia documental.

## 3. Arquitectura propuesta

```text
Repositorio del producto LKS-SDD
  contratos + workflows comunes + runtime Python + perfiles + pruebas
                             |
                   build de una versión/commit
                    /                       \
        plugin/marketplace Codex       paquete Copilot
        seis skills + runtime          seis skills + mismo runtime
                    \                       /
                     proyecto consumidor Git
               Markdown + código + evidencias comunes
```

### 3.1 Núcleo y adaptadores

Conservar inicialmente las rutas de scripts, schemas, profiles y assets para reducir el impacto sobre los hashes y la CLI existente. Añadir fuentes de instrucciones neutrales y adaptadores declarativos; no mover toda la implementación a una biblioteca nueva durante el primer empaquetado.

Estructura orientativa del repositorio del producto; los elementos nuevos todavía no existen:

```text
product/release.json                  versión e identidad únicas
workflows/<skill>/                   fuentes de instrucciones y referencias comunes
adapters/codex/                      manifiesto, metadatos e invocaciones Codex
adapters/copilot/                    frontmatter y guía de herramientas Copilot
skills/<skill>/scripts/              implementación actual reutilizada
scripts/                            motor común y herramientas de distribución
schemas/ profiles/ templates/        contratos y recursos comunes
distribution/                       recetas y manifiestos de empaquetado
tests/hosts/ tests/collaboration/    pruebas nuevas
quality/                            cobertura y evidencia por destino
specs/canonical/                     fuentes actuales preservadas
specs/proposed/                      extensión futura de portabilidad/colaboración
```

El compilador documental combina una fuente de workflow con un adaptador explícito. No debe hacer sustituciones globales de «Codex» por «Copilot»: las diferencias de herramientas, permisos y capacidades necesitan reglas revisadas. Los scripts comunes deben ser idénticos byte a byte en ambas distribuciones de una release. Las salidas generadas no son una segunda fuente editable.

Se conservan exactamente los seis entrypoints. No se necesita una extensión VSIX, un agente personalizado adicional ni un servidor MCP propio para el método.

### 3.2 Identidad y selección del runtime

Introducir un manifiesto neutral con versión del producto, commit, digest del núcleo, versión de contratos soportados, inventario y digest del adaptador. `.codex-plugin/plugin.json` sigue existiendo solo por su función de distribución Codex; deja de ser la única forma de identificar el motor.

Cada proyecto fija una versión exacta y un digest del núcleo en un lock operativo versionado. Este lock no duplica requisitos ni decisiones de negocio. El launcher debe localizar el paquete que coincide exactamente, verificar su integridad y pasar la raíz del proyecto de forma explícita. Ante cero o varias coincidencias, diagnostica el problema; no escoge la instalación más reciente ni descarga automáticamente otra versión.

La ruta absoluta del runtime y el intérprete Python son datos locales. Los documentos compartidos usan rutas relativas al proyecto. La configuración personal no se exporta al repositorio.

Codex puede tener un plugin global distinto del requerido por un proyecto. La skill de entrada debe ejecutar el preflight del lock antes de una mutación y, si no coincide, cargar el workflow y motor exactos de la versión fijada o detenerse con el procedimiento de selección de versión. La prueba debe cubrir dos proyectos abiertos con versiones diferentes; no basta con cambiar `plugin_version` en el índice.

### 3.3 Paquete Copilot y ausencia de skills duplicadas

Se propone distribuir las skills de Copilot en `.github/skills/lks-sdd-*/`, con referencias y recursos explícitos, y el runtime completo en una ruta común versionada del consumidor, por ejemplo `tools/lks-sdd/runtime/`. Ambos hosts utilizarán ese runtime cuando el proyecto adopte este modo de distribución. El plugin Codex conservará su copia para proyectos todavía no vinculados y para instalación inicial.

Se prefiere `.github/skills` a `.agents/skills` en esta primera implementación para no provocar que Codex descubra dos copias de las seis skills: una por plugin y otra por carpeta común. La detección de duplicados de instalaciones personales es parte de la aceptación. El paquete contiene instrucciones reales por workflow, no seis entrypoints vacíos que deleguen todo a un texto gigante.

La ubicación de skills de Copilot y su invocación explícita y automática están documentadas por [VS Code](https://code.visualstudio.com/docs/agent-customization/agent-skills). Se conservarán las descripciones delimitadas y la carga implícita; el frontmatter Copilot mantendrá habilitadas la invocación por el usuario y la selección por el modelo.

El coste de versionar el runtime completo es un repositorio consumidor mayor. A cambio, un clon contiene la versión exacta sin depender del equipo de otro desarrollador. La primera implementación debe medir tamaño y profundidad de rutas del bundle real. Si resulta inviable, la alternativa será descargar un asset inmutable mediante un bootstrap con checksum; esa elección se cerrará con medidas, sin introducir rutas a cachés personales compartidas.

El runtime común debe conservar también las fuentes documentales que utilice la skill Codex: el adaptador instalado verifica su versión y carga las instrucciones exactas del proyecto mediante enlaces explícitos. El compilador y los tests comprobarán que ningún workflow mezcle instrucciones de una versión global con scripts de otra versión fijada.

### 3.4 Repositorio consumidor

```text
AGENTS.md                              reglas comunes y entrada a LKS-SDD
.github/copilot-instructions.md         puente breve hacia reglas comunes
.github/skills/lks-sdd-*/               workflows Copilot generados
tools/lks-sdd/runtime/                  motor y recursos fijados
.lks-sdd/toolchain.lock.json            identidad exacta, sin secretos
.lks-sdd/project.json                   índice del proyecto
docs/lks-sdd/                           contrato semántico compartido
docs/lks-sdd/04-delivery/                tareas, autorizaciones y continuidad
docs/lks-sdd/evidence/                  evidencias y archivos referenciados
src/ o apps/                           aplicación según contrato existente
```

Nombres y rutas nuevos son propuestas sujetas al schema de implementación. El instalador realizará preview del conjunto de archivos, detectará colisiones y aplicará únicamente el bloque gestionado. Preservará instrucciones de equipo preexistentes. Actualizar o retirar el paquete no borra documentación, código, evidencia ni personalizaciones ajenas.

`AGENTS.md` contendrá las reglas comunes; el puente Copilot será corto y remitirá a ellas. VS Code documenta tanto `AGENTS.md` como `.github/copilot-instructions.md`; el preflight y las pruebas deben comprobar su carga real, incluidas las políticas corporativas aplicables. No se dependerá de instrucciones anidadas experimentales para reglas esenciales. [Instrucciones en VS Code](https://code.visualstudio.com/docs/agent-customization/custom-instructions).

Los locks, instrucciones y runtime gestionado deben estar presentes para todos los participantes, aunque cada uno utilice una herramienta distinta. No se añadirá o retirará el adaptador al cambiar de editor. Esto evita diferencias artificiales del árbol verificado entre desarrolladores.

Credenciales, tokens, `.env` real, sesiones, memorias, cachés y rutas personales quedan fuera de Git. Las capturas y evidencia compartidas deben tener rutas relativas, clasificación y hashes; los archivos voluminosos pueden residir en Git LFS o en almacenamiento de artefactos aprobado con referencias inmutables y acceso probado desde otro clon. Un enlace a una imagen que solo existe en el equipo de origen no completa un relevo.

## 4. Cobertura funcional obligatoria

Cada fila será un requisito del catálogo de paridad. El estado inicial de todas las pruebas Copilot es `not-run`. «Común» significa reutilización del motor con pruebas, no garantía basada solo en compartir archivos.

| ID | Funcionalidad actual que se conserva | Implementación propuesta y comprobación |
|---|---|---|
| F01 | Help, onboarding, límites, conceptos y siguientes pasos | Mismas fuentes; consulta sin mutación del contrato en ambos hosts |
| F02 | Descubrimiento, requisitos, decisiones, incertidumbre y cobertura de definición | Mismo workflow, entrevista contextual y trazabilidad; nada se confirma por silencio |
| F03 | Inicialización aditiva de una aplicación nueva | CLI `define` común; permisos, colisiones y bloqueo ante aplicación existente |
| F04 | Definición UX y prototipos, selección/rechazo y reutilización visual | Codex genera directamente; Copilot prepara relevo a Codex y valida el retorno opcional. Mismos archivos, hashes, revisión y ADR |
| F05 | Adopción: inspección estática, reconciliación y materialización | Tres comandos `adopt-*`; no ejecutar aplicación durante inspección ni cambiar comportamiento |
| F06 | Variantes tecnológicas, dependencias y preparación de adopción | `compatibility`, `profile-impact` y recursos 0.18; preservar resoluciones y colisiones |
| F07 | Gobierno de entregas, versiones, ramas, entornos y recuperación | Mismos Markdown y validadores; decisiones técnicas continúan siendo explícitas |
| F08 | Planificación PLAN/REL/TASK, cobertura integral o política incremental | `planning`; alcance sin tareas, ciclos y dependencias incompletas impiden falsos cierres |
| F09 | Tracking local y elección `repository-only` / `jira-hybrid` | `tracking` común; elección persistente por proyecto y restricciones de binding intactas |
| F10 | Proyección Jira, previews, autorización y recibos | Peer Rovo por host; búsqueda de duplicados, write delimitado, relectura y resultado real |
| F11 | Reporting Jira, comentarios, transiciones, pausa y reconciliación | Mismos hitos y SYNC separados; una operación incierta no se repite ciegamente |
| F12 | Readiness: especificación, plan, slice y automatización | `assess-readiness`; resultados separados, mismos bloqueos y requisitos de autorización |
| F13 | Catálogo completo y perfiles exactos por unidad/binding | Los 23 perfiles; certificar los 17 active y conservar los 6 candidate con sus límites |
| F14 | Preparación e implementación autorizada | `implement` y `work`; mismos locks, alcance y control transaccional |
| F15 | Tablero, transiciones, problemas y salud actual | `tasks`, `work`, `status`; PROB y estado TASK coherentes tras ambos hosts |
| F16 | Autorización, pausa, checkpoint, reanudación y cambio de persona | `planning`, `continuity`; no depender de chats ni de un «current task» global |
| F17 | Validación documental y trazabilidad | `validate-project`, `validate-spec`, `traceability`; mismo contrato y alcance por TASK |
| F18 | Verificación incremental, scopes y evidencia inmutable | `verify`; component/contract/composition/user-flow/persistence/visual sin intercambiarlos |
| F19 | Revisión visual y evidencia por TASK | Navegador, interacción, viewport, resultado, archivos y hashes; 1–5 capturas significativas según contrato |
| F20 | Integración full-stack y persistencia | Gates/observadores existentes, operaciones INT reales, read-back y recarga; mocks no acreditan negocio |
| F21 | Reutilización, nuevos hallazgos, corrección y re-verificación | `verification_subject`, EVID histórica intacta y nuevas evidencias atribuibles |
| F22 | Evidencia de entrega G4 y aprobación humana | Revisión, árbol, build, digest y entorno exactos; generación de plantilla no acredita despliegue |
| F23 | Vistas cliente y clasificación de fuentes | `client-view`; preview, autorización, procedencia y saneamiento comunes |
| F24 | Experiencia management/developer/audit, doctor, caché y rendimiento | `help`, `status`, `work`, `doctor`; mismas semánticas y presupuestos de rendimiento |
| F25 | Calidad del producto, evals, perfiles, empaquetado y piloto | Herramientas de mantenedor comunes y nuevas pruebas por host; no confundirlas con tareas consumidoras |

Inventario público a comprobar automáticamente contra `COMMANDS`: `help`, `define`, `adopt-inspect`, `adopt-validate`, `adopt-materialize`, `assess-readiness`, `implement`, `verify`, `tasks`, `planning`, `tracking`, `continuity`, `profiles`, `compatibility`, `profile-impact`, `validate-project`, `validate-spec`, `traceability`, `client-view`, `status`, `work`, `doctor`. La cobertura debe incluir los subcomandos y opciones de sus parsers; contar únicamente estos 22 nombres sería insuficiente.

Se conservará igualmente la disponibilidad de herramientas de mantenedor empaquetadas hoy: harness, certificación, piloto y distribución. Su uso sobre el repositorio del producto debe quedar separado del trabajo sobre la aplicación consumidora, para no lanzar suites internas con cada consulta de usuario.

## 5. Capacidades dependientes del host

### 5.1 Ficheros, terminal y lectura de imágenes

Los adaptadores declaran capacidades: leer/escribir archivos, ejecutar procesos, observar navegador, leer imágenes y usar peers externos. Resolverán las herramientas realmente disponibles sin codificar IDs privados de sesión. Las reglas de autorización del método siguen en el núcleo; un permiso de terminal del editor no representa una autorización de tarea.

El preflight debe informar versión de host/extensión, modo Agent, modelo elegido, capacidades observadas, Python, Git y dependencias del perfil. Las versiones mínimas se fijarán a partir de las pruebas ejecutadas, no de una suposición sobre «la última versión». Un host/modelo no probado queda fuera de la matriz certificada.

### 5.2 Navegación y evidencia

VS Code documenta herramientas de navegador integradas. Se propone probarlas para exploración y revisión visual, manteniendo como referencia los runners y observadores empaquetados de LKS-SDD para gates técnicos. Si el navegador integrado no exporta la evidencia necesaria, utilizar el runner de navegador del perfil desde terminal y proporcionar sus imágenes al agente. [Herramientas de navegador de VS Code](https://code.visualstudio.com/docs/agents/run/browser-tools).

Se debe comprobar que Copilot puede inspeccionar imágenes, acceder a la aplicación local y conservar capturas accesibles desde otro clon. Los resultados deberán cumplir el schema visual existente. Una captura genérica del navegador integrado no sustituye los observadores de composición, tráfico, persistencia y errores.

### 5.3 Jira mediante Rovo

Atlassian documenta conexión de su servidor Rovo MCP con VS Code/GitHub Copilot y uso desde Codex Desktop. Es una vía técnica disponible para evaluar; no prueba la interoperabilidad completa de LKS-SDD. [Guía oficial de Atlassian](https://support.atlassian.com/atlassian-ai-gateway/docs/get-started-with-the-atlassian-remote-mcp-server/).

Se propone conservar Rovo como peer externo instalado y autenticado separadamente por cada persona. LKS-SDD no empaqueta servidor MCP ni cliente Jira propios. El adaptador valida procedencia, capacidades y parámetros observados, manteniendo `atlassian-rovo` como proveedor semántico, sin reutilizar IDs de conexión de Codex en Copilot.

La aceptación requiere probar lectura, búsqueda exacta, creación, actualización, comentario, transición, relectura y reconciliación con permisos reales de prueba. Si falta una operación, esa capacidad permanece bloqueada. La degradación advisory o required-before-execution conserva el comportamiento actual y no cambia silenciosamente un binding durable.

### 5.4 Generación de imágenes: relevo a Codex confirmado

No se ha acreditado una herramienta nativa de generación de imágenes en Copilot equivalente a la disponible en la aplicación Codex. Leer imágenes, capturar pantallas o usar un modelo de texto no demuestra esa capacidad.

La decisión posterior del usuario descarta incorporar un proveedor externo de generación/edición por API en Copilot. Cuando el brief sea suficiente y se necesiten imágenes nuevas o editadas, Copilot prepara un relevo durable, mantiene la dimensión visual pendiente e invita a abrir ese mismo proyecto en la aplicación Codex. Entrega un mensaje listo para copiar con referencias a los archivos necesarios, sin transferir chats ni lanzar la aplicación automáticamente.

Codex lee ese contexto, genera y permite revisar propuestas, y registra imágenes/decisión humana bajo el contrato actual. El usuario puede permanecer allí o volver a Copilot. Al retomar, Copilot valida identidad del proyecto, versiones, vigencia del brief, assets, hashes y aprobación; no confunde generación con aceptación ni con autorización de implementación.

En una sesión Codex nativa, el prototipado sigue su proceso habitual: no hay invitación, pregunta, fichero ni aviso de relevo. Se mantienen la selección humana y los diagnósticos reales si ImageGen no está disponible. La reutilización de un diseño confirmado y los cambios sin impacto visual no provocan saltos innecesarios.

Este procedimiento pasa a ser el flujo soportado propuesto, no un fallback transitorio. La aceptación acredita equivalencia del proceso completo mediante relevo, no generación nativa en Copilot. No requiere API adicional; requiere que quien genere disponga de acceso a Codex y capacidad disponible. El contrato de relevo y sus pruebas están en el plan de implementación vigente.

## 6. Modelo de colaboración entre desarrolladores

### 6.1 Reglas comunes

Un clon/worktree por persona y flujo de trabajo; ramas según la política confirmada del consumidor. El plan identifica un responsable por TASK y sus dependencias. Dos tareas independientes pueden progresar en paralelo. Compartir el mismo directorio físico con dos agentes escritores queda fuera del modelo certificado.

La planificación y los cambios en contratos compartidos se integran de forma coordinada. Cada tarea declara los archivos/unidades afectados; cambios sobre el mismo contrato, lock, migración o interfaz requieren reconciliación antes de seguir. Tener dos TASK distintas no demuestra que sus cambios sean independientes.

### 6.2 Identificadores estables y autoría

Se propone extender el contrato para permitir IDs distribuidos en los hechos operativos nuevos, por ejemplo `EXEC-<uuid>` y `CKPT-<uuid>`, preservando los IDs históricos `EXEC-###`/`CKPT-###`. AUTH, EVID, SYNC y otros generadores susceptibles de colisión deben recibir el mismo análisis. No se renumerará evidencia existente al integrar ramas.

PLAN/REL/TASK y otros IDs humanos pueden conservar numeración asignada durante planificación coordinada. Su creación offline simultánea necesita reserva previa o el nuevo formato; no utilizar «máximo local + 1» como generador global.

Mantener identidad estable separada de etiquetas de presentación. Registrar rol o alias de participante, host y versión como procedencia de ejecución; una cadena `--actor` o el nombre de un modelo no prueba por sí sola la autoridad humana. Las decisiones de autorización continúan siendo canónicas y la identidad Git aporta trazabilidad adicional.

Esta modificación afecta schemas, regex, rutas, ordenación, marcadores Jira, plantillas, validadores y compatibilidad. Se requiere un inventario transversal de todos los consumidores de IDs y pruebas de historial mixto; no basta con cambiar el generador.

### 6.3 Estado por ejecución y selección local

Consolidar un registro canónico por ejecución en Markdown, enlazado con TASK, AUTH, rama/base, checkpoints y evidencias. Derivar las proyecciones de `project.json` desde ese registro, junto con las tablas canónicas existentes. El índice no decidirá cuál es la tarea que todos los desarrolladores están editando.

La selección local de TASK/EXEC vive fuera de Git y se excluye de los artefactos compartidos. Todas las rutas mutadoras aceptan selección explícita. Si hay varias ejecuciones candidatas, muestran la ambigüedad; no seleccionan «la última» ni la tarea del otro usuario. Reutilizar la selección ya implementada en verificación y extenderla coherentemente al resto de comandos.

Los archivos por ejecución reducen conflictos, pero las tablas compartidas de planificación/trazabilidad/tracking seguirán necesitándolos resolver semánticamente. Se propone un reconciliador de tres versiones —base, rama A y rama B— que emita preview, diagnóstico y plan de actualización del índice. Nunca aplicará last-write-wins sobre decisiones, autorizaciones o evidencias.

### 6.4 Coordinación y exclusividad

La primera versión de equipo tendrá asignaciones canónicas de TASK integradas antes de empezar. Para acciones que requieren exclusividad entre clones, se propone un registro operacional de reservas en una referencia Git dedicada, con actualizaciones condicionales contra el commit observado y rechazo de avances concurrentes. La referencia es un control de concurrencia, no otra fuente de requisitos ni de autorizaciones.

Especificación mínima de reserva: proyecto, TASK/EXEC, propietario, versión de reserva, recursos afectados y estado. Reclamar o transferir se confirma contra el servidor; una operación rechazada obliga a refrescar y resolver. El historial no se reescribe y no se hace force-push para apropiarse de una reserva. Las escrituras remotas de coordinación requieren la política de autorización y permisos acordada por el proyecto.

La reserva no se libera automáticamente porque venza una hora: un agente antiguo podría continuar ejecutando. La transferencia exige detener/quiescer el ejecutor anterior, comprobar su último checkpoint, resolver operaciones inciertas y registrar el relevo. Antes de cada nueva operación exclusiva se comprueba el token vigente. Si se pierde contacto con Git, pueden continuar análisis y cambios locales de código del alcance ya autorizado; nuevas proyecciones Jira, transferencias, cierre compartido y aceptación integrada esperan sincronización.

Implementar un lock local por checkout para las transacciones del motor y comprobar los bytes previos bajo ese lock. El rollback debe restaurar solo los bytes de la propia transacción; ante una escritura ajena inesperada, conservar diagnóstico y no sobrescribirla. El lock local no sustituye la coordinación Git entre máquinas.

La exclusividad absoluta frente a un editor manual o una herramienta que ignore el protocolo no puede garantizarse con Markdown. Se propone detectar esos cambios en validación y exigir checks de integración y revisión en la rama protegida. No se presentarán los prompts como un mecanismo de seguridad infalible.

### 6.5 Relevo Codex → Copilot y Copilot → Codex

1. La persona saliente guarda estado TASK/EXEC, checkpoint, rutas cambiadas, pruebas, evidencia disponible, pendientes y siguiente acción segura.
2. Publica el trabajo mediante el flujo Git autorizado del proyecto. Si necesita entregar WIP, usa la rama acordada; un checkpoint por sí solo no comparte cambios sin commit/push.
3. La persona entrante obtiene código, Markdown, assets y evidencias, selecciona el runtime exacto y ejecuta preflight de proyecto y continuidad.
4. Comprueba autorización y responsabilidad. El cambio de persona puede conservar una autorización por rol si su alcance lo permite; no se presupone transferible toda autorización nominativa.
5. Transfiere la reserva cuando proceda. Si existe deriva, un recibo externo incierto o archivos ausentes, reconcilia antes de continuar.
6. Prosigue la ejecución cuando sea atribuible y compatible; en otro caso crea una nueva ejecución vinculada al relevo, sin alterar la historia anterior.

Aceptación: la persona entrante debe completar el escenario sin acceso al chat ni a la carpeta personal de la saliente. El escenario se prueba en ambos sentidos y también Codex→Codex y Copilot→Copilot entre usuarios distintos.

### 6.6 Integración de ramas y validez de evidencia

La integración valida IDs, referencias, tareas, autorizaciones, índice y assets con el reconciliador. Las EVID se conservan como hechos del árbol y entorno observados. Después de combinar ramas se calcula el sujeto técnico integrado: si ha cambiado, se ejecutan los gates afectados y se registra evidencia nueva del resultado integrado. Que ambas ramas estén verdes no acredita su combinación.

La huella técnica incluirá el núcleo fijado y la configuración con impacto en el artefacto. La procedencia del host, la ruta absoluta y el usuario no deberán alterar por sí solos el contenido técnico; sí deben quedar registrados para auditoría. No se añadirá una exclusión genérica de `tools/`, `.github/` o `docs/`: podría ocultar un cambio de gate, dependencia o contrato.

El contrato actual incorpora la versión del plugin al sujeto; evolucionar esa identidad exige pruebas específicas de reutilización y compatibilidad. A igualdad de bytes y contratos, dos clones con distinta ruta deben obtener el mismo sujeto. Una actualización del núcleo requiere evaluar de nuevo la evidencia reutilizable.

### 6.7 Jira compartido: evitar efectos duplicados

Los recibos locales de un clon no son visibles inmediatamente en otro. Dos búsquedas simultáneas de un marker ausente podrían terminar en dos creaciones; el marker por sí solo no hace atómica la operación.

Designar un escritor operacional por TASK/evento mediante la coordinación anterior. Antes de escribir, persistir la intención autorizada y hacerla visible en la referencia operacional compartida; la confirmación allí debe enlazar el hash de la autorización canónica. El otro host debe observar esa operación pendiente y abstenerse de ejecutarla. Después del write, registrar relectura y resultado; reflejar el recibo en el contrato de la rama siguiendo el flujo Git acordado.

Si hay caída entre write y recibo, la tarea queda en reconciliación y el escritor no se transfiere hasta investigar el resultado remoto. Si Jira no proporciona idempotencia atómica, no prometer exactamente-una-vez ante cualquier fallo: garantizar ausencia de reintento ciego, exclusión bajo el protocolo y detección/reconciliación de duplicados.

### 6.8 Alternativa de menor alcance: relevo secuencial

Si el equipo empieza trabajando de uno en uno sobre el estado LKS-SDD, puede conservarse temporalmente el schema 1.5 con un responsable de escritura, sincronización Git antes de cada relevo y selección explícita de ejecución. Esa variante reduce el trabajo de IDs y coordinación distribuida y permite probar antes la adaptación Copilot. Requiere igualmente resolver las herramientas externas y ejecutar las pruebas de relevo; no se certificará como trabajo paralelo seguro entre clones.

La recomendación es usar esa variante como hito piloto del empaquetado dual, manteniendo visible el trabajo P06/P07 necesario para el objetivo más amplio. No exigir nuevas reservas Git a un proyecto que todavía no ha habilitado colaboración paralela.

## 7. Contratos, versiones y evolución de proyectos existentes

La distribución dual de skills puede prepararse como una evolución compatible. Sin embargo, el soporte multiusuario descrito altera IDs, ejecución, coordinación y proyecciones; no debe introducirse silenciosamente bajo schema 1.5, que actualmente es estricto.

La recomendación inicial de una nueva línea mayor, provisionalmente **LKS-SDD 2.0.0**, corresponde a la evolución con colaboración paralela avanzada y su extensión de contrato explícita en `specs/proposed/`. No fija la versión de la primera entrega secuencial: el plan vigente exige resolverla en P01 según los cambios reales. La numeración exacta del nuevo schema/método se fijará al cerrar su especificación. La versión de LKS-SDD, la versión del schema y la versión del método son dimensiones distintas.

Los dos paquetes finales saldrán de un único commit/tag y compartirán versión y digest del núcleo. No habrá una línea funcional separada «Copilot 1.x». Un RC dual incompleto puede publicarse como tal con autorización, pero no como una versión estable de paridad completa.

Propuesta de transición: lectura y operación 1.5 existentes mediante el núcleo compatible mientras no se habilite colaboración avanzada; activación del nuevo contrato por una conversión explícita, previsualizada y verificada en una rama de actualización. Esa conversión es una capacidad nueva y no existe hoy. Debe preservar documentos sustantivos, IDs y EVID históricos, materializar solo metadatos/índices nuevos y detenerse ante ambigüedad. Los runtimes antiguos rechazan el schema nuevo; todos los participantes se actualizan antes del primer write bajo el nuevo contrato.

La vuelta atrás tiene límites: antes del primer write nuevo se puede revertir la rama de actualización revisada; después, no se promete convertir historia nueva al contrato antiguo. Se conserva la línea anterior para proyectos que aún no han migrado y se prepara recuperación por roll-forward. Las fuentes de `specs/canonical/` no se editan para adaptar el motor.

## 8. Release y distribución reproducibles

Por versión, generar los dos destinos y las evidencias de release desde un checkout limpio del mismo commit. Se conservan los ZIP plugin y marketplace de Codex y se añade el ZIP Copilot; los archivos de evidencia se determinan con un manifiesto de assets, sustituyendo el supuesto actual de exactamente cinco archivos.

El manifiesto conjunto incluirá versión, commit, digests del núcleo y adaptadores, schemas admitidos, plataformas/hosts/modelos probados, dependencias externas y estado de paridad por F01–F25. Los checksums cubren los assets; un inventario interno valida todos los archivos y rutas del paquete extraído.

Cada build se repite con los mismos inputs inmutables y se comparan bytes. Los reportes de pruebas reales serán inputs referenciados por hash; tiempos, hostname y logs variables no se generarán dentro del segundo build. Se validan tanto los ZIP extraídos como la instalación en un consumidor sintético.

La matriz CI tendrá núcleo común, paquete Codex, paquete Copilot y colaboración. Las pruebas de host que precisen aplicación real, sesión o licencia se ejecutan en entornos de aceptación dedicados; no se simulan mediante el simple éxito de un comando Python. La publicación dual estable requiere todos los gates obligatorios de los dos destinos; un fallo Copilot no se omite para presentar la release como compatible.

Si cambia alguno de los archivos que participa en `CERTIFICATION_ENGINE_FILES`, repetir las certificaciones afectadas y regenerar sus locks desde resultados reales. Copiar una certificación de 1.0 a un motor modificado no es aceptable. Los candidates se conservan como tales.

## 9. Plan de implementación propuesto

Los paquetes de trabajo siguientes son planificación técnica propuesta; no son TASK canónicas autorizadas ni una orden de ejecución sobre consumidores.

| Paquete | Trabajo y archivos principales | Dependencias | Resultado de salida |
|---|---|---|---|
| P01 | Cerrar inventario F01–F25, extraer API de parsers, spike real de skills/navegador/Rovo/relevo visual | Ninguna | Matriz de capacidades y versiones observadas; contrato viable de relevo a Codex |
| P02 | Especificar adaptadores, identidad, lock y contrato de colaboración en `specs/proposed/`; casos de migración | P01 | Contrato revisable de compatibilidad, concurrencia, autoría y evolución |
| P03 | Resolver runtime y manifiesto neutral; actualizar dispatcher/doctor sin romper CLI actual | P02 | Un motor que funciona desde ambos árboles de instalación y rutas distintas |
| P04 | Compilar seis workflows por host; enlazar recursos, metadatos y reglas compartidas | P03 | Paquetes de skills completos, sin duplicados ni dependencia de rutas personales |
| P05 | Installer/upgrade/retirada con preview, checksum, bloque gestionado y preservación del consumidor | P03–P04 | Clon nuevo listo con versión fijada, sin editar configuración personal compartida |
| P06 | IDs distribuidos, registros por ejecución, selección local, locks y reconciliador de ramas | P02–P03 | Trabajo paralelo y continuidad sin colisiones ni sobrescritura de historia |
| P07 | Coordinación Git, asignaciones, transferencia y exclusión de escrituras Jira entre clones | P06 | Relevo verificable y tratamiento de resultados inciertos |
| P08 | Adaptación de navegador, relevo visual a Codex y Rovo; saneamiento y exportación de evidencia | P01, P04, P07 para writes distribuidos | F04 acreditada por relevo; F10/F11/F19/F20 observadas en ambas superficies |
| P09 | Actualizar schemas/validadores, conversión explícita y compatibilidad histórica | P06–P08 | Un consumidor 1.5 pasa al contrato nuevo conservando su evidencia |
| P10 | Builder dual, manifiestos de assets, CI, recertificación de perfiles, pruebas de host/equipo | P05–P09 | RC reproducible con informes separados y bloqueos visibles |
| P11 | Guías de instalación/equipo, aceptación mixta y revisión final de paridad | P10 | Candidato a release dual estable con toda la matriz obligatoria satisfecha |

P01 debe preceder a una estimación cerrada: especialmente las políticas corporativas, compatibilidad de runtime y coordinación de writes Jira pueden alterar el esfuerzo. El núcleo portable y el estado distribuido son trabajos distintos; la salida de P04 no completa el objetivo del usuario. Esta tabla conserva el desglose preliminar: el plan vigente reorganiza sus paquetes y separa la primera entrega secuencial de la colaboración paralela avanzada.

## 10. Plan de aceptación y demostración de paridad

Todos los casos nuevos comienzan como `not-run`. Cada resultado identificará commit de producto, paquete y digest, fixture/commit consumidor, host/extensión/modelo, sistema, participantes mediante alias, pasos, observaciones, archivos y resultado. Los ensayos reales se realizan en proyectos sintéticos y cuentas de prueba autorizadas.

| Caso | Escenario | Resultado exigido | Cobertura |
|---|---|---|---|
| T01 | Clon limpio; instalar cada distribución | Seis skills reales, recursos íntegros, versión exacta y comandos ejecutables | F01–F25 |
| T02 | Invocación natural y explícita de cada skill, con prompts que no corresponden | Enrutamiento correcto y ausencia de mutación desde help/readiness | F01–F03, F12 |
| T03 | Proyecto nuevo, entrevista, incertidumbre, UX y aprobación | Contrato completo sin decisiones inventadas; prototipos locales confirmados solo por persona | F02–F04 |
| T04 | Adopción de repositorio existente con contradicciones y colisiones | Inspección estática, reconciliación y materialización aditiva | F05–F06 |
| T05 | Gobierno, plan completo/parcial, dependencias y ciclos | Diagnósticos y bloqueos equivalentes en ambos hosts | F07–F09, F12 |
| T06 | AUTH ausente, caducada por deriva o fuera de alcance | Rechazo de implementación sin escribir contrato/código | F12, F14, F16 |
| T07 | Preparación y ejecución de todos los perfiles active | Gates y certificaciones exactos; candidates/Entra no se promocionan por copia | F06, F13–F14 |
| T08 | Pausar en Codex y reanudar en Copilot con otro usuario, y a la inversa | Continuidad desde Git, sin chat ni carpeta personal del anterior | F14–F17 |
| T09 | Dos usuarios con la misma herramienta y cambio de rutas locales | Igual contrato y selección correcta; relevo sin autoridad inventada | F16, F24 |
| T10 | Dos clones crean hechos desde la misma base | IDs distintos para hechos distintos, referencias preservadas al integrar | F15–F18 |
| T11 | Dos tareas independientes se implementan a la vez | Estado por TASK/EXEC; ningún current-task global pisa al otro | F08, F14–F18 |
| T12 | Dos intentos de tomar la misma TASK o recurso compartido | Solo una reserva vigente; rechazo o reconciliación del segundo | F14, F16 |
| T13 | Edición concurrente, crash y rollback de transacción | Sin pérdida de cambios ajenos; recuperación explicable | F03, F14–F18 |
| T14 | Cambio del contrato común en otra rama | AUTH/plan obsoletos se detectan antes de operaciones dependientes | F07–F08, F12, F16 |
| T15 | Verificación backend-only/frontend-only/full-stack | Aplicabilidad correcta y scopes no intercambiables | F18–F20 |
| T16 | UI→API→BD, read-back, recarga y mock funcional | Persistencia real acreditada; mock funcional rechazado para integración | F18–F20 |
| T17 | Evidencia visual ausente, corrupta, descontextualizada o falsa | Rechazo; una captura aislada no satisface aceptación | F19 |
| T18 | Prototipado nativo Codex y relevo Copilot→Codex→Copilot con retorno opcional | Codex nativo sin avisos; imagen real, aprobación y reanudación validada sin API adicional. Desglosado en V01–V24 del plan vigente | F04 |
| T19 | Jira: crear/actualizar/comment/transition desde los dos hosts | Preview autorizado, marcador y relectura, recibos exactos y límites de datos | F09–F11 |
| T20 | Dos clones proyectan la misma TASK y caída tras escritura remota | Exclusión; uncertain persistente y reconciliación sin repetición ciega | F10–F11 |
| T21 | Rovo ausente, permisos insuficientes, campo obligatorio desconocido | Degradación visible y gate correcto, sin fallback de proveedor o destino | F09–F12 |
| T22 | Mismos bytes en dos rutas, cambio administrativo, cambio técnico y upgrade de núcleo | Sujetos coherentes; reutilización válida solo donde corresponde | F18, F21, F24 |
| T23 | Dos ramas verificadas se integran con cambio técnico | Evidencia histórica intacta; verificación del resultado integrado | F17–F22 |
| T24 | Hallazgo posterior, corrección y re-verificación por otra persona/host | Salud actual y EVID histórica separadas, nueva evidencia atribuible | F15–F16, F21 |
| T25 | G4, vista cliente y cierre de release | Mismos checks; sin confundir draft, build, promoción y aceptación | F22–F23 |
| T26 | Dos proyectos con distintas versiones; skill personal duplicada | Selección exacta o bloqueo explicado; sin mezcla de núcleo/adaptador | F01, F24 |
| T27 | Conversión de proyecto 1.5 y conservación de IDs/EVID | Preview exacto, historia byte a byte y rechazo seguro del runtime antiguo | F16–F18, F21 |
| T28 | Doble build y extracción, upgrade con colisión y retirada | Bytes reproducibles y cero pérdida de personalizaciones o evidencia | F25 |
| T29 | Coste administrativo, doctor y status con fixture de rendimiento | Preservar presupuestos actuales o justificar cambios medidos | F24 |
| T30 | Uso de herramientas de mantenedor y configuración de piloto incompleta | Resultados propios del producto; piloto pendiente sigue pendiente | F25 |

Pruebas deterministas: ejecutar suites existentes, paridad de JSON normalizando solo datos volátiles explícitos, CLI completa y comparación de recursos/digests. No normalizar bloqueos, decisiones, scopes o estados para conseguir igualdad artificial.

Pruebas conversacionales: ejecutar workflows completos y casos negativos con cada host/modelo declarado; recoger artefactos y observaciones. Repetir los escenarios de autorización, reconciliación e invocación para detectar variación. La matriz inicial debe incluir al menos tres desarrolladores con ambas herramientas representadas y relevo en ambos sentidos; las licencias y sesiones son individuales.

Criterio de cierre: F01–F25 tienen implementación o comportamiento condicional explícito conforme al alcance aprobado, todos los casos obligatorios aplicables pasan, los escenarios de equipo mixto pasan y no hay regresiones Codex. F04 se acredita mediante generación nativa Codex y relevo visual completo desde Copilot; no exige generación integrada en Copilot. La primera entrega secuencial no acredita los escenarios de concurrencia distribuida: su asignación queda explícita en el plan vigente.

Los modelos pueden variar en estilo y calidad. La aceptación usa criterios de negocio, controles observables y gates; registrar una lista de modelos probados y no prometer equivalencia para cualquier modelo seleccionable en Copilot.

## 11. Decisiones pendientes con recomendación

| Decisión | Recomendación técnica | Qué falta para cerrarla |
|---|---|---|
| Forma de distribución Copilot | Skills de proyecto en `.github/skills` y runtime común fijado | Medir tamaño/rutas y completar P01/P05 |
| Protocolo de relevo visual; ruta a Codex ya confirmada | Ficha durable y retorno opcional; ninguna API de imágenes adicional | Formato, validación de retorno y pruebas reales; Codex nativo sin avisos |
| Coordinación entre clones | Relevo secuencial en la primera entrega; reservas y concurrencia distribuida en P11 del plan vigente | Transferencia y recuperación probadas; alcance y política avanzada por aprobar |
| Evolución de contratos | Resolver compatibilidad de la primera entrega en P01; línea mayor y conversión explícita si se activa el contrato avanzado | Especificar formato auxiliar, huellas y, para P11, schema, identificadores e historial mixto |
| Versiones de host/modelos | Windows local inicialmente y matriz explícita de versiones probadas | Ensayos reales en equipos/licencias representativos |
| Publicación dual | Un tag, un núcleo, dos destinos; todas las puertas obligatorias por host | Ejecución del plan, aceptación y autorización de publicación |

La aprobación de esta propuesta seleccionaría una arquitectura y un alcance de implementación. No demostraría por sí misma compatibilidad, interoperabilidad ni aceptación del producto resultante.

## 12. Verificación de esta propuesta

Realizado: lectura de contratos, manifiesto, CLI, módulos de continuidad/preparación/verificación, mecanismos de IDs/transacción/huellas, catálogo, builder, CI y documentación oficial de las superficies. No se han ejecutado sesiones funcionales de Copilot ni pruebas reales de equipo/Jira/imágenes como parte de esta propuesta.

Comprobaciones realizadas sobre el baseline 1.0.0 durante la elaboración de la propuesta:

| Comprobación | Resultado observado | Límite de la evidencia |
|---|---|---|
| Validación de las seis skills y estructura del plugin | Correcta | No demuestra su descubrimiento ni ejecución en Copilot |
| `validate_plugin_contract.py .` | Contrato 1.0.0 válido, M0–M5 y evolución schema 1.5 | Valida el contrato actual, no el propuesto |
| `validate_reference_profile.py --all --allow-unvalidated` | 23 perfiles estructuralmente válidos | No certifica perfiles candidate ni un motor futuro |
| `validate_fixture_manifest.py .` | Manifiesto válido, 14 fixtures | No equivale a ejecutar todos los escenarios de los fixtures |
| `tests/run_unit_tests.py --suite fast` | 48/48 pruebas superadas, sin fallos ni omitidas; 41,855 s | Suite rápida existente; no harness completo ni pruebas de host |
| Enlaces locales del documento | 18 enlaces, ninguno roto | Existencia de destinos, no aceptación semántica de la propuesta |
| Comprobación de whitespace y fuentes canónicas | Sin errores detectados; `specs/canonical/` sin cambios | Solo se ha añadido este documento; no se ha implementado el producto dual |

La primera ejecución de la suite rápida encontró un error de permisos sobre temporales de Windows dentro del sandbox; la repetición autorizada fuera de él terminó correctamente. No se han ejecutado el harness completo, las certificaciones de release ni un piloto funcional nuevo.

Estos resultados no deben interpretarse como ejecución de T01–T30, que permanecen `not-run` hasta la implementación y aceptación correspondientes. No se ha instalado, publicado ni activado ninguna distribución, ni creado commits o realizado push.
