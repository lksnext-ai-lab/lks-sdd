# Changelog

## 2.0.2 — 2026-09-18 — rutas largas Windows

- Normaliza internamente raíces Windows mediante rutas extended-length sin persistir
  el prefijo `\\?\` en contratos, recibos, hashes, mappings ni mensajes de negocio.
- Mantiene las comprobaciones de symlinks, junctions, escapes, `.git`, repositorios
  anidados y secretos; los fallos reales de `MAX_PATH` ahora son explícitos y accionables.
- Añade una regresión Windows que compara instalación corta/larga, contrato, perfiles,
  todas las entradas de integridad del runtime, diagnóstico, preview y ausencia de
  escrituras en el proyecto consumidor.

## 2.0.1 — 2026-09-18 — migración 1.5→2.0

- Añade migración oficial autónoma y reversible desde 1.5 a 2.0 con inventario
  cerrado, preview autorizado por hash exacto, conservación uno-a-uno y recibo
  auditable.
- Impide cortes mixtos, conserva runtime/lock legacy como histórico y bloquea
  solo las TASK que requieren reconciliación semántica antes de continuar.
- Refuerza `migration-status` contra alteraciones de mapping, disposiciones,
  contadores, fingerprints y recibos; mantiene separadas la migración técnica,
  la autoridad de negocio y la aceptación por host.
- Corrige la documentación de rutas de variantes 1.5/2.0 y actualiza el catálogo
  de distribución Copilot a `copilot-v2.0.1`.

## 2.0.0 — 2026-09-18

- Dependencias Python de validación declaradas con versiones/hashes, instalación
  explícita y CI limpio; ausencia de `jsonschema` bloquea con diagnóstico accionable.

- Contrato documental 2.0 y método 2.0.0, separados de la versión del plugin.
- Especificaciones humanas por funcionalidad, relaciones navegables, catálogo e
  historia recuperables; consulta documental de solo lectura y código condicionado.
- Contexto literal de ejecución, alcance autorizado, diff real, continuidad,
  corrección, evidencia tipada y variantes de proyecto con cierre controlado.
- Migración explícita desde 1.5, originales conservados, recuperación y rollback
  protegidos, reconciliación de identidades y recibos de seguimiento remoto.
- Se conservan seis skills, runtime fijado y motor de perfiles. La aprobación de
  publicación v2 es independiente; no hereda aceptación 1.x ni activa instalaciones.
- Guías v2, compatibilidad/migración e instalación actualizadas; temporales y salidas
  regenerables retirados del checkout, conservando contratos y evidencias.

### Consultas humanas del proyecto

- Añade `query`, un lector documental de solo lectura con relaciones en ambos
  sentidos, prosa, procedencia y enlaces; admite documentación anterior o parcial a SDD.
- Permite contraste estático con código por petición expresa o carencia documental
  ligada al contexto previo; no ejecuta ni modifica el consumidor.
- Integra una guía de respuesta profesional y comprensible en las seis skills,
  con separación entre lo acordado, propuesto, observado, inferido y desconocido.
- Mantiene validación contractual, autorización, evidencia histórica, runtime
  fijado y aceptación humana como estados separados. No publica ni activa el plugin.

### Variantes tecnológicas de proyecto

- Añade diagnóstico por niveles y aprobación local durable preview/hash/apply,
  con caducidad y alcance ligado a stack, manifests/locks, observer, AUTH y entorno.
- Conserva el modo estricto y las certificaciones/locks; una variante aprobada no
  se convierte en un perfil global. Preparación optativa sin copiar el scaffold.
- Ejecuta observers revisados en Docker aislado y registra artefactos, hashes,
  gates ejecutados/reutilizados/omitidos y reservas en evidencia canónica.
- Permite cierre de TASK con política explícita y todos sus gates críticos pasados,
  manteniendo entrega, release y producción como decisiones separadas.

La distribución dual 1.1.1 conserva un plugin nativo de agente para Copilot,
preparación explícita del proyecto sin skills duplicadas, migración reversible por
recibos, una guía desde cero compartida por README y la skill de ayuda, y corrige el
presupuesto de rutas de la distribución nativa de Windows.

## 1.1.1 — 2026-09-11 — corrección de rutas de distribución

- Acorta de forma determinista sólo las rutas de evidencia dentro de los paquetes,
  sin cambiar la fuente hash-addressed, los bytes observados ni los contratos de
  perfiles del repositorio.
- Revalida hashes y tamaños de los artefactos de certificación, actualiza los
  manifiestos derivados y entrega el mismo núcleo compacto a Codex y Copilot.
- Calibra de 60 a 90 segundos el límite interno por módulo `fast`, tras medir
  60,191 s para el shard de experiencia limpio; conserva el límite bloqueante
  de 120 s de la suite y todas las aserciones funcionales y de rendimiento.
- Simplifica la puerta de release para ejecutar una sola vez el harness integral:
  elimina la ejecución previa de preflight y las suites/evals duplicados de la
  ruta estándar, pero conserva la atestación completa inicial, los cuatro tiers,
  los evals y el doble build. El techo externo de 900 s sólo recupera el diagnóstico
  de un despachador bloqueado; los presupuestos bloqueantes de cada tier siguen
  aplicándose dentro de su runner.
- Reduce la fixture Git de portabilidad a `.gitattributes` y los artefactos
  contractuales hash-locked que el test compara realmente. Conserva clon local,
  `core.autocrlf`, bytes, hashes y `git diff --check`, sin repetir sobre 1.307
  archivos el contrato ya validado por el harness.
- Actualiza la etiqueta de instalación nativa de Copilot a `copilot-v1.1.1` y la
  documentación de actualización, sin cambiar schema/método del consumidor ni
  activar instalaciones personales.
- La publicación estable requiere una aprobación propia 1.1.1 y los gates limpios,
  reproducibles y de paquete del commit exacto; los canales humanos detallados y el
  piloto permanecen con su evidencia real.

## 1.1.0 — 2026-09-11 — distribución dual estable

- Promoción estable aprobada por el responsable tras comunicar pruebas satisfactorias
  en Copilot; aprobación propia, sin convertir canales detallados not-run en passed.
- Instalación desde el panel mediante el catálogo del mismo repositorio, que fija
  una etiqueta inmutable del paquete Copilot generado; no se mantiene un segundo código.
- Instalación local alternativa desde la interfaz de ajustes, sin editar JSON.
- Conserva el contrato consumidor, perfiles exactos y límites de la RC descrita debajo.

## 1.1.0-rc.1 — 2026-09-11 — distribución dual en evaluación

- Un núcleo y seis workflows para Codex desktop y GitHub Copilot VS Code Agent.
- Instalador offline con preview/hash/apply, runtime fijado por proyecto, preservación
  de instrucciones, detección de colisiones, retirada y recuperación durable.
- Relevo visual Copilot→Codex con retorno opcional, sin API adicional. Codex nativo
  conserva el proceso sin avisos ni fichas de relevo.
- Validación de identidad, fuentes, imágenes y aprobación canónica al reanudar;
  historial inmutable, nuevas revisiones y colaboración secuencial entre clones.
- Paquetes duales y setup reproducibles, checksums y CI con inventario dinámico.
- La aceptación humana de host, el piloto, la release limpia y publicación no se
  presuponen por disponer de código o paquetes de evaluación.

## 1.0.0 — 2026-09-03 — primera release estable

- Promueve LKS-SDD a su primera línea estable sin cambiar `schema_version: 1.5`
  ni `method_version: 1.5.0`.
- Conserva las seis skills, la invocación implícita, los 23 perfiles y las
  certificaciones técnicas exactas heredadas de 0.18.0.
- Sustituye el piloto cuantitativo obligatorio como autoridad de promoción por
  una aprobación durable del responsable del proyecto, informada por el uso
  satisfactorio del plugin en diferentes equipos.
- Mantiene visibles `definition-conversation`, `activation`, `document-review`
  y `pilot`: un estado `not-run` no se convierte en `passed`, aunque estos
  canales detallados dejan de bloquear `stable`.
- Añade el schema y la evidencia saneada `release-approval`, sin identidades,
  conversaciones, proyectos ni resultados individuales.
- Extiende el harness, el empaquetado reproducible y CI para certificar tanto
  canales `candidate` como `stable`.
- Conserva 0.18.0 como rollback y separa preparación, commit, publicación,
  instalación y activación.

## 0.18.0 — 2026-08-31 — autenticación local y variantes certificadas

- Conserva schema 1.5/método 1.5.0, seis skills, invocación implícita y M0–M5.
- Repara las tablas externas/internas de ART-INTEGRATIONS sin renumerar IDs.
- Añade cinco contratos y nueve variantes exactas para API, SPA, PostgreSQL,
  Alembic y sistema con autenticación local. Su soporte exige certificación vigente.
- Separa diagnóstico tecnológico, preparación nueva y adopción sin sobrescritura.
- Enlaza composición con todos los participantes y evidencia con observaciones,
  hashes y motor semántico; añade negativos y saneamiento previo a persistencia.
- Usa 0.17.0 publicada y verificada como baseline de regresión.
- No certifica producción, cliente móvil nativo, MFA, federación, piloto ni canales
  humanos no ejecutados. No modifica el SAT ni promueve los candidatos anteriores.

Los perfiles `active` comprometidos tienen certificación exacta del motor
actual. El SHA final, la elegibilidad y los assets de la release se acreditan
en `quality-report.json`, `release-manifest.json` y `SHA256SUMS`.

## 0.17.0 — 2026-08-31 — integración multiunidad fail-closed

- Añade un contrato canónico aditivo `INT-###` con consumidor, productor, bindings, operaciones, scopes de evidencia, propietario, TASK conjunta y composición exacta.
- Comparte los scopes `component`, `contract`, `composition`, `user-flow`, `persistence` y `visual` entre planificación, readiness, runner, EVID 1.3, status y trazabilidad.
- Impide que gates de componente, capturas o procesos arrancados por separado cierren criterios cross-unit; sin perfil de sistema exacto certificado informa `automation_support=unsupported`.
- Añade `GATE-BROWSER-FULLSTACK-E2E` con navegador real, API funcional real, mutación UI, lectura, recarga, persistencia, requests, correlación, capturas con hash y errores de consola.
- Rechaza mocks de dominio `/api/v1` para composición/flujo/persistencia y mantiene separado un doble de identidad no productivo autorizado.
- Conserva evidencia histórica sin reescritura y expone `reconciliation-required`; la evidencia de componente demostrada sigue siendo válida para ese alcance.
- Mantiene la aplicabilidad TASK-aware y no exige full-stack a backend-only, frontend standalone o slices sin interfaz confirmada.
- Evoluciona el perfil de sistema React/FastAPI/Keycloak/PostgreSQL a 2.1 `active` con certificación Docker exacta, salud OIDC observable y disponibilidad con reintentos acotados; los canales humanos y externos permanecen `not-run`.
- Versiona los perfiles dependientes del scaffold compartido: API Keycloak/PostgreSQL 1.1.0 y sistema Angular 1.0.0-candidate.2. Cada lock se reconcilia con sus fuentes exactas; el sistema Angular conserva su estado no certificado.

