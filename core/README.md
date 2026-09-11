# LKS-SDD para Codex y GitHub Copilot

LKS-SDD ayuda a desarrollar aplicaciones web con agentes de IA sin perder de vista
lo que las personas han acordado. Primero se aclara el problema, después se documenta
y planifica, se autoriza el trabajo y finalmente se comprueba el resultado.

Este enfoque se llama **Specification-Driven Development (SDD)**, o desarrollo guiado
por especificaciones. LKS-SDD es **Spec-anchored**: mantiene esos acuerdos vigentes
durante el desarrollo, no solo al principio. Sus plugins para Codex desktop y Copilot
en VS Code comparten método, plantillas, validadores y ayuda. Cada aplicación conserva
en su repositorio su propia documentación, código, evidencias y estado.

## Entorno objetivo y compatibilidad

¿Es tu primer contacto con agentes de IA o con SDD? Empieza por la
[guía desde cero](docs/LEARNING-GUIDE.md): explica las herramientas, las decisiones
humanas y un caso completo de reservas de salas. Después sigue
[instalación](docs/INSTALLATION.md) y el [piloto guiado de Copilot](docs/COPILOT-PILOT.md).
No necesitas comprender las siglas de las secciones técnicas para empezar.

La versión `1.1.0` incorpora distribución dual: Codex desktop y GitHub Copilot
en VS Code Agent. Las seis skills comparten un núcleo y contrato consumidor 1.5.
Copilot dispone de un plugin de agente instalable y un runtime fijado por proyecto;
los adaptadores de proyecto se conservan como alternativa sin plugin. Los compañeros
pueden compartir el mismo repositorio con relevo secuencial. La extensión Codex de
VS Code y la escritura simultánea distribuida están fuera de esta entrega.

Para instalar, siga la [guía de instalación desde el panel o ZIP](docs/INSTALLATION.md).
En Codex el prototipado sigue normalmente, sin mensajes de relevo. En Copilot, cuando
hacen falta imágenes nuevas, se prepara una ficha y se invita a continuar esa parte
en Codex; regresar es opcional y no se integra una API de imágenes de pago.
Véanse [relevo visual](docs/VISUAL-HANDOFF.md), [compatibilidad](docs/COMPATIBILITY.md)
y [evidencia y pendientes de aceptación](docs/DUAL-HOST-ACCEPTANCE.md). La promoción
estable tiene aprobación propia tras las pruebas satisfactorias de Copilot comunicadas
por el responsable; no acredita automáticamente todos los recorridos conversacionales.
Claude y otros asistentes quedan fuera del alcance de esta distribución.

La versión `1.0.0` abre la primera línea estable y conserva las seis skills y el contrato de proyectos `method_version: 1.5.0` / `schema_version: 1.5`. Mantiene interfaces `INT-###` tipadas, scopes de evidencia `component`, `contract`, `composition`, `user-flow`, `persistence` y `visual`, EVID 1.3 y el gate `GATE-BROWSER-FULLSTACK-E2E`. Un binding aislado o una captura no pueden acreditar una integración. La aplicabilidad sigue siendo TASK-aware: sin interfaz confirmada, backend y frontend independientes declaran `not-applicable`; la evidencia histórica insuficiente permanece inmutable y se informa como `reconciliation-required`.

Frontend y backend continúan como unidades/bindings independientes; su certificación por separado nunca afirma una composición conjunta. El perfil de sistema `WEB-FASTAPI-REACT-KEYCLOAK-PG` 2.1 está `active`, con soporte H1 y certificación exacta de la composición real mediante `GATE-BROWSER-FULLSTACK-E2E`. Los perfiles Microsoft Entra continúan `candidate`, `unsupported` y con interoperabilidad real `not-run`; los perfiles simulados no los sustituyen. `automation_coverage` sigue siendo diagnóstico y `automation_support` estricto. Los Markdown siguen siendo la única autoridad semántica y el runtime 1.0 opera exclusivamente sobre schema 1.5/método 1.5.0. `plugin_version` conserva la procedencia de materialización. Para `stable`, los gates técnicos y la aprobación durable del responsable del proyecto son bloqueantes; las evaluaciones conversacionales, revisiones detalladas, el piloto y la interoperabilidad real con Atlassian Rovo/Jira conservan su estado real como evidencia opcional. El bundle continúa sin MCP, cliente Jira, conectores propios, hooks, apps ni agentes ejecutables.

