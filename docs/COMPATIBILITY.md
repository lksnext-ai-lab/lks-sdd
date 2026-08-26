# Compatibilidad y entorno objetivo

## Decisión de producto

LKS-SDD 0.11.0 es un plugin Spec-anchored de SDD para Codex. Codex es el entorno objetivo y el único soportado contractualmente. El manifiesto, el descubrimiento de skills, los prompts, los permisos y los workflows se diseñan y evalúan en ese contexto. Atlassian Rovo puede actuar como peer opcional para Jira, pero no es un runtime alternativo ni forma parte del bundle.

| Entorno | Estado | Alcance |
|---|---|---|
| Codex | Objetivo soportado | Seis skills, repositorio local autorizado, validadores, implementación y verificación por perfiles certificados. |
| ChatGPT Work | Superficie auxiliar | Puede analizar documentos transferidos; no se promete ejecución equivalente del plugin. |
| GitHub Copilot | No soportado ni verificado | Sin packaging, contrato de permisos ni evals específicos. |
| Claude o Claude Code | No soportado ni verificado | Sin integración o evidencia de comportamiento equivalente. |
| Otros asistentes | Fuera de alcance | Requieren diseño, seguridad y validación independientes. |

Los Markdown, JSON Schema y scripts Python pueden ser técnicamente reutilizables. Esa portabilidad de formato no convierte el plugin en agnóstico ni demuestra equivalencia de resultados.

## Compatibilidad del contrato de proyecto

| Proyecto consumidor | Validación | Evolución |
|---|---|---|
| Nuevo con LKS-SDD 0.11.0 | Método candidate `1.5.0`, esquema `1.5` | Añade reporting Jira opcional por hitos sobre tracking híbrido, conservando Markdown como autoridad. |
| Existente 1.4 | Compatible sin escritura automática | Continúa operable; migración explícita `1.4 → 1.5` para adoptar reporting, con scope conservador y sin mappings inferidos. |
| Existente 1.3 | Compatible sin escritura automática | Continúa operable; migración explícita `1.3 → 1.4` para adoptar el artefacto de tracking. |
| Existente 1.2 | Compatible sin escritura automática | Su cobertura se deriva conservadoramente; migración explícita `1.2 → 1.3` para nuevas ejecuciones durables. |
| Existente 1.1 | Compatible sin escritura automática | Migración explícita `1.1 → 1.2`; después, en otra operación, `1.2 → 1.3`. |
| Existente 1.0 | Compatible con reglas legacy y avisos | Ruta explícita `1.0 → 1.1 → 1.2 → 1.3 → 1.4 → 1.5`, una operación por salto. |
| Existente 0.9 | Sin salto directo | Ruta histórica `0.9 → 1.0`, un salto autorizado cada vez. |

La actualización del plugin no migra proyectos consumidores. Cada aplicación de migración exige preview, hash coincidente, backup externo, autorización expresa y validación posterior. `1.0 → 1.1` mantiene el bloqueo por `human_review_required`; `1.1 → 1.2` materializa gobierno; `1.2 → 1.3` añade cobertura y continuidad; `1.3 → 1.4` añade tracking; `1.4 → 1.5` añade reporting. Este último conserva `repository-only` como no aplicable y Jira como `projection-only`, no infiere mappings ni escrituras y rechaza ejecuciones o recibos no resueltos. Los checkpoints históricos conservan sus bytes y schema original.

La migración conserva el `Workflow state` histórico de cada tarea. Si una tarea 1.2 figuraba `ready` pero no contiene los nuevos campos ejecutables, el tablero seguirá mostrando ese hecho y `Definition status` quedará `incomplete`; el readiness derivado de la porción será `blocked` hasta completar y confirmar la definición. No se degrada el pasado ni se presenta el estado legado como autorización vigente.

## Compatibilidad tecnológica

La compatibilidad se declara por composición exacta, no por semejanza de nombres:

- **family**: clasificación arquitectónica no seleccionable;
- **capability**: unidad interna reutilizable de reglas y gates;
- **reference profile**: composición cerrada y única unidad certificable;
- **binding**: selección confirmada del perfil para una unidad desplegable;
- **lock**: identidad exacta de perfil, capabilities, driver y gates;
- **certification**: evidencia completa y vigente del gate de composición.

`active` expresa intención de producto; `supported` exige además una certificación exacta válida. `candidate` significa que el perfil puede documentarse y evaluarse, pero el plugin no garantiza todavía su recorrido reproducible `readiness → prepare → implement → verify`. Un proyecto con React/Vite estático no debe forzarse al perfil completo con API, identidad y base de datos; debe seleccionar el perfil coherente con su arquitectura y quedar bloqueado si esa composición no está certificada.

