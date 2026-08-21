# Compatibilidad y entorno objetivo

## Decisión de producto

LKS-SDD 0.8.0 es un plugin SDD para Codex. Codex es el entorno objetivo y el único soportado contractualmente. El manifiesto, el descubrimiento de skills, los prompts, los permisos y los workflows se diseñan y evalúan en ese contexto.

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
| Nuevo con LKS-SDD 0.8.0 | Método `1.2.0`, esquema `1.2` | Formato activo con gobierno, unidades, bindings, planes y tareas. |
| Existente 1.1 | Compatible sin escritura automática | Migración explícita `1.1 → 1.2`; crea pendientes, nunca inventa decisiones. |
| Existente 1.0 | Compatible con reglas legacy y avisos | Primero `1.0 → 1.1`; después, en otra operación, `1.1 → 1.2`. |
| Existente 0.9 | Sin salto directo | Ruta histórica `0.9 → 1.0`, un salto autorizado cada vez. |

La actualización del plugin no migra proyectos consumidores. Cada aplicación de migración exige preview, hash coincidente, backup externo, autorización expresa y validación posterior. `1.0 → 1.1` mantiene el bloqueo por `human_review_required`; `1.1 → 1.2` materializa gobierno, arquitectura, planes, tareas y bindings como pendientes cuando no existe una decisión confirmada.

## Compatibilidad tecnológica

La compatibilidad se declara por composición exacta, no por semejanza de nombres:

- **family**: clasificación arquitectónica no seleccionable;
- **capability**: unidad interna reutilizable de reglas y gates;
- **reference profile**: composición cerrada y única unidad certificable;
- **binding**: selección confirmada del perfil para una unidad desplegable;
- **lock**: identidad exacta de perfil, capabilities, driver y gates;
- **certification**: evidencia completa y vigente del gate de composición.

`active` expresa intención de producto; `supported` exige además una certificación exacta válida. `candidate` significa que el perfil puede documentarse y evaluarse, pero el plugin no garantiza todavía su recorrido reproducible `readiness → prepare → implement → verify`. Un proyecto con React/Vite estático no debe forzarse al perfil completo con API, identidad y base de datos; debe seleccionar el perfil coherente con su arquitectura y quedar bloqueado si esa composición no está certificada.

El esquema 1.2 admite varias unidades desplegables y un binding independiente por unidad. La combinación dinámica de capabilities dentro de un proyecto no crea automáticamente un perfil nuevo: la composición debe existir y estar certificada en la release del plugin.

## CLI portable

`<plugin-root>` es la carpeta que contiene `.codex-plugin/plugin.json`; `<project-root>` es la raíz del proyecto consumidor. No deben confundirse.

```powershell
python "<plugin-root>/scripts/lks_sdd.py" profiles --all
python "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>" --json
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation --json
python "<plugin-root>/scripts/lks_sdd.py" assess-readiness "<project-root>" --increment INC-001 --json
python "<plugin-root>/scripts/lks_sdd.py" tasks "<project-root>" board
python "<plugin-root>/scripts/lks_sdd.py" migrate "<project-root>" --target-schema 1.2 --dry-run
```

Use la ayuda de la versión instalada para los argumentos exactos. Una evaluación, preview o plan no autoriza escribir, mergear, desplegar ni promover artefactos.

## ImageGen y otras capacidades condicionales

ImageGen puede utilizarse cuando Codex lo expone, existe frontend o cambio visual aplicable y el brief es suficiente. No forma parte del manifiesto, no se presume disponible y no sustituye requisitos, responsive, accesibilidad o validación humana. La disponibilidad de ImageGen en otra superficie tampoco demuestra compatibilidad del plugin completo.

## Regla para futuras integraciones

Añadir otro runtime, arquitectura o combinación tecnológica exige contrato propio, permisos, locks, scaffold, gates, evals y evidencia representativa. No se declarará soporte por inferencia, popularidad de la tecnología o éxito aislado de Codex escribiendo código.
