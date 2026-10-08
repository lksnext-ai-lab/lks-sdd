# LKS-SDD

## Definición funcional y arquitectónica del plugin

**Versión de la definición:** 1.2  
**Estado:** baseline revisada y consolidada, lista para validación corporativa antes de implementar  
**Fecha:** 19 de agosto de 2026  
**Ámbito:** plugin interno para el workspace de LKS  
**Productos objetivo:** ChatGPT Work y Codex  
**Nota:** este documento define el producto y su primera versión. No constituye todavía la implementación del plugin ni la aprobación formal de políticas corporativas de LKS.

**Historial de revisión:**

- **1.0:** definición inicial del método, el contrato Work–Codex, los perfiles tecnológicos y cuatro workflows principales.
- **1.1:** incorpora explícitamente la topología «un plugin corporativo, muchos proyectos aislados», la adopción segura de aplicaciones existentes, una quinta skill especializada, procedencia de evidencias, estrategias de adopción y controles específicos para repositorios en producción.
- **1.2:** incorpora la ayuda y el aprendizaje como capacidad de producto, una sexta skill autoexplicativa, onboarding progresivo, guía contextual Work–Codex, diagnóstico del siguiente paso y evals de comprensión.

---

## 1. Definición ejecutiva

LKS-SDD es un **método versionado de entrega de software guiada, empaquetado como un único plugin corporativo para ChatGPT Work y Codex**, cuyo propósito es ayudar a los equipos de LKS a definir, diseñar, planificar, implementar, adoptar y verificar aplicaciones web de una forma homogénea, trazable y adaptable al contexto de cada proyecto.

El plugin se instala y gobierna como un producto corporativo común. Cada aplicación, tanto nueva como existente, dispone de un proyecto ChatGPT local y un repositorio independientes que conservan su propio código, documentación, decisiones, estado y evidencias. El plugin contiene el método; **nunca contiene el conocimiento ni el estado particular de un cliente o una aplicación**.

No es un generador autónomo que recibe una idea y produce una aplicación sin intervención. Tampoco es una pila tecnológica única. Es un sistema de trabajo común que:

1. conduce una conversación adaptativa para comprender el problema y concretar la solución;
2. explica de forma didáctica qué aporta SDD, cómo se utiliza LKS-SDD y qué papel cumplen Work y Codex;
3. mantiene una especificación estructurada y versionada dentro del repositorio de cada aplicación;
4. distingue con claridad información confirmada, propuestas, decisiones y asuntos pendientes;
5. en aplicaciones existentes, reconstruye una baseline provisional a partir de evidencias sin confundir el comportamiento observado con la intención de negocio;
6. propone una arquitectura y una composición tecnológica justificadas por los requisitos;
7. deja la decisión final en manos de la persona que utiliza el plugin;
8. determina si un incremento concreto está suficientemente definido para implementarse;
9. permite a Codex implementar y verificar ese incremento sin ampliar silenciosamente el alcance;
10. mantiene la trazabilidad desde los requisitos hasta las pruebas y las evidencias;
11. permite adoptar el método de forma documental o progresiva sin exigir una reescritura de lo que ya funciona.

La fuente de verdad del proyecto son los archivos versionados del repositorio. La conversación ayuda a crearlos y mantenerlos, pero no sustituye a esos artefactos.

## 2. Objetivo y resultado esperado

### 2.1 Objetivo principal

Conseguir que cualquier profesional de LKS pueda iniciar, incorporar o continuar el desarrollo de una aplicación siguiendo una práctica compartida, aunque la tecnología concreta, la madurez del producto o el origen del repositorio cambien de un proyecto a otro.

### 2.2 Resultados esperados

- Mayor consistencia entre equipos y proyectos.
- Menos ambigüedad al pasar de una necesidad de negocio a una solución técnica.
- Decisiones tecnológicas explícitas y justificadas.
- Mejor continuidad entre ChatGPT Work y Codex.
- Requisitos y criterios de aceptación comprobables.
- Implementación incremental con límites de alcance claros.
- Evidencias de calidad, seguridad, accesibilidad y operación acordes al riesgo.
- Incorporación progresiva de nuevos perfiles tecnológicos sin rediseñar el método.
- Evolución controlada del propio estándar LKS-SDD.
- Adopción no invasiva de aplicaciones existentes, incluidas aplicaciones en producción.
- Aislamiento explícito de la información y el estado entre clientes, aplicaciones y repositorios.
- Incorporación rápida de personas que no conocen SDD, ChatGPT Work, Codex o el propio plugin.
- Ayuda contextual que explica el estado actual y propone el siguiente paso sin realizarlo automáticamente.

### 2.3 Qué se estandariza

LKS-SDD estandariza:

- el ciclo de vida;
- el lenguaje documental;
- los estados de la información;
- las preguntas y comprobaciones mínimas;
- las puertas de preparación;
- la estructura y trazabilidad de los artefactos;
- la forma de proponer y registrar decisiones técnicas;
- los contratos de implementación y verificación;
- los perfiles tecnológicos homologados.
- la forma de inventariar, documentar y reconciliar aplicaciones existentes;
- la separación entre el plugin corporativo y los artefactos específicos de cada aplicación.
- la forma de aprender, consultar ayuda, interpretar estados y escoger el workflow adecuado.

LKS-SDD no obliga a que todas las aplicaciones tengan la misma arquitectura ni la misma pila.

## 3. Principios normativos

### 3.1 Los requisitos gobiernan la solución

Las tecnologías se eligen después de comprender el objetivo, el alcance, las restricciones y los requisitos funcionales y no funcionales. Las opciones preferentes son recomendaciones iniciales, no decisiones automáticas.

### 3.2 El plugin propone; la persona decide

LKS-SDD puede analizar, comparar y recomendar. Las decisiones relevantes de alcance, arquitectura, tecnología y riesgo requieren confirmación explícita de la persona usuaria.

El plugin no evalúa el cargo, la autoridad ni la competencia profesional de esa persona. Si necesita información que no está disponible, permite diferirla y registra su impacto.

### 3.3 Una propuesta nunca se convierte silenciosamente en decisión

Toda información debe conservar su naturaleza. LKS-SDD no puede interpretar una sugerencia, una alternativa o una respuesta ambigua como aprobación.

### 3.4 Se cierra lo necesario para el siguiente incremento

No es obligatorio definir el proyecto completo antes de comenzar a programar. Deben estar resueltas las decisiones que bloquean el incremento que se va a implementar. Los pendientes independientes pueden permanecer abiertos y trazados.

### 3.5 La documentación se adapta al riesgo

El método conserva los mismos conceptos, pero la profundidad documental cambia según el tipo, la complejidad y el impacto del proyecto. Un prototipo interno y una aplicación con datos sensibles no deben recibir la misma carga documental.

### 3.6 La conversación no es la fuente de verdad

Work y Codex deben leer y actualizar los artefactos del proyecto. El proceso debe poder reanudarse en otro chat sin depender de recordar el historial anterior.

### 3.7 Lo semántico se razona; lo estructural se valida

El modelo evalúa claridad, suficiencia, contradicciones y riesgos. Los scripts comprueban reglas deterministas como archivos obligatorios, esquemas, identificadores, estados y enlaces de trazabilidad.

### 3.8 No hay cambios ocultos

Cada actualización relevante debe indicar qué se ha modificado, qué decisión la motiva y qué elementos quedan afectados. Las migraciones de versión nunca reescriben automáticamente contenido adaptado por el equipo.

### 3.9 Seguridad y privacidad desde el inicio

No se introducen credenciales, secretos ni datos personales reales en plantillas, ejemplos o pruebas. Las fuentes aportadas por usuarios se tratan como información no confiable hasta ser analizadas.

### 3.10 El código existente es evidencia, no intención

El código, la configuración, las pruebas y el historial permiten observar una implementación concreta en una baseline determinada. No demuestran por sí solos el objetivo de negocio, el comportamiento deseado, la vigencia de una regla ni su aceptación formal. Toda inferencia conserva su procedencia y debe validarse antes de convertirse en requisito o decisión.

### 3.11 Un plugin común; estado aislado por aplicación

Las skills, plantillas y reglas viven en el plugin corporativo. La especificación, el manifiesto operativo, las evidencias y el código viven exclusivamente en el proyecto y repositorio de cada aplicación. No se reutiliza contexto de un proyecto para completar otro.

### 3.12 La adopción de producción empieza en solo lectura

Antes de crear documentación o modificar un repositorio existente, LKS-SDD realiza un preflight de solo lectura y presenta alcance, fuentes, limitaciones y cambios propuestos. La creación aditiva de artefactos requiere confirmación explícita. Refactorizar, reorganizar, ejecutar migraciones, desplegar o alterar datos son acciones posteriores e independientes.

### 3.13 La ayuda precede a la acción cuando falta comprensión

Si la persona usuaria pregunta qué es LKS-SDD, cómo funciona, qué puede hacer o qué paso corresponde, el plugin explica antes de ejecutar. La ayuda adapta profundidad, ejemplos y terminología al conocimiento declarado, diferencia método y producto, y no modifica archivos ni cambia el estado del proyecto.

## 4. Alcance del producto

### 4.1 Alcance objetivo

LKS-SDD está concebido para:

