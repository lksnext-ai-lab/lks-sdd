# LKS-SDD — extensión propuesta 1.5: catálogo granular y perfiles Microsoft Entra

Estado: propuesta candidate, no canónica
Versión de método: 1.5.0
Plugin de referencia: 0.12.0
Fecha: 2026-08-26

## 1. Problema

Un catálogo basado únicamente en combinaciones completas puede producir dos errores opuestos: multiplicar perfiles por cada permutación tecnológica o declarar que toda una arquitectura carece de automatización aunque varias piezas sí tengan contrato reutilizable. Ninguno autoriza sustituir una decisión confirmada por otra tecnología parecida.

## 2. Modelo acotado

El catálogo mantiene cuatro niveles:

1. la familia clasifica y no es seleccionable;
2. la capability describe un contrato granular reutilizable y sus gates;
3. el perfil exacto cierra una composición y sigue siendo la única unidad seleccionable y certificable;
4. el binding liga el perfil a una unidad desplegable del proyecto.

Las capabilities MUST NOT componerse dinámicamente dentro de un proyecto para crear soporte implícito. Una combinación nueva requiere descriptor, driver, scaffold, lock, gates de capability, gate de composición, evals y certificación exacta.

## 3. Capabilities de identidad

La candidate añade:

- `CAP-OIDC-DISCOVERY-JWKS`: discovery OpenID, issuer exacto y `jwks_uri` declarado por el proveedor;
- `CAP-OIDC-API-BEARER`: autenticación bearer y semántica 401/403;
- `CAP-OIDC-SPA-PKCE`: callback, logout y adquisición de token mediante Authorization Code con PKCE;
- `CAP-ENTRA-CLAIMS`: tenant, audience, scopes delegados y app roles de Microsoft Entra.

`CAP-IDENTITY-OIDC` permanece como contrato base. Las nuevas capabilities no modifican sus bytes ni los de perfiles activos anteriores.

## 4. Perfiles exactos candidate

`API-FASTAPI-ENTRA-PG-OCI` cubre una unidad API con discovery/JWKS, bearer, tenant y permisos Entra, FastAPI, PostgreSQL/Alembic y OCI. `WEB-REACT-VITE-ENTRA-STATIC` cubre una unidad SPA estática React/Vite con MSAL Browser y Authorization Code con PKCE.

Frontend y backend mantienen `UNIT/BIND` separados. Esta versión no declara un perfil de sistema Entra y no sustituye Entra por Keycloak. Ambos perfiles permanecen `candidate`, con lock `validated=false` y certificaciones `not-run`.

## 5. Diagnóstico de cobertura

`automation_support` conserva únicamente `selection-required`, `supported` o `unsupported`. La salida `automation_coverage` es ortogonal y MUST incluir por binding:

- `catalog_fit`: `exact`, `candidate` o `not-catalogued`;
- preparación;
- implementación;
- verificación local;
- interoperabilidad externa;
- evidencia de entrega;
- capabilities declaradas, bloqueadas y ausentes;
- bloqueos de cualificación y siguiente paso.

No existe `partially-supported`. La cobertura no autoriza implementación, no cambia una decisión técnica y no convierte un perfil candidate en soportado.

## 6. Identidad y seguridad

La API obtiene las claves exclusivamente del `jwks_uri` del discovery exacto; MUST validar firma, issuer, audience, tenant, expiración y permisos. Una ruta hardcoded de Keycloak no es válida para Entra. La SPA MUST usar Authorization Code con PKCE y MUST NOT contener client secrets ni persistir tokens en almacenamiento administrado por la aplicación.

Las pruebas locales pueden usar metadata y claims sintéticos. Esa evidencia MUST NOT acreditar interoperabilidad con un tenant real, conditional access, consentimiento, renovación, logout, registro de aplicaciones o permisos productivos.

## 7. Promoción

Promover cualquiera de los perfiles exige ejecutar todos sus gates, incluida interoperabilidad real autorizada, registrar evidencia exacta y revisar seguridad y experiencia humana. Hasta entonces, preparación y gates locales pueden describirse como `defined-not-certified`, pero `automation_support` permanece `unsupported`.

## 8. Compatibilidad

La extensión no cambia `method_version: 1.5.0`, `schema_version: 1.5` ni los documentos consumidores. No requiere migración. No modifica las fuentes de `specs/canonical/`, los perfiles activos ni el motor de certificación; por ello las seis certificaciones activas anteriores conservan sus bytes y vigencia.
