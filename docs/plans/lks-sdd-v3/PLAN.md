# Plan de implementación de LKS-SDD v3

Fecha: 2026-09-29. Identificador: **PLAN-V3-001**. Revisión: **v3-plan-02**.
Estado: **plan preparado para revisión; implementación pendiente de autorización**.

La propuesta funcional y técnica **v3-propuesta-03 está validada** por el usuario.
La [decisión registrada](APPROVAL.md) identifica su contenido exacto y el permiso para
elaborar este plan. Este documento convierte ese alcance en 17 tareas verificables.
Todas las tareas de implementación están pendientes: redactar sus fichas no las ejecuta.
Esta revisión incorpora la [revisión crítica](REVIEW.md): conserva el alcance aprobado,
anticipa integración y medición y completa recorridos de entrada que estaban poco definidos.
La revisión anterior se conserva como borrador histórico, sin atribuirle aprobación.

## 1. Qué se entregará y qué se mantiene fuera

Un plugin v3 con proceso configurable para una persona o un equipo, propuesta concreta
validada antes del plan, responsables y relevos trazables, ramas por petición, controles
Sonar/Dependency-Check durante la implementación, orientación sencilla y migración
conservadora desde los formatos 2.x admitidos. La carga progresiva debe reducir trabajo
innecesario sin perder obligaciones ni calidad del código.

Se mantienen seis skills, núcleo local Python, Markdown canónico e índice reconstruible.
No se añaden servicios, MCP, conectores, hooks, apps ni agentes ejecutables. No se
implementan pipelines, despliegues o gobierno de CI/CD. La preparación de información SDD
para un PR no publica el PR ni lo aprueba.

La base inspeccionada es plugin **2.3.1**, commit
`d50f1ab86647615d654a6e1d539e1db55e63c886`, rama
`codex/team-workflow-traceability`, más las propuestas locales identificadas en
[APPROVAL.md](APPROVAL.md). El destino aprobado es plugin **3.0.0**, método **3.0.0**,
formato **3.0**, como tres ejes distintos. Las fuentes de `specs/canonical/` no se editan.

Este es un plan de mantenimiento del plugin. Sus IDs no son TASKs de un consumidor
inicializado ni activan un formato v3 inexistente. La planificación se mantiene en
este repositorio, sin crear proyecciones externas ni elegir configuración para clientes.

## 2. Recorrido y puntos de comprobación

| Bloque | Tareas | Resultado comprobable antes de seguir |
|---|---|---|
| A. Base documental | 001–002 | Contrato v3 coherente, frontera v2 y escrituras recuperables; identidades estables. |
| B. Gobierno y definición | 003–005 | Proceso viable, autoridad vigente y propuesta exacta validada antes de planificar o ejecutar. |
| C. Trabajo y calidad | 006–009 | Relevos, ramas y controles conectados al ciclo real, con integración explícita. |
| D. Contexto y migración | 010–012 | Contexto suficiente en modo de comparación; migración probada en copias y trabajo abierto conservado. |
| E. Uso y empaquetado | 013–015 | Misma experiencia en seis skills/ambos hosts; candidato local con compatibilidad declarada. |
| F. Verificación y aceptación | 016–017 | Evidencia conjunta y observación humana de agilidad, migración y eficiencia. |

Los bloques son una explicación del recorrido, no barreras secuenciales adicionales.
Mandarán las condiciones de inicio, resultados intermedios y cierre de cada tarea;
contexto, diagnóstico y trabajos transversales pueden prepararse con el núcleo disponible.

La documentación futura de v3 y los schemas se añaden de forma aditiva. Las reglas nuevas
no se fuerzan dentro de los writers v2. Solo se extrae una utilidad común si conserva
sus contratos anteriores con regresión focal; no se hará una reescritura general del runtime.

## 3. Tareas, responsabilidades y orden

