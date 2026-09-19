# Aprender a trabajar con LKS-SDD, Codex y Copilot

Esta introducción conserva ejemplos del workflow 1.5. Para trabajar con la versión 2,
continúa con el [índice v2](V2-INDEX.md), la [estructura documental](V2-AUTHORING.md)
y el [ciclo de trabajo](V2-WORKFLOWS.md); no copies comandos 1.x sobre un proyecto v2.
La instalación personal no migra el contrato del proyecto.

Esta guía no presupone experiencia con agentes de IA. Su objetivo es que puedas
entender qué estás aprobando, qué está haciendo la herramienta y cómo comprobar
el resultado. No necesitas memorizar comandos ni identificadores para empezar.

## 1. Antes de instalar: qué problema resolvemos

Pedir «hazme una aplicación de reservas» deja muchas preguntas abiertas: quién
puede reservar, qué sucede con los solapamientos, dónde se guardan los datos y qué
significa que el trabajo esté terminado. Un agente puede producir código aunque
estas preguntas no estén resueltas. Ese código puede funcionar y, aun así, resolver
el problema equivocado.

LKS-SDD organiza la conversación para convertir una intención en acuerdos escritos,
un plan autorizado y resultados comprobables. No elimina el juicio humano ni
garantiza automáticamente que el software sea correcto o seguro.

## 2. Las piezas, sin confundirlas

| Pieza | Qué es | Ejemplo práctico |
|---|---|---|
| Modelo de IA | Motor que interpreta contexto y propone respuestas | Puede equivocarse o completar huecos con suposiciones |
| Agente | Asistente con acceso a herramientas y un ciclo de trabajo | Lee archivos, propone cambios, ejecuta pruebas con los permisos disponibles |
| VS Code | Editor donde una persona trabaja con archivos y terminales | Abres la carpeta de tu aplicación |
| GitHub Copilot | Asistente que puede actuar dentro de VS Code | Utilizas su modo Agent para trabajar sobre el proyecto |
| Codex desktop | Otra aplicación de trabajo con agentes | Puede continuar el mismo proyecto desde su copia local |
| Skill | Instrucciones especializadas que el agente carga cuando corresponde | Definir requisitos o verificar una tarea |
| Plugin | Paquete instalable de esas capacidades y sus recursos | LKS-SDD aparece en el panel de plugins |
| Repositorio Git | Archivos e historial de cambios compartibles | Conserva código, acuerdos y evidencia; no es el historial del chat |
| Runtime de LKS-SDD | Copia concreta de los scripts y reglas del método | Permite al equipo usar la misma versión en un proyecto |

Un plugin de agente no es una extensión VSIX tradicional. Tampoco es un modelo
nuevo ni una licencia de IA. Instalarlo no concede acceso a cuentas, imágenes,
Jira o servicios externos que tu organización no haya habilitado.

## 3. Qué significa SDD y por qué decimos Spec-anchored

SDD significa desarrollo guiado por especificaciones. Una especificación describe
el comportamiento acordado y cómo se comprobará. No es solo una lista de pantallas.

En LKS-SDD la especificación sigue vigente después de empezar a programar:
**Spec-anchored** significa que el trabajo permanece vinculado a esos acuerdos.
Si cambian las reglas de reserva, también revisamos documentos, tareas y pruebas.
No generamos necesariamente todo el código desde un documento ejecutable
(Spec-as-source), ni descartamos la especificación tras el encargo inicial (Spec-first).

Ejemplo: «no permitir dos reservas solapadas de una sala» es un requisito. La
elección de PostgreSQL es una decisión técnica diferente. Un test de solapamiento
es evidencia de un caso; no demuestra por sí solo permisos, persistencia o seguridad.

## 4. Quién hace qué

La persona responsable aclara objetivos, resuelve decisiones críticas, aprueba
alcance y autoriza cambios. El agente ayuda a descubrir preguntas, documenta,
propone un plan, implementa lo autorizado y ejecuta comprobaciones disponibles.
El equipo revisa los cambios y acepta la entrega con las evidencias correspondientes.

Una propuesta del agente no es una decisión tuya. «Me gusta esa pantalla» tampoco
autoriza a construir todo el sistema, instalar dependencias nuevas o publicarlo.
Los permisos de la herramienta y la autorización funcional son controles distintos.

## 5. El recorrido completo con un ejemplo

