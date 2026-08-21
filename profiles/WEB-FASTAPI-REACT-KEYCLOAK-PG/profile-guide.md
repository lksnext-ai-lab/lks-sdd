# Perfil WEB-FASTAPI-REACT-KEYCLOAK-PG

Este perfil de referencia activo proporciona la combinación web completa H0 de LKS-SDD para Codex: SPA React, API FastAPI, PostgreSQL, identidad Keycloak mediante OpenID Connect y entrega con contenedores OCI. `supported` depende siempre de que su certificación exacta continúe coincidiendo con descriptor, driver, scaffold, composición, gates y lock de la release instalada.

## Condiciones de uso

- Codex solo puede proponerlo después de evaluar requisitos y restricciones.
- Su selección requiere una decisión ADR confirmada en los Markdown del proyecto.
- El lock exacto se copia al proyecto y no se actualiza silenciosamente.
- El scaffold es un punto de partida, no una aplicación terminada ni una arquitectura obligatoria para todos los proyectos.
- Los secretos del proyecto consumidor se suministran mediante el mecanismo aprobado para cada entorno; `.env.example` contiene únicamente nombres y marcadores. `infra/compose/gate.env` contiene credenciales sintéticas exclusivas del gate reproducible y no es una configuración desplegable ni un secreto reutilizable.
- La implementación se limita al incremento confirmado y conserva la trazabilidad requisito–aceptación–decisión–incremento–prueba–evidencia.

## Puerta técnica

`scripts/run_reference_profile_gate.py` copia el scaffold a una carpeta temporal y comprueba locks, lint, tipado, tests, build, OpenAPI y la composición completa. Con `--containers` construye e inicia PostgreSQL, Keycloak, API y frontend usando únicamente las credenciales sintéticas de gate, y verifica salud, OIDC y navegación; no se considera superada si una comprobación requerida no se ejecuta.

El lifecycle `active` significa que el plugin puede automatizar esta composición exacta cuando la certificación está vigente. Expresa capacidad implementada y probada del producto; no equivale a aprobación corporativa, selección automática para un proyecto ni autorización de despliegue.
