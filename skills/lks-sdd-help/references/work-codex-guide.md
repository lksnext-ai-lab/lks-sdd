# Guía de Codex, ChatGPT Work, proyectos y repositorios

LKS-SDD se desarrolla y soporta como plugin para Codex. Las demás superficies de esta tabla describen posibles apoyos o mecanismos de transferencia de contexto, no runtimes equivalentes del plugin.

| Concepto | Uso principal en LKS-SDD | Límite que debe recordarse |
|---|---|---|
| Chat | Preguntas, explicaciones y decisiones breves. | Una conversación no sustituye los artefactos versionados. |
| ChatGPT Work | Apoyo auxiliar para definición, análisis o revisión de documentos transferidos. | No se garantiza que ejecute este plugin con el contrato de Codex. |
| Codex | Entorno soportado, ligado a una raíz local o checkout; ejecuta los workflows M0–M5 de definición, adopción, readiness, implementación, verificación, calidad y piloto controlado. | Las escrituras, instalaciones y ejecuciones requieren sus autorizaciones; un proyecto ChatGPT no concede acceso local. |
| Plugin | Paquete de Codex con skills y recursos. | No guarda el conocimiento sustantivo de un cliente ni declara portabilidad automática a otros asistentes. |
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
