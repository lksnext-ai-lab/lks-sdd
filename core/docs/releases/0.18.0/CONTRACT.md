# LKS-SDD 0.18.0 — contrato autorizado de entrega

Estado: implementación autorizada; certificación y publicación pendientes.
Origen: plan aprobado expresamente en la tarea del 2026-08-31.
Base: main, 9b13616e9f9d67c7112ee620c65b8ea6831c50c2 (0.17.0).
Trabajo: rama codex/release-0.18.0, worktree C:/Dev/lks-sdd-0.18.0.

## Decisiones y límites

Entregar 0.18.0 como prerelease en el repositorio privado
lksnext-ai-lab/lks-sdd y actualizar exclusivamente el marketplace personal
lks-sdd-development. Commits, push, PR, integración, tag y actualización local
están autorizados por el plan de ejecución. No se autoriza promoción estable,
M6, marketplace público/workspace ni despliegue o certificación productiva.

Se conservan schema_version 1.5, method_version 1.5.0, los Markdown consumidores
como autoridad, las seis skills y su invocación implícita. No se modifican
specs/canonical ni se incorporan MCP, conectores, hooks o agentes ejecutables.
SAT es exclusivamente referencia de lectura: no se modifican documentos,
código, dependencias, datos ni despliegues. Tampoco se ejecuta su aplicación.
Los archivos no versionados site/ y docs/LKS-SDD-SITE-STORYBOARD.md del checkout
original se conservan intactos. La corrección ART-INTEGRATIONS se integra como
cambio independiente; no se publica una 0.17.1.

La compatibilidad documental no constituye compatibilidad de runtime. Una
versión declarada, una versión resuelta y una observada en ejecución son hechos
distintos. La actualización del plugin nunca modifica automáticamente bindings,
locks, variantes ni dependencias del consumidor.

## Catálogo aprobado

| Contrato arquitectónico (no seleccionable) | Perfiles exactos nuevos |
|---|---|
| API-FASTAPI-LOCAL-AUTH-PG-OCI | API-FASTAPI-LOCAL-AUTH-PG-OCI-PY313; API-FASTAPI-LOCAL-AUTH-PG-OCI-PY314 |
| WEB-REACT-VITE-LOCAL-AUTH-STATIC | WEB-REACT-VITE-LOCAL-AUTH-STATIC-TS59; WEB-REACT-VITE-LOCAL-AUTH-STATIC-TS60 |
| WEB-FASTAPI-REACT-LOCAL-AUTH-PG | WEB-FASTAPI-REACT-LOCAL-AUTH-PG-PY313-TS59; WEB-FASTAPI-REACT-LOCAL-AUTH-PG-PY314-TS60 |
| DATA-POSTGRES-OCI | DATA-POSTGRES-OCI-PG18 |
| JOB-ALEMBIC-PG-OCI | JOB-ALEMBIC-PG-OCI-PY313; JOB-ALEMBIC-PG-OCI-PY314 |

| Dependencia | Línea observada en SAT | Referencia actual |
|---|---|---|
| Python / FastAPI | 3.13 / 0.125.0 | 3.14 / 0.141.1 |
| SQLAlchemy / Alembic | 2.0.45 / 1.17.2 | 2.0.52 / 1.19.1 |
| PyJWT | 2.10.1 | 2.13.0 |
| React | 19.2.7 | 19.2.7 |
| TypeScript / Vite | 5.9.3 / 8.0.16 | 6.0.3 / 8.1.5 |
| Vitest | 4.1.10 | 4.1.11 |
| Gestores | pip y npm | uv y pnpm |

Versiones de herramientas, dependencias transitivas e imágenes por digest se
resuelven antes de certificar. Las bibliotecas de seguridad comunes se fijan en
los locks. React 16/17 son pruebas negativas de combinación no cubierta, nunca
nuevo soporte. Los IDs anteriores se conservan. Nueve variantes nuevas
permanecen candidate/unsupported hasta completar certificación. Se recertifican
también los ocho perfiles activos; los otros seis candidatos no se promueven.

## Trabajo y aceptación trazable

