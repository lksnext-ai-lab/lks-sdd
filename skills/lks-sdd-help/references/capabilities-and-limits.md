# Capacidades y límites de LKS-SDD 0.7.0

Estas capacidades describen el plugin LKS-SDD ejecutado con Codex. No constituyen una promesa de comportamiento equivalente en GitHub Copilot, Claude u otros asistentes.

## Disponibles

- Explicar el método, ofrecer onboarding y orientar desde el estado de un proyecto sin modificarlo.
- Inicializar de forma aditiva la documentación de una aplicación nueva autorizada.
- Encuadrar ideas ambiguas sin presuponer el dominio y mantener especificaciones profesionales separando propuestas de decisiones.
- Mostrar snapshots compactos de cobertura al completar bloques relevantes, sin sustituir readiness ni usar porcentajes engañosos.
- Definir pantallas, flujos, estados e interacción cuando existe frontend.
- Generar con ImageGen entre una y tres propuestas para un frontend nuevo o cambio visual material cuando el brief sea suficiente y la capacidad esté disponible; conservar validación, estado y activos trazables. Si no está disponible, declarar el fallback y el pendiente.
- Adoptar aplicaciones existentes mediante inspección estática, reconciliación y materialización documental autorizada.
- Inicializar proyectos nuevos con método 1.1.0 y esquema 1.1, y validar proyectos 1.0 en modo de compatibilidad sin reescribirlos.
- Validar tablas, estados, propietarios de IDs, listas, rangos inclusivos `..`, relaciones y una matriz separada de datos, identidad, seguridad, privacidad e integraciones mediante un contrato declarativo común.
- Evaluar readiness de un incremento con bloqueos explicables, separando `specification_readiness` de `automation_support`.
- Comprobar trazabilidad en fase `preimplementation` hasta pruebas planificadas y en fase `verification` hasta evidencia ejecutada; un alcance vacío falla de forma explícita. El preflight resuelve además las relaciones del contrato activo y queda incompleto ante destinos inexistentes, históricos o no confirmados, con diagnósticos `LKS-ACTIVE-*`; sigue siendo un handoff estructural y no una evaluación completa de readiness.
- Distinguir la huella documental completa de la huella del contrato activo, conservando historial sin convertir elementos rechazados, sustituidos o retirados en inputs de implementación.
- Preparar el scaffold del perfil H0 para un incremento listo mediante preview y autorización.
- Planificar verificaciones locales del perfil H0 para una implementación `in-progress` o `completed` del mismo incremento, y ejecutarlas o registrar evidencia solo cuando ese registro está `completed` y mantiene coherencia de perfil; incluye la integración opcional con PostgreSQL y Keycloak.
- Validar especificación y trazabilidad, preparar migraciones explícitas 0.9 → 1.0 o 1.0 → 1.1 de un solo salto y generar borradores cliente controlados.
- Ejecutar el harness candidate M4, comparar releases y conservar como `not-run` la evidencia aún no aportada.
- Generar un bundle candidate de marketplace y preparar un piloto saneado que permanece bloqueado hasta completar su configuración externa.

## No disponibles todavía

- Seleccionar una pila automáticamente o tratar el perfil H0 candidato como homologación corporativa.
- Implementar o verificar automáticamente pilas distintas del perfil H0.
- Migrar automáticamente proyectos al actualizar el plugin, encadenar saltos de esquema o aplicar una migración con entradas en `human_review_required`; cada entrada listada se resuelve explícitamente en los Markdown de origen. La `Identity` agregada se traslada a tres dominios `pending` para resolverlos después en 1.1, sin inferir referencias ni readiness.
- Normalizar o modernizar código existente durante la adopción.
- Instalar automáticamente el bundle, desplegar, acceder a producción o aprobar excepciones.
- Presentar la infraestructura M5 como un piloto ya ejecutado o una decisión `go` sin resultados reales.
- Presentar canales opcionales candidate `not-run` o pruebas `skipped` como superados, o promover a stable sin los ocho canales requeridos.
- Presentar una imagen generada como diseño confirmado, código, prueba de accesibilidad o evidencia semántica/humana ejecutada.
- Usar MCP, conectores, hooks, apps o agentes.
- Ejecutar el plugin con soporte garantizado fuera de Codex.

La baseline normativa es candidata. Puede orientar un piloto, pero no debe presentarse como política corporativa, certificación ni aprobación formal.