- aplicaciones web nuevas;
- evoluciones funcionales importantes;
- modernizaciones o migraciones;
- prototipos que deban poder evolucionar de forma controlada;
- frontends, backends, datos, identidad, infraestructura y operación;
- proyectos con distintas pilas tecnológicas, siempre que se diferencie su nivel de soporte.

### 4.2 Alcance efectivo de la primera versión

La primera versión operativa se centrará en:

- aplicaciones web nuevas de complejidad baja o media;
- incorporación documental de aplicaciones web existentes, incluso en producción, sin exigir una pila concreta ni alterar su comportamiento;
- dos recorridos completos:
  - nueva aplicación: Work → especificación versionada → Codex;
  - aplicación existente: Codex en solo lectura → Work valida y completa → Codex reconcilia → flujo incremental normal;
- definición adaptativa de requisitos y arquitectura;
- planificación e implementación incremental;
- trazabilidad y comprobación de preparación;
- un perfil tecnológico de referencia completamente probado:
  - backend Python con FastAPI;
  - frontend React;
  - base de datos PostgreSQL;
  - identidad con Keycloak;
- capacidad de documentar y evaluar alternativas sin prometer generación automatizada completa para todas ellas.
- ayuda autoexplicativa, onboarding progresivo y orientación contextual para personas con distinto conocimiento de SDD, Work y Codex;

En una aplicación existente, la v1 puede inventariar y documentar cualquier pila que Codex pueda analizar de forma segura. La generación, refactorización o normalización automatizada solo se considera homologada para perfiles tecnológicos que dispongan de contrato, plantillas y evals aprobadas.

### 4.3 Fuera del alcance de la primera versión

- Compatibilidad automatizada con cualquier combinación tecnológica.
- Agentes especializados por disciplina.
- MCP, conectores o una interfaz visual propia.
- Integración en vivo con Jira, GitHub, GitLab, catálogos internos o CI/CD.
- Clonado, autenticación o administración de repositorios remotos: la v1 trabaja sobre una copia local ya disponible; GitHub o GitLab son únicamente procedencia registrada.
- Despliegues automáticos en producción.
- Creación de cuentas, secretos o infraestructura corporativa.
- Verificación de jerarquías o aprobaciones organizativas.
- Sustitución de especialistas de producto, UX, arquitectura, seguridad o legal.
- Migración automática de proyectos entre versiones de LKS-SDD.
- Reorganización, refactorización o modernización automática de aplicaciones existentes durante su adopción.
- Certificación automática de cumplimiento por el mero hecho de generar una baseline documental.
- Deducción definitiva de objetivos, reglas de negocio o requisitos únicamente a partir del código.
- Gestión integral de incidencias y operación.
- Soporte del plugin en superficies que actualmente no admiten plugins, como la extensión IDE.

Estas capacidades podrán incorporarse posteriormente si aportan valor demostrado.

## 5. Modelo operativo Work–Codex

### 5.1 Papel de ChatGPT Work

Work es el espacio principal para:

- comprender el objetivo de la aplicación;
- explorar usuarios, necesidades y flujos;
- delimitar el alcance incluido y excluido;
- identificar supuestos, restricciones, integraciones y riesgos;
- definir requisitos funcionales y no funcionales;
- concretar criterios de aceptación;
- formular y comparar alternativas técnicas;
- proponer arquitectura y pila tecnológica;
- registrar decisiones explícitas;
- planificar incrementos y estrategia de pruebas;
- mantener los borradores y evaluar su suficiencia.
- en aplicaciones existentes, validar propósito, usuarios, reglas de negocio y comportamiento deseado que el código no puede demostrar;
- resolver con la persona usuaria contradicciones entre código, documentación y declaraciones.

### 5.2 Papel de Codex

Codex es el espacio principal para:

- en aplicaciones existentes, realizar primero una inspección técnica estricta y de solo lectura;
- construir un inventario y una arquitectura `as-is` con fuentes, revisión y limitaciones;
- leer la baseline documental aprobada;
- comprobar que el incremento solicitado está preparado;
- crear la estructura de código correspondiente al perfil confirmado;
- implementar un incremento sin ampliar su alcance;
- crear y ejecutar pruebas;
- realizar verificaciones técnicas y visuales cuando proceda;
- actualizar trazabilidad, decisiones y evidencias;
- detectar divergencias entre especificación y código;
- preparar un candidato verificable para entrega.

### 5.3 Ruta para una aplicación nueva

1. Se crea o selecciona el repositorio local de la aplicación.
2. Se crea un proyecto ChatGPT local asociado a esa carpeta.
3. En Work se invoca LKS-SDD para definir objetivo, alcance, requisitos, arquitectura y planificación.
4. Cuando un incremento supera su puerta de preparación, Codex lo implementa y verifica en el mismo repositorio.
5. Los documentos, el estado, el código y las evidencias evolucionan juntos.

### 5.4 Ruta para una aplicación existente

1. Se trabaja sobre un checkout local del repositorio vigente; no se duplica la aplicación para crear otro «proyecto LKS-SDD».
2. Codex realiza un **preflight y descubrimiento estricto de solo lectura**, con raíz y alcance confirmados.
3. Presenta fuera del repositorio una baseline técnica provisional que separa observaciones, inferencias, contradicciones y desconocidos. En esta fase no crea archivos en el repositorio.
4. Work recibe ese informe mediante el proyecto local o una transferencia explícita, valida el propósito, los procesos, las reglas y el comportamiento deseado, y pregunta únicamente por lo que las fuentes no demuestran.
5. Codex reconcilia la intención confirmada con el estado observado, registra brechas y fija la baseline a una revisión concreta del repositorio.
6. La persona usuaria elige una estrategia: solo documental, normalización progresiva o modernización planificada.
7. Codex muestra la estructura, el diff y las colisiones previstas. Tras confirmación, materializa de forma aditiva el espacio documental LKS-SDD, normalmente en una rama o worktree de adopción.
8. Las mejoras futuras pasan al mismo flujo incremental de definición, preparación, implementación y verificación.

El recorrido inverso inicial **Codex → Work → Codex** es una excepción de arranque para obtener y validar la baseline de una aplicación existente. Después de adoptarla, rige el flujo normal.

Una rama o worktree es una medida de aislamiento y revisión, no un nuevo producto ni una copia lógica de la aplicación. Si se utiliza un worktree, la carpeta activa del proyecto local debe ser la que reciba las modificaciones autorizadas.

### 5.5 Contrato de continuidad y topología

El contrato entre Work y Codex son los archivos del repositorio. El flujo preferente utiliza un proyecto local en la aplicación de escritorio vinculado a la carpeta del desarrollo.

La relación por defecto es:

**un plugin LKS-SDD corporativo → muchos proyectos ChatGPT locales → un repositorio y estado aislados por aplicación**.

El repositorio de desarrollo del propio plugin LKS-SDD constituye otro proyecto independiente. No se mezcla con los repositorios que consumen el estándar.

Para una aplicación compuesta por varios repositorios, la v1 exige declarar un repositorio coordinador y el alcance exacto de cada fuente. El soporte multi-repositorio plenamente automatizado queda fuera de la primera versión.

Se deben contemplar estas limitaciones:

- un proyecto ordinario de ChatGPT no proporciona por sí mismo acceso directo a una carpeta local;
- Codex CLI utiliza su directorio de trabajo y no la vista de Projects;
- la extensión IDE no admite actualmente plugins;
- si Work no puede escribir en la carpeta, se utilizará una exportación o sincronización explícita de los artefactos antes del traspaso a Codex.
- GitHub y GitLab no requieren lógicas diferentes en la v1: Codex trabaja sobre el checkout local y no gestiona autenticación, permisos ni operaciones remotas.

`AGENTS.md` guía a Codex dentro del repositorio, pero no sustituye las instrucciones y skills que guían a Work.

## 6. Ciclo de vida

### 6.1 Dos rutas de entrada

La fase 0 clasifica el proyecto y selecciona una ruta. Ninguna se elige implícitamente cuando ya existe código.

| Ruta | Fase | Entorno principal | Resultado | Puerta de salida |
|---|---|---|---|---|
| Nueva | N0. Inicio | Work | Proyecto, riesgo, complejidad, versión y profundidad documental | Modo `new` confirmado |
| Existente | E0. Encuadre seguro | Persona usuaria y Codex | Raíz, alcance, estado productivo, exclusiones y permisos de inspección | Preflight confirmado |
| Existente | E1. Arqueología técnica | Codex, solo lectura | Inventario, arquitectura observada, fuentes, revisión, incertidumbres y cobertura | Informe técnico revisable |
| Existente | E2. Validación funcional | Work | Propósito, usuarios, reglas, comportamiento esperado y prioridades confirmados | Intención suficientemente validada |
| Existente | E3. Reconciliación | Codex | Coincidencias, brechas, contradicciones, desconocidos, riesgos y desviaciones | Baseline reconciliada |
| Existente | E4. Estrategia de adopción | Work y persona usuaria | Estrategia y límites confirmados | Materialización autorizable |
| Existente | E5. Materialización | Codex, tras autorización | Espacio documental aditivo y baseline adoptada | Sin colisiones ni cambios funcionales |

Las dos rutas convergen en el ciclo común siguiente:

