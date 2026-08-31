# Variantes, diagnóstico y adopción en 0.18

Los proyectos conservan schema 1.5 y método 1.5.0. Un contrato arquitectónico
agrupa variantes, pero no es seleccionable. La selección continúa usando
`PROFILE-ID@version`, con ADR, binding y lock exactos. El scaffold es una
implementación de referencia; el diagnóstico de un consumidor no instala
dependencias ni copia su código.

| Contrato descriptivo | Variantes exactas, sufijo del ID |
|---|---|
| API-FASTAPI-LOCAL-AUTH-PG-OCI | PY313, PY314 |
| WEB-REACT-VITE-LOCAL-AUTH-STATIC | TS59, TS60 |
| WEB-FASTAPI-REACT-LOCAL-AUTH-PG | PY313-TS59, PY314-TS60 |
| DATA-POSTGRES-OCI | PG18 |
| JOB-ALEMBIC-PG-OCI | PY313, PY314 |

| Dimensión fijada | Línea PY313 / TS59 | Línea PY314 / TS60 |
|---|---|---|
| Python / FastAPI | 3.13.15 / 0.125.0 | 3.14.7 / 0.141.1 |
| SQLAlchemy / Alembic | 2.0.45 / 1.17.2 | 2.0.52 / 1.19.1 |
| PyJWT | 2.10.1 | 2.13.0 |
| Node / React | 24.19.0 / 19.2.7 | 24.19.0 / 19.2.7 |
| TypeScript / Vite | 5.9.3 / 8.0.16 | 6.0.3 / 8.1.5 |
| Vitest | 4.1.10 | 4.1.11 |
| Gestores | pip 26.2.1 / npm 11.12.0 | uv 0.12.5 / pnpm 10.34.5 |

PostgreSQL 18.4 es compartido. Los locks incluyen dependencias transitivas e
imágenes por digest; esta tabla no sustituye sus identidades exactas ni afirma
que el SAT ejecute estas versiones resueltas. La imagen Python de la segunda
línea también fija pip 26.2.1 como herramienta auxiliar.

Cada directorio de perfil contiene descriptor, driver, lock y
`resolved-technology.json`. Este último distingue dependencias bloqueadas de
observaciones de ejecución. La evidencia completa añade observaciones saneadas,
capturas, hashes y huella del motor semántico. Una declaración `version_range`
no es una prueba de compatibilidad. La consulta de perfiles determina el soporte
vigente; ni el nombre del perfil ni su presencia en el paquete lo garantizan.

```text
python <plugin-root>/scripts/lks_sdd.py compatibility <project-root> --profile API-FASTAPI-LOCAL-AUTH-PG-OCI-PY313 --json
python <plugin-root>/scripts/lks_sdd.py profile-impact --help
```

El diagnóstico separa `incompatible` (contradicción demostrada), `not-evaluated`
(combinación no cubierta), `insufficient-information` y `catalog-match`. El
último no acredita ejecución del consumidor. Se comparan manifiestos, locks,
runtime declarado, herramientas y huellas. React 16/17 son negativos del catálogo,
no nuevas variantes soportadas. Una actualización del plugin no modifica las
dependencias, bindings, decisiones ni locks del consumidor.

## Preparación existente y composición

`new-project` materializa fuentes del scaffold. `adopt-existing` usa adaptadores
para `backend/`–`frontend/`, `apps/backend/`–`apps/frontend/` o una unidad explícita.
Observa entradas ASGI y fragmentos HTTP estáticos sin importarlos ni ejecutar
comandos de metadatos. Los prefijos de routers y la conducta real siguen sin
verificarse hasta contrastar el contrato.

El preview de adopción prepara exclusivamente recursos bajo
`.lks-sdd/verification/` y descriptores/locks/huellas de verificación. Conserva
cada byte funcional existente. La configuración de fixture y el encaje funcional
quedan como pendientes explícitos: el runner impide ejecutar provisión o
migraciones del scaffold contra una aplicación adoptada. Las adaptaciones del
consumidor necesitan su propio alcance; no se infieren de un match tecnológico.

API, SPA, base de datos y migrador tienen cuatro UNIT/BIND independientes. Una
INT selecciona el sistema con `Exact composition`; no se crea una quinta unidad
ficticia. La identidad incluye el lock del sistema y todos sus participantes.
Si falta uno, cambia su variante, unidad o lock, la verificación falla cerrada.

## Observadores y seguridad

Las tablas externas e internas de integraciones son opcionales y coexisten.
Sus INT son únicos y no se renumeran. Una referencia externa no exige UNIT.
HTTP declara operaciones `METHOD /ruta`; PostgreSQL, `TABLE recurso`; migración,
`REVISION origen -> destino`. El flujo web conjunto exige navegador. Una tarea
aislada de base de datos no lo exige. Login, auditoría o una escritura ajena a
la INT no acreditan persistencia de negocio.

La referencia local usa Argon2id, JWT HS256 con keyring externo, acceso en memoria,
refresh opaco rotatorio en cookie Secure/HttpOnly/SameSite, almacenamiento hash,
revocación servidor, permisos actuales y aislamiento por organización. Requiere
HTTPS y origen exacto; limita cuerpos, trabajo de contraseñas y concurrencia.
El cliente acota las esperas y no afirma revocación remota sin confirmación.

Solo se certifican desarrollo aislado y CI con datos sintéticos. MFA, registro
público, recuperación por correo, federación, cliente móvil nativo y producción
quedan fuera. El contrato HTTP puede comprobarse sin certificar una aplicación
móvil. Caída y lentitud se registran con su resultado real: un timeout no se
convierte en un HTTP 503 ni en una comprobación humana superada.

El informe de impacto es de lectura y amplía alcance ante incertidumbre. Nunca
permite omitir recertificación. Los lectores históricos no reescriben evidencia
previa ni garantizan su suficiencia con el motor vigente.
