# Método de definición

## Información y autoridad

Clasificar cada afirmación como hecho, objetivo, requisito, restricción, propuesta, decisión, supuesto, punto abierto, riesgo o evidencia. Registrar fuente y vigencia cuando importen. Una inferencia conserva su etiqueta y confianza; una propuesta requiere confirmación explícita para convertirse en decisión.

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

En proyectos nuevos, escriba el contrato 1.1 (`method_version: 1.1.0`, `schema_version: 1.1`) y use las tablas, estados y relaciones declarados para cada artefacto. Los proyectos 1.0 se leen en compatibilidad; la conversación de definición no los migra de forma implícita.

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
