# Changelog

## 0.7.0 — 2026-08-20 — contrato documental y handoff fiable

- Unifica el análisis de artefactos, tablas, estados y referencias para que validación, ayuda, trazabilidad y readiness consuman el mismo contrato documental normalizado.
- Endurece las referencias individuales, listas y rangos inclusivos `..`: evita expansiones parciales silenciosas y admite las formas legacy `a` o separadas por espacios solo en compatibilidad, con aviso.
- Separa relaciones activas de elementos históricos y calcula fingerprints distintos para integridad documental e inputs activos de implementación.
- Añade una matriz de aplicabilidad por dominio para datos, identidad, seguridad, privacidad e integraciones sin forzar un único estado agregado.
- Hace fallar de forma explícita la trazabilidad vacía o incompleta, incorpora un preflight de handoff y separa readiness funcional de soporte automatizado sin convertir limitaciones del perfil en defectos de la especificación.
- Añade diagnósticos estructurados, localizados y agrupados por causa raíz, manteniendo una vista textual compatible para los consumidores existentes.
- Añade la migración explícita 1.0 → 1.1 con dry-run y cierre seguro: cualquier entrada de `human_review_required` bloquea siempre la aplicación antes de crear backup o escribir hasta resolver el Markdown 1.0 de origen y repetir el preview. La dimensión agregada `Identity` se traslada sin inferencias a tres aplicabilidades `pending` con motivo; permite completar la migración si no existen otras revisiones, pero bloquea readiness hasta resolverse en 1.1.
- Incorpora fixtures y regresiones del recorrido real de la calculadora para cubrir el handoff `define → validate → help → traceability → readiness → prepare → verify-plan` que no representaban los happy paths anteriores.
- Cierra la puerta de verificación sobre el registro real de implementación: el plan anticipatorio solo admite el mismo incremento en `in-progress` o `completed`, y la ejecución o el registro de evidencia exigen `implementation.status=completed` y un perfil coherente antes de invocar checks o escribir archivos.
- Endurece la atestación y el empaquetado candidate: el harness captura antes de ejecutar checks la concordancia exacta entre `HEAD`, índice y bytes reales, y rechaza cualquier archivo no versionado preexistente, incluso ignorado; el builder revalida el esquema, hashes comprometidos, inventarios, evidencias, métricas y comparación del reporte antes de leer los bytes del commit e incluirlo en `SHA256SUMS`.
- Mantiene la release como candidate: los canales sin evidencia continúan `not-run`; el harness aún no importa resultados de `definition-conversation`, por lo que `stable` permanece bloqueado aunque se aporten observaciones de activación y revisión documental.

## 0.6.1 — 2026-08-20 — clasificación para desarrollo

- Reclasifica el plugin y su entrada de marketplace de `Productivity` a `Developer Tools`, de acuerdo con su finalidad de definición, implementación y verificación de software.
- Mantiene sin cambios el método, el esquema, las seis skills, los gates, los perfiles bloqueados y los contratos de proyectos consumidores.
- Conserva el estado de release candidate y no presenta como ejecutados los canales semánticos, humanos o de piloto pendientes.

## 0.6.0 — 2026-08-20 — definición guiada y diseño visual

- Refuerza el encuadre inicial para que una idea breve no se convierta silenciosamente en un producto genérico: mantiene tandas pequeñas de preguntas de alto impacto, opciones neutrales y supuestos explícitos.
- Añade snapshots compactos de cobertura al cerrar bloques relevantes, diferenciando información suficiente, parcial, desconocida, no aplicable y bloqueada sin porcentajes de madurez.
- Amplía el anexo condicional de UX con inventario, detalle y estados por pantalla, flujos enlazados, interacción, dirección visual y trazabilidad hacia requisitos y criterios.
- Define un ciclo de prototipado condicional con ImageGen: `Visual mode` explícito, brief suficiente, de una a tres propuestas PNG/JPG, validación humana estructurada, reutilización trazable, activos versionados, hashes y fallback explícito.
- Endurece gates contra rebajas de versión aisladas, PNG/JPEG ficticios, contratos de pantalla incompletos y evidencia visual no ligada a la implementación, UX, baseline, viewport y capturas exactos.
- Corrige FX-01 para que la entrevista adaptativa no se presente como evidencia automatizada y añade los escenarios FX-20 y FX-21 como evaluación semántica/humana todavía `not-run`.
- Mantiene Codex como único runtime soportado, ChatGPT Work como apoyo auxiliar y las seis skills existentes sin MCP, conectores, hooks, apps ni agentes añadidos.
- Actualiza el contrato, la documentación, el empaquetado y la infraestructura de piloto a la candidate 0.6.0 sin ejecutar M6, el piloto real ni la promoción a `stable`.