## 0.16.0 — 2026-08-29 — evidencia de validación por tarea

- Cierra el contrato visual 1.2 con política configurable de una a cinco imágenes por TASK de interfaz, semántica verificable, integridad SHA-256, dimensiones reales y rechazo controlado de duplicados o contradicciones.
- Genera en una sola pasada fichas de evidencia derivadas para todas las TASK durante `work verify`; las fichas no son autoridad, no se editan manualmente y no participan en `verification_subject`.
- Mantiene EVID históricas inmutables y separa verificación histórica, salud actual, hallazgos posteriores y re-verificación pendiente.
- Evoluciona `work status` con `current_task: null` cuando no existe una TASK activa y separa código, tests, verificación, salud y entrega sin exponer recibos ni hashes en la vista breve.
- Limita Jira a un comentario por hito de verificación, fallo, hallazgo, corrección o re-verificación; un resultado distinto de `verified` nunca transiciona a Done.
- Conserva lectura de proyectos y EVID 0.15, rollback atómico, trazabilidad y reutilización por `verification_subject`; los nuevos artefactos visuales usan schema 1.2 sin reescribir los históricos 1.1.
- Añade fixture genérico, regresiones adversariales, benchmark 0.15→0.16, guía de migración y validación de empaquetado reproducible.

## 0.15.0 — 2026-08-29 — experiencia ágil y harness de calidad