Los responsables son **roles propuestos**, pendientes de asignar a personas/agentes
al autorizar la ejecución. No se inventan nombres, capacidad, fechas ni estimaciones.

| Tarea | Entregable principal | Inicio tras | Cierre tras | Responsabilidad |
|---|---|---|---|---|
| [TASK-V3-001](tasks/TASK-V3-001.md) | Contrato v3 y frontera con v2 | — | — | Mantenimiento del contrato |
| [TASK-V3-002](tasks/TASK-V3-002.md) | Identidades documentales y escritura recuperable | 001 | 001 | Mantenimiento del almacenamiento |
| [TASK-V3-003](tasks/TASK-V3-003.md) | Proceso, miembros y autoridad | 001 | 002 | Mantenimiento del modelo de proyecto |
| [TASK-V3-004](tasks/TASK-V3-004.md) | Propuesta exacta, aprobación y planificación | 002 | 003 | Mantenimiento de definición y planificación |
| [TASK-V3-005](tasks/TASK-V3-005.md) | Transiciones, dependencias y excepciones | 001 | 004 | Mantenimiento del motor de proceso |
| [TASK-V3-006](tasks/TASK-V3-006.md) | Especialistas, contribuciones y relevos | 002 | 005 | Mantenimiento de coordinación |
| [TASK-V3-007](tasks/TASK-V3-007.md) | Ramas, sincronización e integración | 002 | 006, 008 | Mantenimiento de integración Git |
| [TASK-V3-008](tasks/TASK-V3-008.md) | Sonar y Dependency-Check: evidencia y viabilidad | 002 | 005 | Mantenimiento de calidad |
| [TASK-V3-009](tasks/TASK-V3-009.md) | Implementación, corrección y cierre de tareas | 005 | 007 | Mantenimiento del ciclo de ejecución |
| [TASK-V3-010](tasks/TASK-V3-010.md) | Contexto suficiente, selección y caché | 002 | 005 | Mantenimiento del contexto |
| [TASK-V3-011](tasks/TASK-V3-011.md) | Adopción y migración: diagnóstico y vista previa | 001 | 005 | Mantenimiento de migración |
| [TASK-V3-012](tasks/TASK-V3-012.md) | Migración: aplicación, recuperación y continuidad | 011 | 009, 011 | Mantenimiento de migración |
| [TASK-V3-013](tasks/TASK-V3-013.md) | Estado del recorrido y orientación al usuario | 001 | 010, 012 | Mantenimiento de experiencia de uso |
| [TASK-V3-014](tasks/TASK-V3-014.md) | CLI y seis skills con carga progresiva | 001 | 013 | Mantenimiento de hosts y skills |
| [TASK-V3-015](tasks/TASK-V3-015.md) | Compatibilidad y distribución local v3 | 001 | 014 | Mantenimiento de distribución |
| [TASK-V3-016](tasks/TASK-V3-016.md) | Verificación conjunta y regresión | 001 | 015 | Revisión técnica e integración |
| [TASK-V3-017](tasks/TASK-V3-017.md) | Aceptación de uso, migración y eficiencia | — | 016 | Revisión funcional y técnica con usuarios |

Cada ficha contiene alcance, exclusiones, archivos, interfaces, aceptación, evidencia,
riesgos y lectura necesaria. La [matriz de trazabilidad](TRACEABILITY.md) asigna una
propiedad principal a los **69 requisitos y 100 casos**; las contribuciones transversales
no duplican esa propiedad. 015 entrega compatibilidad/distribución y 016 verifica el
conjunto; no son tareas vacías aunque no creen requisitos funcionales adicionales.

La tabla y las fichas muestran solo dependencias directas. Sus antecedentes transitivos
siguen siendo exigibles; se omite repetirlos para facilitar la lectura.

**Inicio no significa cierre.** La columna «Inicio tras» habilita trabajo independiente:
diseño de mensajes, parsers, fixtures, diagnóstico o conexión de capacidades ya operativas.
La columna «Cierre tras» exige el resultado integrado. No se registra como terminado
un caso que todavía necesita un productor, una herramienta o una observación humana.

