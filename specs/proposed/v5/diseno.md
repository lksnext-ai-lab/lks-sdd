# LKS-SDD v5: propuesta integrada

Fecha: 21 de octubre de 2026. Estado: **diseño aprobado como base de implementación de la candidata v5**.
Base de código comprobada: 4.0.3, `ecc033c775319163c51b11a76637b45a7460efe7`.
La [petición](tarea.md) gobierna este diseño. El [plan](plan.md) reúne ejecución,
comprobaciones, resultados y pendientes. No cambia el contrato publicado.

## Decisiones recibidas y alcance

La petición decide tres tipos de documentos duraderos y tres fases. Tras el prototipo,
la instrucción «Adelante. Completa los pendientes hasta tener la v5 preparada para
release» autoriza implementar el modelo, la migración integral y las seis skills.
No autoriza commits, publicación, instalación ni migrar consumidores activos.
El contrato operativo implementado se documenta en `docs/V5.md`; el plan recoge
las verificaciones reales y las diferencias frente al experimento inicial.

### Aclaraciones vinculantes posteriores a la revisión

Joseba precisa que la migración **no debe permitir volver atrás** y autoriza
eliminar el material sustituido sin conservarlo por precaución. Esta decisión
sustituye la exigencia anterior de rollback y recuperación posterior de la migración.
La conversión debe poder reanudarse para terminar si se interrumpe; eso no requiere
una función de reversión ni una copia íntegra del modelo anterior. Una vez convertido
y comprobado el contenido útil, se eliminan fuentes sustituidas, backups, inventarios
y temporales sin utilidad. No se cambia ni purga el historial normal de Git.

El criterio de crecimiento se aplica a **la documentación del proyecto en su
conjunto**. Una especificación puede ser grande o crecer cuando añade comportamiento,
reglas o conocimiento útil. Lo que debe evitarse es el crecimiento sin valor debido
a controles y trazabilidad del plugin, duplicaciones, recibos, snapshots o expedientes.
El tamaño de un documento o del contexto de una consulta, por sí solo, no demuestra
ese incumplimiento. La selección de contexto sigue siendo una optimización útil,
pero no reemplaza la evaluación del volumen y valor documental total.

El diagnóstico observa el runtime 4.0.2, no 4.0.3: 39 duraciones core capturadas
suman al menos 4 h 38 min; no equivalen a todo el coste administrativo. Las 31 h 39 min
incluyen desarrollo, esperas y operación. Las dos huellas de aplicación no representan
todas las entradas de los 15 pipelines. Esos datos motivan el rediseño, pero no
demuestran ahorro ni una causa CPU/I/O concreta. Las recomendaciones del informe
son antecedentes; no sustituyen el modelo documental solicitado.

## Propuesta de producto

```text
docs/sdd/
  especificaciones/
    ordenes-de-trabajo.md
    permisos.md
  tareas/
    T-20261021-7ab2-correccion/
      tarea.md
      plan.md
```

La especificación conserva comportamiento, excepciones, datos, permisos e
interfaces por capacidad de negocio. Las reglas compartidas son especificaciones
transversales, del mismo tipo documental. Las políticas existentes del proyecto
siguen en sus ubicaciones; se referencian, sin copiarlas ni imponer otra plantilla.

La tarea contiene petición, alcance, unidades afectadas, criterios observables y
decisiones. El plan reúne enfoque, pasos, comprobaciones, estado, siguiente acción,
bloqueos, decisiones de ejecución y resultado. Solo se crean apartados pertinentes.
El nombre legible acompaña un identificador estable; renombrar no cambia identidad.

Una subtarea solo se abre si requiere ejecución, responsabilidad o dependencia
independiente. La principal enlaza a sus hijas y resume el resultado conjunto. Los
pasos ordinarios son una lista dentro del mismo plan. Las tareas cerradas siguen
siendo legibles y quedan fuera de la lectura inicial de otras tareas.

### Recorrido

| Fase | Operación habitual | Escritura duradera |
|---|---|---|
| Definición | Leer unidades y política pertinente; concretar el cambio. | `tarea.md`. |
| Planificación | Preparar enfoque y pruebas proporcionales; registrar autoridad vigente. | `plan.md`. |
| Ejecución | Implementar y consumir resultados; actualizar estado cuando cambia. | El mismo plan y código/tests del producto. |
| Consolidación, dentro de ejecución | Incorporar contrato consolidado, resumir resultado y limpiar. | Especificaciones afectadas y el mismo plan. |

