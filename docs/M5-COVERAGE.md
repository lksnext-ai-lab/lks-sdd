# Cobertura auditable de M5

## Hechos verificados

- El builder genera plugin y marketplace de desarrollo con estructura Codex, ZIP reproducible, manifiesto y checksums.
- La configuración de piloto distingue `prepared`, `running`, `closed` y `withdrawn`; el ejemplo no puede iniciar sin muestra, aliases, responsables, seguridad, paquete y rollback.
- Las observaciones usan campos cerrados y se almacenan fuera del repositorio; no admiten texto libre ni proyectos o participantes no autorizados.
- El resumen conserva solo conteos, cobertura de rutas y métricas agregadas, sin códigos `PRJ-*` o `USR-*`.
- La decisión vincula muestra, rutas, seguridad, permisos, calidad documental, carga y canales M4; una incidencia de seguridad fuerza `no-go`.
- GitHub Issues queda reservado a soporte saneado y el canal confidencial de seguridad sigue siendo obligatorio antes del inicio.

## Correspondencia

| Entregable EP-12 | Implementación | Evidencia |
|---|---|---|
| Marketplace de desarrollo | `distribution/marketplace.template.json`, `build_candidate_package.py` | Estructura `./plugins/lks-sdd` y bundle reproducible |
| Documentación y onboarding | `README.md`, `docs/DISTRIBUTION.md`, `pilot/ONBOARDING.md` | Instalación controlada, primera sesión y cierre |
| Canal de soporte | `SUPPORT.md`, `.github/ISSUE_TEMPLATE/` | Issues no sensibles y separación de seguridad |
| Feedback compatible con privacidad | `pilot-observation.schema.json`, `manage_pilot.py` | Contrato cerrado, aliases y almacén externo |
| Plan y resultados | `pilot/PLAN.md`, `pilot-config.example.json`, resumen y decisión | Plan versionado; resultados reales aún pendientes |
| Paquete candidate | `build_candidate_package.py` | Dos ZIP, manifiesto y `SHA256SUMS` |
| Responsables y rollback | Configuración bloqueante, `pilot/ROLLBACK.md` | No se inicia con roles o checksum ausentes |

## Estado de aceptación

La infraestructura de EP-12 está implementada y probada. La aceptación operativa completa de M5 permanece pendiente porque todavía no se ha ejecutado el piloto con 3–5 proyectos y 5–8 participantes ni existe una decisión real. El sistema devuelve `blocked`/`not-run` en vez de fabricar esos resultados.
