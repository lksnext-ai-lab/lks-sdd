# Plan y resultado de LKS-SDD v5

Estado: **candidata local corregida, validada automáticamente y empaquetada; sin publicar ni instalar**.
Fecha: 21 de octubre de 2026. Rama: `codex/lks-sdd-v5`.
Base: `ecc033c775319163c51b11a76637b45a7460efe7` (4.0.3).

## Autoridad y decisiones

La petición de completar v5 autoriza implementación, validación y preparación local.
No autoriza publicación, registro, instalación, commit o push. La petición literal
permanece intacta en `tarea.md`; no se modifica `specs/canonical` ni el checkout principal.
El worktree conserva cambios únicos: integración y retirada no proceden todavía.

Decisiones posteriores de Joseba incorporadas:

- Migración definitiva, sin rollback ni backups por precaución. Una interrupción se
  reanuda hacia v5. Se conserva conocimiento útil y se retira control sustituido;
  el historial Git queda intacto.
- El criterio es el valor y volumen del conjunto documental. Un documento útil
  grande no es un fallo. Se elimina crecimiento administrativo redundante; una
  medición de contexto aislada no acredita ni refuta ese objetivo.
- Un único informe tras la conversión muestra archivos, bytes, cambios y pendientes.
  Vive en `docs/informe-conversion-sdd-v5.md`, fuera del árbol canónico de tres tipos.
  Es una fotografía de la migración, no un expediente por archivo ni un nuevo diario.

## Resultado de la revisión crítica

| Hallazgo | Corrección y evidencia automatizada |
|---|---|
| Criterios/políticas heredados no operativos | Se normalizan criterios explícitos y controles conocidos; las definiciones incompletas quedan visibles sin crear backlog de migración; la cobertura se exige al cerrar trabajo vigente. Continuación y cierre de una tarea migrada comprobados. |
| Pérdida de una edición concurrente | Precondiciones inmediatamente antes de sustituir cada archivo y nueva comprobación del conjunto convertido antes de retirar el origen y emitir el informe. Conflicto conserva la edición ajena. |
| CI antiguo rejuvenecido al importar | Fecha original de ejecución; importar no renueva vigencia. Sin fecha comprobable no se satisface una política de caducidad. Reimportar no hace crecer el plan. |
| Subtareas desactivaban cobertura del padre | Cobertura explícita propia o enlaces a criterios de hijos cerrados con pruebas vigentes; no se duplican resultados. |
| Close eludía controles de entrega | Misma validación de autoridad y política que delivery; not-run puede registrarse honestamente sin permiso de despliegue. |
| Subdividir revocaba autoridad | La organización interna conserva autoridad del padre; el hijo no adquiere una autorización inventada. |
| Metadatos administrativos invalidaban tests | Huella técnica separada de procedencia de autoridad y organización; contrato, código, configuración y entradas pertinentes siguen invalidando. |
| Contexto mayor por contenido ajeno | Reclasificado como observación secundaria; no demostraba crecimiento administrativo global. Se comprueba volumen total con 0/10/100 registros históricos y ciclos repetidos. |

El lock coordina este runtime y las comprobaciones son optimistas. No se presenta
como exclusión absoluta de editores externos o coordinación distribuida.

## Implementación y escenarios

Núcleo autónomo estándar Python, Markdown canónico, capacidades funcionales y tarea
con un único plan evolutivo. Seis skills completas para Codex y Copilot; 22 archivos
en el núcleo distribuido y ningún motor anterior ejecutable. La conversión lee
1.5, 2.0, 3.0 y 3.1 directamente. No hay escritura dual ni migración silenciosa.

| Escenario solicitado | Evidencia y límite |
|---|---|
| Corrección pequeña | Definición, autorización, prueba, reutilización y cierre; solo tarea y plan. CLI con JSON por stdin y documentos inline. |
| Lotes de cambios | Dos ciclos guionizados de seis ajustes; prueba conjunta y reutilización. No equivale a reproducir la entrega UX original ni medir trabajo total del agente. |
| Cambio complejo | Subtareas con criterios delegados y cobertura completa del padre; evidencia compartida por referencia. |
| Contratos/permisos compartidos | Dependencias e invalidación por cambio de contrato aplicable. |
| Dos personas | Conflictos, conciliación y preservación de edición durante la escritura. |
| Interrupción/cambio de chat | Estado y siguiente paso en el plan; reanudación sin repetir pruebas vigentes. |
| CI/VPN/credenciales ausentes | Espera acotada y bloqueo localizado en simulaciones; no se afirma una caída real de servicios. |
| Pruebas vigentes | Reutilización tras cambios administrativos; caducidad original y cambios pertinentes invalidan. |
| Entrega/despliegue | Seis hechos separados, autoridad y controles compartidos. No se despliega ninguna aplicación. |
| Migración con histórico | Caso SAT en copia del snapshot exacto; ver resultado integral final. |
| Migración interrumpida o contradictoria | Reanudación definitiva, conflictos preservados, sin rollback ni copias antiguas. |
| Cierre y limpieza | Solo temporales propios; contenido ajeno conservado. Informe único tras éxito, sin duplicación al reanudar. |

