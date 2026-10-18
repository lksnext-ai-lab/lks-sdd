# Aplicabilidad y continuidad documental

El contexto conserva el cierre literal de petición/propuesta/tarea, reglas globales,
contratos compartidos y dependencias transitivas y entrantes. No hace
falta PLAN para acreditar pertenencia por las relaciones de una propuesta. Una
discrepancia entre relaciones y petición declarada conserva el contenido y se diagnostica.
Las decisiones sobre el alcance requieren aclararla; las consultas y la continuidad
informan del pendiente y conservan los hechos necesarios.
La referencia completa se obtiene con `context` y `reference: true`.
`comparison: true` añade diferencias de pertenencia y caracteres frente a esa
referencia, y comprueba identidad literal en las fuentes comunes. No acredita por
sí sola equivalencia semántica. `excluded_units`, `excluded_prose` y
`scope_diagnostics` explican exclusiones e incertidumbres.

En autoría, `proposal_units` se hereda de los planes concordantes o de la petición.
Planes con porciones distintas requieren declarar la porción explícita compatible;
el orden de los elementos nunca decide el alcance. Los contratos entrantes y las
dependencias tipadas forman parte de la vigencia de una aprobación. Las tareas o
planes posteriores no conceden autoridad ni obligan por sí solos a reaprobar la propuesta.

En el cálculo de vigencia, el inventario `interfaces` de una propuesta (o feature
heredada) expresa pertenencia: no se recorre al revés para incluir de nuevo toda la
propuesta y sus tecnologías en la autorización de cada plan/tarea. La propuesta se
comprueba por separado sobre su contenido exacto. Se conservan los contratos de
interfaz, las reglas globales y las dependencias explícitas entrantes o tipadas,
incluso cuando coinciden con un enlace de pertenencia. El contexto literal no se
recorta por esta distinción y ningún cambio renueva una decisión anterior.

Los Markdown sin bloques o con prosa fuera de ellos conservan su texto íntegro cuando
no existe alcance acreditado. Esa prosa puede contener condiciones globales aunque
en el archivo solo haya una propuesta. La carpeta, edad y ausencia de cambios no
acreditan independencia. Los adjuntos se siguen después de seleccionar fuentes:
logs, código y HTML fuente son texto; los recursos visuales necesitan observación.

## Reconciliar prosa existente por lotes

1. Consultar `catalog` con `kind: prose`, offset y limit para localizar fuentes y
   hashes del texto. La página no contiene sus cuerpos ni escribe decisiones.
   Para trabajar en una porción, `kind: scope` con `roots` devuelve pertenencias y
   una página literal (20 fuentes por defecto, máximo 100). Un lote opcional
   `proposals` con las mismas filas del formato siguiente produce `proposed_project`,
   listo para la revisión de gobierno existente. No modifica archivos ni acredita
   la clasificación. Se conserva la revisión actual y se incrementa la propuesta.
2. Leer el contenido literal de las fuentes necesarias y sus adjuntos. Usar inspección
   acotada o exportación de la vista cuando el corpus sea grande. Preparar propuestas
   de alcance con fundamento; preguntar únicamente las dudas concretas que persistan.
3. Proponer `project.data.context_scopes` en el Markdown canónico del proyecto:

```json
{
  "version": "lks-sdd-prose-scope/1",
  "sources": [
    {
      "path": "docs/lks-sdd/documento.md",
      "sha256": "<hash de prosa devuelto por catalog>",
      "units": ["<UUID de petición, propuesta, tarea o plan>"],
      "global": false,
      "reason": "Fundamento concreto de pertenencia e independencia"
    }
  ]
}
```

4. Revisar el lote como cambio de gobierno, incluyendo fuentes literales, contenido,
   alcance y motivo. Usar `governance` con autoridad competente, recibo vigente y
   autorización de aplicación. No basta escribir una etiqueta ni marcarla confirmed.
5. Consultar otra vez contexto y catálogo; verificar obligaciones y continuación.

`sha256` identifica exactamente la prosa parseada, no el hash del archivo completo.
No se calcula sobre un resumen. Una fuente mixta con reglas globales usa `global: true`
y permanece incluida. Se pueden declarar varias unidades para un contrato compartido.
Fuentes sin declaración, texto cambiado o declaraciones sin decisión vigente permanecen
incluidos. No se crea una excepción implícita ni se reaproban funcionalidades históricas.
Las nuevas decisiones conservan también las huellas de los adjuntos de cada fuente.
Cambiar un adjunto directo o transitivo invalida la exclusión aunque la prosa no
cambie. Una declaración antigua con adjuntos sin ese manifiesto se trata de forma
conservadora hasta su revisión; la prosa sin adjuntos mantiene su compatibilidad.
La declaración conserva la referencia a la decisión competente; el índice sigue derivado.
Su acreditación exige una revisión `governance` de presentación `/2`, con fuente,
ámbito y motivo visibles. Una decisión 3.2 u otro cambio de configuración no activa
por sí solo esta extensión nueva.

Este formato cabe en schema 3.1 / método 3.1.0. El runtime 3.2 conserva su comportamiento
conservador y no aprovecha estas declaraciones. Adoptar la nueva selección exige actualizar
explícitamente el runtime fijado mediante [V3-MIGRATION.md](V3-MIGRATION.md). El corte
conserva documentos, historia, permisos y recuperación. No se exige migrar masivamente el
corpus para obtener mejoras de transporte y cálculo; la reconciliación inicial tiene
coste y solo se amplía cuando el ahorro posterior la justifica.

## Continuidad y transporte

Use `--compact` con `review` y `decision-view` para transportar una sola copia del
cuerpo literal y su recibo. `--json` conserva el formato detallado anterior salvo que
se combine con `--compact`. `--details` o `--output` recuperan fuentes y secciones
completas. La exportación no sustituye por sí sola la lectura para decidir.
`--compact --output` mantiene el archivo completo y compacta la salida de consola.

Los checkpoints simples anteriores pueden recuperarse con `trace`/`history`; el
último del ámbito, pendientes, problemas, decisiones y evidencias siguen disponibles.
Solo se omiten avances expresamente informativos, sin reservas, análisis, carácter
crítico ni resultado negativo; los registros inciertos permanecen incluidos.
Una clave `operation_id` distingue el reintento de un hecho ya registrado de una
observación nueva. No se borra historia ni se deduplican actores o hechos por su texto.

Dentro de una consulta pública se reutiliza el modelo validado. Cada nueva operación
recarga fuentes; las mutaciones y la aplicación conservan guards frescos y la detección
de concurrencia. Esto reduce cálculo, sin presumir retención del contexto de la IA.
