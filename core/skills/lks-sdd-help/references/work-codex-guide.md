# Guía de Codex, ChatGPT Work, proyectos y repositorios

LKS-SDD tiene distribuciones para Codex desktop y Copilot en VS Code Agent. El
plugin personal aporta las entradas; el proyecto compartido fija el núcleo.
Consulte la [guía desde cero](../../../docs/LEARNING-GUIDE.md) y la
[instalación](../../../docs/INSTALLATION.md). Las superficies auxiliares no se
convierten por ello en runtimes equivalentes; la aceptación real se informa aparte.

| Concepto | Uso principal en LKS-SDD | Límite que debe recordarse |
|---|---|---|
| Chat | Preguntas, explicaciones y decisiones breves. | Una conversación no sustituye los artefactos versionados. |
| ChatGPT Work | Apoyo auxiliar para definición, análisis o revisión de documentos transferidos. | No se garantiza que ejecute este plugin con el contrato de Codex. |
| Codex | Entorno soportado, ligado a una raíz local o checkout; ejecuta los workflows M0–M5 y el contrato 1.5 de definición, planificación integral, tracking/reporting opcional, continuidad, perfiles, adopción, readiness, implementación, verificación, calidad y piloto controlado. | Las escrituras, instalaciones y ejecuciones requieren sus autorizaciones; un proyecto ChatGPT no concede acceso local. |
| Copilot en VS Code | Destino del plugin de agente con las seis capacidades y núcleo fijado. | Las imágenes requieren relevo a Codex; permisos, navegador y peers se validan en el host real. |
| Plugin | Paquete de skills y recursos con distribución propia para cada host. | No guarda el conocimiento sustantivo de un cliente ni sustituye el estado del proyecto. |
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

En el plugin nativo Copilot la raíz instalada contiene `plugin.json`, `skills/`,
`core/` y `setup/`. Sus wrappers resuelven `<plugin-root>` al runtime del lock del
consumidor; sin proyecto, solo la ayuda usa `core/`. Los siguientes paths se refieren
al núcleo, no a la carpeta exterior del plugin Copilot.

- `<plugin-root>` contiene `.codex-plugin/plugin.json`, `skills/` y `scripts/lks_sdd.py`;
- `<project-root>` contiene `.lks-sdd/project.json`, `docs/lks-sdd/` y, cuando exista, el código de la aplicación.

El patrón portable es `python "<plugin-root>/scripts/lks_sdd.py" <comando> "<project-root>"`. El dispatcher ofrece `help`, `define`, adopción, readiness, `planning`, `tracking`, implementación, `continuity`, verificación, `tasks`, `local technology declaration`, validación, trazabilidad y vistas cliente; no incluye migrador de proyectos.

Los proyectos materializados por 0.15.0 usan método 1.5.0 y esquema 1.5, único contrato operativo. El índice puede conservar un `plugin_version` anterior como procedencia. El runtime no migra ni reescribe proyectos y rechaza otros schemas sin inferir confirmaciones, mappings, avance, evidencia o escrituras Jira.

Los prototipos visuales generados en una superficie sin acceso a la raíz no se consideran assets locales por aparecer en el chat. Deben transferirse explícitamente a `docs/lks-sdd/03-solution/ui-prototypes/`, comprobar formato, dimensiones y SHA-256, enlazarse desde `ART-UX` y conservarse como `proposal` hasta validación humana. Si la transferencia no se ha realizado, el estado es `pending`.

Las capacidades dependientes de producto se verifican en [realidad del producto](product-reality.md).
