# Definición y prototipado de frontend

## Aplicabilidad

La experiencia e interfaz es aplicable cuando el proyecto o incremento crea o modifica una superficie utilizada por una persona: pantalla web, formulario, navegación, panel, diálogo, flujo asistido u otra interacción. Registre en `ART-INCREMENTS`:

- `applicable` cuando el incremento incluye o altera interacción o presentación para una persona;
- `not-applicable` cuando no existe impacto de interfaz, siempre con motivo;
- `pending` cuando todavía no puede determinarse, explicando qué falta.

Para un incremento `applicable`, `UX contract` enlaza los elementos `UX-###` aplicables dentro de `ART-UX`. `Visual mode` distingue `pending`, `new`, `material-change`, `reuse` y `none`. `new` o `material-change` enlaza uno o más `VIS-###` o queda `pending`; `reuse` enlaza una baseline `VIS-###` confirmada y explica el alcance reutilizado; `none` usa `not-applicable: motivo` únicamente cuando el incremento no crea ni cambia pantalla, flujo, patrón de interacción o dirección visual. Si sí introduce alguno de esos cambios, un prototipo pendiente impide tratar la definición visual como suficiente.

## Base textual previa

Antes de generar imágenes, documentar como mínimo:

1. usuarios y tareas prioritarias;
2. mapa de pantallas y navegación;
3. por pantalla: entrada/salida, jerarquía, acciones principales y secundarias, permisos/roles, responsive, accesibilidad, contenido pendiente y estados aplicables;
4. flujos normales y alternativos enlazados a sus pantallas;
5. carga, vacío, error, falta de permisos, éxito, confirmación y recuperación aplicables;
6. validaciones, acciones destructivas y diálogos;
7. responsive, accesibilidad, marca, estilo, densidad y restricciones visuales;
8. requisitos y criterios de aceptación enlazados.

No usar una imagen para decidir información que todavía está abierta. Si falta una decisión que cambia sustancialmente la pantalla, mantener la dimensión `partial` y preguntar antes de generar.

## Propuestas con ImageGen

El adaptador activo determina el host, no la existencia de carpetas. En Codex nativo
se ejecuta este flujo sin avisos, preguntas ni archivos de relevo. Si Codex recibe
un relevo existente, primero valida su vigencia y continúa desde el brief conservado.
En GitHub Copilot, un brief suficiente y generación necesaria activan el protocolo
de `<plugin-root>/docs/VISUAL-HANDOFF.md`: preparar ficha, invitar una vez a Codex y
validar el resultado si se vuelve. No llamar APIs de imágenes ni instalar proveedores.
Un brief incompleto se completa en el host actual; backend y reutilización no
provocan el salto. Las confirmaciones humanas y los pendientes siguientes se conservan.

Con un brief suficiente, un cambio visual aplicable e ImageGen disponible, la generación es obligatoria antes de cerrar la definición visual. Crear entre una y tres propuestas PNG o JPG ajustadas al mismo alcance. En una aplicación nueva o rediseño material, presentar normalmente dos o tres direcciones comparables y explicar qué decisión permite contrastar cada una; si una sola propuesta es suficiente, conservar la justificación en el brief. Para extender una dirección visual ya confirmada puede bastar un prototipo fiel a esa línea. La generación visual no crea código. Cada salida empieza en estado `proposal` y debe:

- corresponder a un brief o prompt conservado;
- evitar texto ficticio como fuente de requisitos;
- quedar guardada o transferida a `docs/lks-sdd/03-solution/ui-prototypes/`;
- usar nombre estable que incluya el ID `VIS-###` y una revisión;
- comprobar existencia, formato, dimensiones y SHA-256 antes de registrarla como asset local;
- enlazarse desde la tabla de prototipos de `ART-UX` mediante Markdown relativo.

Si ImageGen, el acceso a la raíz o la transferencia no están disponibles, registrar `Visual mode=pending`, `Visual prototype=pending` y su motivo en `ART-INCREMENTS`, conservar el brief y el impacto en `ART-OPEN` y explicar el fallback. No crear una fila `VIS-###` hasta que exista un archivo local comprobable con su hash. Cualquier generación o validación no ejecutada permanece `not-run` en la evidencia; no se presenta como superada. No inventar una ruta, checksum, imagen o validación.

## Validación humana

Presentar las propuestas con las diferencias relevantes y pedir una selección, rechazo o corrección explícita. No inferir aprobación por silencio, preferencia ambigua ni continuación de la conversación. Registrar `Human validation` como `pending` o con el formato `user-confirmed; role=<rol-o-alias-no-identificativo>; date=AAAA-MM-DD; ref=ADR-###`; no inventar nombre ni autoridad. Una imagen o dirección solo pasa a `confirmed` después de validación humana explícita y de enlazar la misma decisión en su columna. Conservar como `rejected` o `superseded` las variantes descartadas cuando aporten trazabilidad.

Una baseline se reutiliza con `Visual mode=reuse`, una razón delimitada y uno o más `VIS-###` confirmados. El activo debe mantener archivo, firma, hash y ADR; esa ADR también forma parte de la dirección visual y de las decisiones del incremento actual. `Visual mode=none` nunca sustituye esta trazabilidad.

## Autoridad y precedencia

Los Markdown confirmados mandan sobre comportamiento, copy exacto, datos, reglas, estados y aceptación. Un prototipo confirmado gobierna únicamente la dirección visual y composición que `ART-UX` declara. Si imagen y Markdown se contradicen, abrir un punto pendiente y no elegir silenciosamente una interpretación.

Codex recibe conjuntamente requisitos, criterios, contrato UX y assets confirmados. La imagen no constituye evidencia de implementación ni de accesibilidad; esas evidencias se producen durante verificación.

## Referencias oficiales aplicadas

Este flujo adopta cuatro prácticas de la documentación oficial de OpenAI: sintetizar primero historias y restricciones; explorar varias direcciones visuales antes de implementar; adjuntar a Codex la referencia seleccionada; y verificar la interfaz construida en navegador y viewports representativos.

- [Get from idea to proof of concept](https://learn.chatgpt.com/use-cases/idea-to-proof-of-concept)
- [Turn user stories into UI mocks](https://learn.chatgpt.com/use-cases/user-stories-to-ui-mocks)
- [Frontend prompt instructions](https://developers.openai.com/api/docs/guides/frontend-prompt)
- [GPT Image Generation Models Prompting Guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide)
