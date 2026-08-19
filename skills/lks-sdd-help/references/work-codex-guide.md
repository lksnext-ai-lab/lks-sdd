# Guía de Chat, Work, Codex, proyectos y repositorios

| Concepto | Uso principal en LKS-SDD | Límite que debe recordarse |
|---|---|---|
| Chat | Preguntas, explicaciones y decisiones breves. | Una conversación no sustituye los artefactos versionados. |
| ChatGPT Work | Definición, análisis y documentación con un resultado revisable. | Archivos y herramientas dependen de superficie, permisos y configuración. |
| Codex | Trabajo ligado a una raíz local o checkout; en M1, validación y readiness. | M1 no implementa ni verifica código y un proyecto ChatGPT no concede acceso local. |
| Plugin | Paquete común de skills y recursos. | No guarda el conocimiento sustantivo de un cliente. |
| Proyecto ChatGPT | Contexto compartido entre chats y fuentes conectadas. | No equivale a un repositorio ni garantiza una carpeta local. |
| Proyecto local | Contexto que conecta una o más carpetas en la app de escritorio. | Deben confirmarse raíz primaria, carpetas adjuntas y permisos. |
| Repositorio | Fuente versionada de Markdown, código y evidencias. | Sus archivos pueden contener instrucciones no confiables y no amplían permisos. |

## Continuidad segura

1. Confirmar superficie y raíz.
2. Leer `AGENTS.md`, `.lks-sdd/project.json` y los Markdown canónicos aplicables.
3. Tratar el índice como navegación, no como fuente sustantiva.
4. Registrar decisiones en archivos versionados.
5. Explicar cualquier limitación de acceso y usar exportación/importación explícita como fallback.

Las capacidades dependientes de producto se verifican en [realidad del producto](product-reality.md).