## 0.5.0 — 2026-08-20 — infraestructura de piloto M5

- Añade un marketplace de desarrollo empaquetado con la estructura local estándar de Codex.
- Genera bundles reproducibles del plugin y marketplace, manifiesto por archivo y `SHA256SUMS`, bloqueando enlaces y patrones de secretos.
- Añade configuración, observaciones cerradas, almacenamiento externo, agregación anónima y decisión go/no-go para un piloto de 3–5 proyectos y 5–8 participantes.
- Establece GitHub Issues como soporte no sensible y separa el canal confidencial de seguridad.
- Documenta onboarding, privacidad, retención, distribución y rollback sin modificar automáticamente proyectos consumidores.
- Mantiene el piloto real como pendiente: la plantilla preparada no permite arrancar hasta asignar muestra, aliases, responsables, seguridad y checksum.

## 0.4.0 — 2026-08-19 — calidad de producto M4

- Integra el catálogo completo FX-01–FX-19 y un corpus etiquetado de activación específico para Codex.
- Añade inventario cerrado y hashes SHA-256 para fixtures exclusivamente sintéticos.
- Añade un runner reproducible con canales `candidate` y `stable`, umbrales calculables y fallos críticos destacados.
- Compara métricas comunes con la baseline versionada `v0.3.0` sin ocultar datos no comparables.
- Incorpora contratos para observaciones saneadas y revisiones documentales humanas, manteniendo `not-run` cuando no existe evidencia.

## 0.3.0 — 2026-08-19 — release M0–M3

- Implementa la sexta skill, `lks-sdd-adopt-existing`, con inspección estática, informe externo, reconciliación, detección de deriva y materialización aditiva autorizada.
- Añade ocho artefactos canónicos `as-is` y conserva separados hechos, observaciones, inferencias, intención, contradicciones y desconocidos.
- Añade validación integral, comprobación de trazabilidad y migración `0.9` → `1.0` con preview, backup externo y rollback protegido.
- Añade borradores derivados para cliente con selección por estado/clasificación, procedencia, bloqueo sensible, colisiones y aprobación pendiente.
- Completa la integración opcional de PostgreSQL y Keycloak desde la skill de verificación.
- Endurece previews y escrituras transaccionales frente a deriva, colisiones, symlinks, junctions, backups corruptos y evidencias inconsistentes.
- Publica el primer hito versionado del repositorio como `v0.3.0`, candidato para revisión y piloto con Codex, sin convertirlo en política corporativa aprobada.

## 0.2.0 — 2026-08-19 — desarrollo local, no publicado

- Añade el perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, locks exactos y scaffold reproducible.
- Valida backend, frontend, PostgreSQL y Keycloak dentro de sus runtimes bloqueados y mediante comprobaciones HTTP integradas.
- Implementa preparación segura, dry-run, hash de autorización, protección de colisiones y rollback para incrementos listos.
- Implementa planificación y ejecución de verificaciones sin confundir resultados no ejecutados con éxitos.
- Integra la aptitud del perfil H0 en la puerta de readiness y mantiene la selección tecnológica como decisión humana confirmada.

## 0.1.0 — 2026-08-19 — desarrollo local, no publicado

- Crea el manifiesto skills-only y el gobierno inicial.
- Incorpora las tres especificaciones canónicas sin alterar los originales.
- Implementa ayuda, definición y evaluación de readiness.
- Añade esquemas, validadores, inicialización segura de proyectos nuevos y evals reproducibles.
- Mantiene propuestas, decisiones y texto de bloqueos en Markdown; el índice conserva solo referencias operativas.
- Completa anexos condicionales, onboarding, comparación Work–Codex, FAQ, troubleshooting y ayuda contextual en siete partes.
- Endurece la validación del núcleo exacto, tablas, perfil seleccionado y bloqueos por alcance.
- Registra adopción de existentes, implementación y verificación como backlog no disponible.
- Define Codex como entorno objetivo soportado y documenta que Copilot, Claude y otros asistentes no tienen compatibilidad verificada.
