# Capacidades y límites de LKS-SDD 2.0.1

Para contrato 2.0 use [la política común v2](../../../docs/V2-WORKFLOWS.md).
La versión 2 implementa el nuevo ciclo; la publicación técnica no acredita aceptación
real de host. Los detalles siguientes conservan capacidades de contrato 1.5;
no deben mezclarse sus comandos ni sus tablas con las operaciones v2.

La evidencia visual nueva aplica una política predeterminada de una a cinco imágenes por TASK con interfaz. Cada captura debe enlazar aceptación e interacción, conservar contexto reproducible y declarar un resultado; el archivo por sí solo nunca acredita `passed`. `work verify` genera fichas TASK derivadas sin convertirlas en autoridad ni alterar el sujeto técnico. Una EVID conserva el hecho histórico y los hallazgos posteriores cambian la salud actual hasta una corrección y re-verificación gobernadas.

La evidencia funcional usa scopes tipados compartidos: `component`, `contract`, `composition`, `user-flow`, `persistence` y `visual`. Solo una interfaz `INT-###` confirmada con flujo web activa el gate de navegador para su TASK propietaria; HTTP, PostgreSQL y migración usan observadores propios. Arrancar unidades o aprobar sus tests por separado no acredita comunicación; una captura no acredita persistencia; un mock de una operación funcional, sea cual sea su ruta, no acredita integración. La identidad controlada puede usar el doble autorizado por el perfil no productivo.

Las seis capacidades comparten núcleo entre Codex desktop y el adaptador GitHub Copilot
para VS Code Agent. Copilot deriva la generación de prototipos a Codex sin API adicional;
Codex nativo no muestra avisos de relevo. La aceptación conversacional real por host
permanece separada de las pruebas automatizadas. Otros asistentes y la extensión Codex
de VS Code están fuera de alcance. Consultar `<plugin-root>/docs/INSTALLATION.md` y
`<plugin-root>/docs/DUAL-HOST-ACCEPTANCE.md` para instalación, evidencia y límites.

## Disponibles

- Explicar el método, ofrecer onboarding y orientar desde el estado de un proyecto sin modificarlo.
- Mantener una especificación Spec-anchored como contrato versionado que evoluciona con el código y hace visible la deriva que debe reconciliarse.
- Inicializar de forma aditiva la documentación de una aplicación nueva autorizada.
- Encuadrar ideas ambiguas sin presuponer el dominio y mantener especificaciones profesionales separando propuestas de decisiones.
- Mostrar snapshots compactos de cobertura al completar bloques relevantes, sin sustituir readiness ni usar porcentajes engañosos.
- Definir pantallas, flujos, estados e interacción cuando existe frontend.
- Generar con ImageGen entre una y tres propuestas para un frontend nuevo o cambio visual material cuando el brief sea suficiente y la capacidad esté disponible; conservar validación, estado y activos trazables. Si no está disponible, declarar el fallback y el pendiente.
- Adoptar aplicaciones existentes mediante inspección estática, reconciliación y materialización autorizada de una baseline documental, sin tratar el código observado como intención aprobada.
- Inicializar y validar proyectos con método 1.5.0 y esquema 1.5; rechazar otros contratos sin reescribirlos y conservar `plugin_version` como procedencia de materialización.
- Definir y evolucionar `bounded-release`, `continuous-evolution` o `maintenance-stream`, incluyendo SemVer u otra política confirmada, Git/ramas, entornos, CI/CD, promoción inmutable, despliegue, recuperación y revisiones `CHG-###`.
- Gestionar planes, releases y tareas mediante `PLAN/REL/TASK`, un mapa de cobertura primaria/contribuyente, fichas ejecutables, estados, salud, progreso, dependencias, bloqueos, evidencias e historial.
- Exigir antes de confirmar el plan una decisión explícita entre tracking `repository-only` y `jira-hybrid`; la opción local conserva una experiencia completa y no solicita Atlassian.
- En modo `jira-hybrid`, conservar los Markdown como contrato autoritativo y proyectar tareas hacia Jira mediante un peer Atlassian Rovo instalado y autenticado por separado, con preflight de lectura, preview determinista, autorización explícita y recibos `SYNC-###`.
- Elegir por separado `projection-only` o `milestone-reporting`, con gate `advisory` o `required-before-execution`; publicar solo hitos significativos mediante comentarios saneados y transiciones basadas en IDs confirmados.
- Autorizar un hito con una sola confirmación humana y conservar recibos separados para comentario y transición, con pausa/reanudación, idempotencia y reconciliación append-only.
- Bloquear reintentos ambiguos y separar el estado remoto del estado canónico: un issue en `Done` no cierra por sí solo una `TASK-###` local.
- Distinguir cierre de especificación, soporte de automatización, completitud del plan, readiness de la porción, autorización, implementación, verificación y entrega en el mismo resumen.
- Detectar alcance, aceptación y pruebas sin tarea, definiciones incompletas, solapamientos primarios, releases incoherentes, ciclos y dependencias canceladas.
- Persistir `AUTH-###`, `EXEC-###` y `CKPT-###` para iniciar, pausar y reanudar una ejecución sin depender de la conversación.
- Resolver arquitecturas multiunidad y multiperfil mediante `UNIT-###` y `BIND-###`, sin convertir familias o capabilities en composiciones homologadas.
- Validar tablas, estados, propietarios de IDs, listas, rangos inclusivos `..`, relaciones y una matriz separada de datos, identidad, seguridad, privacidad e integraciones mediante un contrato declarativo común.
- Evaluar readiness de un incremento con bloqueos explicables, separando `specification_readiness`, `automation_support`, `planning_completeness` y `selected_slice_readiness`.
- Explicar `automation_coverage` por binding sin rebajar `automation_support`: capabilities granulares permiten localizar preparación, gates locales, interoperabilidad y evidencia pendientes, pero solo un perfil exacto active y certificado es implementable.
- Documentar como candidates los perfiles exactos `API-FASTAPI-ENTRA-PG-OCI` y `WEB-REACT-VITE-ENTRA-STATIC`, manteniendo frontend/backend separados y sin sustituir Microsoft Entra por Keycloak.
- Implementar en desarrollo, CI, integración y aceptación-preproducción mediante los perfiles exactos `API-FASTAPI-SIMULATED-OIDC-PG-OCI` y `WEB-REACT-VITE-SIMULATED-OIDC-STATIC`, con bindings separados, certificación exacta, interoperabilidad externa `not-applicable` y bloqueo fail-closed en producción. No acreditan ni sustituyen Microsoft Entra.
- Comprobar trazabilidad en fase `preimplementation` hasta pruebas planificadas y en fase `verification` hasta evidencia ejecutada; un alcance vacío falla de forma explícita. El preflight resuelve además las relaciones del contrato activo y queda incompleto ante destinos inexistentes, históricos o no confirmados, con diagnósticos `LKS-ACTIVE-*`; sigue siendo un handoff estructural y no una evaluación completa de readiness.
- Distinguir la huella documental completa de la huella del contrato activo, conservando historial sin convertir elementos rechazados, sustituidos o retirados en inputs de implementación.
- Preparar de forma genérica y collision-safe cada perfil exacto activo de una selección TASK, copiando locks por binding mediante preview y autorización.
- Verificar gates componibles G2/G3 y evidencia G4 contra commit/árbol/build/digests/entorno exactos, sin desplegar ni autorizar una entrega.
- Validar especificación y trazabilidad 1.5 y generar borradores cliente controlados desde información confirmada, con procedencia y aprobación pendiente.
- Ejecutar el harness candidate M4, comparar releases y conservar como `not-run` la evidencia aún no aportada.
- Generar un bundle candidate de marketplace y preparar un piloto saneado que permanece bloqueado hasta completar su configuración externa.

