# Changelog

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
