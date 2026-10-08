# LKS-SDD v3 · flujo de equipo simplificado

## Ajuste final de identidad visual

Edit the supplied infographic with one very focused identity clarification. Preserve ALL wording, composition, colors, connectors, milestone positions, other portraits, logo and footer unchanged.

At the "Validación funcional" milestone near the right, replace its current avatar with an unmistakably IDENTICAL miniature of the functional responsible woman shown at the far LEFT starting "Petición y requisitos": same wavy shoulder-length dark hair, same facial features, same teal jacket and white shirt, same pose. This must clearly be the SAME PERSON returning at the end, and must NOT look like the straight-haired Frontend specialist.
Above this final small portrait, in the available whitespace, add the concise two-line role label "Responsable funcional" in dark petroleum, legible but smaller than the milestone heading. Do not move or compress the process to do this. Keep the final avatar small, equal in size to the other milestone avatars.
Also make the first avatar slightly smaller than it currently is, while preserving its exact identity and local label positioning, so avatars consistently support the process.
Do not change any other text or line, especially the fork starting before validation, the two approval gates, specialist paths, integration and the CI/CD return. Keep 16:9 landscape and high typography clarity.

Generación: herramienta integrada ImageGen.
Referencia visual: `lks-sdd-v3-equipo-cicd-v2.png`.
Objetivo: una línea de proceso que se bifurca por especialidades desde la validación técnica y vuelve a unirse en la integración; la misma persona funcional define y acepta.

## Prompt

Deliverable
Redesign the supplied LKS infographic completely as ONE polished Spanish corporate infographic, landscape 16:9, preferably 1920 x 1080. Use ImageGen. Input image 1 is a branding and character-reference source only: keep the LKS header treatment, outlined orange logo and copyright, but REPLACE THE WHOLE BODY COMPOSITION. The old row of cards and excess roles must disappear.

Audience and objective
Explain a configured TEAM workflow supported by LKS-SDD v3 to functional leads and developers. The dominant object must be a left-to-right PROCESS LINE that forks into THREE long specialist paths, and then converges back into ONE path for integration and acceptance before PR. Small human avatars mark when people participate. The SAME functional responsible person starts and ends the process. Specialists participate from technical proposal validation through planning, implementation and verification of their respective parts. Avatars support the process; they are not the main illustrations.

Exact content
Header title: "LKS-SDD v3 · del requisito al PR"
Header subtitle: "Un responsable funcional y especialistas que colaboran en una misma petición."
Local small context above the diagram: "Ejemplo: solicitud y aprobación de vacaciones"

Main process, in strict order:
1. Shared starting milestone: "Petición y requisitos"
   Owner: "Responsable funcional"
   Small explanatory label: "Define necesidad, reglas y aceptación"

Then fork into three specialist paths. Their direct labels and example deliverables:
"Frontend" / "Formulario y estado"
"Backend" / "Reglas y API"
"BBDD" / "Datos e historial"

ALL THREE PATHS go through FOUR aligned stages, left to right. Use column headings above the paths, with tiny milestones and small recurring avatars on each path:
"Validar propuesta"
"Planificar"
"Implementar"
"Verificar su parte"

Between "Validar propuesta" and "Planificar", place a distinct shared procedural checkpoint across all three paths, with a SMALL avatar of the functional responsible person and tiny specialist portraits if useful. Its exact label is:
"Propuesta funcional y técnica validada"
This is joint validation of a concrete solution, BEFORE planning.

Between "Planificar" and "Implementar", show a more compact shared procedural checkpoint:
"Plan aprobado y ejecución autorizada"
Associate this checkpoint with a small functional responsible avatar. The specialists plan the tasks and dependencies of their parts, and the configured responsible person approves/authorizes.

After ALL THREE specialist paths finish verification, converge into a single shared line:
"Integración"
Under it: "El equipo comprueba el conjunto"
Associate it with the same three small specialist avatars; DO NOT invent another integrator person.