1.0 consolida las variantes tecnológicas cerradas, autenticación local para desarrollo aislado/CI, diagnóstico de dependencias sin instalación, preparación de adopción sin sobrescritura y certificaciones enlazadas a observaciones incorporadas en 0.18. La especificación y los límites técnicos están en [Variantes y adopción](docs/releases/0.18.0/TECHNOLOGY-AND-ADOPTION.md); la [hoja del SAT](docs/releases/0.18.0/SAT-ADAPTATION.md) es una propuesta sin ejecución. El soporte vigente siempre exige certificación exacta, no basta la presencia de un perfil en el catálogo.

## Posicionamiento Spec-anchored

LKS-SDD no utiliza la especificación como un encargo inicial que se descarta al comenzar a programar. La mantiene como un contrato vivo, versionado y verificable durante todo el ciclo de vida. Cuando cambia el comportamiento acordado, deben revisarse la especificación aplicable, la planificación, el código y las evidencias afectadas; si divergen, la discrepancia se hace visible y se reconcilia antes de continuar con una autorización obsoleta.

Este enfoque ocupa deliberadamente un punto intermedio:

| Enfoque | Papel de la especificación | Relación con el código |
|---|---|---|
| Spec-first | Aclara el inicio del desarrollo | Puede quedar como antecedente y perder vigencia |
| **Spec-anchored — LKS-SDD** | Permanece como documentación confiable y contrato contrastable | Especificación y código evolucionan con trazabilidad, gates y evidencia |
| Spec-as-source | Describe de forma ejecutable el sistema | El código se genera principalmente desde la especificación |

LKS-SDD no es Spec-as-source: permite trabajar directamente sobre el código y no presupone que toda la solución pueda generarse mecánicamente. Sí permite generar o modificar código desde una especificación confirmada, pero el resultado solo se considera conforme después de revisarlo y verificarlo.

La misma ancla sirve en dos sentidos:

- En una aplicación nueva, la intención acordada se convierte en especificación antes de autorizar la implementación.
- En un repositorio existente sin especificaciones, la adopción reconstruye una baseline documental a partir de hechos observables del código y los reconcilia con la intención confirmada. El código aporta evidencia del `as-is`; no decide por sí solo qué comportamiento es correcto o deseado.

Para una empresa de servicios, esta continuidad permite desarrollar con agilidad sin perder un artefacto comprensible que pueda contrastarse con el cliente. Los borradores para cliente se derivan únicamente de información confirmada y clasificada para ese uso, conservan procedencia y requieren revisión humana; no sustituyen el contrato canónico del repositorio.

## Principios operativos