### Orientarse: sin modificar nada

Puedes escribir: «Explícame cómo empezar con LKS-SDD. No cambies archivos todavía».
La ayuda explica opciones. No crea el proyecto como efecto secundario de responder.

### Definir: acordar el problema

«Quiero definir una aplicación interna de reservas de salas. Antes de programar,
ayúdame a concretar usuarios, permisos, reglas y criterios de aceptación».

El agente preguntará por aspectos que cambian la solución. Es legítimo contestar
«todavía no lo sabemos»: debe quedar como pendiente, no como una aprobación tácita.
Ejemplo de aceptación: «si existe una reserva de 10:00 a 11:00, un segundo intento
de 10:30 a 11:30 para la misma sala se rechaza y no se guarda».

### Explorar la interfaz: decidir antes de construir

Un prototipo visual permite discutir distribución, jerarquía y estados. Una imagen
no demuestra que un botón funcione, que haya base de datos o que la aplicación sea accesible.
En Copilot, las imágenes nuevas se preparan mediante un relevo a Codex. La ficha
guarda el contexto necesario. Abres el mismo proyecto en Codex y continúas esa parte.
Puedes permanecer allí o regresar a Copilot después de guardar y transferir los cambios.
En Codex el trabajo visual normal sigue directamente, sin anunciar un cambio de herramienta.
No añadimos una API de imágenes de pago: cada persona usa su acceso autorizado a Codex.

### Planificar: convertir acuerdos en trabajo verificable

El plan agrupa una entrega y la divide en tareas. Una tarea debería tener alcance,
dependencias y pruebas identificables. «Hacer el backend» puede ser demasiado amplio;
«rechazar solapamientos al registrar una reserva» permite verificar un resultado concreto.

Antes de implementar se revisan tanto la especificación como la cobertura del plan.
Una tarea preparada no significa que toda la entrega esté planificada. El desarrollo
incremental requiere una decisión expresa; no es una forma de ignorar pendientes críticos.

### Autorizar e implementar

«Revisa si la tarea de validación de solapamientos está preparada y muéstrame qué
cambios propones antes de ejecutarlos». Tras revisar la propuesta, autorizas el alcance
concreto. El agente registra esa autorización mediante el procedimiento del método.
Si cambian las condiciones relevantes, la autorización anterior puede dejar de ser válida.

No elijas una pila porque aparezca en un ejemplo. Un perfil es una combinación
técnica exacta con reglas y comprobaciones propias. Que un perfil exista en el catálogo
no significa que esté certificado: los candidatos no habilitan automáticamente implementación.

### Verificar y entregar

«Verifica la tarea y separa qué está probado, qué falta y qué necesita revisión humana».
La verificación contrasta aceptación y pruebas, no solo que el programa arranque.
Frontend y backend pueden pasar pruebas por separado sin comunicarse correctamente.
Una prueba de integración comprueba esa comunicación; una de persistencia comprueba
que los datos realmente se conservan; la revisión visual evalúa otra dimensión.

Código escrito, pruebas superadas, aceptación humana y despliegue son hitos distintos.
LKS-SDD no debe publicar, hacer push o desplegar simplemente porque una tarea pase tests.

## 6. Las seis capacidades que puedes pedir

| Capacidad | Cuándo utilizarla | Qué no implica |
|---|---|---|
| help | Entender el método, consultar estado o resolver dudas | No cambia archivos |
| define | Crear o continuar especificaciones y planificación | No autoriza implementación por sí sola |
| adopt-existing | Documentar un sistema que ya tiene código | El código observado no decide qué debería ser correcto |
| assess-readiness | Comprobar si el alcance está preparado | No aprueba ni ejecuta tareas |
| implement | Ejecutar una porción expresamente autorizada | No amplía alcance ni elimina decisiones pendientes |
| verify | Contrastar implementación y evidencia | No sustituye aceptación ni autoriza producción |

Puedes pedirlo en lenguaje natural. La selección implícita depende del agente y
de su contexto; si no carga la skill, selecciónala explícitamente en la interfaz.
En el plugin Copilot aparecen comandos con prefijo, por ejemplo
`/lks-sdd:lks-sdd-help`. En la alternativa de skills de proyecto el comando es
`/lks-sdd-help`. No mantengas ambos mecanismos activos para el mismo proyecto.

## 7. Qué se comparte y qué permanece personal

