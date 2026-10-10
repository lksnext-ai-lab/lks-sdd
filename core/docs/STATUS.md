# Estado actual de LKS-SDD

La versión 3.4.0 está en preparación: añade diagnóstico de uso para mejorar el
plugin, con observaciones, hallazgos, reporte/prompt y paquete portable. El destino
operativo es schema 3.1/método 3.1.0 y runtime con formato lks-sdd-usage/1. Los
proyectos existentes conservan su runtime hasta un corte expresamente autorizado.
El avance y sus comprobaciones se conservan en
[el seguimiento](plans/plugin-improvement-feedback/IMPLEMENTATION.md).

La aprobación propia de 3.4.0 y el commit/integración local se autorizaron el
2026-10-10. Commit final limpio, gate stable, assets exactos, publicación e
instalación se acreditan por separado. La preparación del código no
se anuncia como release final ni como actualización de un host o consumidor.

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