No habrá una autorización por comando. La decisión se registra una vez, con autor,
alcance y límites. Una ampliación material exige resolver solo su parte. Declarar
un nombre no autentica a una persona; un hash tampoco otorga autoridad.

Estado de trabajo propuesto: definido, preparado, en curso, bloqueado y cerrado.
La fase y la siguiente acción se derivan de la tarea y el plan. Los hechos de
implementación, verificación, integración, publicación, despliegue y aceptación se
registran por separado dentro del resultado: cerrar no transforma pendientes en
éxitos. Una tarea puede terminar su alcance local con despliegue o aceptación
pendientes, explícitos, si eso es lo acordado.

### Qué desaparece, se fusiona o se conserva

| Mecanismo actual | Tratamiento v5 propuesto | Valor preservado |
|---|---|---|
| Propuesta/SPEC por cambio y documentos históricos necesarios para entenderlo | Tarea con cambio; especificación consolidada por capacidad. | Intención, excepciones y contrato vigente. |
| PLAN/TASK/EXEC/CKPT y seguimiento separado | Tarea y un plan evolutivo. | Responsabilidad, continuidad y siguiente acción. |
| AUTH, recibos y presentaciones por transición | Decisión breve en tarea o plan; autorización reutilizada dentro de su alcance. | Quién decide, qué cubre y cuándo deja de cubrir. |
| Expedientes de evidence/verify/close/integrate/delivery | Resultados referenciados en el plan; cierre transaccional. | Procedencia y hechos de entrega separados. |
| Inventarios y snapshots versionados por operación | Precondiciones en memoria; journal temporal solo durante escritura recuperable. | Conflictos, integridad y recuperación. |
| Paquetes completos de contexto y diagnósticos rutinarios | Lectura directa y deduplicada; diagnóstico optativo. | Contenido literal relevante y ampliación ante incertidumbre. |
| Índice como requisito de operación | Índice regenerable opcional. | Navegación; Markdown suficiente para operar. |
| Histórico operativo y objetos v4 | Lector de conversión; retirada definitiva tras extraer y comprobar lo útil. | Conocimiento vigente y decisiones necesarias, sin rollback ni archivo legacy. |
| Calidad, política de entrega y permisos del proyecto | Referencias y controles vigentes. | No se eluden por objetivos de velocidad. |

## Arquitectura propuesta

Mantener las seis skills y la invocación implícita, revisando su contenido para v5.
Mantener la identidad del plugin y ambos destinos de distribución. El prototipo es
Python con biblioteca estándar para probar decisiones de producto; no decide el
lenguaje final por inercia. No añade MCP, hooks, servicios ni agentes ejecutables.

El núcleo v5 tendrá cuatro responsabilidades: documentos/contexto, operaciones
recuperables, resultados de comprobación y conversión. No dependerá del motor v4.
El lector de versiones anteriores solo se carga al convertir. Los adaptadores de
Git, CI y calidad consumen sus formatos existentes; no crean scripts por tarea.

Las operaciones públicas propuestas son consultar, preparar/actualizar, comprobar,
consolidar y convertir. Los nombres finales de CLI son secundarios. Una operación
devuelve estado, cambio relevante y siguiente acción; detalle solo a demanda.
Los trabajos largos devuelven una referencia de operación que el host espera con
su mecanismo nativo; el modelo no se usa como temporizador. No se promete un
servicio de notificación donde el host no lo ofrezca.

### Contexto y concurrencia

La entrada habitual es una tarea concreta: sus dos documentos, unidades afectadas,
dependencias transitivas explícitas y reglas aplicables. Los enlaces a evidencias
no incorporan automáticamente el binario ni todo su histórico. Una dependencia
desconocida se señala y amplía la lectura necesaria; no se declara irrelevante.
Una comprobación de referencias detecta unidades ausentes y ciclos sin duplicar.