El equipo comparte documentos, código, imágenes seleccionadas, evidencia y el lock
de versión. Cada desarrollador trabaja en su propio clon: una copia local del mismo
repositorio. Una rama permite preparar cambios antes de integrarlos mediante revisión.
Un commit registra cambios localmente; push los envía al servidor; ninguno equivale a desplegar.

No compartas claves, tokens, archivos .env reales, cachés personales de Codex/Copilot
ni sesiones de chat. La continuidad debe poder reconstruirse desde el repositorio.
Jira, si se elige, es una proyección operativa opcional: no reemplaza la documentación
canónica ni transforma un estado remoto en evidencia de que una tarea esté terminada.

Trabaja con un responsable de escritura por alcance compartido. Antes del relevo,
guarda y transfiere los cambios por el flujo Git autorizado. El siguiente compañero
actualiza su clon, comprueba integridad y pide el estado antes de escribir. Esta versión
no implementa reservas distribuidas para varios agentes modificando a la vez el contrato.

## 8. Dónde mirar cuando algo no encaja

| Ubicación | Función |
|---|---|
| docs/lks-sdd/ | Acuerdos y documentación canónica de la aplicación |
| .lks-sdd/project.json | Índice para encontrar los documentos; no sustituye su significado |
| .lks-sdd/distribution-lock.json | Versión e integridad del núcleo utilizado por el proyecto |
| .lks-sdd/runtime/ | Núcleo fijado; no lo edites manualmente |
| .lks-sdd/handoffs/visual/ | Fichas y resultados del relevo visual |
| AGENTS.md | Instrucciones compartidas para los agentes |
| .github/lks-sdd-host.md | Particularidades del trabajo desde Copilot |

El repositorio del producto LKS-SDD es distinto del repositorio de tu aplicación.
Los scripts del plugin pertenecen al producto; tus reservas, requisitos y decisiones
pertenecen al consumidor. Instalar el plugin no materializa una aplicación.

## 9. Cómo interpretar estados y siglas

`passed` significa que una comprobación concreta pasó. `failed` indica fallo.
`not-run` significa que no se ejecutó; no lo interpretes como éxito. `not-applicable`
requiere una razón. `blocked` necesita resolver una condición. `reconciliation-required`
indica que hay que contrastar información o evidencia que ya no coincide.

INC identifica un incremento de alcance; REQ un requisito; ADR una decisión de
arquitectura; TASK una tarea; AUTH una autorización; EXEC una ejecución; CKPT un
punto de continuidad; EVID evidencia; VIS una referencia visual. Un gate es una
comprobación de paso, no una aprobación humana. Un hash es una huella de bytes:
detecta cambios, pero no demuestra que su contenido sea correcto ni quién lo aprobó.

## 10. Problemas habituales y siguiente lectura

- No aparecen skills: revisa plugin habilitado, carpeta correcta, nueva conversación
  y políticas corporativas. No desactives controles de seguridad para forzar su carga.
- Hay dos comandos parecidos: probablemente conviven plugin y adaptadores de proyecto.
  Sigue la migración documentada; no borres instrucciones personalizadas.
- Integridad bloqueada: conserva los archivos y revisa el diagnóstico. No edites el
  lock para que «pase». Actualiza o recupera con el instalador autorizado.
- Copilot no genera imágenes: es el comportamiento acordado. Usa la ficha de relevo.
- El agente dice «terminado» sin evidencia: pide resultados y pendientes separados.
- Un compañero no ve lo que aprobaste: comprueba que los documentos e imágenes se
  transfirieron al repositorio. El chat de otra persona no se sincroniza por Git.

Continúa con [instalación y primer uso](INSTALLATION.md),
[prueba guiada del plugin](COPILOT-PILOT.md), [relevo visual](VISUAL-HANDOFF.md),
[compatibilidad y límites](COMPATIBILITY.md), [arquitectura](ARCHITECTURE.md) y
[validación técnica](VALIDATION.md). Para responsables de distribución:
[empaquetado](DISTRIBUTION.md) y [publicación](RELEASING.md).

La [aceptación por host](V2-HOST-ACCEPTANCE.md) distingue implementación, pruebas
automáticas y pruebas reales pendientes. Esta guía enseña el flujo esperado; no es
un acta que certifique que todas las herramientas lo hayan ejecutado correctamente.
