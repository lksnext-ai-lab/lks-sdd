# Compatibilidad y entorno objetivo

## Decisión de producto

**Estado:** decisión confirmada para la implementación del plugin.

LKS-SDD es un plugin de desarrollo guiado por especificaciones (SDD) para Codex. Codex es el entorno objetivo y el único soportado contractualmente. Las capacidades, descripciones, prompts, validadores y futuros workflows de implementación y verificación deben diseñarse y evaluarse en ese contexto.

Esta decisión no modifica las fuentes de `specs/canonical/`; delimita el producto que se implementa a partir de ellas.

## Matriz de compatibilidad

| Entorno | Estado | Alcance |
|---|---|---|
| Codex | Objetivo soportado | Manifiesto del plugin, skills, invocación implícita, acceso autorizado al repositorio y ejecución de validadores locales. |
| ChatGPT Work | Superficie auxiliar, no runtime soportado | Puede ayudar a analizar o revisar documentos transferidos, incluidos briefs y propuestas visuales, pero no se promete que ejecute este plugin o ImageGen con el mismo contrato que Codex. |
| GitHub Copilot | No soportado ni verificado | No se ha implementado packaging, descubrimiento, instrucciones ni evaluación específicos para Copilot. |
| Claude o Claude Code | No soportado ni verificado | No se ha implementado packaging, descubrimiento, instrucciones ni evaluación específicos para estos entornos. |
| Otros asistentes | Fuera de alcance | Requieren un análisis y una validación independientes antes de declarar compatibilidad. |

## Qué puede ser portable

Los Markdown canónicos de un proyecto consumidor, los esquemas JSON y los scripts Python sin dependencias externas usan formatos generales. Pueden servir como base para otra integración, pero su reutilización aislada no demuestra compatibilidad del plugin ni equivalencia de resultados.

Son específicos del contrato de Codex:

- `.codex-plugin/plugin.json` y su presentación en la interfaz;
- el descubrimiento por descripciones y la invocación implícita de skills;
- los metadatos `agents/openai.yaml`;
- la interpretación de instrucciones, permisos y raíces de trabajo;
- los futuros workflows que inspeccionen, implementen o verifiquen código con Codex.

## Capacidad condicional de ImageGen

La definición visual v0.6 puede solicitar ImageGen cuando la superficie Codex activa exponga esa capacidad, el frontend o cambio visual lo haga aplicable y exista un brief suficiente. ImageGen no forma parte del manifiesto del plugin, no se empaqueta como MCP, app, conector o agente y su disponibilidad no se presume.

Si está disponible, el flujo genera entre una y tres propuestas para validación humana. Si no lo está, se conserva la especificación textual y el estado `not-run` o pendiente correspondiente; no se fabrica un archivo ni se declara una validación visual. La posibilidad de generar imágenes en otra superficie no demuestra compatibilidad del plugin completo con ella.

## Regla para futuras integraciones

No se presentará LKS-SDD como plugin agnóstico ni como compatible con otro asistente por similitud de formato. Añadir un entorno requiere una decisión explícita, un contrato de integración propio, pruebas representativas y documentación de las diferencias de comportamiento y seguridad.
