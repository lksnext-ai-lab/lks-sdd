# Migración y continuación en v3.1

El destino operativo del desarrollo pendiente de publicación es schema 3.1 y
método 3.1.0. Instalar el plugin personal no cambia un consumidor ni su runtime
fijado. Consultar no migra. El CLI actualizado exige contrato 3.1, colaboración
confirmada y runtime compatible antes de escrituras ordinarias; las instrucciones
de las seis skills comprueban también estas condiciones antes de código de aplicación.

Se admite conversión directa de schema 2.0, métodos 2.0.0/2.1.0, y adopción desde
3.0, con o sin lock. Un proyecto 3.1 puede preparar la actualización del runtime
por la misma entrada. Un origen desconocido, inválido o con transacción pendiente
no se convierte: diagnostique y recupere primero con el formato del diario original.
El formato 1.5 conserva lectores y recuperadores; no tiene conversión directa a 3.1.
Las bibliotecas de compatibilidad de los plugins 3.0.0/3.1.0 podían crear schema
2.0. Sin lock verificable se conserva esa procedencia como `declared-in-index`,
incluido su índice original exacto; no se acredita como runtime verificado ni se
presume compatibilidad de versiones futuras. El destino exige el runtime comprobado.

1. En la rama acordada, consulte `migration-diagnose`. Devuelve formato, runtime,
   impedimentos y continuidad sin escribir; `include_inventory: true` permite
   solicitar el inventario completo cuando sea necesario.
2. Prepare `migration-preview` con `runtime_bundle` compatible y declaración
   concreta. Para v2: `actor_name`, `profile`, `controls`, `statement`, `target`,
   `collaboration` y, si procede, `members: [{key,name,roles}]`. La colaboración
   resuelve `$owner` y esas claves a UUID nuevos; no selecciona personas ni controles.
   Para 3.0/3.1: `actor` vigente, `collaboration`, `statement` y `runtime_bundle`.
   Se conserva la identidad de los miembros actuales y se vinculan las peticiones
   activas a la configuración confirmada. No se rebautizan autores históricos.
3. Para volumen, declare `packet_directory`, un directorio nuevo fuera del consumidor.
   Revise el descriptor `packet.json`, sus fuentes/efectos y los objetos referidos.
   También `--output` guarda un paquete completo con objetos adyacentes. Transporte
   juntos descriptor y objetos; no dependen del temporal del validador.
4. Autorice el hash exacto del paquete y aplíquelo. Antes de escribir se valida el
   destino 3.1 completo, incluidos runtime y adaptadores. El diario conserva bytes
   anteriores y posteriores y permite `recover` o `rollback`; no promete atomicidad
   simultánea de varios archivos. Un diario pendiente bloquea operaciones normales.
5. Compruebe `validate`, `runtime-doctor` y `migration-continuation`. Reevalúe la
   tarea seleccionada: conversión técnica, autorización de ejecución y aceptación
   humana son resultados distintos. Conserve planes y decisiones equivalentes;
   reconcilie solo la porción abierta y lo nuevo necesario para trabajar.

El recibo v2 → 3.1 conserva el mapa de identidades, procedencia y correspondencias
de contenido. Los bytes originales activos y los recursos se respaldan mediante
un estado independiente por contenido; `legacy.original` continúa siendo una
ruta histórica resoluble. El catálogo técnico de fuentes es un objeto verificado,
con sus hashes y disposiciones completas. La historia física antigua se inventaría,
protege y conserva en su lugar: no se copia otra vez ni se elimina durante el corte.
Las conversiones 2.0 → 3.0 ya existentes siguen siendo legibles con sus árboles.

La lectura de gran volumen utiliza los parsers y verificaciones globales v2:
solo externaliza los mapas conocidos de ejecución/checkpoint antes del límite
normalizado de 32 MiB. No recorta cuerpos, relaciones, reglas, evidencia o decisiones.
Un contrato cuyo contenido irreducible aún excede ese límite permanece bloqueado.
Los presupuestos del migrador son 256 MiB de Markdown original, 100.000 fuentes
documentales y 2 GiB de fuentes/payload únicos; objeto 64 MiB, manifiesto 32 MiB,
descriptor 64 MiB. Se mantienen 16 MiB/50.000 entradas por inventario, 32 MiB de
inventarios únicos por carga y 20.000 miembros por sujeto v3. Fragmentar no dispensa
estos límites ni las comprobaciones de identidades y enlaces entre documentos.

Una confirmación de contenido v2 solo se reutiliza si coinciden la unidad convertida,
su cierre de dependencias y los originales verificables. Las autorizaciones y
actuaciones históricas se conservan como hechos; no conceden permiso actual.
`old-branch` permite comparar un checkout v2 pendiente con el mapa compartido.
Un clon desconectado o runtime antiguo puede seguir actuando fuera de estas entradas;
no existe un bloqueo distribuido. No degrade el runtime tras generar referencias nuevas.

La limpieza del historial existente requiere otro encargo: inventario de todas las
referencias y diarios, respaldo independiente, reconstrucción comparada y restauración
probada antes de autorizar retirada de copias. Este desarrollo no ejecuta esa limpieza.
Publicación y actualización se describen en [almacenamiento](DOCUMENT-STORAGE.md).
