# Configurar, adoptar o migrar un proyecto

Para configuración muestre objetivo, configuración propuesta, personas y
responsabilidades, controles y condiciones, cambios respecto a lo actual e impacto
y pendientes. Pregunte la identidad solo cuando sea necesaria y no esté declarada
en el chat; Git o Windows no la demuestran. No seleccione equipo, controles o pila
por defecto. Sonar y Dependency-Check tienen decisiones y viabilidad independientes.

Para adopción muestre alcance inspeccionado, comportamiento observado, intención
por confirmar, diferencias/desconocidos, documentos a incorporar y decisiones
pendientes. `adopt-inspect` es lectura acotada; no convierte observaciones en intención
aceptada. Un sistema sin SDD no pasa por un proyecto v2 ficticio. La consulta
`decision-view` permite preparar estos datos antes de inicializar; nunca fabrique
una aprobación para consultar cómo quedaría la configuración.

Para migración muestre situación y destino, cambios, información/acuerdos conservados,
trabajo afectado, comprobaciones/recuperación y pendientes. Lea
[migración](../V3-MIGRATION.md) únicamente cuando prepare ese cambio. Conserve
identidades, decisiones e historia; no regenere planes equivalentes ni renueve
autoridad por cambiar encabezados. Un runtime global nuevo no migra consumidores.

Para cambiar responsables, proceso o controles explique el antes y después y la
afección a trabajos en curso. Se aplica la autoridad previa competente; no rebaje
controles para fingir una aprobación. Configuración, runtime y decisiones ausentes
pueden agruparse sobre contenido ya mostrado. Una consulta no inicia migración.
Ante interrupción, lea [recuperación](exceptions-continuity.md).