- Añade status management/developer/audit, fast path `work` compuesto y transaccional, `doctor --quick`, lifecycle vigente de problemas, instrumentación local y una reducción medida del 60 % de comandos administrativos.
- Separa `verification_subject` de la revisión administrativa para reutilizar gates solo con identidad técnica/contractual idéntica; cualquier ambigüedad o cambio técnico invalida de forma segura.
- Comparte el parser canónico de listas/rangos entre checker y actualizador y completa evidencia 1.2 single/multiprofile con validación CLI y rollback posterior a escritura.
- Clasifica todos los módulos de tests exactamente una vez en `fast`, `integration`, `package` o `profile`; `all` conserva la ejecución integral sin duplicados y el CLI sin argumentos sigue siendo compatible.
- Añade progreso por stderr, tiempos por test y módulo, selección focalizada y por cambios, límites por fase y terminación del árbol completo de procesos cuando expira un timeout.
- Hace que el harness falle antes de lanzar tests si el checkout está sucio, evita sobrescrituras opacas sin una razón de rerun y separa la certificación Docker del presupuesto ordinario candidate.
- Evoluciona el quality report a 1.2 con telemetría diagnóstica y presupuestos bloqueantes; conserva el schema 1.1 para validar evidencia histórica sin permitir que sustituya el reporte 1.2 de una release nueva.
- Introduce GitHub Actions escalonado para PR, `main` y tags, sin secretos ni publicación automática, y mantiene todos los canales semánticos, humanos, Entra y Rovo/Jira no ejecutados en su estado real.
- Conserva `method_version: 1.5.0` y `schema_version: 1.5` como único contrato operativo; elimina schemas y migradores públicos pre-1.5 sin reescribir la procedencia `plugin_version` ni la evidencia histórica.

## 0.14.2 — 2026-08-28 — evidencia autoconsumible y registro transaccional

- Hace canónica la identidad de perfil del EVID 1.2: una ejecución con un solo binding registra arriba su `profile_id` y `profile_version` exactos; una ejecución multiperfil omite ese resumen y conserva la identidad completa en `profile_bindings`, `profile_locks` y `build_identity_material`.
- Valida conjuntamente bindings, perfiles/versiones, locks, material canónico y `build_id`; mantiene legibles las evidencias 1.2 heredadas cuando esa identidad se puede reconstruir sin ambigüedad, sin reescribirlas.
- Unifica la aplicabilidad de `visual-browser-review` entre runner, EVID y `validate-project` mediante la selección exacta de TASK. La no aplicabilidad backend se registra fuera de `checks`; un slice visual sigue exigiendo exactamente una revisión ejecutada y `passed`.
- Añade `traceability --task TASK-###` para verificar el alcance exacto de requisitos del slice sin acreditar tareas futuras del mismo incremento.
- Valida la evidencia candidata antes de escribir y vuelve a ejecutar `validate-project` y `traceability verification` sobre el estado materializado. Cualquier rechazo restaura conjuntamente EVID, ART-TRACE, manifest, `verification`, `last_delivery` y la proyección EXEC.
- Añade regresiones E2E multiperfil G3 → G4 → registro → ambos validadores y una regresión que fuerza el rechazo posterior para demostrar el rollback completo.
- No cambia el schema de proyecto, no migra consumidores y no modifica `specs/canonical/`.

