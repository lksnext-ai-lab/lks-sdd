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
| Plan y resultados | `pilot/PLAN.md`, `pilot-config.example.json`, resumen y decisión | Herramienta opcional de aprendizaje; resultados reales aún pendientes |
| Paquete de release | `build_candidate_package.py` | Dos ZIP, reporte de calidad ligado al commit, manifiesto y `SHA256SUMS` |
| Responsables y rollback | Configuración bloqueante, `pilot/ROLLBACK.md` | No se inicia con roles o checksum ausentes |

## Estado de aceptación

La infraestructura de EP-12 está implementada y probada. El piloto cuantitativo de 3–5 proyectos y 5–8 participantes permanece pendiente y el sistema devuelve `blocked`/`not-run` en vez de fabricar resultados. Desde 1.0.0 este piloto es una herramienta opcional de aprendizaje: la promoción estable se decide mediante gates técnicos completos y aprobación durable del responsable del proyecto, que puede basarse en el uso satisfactorio agregado de diferentes equipos.
