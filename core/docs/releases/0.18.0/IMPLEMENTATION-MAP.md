# Correspondencia de alcance, implementación y evidencia

Este mapa enlaza todos los bloques aprobados. Un enlace a pruebas no afirma que
la release haya pasado: el resultado definitivo pertenece a certificaciones
exactas, quality-report y release-manifest. Consultar CHECKPOINT para el estado.

| Bloque | Implementación principal | Prueba o evidencia de cierre |
|---|---|---|
| R18-01 | CONTRACT.md y CHECKPOINT.md | Correspondencia con plan autorizado y revisión del diff |
| R18-02 | document-contracts.json, delivery_engine.py | test_integrations_v018: ambas tablas, opcionalidad, IDs y round-trip |
| R18-03 | integration_contract.py, planning_engine.py, readiness y runner | Operaciones fuera de /api/v1, login ajeno rechazado, observadores por protocolo |
| R18-04 | architecture-contracts.json y nueve directorios de perfil | validate_reference_profile --all --allow-unvalidated; catálogo exacto |
| R18-05 | technology_resolution.py, validate_reference_profile.py | Declarado/resuelto/runtime, deriva de dependencias, React 16/17 negativos |
| R18-06 | adoption_preparation.py, prepare_increment.py | Fixtures adoption-flat/apps-v018; conservación de cada byte funcional |
| R18-07 | composition_contract.py, preparación, readiness, build identity | Cuatro participantes, ausencia de unidad ficticia, faltas y unidades ajenas rechazadas |
| R18-08 | shared/local-auth/backend/security.py, main.py y provision.py | GATE-LOCAL-CREDENTIALS y tests reales de PostgreSQL |
| R18-09 | security.py y GATE-LOCAL-JWT | Claims, algoritmo, clave, expiración, rotación y revocación |
| R18-10 | main.py, frontend/auth.ts y observador browser | Refresh concurrente/reutilización; cookie segura; memoria, pestañas y logout |
| R18-11 | main.py y tablas de organizaciones/pertenencias | GATE-TENANT-AUTHORIZATION y accesos por objetos/relaciones |
| R18-12 | body_limit.py, security.py, middleware y auditoría | GATE-SECURITY-CONFIG/AUDIT; agotamiento, CSRF y fallos cerrados |
| R18-13 | Nueve drivers y verification/gate.py | Gates independientes API/SPA/PG/job y observador HTTP sin cliente nativo |
| R18-14 | verification/web_gate.py, browser/auth.spec.js, http_probe.py | Browser real, SQL independiente, lectura tras reinicio y outage sin fallback |
| R18-15 | Plantillas, materializadores, esquemas y suites de consumidor | Suites fast/integration/package/profile; round-trip y visual por TASK |
| R18-16 | observation_contract.py, profile_registry.py, runner y schema cert 1.1 | Manifest de observaciones/capturas, hashes exactos y lectores históricos |
| R18-17 | evidence_safety.py, evidence_contract.py y observadores | Saneamiento previo a salida; evidencia contaminada/SQL simulado/locks ajenos rechazados |
| R18-18 | profile_impact.py y build_identity_material | Impacto conservador, nunca exención; build estable separado del run |
| R18-19 | Baseline v0.17.0, workflow, harness y FX-61..69 | Assets baseline verificados; 54 casos automatizados; humanos nuevos not-run |
| R18-20 | Certificación de 8 activos y 9 variantes; builder | Gates completos exactos, candidate passed/eligible, dos builds idénticos |
| R18-21 | Rama codex/release-0.18.0 y commits funcionales | PR/CI, main final y checkout limpio; reporte externo y tag anotado |
| R18-22 | Prerelease privada v0.18.0 | Cinco assets descargados y comprobados contra manifest/SHA256SUMS |
| R18-23 | Marketplace personal local y copia 0.17 conservada | remove/add soportados; registro y activación verificados por separado |
| R18-24 | SAT-ADAPTATION.md y cierre de release | SHA/tag/URL/hashes/estados y hoja documental/funcional sin ejecución SAT |

Las referencias `shared/local-auth` de la tabla corresponden a
`profiles/_shared/local-auth`. No se cambian las fuentes de `specs/canonical/`.
La certificación no incluye canales humanos/piloto no ejecutados ni producción.