Cada ID es un bloque independiente. CHECKPOINT.md registra estado, cambios,
comandos, resultados, revisión y pendientes. La evidencia no ejecutada permanece
not-run; un checkpoint documental no acredita un gate técnico.

| ID / hito | Entrega y aceptación obligatoria | Verificación y evidencia prevista |
|---|---|---|
| R18-01 / H0 | Este contrato, decisiones, dependencias y mapa íntegro de alcance | Revisión frente al plan autorizado; diff limitado a documentación |
| R18-02 / H1 | ART-INTEGRATIONS acepta tablas externa/interna, juntas, separadas o ausentes si no aplican; IDs y estados preservados; duplicados rechazados | Regresiones de parseo, referencias y round-trip de plantilla y bundle |
| R18-03 / H1 | Semántica común de operaciones declaradas, observadores HTTP/PG/migración; login no acredita persistencia; browser solo flujo web | Pruebas de planificación, readiness, runner, registro y trazabilidad; rutas sin /api/v1 |
| R18-04 / H2 | Contrato reutilizable separado de variante, scaffold y resolución; cinco contratos, nueve IDs exactos | Validación de catálogo/drivers/locks y combinaciones no seleccionables |
| R18-05 / H2 | Diagnóstico de manifiestos/locks/runtime sin instalación; incompatibilidad, no evaluado e insuficiencia separados; detección de drift | Fixtures de ambas líneas; dependencia modificada con lock de perfil intacto; React 16/17 |
| R18-06 / H2 | Preparación explícita new-project/adoption; adaptadores empaquetados backend/frontend y apps/backend/apps/frontend; preview sin sobrescritura | Dos fixtures genéricos sin negocio/datos SAT; hashes de archivos antes/después; rechazo de comandos arbitrarios |
| R18-07 / H2 | Composición desde INT.Exact composition, lock y participantes en identidad; DB/job independientes sin unidad ficticia de sistema | Casos positivos de cuatro unidades y negativos de participantes, identidad y bindings |
| R18-08 / H3 | CAP-LOCAL-CREDENTIALS: Argon2id, alta administrada, cambio con reautenticación y recuperación asistida de un uso | Tests de hash/salt/parámetros y revocación; sin registro público ni correo |
| R18-09 / H3 | CAP-LOCAL-JWT-SESSION: HS256, keyring aleatorio >=256 bits, kid controlado, validación de claims, acceso 15 min | Tokens alterados/expirados/incompletos, otra audiencia/emisor/clave, rotación, revocación |
| R18-10 / H3 | CAP-LOCAL-AUTH-SPA: acceso solo memoria, refresh opaco hash PG/cookie HttpOnly Secure SameSite; rotación atómica y detección de reutilización; máximo 8 h / inactividad 30 min | HTTPS local real, concurrencia, varias pestañas, expiración, logout idempotente y sin red |
| R18-11 / H3 | CAP-TENANT-AUTHORIZATION: usuario/pertenencia activos, permisos vigentes en servidor, denegación por defecto, aislamiento objetos/relaciones | Usuarios inexistentes/inactivos/sin pertenencia; cambio de permisos/empresa; accesos cruzados |
| R18-12 / H3 | CAP-SECURITY-CONFIG-AUDIT: errores genéricos, límites cuenta/origen y recursos, TLS/CORS/CSRF/origen, secretos externos y auditoría saneada, fallo cerrado | Abuso concurrente, indisponibilidad sesión/DB, ausencia de secretos/credenciales, configuración insegura rechazada |
| R18-13 / H3 | API, SPA, PostgreSQL y migrador verificables independientemente; contrato HTTP móvil separado sin certificar cliente nativo | Gates de cada componente; migración vacía y desde anterior; recuperación/forward-fix con datos sintéticos |
| R18-14 / H4 | Dos sistemas completos con UI/API/DB reales | Escritura UI, observación SQL independiente, recarga, reinicio API, fallos/lentitud API/DB/sesiones sin mocks |
| R18-15 / H4 | Coherencia integral de plantillas/artefactos; pendientes legítimos diferenciados de errores | Round-trip completo desde repositorio y bundle extraído; visual por TASK y not-applicable determinista |
| R18-16 / H4 | Certificación enlazada a observaciones saneadas y sus hashes; dependencia de motor semántico; lectores históricos | Evidencias de otra revisión/variante/entorno rechazadas; formato anterior legible; seis scopes conservados |
| R18-17 / H4 | Minimización y saneamiento antes de stdout/persistencia; evidencia contaminada bloqueada sin reescribir historia | Credenciales HTTP/logs/trazas/capturas, procedencia alterada, persistencia simulada, logout falso, mocks funcionales |
| R18-18 / H4 | Diagnóstico de impacto read-only conservador; identidad build estable separada de ejecución | Contratos/perfiles/variantes/locks/fixtures/certs afectados con motivo; incertidumbre amplía; nunca exime recertificar |
| R18-19 / H5 | Baseline publicada 0.17 verificada; documentación/workflow/harness alineados; inventario exacto actualizado | Hashes assets baseline; fast/integration/package/profile/evals/benchmark/harness candidate; presupuestos existentes |
| R18-20 / H5 | Recertificación 8 activos + 9 nuevos con motor definitivo; paquete completo reproducible | Certs exactas; gate.status=passed y eligible=true; doble build mismo SHA/fecha/reporte byte a byte; validación de ambos extraídos |
| R18-21 / H6 | Commits por bloque, PR revisable, CI, integración y checkout dedicado limpio del SHA main final | Revisión diff/secretos/canónicos; reporte fuera del checkout; tag anotado v0.18.0; workflow del tag antes de publicar |
| R18-22 / H6 | Prerelease privada con cinco assets y evidencias dentro de bundles; lectura posterior | ZIP plugin, ZIP marketplace, quality-report.json, release-manifest.json, SHA256SUMS; descarga/hash/versión/SHA/inventario/enlaces |
| R18-23 / H6 | Marketplace descargado verificado en nueva carpeta 0.18; copia 0.17 conservada y rollback preparado | CLI soportado remove/add, registro/version/seis skills, reinicio y tarea nueva para activación; estados separados |
| R18-24 / H6 | Cierre trazable y hoja de adaptación SAT sin ejecutarla | SHA/tag/URL/hashes/pruebas/variantes/pendientes; cambios consumidores documentales/funcionales separados del plugin |

