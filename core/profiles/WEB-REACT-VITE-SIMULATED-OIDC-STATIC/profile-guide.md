# WEB-REACT-VITE-SIMULATED-OIDC-STATIC

Perfil activo y estrictamente no productivo para una SPA React/Vite con un doble OIDC controlado. Conserva la frontera de autenticación, genera PKCE S256 por acceso sintético y mantiene sesión y access token únicamente en `sessionStorage`.

## Frontera de seguridad

- `VITE_APP_ENV` debe ser uno de los entornos no productivos cerrados del perfil; ausencia, valores desconocidos y producción bloquean el adaptador.
- El issuer usa exclusivamente `/__test__/oidc`; HTTP se limita a loopback y HTTPS permite una topología browser-reachable de integración o aceptación-preproducción.
- No admite client secret, implicit flow ni persistencia en `localStorage`.
- El token endpoint debe ser el del doble no productivo acordado.
- Este perfil no acredita Microsoft Entra, consent, conditional access, renovación ni logout reales.

## Uso previsto

Desarrollo, CI, integración y aceptación-preproducción con identidades sintéticas. La sustitución por el proveedor productivo se realiza tras la interfaz de identidad y exige otro binding exacto certificado.
