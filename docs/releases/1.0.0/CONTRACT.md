# Contrato de cierre LKS-SDD 1.0.0

## Decisión confirmada

El responsable del proyecto considera suficiente para la promoción estable el
uso satisfactorio del plugin por diferentes equipos. Su aprobación durable es
la autoridad humana de cierre; no se exige reconstruir conversaciones, guardar
identidades ni completar una muestra cuantitativa de piloto.

## Alcance

- Promover la versión del plugin a 1.0.0 y el canal a `stable`.
- Conservar método 1.5.0, schema 1.5, seis skills e invocación implícita.
- Mantener intactas las fuentes de `specs/canonical/`.
- Añadir un canal `release-approval` ligado por hash a la release.
- Mantener los canales humanos detallados visibles con su estado real.
- Certificar puertas técnicas, reproducibilidad y bundle desde commit limpio.

## Criterios de aceptación

1. El manifest, changelog, documentación, runtime y nota de release coinciden
   en 1.0.0.
2. `stable` exige los cuatro canales técnicos y `release-approval`.
3. La aprobación solo pasa con rol `project-owner`, decisión `approved` y cero
   hallazgos bloqueantes.
4. `not-run`, `incomplete` y `failed` conservan su significado en los canales
   opcionales; nunca se transforman en `passed`.
5. El reporte estable solo es elegible desde fuente limpia y sin regresiones.
6. El builder verifica la aprobación comprometida y su hash antes de empaquetar.
7. Los dos builds y los bundles extraídos deben validarse antes de publicar.

## Fuera de alcance de esta autorización

Commit, push, etiqueta, GitHub Release, registro de marketplace, instalación y
activación. Cada operación requerirá autorización separada.