Las escrituras comprueban la base leída de cada archivo afectado. Si otra tarea
consolida la misma unidad, la siguiente debe reconciliar su cambio sobre esa base.
No se aceptan reemplazos silenciosos. El journal conserva preimagen y destino
durante una escritura; recuperar solo acepta cada archivo en su versión anterior
o en la ya escrita por esa operación. Un tercero distinto produce conflicto.
Un bloqueo local coordina procesos del plugin; no se presenta como lock distribuido
ni como protección absoluta frente a editores ajenos. Git y la revisión de merges
siguen resolviendo concurrencia entre clones.

El coste de una consulta normal depende del alcance vigente. No se recorre todo el
histórico para consultar una tarea. Reconstruir un índice completo o convertir un
proyecto sí tiene coste proporcional al inventario, y se declara por separado.

### Pruebas, reutilización y despliegue

Cada comprobación declara criterio/riesgo, alcance de entradas, comando o proveedor,
configuración, entorno y resultado. Una reutilización requiere igualdad de entradas
relevantes y condiciones; incluye tests, dependencias, configuración y versión de
herramientas, no solo código de aplicación. Añadir o eliminar un archivo dentro de
un alcance invalida la huella. Entradas incompletas, resultados fallidos, caducados
o evidencia no recuperable impiden presentar la prueba como vigente.

El resultado vive una vez en el plan con referencia al artefacto. JUnit, CI o Sonar
conservan sus resultados originales; la v5 no redacta un informe equivalente. Si
una referencia expira pronto, conservar el resultado mínimo necesario antes de
cerrar. Imágenes, ZIP y binarios se describen por tipo, tamaño, hash y referencia;
no se leen como UTF-8 para poder cerrar.

Cambiar documentación fuera de las entradas declaradas conserva la validez del
test. Eso no dispensa una política explícita de proyecto. Si exige una regresión
completa tras despliegue se cumple; si no, la entrega comprueba versión, salud y
funcionamiento afectado. El runtime no dispara por defecto una suite general.

La selección automática de dependencias nunca sustituye la revisión del alcance:
el prototipo exige entradas explícitas y no acredita que pueda inferirlas todas.

## Migración y limpieza

Objetivo inicial: formato 3.1/método 3.1.0 usado por plugin 4.0.2 y 4.0.3, incluyendo
sus representaciones documentales. Añadir lectores directos de 3.0, 2.0 y 1.5
después de caracterizar sus fixtures; no exigir migraciones intermedias. Soporte
planeado no equivale a soporte demostrado por el prototipo.

La conversión prepara un borrador de unidades y tareas/planes y una vista breve de
contenido útil, retirada y ambigüedades. El agente propone la
consolidación semántica; el runtime valida cobertura y referencias, no inventa qué
contrato prevalece. Las contradicciones materiales conservan su fuente y bloquean
solo el conjunto afectado. La vista no exige un expediente por documento.

La aplicación autorizada liga esa propuesta a las fuentes leídas. La migración es
definitiva: no ofrece rollback, backups de reversión ni plazos de retención del
modelo sustituido. Mientras está pendiente conserva solo las fuentes todavía
necesarias y el estado mínimo para reanudar hacia v5. Verificada la conversión,
retira ese material. No se crea un árbol legacy ni se permite doble escritura.
Esta decisión se refiere a migración; no elimina la detección de conflictos ni la
reanudación de operaciones ordinarias sobre los documentos v5.

Se actualizan referencias e instrucciones antes de retirar archivos. No basta con
borrar `docs/lks-sdd`: hay que resolver consumidores, rutas compartidas y runtime
fijado. Un origen desconocido o una dependencia externa no demostrada queda
pendiente; no se borra por estar en una carpeta con nombre antiguo. Los runtimes
compartidos y las instalaciones personales quedan fuera de la limpieza.

El cierre elimina solo temporales propiedad de la operación y sin uso pendiente.
Tests, utilidades reutilizables y resultados singulares permanecen. Un fallo abierto
retiene su diagnóstico mínimo. La limpieza y la consolidación se reanudan juntas;
los archivos ajenos no son candidatos.

## Prototipo y aceptación

El experimento aislado recorre tarea → plan → prueba real → reutilización/invalidez
→ consolidación → recuperación/limpieza. Incluye contexto con histórico creciente,
conflicto de dos tareas y conversión de una extracción acotada de documentos reales
del caso SAT Next AI, conservando procedencia. No opera producción.

