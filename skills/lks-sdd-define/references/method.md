# Método de definición

## Información y autoridad

Clasificar cada afirmación como hecho, objetivo, requisito, restricción, propuesta, decisión, supuesto, punto abierto, riesgo o evidencia. Registrar fuente y vigencia cuando importen. Una inferencia conserva su etiqueta y confianza; una propuesta requiere confirmación explícita para convertirse en decisión.

LKS-SDD es Spec-anchored: la especificación confirmada continúa vigente después de generar o modificar código. Un cambio funcional debe actualizar o reconciliar el contrato afectado antes o junto con la implementación; las huellas, planificación y autorizaciones obsoletas no se reutilizan. El código generado desde una especificación sigue necesitando revisión y verificación.

## Conversación adaptativa

1. Leer el estado versionado.
2. Interpretar la información sin inventar.
3. Si la idea aún es ambigua, realizar el encuadre inicial descrito en [entrevista de descubrimiento](discovery-interview.md) antes de asignarle un dominio, propósito o comportamiento genérico.
4. Detectar vacíos, ambigüedades, contradicciones y riesgos.
5. Actualizar solo artefactos afectados y preservar ediciones humanas.
6. Actualizar la cobertura cualitativa para el alcance o incremento declarado.
7. Mostrar un resumen compacto en los hitos de definición.
8. Formular una a tres preguntas de mayor impacto y explicar su motivo.
9. Permitir responder, diferir, justificar `not-applicable` o cerrar el nivel de detalle.

Cada dimensión se marca `unknown`, `partial`, `sufficient` o `not-applicable: motivo`. `Sufficient` significa suficiente para el alcance o siguiente incremento indicado, no terminado ni aprobado globalmente. No usar porcentajes globales de madurez.

En proyectos nuevos, escriba el contrato 1.3 (`method_version: 1.3.0`, `schema_version: 1.3`) y use las tablas, estados y relaciones declarados para cada artefacto. Los proyectos 1.0, 1.1 y 1.2 se leen en compatibilidad; la conversación de definición no los migra de forma implícita.

Antes de G2, la definición incluye tres capas inseparables del producto: arquitectura por `UNIT-###` y `BIND-###`, gobierno de entrega versionado por `CHG-###`, y planificación ejecutable `PLAN-###` → `REL-###` → `TASK-###`. El modelo de entrega se elige entre `bounded-release`, `continuous-evolution` y `maintenance-stream`; cualquier cambio posterior conserva la decisión anterior y declara fecha efectiva, impacto, transición y trigger de revisión.

Cada tarea mantiene una fila breve para seguimiento visual y una ficha independiente con definición ejecutable, dependencias, gates, estado, salud, progreso, bloqueos, revisión, build, artefacto, entorno, evidencia e historial. Una tabla por horizonte mayor evita que el tablero se convierta en un registro inmanejable.

La cobertura completa es una dimensión distinta del readiness de una tarea. `ART-PLANNING` declara el objetivo, política, ownership primario y contribuyente de cada elemento activo, confirmaciones, autorizaciones y cambios. Un plan solo queda `complete` después de validar cobertura, definiciones ejecutables, coherencia release/TASK, DAG acíclico, fronteras paralelas e integración conjunta, y de confirmar humanamente sus huellas. Sin duraciones confirmadas se describe el orden estructural, no un camino crítico inventado.

Al cerrar suficientemente una especificación, el handoff muestra de forma automática: completado; estado separado de especificación, arquitectura/automatización, planificación, porción, implementación, verificación y entrega; trabajo sin tarea; recomendación; y decisión humana. Si el plan es parcial, la opción recomendada es completar la descomposición. Trabajar por porciones exige una ADR explícita `incremental-authorized` y mantiene la incompletitud visible.

## Resumen de definición

Mostrar el resumen después del encuadre inicial, al cerrar un bloque funcional material, al consolidar solución, UX o decisiones técnicas, antes de recomendar readiness, cuando un cambio reabra una dimensión suficiente, cuando la persona pause el trabajo y cuando lo solicite. No repetirlo tras ediciones menores que no aportan orientación. Indicar siempre fase y alcance o incremento. Mantenerlo breve y legible:

- **✓ Suficiente para avanzar:** dimensiones `sufficient` para el alcance indicado.
- **△ Requiere profundización:** dimensiones `partial` y qué falta.
- **○ Aún desconocido:** dimensiones `unknown` relevantes.
- **⛔ Bloqueos:** puntos abiertos que impiden el siguiente paso, sin mezclar pendientes independientes.
- **→ Siguiente decisión:** una decisión o pregunta de máximo impacto.

Los símbolos refuerzan el escaneo, pero el texto siempre conserva el significado sin depender del color. Ofrecer el detalle completo por dimensión, pero no desplegarlo por defecto.

## Ruta

La ruta `new` puede inicializar documentación de forma aditiva. Si existen indicadores de aplicación previa, no escribir desde definición y derivar a `lks-sdd-adopt-existing`. Esa ruta separa inspección estática, reconciliación, confirmación y materialización documental; ningún paso de adopción modifica código o comportamiento.

Al recomendar readiness, separe la suficiencia de la especificación del soporte de automatización para la pila elegida. Un resultado preparado no autoriza implementación y una pila sin soporte no debe sustituirse automáticamente.