## No disponibles todavía

- Seleccionar una pila automáticamente o tratar un perfil activo como homologación corporativa.
- Implementar mezclas arbitrarias, familias, capabilities aisladas o perfiles candidatos que no tengan certificación exacta de composición.
- Migrar contratos de proyecto, modificar consumidores al actualizar el plugin o convertir propuestas de gobierno, ramas, entornos o arquitectura en decisiones.
- Declarar completa una release a partir de una tarea lista, autorizar por inferencia, inventar tareas, estimaciones, fechas, avance o evidencia.
- Crear commits, pushes, merges o despliegues como efecto de un checkpoint.
- Normalizar o modernizar código existente durante la adopción.
- Inferir desde el código existente que su comportamiento es correcto, deseado o aprobado por el cliente.
- Tratar la especificación como generador automático de todo el código o considerar conforme un resultado solo porque fue generado desde ella.
- Instalar automáticamente el bundle, desplegar, acceder a producción o aprobar excepciones.
- Presentar la infraestructura M5 como un piloto ya ejecutado o una decisión `go` sin resultados reales.
- Presentar canales opcionales `not-run` o pruebas `skipped` como superados, o promover a stable sin gates técnicos y aprobación durable del responsable del proyecto.
- Presentar una imagen generada como diseño confirmado, código, prueba de accesibilidad o evidencia semántica/humana ejecutada.
- Incorporar o ejecutar directamente MCP, conectores, hooks, apps o agentes dentro del bundle. La interoperabilidad opcional con el peer Rovo no lo convierte en una dependencia embebida ni autoriza acceso remoto.
- Ejecutar el plugin con soporte garantizado fuera de Codex.

La baseline normativa es candidata. Puede orientar un piloto, pero no debe presentarse como política corporativa, certificación ni aprobación formal.


La ampliación de autenticación local, variantes y preparación de adopción se detalla en `docs/releases/0.18.0/TECHNOLOGY-AND-ADOPTION.md`. Los cinco contratos añaden nueve variantes; el catálogo contiene 23 perfiles. Cada soporte vigente requiere evidencia exacta del motor actual.
