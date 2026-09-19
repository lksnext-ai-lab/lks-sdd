# Estado actual de LKS-SDD

La distribución vigente es **2.1.2** con contrato consumidor **2.0** y método
**2.0.0**. La versión del plugin, el método y el schema son identidades distintas.

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
[compatibilidad](COMPATIBILITY.md) y el [protocolo de host](V2-HOST-ACCEPTANCE.md)
para los controles y límites aplicables.
