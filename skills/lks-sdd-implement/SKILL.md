---
name: lks-sdd-implement
description: "Use with Codex. Implement or resume authorized LKS-SDD tasks, preserve complete scope and context, coordinate handoffs, and correct applicable Sonar and dependency findings."
---

# Implementar y corregir

Antes de anunciar implementación o editar código de aplicación, compruebe qué
especificación validada, plan aprobado y tareas autorizadas cubren la petición
concreta. Explique brevemente esa cobertura con referencias. Si falta o cambia el
alcance, use `lks-sdd-define` para documentar, validar y planificar primero.
«Implementa estos cambios» no permite asumir documentos o aprobaciones inexistentes.
Las decisiones aplazadas deben quedar registradas; compruebe su impacto antes de
separar trabajo independiente. Reutilice decisiones vigentes sin pedirlas otra vez.

Lea el formato de `.lks-sdd/project.json` y respete el runtime fijado por el proyecto.
No migre por cargar esta skill. Si falta el índice, inspeccione el Markdown antes de
asumir un proyecto nuevo. Una garantía desconocida bloquea solo el trabajo afectado.

- Para formato **3.0 o 3.1**, lea [reglas comunes v3](../../docs/V3-COMMON.md) y
  [esta operación](references/v3.md).
- Para **2.0 o 1.5**, lea solo [procedimiento conservado](references/v2-and-legacy.md).
- Para un proyecto sin SDD, confirme configuración y use v3 si se solicita iniciar
  o adoptar; una consulta no inicializa nada.

Cargue únicamente la ruta aplicable. Al confirmar un hito, explique qué se ha hecho,
dónde queda el proceso, qué falta y la próxima acción. Si ya está autorizada, continúe.
