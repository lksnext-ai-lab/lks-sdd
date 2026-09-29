# Entrada de Copilot sin runtime fijado

Resuelva la raíz del plugin desde el archivo de la skill instalada, nunca desde el
directorio de trabajo ni una variable inventada. Para ayuda, lea la skill help del
core y la guía desde cero en modo de solo lectura. Una consulta no inicializa nada.

Para definir, adoptar o implementar un proyecto sin lock, presente la preparación
concreta mediante setup/install.py copilot <proyecto> del plugin instalado.
Obtenga su preview; --apply --authorize HASH solo aplica los cambios comprendidos
en la autorización actual. No repita una aprobación vigente ni instale globalmente.
Un proyecto existente de otro formato necesita su migración explícita, no una
sustitución silenciosa de runtime. No active a la vez plugin y skills de proyecto.

Después cargue la skill desde el runtime fijado y sus referencias completas, con
herramientas del host actual. Para trabajo visual, lea la sección correspondiente
de HOST-COPILOT-DETAILS.md. Copilot no llama ImageGen ni una API de imágenes;
conserva el relevo documentado a Codex y los pendientes de aceptación.

Mantenga todos los controles del método, decisiones humanas y límites de commit,
push y publicación. No configure proveedores, MCP ni permisos personales.
