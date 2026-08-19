# Cobertura auditable de M2

Este documento conserva la fotografía histórica cerrada por la versión `0.2.0`. La adopción, migración y entrega incorporadas después se describen en `M3-COVERAGE.md`.

## Hechos verificados

- Existe un único perfil H0: `WEB-FASTAPI-REACT-KEYCLOAK-PG`, estado `candidate`, versión `1.0.0-candidate.1`.
- Python, Node.js, PostgreSQL, Keycloak y nginx están fijados también por digest; las dependencias Python y npm usan locks exactos.
- El gate completo superó lint, tipado, tests, OpenAPI, build y comprobaciones HTTP de API, frontend y discovery OIDC.
- Readiness bloquea perfiles ausentes, distintos de H0 o con lock no validado.
- Implementación exige dry-run, hash coincidente y autorización explícita; no sobrescribe colisiones y revierte una aplicación fallida.
- Verificación separa planificación y ejecución, registra limitaciones y nunca presenta `not-run` como `passed`.

## Correspondencia

| Épica | Implementación | Evidencia |
|---|---|---|
| EP-05 Perfil de referencia | Perfil, lock, guía, scaffold backend/frontend, identidad OIDC, base de datos, contenedores y CI. | `profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/`, `scripts/validate_reference_profile.py` |
| EP-06 Implementación | Puerta previa, preview determinista, autorización, materialización H0, índice y rollback. | `skills/lks-sdd-implement/` |
| EP-07 Verificación | Plan fijo por perfil, ejecución controlada, estados inequívocos y evidencia opcional. | `skills/lks-sdd-verify/` |

## Límites

- El scaffold expresa fronteras técnicas; no inventa dominio ni selecciona el perfil por la persona usuaria.
- El lock validado acredita reproducibilidad técnica del perfil, no aprobación corporativa ni idoneidad universal.
- La adopción automatizada, migraciones y vistas derivadas para cliente permanecen en M3.
