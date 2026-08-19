# Realidad del producto

**Guía:** 0.1

**Última comprobación:** 2026-08-19
**Ámbito:** afirmaciones dependientes de productos OpenAI

**Contrato de LKS-SDD:** Codex es el entorno objetivo soportado. Las otras superficies se documentan como contexto o fallback y no implican compatibilidad equivalente del plugin.

| Superficie o concepto | Estado comprobado | Límites y fallback | Fuente oficial |
|---|---|---|---|
| Plugin | Un plugin puede agrupar skills y, opcionalmente, MCP. Una forma skills-only es válida cuando bastan instrucciones y recursos empaquetados. | Instalación, disponibilidad y publicación dependen de la superficie y del gobierno del workspace. Este repositorio no instala ni publica. | [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins) |
| Skill | `SKILL.md` aporta nombre, descripción e instrucciones; puede incluir referencias, scripts, plantillas y assets. El modelo considera la descripción y carga instrucciones cuando coincide la intención o existe invocación directa. | La activación automática es una conveniencia, no una garantía contractual. Ante duda, invocar `$lks-sdd-help`, `$lks-sdd-define` o `$lks-sdd-assess-readiness`. | [Skills](https://developers.openai.com/plugins/concepts/skills) |
| ChatGPT Work | Puede servir como superficie auxiliar para análisis y resultados revisables. | LKS-SDD no lo declara runtime soportado. Si no hay acceso a la carpeta o al plugin, trabajar sobre fuentes adjuntas o transferir los Markdown versionados de forma explícita. | [Get started with ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work) |
| Proyecto ChatGPT | Agrupa chats, archivos, instrucciones y fuentes compartidas. No proporciona por sí solo acceso directo a una carpeta local. | Subir o conectar las fuentes necesarias. No confundir este contexto conversacional con el repositorio versionado. | [Projects and chats](https://learn.chatgpt.com/docs/projects) |
| Proyecto local y Codex | Es el entorno objetivo de LKS-SDD. Un proyecto local conecta carpetas del equipo; Codex trabaja con la raíz primaria y el árbol de trabajo actual. En CLI, el directorio de inicio o `--cd` fija la raíz. | Confirmar siempre la raíz y los permisos. Conservar orientación durable en `AGENTS.md` o documentación versionada, no solo en el chat. | [Projects and chats](https://learn.chatgpt.com/docs/projects) |

Si una capacidad no puede comprobarse en la superficie actual, declararla incierta y usar el fallback conservador. No deducir disponibilidad por una versión anterior de esta guía.