- Los Markdown versionados de cada aplicación son la fuente de verdad; `.lks-sdd/project.json` es solo el índice operativo.
- La especificación permanece vigente después de implementar: un cambio funcional revisa el contrato y la deriva entre documentación, código o evidencia exige reconciliación explícita.
- LKS-SDD propone, pregunta y explica. La persona usuaria decide y confirma.
- Una idea breve no se interpreta como un producto genérico: primero se aclaran dominio, usuarios, propósito y contexto mediante preguntas de alto impacto.
- Hechos, inferencias, propuestas, decisiones y pendientes se conservan como tipos distintos.
- Los bloques de definición se resumen como suficientes, parciales, desconocidos, no aplicables o bloqueados, sin porcentajes de madurez engañosos.
- Ninguna tecnología se selecciona automáticamente. Familias y capabilities son reutilizables, pero solo un perfil de referencia cerrado, certificado y ligado a una unidad desplegable puede declararse soportado.
- La cobertura granular no equivale a soporte parcial: un perfil candidate puede tener scaffold y gates definidos, pero no habilita implementación hasta su certificación exacta.
- Antes de G2 se confirma el modelo de entrega (`bounded-release`, `continuous-evolution` o `maintenance-stream`), versionado, Git/ramas, entornos, CI/CD, promoción, despliegue y recuperación. Los cambios posteriores se registran, no reescriben el historial.
- El trabajo se planifica como `PLAN-###` → `REL-###` → `TASK-###`; `ART-PLANNING` demuestra qué alcance, aceptación y pruebas pertenecen a cada tarea. Una tarea `ready` no implica que toda la release esté planificada.
- Antes de materializar tareas 1.5 se confirma el backend de seguimiento. `repository-only` no necesita servicios externos; `jira-hybrid` proyecta una vista operacional saneada y puede informar hitos, pero no traslada a Jira la autoridad sobre alcance, AUTH, evidencia o `done`.
- Toda operación externa procesa una sola `TASK-###`: genera una intención determinista, busca el marcador mediante Rovo, persiste un `SYNC-###` autorizado para el hash exacto antes de escribir, ejecuta la operación separada, relee Jira y cierra ese recibo con el resultado y la huella observada. Un resultado remoto incierto nunca permite reintento ciego ni duplicar un issue.
- El reporting Jira es opcional, puede pausarse y no genera ruido por archivo o comando. Usa eventos de inicio, progreso significativo, bloqueo, reanudación, revisión y verificación; comentarios y transiciones tienen recibos independientes y reconciliación append-only.
- Al cerrar una especificación, LKS-SDD muestra una transición orientada a acción: completado, estado separado de cada fase, huecos de planificación, siguiente paso y decisión humana necesaria. El camino recomendado es confirmar la planificación integral antes de implementar.
- La planificación `partial` solo habilita una porción mediante una política incremental confirmada y una autorización humana ligada a huellas vigentes. Una propuesta de tareas nunca se convierte por sí sola en decisión.
- `AUTH-###`, `EXEC-###` y `CKPT-###` conservan en el repositorio la autorización, la ejecución y el estado observable para pausar o reanudar sin depender del chat. Código escrito y código verificado siguen siendo hechos distintos.
- ImageGen se usa solo con un brief visual suficiente y capacidad disponible; una imagen propuesta no equivale a diseño confirmado ni sustituye requisitos o accesibilidad.
- La baseline normativa incluida es candidata. Sus `MUST`, `SHOULD` y `MAY` no equivalen a política corporativa aprobada.
- Una consulta de ayuda no modifica archivos. Una evaluación de readiness no autoriza implementación.
- La preparación de la especificación (`specification_readiness`) y el soporte de automatización (`automation_support`) se informan por separado. Una pila puede estar suficientemente especificada y no disponer de automatización implementable en este plugin.
- La trazabilidad previa a implementar exige requisito, aceptación, decisión o no aplicabilidad motivada, incremento y prueba. También resuelve el contrato activo del incremento: una relación activa a un elemento inexistente, no confirmado o histórico deja el preflight incompleto con diagnósticos `LKS-ACTIVE-*`. Esta puerta comprueba el handoff estructural, no sustituye la evaluación completa de readiness. La fase de verificación exige además evidencia ejecutada; una comprobación de alcance vacío nunca se presenta como válida. El plan puede anticiparse para una implementación `in-progress` del mismo incremento, pero ejecutar checks o registrar evidencia requiere `implementation.status: completed` y coherencia con el perfil seleccionado.
- No se genera código cuando faltan decisiones críticas para el incremento afectado.

## Estructura