| Fase | Entorno principal | Resultado | Puerta de salida |
|---|---|---|---|
| 1. Descubrimiento y alcance | Work | Objetivo, usuarios, problema, valor, alcance, exclusiones, restricciones, supuestos y éxito | Alcance suficientemente entendido |
| 2. Especificación | Work | Flujos, requisitos, datos, integraciones, cualidades y criterios de aceptación | Información suficiente para diseñar |
| 3. Diseño técnico | Work | Alternativas, propuesta razonada, arquitectura, pila, identidad, datos, infraestructura y ADR | Baseline técnica confirmada |
| 4. Planificación | Work | Incrementos verticales, dependencias, riesgos, pruebas y definición de terminado | Incremento preparado para Codex |
| 5. Implementación | Codex | Código, configuración, pruebas y documentación del incremento | Implementación completada |
| 6. Verificación y entrega | Codex con revisión humana | Evidencias de aceptación, calidad, seguridad, accesibilidad, rendimiento, despliegue y reversión | Incremento verificado o candidato a entrega |
| 7. Operación y evolución | Work y Codex | Feedback, incidencias, deuda, nuevas decisiones, cambios de alcance, deriva de baseline y retirada | Nueva iteración o cierre |

En una aplicación adoptada, las fases 1 a 4 se aplican al siguiente incremento o cambio, utilizando la baseline como contexto; no obligan a redefinir desde cero toda la aplicación.

### 6.2 Estados de una puerta

Toda puerta produce uno de estos resultados:

- **Listo:** no existen bloqueos conocidos para el alcance evaluado.
- **Listo con pendientes no bloqueantes:** el incremento puede continuar y los pendientes quedan registrados.
- **Bloqueado para el alcance afectado:** faltan decisiones o evidencias indispensables para una parte concreta.

Un bloqueo no debe paralizar trabajo independiente.

### 6.3 Reapertura, cambio y deriva

Una fase puede reabrirse. Cuando cambia una decisión, LKS-SDD realiza análisis de impacto sobre requisitos, arquitectura, planificación, implementación y pruebas antes de actualizar la baseline.

En una aplicación existente, si el repositorio cambia después de la revisión registrada, la baseline pasa a estado `stale` hasta comprobar el impacto. Esto no invalida todo el conocimiento, pero impide presentar como actuales las observaciones afectadas.

### 6.4 Estrategias de adopción

La estrategia puede aplicarse a toda la aplicación o variar por componente, siempre de forma explícita:

1. **Solo documental.** Comprender y gobernar el sistema sin modificarlo. La salida es una baseline reconciliada, con riesgos, desviaciones, desconocidos y un punto de entrada para futuras mejoras. No implica homologación.
2. **Normalización progresiva.** Mantener la arquitectura existente y aplicar las convenciones LKS-SDD únicamente al código que se toca. Exige límites, regla de no empeorar, deuda heredada visible, pruebas de caracterización o regresión y un primer incremento reversible. No permite una refactorización transversal encubierta.
3. **Modernización planificada.** Separar arquitectura `as-is` y `to-be` y definir una transición. Exige motivación de negocio, coexistencia o sustitución, contratos, migración de datos, compatibilidad, despliegue, reversión, observabilidad y retirada. Su ejecución queda fuera del bootstrap de adopción y se divide en incrementos explícitos.

Elegir una estrategia no autoriza a ejecutarla. Cada cambio posterior supera sus puertas de definición, preparación, implementación y verificación.

## 7. Comportamiento conversacional

La experiencia debe ser una conversación continua con LKS-SDD, no un cuestionario rígido ni una secuencia de comandos que el usuario tenga que memorizar.

En cada interacción, la skill de definición debe:

1. leer el estado vigente del proyecto;
2. interpretar la nueva información sin inventar hechos;
3. clasificarla correctamente;
4. detectar vacíos, ambigüedades, contradicciones y riesgos;
5. actualizar únicamente los artefactos afectados;
6. mostrar un resumen breve de los cambios;
7. formular entre una y tres preguntas de mayor impacto;
8. explicar por qué son necesarias;
9. permitir responder, diferir, marcar como no aplicable o cerrar el nivel de detalle;
10. indicar el siguiente paso recomendado.

### 7.1 Evaluación de suficiencia

Cada dimensión se califica como:

- **Desconocida**.
- **Parcial**.
- **Suficiente para el alcance o incremento actual**.
- **No aplicable**, con justificación.

No se utilizarán porcentajes globales de madurez que produzcan una falsa sensación de precisión.

### 7.2 Órdenes naturales que debe comprender

- Iniciar o reanudar LKS-SDD.
- Mostrar el estado actual.
- Mostrar vacíos y decisiones pendientes.
- Revisar el alcance para evitar ampliaciones.
- Proponer alternativas técnicas.
- Cambiar una decisión y analizar su impacto.
- Cerrar una fase con el nivel de detalle actual.
- Evaluar si un incremento está preparado para Codex.
- Implementar el incremento aprobado.
- Verificar el incremento y mostrar evidencias.
- Adoptar una aplicación existente sin modificarla todavía.
- Inventariar este repositorio en modo de solo lectura.
- Mostrar qué está observado, inferido, contradicho o todavía desconocido.
- Comparar la baseline documentada con el estado actual del repositorio.
- Elegir entre adopción documental, normalización progresiva o modernización planificada.

La activación automática de skills es una comodidad. No será una dependencia: al iniciar un nuevo chat o cambiar de fase se recomendará invocar explícitamente LKS-SDD.

### 7.3 Conversación adaptativa en adopción

Antes de inspeccionar, LKS-SDD confirma en una tanda breve:

- si la aplicación está en producción;
- qué repositorio, módulo y carpetas forman parte del alcance;
- si el objetivo es documentar, normalizar progresivamente o estudiar una modernización;
- si se autoriza solo análisis estático o si más adelante podrán proponerse ejecuciones controladas;
- qué fuentes existentes son relevantes;
- qué datos, secretos, rutas o componentes deben excluirse.

Después del inventario, Work no repite preguntas técnicas ya observadas. Prioriza propósito, usuarios, procesos críticos, reglas de negocio, comportamiento que debe preservarse, obligaciones, problemas conocidos y la fuente que debe prevalecer ante cada contradicción concreta.

## 8. Modelo de información

### 8.1 Tipos de información

- **Hecho:** condición verificable, con fuente y fecha cuando sea relevante.
- **Objetivo:** resultado que el proyecto pretende conseguir.
- **Requisito:** necesidad confirmada, inequívoca y comprobable.
- **Restricción:** límite externo que condiciona la solución.
- **Propuesta:** alternativa sugerida por LKS-SDD; nunca equivale a decisión.
- **Decisión:** elección confirmada explícitamente por la persona usuaria.
- **Supuesto:** premisa provisional pendiente de comprobación.
- **Punto abierto:** información ausente, con impacto y dependencias.
- **Riesgo:** evento incierto con probabilidad, impacto y tratamiento.
- **Evidencia:** resultado verificable que demuestra una comprobación.

### 8.2 Procedencia, confianza y temporalidad

Cada afirmación relevante de una aplicación existente registra tres ejes separados:

- **Naturaleza:** observación técnica, declaración humana, requisito deseado, inferencia, contradicción o desconocido.
- **Fuente:** código, configuración, esquema o migración, prueba, contrato API, documentación, historial, telemetría autorizada, ticket o declaración.
- **Vigencia:** revisión del repositorio, fecha y alcance para los que la afirmación fue comprobada.

Estados normalizados de procedencia:

- `observed_in_code`: observado directamente en código o configuración.
- `observed_in_test`: demostrado únicamente por una prueba o evidencia ejecutada.
- `documented_unverified`: descrito en documentación, pero no verificado en la implementación.
- `user_confirmed`: confirmado como intención o requisito por la persona usuaria.
- `inferred`: deducido a partir de fuentes; incluye justificación y confianza alta, media o baja.
- `unknown`: no existe evidencia suficiente.
- `contradictory`: dos o más fuentes discrepan y todavía no se ha resuelto cuál prevalece.

La confianza se aplica a una inferencia concreta, nunca como puntuación global de «comprensión». Repetir una inferencia no aumenta su confianza. La ausencia de evidencia se registra como desconocido, no como ausencia funcional.

Una evidencia técnica incluye, cuando proceda: revisión del repositorio, ruta relativa y símbolo o sección, herramienta y versión, entorno saneado, fecha, resultado, limitaciones y política de redacción o retención. No se copian secretos ni logs productivos completos.

### 8.3 Identificadores estables

Se utilizarán identificadores inmutables:

- `OBJ-###`: objetivos.
- `RF-###`: requisitos funcionales.
- `RNF-###`: requisitos no funcionales.
- `RT-###`: requisitos o restricciones técnicas.
- `ADR-###`: decisiones arquitectónicas.
- `CA-###`: criterios de aceptación.
- `INC-###`: incrementos.
- `TST-###`: pruebas.
- `EVD-###`: evidencias.
- `OBS-###`: observaciones del estado actual.
- `DISC-###`: discrepancias entre fuentes o entre `as-is` y `to-be`.
- `RSK-###`: riesgos.
- `OPEN-###`: puntos abiertos.

Los identificadores retirados no se reutilizan.

### 8.4 Trazabilidad mínima

La cadena obligatoria es:

**requisito → criterio de aceptación → decisión o arquitectura relevante → incremento → prueba → evidencia**

No se exigirá trazabilidad hasta líneas concretas de código. Cuando aporte valor, el incremento podrá enlazar componentes o módulos.

En adopción, la cadena adicional es:

