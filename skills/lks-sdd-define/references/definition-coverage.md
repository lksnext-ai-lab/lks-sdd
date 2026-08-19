# Matriz de cobertura de definición

Revise cada dimensión con uno de cuatro estados: `unknown`, `partial`, `sufficient` o `not-applicable: motivo`. El estado se evalúa para el siguiente incremento, no como porcentaje global del proyecto.

| Dimensión | Suficiencia observable para el siguiente incremento |
|---|---|
| Problema, objetivo y valor | Problema y resultado esperado comprensibles, con medida de éxito o pendiente explícito. |
| Stakeholders y usuarios | Perfiles afectados, necesidades y autoridad de decisión diferenciadas. |
| Alcance | Incluido, excluido, supuestos y límites explícitos. |
| Funcional y reglas | Requisitos atómicos, fuente, prioridad y aceptación enlazadas. |
| Calidad | NFR medibles y estrategia de prueba proporcional al riesgo. |
| Restricciones | Condicionantes técnicos, legales, cliente, tiempo y operación con impacto. |
| Datos | Clasificación, ciclo de vida, migración o no aplicabilidad justificada. |
| Identidad, seguridad y privacidad | Necesidades y decisiones relevantes o no aplicabilidad justificada. |
| Integraciones | Sistemas, contratos, fallos y autenticación relevantes o no aplicabilidad justificada. |
| Solución y tecnología | Alternativas, encaje, riesgos, soporte y decisiones confirmadas separadas. |
| Entrega | Incremento vertical, dependencias, riesgos y alcance independiente. |
| Operación | Despliegue, observabilidad, continuidad y soporte según aplicabilidad. |

Registre la evidencia en los artefactos canónicos afectados. Use `ART-OPEN` para el vacío y su impacto; no duplique contenido sustantivo en `.lks-sdd/project.json`. Si la persona cierra deliberadamente el nivel de detalle, conserve qué se cerró, para qué alcance y qué riesgo residual permanece.