- `.codex-plugin/plugin.json`: manifiesto del plugin.
- `skills/`: seis workflows de producto descubribles: ayuda, definición, adopción, readiness, implementación y verificación.
- `profiles/`: catálogo de familias/capabilities, perfiles cerrados, drivers, scaffolds, locks y certificaciones exactas.
- `schemas/`: contrato de proyecto/front matter 1.5, fragmentos documentales internos, contratos versionados de evidencia y calidad, tracking/reporting, perfiles, drivers, locks y certificaciones.
- `scripts/`: validación, trazabilidad, gobierno de entrega, cobertura de planificación, autorización, tablero TASK, tracking operacional, continuidad, registro multiperfil, gates y vistas derivadas. No incluye migrador de proyectos.
- `templates/client/`: plantilla profesional para borradores derivados, nunca fuente canónica.
- `specs/canonical/`: tres fuentes originales preservadas por hash y cuatro extensiones aditivas: definición visual 0.6, contrato/handoff 1.1, gobierno/entrega/perfiles/tareas 1.2 y planificación/continuidad 1.3.
- `specs/proposed/`: extensiones candidate 1.4 de tracking, 1.5 de reporting Jira y 1.5 de catálogo granular/Entra, todavía no canónicas ni aprobadas como política corporativa.
- `tests/`: fixtures declarativos y evals deterministas de invariantes.
- `quality/`: catálogo M4, corpus de activación, fixtures bloqueados y baselines de comparación.
- `pilot/`: ejemplo bloqueado, plan y rollback para el piloto controlado M5.
- `distribution/`: plantilla estándar del marketplace de desarrollo generado externamente.
- `docs/ARCHITECTURE.md`: arquitectura de la versión 1.0.0 y límites vigentes.
- `docs/COMPATIBILITY.md`: entorno Codex soportado y límites de portabilidad.
- `docs/M1-COVERAGE.md`: correspondencia auditable entre M0–M1, implementación y pendientes.
- `docs/M2-COVERAGE.md`: fotografía histórica del primer perfil H0, implementación y verificación en 0.2.0.
- `docs/M3-COVERAGE.md`: correspondencia auditable entre adopción, migración y vistas cliente.
- `docs/M4-COVERAGE.md`: correspondencia auditable entre EP-10 y el harness integrado.
- `docs/M5-COVERAGE.md`: correspondencia auditable entre EP-12 y la infraestructura de piloto.
- `docs/V0.6-DEFINITION-UX-COVERAGE.md`: cobertura de la evolución compatible de entrevista, estado de definición y diseño visual.
- `docs/V0.7-CONTRACT-HANDOFF-COVERAGE.md`: cobertura del contrato documental 1.1, compatibilidad 1.0 y handoff por incremento.
- `docs/V0.8-DELIVERY-MULTIPROFILE-COVERAGE.md`: cobertura de gobierno, planificación TASK, perfiles exactos, gates y evidencia de entrega.
- `docs/V0.9-PLANNING-CONTINUITY-COVERAGE.md`: cobertura de planificación integral, autorización delimitada, checkpoints y reanudación.
- `docs/V0.10-JIRA-ROVO-COVERAGE.md`: cobertura del tracking híbrido, degradación, autoridad y límites de Rovo.
- `docs/V0.11-JIRA-MILESTONE-COVERAGE.md`: cobertura del reporting de hitos, UX opcional, receipts, idempotencia y degradación.
- `docs/V0.12-ENTRA-PROFILE-COVERAGE.md`: capabilities granulares, perfiles Entra candidate, diagnósticos y límites de certificación.
- `docs/V0.14-INCREMENTAL-VERIFICATION-COVERAGE.md`: aplicabilidad visual por TASK, build/G4, CKPT y PROB/Jira.
- `docs/V0.15-PRODUCT-EXPERIENCE.md`: vistas management/developer/audit, fast path, problemas, sujeto técnico, doctor, caché y benchmark.
- `docs/V0.16-VALIDATION-EVIDENCE.md`: diagnóstico, diseño, schemas, benchmark, compatibilidad y migración de evidencia por TASK.
- `docs/V0.17-FULLSTACK-INTEGRATION-EVIDENCE.md`: interfaz multiunidad, scopes tipados, aplicabilidad, E2E full-stack y reconciliación histórica.
- `docs/JIRA-ROVO-INTEGRATION.md`: contrato operativo de interacción entre las skills y el peer Rovo opcional.
- `docs/QUALITY-HARNESS.md`: ejecución, evidencia y semántica de las puertas candidate/stable.
- `docs/DISTRIBUTION.md`: empaquetado, instalación controlada y retirada.
- `docs/RELEASING.md`: política de versiones, etiquetas y releases técnicas de GitHub.

## Validación local

