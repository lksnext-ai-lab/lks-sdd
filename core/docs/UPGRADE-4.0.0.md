# Actualización a LKS-SDD 4.0.0

La release conserva las seis skills y sus identidades, el formato de proyecto 3.1
y el método 3.1.0. El responsable autoriza su publicación el 2026-10-18 con las
reservas técnicas documentadas. El gate estable y los artefactos acreditan el SHA
publicado; los ensayos anteriores conservan su fuente original.

## Cambios

- Presentación operativa explícita, transporte compatible y diagnóstico íntegro externo.
- Preparación y operaciones compuestas con permisos, guardas frescas y recibos por etapa.
- Contexto por alcance e instrucciones por operación, conservando obligaciones y literales.
- Mantenimiento proporcional y reutilización acotada durante una evaluación inmutable.
- Cierre administrativo con límites separados para rutas Git y código elegible.
- Lectura mixta de objetos sueltos/ZIP, escritura agrupada y compactación física explícita.

## Proyectos creados con v3

Instalar 4.0 no cambia el runtime fijado de ningún proyecto. Diagnosticar contrato,
lock y pendientes; conservar un respaldo y preparar la actualización con el bundle
compatible, actor y configuración confirmados. Revisar y autorizar el preview exacto,
aplicar y comprobar `runtime-doctor` y continuidad. La ruta probada de actualización
parte de 3.4.3/formato 3.1; no certifica todos los orígenes 3.x. Las rutas anteriores
se mantienen según [V3-MIGRATION](V3-MIGRATION.md).

Después del corte, [la compactación](DOCUMENT-STORAGE.md#publicación-consumidores-y-compactación-explícita-en-desarrollo-40)
puede agrupar objetos existentes. `v3 store-preview` fija originales, paquetes, pin,
respaldo y destino de restauración externos. `v3 store-compact` comprueba respaldo
y restauración byte a byte, conservando originales. Solo `v3 store-recover` con
autorización separada de retirada permite eliminar esos duplicados físicos.
No elimina documentos Markdown canónicos, historia lógica, código ni runtimes antiguos.

El alcance por operación admite hasta 50.000 objetos y 64 MiB lógicos; los objetos
de más de 8 MiB permanecen sueltos. Datos desconocidos/corruptos o falta de espacio
bloquean. No hay limpieza automática por edad ni GC. Tras crear ZIP, volver a un
lector antiguo exige restauración compatible; cambiar solo el pin se rechaza.

## Evidencia y reservas

| Resultado sintético | Alcance |
| --- | --- |
| 20.384 a 9.352 archivos internos activos (−54,12 %) | Compactación de 11.038 originales, con todos los objetos lógicos conservados; bytes activos +7,57 %. |
| 407 a 25 archivos internos nuevos (−93,86 %) | F8 funcional final; bytes nuevos +5,89 %, dentro del límite acordado. No es otra campaña comparativa temporal. |
| Conservación de F8 | 100 archivos iniciales inmutables, 338 elementos y seis recibos previos intactos; nueve invocaciones públicas y cierre/integración explícitos. |

Los resultados de desarrollo se ligan a la fuente de sus ensayos; la promoción de
versión/documentación y el SHA estable tienen su validación de release separada.
La comparación histórica S8 no alcanzó el objetivo temporal del 20 % y fue
aproximadamente un 33,48 % más lenta. El responsable acepta ese compromiso; no se
reclasifica como ahorro. AC-40 sigue inconcluso y los costes comparativos AC-52
pertenecen al componente histórico; no se atribuyen al runtime final sin medirlo.

Windows nativo/H2, selección y continuidad real de hosts y percepción humana
prolongada permanecen pendientes. No se acredita ahorro de tokens facturados ni
garantía universal de rendimiento. La evidencia archivada de F8 conserva datos y
runtimes, excluyendo `.git` y bytecode; no es un respaldo de Git completo.

La aprobación del responsable cierra el desarrollo y acepta publicar con estas
reservas. Publicación, instalación personal, actualización de cada consumidor y
aceptación en una conversación nueva siguen siendo hechos separados.