## 0.14.1 — 2026-08-28 — registro compatible de evidencia vacía

- Unifica la definición de evidencia de trazabilidad pendiente entre el lector y el registrador: una celda `Evidence` vacía, formada solo por espacios, `none`, `pending` o `not-run` puede enlazarse atómicamente al `EVID-###` exacto después de superar la verificación.
- Conserva el cierre fail-closed: exige `INC-###` exacto, no sobrescribe evidencias existentes, no altera filas de otros incrementos, rechaza tablas malformadas y revierte conjuntamente EVID, ART-TRACE y manifest ante un fallo de escritura.
- Mantiene proyectos schema 1.5 sin migración ni normalización previa; las huellas activas no cambian hasta el registro autorizado de evidencia.
- Añade los campos de perfil compatibles al EVID 1.2 generado por el runner para que el propio validador pueda consumirlo inmediatamente, sin eliminar los bindings y locks exactos del contrato multiperfil.
- Añade regresión completa G3 → plantilla G4 → cierre con Evidence inicialmente vacío y conserva sin cambios los contratos de aplicabilidad visual por TASK, `build_id` determinista, CKPT semántico y PROB/Jira de 0.14.0.
- No modifica `specs/canonical/`, schemas de proyecto ni proyectos consumidores.

## 0.14.0 — 2026-08-27 — verificación incremental, build reproducible y continuidad Jira

- Calcula `visual-browser-review` sobre la selección exacta de `TASK-###`: una porción backend sin interfaz registra una no aplicabilidad determinista, mientras cualquier referencia UX/VIS, capability frontend/browser, unidad de interfaz, slice mixto o verificación conjunta de una release con interfaz mantiene el gate obligatorio.
- Limita los gates de perfiles a los bindings de las tareas seleccionadas y conserva el resto de tareas del incremento fuera de la ejecución incremental.
- Separa `build_id` estable de `verification_run_id`: el build deriva solo de revisión, árbol, locks, perfiles/bindings y digests canónicos; duraciones, timestamps, logs, PID y nombres Docker permanecen en la evidencia de ejecución sin afectar la identidad.
- Añade evidencia de entrega G4 1.1 compatible con lectura 1.0 y el flujo `--materialize-delivery-template`: G3 produce el build y una plantilla `draft`; G4 solo finaliza con revisión, árbol, build, digests y evidencia `passed` coincidentes.
- Valida CKPT mediante frontmatter y tablas semánticas, aceptando YAML equivalente entrecomillado o no, y rechazando rutas no canónicas, enlaces, identidades ambiguas, otra TASK u otra ejecución.
- Normaliza internamente problemas TASK como `problems` con alias compatible `issues`; el `PROB-###` creado al transicionar a `blocked` es consumible inmediatamente por checkpoints y reporting Jira, pero uno resuelto, ajeno o inexistente se rechaza.
- Mantiene Jira como proyección outbound gobernada: preview, lectura/marker, autorización exacta, escritura, relectura y recibo append-only; un fallo remoto no altera el estado canónico local y no se amplían las operaciones permitidas.
- Conserva método/esquema de proyecto 1.5 y compatibilidad 1.0–1.5. No migra proyectos consumidores ni modifica las siete fuentes de `specs/canonical/`.

## 0.13.0 — 2026-08-27 — perfiles OIDC simulados certificados para desarrollo no productivo

- Añade `API-FASTAPI-SIMULATED-OIDC-PG-OCI` y `WEB-REACT-VITE-SIMULATED-OIDC-STATIC` como perfiles `active` exactos para el piloto GPX con identidad OIDC simulada y controlada.
- Implementa discovery, JWKS, tokens RS256, Authorization Code con PKCE S256, sesión de navegador, autenticación/autorización y gates de integración sin depender de un tenant externo.
- Ambos perfiles exigen un entorno no productivo explícito, un issuer dedicado `/__test__/oidc`, IDs sintéticos estables y fallan de forma cerrada en producción o ante configuración ambigua.
- No acreditan interoperabilidad con Microsoft Entra; los perfiles Entra existentes conservan su estado `candidate`, `unsupported` y `external_interoperability: not-run`.
- Regenera locks y certificaciones exactas de los gates completos sobre los bytes definitivos. La release sigue siendo candidate y no promueve M6, `stable` ni política corporativa.

## 0.12.0 — 2026-08-26 — catálogo granular sin combinatoria abierta y perfiles Microsoft Entra

