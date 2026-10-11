# Estado actual de LKS-SDD

La versión 3.4.1 corrige el
inventario automático de código para excluir las entradas prohibidas antes de
leerlas, conservando el rechazo explícito, los guards y los límites. Mantiene
schema 3.1/método 3.1.0 y los formatos técnicos de 3.4.0. Los proyectos existentes
conservan su runtime e instalación. La causa y 29 pruebas distintas superadas
quedan en [la corrección del inventario](CODE-INVENTORY.md).

La aprobación propia de 3.4.1, commit/integración y publicación se recibió el
2026-10-11 y queda en `quality/release-approval-v3.4.1.json`. La decisión anterior
de 3.4.0 no se reutiliza para este parche. Commit final limpio, gate stable, assets
exactos y disponibilidad publicada se acreditan por separado mediante la evidencia
de release. La publicación no actualiza un host ni un consumidor.

## Estado técnico

- La release estable requiere una aprobación propia, validación contractual, las
  pruebas de humo definidas y la regresión de rutas largas de Windows.
- El empaquetado y la promoción acreditan el commit, manifiesto, checksums y assets
  exactos. La publicación final de una draft sigue siendo humana.
- La caché de dependencias de CI es una optimización; no es evidencia de release.

## Límites vigentes

- La aceptación conversacional de Codex y Copilot, el piloto con personas y la
  interoperabilidad externa permanecen `not-run` hasta que exista evidencia real.
- Los roles declarados y los hashes no autentican personas ni firmas de editor.
- La distribución no instala plugins, no migra consumidores ni publica releases por
  sí misma.

## Compatibilidad

Los proyectos 1.5 continúan en su runtime fijado hasta una migración explícita a
2.0. La ruta oficial conserva preview autorizado, recibo de conservación y rollback.
La retirada de soporte 1.5 requerirá una decisión de producto independiente.

Consulte [validación](VALIDATION.md), [releases](RELEASING.md),
[compatibilidad](COMPATIBILITY.md) y el [protocolo de host v3](V3-HOST-ACCEPTANCE.md)
para los controles y límites aplicables.
