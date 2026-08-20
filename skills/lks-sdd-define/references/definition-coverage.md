# Matriz de cobertura de definición

Revise cada dimensión con uno de cuatro estados: `unknown`, `partial`, `sufficient` o `not-applicable: motivo`. El estado se evalúa para el siguiente incremento, no como porcentaje global del proyecto.

| Dimensión | Suficiencia observable para el siguiente incremento |
|---|---|
| Contexto profesional, problema y valor | Dominio, proceso actual, problema, tarea o decisión asistida y resultado esperado comprensibles, con medida de éxito o pendiente explícito. |
| Stakeholders, usuarios y uso | Perfiles afectados, necesidades, situación de uso y autoridad de decisión diferenciadas. |
| Alcance | Incluido, excluido, supuestos y límites explícitos. |
| Funcional, entradas y reglas | Requisitos atómicos; entradas, unidades, reglas, excepciones y fuentes autorizadas; prioridad y aceptación enlazadas. |
| Experiencia e interfaz | Aplicabilidad confirmada; para frontend, pantallas, flujos, estados, diálogos, accesibilidad, dirección visual y validación de prototipos suficientes para el incremento. |
| Calidad | NFR medibles y estrategia de prueba proporcional al riesgo. |
| Restricciones | Condicionantes técnicos, legales, cliente, tiempo y operación con impacto. |
| Datos | Clasificación, ciclo de vida, migración o no aplicabilidad justificada. |
| Identidad, seguridad y privacidad | Necesidades y decisiones relevantes o no aplicabilidad justificada. |
| Integraciones | Sistemas, contratos, fallos y autenticación relevantes o no aplicabilidad justificada. |
| Solución y tecnología | Alternativas, encaje, riesgos, soporte y decisiones confirmadas separadas. |
| Entrega | Incremento vertical, dependencias, riesgos y alcance independiente. |
| Operación | Despliegue, observabilidad, continuidad y soporte según aplicabilidad. |

Registre el estado resumido en la tabla de cobertura de `ART-STATUS` y la evidencia sustantiva en los artefactos canónicos afectados. Use `ART-OPEN` para el vacío y su impacto; no duplique contenido sustantivo en `.lks-sdd/project.json`. Si la persona cierra deliberadamente el nivel de detalle, conserve qué se cerró, para qué alcance y qué riesgo residual permanece.

`Sufficient` solo significa que hay información suficiente para avanzar en el alcance indicado. Para una interfaz aplicable, una imagen no vuelve suficiente la dimensión si faltan comportamiento, copy, estados o aceptación en Markdown. Un prototipo requerido permanece `proposal` hasta validación humana explícita.