Los esquemas 1.2, 1.3, 1.4 y 1.5 admiten varias unidades desplegables y un binding independiente por unidad. La combinación dinámica de capabilities dentro de un proyecto no crea automáticamente un perfil nuevo: la composición debe existir y estar certificada en la release del plugin. El tracking Jira no modifica ni recertifica perfiles tecnológicos.

## CLI portable

`<plugin-root>` es la carpeta que contiene `.codex-plugin/plugin.json`; `<project-root>` es la raíz del proyecto consumidor. No deben confundirse.

```powershell
python "<plugin-root>/scripts/lks_sdd.py" profiles --all
python "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>" --json
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation --json
python "<plugin-root>/scripts/lks_sdd.py" assess-readiness "<project-root>" --increment INC-001 --json
python "<plugin-root>/scripts/lks_sdd.py" planning "<project-root>" --increment INC-001 assess
python "<plugin-root>/scripts/lks_sdd.py" tasks "<project-root>" board
python "<plugin-root>/scripts/lks_sdd.py" tracking status "<project-root>" --json
python "<plugin-root>/scripts/lks_sdd.py" tracking preview-sync "<project-root>" --task TASK-001 --json
python "<plugin-root>/scripts/lks_sdd.py" continuity "<project-root>" resume
python "<plugin-root>/scripts/lks_sdd.py" migrate "<project-root>" --target-schema 1.5 --dry-run
```

Use la ayuda de la versión instalada para los argumentos exactos. Una evaluación, preview o plan no autoriza escribir, mergear, desplegar ni promover artefactos.

## ImageGen y otras capacidades condicionales

ImageGen puede utilizarse cuando Codex lo expone, existe frontend o cambio visual aplicable y el brief es suficiente. No forma parte del manifiesto, no se presume disponible y no sustituye requisitos, responsive, accesibilidad o validación humana. La disponibilidad de ImageGen en otra superficie tampoco demuestra compatibilidad del plugin completo.

## Jira y Atlassian Rovo

| Capacidad | Estado 0.11.0 candidate |
|---|---|
| `repository-only` | Soportada sin dependencia externa |
| Modelo local de `jira-hybrid`, previews y acuses | Implementado y validable con datos sintéticos |
| Autorización durable por tarea | `authorize-sync` guarda `SYNC-###` antes de la escritura; `record-result` lo cierra por ID |
| Reconciliación | `reconcile-result --anchor-sync-id` registra una lectura Rovo autorizada para `uncertain`, `conflict` o una key modificada dentro del prefijo confirmado aunque el plan derive; no autoriza escrituras |
| Rovo como peer | Opcional; instalación, conexión, permisos y autenticación separados |
| Creación/actualización real en Jira | Requiere herramienta Rovo disponible y autorización explícita; interoperabilidad real `not-run` |
| Comentarios de hitos | Soportados con marker, preview determinista, una confirmación y recibo separado |
| Transiciones | Opcionales; solo con status mapping confirmado y transition ID observado, con recibo separado |
| Pausa y reconciliación | Reporting pausable; resultados inciertos se resuelven con recibos append-only |
| Adjuntos | No soportados |
| Jira-only o autoridad remota sobre AUTH/evidencia | No soportado |

El manifiesto no declara una dependencia dura porque no se ha validado una sintaxis oficial de dependencia entre plugins para esta release. Ausencia, permisos insuficientes o error de Rovo producen un estado degradado visible; nunca un éxito simulado. Un plan local no confirmado deja el eje de tracking `not-assessed`; Jira no puede suplir esa confirmación. Cada preview abarca una única TASK. Para `create`, la búsqueda Rovo del marcador debe acreditar `no-match`; para `update`, la identidad y el marcador deben acreditar `matched`. `authorize-sync` persiste el recibo antes del write; un éxito de `record-result` exige observar el marcador exacto y la huella proyectada, y ningún recibo cambia el estado canónico de la TASK.

La candidate 0.11.0 no ofrece `detach` ni `rebind`: cuando existen mappings o recibos durables, no permite abandonar Jira ni cambiar site, proyecto o tipo. Reconciliar `uncertain`, `conflict` o una key modificada dentro del prefijo confirmado no elimina esa restricción. Un cambio de prefijo por rename o movimiento queda fuera de soporte y mantiene conflicto o reconciliación pendiente. Las proyecciones `confidential`/`restricted`, con secretos o datos personales detectables se bloquean; site y URL deben ser HTTPS sin credenciales, query ni fragmento. Véase `docs/JIRA-ROVO-INTEGRATION.md`.

## Regla para futuras integraciones

Añadir otro runtime, arquitectura o combinación tecnológica exige contrato propio, permisos, locks, scaffold, gates, evals y evidencia representativa. No se declarará soporte por inferencia, popularidad de la tecnología o éxito aislado de Codex escribiendo código.