También se comprueban fuentes nativas 1.5/2.0/3.0/3.1, objetos loose/ZIP y corrupción,
rutas inseguras y largas Windows, integridad de runtime/adapters y CLI de ambos hosts.
Los ZIP leídos como fuente antigua no son backups creados por la migración v5.

## Auditoría de carga administrativa y validación actual

La calificación anterior de «57 tareas con pendientes heredados» era incorrecta.
El contraste con los blobs del snapshot SAT
`e55f87a122aa6e3595d8a26d2bb729dd867cad26` identifica:

- **45** registros bloqueados exclusivamente por el conversor: exigía configurar
  checks, Sonar y criterios incluso para borradores, solicitudes y propuestas.
- **12** tareas con indicadores antiguos del método. No equivalen a 12 defectos:
  nueve tenían estados ready, in-review o backlog; TASK-014 y TASK-015 declaraban
  implementación al 100 % pero pedían autorización/checkpoints/observers del método
  anterior. TASK-012 ya declaraba estado blocked y se conserva como tal, sin afirmar
  que sea un defecto funcional actual comprobado.
- Sonar tenía alcance por rutas; la migración lo había extendido indiscriminadamente.
  Se conserva obligatorio para las rutas originales (backend/app, backend/alembic y
  frontend/src, unión conservadora de las políticas de origen). Un alcance desconocido
  no exime del control; documentación ajena a esas rutas no exige Sonar.

Correcciones aplicadas: no hay bloqueos por configuración ausente ni reapertura de
trabajos terminados. Los comentarios históricos no ordenan reconstruir controles
retirados. Solicitudes, propuestas, cambios y entregas conservan su contenido sin
convertirse automáticamente en nuevas tareas. Los controles se preparan al retomar
el alcance y siguen siendo exigibles al cierre. Las skills de adopción y preparación
explican esta distinción; el informe de conversión ya no llama pendientes reales a
los indicadores administrativos.

La auditoría administrativa previa usó blobs Git de solo lectura y obtuvo:
**76 pares tarea/plan** (71 tareas del origen y 5 planes compartidos), frente a 100.
Se eliminan **24 tareas artificiales**, conservando el contenido útil. Estados:
43 cerradas, 22 definidas, 8 en curso, 2 preparadas y 1 bloqueada (TASK-012).
**166 documentos canónicos**, frente a 214; 3.420.458 bytes frente a 3.418.455.
El aumento de 2.003 bytes conserva criterios que antes se normalizaban en tareas
artificiales; no representa crecimiento de controles. Los 12 criterios literales UX
permanecen intactos y las 166 relaciones/documentos pasan validate.
Evidencia: `tests/reports/v5-full/admin-source-audit.json`,
`admin-projection-results.json` y `admin-projection/`.

## Última revisión crítica

Se corrigen seis fuentes adicionales de trabajo administrativo:

| Fricción | Resultado y comprobación |
|---|---|
| Repetir controles comunes en el padre | Delegación completa por criterion_links reutiliza pruebas actuales de hijos cerrados. Cobertura parcial o entradas cambiadas se rechazan. |
| Reautorizar un cambio de responsable | Se conserva la autoridad del mismo alcance y se reutilizan las pruebas. Una ampliación de alcance sigue invalidándola. |
| Logs acumulados por reintentos | Un log por comprobación, sustituido en fallo y retirado tras éxito; una edición ajena se conserva como conflicto. |
| Rellenar otra vez seis hechos de entrega | Close conserva los hechos registrados, recibe solo cambios y deja unknown para lo no observado. No declara éxitos por defecto. |
| Formularios y llamadas sin necesidad | Init admite política explícita vacía; prepare acepta rutas de alcance. Las seis skills evitan doctor duplicado y reconstrucción de controles retirados. |
| Solicitudes sin propietario dentro de la política | Su contenido queda en antecedentes.md, fuera del contexto automático y de la política transversal. |