- Añade cuatro capabilities de identidad reutilizables para discovery/JWKS, API bearer, SPA Authorization Code con PKCE y claims de Microsoft Entra, manteniendo el perfil exacto como única unidad seleccionable y certificable.
- Incorpora `API-FASTAPI-ENTRA-PG-OCI` y `WEB-REACT-VITE-ENTRA-STATIC` como profiles candidate con descriptor, scaffold, driver, guide y lock `validated=false`; no crea un perfil de sistema ni sustituye Entra por Keycloak.
- Añade `automation_coverage` como diagnóstico por binding de encaje, preparación, implementación, gates locales, interoperabilidad externa y evidencia de entrega, sin introducir `partially-supported` ni rebajar `automation_support`.
- Implementa discovery OIDC mediante el `jwks_uri` declarado, validación de issuer/audience/tenant/scopes/app roles y 401/403 en la API; la SPA usa MSAL Browser con PKCE y sesión de navegador sin client secrets.
- Mantiene método 1.5.0, schema 1.5, compatibilidad 1.0–1.5, seis perfiles active y sus certificaciones sin cambios. No requiere migración de proyectos consumidores.
- Amplía las seis skills, evals, documentación y validaciones. Interoperabilidad real Entra, revisión humana, gates completos de los candidates y piloto permanecen `not-run`; la release sigue siendo candidate.

## 0.11.0 — 2026-08-26 — reporting Jira por hitos sin perder la experiencia local

- Evoluciona el contrato candidate a método/esquema 1.5 y mantiene compatibles 1.0–1.4; la migración 1.4 → 1.5 es explícita, reversible y no ejecuta escrituras externas ni infiere workflow mappings.
- Mantiene `repository-only` como una experiencia completa sin prompts Atlassian. En `jira-hybrid`, separa `projection-only` de `milestone-reporting` y ofrece coordinación `advisory` o `required-before-execution`.
- Añade hitos de implementación y verificación (`started`, progreso, bloqueo, reanudación, revisión, verificación pendiente/fallida y `done`) derivados únicamente de `TASK/EXEC/CKPT/PROB/EVID` durables.
- Genera comentarios saneados e idempotentes y transiciones opcionales solo mediante status IDs confirmados y transition IDs observados; una confirmación cubre el preview y cada operación conserva un recibo `SYNC-###` independiente.
- Añade pausa/reanudación controlada, estado de reporting separado, resultados `failed/conflict/uncertain` y reconciliación append-only sin reintentos ciegos ni cambios de autoridad.
- Conserva el bundle skills-only y el peer Atlassian Rovo opcional: no incluye MCP, cliente Jira, credenciales, hooks, apps ni agentes ejecutables.
- Optimiza el Quality Gate: el ciclo de desarrollo dispone de una vía rápida focalizada y el candidate puede reutilizar certificaciones exactas y vigentes; Docker completo sigue siendo obligatorio ante deriva, caducidad o ejecución explícita.
- Amplía pruebas, corpus, cobertura, documentación y notas de release. La interoperabilidad real Rovo/Jira, las conversaciones humanas y el piloto permanecen `not-run`; la release sigue siendo candidate.

## 0.10.0 — 2026-08-26 — tracking operativo opcional con Jira y Rovo

- Añade el contrato candidate de tracking operativo 1.4 sin modificar las siete fuentes canónicas vigentes: los Markdown del proyecto consumidor siguen siendo la autoridad semántica y `.lks-sdd/project.json` continúa como índice.
- Pregunta, antes de materializar la planificación de tareas, si el proyecto usará `repository-only` o `jira-hybrid`; no incorpora un modo Jira-only ni convierte una integración externa en fuente de verdad alternativa.
- Incorpora `ART-TRACKING`, registros `TRK-###` y operaciones `SYNC-###` para separar decisión de backend, políticas cerradas, bindings externos, vistas previas, recibos y reconciliación de la planificación canónica.
- Mantiene las seis skills y el manifiesto `skills-only`. Atlassian Rovo es un peer opcional, instalado y autorizado por separado; el bundle no contiene MCP, cliente Jira, credenciales, hooks, apps ni agentes ejecutables.
- Hace fail-closed las escrituras remotas: una vista previa local no acredita ejecución externa, un resultado incierto no permite reintento ciego y `Done` en Jira nunca autoriza, verifica ni cierra una `TASK-###`.
- Conserva compatibilidad de lectura y validación con 1.0–1.3. La migración 1.3 → 1.4 es explícita, reversible y no crea issues, no inventa decisiones humanas y mantiene congelado el contrato histórico 1.2 → 1.3 en plugin 0.9.1/método 1.3.0.
- Amplía corpus, casos de calidad y cobertura contractual para selección de modo, prevención de duplicados mediante correlación/recibos, degradación, privacidad, conflictos y conservación de autoridad. Las conversaciones humanas y la interoperabilidad real Rovo/Jira permanecen `not-run` en esta candidate.
- Actualiza manifiesto, ayuda de distribución, piloto bloqueado y notas de release a 0.10.0 sin publicar, instalar, activar ni promover el plugin a `stable`.

## 0.9.1 — 2026-08-23 — posicionamiento Spec-anchored