Next, on the single line:
"Validación funcional"
Under it: "Comprueba lo acordado y acepta"
Associate it with the EXACT SAME small functional avatar from the start. This is before PR, after technical integration. This person validates end-to-end behavior against requirements.

Finally the line exits the LKS-SDD scope into a slim clearly separated external project-delivery zone:
"PR"
then "CI/CD del proyecto"
then "Despliegue"
Keep this tail small and subordinate, with simple line icons, no extra human persona. CI/CD belongs to the project and is outside the plugin's execution scope.

Local quality annotation attached only to specialist implementation / verification:
"Pruebas · Sonar · Dependency-Check"
"Según la configuración del proyecto"

Tiny process-specific traceability annotation:
"Una petición y su rama · tareas, responsables y evidencias vinculados"

A subordinate thin dashed RETURN connector from the CI/CD tail toward the process, visually much lighter than the main fork:
"Problemas de CI/CD: vincular a la petición y a las tareas afectadas"
Under this connector, small concise note:
"Corregir la tarea; revalidar la propuesta si cambia el alcance."
This is a conceptual feedback route, not a claim of automatic integration.

Footer exactly: "© LKS NEXT 2026 – Todos los derechos reservados"

Composition
Make the central branched process occupy approximately 65-70% of the BODY height and most of its width. Use elegant railway/metro-style or precise technical flow lines, clear right-facing arrows, round nodes and gentle curves. DO NOT put phases into cards, panels, boxes or separate illustrations. Work with generous white space and direct labels.
Suggested relative layout: shared start at far left (10% width), fork around 20%; three horizontal lanes through the middle (24-64% width), reconverge around 71%; integration at 75%, functional validation at 85%; external PR/CI/CD tail at far right. Let lane heights be distinct and spread out, not cramped. The branch paths MUST already be separate during validation AND planning; they must not branch only at implementation.
Use 4 aligned column headings over the parallel section, and carefully separate the two approval checkpoints from those headings. Thin vertical orange checkpoint markers crossing the lanes, with their short labels above or below the diagram, can convey shared gates. Keep connectors visible, every path connected, no ambiguous ends or crossing text. Implement the mandatory chronology exactly.
Small circular adult professional avatar portraits (about 40-52 pixels on a 1920-wide canvas) sit adjacent to milestones, never large bust illustrations. Reuse the same specialist identity along its lane. Only FOUR human identities total: one functional responsible woman with dark wavy hair and teal jacket; one Frontend woman with straight dark hair; one Backend man with glasses; one BBDD man with curly hair and beard. Do not duplicate any of these as a new role. A few repeated avatars at key stages help reading; no separate roles legend, and no large portraits.

LKS visual system
White editorial corporate content-slide background. Preserve the supplied small upper-right orange outlined LKS Next logo, title at upper-left, short orange rule and subtitle. A clean matte technical design, restrained and modern. Title moderate charcoal Poppins-like semibold; Inter-like labels. Petroleum #102C36 and graphite #33444C for type and shared line; slate #58788E, teal #438C8B and muted petroleum differentiate specialist paths; orange #F85900 for shared approvals and directional emphasis. Pale #E8EFF2 only if needed behind small annotations. No gradients, glows or glossy 3D. All body elements inside generous content margins; footer small bottom-left. Make each Spanish label crisp, spelled correctly and legible.

Constraints
Do not retain the reference's card grid or large avatars. No extra "responsable técnico", "revisor", "integrador" or "DevOps" characters. No new roles legend. No suggestion that functional acceptance replaces technical integration testing. Do not label integration as merge into main. No claim that Sonar applies when unconfigured. No claim of automatic CI/CD connector. No invented data or copy. No bottom conclusion ribbon, summary band, slogan, decorative background, stock photo or watermark. Do not generate a different logo. Prioritize the intelligible fork-and-rejoin process over decoration and fit all content without tiny text.
