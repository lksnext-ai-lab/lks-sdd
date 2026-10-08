# Reglas comunes para ejecutar el plan v3

Referencia: [PLAN-V3-001 / v3-plan-02](PLAN.md).
Estado actual: **planificación preparada; ejecución sin autorizar**.

## Entrada de una tarea

La autorización futura identificará revisión del plan, tareas/alcance y límites. Puede
abarcar varias tareas coherentes con el grafo y no se repite por cada fichero o comando.
Antes de actuar, comprobar rama/base, cambios existentes, disponibilidad de dependencias
y vigencia del encargo. Conservar trabajo ajeno y no reemplazar decisiones del usuario.

Entregar al agente o especialista:

- Su ficha, estas reglas y la decisión/descriptor aplicables.
- Los requisitos y casos asignados en [TRACEABILITY.md](TRACEABILITY.md), en su
  **redacción literal** y con las restricciones/dependencias compartidas pertinentes.
- Las secciones técnicas indicadas y las interfaces/resultados de tareas precedentes.
- Los archivos concretos que necesitan cambiarse y las instrucciones aplicables del repo.

La lectura inicial no carga todas las fichas, el histórico ni las 100 pruebas. La
selección no autoriza omitir prosa normativa, adjuntos o reglas globales. Si el ámbito es
incierto, ampliar y explicar la causa; nunca sustituir una obligación por su hash.

## Trabajo y decisiones

La tecnología de partida es la infraestructura Python actual del plugin. No se decide
una pila de aplicaciones consumidoras al ejecutar este plan. Conservar los contratos
v2 y sus pruebas; no seleccionar una nueva dependencia, tecnología o servicio por
comodidad. Un dato crítico que afecte al diseño aprobado requiere decisión localizada.

Los módulos nuevos son una distribución de implementación propuesta. Un cambio de
archivo/firma sin efecto contractual se registra en la ficha correspondiente; cambiar
garantías, comportamiento o aceptación requiere revisar la porción afectada de la
propuesta. No modificar `specs/canonical/` ni ajustar requisitos para acomodar el código.

No crear MCP, hooks, apps, conectores o agentes ejecutables. No publicar, instalar,
commitear, hacer push o migrar consumidores reales sin permiso específico. Las pruebas
pueden usar fixtures y repositorios temporales propios; no alteran proyectos reales.

El reparto a varios agentes, si se autoriza, debe señalar archivos que edita cada uno.
Un integrador aplica cambios de CLI, schemas y distribución compartidos. No ejecutar
dos escritores en el mismo checkout ni reemplazar el diff de otro especialista.
Los puntos de sincronización son entregables/interfases, no comprobaciones por comando.

## Inicio, cierre y control del trabajo abierto

Las fichas distinguen dependencias para iniciar trabajo independiente y para cerrar.
Empezar un parser, un mensaje o un paquete de prueba no acredita la integración pendiente.
Respetar también los resultados intermedios explícitos: `base-git-local` debe estar
probado antes de la autoría de 004 o la adopción de 011; “007 iniciada” no lo acredita.
Usar los recorridos R1–R4 del plan para entregar resultados utilizables pronto. Con una
persona se prioriza una porción activa; con equipo, solo las que tengan capacidad y
archivos asignados. No abrir frentes por el mero hecho de que lo permita el grafo.

013–017 son trabajos transversales con entregas parciales. Preparar protocolos, mensajes,
escenarios y compatibilidad temprano, conectar cada capacidad cuando sea real y cerrar
solo tras sus dependencias. Estas porciones no generan nuevos permisos, IDs ni fichas
administrativas. La autorización inicial del alcance se reutiliza mientras siga vigente.

Las fichas/PLAN Markdown son la fuente del encargo. `task-graph.json`, tablas de cobertura
y `plan-manifest.json` son vistas/identificadores derivados; una discrepancia exige
reconciliarlos desde el texto, no escoger el último JSON. Conservar instantáneas antes
de cambiar una revisión presentada. Los resultados operativos posteriores quedan fuera
del contenido normativo aprobado para no invalidarlo por actualizar progreso.

## Verificación y criterio común de terminado

Una tarea técnica puede marcarse completada cuando:

1. Entrega el comportamiento y límites de su ficha con código/documentación coherentes.
2. Sus requisitos y casos asignados tienen evidencia pertinente a la revisión exacta;
   los casos con componente humano se identifican para 017, sin darlos por aceptados.
   Un caso compuesto exige todas sus condiciones; la evidencia debe distinguir qué
   acredita el componente y qué falta integrar con sus contribuyentes.
3. Los contratos que consumen otras tareas están implementados y sus dependencias
   verificadas; no se declara integración solo con dobles de prueba.
4. Pasan las comprobaciones focales y el contrato aplicables al cambio; se revisa el diff,
   incluidos efectos en v2, trazabilidad y rutas largas si corresponde.
5. Se registran fallos pendientes, límites, decisiones necesarias y el siguiente paso.

La ficha mantiene estado de implementación técnica distinto del de aceptación integral.
Un requisito transversal solo queda acreditado completamente con 016/017 según la matriz.
No se etiqueta toda v3 lista porque hayan cerrado los módulos.

Ejecutar la validación documentada del contrato:
`python -B -X utf8 scripts/validate_plugin_contract.py .`.
Las pruebas se eligen por comportamiento/impacto, usando opciones comprobadas del runner.
No añadir tests que solo reflejen el código ni repetir baterías completas sin cambios
que lo justifiquen. Una corrección repite su escenario y regresiones materiales afectadas.

## Salida y continuidad

El resultado de la tarea incluye: cambios y por qué; alcance/UID y revisión; diff/archivos;
pruebas con resultado y artefactos recuperables; decisiones y reservas; dependencias
habilitadas; lectura mínima para quien continúe. No copiar informes enteros al chat.

Registrar en la ficha la revisión/estado de trabajo sin alterar la instantánea aprobada
del plan. Al aprobar el plan, conservar primero los bytes identificados por su descriptor
como snapshot; después las fichas de seguimiento pueden evolucionar con trazabilidad.
La revisión v3-plan-02 todavía no está aprobada: no inventar ese snapshot como aceptación.

Al completar un hito, explicar en lenguaje sencillo qué se ha completado, dónde queda
el proceso, qué falta y si el usuario debe actuar. Si el paso siguiente ya está autorizado,
continuar. Si falta permiso para una operación externa, presentar su objeto concreto y
separar esa limitación del trabajo independiente que sí puede avanzar.

## Lo que no demuestra una evidencia

- Un hash no demuestra que el contenido esté disponible ni sea correcto.
- Un fixture de Sonar no acredita conectividad ni análisis real.
- Un test automatizado no acredita comprensión humana, identidad autenticada o agilidad.
- Un paquete generado en pruebas no es una release publicada o una instalación activa.
- Una migración técnicamente íntegra no concede las autorizaciones para reanudar.
- Menos texto en el primer prompt no demuestra menos coste total ni mejor código.
