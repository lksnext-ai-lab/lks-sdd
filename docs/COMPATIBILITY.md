# Compatibilidad y entorno objetivo

## Decisión de producto

**Estado:** decisión confirmada para la implementación del plugin.

LKS-SDD es un plugin de desarrollo guiado por especificaciones (SDD) para Codex. Codex es el entorno objetivo y el único soportado contractualmente. Las capacidades, descripciones, prompts, validadores y workflows de implementación y verificación se diseñan y evalúan en ese contexto.

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
- los workflows que inspeccionan, implementan o verifican código con Codex.

## Compatibilidad de contrato

| Proyecto consumidor | Validación | Evolución |
|---|---|---|
| Nuevo con LKS-SDD 0.7.0 | Método `1.1.0` y esquema `1.1`, con contrato estricto por tabla | Es el formato activo para nuevas inicializaciones y adopciones materializadas. |
| Existente con esquema `1.0` | Válido en modo de compatibilidad, con avisos para sintaxis o estados legacy | La actualización del plugin no lo modifica. La migración 1.0 → 1.1 es explícita y puede requerir revisión humana. |
| Existente con esquema `0.9` | No salta directamente a 1.1 | Se conserva la ruta histórica 0.9 → 1.0 mediante `--target-schema 1.0`; cada salto se prepara, autoriza y valida por separado. |

El formato 1.1 usa listas separadas por coma o punto y coma y rangos inclusivos `FR-001..FR-079`. La forma `FR-001 a FR-079` y las listas separadas únicamente por espacios son compatibilidad 1.0 con aviso, no sintaxis nueva. Ningún modo acepta expansiones parciales silenciosas.

## CLI portable del plugin

`<plugin-root>` es la carpeta instalada que contiene `.codex-plugin/plugin.json`; `<project-root>` es la raíz del proyecto consumidor. Son ubicaciones distintas y no se debe resolver `scripts/` contra el consumidor. Los comandos operativos soportados se despachan así, independientemente del directorio personal donde esté instalado el plugin:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>" --json
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation --json
python "<plugin-root>/scripts/lks_sdd.py" assess-readiness "<project-root>" --increment INC-001 --json
python "<plugin-root>/scripts/lks_sdd.py" migrate "<project-root>" --target-schema 1.1 --dry-run
```

El dry-run de migración devuelve un hash y la lista `human_review_required`. Los estados legacy `fact`, `requirement` o `assumption` se proponen como `draft`. Si la lista contiene entradas, `--apply` falla siempre antes de crear el backup o escribir archivos: revisar o aceptar la lista no basta. Resuelva cada entrada listada en los Markdown canónicos 1.0, valide el proyecto y repita el dry-run hasta obtener una lista vacía.

La antigua dimensión agregada `Identity` no puede separarse dentro de la tabla 1.0. Por ello, la migración crea las filas de identidad, seguridad y privacidad como `pending`, sin referencias activas inferidas y con un extracto seguro del valor anterior en el motivo. Esas filas no forman parte de `human_review_required`: si no hay otras entradas, la migración puede aplicarse y el resultado valida, pero readiness del incremento permanece bloqueado hasta que los tres dominios se resuelvan explícitamente en los Markdown 1.1. La aplicación sigue exigiendo autorización, backup externo y el hash exacto; la actualización o recarga del plugin nunca sustituye ese consentimiento. Use siempre la ayuda incluida en la versión instalada para los argumentos disponibles.

## Capacidad condicional de ImageGen

La definición visual v0.6 puede solicitar ImageGen cuando la superficie Codex activa exponga esa capacidad, el frontend o cambio visual lo haga aplicable y exista un brief suficiente. ImageGen no forma parte del manifiesto del plugin, no se empaqueta como MCP, app, conector o agente y su disponibilidad no se presume.

Si está disponible, el flujo genera entre una y tres propuestas para validación humana. Si no lo está, se conserva la especificación textual y el estado `not-run` o pendiente correspondiente; no se fabrica un archivo ni se declara una validación visual. La posibilidad de generar imágenes en otra superficie no demuestra compatibilidad del plugin completo con ella.

## Regla para futuras integraciones

No se presentará LKS-SDD como plugin agnóstico ni como compatible con otro asistente por similitud de formato. Añadir un entorno requiere una decisión explícita, un contrato de integración propio, pruebas representativas y documentación de las diferencias de comportamiento y seguridad.
