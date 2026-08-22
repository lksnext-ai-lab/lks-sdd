# Capacidades y límites de LKS-SDD 0.9.0

Estas capacidades describen el plugin LKS-SDD ejecutado con Codex. No constituyen una promesa de comportamiento equivalente en GitHub Copilot, Claude u otros asistentes.

## Disponibles

- Explicar el método, ofrecer onboarding y orientar desde el estado de un proyecto sin modificarlo.
- Inicializar de forma aditiva la documentación de una aplicación nueva autorizada.
- Encuadrar ideas ambiguas sin presuponer el dominio y mantener especificaciones profesionales separando propuestas de decisiones.
- Mostrar snapshots compactos de cobertura al completar bloques relevantes, sin sustituir readiness ni usar porcentajes engañosos.
- Definir pantallas, flujos, estados e interacción cuando existe frontend.
- Generar con ImageGen entre una y tres propuestas para un frontend nuevo o cambio visual material cuando el brief sea suficiente y la capacidad esté disponible; conservar validación, estado y activos trazables. Si no está disponible, declarar el fallback y el pendiente.
- Adoptar aplicaciones existentes mediante inspección estática, reconciliación y materialización documental autorizada.
- Inicializar proyectos nuevos con método 1.3.0 y esquema 1.3, y validar proyectos 1.0/1.1/1.2 en compatibilidad sin reescribirlos.
- Definir y evolucionar `bounded-release`, `continuous-evolution` o `maintenance-stream`, incluyendo SemVer u otra política confirmada, Git/ramas, entornos, CI/CD, promoción inmutable, despliegue, recuperación y revisiones `CHG-###`.
- Gestionar planes, releases y tareas mediante `PLAN/REL/TASK`, un mapa de cobertura primaria/contribuyente, fichas ejecutables, estados, salud, progreso, dependencias, bloqueos, evidencias e historial.
- Distinguir cierre de especificación, soporte de automatización, completitud del plan, readiness de la porción, autorización, implementación, verificación y entrega en el mismo resumen.
- Detectar alcance, aceptación y pruebas sin tarea, definiciones incompletas, solapamientos primarios, releases incoherentes, ciclos y dependencias canceladas.
- Persistir `AUTH-###`, `EXEC-###` y `CKPT-###` para iniciar, pausar y reanudar una ejecución sin depender de la conversación.
- Resolver arquitecturas multiunidad y multiperfil mediante `UNIT-###` y `BIND-###`, sin convertir familias o capabilities en composiciones homologadas.
- Validar tablas, estados, propietarios de IDs, listas, rangos inclusivos `..`, relaciones y una matriz separada de datos, identidad, seguridad, privacidad e integraciones mediante un contrato declarativo común.
- Evaluar readiness de un incremento con bloqueos explicables, separando `specification_readiness`, `automation_support`, `planning_completeness` y `selected_slice_readiness`.
- Comprobar trazabilidad en fase `preimplementation` hasta pruebas planificadas y en fase `verification` hasta evidencia ejecutada; un alcance vacío falla de forma explícita. El preflight resuelve además las relaciones del contrato activo y queda incompleto ante destinos inexistentes, históricos o no confirmados, con diagnósticos `LKS-ACTIVE-*`; sigue siendo un handoff estructural y no una evaluación completa de readiness.
- Distinguir la huella documental completa de la huella del contrato activo, conservando historial sin convertir elementos rechazados, sustituidos o retirados en inputs de implementación.
- Preparar de forma genérica y collision-safe cada perfil exacto activo de una selección TASK, copiando locks por binding mediante preview y autorización.
- Verificar gates componibles G2/G3 y evidencia G4 contra commit/árbol/build/digests/entorno exactos, sin desplegar ni autorizar una entrega.
- Validar especificación y trazabilidad, preparar migraciones explícitas 0.9 → 1.0, 1.0 → 1.1, 1.1 → 1.2 o 1.2 → 1.3 de un solo salto y generar borradores cliente controlados.
- Ejecutar el harness candidate M4, comparar releases y conservar como `not-run` la evidencia aún no aportada.
- Generar un bundle candidate de marketplace y preparar un piloto saneado que permanece bloqueado hasta completar su configuración externa.

## No disponibles todavía

- Seleccionar una pila automáticamente o tratar un perfil activo como homologación corporativa.
- Implementar mezclas arbitrarias, familias, capabilities aisladas o perfiles candidatos que no tengan certificación exacta de composición.
- Migrar automáticamente al actualizar el plugin, encadenar saltos o convertir propuestas de gobierno, ramas, entornos o arquitectura en decisiones.
- Declarar completa una release a partir de una tarea lista, autorizar por inferencia, inventar tareas, estimaciones, fechas, avance o evidencia.
- Crear commits, pushes, merges o despliegues como efecto de un checkpoint.
- Normalizar o modernizar código existente durante la adopción.
- Instalar automáticamente el bundle, desplegar, acceder a producción o aprobar excepciones.
- Presentar la infraestructura M5 como un piloto ya ejecutado o una decisión `go` sin resultados reales.
- Presentar canales opcionales candidate `not-run` o pruebas `skipped` como superados, o promover a stable sin los ocho canales requeridos.
- Presentar una imagen generada como diseño confirmado, código, prueba de accesibilidad o evidencia semántica/humana ejecutada.
- Usar MCP, conectores, hooks, apps o agentes.
- Ejecutar el plugin con soporte garantizado fuera de Codex.

La baseline normativa es candidata. Puede orientar un piloto, pero no debe presentarse como política corporativa, certificación ni aprobación formal.