Hay un resultado intermedio explícito: **base-git-local**, propiedad de 007, disponible
tras 001/002. Incluye detección de repositorio/referencia/sujeto real y la condición de
rama para la petición, con pruebas locales. 004 y la adopción de 011 lo necesitan para
escribir y cerrar su recorrido de autoría. No esperan al cierre completo de 007, que
añade equipo, calidad e integración. Se registra en la misma ficha/evidencia de 007,
sin otra tarea o aprobación. Así se evita una dependencia circular oculta.

001 inicia el núcleo; 017 puede preparar desde el principio protocolo, escenarios y
captura de la referencia actual. Tras 001 pueden comenzar preparación de gobierno,
transiciones, inventario de migración y los trabajos transversales 013–016. Tras 002 se
abren aprobación, equipo, Git, análisis y contexto en las porciones con contrato disponible.
No se espera a terminar todo el runtime para probar CLI, empaquetado o comprensión.

**Recorridos integrados durante el desarrollo:**

| Comprobación | Resultado demostrable | Contribución y condición |
|---|---|---|
| R1. Entrar y decidir | Proyecto nuevo o existente sin SDD → configuración propuesta → petición en rama/base → propuesta validada → plan. Sin generar código del consumidor. | 001–005 y porción local de 007; 011 para adopción, 013/014 para uso. 016 lo comprueba cuando estén esas porciones. |
| R2. Ejecutar y continuar | Tarea autorizada → implementar → analizar/corregir o no uso acordado → verificar/cerrar → reanudar. | 006–010 más CLI/mensajes operativos; prueba en copia y evidencia vinculada a entradas exactas. |
| R3. Colaborar y evolucionar | Relevo entre clones, integración conjunta, cambio parcial de política/propuesta y migración con plan abierto. | 006–012; comprobar recepción, conservación, conflictos y continuidad. |
| R4. Candidato completo | Mismos recorridos desde paquetes de prueba en ambos hosts; aceptación de uso y eficiencia. | Cierre de 014–016 y observaciones de 017; sin instalar o publicar por inferencia. |

Son puntos de comprobación de las mismas tareas, no nuevas autorizaciones o expedientes.
Puede corregirse un recorrido antes de acabar todos los módulos. 016 integra resultados
desde R1; su cierre espera el conjunto. 017 prepara/observa porciones disponibles y cierra
tras 016. No se obtiene una mejora temporal demostrada solo cambiando este orden.

El camino crítico **temporal queda sin determinar** hasta disponer de duraciones.
Con una persona se sigue R1 → R2 → R3 → R4; con equipo se abre solo trabajo independiente
con capacidad y archivos asignados. Se termina una porción útil antes de abrir otra
sin necesidad; el grafo no es una orden de iniciar 17 tareas a la vez.

## 4. Contratos entre componentes y trabajo de los agentes

001 fijará un núcleo mínimo de tipos, referencias, procedencia, errores y precondiciones
con ejemplos válidos/negativos. Los responsables ampliarán sus contratos específicos al
entregar cada porción, con revisión del integrador; 001 no diseña anticipadamente todos
los detalles ni retrasa toda la implementación. Las fronteras compartidas son:

| Frontera | Produce / consume | Contrato mínimo y comprobación conjunta |
|---|---|---|
| Fuentes → modelo | 001–002 / todas | UID, revisión, contenido literal, procedencia, referencias y estado derivado. 016 prueba reconstrucción sin índice. |
| Política y autoridad → transición | 003–004 / 005, 009 | Revisión fijada, autoridad actual, unidades aprobadas, precondiciones y causas. 016 prueba cambios concurrentes y aprobación parcial. |
| Asignación/Git → operación | 006–007 / 009–013 | Porción, responsable, estado de recepción, repo/base/sujeto y observación. 016 usa dos clones. |
| Análisis → cierre | 008 / 005, 007, 009 | Uso, aplicabilidad, obligatoriedad, estado, resultado terminal, entradas, vigencia, hallazgos y tareas cubiertas. 016 prueba corrección y composición. |
| Modelo → contexto | 001–009 / 010, 014 | Núcleo literal, incertidumbres, dependencias inversas, inventario y localizadores. 016 contrasta cobertura; 017 mide el trabajo completo. |
| Migración → continuidad | 011–012 / 009, 013–015 | Origen exacto, mapa único, decisiones reutilizables, autorizaciones pendientes, originales y recuperación. 016 prueba interrupción y rama antigua. |
| Diagnóstico → conversación | 005–013 / 014 | Hechos persistidos, fase/pendientes, causa y siguiente acción; 017 comprueba comprensión con personas. |

Todos los componentes son bibliotecas locales del mismo plugin, no servicios nuevos.
La CLI y los schemas compartidos tendrán un único integrador por archivo.
014 conecta cada operación en cuanto exista implementación verificable; 015 prueba su
empaquetado desde ese momento. Los comandos aún sin capacidad se mantienen ausentes,
sin entrypoints vacíos ni activación prematura sobre consumidores. La lógica de decisiones
queda en el núcleo, sin duplicarla en prompts por host.
Antes de añadir un módulo, su propietario identifica qué reutiliza, qué adapta y qué
debe separar por contrato. Los nombres de fichero no obligan a duplicar subsistemas v2.

Al asignar una tarea se entregan su ficha, [reglas comunes](EXECUTION.md), fuentes literales
aplicables y resultados de dependencias. No se vuelca todo el plan o la historia del
proyecto en cada chat. Ante una obligación incierta se amplía la lectura; no se omite
para cumplir un presupuesto. La autorización puede cubrir varias tareas en una decisión.

La ejecución concurrente futura necesitará checkouts/rutas separados y coordinación de
archivos comunes. Este plan no crea agentes, worktrees ni ramas adicionales. Quien integre
conserva autoría, decisiones y evidencia de cada contribución y revisa el resultado conjunto.

## 5. Estrategia de verificación proporcionada

- Cada tarea comprueba su comportamiento y fallos materiales con fixtures y pruebas
  focales; no repite la suite completa después de cada edición.
- 016 integra por recorridos desde el inicio y cierra los casos automáticos y las
  comprobaciones de contrato entre componentes; la detección de fallos no espera a 015.
  Los 100 casos son cobertura de aceptación, no 100 comandos o nuevas puertas de CI.
- 017 fija el protocolo y conserva la referencia actual antes de modificarla; observa
  porciones tempranas y completa individual, equipo y mantenimiento en Codex y Copilot.
  Cuenta decisiones, repeticiones, tiempo administrativo y comprensión; pruebas estáticas
  no acreditan aceptación humana.
- La selección de contexto empieza en comparación, conservando la ruta suficiente.
  Solo se activa tras comprobar cobertura, calidad y consumo de la tarea completa.
  Descubrimiento ≤800 tokens, instrucciones ordinarias ≤2.000 y primera vista diagnóstica
  ≤1.000 son objetivos del contenido controlado por el plugin. 8.000 tokens es un aviso
  del paquete de proyecto, nunca permiso para recortar obligaciones.
- La migración se prueba en copias sintéticas o expresamente autorizadas, con muestras
  de cada origen documentado y variantes relevantes. Un origen pendiente no figura
  como compatible probado; la pérdida de un informe no se convierte en evidencia válida.
- Se mantiene la puerta estable pequeña de [VALIDATION.md](../../VALIDATION.md).
  Los ensayos de aceptación de esta evolución no crean una batería permanente paralela,
  una infraestructura de CI ni autorizan publicación. Si el contrato nuevo exige ajustar
  comprobaciones existentes, se adapta su contenido dentro de su función actual.

