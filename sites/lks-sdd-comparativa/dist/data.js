const cell = (text, note = '', kind = 'neutral') => ({text, note, kind});
const yes = note => cell('Sí', note, 'yes');
const no = (note = 'responsabilidad del equipo') => cell('No', note, 'no');
const partial = note => cell('Parcial', note, 'partial');
const host = note => cell('Agente del entorno', note, 'host');
const tool = (note = '') => cell('Según herramienta', note, 'neutral');
const row = (label, values) => ({label, values});
const FRAMEWORKS = [
  {name:'LKS-SDD', short:'LKS-SDD', type:'Método y plugin', logo:'assets/lks.svg', className:'lks'},
  {name:'Kiro', short:'Kiro', type:'Entorno con SDD', logo:'assets/kiro.ico', className:'kiro'},
  {name:'Spec Kit + Copilot', short:'Spec Kit', type:'Método + agente', logo:'assets/github.svg', className:'github'},
  {name:'Desarrollo asistido por IA', short:'IA asistida', type:'Enfoque de referencia', glyph:'↗', className:'control'},
  {name:'Vibe coding', short:'Vibe coding', type:'Enfoque de referencia', glyph:'≈', className:'control'}
];
const SECTIONS = [
{id:'ejecucion',nav:'Ejecución',title:'Modelo de desarrollo y ejecución',question:'¿Quién conduce el trabajo y quién lo ejecuta?',rows:[
 row('Forma de trabajo',[cell('Delegación en agentes'),cell('Delegación en agentes'),cell('Delegación en agentes'),cell('Programador con IA'),cell('Iteración por instrucciones')]),
 row('Unidad habitual de delegación',[cell('Funcionalidad o tarea'),cell('Funcionalidad o tarea'),cell('Funcionalidad o tarea'),cell('Consulta o ayuda puntual'),cell('Resultado solicitado')]),
 row('Cambios coordinados en varios archivos',[host('Codex o Copilot'),host('Kiro'),host('Copilot'),cell('Programador con IA'),tool()]),
 row('Ejecución de pruebas y correcciones',[host('herramientas del proyecto'),host('herramientas del proyecto'),host('herramientas del proyecto'),cell('Programador con IA'),tool()]),
 row('Paralelización automática de tareas independientes',[cell('Según entorno','el plugin no incorpora un ejecutor de agentes'),yes('incorporada en la ejecución de tareas'),cell('Según entorno','marcas de paralelismo; ejecución mediante Copilot'),no(),tool()]),
 row('Revisión técnica del código por una persona',[cell('Según política','controles del proyecto'),cell('Según política','controles del proyecto'),cell('Según política','controles del proyecto'),cell('Parte del enfoque','el programador revisa el trabajo'),cell('Limitada o variable','se prioriza observar el resultado')])
],insights:[['Delegar es una capacidad común','Las tres propuestas SDD permiten encargar implementación a agentes, con cambios en varios archivos y pruebas.'],['El método organiza la ejecución','LKS-SDD y Spec Kit añaden procedimientos al entorno; Kiro integra procedimiento y ejecución en su producto.'],['Los controles comparan hábitos','La IA asistida mantiene al programador al frente. Vibe coding se concentra en pedir, observar y ajustar resultados.']],sources:['kiro-specs','speckit','vscode','vibe']},
{id:'definicion',nav:'Definición',title:'Especificación y planificación',question:'¿Cómo se transforma una necesidad en trabajo ejecutable?',rows:[
 row('Define el comportamiento antes de implementar',[yes(),yes(),yes(),no(),no('no es requisito del enfoque')]),
 row('Separa comportamiento y solución técnica',[yes(),yes(),yes(),no(),no('no es requisito del enfoque')]),
 row('Define criterios de aceptación',[yes(),yes(),yes(),no(),no('no es requisito del enfoque')]),
 row('Procedimiento para aclarar ambigüedades',[yes('forma parte del proceso'),yes('análisis opcional de requisitos'),yes('clarificación opcional'),no('la IA puede ayudar'),no('aclaraciones conversacionales')]),
 row('Planifica el trabajo antes de codificar',[yes(),yes(),yes(),no(),no('no es requisito del enfoque')]),
 row('Descompone el trabajo en tareas y dependencias',[yes(),yes(),yes(),no(),no('no es requisito del enfoque')]),
 row('Mantiene las especificaciones durante la evolución',[yes('acuerdos vigentes prescritos por el método'),yes('refinamiento y sincronización de documentos'),cell('Configurable','el equipo elige la estrategia de mantenimiento'),no(),no('depende de las prácticas añadidas')])
],insights:[['La base SDD es compartida','Las tres definen qué debe hacer el sistema, cómo abordarlo y qué tareas realizar. Los nombres de los documentos no cambian esa equivalencia.'],['La diferencia aparece al evolucionar','LKS-SDD prescribe conservar los acuerdos vigentes; Kiro permite refinar sus documentos; Spec Kit deja elegir su estrategia de mantenimiento.'],['El proceso debe existir en algún lugar','La IA asistida y vibe coding no aportan por sí mismos un procedimiento de especificación. El equipo puede incorporarlo.']],sources:['kiro-specs','kiro-practices','speckit','persistence']},
{id:'gobierno',nav:'Equipo y gobierno',title:'Coordinación, responsabilidades y decisiones',question:'¿Cómo se comparte el trabajo y se decide su aceptación?',rows:[
 row('Organización del trabajo mediante ramas Git',[yes('rama, base y destino de la petición'),cell('Según entorno','herramientas Git'),cell('Opcional','extensión Git de Spec Kit'),no(),tool()]),
 row('Registro de responsables, asignaciones y relevos',[yes('registros específicos y aceptación de encargos'),partial('tareas; asignación humana a cargo del equipo'),partial('tareas; asignación humana a cargo del equipo'),no(),no()]),
 row('Revisión conjunta antes de aceptar el trabajo integrado',[yes('recorrido integral optativo 3.1'),no('en el flujo SDD comparado'),no('en el flujo SDD comparado'),no(),no()]),
 row('Revisión humana contemplada en el proceso',[yes(),yes('flujo estándar; Quick Spec omite aprobaciones intermedias'),yes('revisión entre pasos'),yes('el programador conduce la revisión'),cell('Variable','no se exige revisión técnica sistemática')]),
 row('Registro de aprobación y autorización de ejecución',[yes('decisiones explícitas y diferenciadas'),partial('confirmaciones de fases'),partial('revisiones y listas de comprobación'),no(),no()]),
 row('Decisiones vinculadas a responsables y alcance',[yes('responsabilidades declaradas'),partial('documentos y prácticas del equipo'),partial('documentos y prácticas del equipo'),no(),no()]),
 row('Aceptación funcional separada de la implementación',[yes('decisión diferenciada'),no('responsabilidad del equipo'),no('responsabilidad del equipo'),no(),no()]),
 row('Control de permisos técnicos del agente',[cell('Según entorno'),cell('Según entorno'),cell('Según entorno'),cell('Según entorno'),cell('Según entorno')])
],insights:[['Coordinación compartida en LKS-SDD','Ramas, responsables, asignaciones y relevos hacen explícito cómo se reparte y se retoma el trabajo. No equivalen a ejecutar agentes en paralelo.'],['Las decisiones tienen momentos distintos','LKS-SDD registra aprobación, autorización y aceptación. Kiro y Spec Kit incluyen revisión, con diferente grado de formalización.'],['Permiso técnico y decisión funcional','Poder ejecutar un comando no acredita que el alcance esté aprobado. Los roles de LKS-SDD son declarados, no identidades autenticadas.']],sources:['kiro-specs','speckit','git-extension','kiro-permissions']},
{id:'calidad',nav:'Calidad',title:'Calidad, verificación y evidencia',question:'¿Qué permite afirmar que el trabajo está comprobado?',rows:[
 row('Define comprobaciones y pruebas',[yes(),yes(),yes(),no('el programador puede definirlas con IA'),no('pueden añadirse')]),
 row('Contrasta implementación y especificaciones',[yes(),yes(),yes('incluye el paso Converge'),no('la IA puede ayudar si hay especificaciones'),no('no se exige especificación')]),
 row('Uso de analizadores de calidad y seguridad',[yes('herramientas externas configuradas'),yes('herramientas externas configuradas'),yes('herramientas externas configuradas'),yes('herramientas del equipo'),tool()]),
 row('Registro estructurado de evidencia de verificación',[yes('alcance, procedencia y resultado'),partial('resultados y documentación de tareas'),partial('resultados y documentación del proceso'),no(),no()]),
 row('Distingue implementar, verificar y aceptar',[yes('estados y decisiones explícitos'),partial('ejecución y validación; aceptación del equipo'),partial('implementación y contraste; aceptación del equipo'),no(),no()])
],insights:[['Las herramientas no son exclusivas','Las tres propuestas pueden utilizar pruebas y analizadores del proyecto. La disponibilidad de una herramienta no acredita mejor calidad.'],['LKS-SDD explicita la evidencia','Relaciona lo comprobado con su alcance y procedencia, y distingue verificación técnica de aceptación funcional.'],['Se comparan controles, no resultados','Kiro incorpora comprobaciones en sus tareas y Spec Kit un contraste final. La calidad del software exige evaluar resultados reales.']],sources:['kiro-specs','kiro-correctness','speckit','agentic-sdd']},
{id:'evolucion',nav:'Evolución y entrega',title:'Evolución, herramientas y entrega',question:'¿Cómo encaja cada enfoque en el entorno de la organización?',rows:[
 row('Aplicación sobre proyectos existentes',[yes('adopción acotada y reconciliación de intención'),yes(),yes(),yes(),tool()]),
 row('Conserva conocimiento del proyecto fuera del chat',[yes('documentación del proyecto'),yes('especificaciones y reglas del proyecto'),yes('especificaciones y reglas del proyecto'),no('el equipo elige dónde conservarlo'),tool()]),
 row('Permite incorporar reglas de desarrollo de LKS',[yes('políticas y documentación configuradas'),yes('instrucciones del proyecto'),yes('constitución e instrucciones del proyecto'),no('responsabilidad del equipo'),no('responsabilidad del equipo')]),
 row('Entorno de ejecución',[cell('Codex y Copilot','migrable a Kiro y Claude Code; adaptación y validación pendientes'),cell('Kiro'),cell('Copilot','Spec Kit admite otros agentes'),tool(),tool()]),
 row('Aporta su propio sistema de CI/CD y despliegue',[no(),no(),no(),no(),no()]),
 row('Puede automatizar operaciones de CI/CD y despliegue',[host('requiere configuración, accesos y autorización'),host('requiere configuración, accesos y autorización'),host('requiere configuración, accesos y autorización'),cell('Programador con IA','dirige la automatización'),tool('puede incluir automatización')])
],insights:[['Un método puede cruzar entornos','LKS-SDD se distribuye para Codex y Copilot. Adaptarlo a Kiro y Claude Code es viable en principio, pendiente de implementación y validación.'],['La documentación sostiene la continuidad','Las tres propuestas SDD conservan información fuera del chat para retomar trabajo y compartir contexto entre personas.'],['La entrega también es automatizable','Las tres pueden apoyarse en el agente del entorno para operar CI/CD. El equipo mantiene la infraestructura, los accesos y las reglas de despliegue.']],sources:['kiro-skills','claude-skills','existing-projects','kiro-hooks']}
];
const SOURCES = {
 'kiro-specs':{title:'Kiro · Especificaciones y ejecución de tareas',url:'https://kiro.dev/docs/specs/'},
 'kiro-practices':{title:'Kiro · Mantenimiento de las especificaciones',url:'https://kiro.dev/docs/specs/best-practices/'},
 'kiro-permissions':{title:'Kiro · Permisos del agente',url:'https://kiro.dev/docs/permissions/'},
 'kiro-correctness':{title:'Kiro · Verificación mediante propiedades',url:'https://kiro.dev/docs/specs/correctness/'},
 'kiro-skills':{title:'Kiro · Skills portables',url:'https://kiro.dev/docs/skills/'},
 'kiro-hooks':{title:'Kiro · Automatización con hooks',url:'https://kiro.dev/docs/hooks/'},
 'speckit':{title:'GitHub Spec Kit · Proceso de desarrollo',url:'https://github.github.com/spec-kit/quickstart.html'},
 'persistence':{title:'GitHub Spec Kit · Persistencia de especificaciones',url:'https://github.github.com/spec-kit/concepts/spec-persistence.html'},
 'git-extension':{title:'GitHub Spec Kit · Extensión Git',url:'https://github.com/github/spec-kit/blob/main/extensions/git/README.md'},
 'agentic-sdd':{title:'GitHub Spec Kit · Implementación y contraste final',url:'https://github.github.com/spec-kit/reference/agentic-sdd.html'},
 'existing-projects':{title:'GitHub Spec Kit · Proyectos existentes',url:'https://github.github.com/spec-kit/guides/existing-projects.html'},
 'vscode':{title:'VS Code · Desarrollo con agentes',url:'https://code.visualstudio.com/docs/agents/overview'},
 'claude-skills':{title:'Claude Code · Skills',url:'https://code.claude.com/docs/en/skills'},
 'vibe':{title:'Simon Willison · Vibe coding e IA asistida',url:'https://simonwillison.net/2025/Mar/19/vibe-coding/'}
};