- Explicita LKS-SDD como metodología Spec-anchored: la especificación permanece como contrato vivo, versionado y confiable durante definición, planificación, implementación y verificación.
- Diferencia de forma didáctica Spec-first, Spec-anchored y Spec-as-source, sin presentar la generación de código como prueba de conformidad.
- Refuerza la adopción de repositorios existentes como construcción de una baseline documental desde evidencia del `as-is`, separada de la intención y aceptación que requieren confirmación humana.
- Explica el valor para empresas de servicios: documentación contrastable con el cliente y vistas derivadas con procedencia, clasificación y revisión, sin crear otra fuente canónica.
- Actualiza manifiesto, ayuda, onboarding, FAQ, arquitectura, capacidades, metadatos de interfaz y el caso de activación `ACT-019`; mantiene las seis skills, el método 1.3, el esquema 1.3 y los perfiles sin cambios funcionales.
- No requiere migración de proyectos consumidores y conserva la release como candidate; los canales humanos, semánticos y de piloto no ejecutados permanecen `not-run`.

## 0.9.0 — 2026-08-22 — planificación integral y continuidad autónoma

- Añade el contrato de método 1.3 y separa explícitamente readiness de especificación, soporte de automatización, completitud e integridad de planificación, readiness de la porción seleccionada, implementación, verificación y entrega.
- Emite un handoff orientado a acción cuando la especificación está cerrada, sin presentar una tarea `ready` como planificación completa ni usar un `ready` global ambiguo.
- Incorpora `ART-PLANNING` con objetivo, política `complete-before-implementation` o `incremental-authorized`, propiedad primaria de todo el contrato activo, contribuyentes, autorizaciones y cambios `PCH-###`.
- Deriva huecos concretos de requisitos, aceptación, pruebas y obligaciones activas; valida definiciones ejecutables, release, ausencia de propiedad duplicada, DAG acíclico, raíces, fronteras paralelas e integración conjunta.
- Mantiene el camino crítico como `undetermined` cuando no existen duraciones confirmadas y no inventa fechas, esfuerzo, velocidad, capacidad, avance, autoridad ni evidencia.
- Añade autorizaciones `AUTH-###` ligadas a tareas y fingerprints separados de especificación y planificación; persisten entre pausas y se invalidan ante divergencia, cambio de alcance o revocación.
- Añade ejecuciones `EXEC-###` y checkpoints `CKPT-###` versionables con revisión, rama, archivos y hashes observados, entregables, aceptación, gates, evidencia, bloqueos, siguiente acción y trabajo paralelo seguro.
- Endurece dependencias: `cancelled` ya no equivale a `done`. Reabrir una tarea terminada exige un `PCH-###` confirmado por fallo del contrato original; el alcance nuevo crea otra tarea.
- Impide iniciar una tarea 1.3 sin `EXEC-###` activa y marcarla `done` mediante referencias declarativas: revisión, build, artefacto, entorno y gates deben coincidir con una evidencia canónica `verified` enlazada a la ejecución.
- Añade comandos portables `planning` y `continuity`, integra el checkpoint inicial en la preparación autorizada y valida al reanudar si procede continuar, reconciliar o replanificar.
- Añade migración explícita y reversible `1.2 → 1.3`, que crea cobertura y continuidad pendientes sin inventar tareas, completitud, autorización, ejecución, checkpoint, avance o evidencia.
- Conserva el workflow histórico de tareas migradas, pero separa su readiness ejecutable: una tarea 1.2 antes `ready` queda visible como tal y bloqueada para ejecución hasta completar la definición 1.3.
- Actualiza las seis skills, ayudas, plantillas, esquemas, documentación, validadores, pruebas y escenarios, incluido el caso real de `prueba-calculadora` con especificación cerrada, `TASK-001` ready y release todavía parcial.
- Mantiene la release como candidate y los canales humanos, semánticos o de piloto no ejecutados como `not-run`; no instala ni activa el plugin al publicarlo.

## 0.8.0 — 2026-08-21 — gobierno de entrega y arquitectura multiperfil