**85 pruebas automáticas superadas, cero skips**, en una ejecución de 186,265 s
(`review-unit-results.json`; duración del runner, no benchmark). Las 23 de humo y la
regresión de rutas largas Windows forman parte de esa ejecución. Un último ajuste
de texto de adapters se verifica adicionalmente en `review-final-adapters.json`.
Integridad estática superada; `review-technical-gate.json` recoge las comprobaciones
y sus límites, sin simular la aprobación de release estable.

Migración integral de la candidata actual: **superada**, sobre la copia nueva
`tests/reports/v5-full/sat-release-review`, snapshot exacto
`e55f87a122aa6e3595d8a26d2bb729dd867cad26`. Evidencia en
`review-real-results.json` e informe generado
`sat-release-review/docs/informe-conversion-sdd-v5.md`.

- Documentación activa: **1.403 → 167 archivos**, **18.442.542 → 3.420.678 bytes**.
- Alcance completo SDD/apoyo/runtime: **9.563 → 282 archivos**, **1.413.145.657 →
  13.877.700 bytes**, más el único informe de conversión fuera de la medida.
- Se conservan 76 pares tarea/plan, 43 cerrados y un bloqueo explícito del origen;
  los 12 criterios literales UX y sus 55 aceptaciones enlazadas siguen íntegros.
- Runtime `5.0.0-86831400f61b`, idéntico al empaquetado. Doctor, 167 documentos y
  validador CI convertido: passed. Cero backups, staging y journal de migración;
  runtime anterior y árbol documental sustituido retirados.

Preparación: 141,860 s; aplicación: 155,288 s. El ensayo comprueba la conversión
completa, no la regresión funcional de SAT ni aceptación humana. El consumidor
activo permanece sin cambios. Los ensayos anteriores se conservan como antecedentes.

**Conclusión técnica:** no quedan hallazgos bloqueantes identificados en los
recorridos revisados; la candidata queda preparada localmente para el paso de release.
La autorización de publicación y la fuente comprometida limpia siguen separadas,
y los canales conversacionales/humanos no ejecutados mantienen ese estado explícito.

## Paquetes y límites de entrega

Paquetes reproducibles en `dist/v5-prepared`, con `PREPARATION.json`, manifest y
SHA256SUMS. Huella del núcleo:
`sha256:86831400f61b1b04245e9306a004bbb68a1817a96bed7bda9cc9d80a22b24383`.
Cuatro bundles: plugin, marketplace Codex, plugin nativo Copilot y payload de proyecto.
`extensions.ps1 build` produce además el ZIP de soporte local, sin registro ni instalación.
Los cuatro bundles reproducen byte a byte y el validador nativo Copilot pasa.

Publicación, instalación, aceptación conversacional Codex/Copilot, piloto humano,
regresión y despliegue de SAT: **not-run**. La release estable mantiene su aprobación
explícita y fuente limpia vinculada a commit; no se han autorizado esos pasos.
No se afirma ahorro total del agente ni de tokens a partir de bytes o latencias.
`billed_tokens: null`; métricas de tiempo administrativo total y máquina fría no observadas.

La revisión automática de ejecución rechazó por política el borrado de las copias
de ensayo anteriores `tests/reports/v5-full/sat-copy` y `sat-final`. Se conservan;
no se ha eludido el rechazo. Son restos locales de ensayos previos, no backups
creados por el motor definitivo ni consumidores activos.

## Autorización de release 5.0.0

El 2026-10-21 el responsable autoriza explícitamente commit, push y publicación de
la release v5.0.0. La autorización se registra en
`quality/release-approval-v5.0.0.json`, condicionada al gate estable sobre el commit
final integrado. Los resultados anteriores describen la candidata local evaluada;
los cambios editoriales de release generan una nueva huella de distribución.
La publicación se acredita con el workflow y la release remotos, no con este texto.
Instalación, aceptación conversacional y migración de consumidores activos siguen
fuera de este paso.

La preparación de publicación detecta y corrige la conversión CRLF del checkout Git
nativo Copilot: `.gitattributes` conserva los bytes y el validador exige esa regla.
La prueba de distribución incluye una clonación real con `core.autocrlf=true`;
el preflight estable se vuelve a ejecutar sobre el commit corregido.
