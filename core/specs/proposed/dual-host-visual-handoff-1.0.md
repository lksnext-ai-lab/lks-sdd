# Contrato de implementación dual 1.0 — LKS-SDD 1.1.0-rc.1

Estado: implementación autorizada por el usuario el 2026-09-11; aceptación de host y
publicación pendientes. Esta extensión no modifica ni sustituye `specs/canonical/`.

- Seis workflows comunes, adaptadores Codex desktop y Copilot VS Code Agent. Invocación
  implícita activa; no séptima skill, MCP, conector, hook, app ni agente ejecutable.
- Versiones coordinadas de producto 1.1.0-rc.1; proyecto 1.5/método 1.5.0 sin migración.
- Runtime exacto y hash de inventario por proyecto, sin rutas personales. La presencia
  de una carpeta no identifica al host. La distribución Copilot solo contiene adaptadores;
  los scripts, perfiles, contratos y referencias proceden del mismo núcleo que Codex.
- Instalación offline preview/hash/apply; bloques gestionados, conflictos fail-closed,
  recibo de propiedad y recuperación durable. No descarga, instalación activa, commit,
  push, cambio de política o registro remoto implícitos.
- Relevo auxiliar 1.0 identificado por digest de solicitud e inputs. No AUTH/EXEC ficticios.
  Brief independiente y fuentes canónicas preservadas; resultados aprobados en UX/VIS/ADR.
  Resultado derivado por validación; prototipo no acredita implementación.
- Codex nativo no tiene avisos ni archivos de relevo. Copilot invita una vez si la generación
  es necesaria, sin API de imágenes. El regreso es opcional. Falta de herramienta o cuenta
  deja pendiente el paso; no reduce el contrato ni obliga a contratar un proveedor.
- Colaboración secuencial con un responsable por alcance, transferencia Git explícita e
  integridad al reanudar. La coordinación distribuida P11 no se activa en esta entrega.
- Empaquetado de desarrollo instalable separado de certificación publicable. La RC no
  hereda la aprobación estable 1.0.0. La publicación exige evidencia y autorización nuevas.

Especificaciones operativas: `docs/INSTALLATION.md`, `docs/VISUAL-HANDOFF.md` y
`docs/DUAL-HOST-ACCEPTANCE.md`. `schemas/visual-handoff.schema.json` gobierna el índice
auxiliar; el contenido canónico sigue gobernado por el contrato consumidor existente.
