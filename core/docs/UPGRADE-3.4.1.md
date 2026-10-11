# Actualizar a 3.4.1 y recuperar la versión anterior

La versión estable **3.4.1**, commit/integración y publicación están autorizados
expresamente. Antes de actualizar, compruebe gate, manifiestos y disponibilidad de
assets del commit final. La aprobación no acredita una instalación activa.
La corrección y sus pruebas están en [CODE-INVENTORY](CODE-INVENTORY.md).

## Alcance y compatibilidad

El inventario automático comparte la política existente con el lector del contrato.
Omite nombres prohibidos antes de seleccionar o leer sus archivos, también en rutas
anidadas. Las entradas explícitas prohibidas siguen rechazándose. Conserva los
cambios y eliminaciones de archivos permitidos y los guards de integridad y recursos.

El parche mantiene schema 3.1, método 3.1.0 y todos los formatos técnicos de 3.4.0.
Actualizar un plugin del host deja intacto el runtime fijado del consumidor; ese
runtime solo recibirá la corrección mediante su actualización expresamente autorizada.
Este encargo no inicia ese proceso ni transforma documentos.

## Distribución y recuperación previstas

Tras aprobar la versión y superar el gate sobre el commit final limpio, verificar
que el manifiesto, checksums y ZIPs pertenecen al mismo SHA. Los paquetes finales
previstos son `lks-sdd-plugin-v3.4.1.zip`, `lks-sdd-marketplace-v3.4.1.zip` y
`lks-sdd-copilot-plugin-v3.4.1.zip`, junto con la alternativa de setup.

Las referencias estables son `v3.4.1` para mantenimiento y `copilot-v3.4.1` para
el árbol nativo verificado; son commits distintos. Compruebe su procedencia remota
y que el árbol nativo coincide con el ZIP aprobado. La candidata local anterior
`3.4.1-rc.1` no se publicó ni se etiquetó.

Si se autoriza posteriormente una instalación, conservar el paquete, registro y
ubicación anteriores, instalar desde los assets verificados en el área de extensiones
establecida y comprobar versión/comportamiento en una conversación nueva. Para
recuperar, seleccionar la versión anterior conservada y volver a comprobarla.
Instalación, verificación en host y actualización de runtime son actuaciones separadas.