Un caso acotado no certifica la migración completa de SAT Next AI, todos los formatos
antiguos, las seis skills ni ambos hosts. La aceptación del producto v5 requiere
los doce escenarios de la petición y ensayos completos con calidad comparable.

Antes de medir se fijan dos clases: pequeña (una unidad, un criterio y una prueba
local pertinente) y media (2–4 unidades, permisos o contrato compartido y varias
comprobaciones). El ensayo sintético mide el núcleo y el flujo reproducible; la
interacción del agente, esperas humanas y entrega real requieren observación de host.
No se mezclan ambos ni se presenta latencia de función como coste total de tarea.

Metas recibidas: consulta caliente p95 ≤2 s/fría ≤5 s; administración ≤5/15 min;
cierre ≤1/3 min; cero wrappers del recorrido normal y repeticiones injustificadas;
histórico administrativo ×10/×100 sin crecimiento documental injustificado. Se
medirá el conjunto antes/después de migración y tras ciclos completos, distinguiendo
contenido funcional útil, tarea/plan necesarios, duplicaciones y residuos de control.
Con el mismo conocimiento funcional no deben acumularse documentos por el mero
hecho de consultar, probar, autorizar o cerrar. No se impone un límite arbitrario de
bytes a una especificación útil. Se informa tamaño, repeticiones, entorno, bytes,
operaciones y límites. Los tokens facturados quedan
no observados, nunca estimados a partir de caracteres.

## Implementación de la candidata

El núcleo final usa `lks-sdd/5`, encabezados JSON legibles y tres tipos: unit, task y
plan. Los lectores de origen son directos y de solo lectura; las seis skills y los
paquetes comparten el mismo núcleo v5. Los módulos antiguos quedan fuera del paquete.
La candidata trabaja con preview exacto, disposiciones explícitas de consumidores
externos y retirada acotada del esquema. La migración es definitiva: no genera
backups ni ofrece rollback; una interrupción se reanuda hacia v5 y al finalizar se
eliminan staging y journal. Se conserva el conocimiento útil, se retira el control
histórico sustituido y las definiciones no convertibles quedan visibles para su
conciliación. Los criterios y controles conocidos pasan al modelo operativo.
Un único `docs/informe-conversion-sdd-v5.md`, emitido tras validar la conversión,
compara archivos y bytes del conjunto, desglosa control/runtime/adjuntos y documenta
unidades, tareas, criterios y pendientes. Añade un archivo separado del árbol
canónico, sin copiar fuentes ni acumular informes por elemento o ejecución normal.
Los resultados y las correcciones detectadas en la copia completa están en el plan.
La migración conserva bloqueos declarados en origen, pero no fabrica pendientes por
falta de configuración ejecutable ni obliga a reconstruir controles retirados.
Los indicadores antiguos de reconciliación son contexto, no defectos funcionales
demostrados. Las tareas terminadas no se reabren. Solicitudes, propuestas y registros
de entrega conservan su contenido sin convertirse por defecto en nuevas tareas.
Los controles vigentes mantienen su alcance por rutas y se preparan al retomar el
trabajo pertinente; resultados históricos no se presentan como pruebas actuales.
La revisión final elimina repeticiones del uso diario: los controles comunes de
hijos cerrados se reutilizan cuando la delegación de criterios es completa y las
entradas siguen vigentes; no se copian evidencias al padre. Un cambio de responsable
no cambia por sí mismo el alcance autorizado. Cada comprobación conserva solo su
último log de fallo y lo retira tras éxito, respetando ediciones ajenas. El cierre
actualiza hechos de entrega, conserva los existentes y deja lo desconocido explícito.
La política de un proyecto nuevo puede ser explícitamente vacía. El CLI valida su
integridad sin exigir una llamada adicional de doctor; las ediciones directas sí
requieren esa comprobación. Los antecedentes sin tarea propietaria se conservan
fuera de la política transversal, sin cargarlos en todas las tareas.

La puerta estable conserva aprobación de versión, fuente limpia, integridad,
veintitrés escenarios de humo actuales y rutas largas Windows. La preparación local
no sustituye el commit ni la aprobación estable. Aceptación conversacional del host,
piloto y métricas de coste total del agente se mantienen sin afirmar como superadas.
