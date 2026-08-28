# Capacidades y límites de LKS-SDD 0.14.2

Estas capacidades describen el plugin LKS-SDD ejecutado con Codex. No constituyen una promesa de comportamiento equivalente en GitHub Copilot, Claude u otros asistentes.

## Disponibles

- Explicar el método, ofrecer onboarding y orientar desde el estado de un proyecto sin modificarlo.
- Mantener una especificación Spec-anchored como contrato versionado que evoluciona con el código y hace visible la deriva que debe reconciliarse.
- Inicializar de forma aditiva la documentación de una aplicación nueva autorizada.
- Encuadrar ideas ambiguas sin presuponer el dominio y mantener especificaciones profesionales separando propuestas de decisiones.
- Mostrar snapshots compactos de cobertura al completar bloques relevantes, sin sustituir readiness ni usar porcentajes engañosos.
- Definir pantallas, flujos, estados e interacción cuando existe frontend.
- Generar con ImageGen entre una y tres propuestas para un frontend nuevo o cambio visual material cuando el brief sea suficiente y la capacidad esté disponible; conservar validación, estado y activos trazables. Si no está disponible, declarar el fallback y el pendiente.
- Adoptar aplicaciones existentes mediante inspección estática, reconciliación y materialización autorizada de una baseline documental, sin tratar el código observado como intención aprobada.
- Inicializar proyectos nuevos con método 1.5.0 y esquema 1.5, y validar proyectos 1.0/1.1/1.2/1.3/1.4/1.5 en compatibilidad sin reescribirlos.
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
- Validar especificación y trazabilidad, preparar migraciones explícitas 0.9 → 1.0, 1.0 → 1.1, 1.1 → 1.2, 1.2 → 1.3, 1.3 → 1.4 o 1.4 → 1.5 de un solo salto y generar borradores cliente controlados desde información confirmada, con procedencia y aprobación pendiente.
- Ejecutar el harness candidate M4, comparar releases y conservar como `not-run` la evidencia aún no aportada.
- Generar un bundle candidate de marketplace y preparar un piloto saneado que permanece bloqueado hasta completar su configuración externa.

## No disponibles todavía

- Seleccionar una pila automáticamente o tratar un perfil activo como homologación corporativa.
- Implementar mezclas arbitrarias, familias, capabilities aisladas o perfiles candidatos que no tengan certificación exacta de composición.
- Migrar automáticamente al actualizar el plugin, encadenar saltos o convertir propuestas de gobierno, ramas, entornos o arquitectura en decisiones.
- Declarar completa una release a partir de una tarea lista, autorizar por inferencia, inventar tareas, estimaciones, fechas, avance o evidencia.
- Crear commits, pushes, merges o despliegues como efecto de un checkpoint.
- Normalizar o modernizar código existente durante la adopción.
- Inferir desde el código existente que su comportamiento es correcto, deseado o aprobado por el cliente.
- Tratar la especificación como generador automático de todo el código o considerar conforme un resultado solo porque fue generado desde ella.
- Instalar automáticamente el bundle, desplegar, acceder a producción o aprobar excepciones.
- Presentar la infraestructura M5 como un piloto ya ejecutado o una decisión `go` sin resultados reales.
- Presentar canales opcionales candidate `not-run` o pruebas `skipped` como superados, o promover a stable sin los ocho canales requeridos.
- Presentar una imagen generada como diseño confirmado, código, prueba de accesibilidad o evidencia semántica/humana ejecutada.
- Incorporar o ejecutar directamente MCP, conectores, hooks, apps o agentes dentro del bundle. La interoperabilidad opcional con el peer Rovo no lo convierte en una dependencia embebida ni autoriza acceso remoto.
- Ejecutar el plugin con soporte garantizado fuera de Codex.

La baseline normativa es candidata. Puede orientar un piloto, pero no debe presentarse como política corporativa, certificación ni aprobación formal.
