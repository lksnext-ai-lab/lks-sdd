# API-FASTAPI-SIMULATED-OIDC-PG-OCI

Perfil activo y estrictamente no productivo para una API FastAPI con PostgreSQL, OCI y un doble OIDC controlado. El scaffold expone discovery, JWKS y emisión de tokens sintéticos con una clave RSA efímera generada al arrancar.

## Frontera de seguridad

- `APP_ENV` debe ser uno de los entornos no productivos cerrados del perfil; ausencia, valores desconocidos y producción bloquean identidad, readiness y endpoints del doble.
- El issuer usa exclusivamente `/__test__/oidc`; HTTP se limita a loopback y HTTPS permite integración o aceptación-preproducción con la topología/CORS decidida por el proyecto.
- El issuer, audience, tenant, expiración y permiso se validan antes de aplicar autorización local.
- Los sujetos y objetos son identificadores sintéticos estables; correo y nombre nunca actúan como clave.
- La clave privada no se versiona ni se persiste y cambia en cada arranque.
- Este perfil no acredita Microsoft Entra, conditional access, consentimiento ni registros de aplicación.

## Uso previsto

Desarrollo, CI, integración y aceptación-preproducción cuando el contrato del proyecto permita explícitamente identidad simulada. Producción debe usar y certificar un perfil exacto del proveedor real.