- Añade el contrato de método 1.2 para definir antes de G2 el modelo de entrega, versionado, Git/ramas, CI/CD, entornos, promoción, despliegue, observabilidad y recuperación, sin imponer una estrategia única.
- Modela `bounded-release`, `continuous-evolution` y `maintenance-stream`, y registra cambios posteriores como transiciones `CHG-###` trazables que no reescriben el historial.
- Incorpora planificación por horizontes `PLAN-###`, releases `REL-###` y tareas `TASK-###`, con tablero visual, detalle independiente, dependencias, problemas `PROB-###`, gates y evidencias.
- Añade transiciones de tarea validadas mediante preview, hash de autorización y escritura atómica; completar una tarea exige evidencia, revisión, build, digest y entorno.
- Sustituye el acoplamiento operativo a H0 por un registro multiperfil con familias, capabilities internas, perfiles cerrados, drivers genéricos, bindings por unidad desplegable y locks 2.0.
- Incorpora diez perfiles de referencia: React y Angular estáticos, dos variantes API-only, Next.js SSR, Angular SSR, sistemas web completos React y Angular, worker RabbitMQ y procesador Kafka.
- Declara seis perfiles active y cuatro candidate; solo un active con certificación exacta vigente puede ser `supported`. Un lock identifica la composición, pero no acredita compatibilidad sin gates por capability y gate end-to-end de la composición.
- Añade scaffolds, gates y certificaciones ligadas por hash a descriptor, capabilities, driver, scaffold, composición y motor; cualquier deriva invalida el soporte hasta recertificar.
- Aísla `node_modules` y `.venv` de los gates Docker en volúmenes Linux efímeros con limpieza registrada, evitando que el rendimiento de bind mounts Windows haga fallar de forma intermitente Vitest o mypy; el harness identifica además el check interno que provoca un fallo.
- Generaliza readiness, preparación y verificación a múltiples bindings y tareas, y exige que G3/G4 queden ligados a revisión Git, tree ID/hash, build, digest de artefacto y entorno.
- Añade la migración explícita y reversible `1.1 → 1.2`, que crea gobierno, arquitectura, planes, tareas y bindings pendientes sin inventar decisiones ni evidencias.
- Amplía el harness con FX-22–FX-27 y crea un corpus conversacional 0.8 independiente, todavía `not-run`; el corpus 0.7 queda histórico y no acredita esta línea de producto.
- Actualiza las seis skills, prompts, ayudas, esquemas, plantillas, documentación, metadata, validadores, tests y nota de release; mantiene los canales humanos y de piloto no ejecutados como `not-run`.

## 0.7.0 — 2026-08-20 — contrato documental y handoff fiable

- Unifica el análisis de artefactos, tablas, estados y referencias para que validación, ayuda, trazabilidad y readiness consuman el mismo contrato documental normalizado.
- Endurece las referencias individuales, listas y rangos inclusivos `..`: evita expansiones parciales silenciosas y admite las formas legacy `a` o separadas por espacios solo en compatibilidad, con aviso.
- Separa relaciones activas de elementos históricos y calcula fingerprints distintos para integridad documental e inputs activos de implementación.
- Añade una matriz de aplicabilidad por dominio para datos, identidad, seguridad, privacidad e integraciones sin forzar un único estado agregado.
- Hace fallar de forma explícita la trazabilidad vacía o incompleta, incorpora un preflight de handoff y separa readiness funcional de soporte automatizado sin convertir limitaciones del perfil en defectos de la especificación.
- Añade diagnósticos estructurados, localizados y agrupados por causa raíz, manteniendo una vista textual compatible para los consumidores existentes.
- Añade la migración explícita 1.0 → 1.1 con dry-run y cierre seguro: cualquier entrada de `human_review_required` bloquea siempre la aplicación antes de crear backup o escribir hasta resolver el Markdown 1.0 de origen y repetir el preview. La dimensión agregada `Identity` se traslada sin inferencias a tres aplicabilidades `pending` con motivo; permite completar la migración si no existen otras revisiones, pero bloquea readiness hasta resolverse en 1.1.
- Incorpora fixtures y regresiones del recorrido real de la calculadora para cubrir el handoff `define → validate → help → traceability → readiness → prepare → verify-plan` que no representaban los happy paths anteriores.
- Cierra la puerta de verificación sobre el registro real de implementación: el plan anticipatorio solo admite el mismo incremento en `in-progress` o `completed`, y la ejecución o el registro de evidencia exigen `implementation.status=completed` y un perfil coherente antes de invocar checks o escribir archivos.
- Endurece la atestación y el empaquetado candidate: el harness captura antes de ejecutar checks la concordancia exacta entre `HEAD`, índice y bytes reales, y rechaza cualquier archivo no versionado preexistente, incluso ignorado; el builder revalida el esquema, hashes comprometidos, inventarios, evidencias, métricas y comparación del reporte antes de leer los bytes del commit e incluirlo en `SHA256SUMS`.
- Mantiene la release como candidate: los canales sin evidencia continúan `not-run`; el harness aún no importa resultados de `definition-conversation`, por lo que `stable` permanece bloqueado aunque se aporten observaciones de activación y revisión documental.

## 0.6.1 — 2026-08-20 — clasificación para desarrollo

- Reclasifica el plugin y su entrada de marketplace de `Productivity` a `Developer Tools`, de acuerdo con su finalidad de definición, implementación y verificación de software.
- Mantiene sin cambios el método, el esquema, las seis skills, los gates, los perfiles bloqueados y los contratos de proyectos consumidores.
- Conserva el estado de release candidate y no presenta como ejecutados los canales semánticos, humanos o de piloto pendientes.

## 0.6.0 — 2026-08-20 — definición guiada y diseño visual