**fuente y revisión → observación o inferencia → validación o discrepancia → decisión de conservar, cambiar o retirar → incremento futuro**

## 9. Artefactos del proyecto

### 9.1 Topología corporativa y aislamiento

```text
Repositorio corporativo de LKS-SDD
└── plugin publicado en el workspace de LKS
    ├── método, skills, plantillas, perfiles y validadores
    ├── Proyecto local de aplicación A → repositorio A + estado A
    ├── Proyecto local de aplicación B → repositorio B + estado B
    └── Proyecto local de aplicación C → repositorio C + estado C
```

La publicación es canónica, aunque cada persona o superficie pueda necesitar habilitar o instalar el plugin según los controles del workspace. El plugin no se copia dentro de cada aplicación y no incorpora:

- documentación o código de clientes;
- manifiestos de proyectos consumidores;
- cachés, índices, fixtures o logs con contenido de aplicaciones;
- telemetría con contenido sustantivo de proyectos;
- decisiones heredadas de otro repositorio.

Todo estado específico usa rutas relativas bajo la raíz autorizada del proyecto. El identificador puede ser seudónimo y no necesita incluir el nombre del cliente.

### 9.2 Estructura lógica estándar

```text
mi-aplicacion/
├── .lks-sdd/
│   └── project.json
├── README.md
├── AGENTS.md
├── docs/
│   └── lks-sdd/
│       ├── 00-estado-proyecto.md
│       ├── 01-contexto-y-alcance.md
│       ├── 02-requisitos-funcionales.md
│       ├── 03-requisitos-no-funcionales.md
│       ├── 04-requisitos-tecnicos.md
│       ├── 05-arquitectura.md
│       ├── 06-modelo-datos.md
│       ├── 07-seguridad-identidad.md
│       ├── 08-plan-desarrollo.md
│       ├── 09-criterios-aceptacion.md
│       ├── 10-plan-pruebas.md
│       ├── 11-operacion-despliegue.md
│       ├── trazabilidad.md
│       └── decisiones/
│           └── ADR-###-titulo.md
└── estructura de código, pruebas e infraestructura
    └── creada después de confirmar la arquitectura
```

En una aplicación existente, la estructura previa se conserva. Tras la autorización de materialización se añade, cuando proceda:

```text
docs/lks-sdd/
└── current-state/
    ├── inventario.md
    ├── arquitectura-as-is.md
    ├── evidencia.md
    ├── reconciliacion.md
    ├── desviaciones-y-riesgos.md
    └── estrategia-adopcion.md
```

El estado actual (`as-is`) y el estado deseado (`to-be`) nunca se mezclan en una misma afirmación. La materialización no sustituye `README.md`, `AGENTS.md` ni documentación existente. Si ya existe `AGENTS.md`, LKS-SDD propone una integración mínima como cambio independiente y pide confirmación específica.

### 9.3 Núcleo y anexos

Todos los conceptos anteriores forman el modelo canónico, pero no todos necesitan un archivo separado en todos los proyectos.

Núcleo mínimo:

- estado e índice;
- contexto y alcance;
- requisitos y criterios de aceptación;
- arquitectura y decisiones;
- plan de entrega;
- trazabilidad.

Anexos creados según necesidad:

- experiencia de usuario y accesibilidad;
- datos y migración;
- APIs e integraciones;
- seguridad, privacidad e identidad;
- infraestructura, despliegue y operación;
- estrategia de pruebas;
- costes, licencias y regulación.

LKS-SDD podrá usar una estructura compacta, estándar o ampliada según el riesgo, manteniendo siempre el mismo modelo lógico.

### 9.4 Markdown estructurado

Los documentos son Markdown legible por personas, con metadatos YAML para permitir comprobaciones deterministas. Ejemplo:

```yaml
---
artifact_type: functional-requirements
schema_version: "1.0"
lks_sdd_method_version: "1.0.0"
created_with_plugin_version: "0.1.0"
project_id: "proyecto-ejemplo"
status: draft
last_updated: "AAAA-MM-DD"
---
```

Las plantillas:

- no pueden considerar completo un archivo vacío;
- admiten `no_aplica` con justificación;
- preservan el texto adaptado por el equipo;
- incluyen ejemplos ficticios sin datos sensibles;
- especifican criterios de calidad para cada sección.

### 9.5 Manifiesto de control del proyecto

`.lks-sdd/project.json` es un índice operativo, no una segunda fuente de verdad para requisitos o decisiones. Registra:

- versión del plugin, esquema y perfiles;
- tipo y nivel documental del proyecto;
- fase actual;
- identificador de la baseline vigente;
- rutas de los artefactos;
- perfiles propuestos y seleccionados;
- incremento activo;
- bloqueos y estado de preparación;
- modo de entrada: `new` o `adopt-existing`;
- versión del método creada y última versión del plugin que lo validó;
- rango compatible del plugin y versiones de perfiles;
- tipo de control de versiones y origen `github`, `gitlab`, `other` o `none`, sin credenciales ni URL sensible;
- alcance de la raíz y, en adopción, revisión, rama y estado limpio o sucio inventariados;
- estado de adopción, estrategia, cobertura de evidencias y vigencia de la baseline;
- alcance de escritura documental autorizado.

Estados mínimos de adopción:

`inventory_pending` → `inventory_complete` → `business_validation_pending` → `reconciliation_pending` → `confirmation_pending` → `materialization_pending` → `materialized`.

Si la revisión o el estado del repositorio cambian, la materialización se detiene y la baseline se marca `stale` hasta actualizar el análisis.

El contenido sustantivo continúa en Markdown. Una discrepancia entre el manifiesto y los documentos provoca un error de validación; nunca se resuelve con una sobrescritura silenciosa.

## 10. Calidad de los artefactos

### 10.1 Requisitos

Cada requisito debe ser:

- atómico;
- inequívoco;
- necesario;
- priorizado;
- comprobable;
- trazable;
- compatible con el alcance declarado.

Los requisitos no funcionales deben incluir umbrales o condiciones observables. Expresiones como «rápido», «seguro», «escalable» o «intuitivo» no se consideran suficientes sin concreción.

### 10.2 Decisiones arquitectónicas

Cada ADR contiene:

- contexto;
- alternativas consideradas;
- propuesta inicial, si la hubo;
- decisión confirmada;
- razones;
- consecuencias positivas y negativas;
- riesgos y medidas;
- relaciones con requisitos;
- estado y relaciones `supersedes` o `superseded_by`.

### 10.3 Propuestas tecnológicas

Toda propuesta debe incluir:

- adecuación a los requisitos;
- compatibilidad con otras piezas;
- costes y restricciones;
- riesgos;
- impacto operativo;
- nivel de soporte LKS-SDD;
- alternativa razonable.

### 10.4 Baseline de una aplicación existente

Una baseline `as-is` de calidad:

- declara raíz, revisión, estado y alcance inspeccionados;
- diferencia arquitectura observada y arquitectura deseada;
- enlaza cada afirmación con su procedencia;
- separa observaciones, inferencias, contradicciones y desconocidos;
- registra exclusiones, zonas no inspeccionadas y límites de cobertura;
- no interpreta la existencia de código como requisito aprobado;
- no presenta la documentación generada como certificación de conformidad;
- permite reproducir o revisar la evidencia sin exponer información sensible.

## 11. Perfiles tecnológicos

### 11.1 Composición

La pila se compone por dimensiones:

- frontend;
- backend;
- datos;
- identidad;
- integración;
- infraestructura y despliegue;
- pruebas;
- observabilidad.

No se permitirán combinaciones arbitrarias sin evaluación. Una matriz de compatibilidad indicará qué composiciones están verificadas.

### 11.2 Niveles de soporte

- **Homologado y soportado:** dispone de responsable, versiones admitidas, compatibilidades, reglas de seguridad, plantilla ejecutable, pruebas y política de retirada.
- **Reconocido con guía:** puede seleccionarse y tiene orientación documental, pero su generación no está completamente automatizada o verificada.
- **Experimental:** puede evaluarse en un contexto controlado con riesgos explícitos.
- **Fuera del estándar:** requiere registrar una desviación.

### 11.3 Pila preferente

FastAPI, React, PostgreSQL y Keycloak forman la línea base preferente inicial. LKS-SDD solo la propondrá después de comprobar su encaje con los requisitos. La persona usuaria debe confirmarla.

Angular, Vue, otros backends, otras bases de datos, Cognito y Entra ID forman parte de la arquitectura objetivo de perfiles. No se declararán homologados hasta contar con guías, scaffolding, compatibilidad y pruebas reales.

### 11.4 Desviaciones

Elegir un perfil alternativo homologado no es una excepción. Usar una tecnología no homologada genera un registro de desviación con:

- motivo;
- alcance;
- riesgos;
- medidas compensatorias;
- impacto de mantenimiento;
- fecha de revisión;
- plan de salida o normalización.

LKS-SDD registra la confirmación de la persona usuaria, pero no presume aprobación organizativa.

### 11.5 Capacidad documental y capacidad de implementación

El nivel de soporte se evalúa por capacidad, no únicamente por el nombre de la tecnología:

- **Documentable:** cualquier pila accesible que pueda describirse con evidencia suficiente.
- **Analizable genéricamente:** estructura, dependencias, contratos y riesgos observables sin ejecutar el proyecto.
- **Implementable con garantía LKS-SDD:** solo perfiles probados, versionados y con evals aprobadas.
- **Normalizable o modernizable con garantía:** solo transformaciones concretas que dispongan de contrato, fixtures, pruebas y reversión verificadas.

Una aplicación existente con tecnología no homologada puede adoptar toda la capa documental y de gobierno. Esto no obliga a migrarla ni autoriza a presentar la generación o refactorización como homologadas.

## 12. Arquitectura del plugin

### 12.1 Forma de la primera versión

La primera versión será un plugin basado en skills, plantillas, referencias y scripts locales. No incluirá MCP, conectores, UI, hooks ni agentes especializados.

```text
lks-sdd/
├── .codex-plugin/
│   └── plugin.json
├── README.md
├── CHANGELOG.md
├── GOVERNANCE.md
├── SECURITY.md
├── skills/
│   ├── lks-sdd-define/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   └── templates/
│   │   ├── references/
│   │   │   ├── metodo.md
│   │   │   ├── modelo-calidad.md
│   │   │   └── technology-profiles/
│   │   └── scripts/
│   │       └── init_project.py
│   ├── lks-sdd-adopt-existing/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   └── current-state-templates/
│   │   ├── references/
│   │   │   └── adoption-contract.md
│   │   └── scripts/
│   │       ├── inspect_repository.py
│   │       ├── validate_adoption.py
│   │       └── materialize_adoption.py
│   ├── lks-sdd-assess-readiness/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── readiness-rubric.md
│   │   └── scripts/
│   │       └── validate_spec.py
│   ├── lks-sdd-implement/
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   │   └── scaffolds/
│   │   └── references/
│   │       └── implementation-contract.md
│   ├── lks-sdd-verify/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── verification-contract.md
│   │   └── scripts/
│   │       └── check_traceability.py
│   └── lks-sdd-help/
│       ├── SKILL.md
│       ├── assets/
│       │   ├── quickstart.md
│       │   ├── guided-tour.md
│       │   └── prompt-examples.md
│       └── references/
│           ├── sdd-concepts.md
│           ├── lks-sdd-capabilities.md
│           ├── work-codex-guide.md
│           ├── project-lifecycle.md
│           ├── glossary.md
│           ├── faq.md
│           ├── troubleshooting.md
│           └── product-reality.md
├── tests/
│   ├── evals/
│   └── fixtures/
└── assets/
    ├── icon.png
    └── logo.png
```

Las plantillas y referencias funcionales viven dentro de la skill que las utiliza. Los recursos gráficos del plugin se reservan en `assets/` de raíz.

Los contratos comunes podrán empaquetarse como recursos compartidos únicamente si la validación del plugin demuestra que todas las skills los resuelven de forma portable. Cada skill seguirá siendo autocontenida respecto de su disparador, sus permisos, sus entradas y su criterio de éxito.

### 12.2 Manifest mínimo

```json
{
  "name": "lks-sdd",
  "version": "0.1.0",
  "description": "Método LKS para aprender, definir, adoptar, implementar y verificar aplicaciones web con ChatGPT Work y Codex.",
  "skills": "./skills/"
}
```

La implementación final añadirá únicamente los metadatos admitidos por el esquema vigente. No se incluirán referencias a MCP o apps mientras esos componentes no existan.

## 13. Catálogo de skills de la primera versión

La arquitectura utiliza seis workflows con intención, permisos y criterios de éxito diferenciados. No se crea una skill por documento ni una skill por tecnología.

### 13.1 `lks-sdd-define`

**Superficie principal:** ChatGPT Work.  
**Objetivo:** iniciar o reanudar la definición de una aplicación.

Responsabilidades:

- clasificar el proyecto;
- inicializar una aplicación nueva sin sobrescribir archivos existentes;
- detectar código preexistente y derivar explícitamente al modo de adopción;
- conducir la entrevista adaptativa;
- crear y mantener los Markdown;
- detectar vacíos y contradicciones;
- proponer alternativas y perfiles;
- registrar decisiones y pendientes;
- delimitar el alcance;
- planificar incrementos;
- preparar la revisión de madurez.

Restricción principal: no genera código de aplicación ni convierte propuestas en decisiones.

### 13.2 `lks-sdd-adopt-existing`

**Superficies:** Codex y Work, según el estado de la adopción.  
**Objetivo:** incorporar un repositorio existente a LKS-SDD sin alterar su comportamiento ni confundir implementación observada con intención.

Responsabilidades:

- confirmar la raíz, el alcance, el estado productivo, las exclusiones y los permisos;
- inventariar estáticamente código, configuración, documentación, pruebas, contratos y dependencias;
- registrar revisión, rama, estado limpio o sucio y cobertura;
- producir fuera del repositorio un informe provisional `as-is` con observaciones, inferencias, contradicciones y desconocidos;
- permitir a Work validar propósito, reglas, comportamiento deseado y prioridades;
- reconciliar `as-is`, documentación existente y `to-be` confirmado;
- detectar si el repositorio ha cambiado desde el inventario;
- registrar la estrategia de adopción y sus límites confirmados;
- presentar el diff documental previsto y las colisiones;
- materializar, solo tras autorización explícita, los artefactos LKS-SDD aditivos;
- dejar preparada la entrada al flujo incremental normal.

Restricciones principales:

- el descubrimiento no modifica archivos, ramas, índice, dependencias, configuración ni `.gitignore`;
- no ejecuta aplicación, builds, tests, contenedores, migraciones, gestores de paquetes ni hooks;
- no lee ni reproduce valores de secretos, `.env`, claves o certificados;
- no utiliza red ni accede a sistemas productivos;
- no sustituye `README.md` o `AGENTS.md` existentes;
- no modifica código durante la adopción;
- si la superficie no puede garantizar solo lectura, debe usarse una copia o snapshot aislado y declarar la limitación.

Una vez materializada la baseline, las nuevas necesidades pasan a `lks-sdd-define`, la preparación a `lks-sdd-assess-readiness` y cualquier cambio funcional a `lks-sdd-implement`.

### 13.3 `lks-sdd-assess-readiness`

**Superficies:** Work y Codex.  
**Objetivo:** evaluar si un incremento está preparado para pasar a implementación.

Comprueba:

- alcance del incremento;
- requisitos y criterios de aceptación vinculados;
- decisiones técnicas necesarias;
- datos, identidad e integraciones relevantes;
- estrategia de pruebas;
- contradicciones;
- puntos bloqueantes;
- trazabilidad estructural.

Produce un resultado listo, listo con pendientes o bloqueado para el alcance afectado. No genera código.

### 13.4 `lks-sdd-implement`

**Superficie principal:** Codex.  
**Objetivo:** implementar únicamente el siguiente incremento confirmado.

Responsabilidades:

- leer el estado y la baseline;
- validar la puerta de entrada;
- crear o adaptar la estructura de código del perfil seleccionado;
- implementar por incremento vertical;
- crear pruebas relevantes;
- mantener documentación y trazabilidad;
- detener únicamente las partes dependientes de una decisión crítica abierta;
- informar de desviaciones o cambios de alcance.
- rechazar la implementación sobre un proyecto `adopt-existing` cuya baseline no esté materializada o vigente.

### 13.5 `lks-sdd-verify`

**Superficie principal:** Codex.  
**Objetivo:** verificar el incremento y aportar evidencia.

Responsabilidades:

- ejecutar comprobaciones automáticas;
- validar criterios de aceptación;
- revisar calidad, seguridad, accesibilidad y rendimiento aplicables;
- comprobar trazabilidad;
- documentar resultados y limitaciones;
- clasificar el incremento como verificado, verificado con reservas o no verificado.

### 13.6 lks-sdd-help

**Superficies:** ChatGPT Work y Codex.  
**Objetivo:** enseñar el método y orientar a la persona usuaria sin modificar el proyecto ni iniciar una fase operativa de forma implícita.

Debe responder, entre otras, a estas intenciones:

- «¿Qué es SDD y qué aporta?».
- «¿Qué puede hacer LKS-SDD?».
- «¿Qué diferencia hay entre Work y Codex?».
- «¿Cómo empiezo una aplicación nueva?».
- «¿Cómo incorporo un repositorio existente?».
- «¿Dónde estoy y cuál es el siguiente paso?».
- «¿Por qué me está preguntando esto?».
- «¿Qué significa este estado, puerta, perfil o documento?».
- «Enséñame un ejemplo antes de tocar nada».
- «Tengo un problema utilizando el plugin».

Modos de ayuda:

- **respuesta breve:** explicación directa y un siguiente paso sugerido;
- **onboarding:** recorrido guiado de cinco a diez minutos;
- **guía contextual:** lectura opcional y no modificadora del manifiesto y de los artefactos del proyecto;
- **aprendizaje por ejemplo:** casos de aplicación nueva, adopción, implementación y verificación;
- **consulta de referencia:** conceptos, glosario, capacidades, límites y preguntas frecuentes;
- **resolución de problemas:** diagnóstico didáctico sin asumir que la persona conoce la terminología de ChatGPT.

Contrato didáctico:

- comenzar por el objetivo de la persona, no por la estructura interna del plugin;
- usar lenguaje claro y revelar detalle progresivamente;
- explicar por qué existe cada fase y qué riesgo evita;
- distinguir siempre SDD, LKS-SDD, ChatGPT Work, Codex, plugin, skill, proyecto ChatGPT y repositorio;
- ofrecer ejemplos concretos y prompts de inicio;
- indicar qué es estable en el método y qué depende de versión, superficie, configuración o permisos;
- no afirmar que una capacidad está disponible si la superficie actual no la confirma;
- enlazar, cuando sea útil, la referencia oficial o corporativa;
- terminar con una acción sugerida, no ejecutada.

La guía de realidad del producto registrará para cada afirmación dependiente de OpenAI:

- superficie;
- capacidad;
- estado conocido;
- fecha de verificación;
- fuente oficial;
- limitaciones;
- fallback cuando no esté disponible.

Restricciones:

- no crea ni modifica archivos;
- no cambia fases, puertas, estados o decisiones;
- no activa implementación, adopción o verificación por el mero hecho de explicarlas;
- no sustituye la documentación oficial de OpenAI ni presenta como permanente una característica que pueda evolucionar;
- no abruma con todo el método cuando basta una respuesta breve;
- no presupone experiencia previa.

Criterio de éxito: la persona entiende qué aporta LKS-SDD, en qué contexto se encuentra y qué opción puede escoger a continuación.

### 13.7 Activación

Las descripciones de las skills deben estar orientadas al objetivo del usuario y no solaparse. El modelo podrá activarlas de forma natural cuando la petición coincida, pero se recomienda invocación explícita al iniciar cada fase relevante.

Ejemplos:

> Utiliza LKS-SDD para definir esta aplicación. Todavía no generes código.

> Utiliza LKS-SDD para descubrir este repositorio existente en modo estricto de solo lectura. No crees archivos ni ejecutes el proyecto.

> Utiliza LKS-SDD para comprobar si el incremento está preparado para Codex.

> Utiliza LKS-SDD para implementar el incremento confirmado.

> Utiliza LKS-SDD para verificar el incremento y registrar evidencias.

> Explícame qué es LKS-SDD y cómo se trabaja con Work y Codex. No modifiques el proyecto.

> Utiliza la ayuda de LKS-SDD para decirme en qué fase está este proyecto y qué opciones tengo ahora.

No se presupone que una skill invoque determinísticamente a otra. Todas leen el estado persistido del proyecto y reconocen si deben iniciar, reanudar o rechazar una acción incompatible.

`lks-sdd-adopt-existing` se mantiene separada porque su régimen de permisos y su éxito —una baseline reconciliada y materializada sin cambio funcional— son distintos de definir una aplicación nueva. La descripción de cada skill evitará solapamientos semánticos.

La ayuda constituye un workflow independiente porque su resultado es comprensión y orientación, no producción o modificación de artefactos. Explicar una acción nunca equivale a autorizarla.

## 14. Scripts y automatización determinista

Los scripts de la primera versión serán Python multiplataforma, sin red ni dependencias externas, idempotentes y limitados a la carpeta del proyecto.

### 14.1 `init_project.py`

- Crea la estructura documental adecuada.
- No sobrescribe archivos existentes.
- Admite simulación o vista previa.
- Registra la versión del estándar.
- Puede reanudarse sin duplicar contenido.
- Se limita al modo `new`: si detecta un repositorio con una aplicación preexistente, no inicializa y deriva a `lks-sdd-adopt-existing`.

### 14.2 `inspect_repository.py`

- Realiza inventario estático dentro de la raíz validada.
- No sigue enlaces que salgan de esa raíz.
- No ejecuta código, builds, tests, contenedores, migraciones, gestores de paquetes ni hooks.
- No instala dependencias ni utiliza red.
- Excluye por defecto binarios, artefactos generados, dependencias vendorizadas y valores sensibles.
- Señala únicamente ruta y categoría de un posible secreto; nunca muestra su valor.
- Produce salida por consola o en una ubicación externa explícita durante el preflight.
- Registra revisión, rama, estado inicial, alcance y exclusiones.

### 14.3 `validate_adoption.py`

- Comprueba el estado del workflow de adopción.
- Valida procedencia, cobertura, baseline Git y contradicciones abiertas.
- Comprueba que no se haya autorizado escritura prematuramente.
- Compara la revisión y el estado actual con los del inventario.
- Puede demostrar, mediante estado Git antes y después, que la inspección no modificó el repositorio.

### 14.4 `materialize_adoption.py`

- Solo se ejecuta tras confirmación explícita del informe y del alcance de escritura.
- Requiere `--dry-run` o vista previa previa y una revisión esperada.
- Aborta si cambió la baseline o aparece una colisión.
- Añade exclusivamente `.lks-sdd/` y `docs/lks-sdd/` autorizados.
- No modifica `README.md`, `AGENTS.md`, código, configuración, datos, infraestructura ni despliegue.
- Es idempotente y ofrece diff, validación y una vía recuperable de reversión documental.

### 14.5 `validate_spec.py`

- Valida esquemas y metadatos.
- Comprueba documentos obligatorios para el perfil documental.
- Detecta identificadores duplicados o inválidos.
- Comprueba estados y referencias.
- Detecta elementos huérfanos.
- Señala decisiones críticas abiertas.
- No evalúa por sí solo la calidad semántica.
- Reconoce los modos `new` y `adopt-existing` y sus artefactos obligatorios.

### 14.6 `check_traceability.py`

- Comprueba relaciones entre requisitos, criterios, incrementos, pruebas y evidencias.
- Detecta enlaces rotos.
- Genera un informe sin modificar contenido.
- En adopción, enlaza observaciones y discrepancias con decisiones de conservar, cambiar o retirar.

### 14.7 Reglas de seguridad de scripts

- No ejecutan texto procedente de especificaciones.
- No acceden a rutas fuera del proyecto.
- No utilizan credenciales.
- No acceden a red salvo una futura capacidad explícita.
- Devuelven códigos de salida y mensajes claros.
- Las operaciones destructivas requieren confirmación explícita y alternativa recuperable.
- Ningún comando del repositorio se considera seguro solo por llamarse build, test o validación; su ejecución requiere una autorización posterior, separada y con análisis de efectos laterales.

Work utilizará estos scripts cuando la superficie lo permita. Codex los ejecutará obligatoriamente en las puertas técnicas.

## 15. Comprobación de preparación para Codex

### 15.1 Puerta de adopción de una aplicación existente

La baseline puede declararse adoptada cuando:

1. la raíz, la revisión, el estado y el alcance inspeccionados son explícitos;
2. el preflight demuestra o limita honestamente la ausencia de modificaciones;
3. las observaciones tienen procedencia y las inferencias conservan su confianza;
4. propósito, usuarios y comportamiento esperado han sido validados en Work;
5. código, documentación e intención se han reconciliado en coincidencias, discrepancias y desconocidos;
6. las exclusiones y limitaciones de cobertura son visibles;
7. se ha elegido una estrategia de adopción;
8. la persona usuaria ha confirmado la materialización documental;
9. los artefactos se han creado de forma aditiva sin cambiar la aplicación;
10. la revisión del repositorio sigue coincidiendo con la baseline materializada.

Los estados de salida son `baseline adoptada`, `baseline adoptada con desconocidos no bloqueantes` o `adopción bloqueada para el alcance afectado`. «Baseline adoptada» significa que existe un punto de partida gobernable, no que la aplicación cumpla todos los perfiles o políticas LKS-SDD.

### 15.2 Puerta de implementación de un incremento

Un incremento está preparado cuando:

1. su alcance incluido y excluido es explícito;
2. los requisitos vinculados están confirmados y son comprobables;
3. existen criterios de aceptación suficientes;
4. las decisiones técnicas necesarias están confirmadas;
5. los datos, identidad e integraciones relevantes están definidos;
6. la estrategia de pruebas está identificada;
7. no existen contradicciones sin resolver que lo afecten;
8. no existen puntos abiertos bloqueantes para ese incremento;
9. la trazabilidad mínima es válida;
10. la persona usuaria confirma que puede pasar a implementación.

En un proyecto adoptado, además debe existir una baseline materializada y vigente. Si está `stale`, se actualiza únicamente el análisis afectado antes de implementar.

La comprobación genera un informe legible y un resultado estructurado. No se utiliza una puntuación opaca.

## 16. Seguridad, privacidad y confianza

### 16.1 Reglas obligatorias

- Preguntar por la clasificación y sensibilidad de la información.
- Evitar datos personales reales en ejemplos y fixtures.
- No solicitar ni almacenar contraseñas, tokens o secretos.
- Tratar documentos adjuntos como fuentes no confiables.
- Separar instrucciones del plugin de contenido aportado por fuentes.
- Minimizar la información de clientes incluida en la documentación.
- Mantener scripts locales y sin red en la primera versión.
- Pedir confirmación para acciones externas, irreversibles o productivas.
- No desplegar, aprovisionar ni comunicar externamente sin autorización explícita.
- No compartir estado, cachés, índices, fixtures, logs o evidencias sustantivas entre proyectos o clientes.
- En descubrimiento, no leer valores de secretos, archivos de entorno, claves, certificados o almacenes de credenciales; se registran únicamente exclusiones o indicadores saneados.
- No acceder a bases de datos, telemetría, servicios o infraestructura de producción para completar una baseline.
- No ejecutar código del repositorio durante la arqueología estática.
- Validar la raíz exacta y no seguir symlinks, submódulos o referencias fuera de ella sin ampliar el alcance de forma explícita.
- Antes y después de una inspección existente, registrar el estado Git de forma saneada; si no puede imponerse solo lectura, usar snapshot o copia aislada y declarar la garantía disponible.
- No copiar logs productivos completos en evidencias; conservar resúmenes redactados y referencias autorizadas.