Los comandos reproducibles y sus códigos de salida están documentados en `docs/VALIDATION.md`. La validación contractual es local; el gate técnico completo descarga las imágenes y dependencias bloqueadas y requiere Docker.

Para operar sobre un proyecto consumidor, resuelva `<plugin-root>` como la carpeta instalada que contiene `.codex-plugin/plugin.json`; no busque `scripts/` dentro del proyecto consumidor. El dispatcher portable mantiene separados ambos roots:

```powershell
python "<plugin-root>/scripts/lks_sdd.py" validate-project "<project-root>"
python "<plugin-root>/scripts/lks_sdd.py" traceability "<project-root>" --increment INC-001 --phase preimplementation
python "<plugin-root>/scripts/lks_sdd.py" planning "<project-root>" --increment INC-001 assess
python "<plugin-root>/scripts/lks_sdd.py" tracking status "<project-root>" --json
python "<plugin-root>/scripts/lks_sdd.py" tracking preview-sync "<project-root>" --task TASK-001 --json
python "<plugin-root>/scripts/lks_sdd.py" tracking preview-event "<project-root>" --task TASK-001 --source-ref CKPT-001 --event-kind progress --json
python "<plugin-root>/scripts/lks_sdd.py" continuity "<project-root>" resume
python "<plugin-root>/scripts/lks_sdd.py" status "<project-root>" --task TASK-001
python "<plugin-root>/scripts/lks_sdd.py" work status "<project-root>" --task TASK-001
python "<plugin-root>/scripts/lks_sdd.py" work resolve "<project-root>" --task TASK-001 --problem PROB-001 --cause "..." --evidence EVID-002
python "<plugin-root>/scripts/lks_sdd.py" doctor "<project-root>" --quick
```

`status` usa por defecto una síntesis management en lenguaje de producto. `--view developer` añade diagnóstico accionable y `--view audit --json` conserva el contrato completo. `work` agrupa el ciclo normal de una tarea sin eliminar los comandos bajos ni sus controles.

Use `--phase verification` cuando deba exigir `EVID-###` ejecutada. `tracking preview-sync` exige una única `--task` y solo genera una intención local: no acredita que Rovo haya escrito en Jira. Si el plan local todavía no está confirmado, el tracking queda `not-assessed`, no se inventa una operación. `authorize-sync` exige que la búsqueda Rovo haya devuelto `no-match` para `create` o `matched` para `update`, y guarda el recibo autorizado antes de la escritura. `record-result` lo cierra por `--sync-id`; un éxito requiere observar tanto `LKS-SDD-PROJECT: <project_id>; TASK: TASK-###` como la `projection_fingerprint` exacta tras releer Jira. Para hitos, `preview-event` genera comentario y transición opcional; una confirmación del preview persiste recibos separados y cada operación se cierra con marker o status ID observado. El recibo remoto nunca cambia el estado canónico de la TASK. Solo se proyectan fichas con clasificación externa válida `internal`, `public` o `client`; una clasificación ausente, desconocida, `confidential` o `restricted`, los secretos, los datos personales detectables y las URLs con credenciales, query o fragmento se bloquean. Un binding con mappings o recibos durables no puede cambiarse ni abandonarse en 0.15.0, que no ofrece `detach`/`rebind`.

0.15 no distribuye migradores de proyectos: exige schema 1.5/método 1.5.0 y rechaza contratos anteriores sin escribir. Actualizar el runtime no modifica el `plugin_version` histórico del índice. Durante la adopción desde la única instalación 0.14.2 se conserva un puente de rollback del bundle; la meta para 1.0 es un contrato único sin schemas ni migradores pre-1.0. Los rollbacks transaccionales ante una mutación fallida permanecen porque garantizan atomicidad, no por compatibilidad legacy.

Este repositorio prepara releases técnicas candidate o stable y genera un marketplace reproducible, pero no instala globalmente el plugin ni decide por sí mismo su distribución corporativa. La promoción stable exige gates técnicos y aprobación durable del responsable del proyecto. Licencia, SLA, publicación, instalación y soporte operativo mantienen decisiones separadas. `LICENSE.md` registra las restricciones sin inventar una licencia y `CONTRIBUTING.md` define el contrato de cambio.
