# Revisar las especificaciones

Use esta guía para `review`, `review-proposal`, `close-proposal` y la aprobación
de una propuesta. El mensaje tendrá un título con el cambio de la aplicación y
exactamente estos apartados de segundo nivel, en este orden:

1. Objetivo.
2. Alcance incluido y excluido.
3. Comportamiento esperado.
4. Solución técnica.
5. Impacto.
6. Criterios de aceptación.
7. Decisiones pendientes.

Redacte contenido concreto en los Markdown canónicos. Una enumeración de títulos,
una ruta o «actualizar el servicio» no describen una solución validable. La parte
funcional explica actores, entradas, condiciones, resultado y errores observables.
La técnica explica cada componente real afectado y su interacción; no imponga capas
que la aplicación no tiene ni una pila preferente por defecto.

En `proposal.data.solution`, use `components` e `interactions`. Cada componente
declara `name`, `responsibility`, `current`, `change`, `contracts`, `data`, `errors`,
`verification` y `status` (`proposed` u `observed`). `evidence` identifica la fuente
si el componente es observado. Explique contratos, entradas/salidas, compatibilidad,
datos/migración y manejo de errores/permisos; cuando no cambien, diga por qué. Use
texto útil en esos campos, no palabras de relleno. Los títulos por componente son
de tercer nivel. `interactions` explica la secuencia conjunta o por qué es aislado.

Las cadenas técnicas antiguas siguen siendo consultables y sus acuerdos vigentes
se conservan. Una nueva aprobación necesita suficiente detalle. El validador de
campos detecta ausencias, pero el revisor debe contrastar precisión y coherencia.
Para un cambio acotado use una propuesta conjunta y solo componentes afectados.
Cada campo puede ser una frase concreta; referencie los contratos existentes sin
redactarlos de nuevo. Una corrección comprendida en cobertura y autorización vigentes
continúa por implementación y verificación, conservando únicamente hechos nuevos.
Incluya restricciones y criterios enlazados, prosa aplicable y adjuntos. Distinga
arquitectura observada, propuesta y cuestiones todavía desconocidas.

`review` permite leer borradores sin superar aprobación. Para una respuesta nueva,
prepare `decision-view` sobre la acción exacta, actor, petición y unidades. Una
revisión de una parte no aprueba el conjunto. Con colaboración integral cada
persona requerida revisa el paquete; `close-proposal` puede incluir su propia
conformidad con `review: true`. Use las designaciones vigentes, no firmas por rol.
Una observación bloqueante requiere tratamiento y conformidad de su autor; cargue
[correcciones](corrections.md) si existe ese caso. Una excepción conserva reservas.

Validar la especificación permite preparar el plan. No aprueba tareas futuras ni
autoriza implementación. Si cambia materialmente lo presentado, muestre el cambio
y registre la decisión sobre su nueva base. No invalide otras peticiones ni una
decisión por un cambio exclusivamente de formato.