## Dependencias y puntos de control

H0 -> H1 -> H2 -> H3 -> H4 -> H5 -> H6. H5 depende de todas las
regresiones H1-H4. Cada bloque se cierra con evidencia verificable antes del
siguiente hito; la documentación puede avanzar sin declarar gates superados.
Las suites y presupuestos de docs/VALIDATION.md permanecen bloqueantes. Un
ajuste necesita medición de coste; nunca sirve para ocultar un fallo.

Certificación inicial: desarrollo aislado y CI con identidades/datos sintéticos
y HTTPS local. MFA, federación, recuperación autoservicio y producción quedan
fuera. La revisión visual, humana, piloto e interoperabilidad real conservan su
estado real incluso si la automatización candidate pasa.

## Publicación y recuperación

La baseline es la release 0.17.0 descargada y verificada. Tras integrar el PR,
el SHA final de main se valida en checkout dedicado limpio, con salida externa.
Los dos builds comparten SHA, fecha real de certificación y reporte. Solo tras
CI y workflow del tag correctos se publica v0.18.0. No se mueven tags ni se
sustituyen silenciosamente assets o releases existentes.

Solo el marketplace descargado de esa release y verificado puede alimentar
C:/Users/j.ormazabal/.codex/marketplaces/lks-sdd-development-0.18.0. Se guarda
estado para rollback y se usa el CLI instalado: marketplace remove
lks-sdd-development y add con la raíz verificada. No upgrade para fuente no Git,
ni edición manual de caché, ni cambios globales ajenos a LKS-SDD. Registro,
publicación y activación son estados independientes. Reinicio y tarea nueva
deben observar la versión y seis skills antes de acreditar activación.

Si fallan paquete, CI o assets, no se publica ni actualiza. Si falla registro o
carga, se restaura y verifica la fuente 0.17.0 por el mecanismo soportado.
Restaurar plugin no revierte consumidores ni garantiza lectura de nuevos
formatos internos. No se borra evidencia como reparación.
