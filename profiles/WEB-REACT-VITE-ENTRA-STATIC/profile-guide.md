# WEB-REACT-VITE-ENTRA-STATIC

Perfil candidate para una SPA React/Vite estática con Microsoft Entra ID. Conserva una frontera frontend separada: no materializa backend, PostgreSQL ni un perfil de sistema implícito.

## Decisiones que el proyecto debe confirmar

- tenant ID y client ID de un registro Entra configurado como SPA;
- redirect URI y post-logout URI exactos por entorno;
- audience y scopes delegados de la API protegida;
- estrategia de consentimiento, conditional access, renovación, expiración, errores y observabilidad.

El scaffold usa MSAL Browser con Authorization Code y PKCE, guarda su caché en `sessionStorage` y no acepta secretos de cliente. La configuración `VITE_*` se incorpora al bundle: cada cambio de entorno genera un artefacto distinto y debe recibir otro digest.

## Límite de certificación

Los tests locales prueban configuración tenant-specific, scopes, callback, logout y adquisición silenciosa como contrato de código. El gate de interoperabilidad exige un `storageState` efímero y el contenido de `sessionStorage` mediante `ENTRA_TEST_SESSION_STORAGE_JSON`, ambos obtenidos de un acceso humano autorizado contra un tenant real. Playwright no conserva `sessionStorage` dentro de `storageState`, por eso el gate los recibe por separado y no los imprime ni incorpora a evidencia. Ese gate, la revisión humana y el piloto siguen `not-run`; por ello este perfil no produce `automation_support: supported`.
