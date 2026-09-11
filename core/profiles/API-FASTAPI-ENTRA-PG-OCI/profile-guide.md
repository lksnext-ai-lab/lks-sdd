# API-FASTAPI-ENTRA-PG-OCI

Perfil candidate para una unidad API FastAPI con Microsoft Entra ID, PostgreSQL y entrega OCI. El perfil es exacto y cerrado: no sustituye Entra por Keycloak ni se combina dinámicamente con un frontend.

## Decisiones que el proyecto debe confirmar

- tenant ID, issuer v2.0 tenant-specific y audience de la API;
- scopes delegados y app roles admitidos, incluyendo la semántica de 401 y 403;
- modelo de datos, migraciones, recuperación, compatibilidad OpenAPI, SLO y observabilidad;
- registro de aplicación y permisos Entra separados de cualquier secreto o credencial.

El scaffold liga el issuer público global `https://login.microsoftonline.com/<tenant>/v2.0` al tenant confirmado antes de consultar la red, obtiene `jwks_uri` de su documento OpenID y valida firma, issuer, audience, tenant y permisos. Una nube soberana requiere otro perfil exacto; no se relaja este contrato mediante configuración. No usa rutas específicas de Keycloak. `ENTRA_TEST_ACCESS_TOKEN` solo se admite como variable efímera durante un gate autorizado y nunca debe persistirse ni aparecer en evidencias.

## Límite de certificación

Las pruebas locales con metadata y claims sintéticos cubren contrato, 401 y 403, pero no prueban un tenant real. `GATE-OIDC-INTEGRATION`, la composición completa, la revisión humana y el piloto siguen `not-run`; por ello este perfil no produce `automation_support: supported`.
