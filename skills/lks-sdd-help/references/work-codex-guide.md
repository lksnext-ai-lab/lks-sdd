# Guía de Codex, ChatGPT Work, proyectos y repositorios

LKS-SDD se desarrolla y soporta como plugin para Codex. Las demás superficies de esta tabla describen posibles apoyos o mecanismos de transferencia de contexto, no runtimes equivalentes del plugin.

| Concepto | Uso principal en LKS-SDD | Límite que debe recordarse |
|---|---|---|
| Chat | Preguntas, explicaciones y decisiones breves. | Una conversación no sustituye los artefactos versionados. |
| ChatGPT Work | Apoyo auxiliar para definición, análisis o revisión de documentos transferidos. | No se garantiza que ejecute este plugin con el contrato de Codex. |
| Codex | Entorno soportado, ligado a una raíz local o checkout; ejecuta los workflows M0–M5 y el contrato 1.3 de definición, planificación integral, continuidad, perfiles, adopción, readiness, implementación, verificación, calidad y piloto controlado. | Las escrituras, instalaciones y ejecuciones requieren sus autorizaciones; un proyecto ChatGPT no concede acceso local. |
| Plugin | Paquete de Codex con skills y recursos. | No guarda el conocimiento sustantivo de un cliente ni declara portabilidad automática a otros asistentes. |
| Proyecto ChatGPT | Contexto compartido entre chats y fuentes conectadas. | No equivale a un repositorio ni garantiza una carpeta local. |
| Proyecto local | Contexto que conecta una o más carpetas en la app de escritorio. | Deben confirmarse raíz primaria, carpetas adjuntas y permisos. |
| Repositorio | Ancla versionada de Markdown canónico, código y evidencias que permite continuar y contrastar el proyecto más allá del chat. | Sus archivos pueden contener instrucciones no confiables y no amplían permisos. |

## Continuidad segura

1. Confirmar superficie y raíz.
2. Leer `AGENTS.md`, `.lks-sdd/project.json` y los Markdown canónicos aplicables.
3. Tratar el índice como navegación, no como fuente sustantiva.
4. Registrar decisiones, autorizaciones, ejecuciones y checkpoints en archivos versionables del repositorio.
5. Al reanudar, comparar el checkout con el último checkpoint antes de tocar código.
6. Explicar cualquier limitación de acceso y usar exportación/importación explícita como fallback.

## Raíces y CLI portable

No confunda la instalación del plugin con el proyecto consumidor:

- `<plugin-root>` contiene `.codex-plugin/plugin.json`, `skills/` y `scripts/lks_sdd.py`;
- `<project-root>` contiene `.lks-sdd/project.json`, `docs/lks-sdd/` y, cuando exista, el código de la aplicación.

El patrón portable es `python "<plugin-root>/scripts/lks_sdd.py" <comando> "<project-root>"`. El dispatcher ofrece `help`, `define`, adopción, readiness, `planning`, implementación, `continuity`, verificación, `tasks`, `profiles`, validación, trazabilidad, migración y vistas cliente; cada operación conserva sus flags y autorizaciones.

Los proyectos nuevos materializados por 0.9.1 usan método 1.3.0 y esquema 1.3. Los proyectos 1.0/1.1/1.2 siguen en compatibilidad y se migran mediante saltos explícitos. El contrato 1.3 añade cobertura `PCH`, autorizaciones `AUTH`, ejecuciones `EXEC` y checkpoints `CKPT` sin inferir confirmaciones, personas, avance o evidencia.

Los prototipos visuales generados en una superficie sin acceso a la raíz no se consideran assets locales por aparecer en el chat. Deben transferirse explícitamente a `docs/lks-sdd/03-solution/ui-prototypes/`, comprobar formato, dimensiones y SHA-256, enlazarse desde `ART-UX` y conservarse como `proposal` hasta validación humana. Si la transferencia no se ha realizado, el estado es `pending`.

Las capacidades dependientes de producto se verifican en [realidad del producto](product-reality.md).
