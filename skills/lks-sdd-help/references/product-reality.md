# Realidad del producto

**Guía:** 0.3

**Última comprobación:** 2026-08-21
**Ámbito:** afirmaciones dependientes de productos OpenAI

**Contrato de LKS-SDD:** Codex es el entorno objetivo soportado. Las otras superficies se documentan como contexto o fallback y no implican compatibilidad equivalente del plugin.

| Superficie o concepto | Estado comprobado | Límites y fallback | Fuente oficial |
|---|---|---|---|
| Plugin | Un plugin puede agrupar skills y, opcionalmente, MCP. Una forma skills-only es válida cuando bastan instrucciones y recursos empaquetados. | Publicación técnica, actualización del marketplace e instalación activa son estados distintos. LKS-SDD 0.14.1 sigue siendo candidate, no equivale a distribución estable y no se carga en una tarea ya abierta. | [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins) |
| Skill | `SKILL.md` aporta nombre, descripción e instrucciones; puede incluir referencias, scripts, plantillas y assets. El modelo considera la descripción y carga instrucciones cuando coincide la intención o existe invocación directa. | La activación automática es una conveniencia, no una garantía contractual. Ante duda, invocar `$lks-sdd-help`, `$lks-sdd-define` o `$lks-sdd-assess-readiness`. | [Skills](https://developers.openai.com/plugins/concepts/skills) |
| ChatGPT Work | Puede servir como superficie auxiliar para análisis y resultados revisables. | LKS-SDD no lo declara runtime soportado. Si no hay acceso a la carpeta o al plugin, trabajar sobre fuentes adjuntas o transferir los Markdown versionados de forma explícita. | [Get started with ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work) |
| Proyecto ChatGPT | Agrupa chats, archivos, instrucciones y fuentes compartidas. No proporciona por sí solo acceso directo a una carpeta local. | Subir o conectar las fuentes necesarias. No confundir este contexto conversacional con el repositorio versionado. | [Projects and chats](https://learn.chatgpt.com/docs/projects) |
| Proyecto local y Codex | Es el entorno objetivo de LKS-SDD. Un proyecto local conecta carpetas del equipo; Codex trabaja con la raíz primaria y el árbol de trabajo actual. En CLI, el directorio de inicio o `--cd` fija la raíz. | Confirmar siempre la raíz y los permisos. Conservar orientación durable en `AGENTS.md` o documentación versionada, no solo en el chat. | [Projects and chats](https://learn.chatgpt.com/docs/projects) |

Si una capacidad no puede comprobarse en la superficie actual, declararla incierta y usar el fallback conservador. No deducir disponibilidad por una versión anterior de esta guía.

Para los comandos internos de LKS-SDD, resuelva `<plugin-root>` desde la instalación que contiene `.codex-plugin/plugin.json` y use `python "<plugin-root>/scripts/lks_sdd.py" <comando> "<project-root>"`. Esta CLI del plugin no debe confundirse con los comandos de gestión del marketplace de Codex. Para estos últimos, la ayuda de la versión de Codex instalada es la fuente operativa: no documente subcomandos que esa ayuda no anuncie. Tras una actualización autorizada, confirme la versión resuelta, reinicie Codex y abra una tarea nueva antes de atribuir comportamiento a la release nueva.
