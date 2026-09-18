# Estado de aceptación de la distribución dual

## Versión 2

La versión 2.0.0 tiene un expediente independiente en
[validación v2](validation/v2-implementation.md). Ninguna aprobación descrita más
abajo se reutiliza como aceptación de v2. Sus recorridos reales por host y con
varios usuarios siguen pendientes de ejecución autorizada.

## Historial 1.1.1

Versión de distribución de este registro histórico: 1.1.1. Corrección compatible autorizada el 2026-09-11
y ajustada en la orquestación de su gate el 2026-09-12.
No se puede presentar el resultado como paridad conversacional certificada hasta
ejecutar pruebas reales en ambas herramientas. Este documento separa esos canales.

## Aceptación comunicada y aprobación estable

La aceptación comunicada para 1.1.0 permanece registrada como hecho histórico en
`quality/release-approval-v1.1.0.json`. Para 1.1.1, el responsable autoriza publicar
la corrección de rutas, condicionada a los gates técnicos del commit exacto, en
`quality/release-approval-v1.1.1.json`. Ninguna de las dos aprobaciones equivale a
una ejecución observada por el agente ni aporta identidades o datos de proyectos.

No se aportan versiones del host/modelo, pasos ni evidencias por escenario. Por ello
la matriz detallada conserva `not-run` donde no hay evidencia individual; no contradice
la aceptación general del responsable. El quality report de la release publicada
acredita separadamente los gates técnicos del commit exacto. Instalar o activar en
cuentas personales continúa siendo una acción separada.

## Cobertura implementada

La ampliación autorizada incorpora el plugin nativo Agent Plugins 1.0 para el panel
de Copilot. Su setup no duplica skills de proyecto; la migración conserva el mismo
contrato y requiere preview. El descubrimiento real y el respeto conversacional al
runtime fijado no cuentan con evidencia detallada por caso. La guía didáctica compartida por ayuda
y README está en `docs/LEARNING-GUIDE.md`; el recorrido en `docs/COPILOT-PILOT.md`.

| Paquetes del plan | Implementación | Evidencia requerida |
|---|---|---|
| P01 | Contrato auxiliar, versión RC y colaboración secuencial | Schema y pruebas de invariantes |
| P02–P04 | Núcleo compartido, seis adaptadores, lock, instalador y retirada | ZIP reproducible, instalación aislada, integridad y recuperación |
| P05–P07 | Relevo offline, flujo conversacional, validación canónica y deriva | Pruebas unitarias/adversariales y recorrido real |
| P08 | Workflows comunes completos; contratos de herramientas/peer por host | CLI y regresiones; navegador/Rovo reales según capacidades |
| P09 | Suites automatizadas y protocolo de aceptación humana | Resultados técnicos separados de pruebas con personas |
| P10 | Builder dual, setup, checksums, CI y documentación | Builds diagnósticos; release limpia todavía pendiente |
| P11 | No implementado; fase posterior conforme al plan | Decisión y contrato de concurrencia distribuida separados |

La matriz F01–F25 de la propuesta se conserva: el núcleo no sustituye ni elimina comandos,
opciones, gates, perfiles, Jira, continuidad, implementación, verificación o vista cliente.
F04 es generación nativa Codex y relevo desde Copilot; no generación nativa Copilot.

## Canales que no pueden acreditarse con fixtures

Los siguientes escenarios detallados siguen **not-run** hasta disponer de evidencia:

- Descubrimiento e invocación natural de las seis skills en Codex y Copilot reales.
- V01/V02: generación integrada nativa Codex sin anuncios/fichas de relevo.
- V05–V12: recorrido conversacional con imágenes reales, selección/corrección humana,
  retorno a Copilot y permanencia en Codex; nuevo chat y otro clon.
- Equipo de al menos tres desarrolladores, ambas herramientas representadas.
- Navegador real, permisos y revisión de la aplicación desde Copilot, no sus prototipos.
- Interoperabilidad Rovo/Jira autorizada en los hosts declarados.
- Activación en cuentas personales realizada por el agente (no solicitada).

Registrar versiones de host/extensión/modelo, permisos, commit/digest de distribución,
proyecto/base, pasos, resultados y evidencia sin datos personales. Conservar los 24
escenarios V del plan y los T aplicables; no resumir pruebas sintéticas como V aprobadas.

## Resultados técnicos de esta implementación

Comprobaciones locales del 2026-09-11, sobre árbol de desarrollo (no atestación de
release limpia). Comandos: `python -X utf8 tests/run_unit_tests.py --suite TIER
--json-out tests/reports/native-TIER.json`, para cada tier:

| Suite | Superadas | Omitidas | Fallidas | Duración |
|---|---:|---:|---:|---:|
| fast | 48 | 0 | 0 | 45,48 s |
| integration | 202 | 1 | 0 | 291,57 s |
| package | 91 | 0 | 0 | 175,53 s |
| profile | 33 | 0 | 0 | 87,42 s |

Total: 374 superadas de 375, ninguna fallida. La prueba omitida es
`test_visual_asset_symlink_is_rejected_when_supported`: Windows no concedió el
privilegio para crear el symlink (WinError 1314). No se presenta como superada.
Los informes locales están en `tests/reports/`, ignorados por Git y excluidos del
paquete; los conteos anteriores son el resumen documental, no un quality report firmado.

Después del ajuste final de documentación de setup y rechazo de skills duplicadas,
se repitieron cuatro casos nativos: layout/bootstrap, migración ida/vuelta,
actualización personal sin cambiar lock y rechazo de ZIP corrupto/skills extra.
Resultado: 4/4, 7,97 s. El runtime completo se instaló desde el setup nativo en un
consumidor temporal; definición y validación funcionaron, y una CLI global distinta
fue rechazada. Ninguna prueba registró el plugin en una cuenta activa.

Tras fijar los bytes del paquete nativo con `.gitattributes`, se ejecutaron además
el round-trip Git con `core.autocrlf=true` y el rechazo de ZIP alterado: 2/2, 4,79 s.
El checkout obtenido por Git pudo preparar el consumidor con integridad válida.
Ese Git temporal no creó commits ni publicó contenido.

También superados: `tests/run_evals.py`, `validate_plugin_contract.py`, validador
de plugin Codex, validadores de las seis skills, estructura de 23 perfiles y manifiesto
de 14 fixtures. Las certificaciones exactas active se contrastan en el contrato;
no se ejecutó una nueva certificación Docker. `git diff --check` sin errores.

El benchmark repetido sin cambiar umbrales pasó: status máximo 465,61 ms
(límite 5.000 ms), transición 3.457,01 ms (límite 8.000 ms, objetivo 3.000 ms).
Esto no elimina el fallo temporal observado en una ejecución previa ni demuestra
el rendimiento de todos los equipos. La transición pasa el límite, no su objetivo.

Los ZIP de evaluación se generan con `build_dual_distribution.py --development`;
sus identidades se consultan en `distribution-manifest.json` y `SHA256SUMS`.
`validate_copilot_package.py` verifica el ZIP nativo sin activar el host. La comparación
de dos builds debe hacerse sobre los mismos bytes de fuente, incluyendo esta documentación.
Un paquete diagnosticable e instalable no equivale a una release estable aceptada.