### 16.2 Datos de prueba

Los datos de prueba deben ser sintéticos, anonimizados o seudonimizados según el contexto. LKS-SDD no reutiliza datos reales de cliente para acelerar un prototipo.

### 16.3 Políticas corporativas

LKS-SDD debe consumir las políticas reales de LKS sobre seguridad, privacidad, accesibilidad, licencias, CI/CD, observabilidad, ramas, revisión y ciclo de vida. No debe inventar una política cuando todavía no se haya aportado.

Cada referencia corporativa incluirá propietario, fecha de vigencia, versión y nivel normativo `MUST`, `SHOULD` o `MAY`.

## 17. Gobierno y evolución

### 17.1 Gobierno del plugin

Aunque LKS-SDD no gestiona quién aprueba un proyecto, el propio estándar necesita:

- propietario del método;
- mantenedores del plugin;
- responsables de perfiles tecnológicos;
- revisión de seguridad y privacidad;
- persona administradora encargada de publicar en el workspace;
- canal de soporte;
- calendario de revisión y política de retirada.

Los nombres concretos se asignarán antes del piloto.

### 17.2 Proceso de cambio

1. Propuesta de cambio en Work.
2. Motivación y alcance.
3. Análisis de impacto y compatibilidad.
4. Decisión explícita.
5. Implementación en Codex.
6. Validaciones, pruebas y evals.
7. Revisión del diff y documentación.
8. Publicación controlada.
9. Observación durante el piloto.
10. Promoción, corrección o retirada.

LKS-SDD aplicará este mismo método a su propia evolución.

### 17.3 Versionado

- Versión editorial de esta definición funcional y arquitectónica.
- SemVer para el paquete del plugin.
- Versión del método LKS-SDD aplicada a cada proyecto.
- Versión independiente para el esquema documental.
- Versión independiente para cada perfil tecnológico.
- Registro de versiones en cada proyecto.
- Changelog con cambios, compatibilidad y migración.
- Período de deprecación para capacidades retiradas.

El ejemplo de esta definición usa `definition_version: 1.1`, `plugin_version: 0.1.0`, `method_version: 1.0.0` y `schema_version: 1.0`; son ejes distintos y no deben sincronizarse por coincidencia numérica.

Cada release publica una matriz acotada de compatibilidad. Una versión nueva debe leer las versiones declaradas como soportadas, ofrecer análisis de solo lectura para diagnosticar otras o proponer una migración. No se promete compatibilidad indefinida.

La migración requiere copia o rama, vista previa, backup, diff, validación, confirmación y rollback; nunca sobrescribe silenciosamente texto adaptado ni cambia la semántica de un proyecto por el mero hecho de actualizar el plugin.

## 18. Distribución dentro de LKS

### 18.1 Desarrollo y piloto

- Desarrollo desde un marketplace personal o de repositorio.
- Validación estructural del plugin.
- Piloto con un grupo reducido de desarrolladores.
- Proyectos representativos y datos no sensibles: al menos una aplicación nueva y una existente en copia o entorno no productivo.
- Registro de incidencias, activaciones incorrectas y carga documental.
- Prueba explícita de que una misma publicación del plugin sirve a varios proyectos sin trasladar estado ni contenido entre ellos.

### 18.2 Publicación interna

Una persona administradora del workspace publica el plugin y limita el acceso a los roles seleccionados. La publicación interna permanece dentro del límite organizativo y no equivale a publicación pública.

«Un único plugin corporativo» significa una distribución y versión canónicas. La habilitación concreta puede depender de los controles de cada persona o superficie. Cada proyecto registra la versión aplicada y una actualización del plugin nunca modifica automáticamente sus artefactos.

### 18.3 Ampliación

La disponibilidad general se produce después de verificar:

- utilidad real;
- calidad de los artefactos;
- continuidad Work–Codex;
- seguridad;
- soporte operativo;
- capacidad de mantenimiento;
- éxito del perfil tecnológico inicial.
- éxito del modo de adopción sin cambios funcionales ni fuga de contexto entre proyectos.

## 19. Pruebas y evals del propio plugin

### 19.1 Pruebas estructurales

- Manifest válido.
- Skills válidas y autocontenidas.
- Rutas y recursos empaquetados.
- Scripts idempotentes.
- Inicialización sin sobrescritura.
- Validación de esquemas e identificadores.
- Instalación desde marketplace de desarrollo.
- Inspección de un repositorio existente sin cambio en árbol, contenido, índice o estado Git.
- Materialización aditiva con dry-run, detección de colisiones y revisión esperada.
- Aislamiento de estado entre al menos dos proyectos consumidores.
- Compatibilidad con fixtures de proyecto nuevo, proyecto adoptado y versión anterior soportada.

### 19.2 Escenarios de eval mínimos

- Pregunta abierta sobre qué es SDD y qué valor aporta.
- Persona sin experiencia que solicita un recorrido de inicio.
- Comparación didáctica entre Chat, Work y Codex sin prometer capacidades no verificadas.
- Pregunta contextual sobre fase, puerta, pendientes y siguiente paso.
- Solicitud de ejemplo antes de modificar el proyecto.
- Consulta de ayuda que no debe iniciar otra skill ni escribir archivos.
- Explicación breve frente a explicación profunda según la petición.
- Capacidad dependiente de superficie o versión que requiere advertencia y fuente vigente.
- Problema de uso que debe derivarse a troubleshooting sin culpar a la persona.
- Activación explícita.
- Activación natural correcta.
- Petición que no debe activar LKS-SDD.
- Idea inicial ambigua.
- Requisitos contradictorios.
- Petición prematura de código.
- Aceptación del perfil preferente.
- Rechazo justificado del perfil preferente.
- Selección de una alternativa homologada.
- Desviación no homologada.
- Decisión crítica pendiente.
- Bloqueo que no afecta a otro incremento.
- Cambio de una decisión ya confirmada.
- Solicitud de cerrar deliberadamente el nivel de detalle.
- Reanudación en un chat nuevo.
- Proyecto con una versión anterior del esquema.
- Datos sensibles o credenciales.
- Instrucciones maliciosas dentro de un documento adjunto.
- Recorrido completo Work → Codex → verificación.
- Fallback por exportación e importación de artefactos.
- Aplicación existente en producción con inspección estricta.
- Repositorio limpio y repositorio con cambios de la persona usuaria.
- `README.md`, `AGENTS.md` y documentación LKS-SDD preexistentes que deben preservarse.
- Código, pruebas y documentación contradictorios.
- Regla de negocio no deducible del código.
- Pila tecnológica no homologada que puede documentarse pero no presentarse como implementable con garantía.
- Monorepo grande o inventario de alcance parcial.
- Repositorio con symlinks, submódulos, código generado o configuración externa.
- Secretos, datos sensibles e instrucciones maliciosas dentro de archivos.
- Intento de ejecutar tests, builds, hooks o gestores de paquetes sin autorización.
- Cambio de revisión o estado Git entre inventario y materialización.
- Adopción exclusivamente documental sin cambios de código.
- Normalización limitada al componente tocado, sin refactorización transversal encubierta.
- Modernización que exige plan separado de migración, coexistencia, reversión y retirada.
- Recorrido completo Codex → Work → Codex → flujo incremental normal.
- Dos proyectos de clientes distintos usados consecutivamente sin contaminación de estado.
- GitHub y GitLab tratados como orígenes equivalentes de un checkout local, sin conectores ni credenciales.

### 19.3 Métricas de calidad

- Comprensión del concepto y del siguiente paso tras la ayuda.
- Exactitud de la explicación sobre Work, Codex, plugins y skills.
- Adecuación del nivel de detalle al conocimiento y la pregunta.
- Ausencia verificable de escrituras o cambios de estado durante la ayuda.
- Derivación correcta desde ayuda al workflow elegido por la persona.
- Activación correcta.
- Ausencia de hechos o decisiones inventados.
- Clasificación correcta de información y bloqueos.
- Preguntas pertinentes y priorizadas.
- Ausencia de ampliación silenciosa de alcance.
- Completitud de trazabilidad.
- Conservación de ediciones humanas.
- Reanudación correcta desde los archivos.
- Evidencias de verificación suficientes.
- Ausencia de exposición de información sensible.
- Ausencia verificable de escrituras durante el descubrimiento estricto.
- Procedencia y vigencia de cada afirmación `as-is`.
- Detección correcta de baseline obsoleta.
- Ausencia de contaminación de estado o contenido entre proyectos.
- Diferenciación correcta entre documentable, analizable e implementable con garantía.

## 20. Criterios de aceptación de la primera versión

La v1 se considerará aceptable cuando:

1. pueda instalarse desde un marketplace de desarrollo;
2. aparezca con identidad y versión correctas;
3. inicialice una aplicación nueva sin sobrescribir contenido existente y derive una aplicación preexistente al workflow de adopción;
4. conduzca una conversación adaptativa desde una idea incompleta;
5. genere y mantenga Markdown estructurado;
6. distinga hechos, requisitos, propuestas, decisiones y pendientes;
7. respete la decisión de cerrar el nivel de detalle;
8. proponga la pila preferente solo después de comprobar su encaje;
9. admita documentar una alternativa y su justificación;
10. evalúe preparación por incremento, no de forma global;
11. bloquee código cuando falte una decisión crítica para ese incremento;
12. permita trabajo independiente pese a un bloqueo no relacionado;
13. reanude correctamente desde otro chat;
14. permita a Codex implementar un incremento vertical del perfil de referencia;
15. genere pruebas y evidencias vinculadas a criterios de aceptación;
16. mantenga la trazabilidad mínima;
17. detecte divergencias entre documentos y estado;
18. pase la validación oficial del paquete y las evals definidas;
19. respete las reglas de privacidad, secretos y acciones externas;
20. pueda publicarse de forma limitada en el workspace de LKS;
21. reutilice una única publicación del plugin en varios proyectos sin compartir estado ni contenido entre ellos;
22. realice el inventario estricto de un repositorio existente sin modificar árbol, contenido, índice, rama ni estado Git;
23. no ejecute código, builds, tests, hooks, contenedores, migraciones ni gestores de paquetes durante el descubrimiento;
24. no lea, copie ni muestre valores de secretos o credenciales;
25. distinga observaciones, documentación no verificada, inferencias, contradicciones y desconocidos con procedencia y vigencia;
26. no convierta implementación observada en requisito o intención confirmados;
27. permita a Work validar lo que el código no demuestra y produzca una reconciliación explícita;
28. detecte que la revisión o el estado del repositorio han cambiado y marque la baseline como obsoleta;
29. materialice, tras autorización, una baseline aditiva sin tocar código, configuración, datos, infraestructura, `README.md` o `AGENTS.md` existentes;
30. permita seleccionar y documentar adopción solo documental, normalización progresiva o modernización planificada;
31. documente y analice genéricamente una pila no homologada sin afirmar soporte de implementación inexistente;
32. impida cualquier cambio funcional hasta que la baseline esté materializada y el incremento supere su puerta ordinaria;
33. valide compatibilidad de versiones sin migrar o reescribir automáticamente el proyecto.
34. explique de forma clara qué es SDD, qué aporta LKS-SDD y cuáles son sus límites;
35. ofrezca un onboarding guiado y ejemplos para aplicación nueva y repositorio existente;
36. diferencie correctamente ChatGPT Work, Codex, plugin, skill, proyecto y repositorio;
37. pueda leer el estado del proyecto en modo no modificador y explicar la fase, los pendientes y las opciones siguientes;
38. mantenga una guía versionada de capacidades por superficie, con fuente, fecha de verificación, limitaciones y fallback;
39. responda a consultas de ayuda sin modificar archivos, cambiar estados ni iniciar acciones no solicitadas.

## 21. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Entrevista interminable | Preguntas de alto impacto en tandas pequeñas; opción de diferir o cerrar detalle |
| Exceso de documentación | Perfiles documentales adaptados a riesgo y complejidad |
| Falsa sensación de completitud | Estados cualitativos, riesgos residuales y revisión humana |
| Deriva entre documentos y código | Trazabilidad, validación por incremento y actualización conjunta |
| Activación inconsistente de skills | Flujos sin solapamiento e invocación explícita en cambios de fase |
| Personas que no comprenden el método o las superficies | Skill de ayuda, onboarding progresivo, ejemplos, glosario y explicación contextual |
| Ayuda desactualizada sobre Work o Codex | Guía de realidad separada, fecha de verificación, fuentes oficiales y revisión por release |
| Ayuda que ejecuta acciones por error | Contrato de solo lectura y transición siempre confirmada por la persona |
| Combinaciones tecnológicas no verificadas | Niveles de soporte y matriz de compatibilidad |
| Decisiones implícitas | Confirmación explícita y ADR |
| Cambios silenciosos | Resumen de cambios, diff y baselines |
| Pérdida de contexto entre chats | Artefactos versionados y manifiesto de control |
| Exposición de datos sensibles | Clasificación, minimización, datos sintéticos y ausencia de secretos |
| Estándar difícil de mantener | Propietarios, SemVer, evals, piloto y deprecación |
| Contaminación entre clientes o proyectos | Estado exclusivamente bajo cada raíz; sin cachés, fixtures, memoria ni telemetría compartidos con contenido sustantivo |
| Confundir código actual con intención | Procedencia por afirmación, validación en Work y separación estricta `as-is`/`to-be` |
| Alterar una aplicación productiva al adoptarla | Preflight de solo lectura, comandos prohibidos, snapshot cuando sea necesario y materialización documental autorizada |
| Baseline obsoleta por cambios concurrentes | Revisión y estado registrados; marca `stale` y reconciliación incremental antes de actuar |
| Inspección incompleta de monorepo, submódulos o configuración externa | Alcance y exclusiones explícitos; desconocidos visibles; sin falsa afirmación de cobertura total |
| Tecnología documentada confundida con homologada | Capacidades separadas: documentable, analizable, implementable y modernizable |
| Transferencia imperfecta entre Work y Codex | Artefacto versionado como contrato y exportación o sincronización explícita cuando la superficie no comparta carpeta |
| Skill de solo lectura sin aislamiento técnico suficiente | Perfil de permisos de solo lectura o snapshot/copia; declarar la garantía real disponible |

## 22. Hoja de ruta posterior

Después de validar la v1:

1. evaluar normalización progresiva automatizada para el perfil tecnológico de referencia;
2. incorporar soporte explícito para aplicaciones compuestas por varios repositorios;
3. definir patrones de modernización, pruebas de caracterización y migraciones homologadas para combinaciones seleccionadas;
4. ampliar perfiles de frontend con Angular y Vue;
5. incorporar otras alternativas de backend;
6. ampliar perfiles de datos;
7. incorporar Cognito y Entra ID;
8. añadir matrices de compatibilidad completas;
9. estudiar MCP o conectores para Jira, GitHub, GitLab, catálogo tecnológico y CI/CD;
10. añadir un panel visual de cobertura si aporta valor;
11. incorporar migraciones asistidas entre esquemas;
12. evaluar telemetría agregada de adopción y calidad, sin contenido de clientes y respetando privacidad;
13. valorar agentes especializados solo cuando una necesidad real no pueda cubrirse bien con skills.

## 23. Entradas corporativas necesarias antes de implementar

La arquitectura del plugin queda definida. Para que su contenido sea normativo en LKS deben incorporarse fuentes reales, no inferidas:

- expansión y denominación corporativa definitiva de «LKS-SDD»;
- estándares de código y estructura de repositorios;
- versiones tecnológicas soportadas;
- política de seguridad y privacidad;
- accesibilidad;
- identidad y gestión de secretos;
- CI/CD, ramas y revisión de código;
- observabilidad y operación;
- licencias y dependencias;
- clasificación de riesgos y datos;
- propietarios del estándar y de los perfiles;
- administrador y política de publicación en el workspace.
- política corporativa de trabajo sobre repositorios productivos o sensibles;
- criterio para snapshots, ramas o worktrees de adopción;
- clasificación de tecnologías heredadas, deuda, desviaciones y riesgos aceptados;
- política de retención y redacción de evidencias técnicas;
- compatibilidad y período de soporte entre versiones del método, esquema y plugin;
- alcance corporativo futuro para monorepos y aplicaciones multi-repositorio.

Estas entradas no cambian la definición del producto. Completan el contenido corporativo que el plugin debe aplicar.

## 24. Decisión final de arquitectura

LKS-SDD se implementará como un único plugin interno y versionado con seis skills, documentación Markdown estructurada, un manifiesto operativo mínimo en cada proyecto, perfiles tecnológicos modulares y validadores locales deterministas.

Cada aplicación tendrá un proyecto ChatGPT local y un repositorio propios; el plugin contendrá el método común, nunca el estado o la información de cada cliente. GitHub y GitLab serán orígenes posibles del checkout local, no integraciones en vivo de la primera versión.

Para aplicaciones nuevas, ChatGPT Work será responsable de la definición guiada y Codex de la implementación y verificación. Para aplicaciones existentes, Codex realizará primero descubrimiento estricto de solo lectura; Work validará intención y requisitos; Codex reconciliará y, tras autorización, materializará una baseline documental aditiva. Después, ambos seguirán el mismo contrato incremental versionado.

La primera versión automatizará y probará en profundidad un único perfil de referencia para generación de código. Podrá documentar y analizar genéricamente otras tecnologías sin equiparar esa capacidad con implementación, normalización o modernización homologadas.

No se incorporarán agentes, MCP, conectores, hooks ni UI propia hasta que exista una necesidad demostrada.

Esta baseline puede considerarse la **definición funcional y arquitectónica revisada de LKS-SDD v1, edición 1.2**. El siguiente paso es mantener su contrato de preimplementación alineado, aportar las referencias corporativas pendientes y convertir la baseline en un backlog de implementación verificable.

## 25. Referencias oficiales

- [Arquitectura de plugins](https://developers.openai.com/plugins/concepts/plugins)
- [Skills y activación](https://developers.openai.com/plugins/concepts/skills)
- [Empaquetado, marketplaces y publicación interna](https://developers.openai.com/plugins/build/plugins)
- [Uso de plugins en ChatGPT Work y Codex](https://learn.chatgpt.com/docs/plugins)
- [Introducción a ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)
- [Proyectos y chats](https://learn.chatgpt.com/docs/projects)