Al preparar 017 se concretarán participantes, disponibilidad de hosts, medios reales de
análisis y límites de tiempo administrativo; se fijan antes de observar resultados.
Se compara v2 con v3 solo en comportamientos comunes. Para capacidades nuevas se
compara la ruta v3 suficiente con la seleccionada, sobre las mismas obligaciones;
no se usa como referencia una función inexistente en v2. Se registran cobertura/calidad,
consumo acumulado y costes locales por separado, con tokenizador/métricas identificados.
Estos preparativos tempranos no detienen tareas técnicas independientes. Si un host o un medio real de análisis
no está disponible, su resultado queda **pendiente/no ejecutado**, separado de fixtures
y validación técnica. Nunca se cambia a superado por falta de acceso.

## 6. Riesgos y decisiones todavía necesarias

| Riesgo o dato pendiente | Tratamiento y tarea responsable |
|---|---|
| Crecer en complejidad y contexto | 010/014 aplican carga progresiva; 017 mide el recorrido completo y código resultante. |
| Política flexible que no puede terminar o se autoautoriza | 003/005 validan precedencia, ciclos y funciones antes de activar; explicación mínima. |
| Cambios de contratos, autoridad o base tras revisar | 004/007/009 comprueban vigencia al mutar; revalidación por porción. |
| Medio de Sonar solo disponible después del PR | 008 diagnostica viabilidad antes de prometer cierre; no construye CI/CD. |
| Migrar un origen no inventariado o perder decisiones | 011/012 exigen disposición de cada fuente, mapa único y recuperación comprobada. |
| Diferencias reales entre hosts | 015 prepara el mismo contrato; 017 identifica capacidades y observación real, sin inferir identidad. |
| Rama antigua o escritor concurrente | 007/012 detectan divergencia observable y conservan cambios; no prometen exclusión distribuida. |
| Responsables reales, hosts y umbrales temporales | Se concretan al preparar la ejecución/aceptación correspondiente; no se inventan cuentas ni límites corporativos. |

No se considera cubierto el arranque solo por disponer de schemas: 003 prepara la
configuración/autoridad inicial, 004 la autoría documental, 007 la rama/base incluso sin
primer commit, y 011 la adopción acotada sin contrato SDD. Esta ruta es distinta de
migrar un consumidor 2.x. R1 y 016 comprueban las tres entradas.

Los nombres de módulos que figuran en las fichas son la distribución técnica propuesta
por este plan. Un ajuste interno compatible se documenta sin reabrir toda la definición.
Un cambio de alcance, comportamiento, tecnología o garantía aprobada exige presentar
su impacto y validar la porción afectada antes de implementarla.

## 7. Qué significa terminar y qué se decidirá después

La implementación técnica estará verificada cuando 001–016 dispongan de evidencia
aplicable y no haya obligaciones sin cubrir ni fallos materiales pendientes. El alcance
v3 completo solo se acepta cuando también se resuelva 017: calidad, claridad, agilidad,
continuidad de migración y eficiencia observadas, con sus resultados separados.

La versión podrá prepararse localmente como 3.0.0 en 015; eso no significa publicación,
instalación activa, aceptación humana ni migración de un proyecto real. Commits, push,
publicación, instalaciones y migraciones reales requieren su autorización específica
cuando corresponda, conforme a AGENTS.md.

**Punto actual:** propuesta validada → **plan preparado para revisar** → ejecución pendiente
→ verificación pendiente → aceptación pendiente. El siguiente paso es aprobar este
plan concreto y autorizar su ejecución; ambas decisiones pueden expresarse juntas.
La autorización podrá abarcar las 17 tareas o una porción coherente con sus dependencias.
No será necesario pedir de nuevo permiso por cada tarea comprendida en ella.

El [descriptor del plan](plan-manifest.json) identifica los bytes de esta revisión y
sus fichas. Su aprobación futura no se registra hasta recibirla.
