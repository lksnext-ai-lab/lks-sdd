const cell = (text, note = '', kind = 'neutral') => ({text, note, kind});
const yes = note => cell('Sí', note, 'yes');
const nd = note => cell('No detallado', note || 'en la documentación disponible', 'unknown');
const row = (label, values) => ({label, values});
const FRAMEWORKS = [
  {name:'LKS-SDD', short:'LKS-SDD', type:'Método y plugin reutilizable', logo:'assets/lks.svg', className:'lks'},
  {name:'LKS-NEXTPATH', short:'LKS NextPath', type:'Metodología aplicada al proyecto', logo:'assets/lks.svg', className:'nextpath'}
];
const SECTIONS = [
  {id:'enfoque',nav:'Enfoque',title:'Enfoque y capacidad de adaptación',question:'¿Qué organiza cada propuesta y cómo se adapta a un proyecto?',rows:[
    row('Forma de trabajo',[cell('SDD con agentes'),cell('SDD con agentes')]),
    row('Papel de las personas',[cell('Definir, revisar y decidir','aprobación, autorización y aceptación'),cell('Definir, revisar y decidir','aprobación de plan e issues, pruebas y revisión de PR')]),
    row('Cómo se materializa',[cell('Plugin, skills y controles locales'),cell('Skills, subagentes y herramientas del proyecto')]),
    row('Entorno de ejecución documentado',[cell('Codex y Copilot','adaptación a Kiro y Claude Code pendiente de implementación y validación'),cell('Claude Code','configuración descrita para NextPath')]),
    row('Adaptación a tecnologías diferentes',[cell('Configurable por proyecto','sin selección automática de una pila'),cell('Prevista en el marco general','instancia descrita: FastAPI y React')]),
    row('Adaptación a equipos y clientes',[cell('Configurable por proyecto','roles, revisiones, controles y herramientas; se mantienen las reglas del método'),cell('Prevista en el marco general','se documentan los puntos de revisión de NextPath; variantes de configuración no detalladas')]),
    row('Énfasis de la propuesta',[cell('Condiciones para avanzar y evidencia','lectura del análisis: responsabilidad, alcance y decisiones explícitas'),cell('Secuencia operativa del desarrollo','lectura del análisis: de la especificación a los issues, el código y la actualización del estado')])
  ],insights:[
    ['Una base común','Las dos propuestas plantean desarrollo guiado por especificaciones, ejecutado con agentes y supervisado por personas.'],
    ['Flexibilidad en ambas','LKS-SDD ofrece un núcleo configurable. NextPath concreta un marco que también prevé distintos proyectos y tecnologías.'],
    ['Dos niveles de observación','Se compara un plugin reutilizable con una metodología aplicada a un proyecto. La configuración de NextPath no limita por sí sola el alcance de su marco.']
  ],sources:['sdd-core','np-framework','np-flow']},
  {id:'definicion',nav:'Definición',title:'Especificación y planificación',question:'¿Cómo se transforma una necesidad en trabajo ejecutable?',rows:[
    row('Define el comportamiento antes de implementar',[yes('especificación funcional'),yes('especificación de negocio')]),
    row('Separa comportamiento y solución técnica',[yes('definición funcional y propuesta técnica'),yes('especificación de negocio y plan técnico')]),
    row('Define criterios de aceptación',[yes('criterios y comprobaciones vinculadas'),yes('escenarios Gherkin')]),
    row('Analiza el impacto del cambio',[yes('alcance, dependencias e interfaces'),yes('nuevo, modificar o reutilizar')]),
    row('Planifica el trabajo antes de codificar',[yes('plan y tareas del método'),yes('plan técnico y posterior creación de issues')]),
    row('Organiza la especificación',[cell('Funcionalidades y requisitos','con relaciones entre elementos'),cell('Épicas, funcionalidades y escenarios','la épica actúa como referencia de la funcionalidad')]),
    row('Descompone el trabajo ejecutable',[cell('Tareas del método','con alcance y dependencias'),cell('Issues por repositorio','vinculados a escenarios y GitHub Projects')]),
    row('Define acuerdos entre componentes',[yes('interfaces y dependencias'),yes('plan compartido y contrato API entre backend y frontend')])
  ],insights:[
    ['La especificación es equivalente en propósito','Ambas definen comportamiento, solución técnica, aceptación y trabajo antes de implementar. Cambian los documentos y las unidades de seguimiento.'],
    ['Tareas e issues organizan la ejecución','LKS-SDD conserva las tareas en la documentación del método. NextPath las lleva a issues por repositorio vinculados a escenarios.'],
    ['Las interfaces forman parte del acuerdo','NextPath explicita la coordinación de backend y frontend mediante un contrato API. LKS-SDD recoge interfaces y dependencias de los componentes implicados.']
  ],sources:['sdd-skills','np-flow']},
  {id:'ejecucion',nav:'Ejecución',title:'Ejecución, agentes y coordinación',question:'¿Quién ejecuta, cómo se especializa y cómo se reparte el trabajo?',rows:[
    row('Cambios coordinados en varios archivos',[cell('Agente del entorno','Codex o Copilot'),cell('Agente del entorno','Claude Code')]),
    row('Implementación, pruebas y correcciones',[cell('Agente del entorno','guiado por las tareas y controles del método'),cell('Agente del entorno','implementación por capas y pruebas en cada capa')]),
    row('Subagentes especializados',[cell('Configurables en el entorno','fuera del núcleo; por proyecto, tecnología o disciplina'),cell('Configurados en el proyecto','exploradores, agente de backlog e implementador')]),
    row('Organización de la implementación',[cell('Por tareas y alcance autorizado'),cell('Por repositorio y capas')]),
    row('Evaluación previa de preparación',[cell('Procedimiento específico','lks-sdd-assess-readiness comprueba decisiones, dependencias y evidencia'),cell('Aprobaciones previas','plan e issues; no se detalla una skill equivalente de preparación')]),
    row('Asignaciones y relevos entre participantes',[yes('registros y procedimientos específicos'),nd()]),
    row('Organización y coordinación con Git',[yes('rama, base, destino y referencias compartidas'),yes('repositorios y PR hacia develop; coordinación entre ramas no detallada')]),
    row('Paralelización coordinada de implementación',[cell('Según entorno','el plugin registra coordinación; no incorpora un ejecutor paralelo de agentes'),nd('dos exploradores y pipelines separadas no acreditan esta capacidad')])
  ],insights:[
    ['Especialización sin fijar una tecnología','LKS-SDD puede acompañarse de agentes especializados del entorno. NextPath describe los agentes concretos que utiliza su flujo.'],
    ['Coordinar no equivale a ejecutar en paralelo','Los registros y las ramas de LKS-SDD organizan trabajo compartido. El paralelismo depende del entorno; la presentación de NextPath no detalla implementación paralela coordinada.'],
    ['El alcance del núcleo es distinto','LKS-SDD aporta procedimientos para preparación, asignación y relevo. Los agentes especializados y su ejecución se configuran fuera del núcleo.']
  ],sources:['sdd-coordination','sdd-skills','np-flow']},
  {id:'gobierno',nav:'Verificación',title:'Decisiones, verificación y aceptación',question:'¿Qué se revisa y qué permite dar el trabajo por aceptado?',rows:[
    row('Contempla revisión humana antes de ejecutar',[yes('propuestas y planes según el recorrido y la política del proyecto'),yes('aprobación de plan e issues')]),
    row('Diferencia aprobación y autorización de ejecución',[yes('decisiones distintas; pueden recogerse en una misma intervención'),nd('se describen aprobaciones de plan e issues')]),
    row('Incluye pruebas del resultado',[yes('comprobaciones vinculadas al alcance y criterios'),yes('pruebas durante la implementación, testing humano y CI')]),
    row('Contempla revisión humana del resultado',[yes('según política y criterios de aceptación'),yes('testing y revisión de la PR')]),
    row('Registra aceptación funcional diferenciada',[yes('separada de implementar y verificar'),nd('testing y revisión descritos, sin un estado de aceptación funcional equivalente')]),
    row('Estructura la evidencia de verificación',[yes('alcance, procedencia, resultado y referencia al artefacto'),nd('se describen pruebas y resultados de CI, no un registro equivalente')]),
    row('Tratamiento de cambios en lo acordado',[cell('Revalidación del alcance afectado','gestión explícita de cambios y decisiones'),cell('Cambios de especificación firmados','según la presentación; mecanismo y efectos sobre validaciones no detallados')])
  ],insights:[
    ['La supervisión humana es compartida','Ambas contemplan revisión previa y comprobación del resultado. NextPath hace visibles las aprobaciones de plan e issues, el testing y la revisión de PR.'],
    ['LKS-SDD formaliza las decisiones','Distingue aprobación, autorización, verificación y aceptación funcional, relacionándolas con alcance y evidencia. Sus roles son declarados, no identidades autenticadas.'],
    ['Lo no detallado queda abierto','La presentación de NextPath no permite comprobar todos esos registros. No detallado indica un límite de la fuente, no ausencia de la práctica.']
  ],sources:['sdd-verification','np-framework','np-flow']},
  {id:'integracion',nav:'Integración',title:'Trazabilidad, herramientas y evolución',question:'¿Cómo se conecta el método con la realidad del equipo y del cliente?',rows:[
    row('Conserva documentación fuera del chat',[yes('Markdown canónico del proyecto; el índice es derivado'),yes('especificaciones y estado en los repositorios')]),
    row('Relaciona requisitos y trabajo ejecutado',[yes('relaciones entre especificaciones, tareas y evidencia'),yes('épicas, escenarios e issues vinculados')]),
    row('Actualiza trazabilidad y estado',[cell('En las operaciones del método','las skills mantienen los registros correspondientes'),cell('En un paso específico','/np:traza sincroniza issues, tareas y progreso, y regenera INDEX.md')]),
    row('Integración con gestión y automatización del proyecto',[cell('Adaptable mediante el entorno','GitHub, GitLab u otras herramientas; requiere configuración y validación'),cell('Concretada en GitHub','GitHub Projects, gh y pasos /np:issues y /np:traza')]),
    row('Relación con el CI/CD del equipo o cliente',[cell('Adaptable al proyecto','herramientas y automatizaciones del entorno; la operación de CI/CD queda fuera del núcleo'),cell('Concretada en GitHub Actions','comprobaciones por PR; despliegue no detallado')]),
    row('Puede automatizar operaciones de CI/CD y despliegue',[cell('Mediante el entorno','requiere configuración, accesos y autorización'),cell('Mediante el entorno','CI descrita; automatización del despliegue no acreditada en la presentación')]),
    row('Controles de calidad y seguridad',[cell('Configurables por proyecto','herramientas, alcance y carácter requerido o informativo'),cell('Definidos en marco y proyecto','marco: Sonar y SCA; instancia: pruebas y controles de las pipelines descritas')]),
    row('Procedimiento para adoptar un sistema existente',[cell('Procedimiento específico','inspección acotada y reconciliación de intención'),nd('se contempla modificar y reutilizar; no se detalla un proceso completo de adopción')])
  ],insights:[
    ['Flexibilidad frente a configuración concreta','LKS-SDD puede integrarse con los flujos del equipo o cliente. NextPath documenta una combinación concreta de GitHub Projects, gh y GitHub Actions.'],
    ['La trazabilidad existe en ambos','LKS-SDD la mantiene durante las operaciones del método. NextPath concentra una parte de esa actualización en /np:traza.'],
    ['Integrar requiere trabajo de configuración','La adaptabilidad de LKS-SDD no equivale a disponer de conectores universales. En NextPath, una pipeline descrita tampoco demuestra por sí sola su ejecución ni el despliegue.']
  ],sources:['sdd-core','sdd-quality','np-flow']},
  {id:'skills',nav:'Cruce de skills',title:'Correspondencia de tareas y skills',question:'¿Dónde se resuelve cada tarea? La correspondencia es funcional, no necesariamente uno a uno.',rows:[
    row('Especificar comportamiento',[cell('lks-sdd-define'),cell('/np:spec')]),
    row('Analizar impacto y solución',[cell('lks-sdd-define'),cell('/np:analiza','con dos exploradores')]),
    row('Preparar el plan',[cell('lks-sdd-define'),cell('/np:plan')]),
    row('Descomponer el trabajo',[cell('lks-sdd-define','tareas del método'),cell('/np:issues','issues en GitHub')]),
    row('Evaluar preparación para avanzar',[cell('lks-sdd-assess-readiness'),nd('aprobaciones previas descritas; skill dedicada no identificada')]),
    row('Implementar y corregir',[cell('lks-sdd-implement'),cell('/np:impl')]),
    row('Realizar y comprobar pruebas',[cell('lks-sdd-implement + lks-sdd-verify'),cell('/np:impl + revisión humana y CI','la cobertura está distribuida entre el agente, las personas y las herramientas')]),
    row('Verificar y preparar el cierre',[cell('lks-sdd-verify','con aceptación funcional diferenciada'),cell('Testing y revisión de PR','correspondencia parcial; skill específica no detallada')]),
    row('Consultar y explicar el estado',[cell('lks-sdd-help','consulta sin cambiar el estado del proyecto'),nd('/np:traza actualiza el estado; no es una equivalencia de consulta')]),
    row('Actualizar documentación y trazabilidad',[cell('Operaciones de las distintas skills'),cell('/np:traza')]),
    row('Adoptar un sistema existente',[cell('lks-sdd-adopt-existing'),nd('skill dedicada no identificada')])
  ],insights:[
    ['La agrupación de tareas cambia','NextPath separa especificación, análisis, plan e issues. LKS-SDD reúne ese recorrido en define y separa ayuda, adopción, preparación, implementación y verificación.'],
    ['Una skill no equivale a una capacidad exclusiva','Que una tarea tenga un comando propio no implica mayor cobertura. También puede resolverse dentro de otra skill, por una persona o con herramientas del proyecto.'],
    ['Las especialidades pueden acompañar al método','NextPath menciona skills de capa y UI y subagentes concretos. LKS-SDD admite especialización en el entorno, sin incorporar un catálogo fijo de agentes ejecutables.']
  ],sources:['sdd-skills','np-framework','np-flow']}
];
const SOURCES = {
  'sdd-core':{title:'LKS-SDD · Documentación y código del plugin',url:'#fuente-sdd'},
  'sdd-skills':{title:'LKS-SDD · Seis skills y procedimientos',url:'#fuente-sdd'},
  'sdd-coordination':{title:'LKS-SDD · Coordinación y Git',url:'#fuente-sdd'},
  'sdd-verification':{title:'LKS-SDD · Decisiones y verificación',url:'#fuente-sdd'},
  'sdd-quality':{title:'LKS-SDD · Política y herramientas de calidad',url:'#fuente-sdd'},
  'np-framework':{title:'NextPath · Marco general (diapositivas 4–5)',url:'#fuente-nextpath'},
  'np-flow':{title:'NextPath · Flujo concreto (diapositiva 7)',url:'#fuente-nextpath'}
};