- Refuerza el encuadre inicial para que una idea breve no se convierta silenciosamente en un producto genérico: mantiene tandas pequeñas de preguntas de alto impacto, opciones neutrales y supuestos explícitos.
- Añade snapshots compactos de cobertura al cerrar bloques relevantes, diferenciando información suficiente, parcial, desconocida, no aplicable y bloqueada sin porcentajes de madurez.
- Amplía el anexo condicional de UX con inventario, detalle y estados por pantalla, flujos enlazados, interacción, dirección visual y trazabilidad hacia requisitos y criterios.
- Define un ciclo de prototipado condicional con ImageGen: `Visual mode` explícito, brief suficiente, de una a tres propuestas PNG/JPG, validación humana estructurada, reutilización trazable, activos versionados, hashes y fallback explícito.
- Endurece gates contra rebajas de versión aisladas, PNG/JPEG ficticios, contratos de pantalla incompletos y evidencia visual no ligada a la implementación, UX, baseline, viewport y capturas exactos.
- Corrige FX-01 para que la entrevista adaptativa no se presente como evidencia automatizada y añade los escenarios FX-20 y FX-21 como evaluación semántica/humana todavía `not-run`.
- Mantiene Codex como único runtime soportado, ChatGPT Work como apoyo auxiliar y las seis skills existentes sin MCP, conectores, hooks, apps ni agentes añadidos.
- Actualiza el contrato, la documentación, el empaquetado y la infraestructura de piloto a la candidate 0.6.0 sin ejecutar M6, el piloto real ni la promoción a `stable`.

## 0.5.0 — 2026-08-20 — infraestructura de piloto M5

- Añade un marketplace de desarrollo empaquetado con la estructura local estándar de Codex.
- Genera bundles reproducibles del plugin y marketplace, manifiesto por archivo y `SHA256SUMS`, bloqueando enlaces y patrones de secretos.
- Añade configuración, observaciones cerradas, almacenamiento externo, agregación anónima y decisión go/no-go para un piloto de 3–5 proyectos y 5–8 participantes.
- Establece GitHub Issues como soporte no sensible y separa el canal confidencial de seguridad.
- Documenta onboarding, privacidad, retención, distribución y rollback sin modificar automáticamente proyectos consumidores.
- Mantiene el piloto real como pendiente: la plantilla preparada no permite arrancar hasta asignar muestra, aliases, responsables, seguridad y checksum.

## 0.4.0 — 2026-08-19 — calidad de producto M4

- Integra el catálogo completo FX-01–FX-19 y un corpus etiquetado de activación específico para Codex.
- Añade inventario cerrado y hashes SHA-256 para fixtures exclusivamente sintéticos.
- Añade un runner reproducible con canales `candidate` y `stable`, umbrales calculables y fallos críticos destacados.
- Compara métricas comunes con la baseline versionada `v0.3.0` sin ocultar datos no comparables.
- Incorpora contratos para observaciones saneadas y revisiones documentales humanas, manteniendo `not-run` cuando no existe evidencia.

## 0.3.0 — 2026-08-19 — release M0–M3

- Implementa la sexta skill, `lks-sdd-adopt-existing`, con inspección estática, informe externo, reconciliación, detección de deriva y materialización aditiva autorizada.
- Añade ocho artefactos canónicos `as-is` y conserva separados hechos, observaciones, inferencias, intención, contradicciones y desconocidos.
- Añade validación integral, comprobación de trazabilidad y migración `0.9` → `1.0` con preview, backup externo y rollback protegido.
- Añade borradores derivados para cliente con selección por estado/clasificación, procedencia, bloqueo sensible, colisiones y aprobación pendiente.
- Completa la integración opcional de PostgreSQL y Keycloak desde la skill de verificación.
- Endurece previews y escrituras transaccionales frente a deriva, colisiones, symlinks, junctions, backups corruptos y evidencias inconsistentes.
- Publica el primer hito versionado del repositorio como `v0.3.0`, candidato para revisión y piloto con Codex, sin convertirlo en política corporativa aprobada.

## 0.2.0 — 2026-08-19 — desarrollo local, no publicado

- Añade el perfil H0 `WEB-FASTAPI-REACT-KEYCLOAK-PG`, locks exactos y scaffold reproducible.
- Valida backend, frontend, PostgreSQL y Keycloak dentro de sus runtimes bloqueados y mediante comprobaciones HTTP integradas.
- Implementa preparación segura, dry-run, hash de autorización, protección de colisiones y rollback para incrementos listos.
- Implementa planificación y ejecución de verificaciones sin confundir resultados no ejecutados con éxitos.
- Integra la aptitud del perfil H0 en la puerta de readiness y mantiene la selección tecnológica como decisión humana confirmada.

## 0.1.0 — 2026-08-19 — desarrollo local, no publicado

- Crea el manifiesto skills-only y el gobierno inicial.
- Incorpora las tres especificaciones canónicas sin alterar los originales.
- Implementa ayuda, definición y evaluación de readiness.
- Añade esquemas, validadores, inicialización segura de proyectos nuevos y evals reproducibles.
- Mantiene propuestas, decisiones y texto de bloqueos en Markdown; el índice conserva solo referencias operativas.
- Completa anexos condicionales, onboarding, comparación Work–Codex, FAQ, troubleshooting y ayuda contextual en siete partes.
- Endurece la validación del núcleo exacto, tablas, perfil seleccionado y bloqueos por alcance.
- Registra adopción de existentes, implementación y verificación como backlog no disponible.
- Define Codex como entorno objetivo soportado y documenta que Copilot, Claude y otros asistentes no tienen compatibilidad verificada.
