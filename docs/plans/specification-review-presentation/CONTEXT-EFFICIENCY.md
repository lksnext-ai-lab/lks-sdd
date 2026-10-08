# Eficiencia del contexto para las decisiones del usuario

Fecha: 2026-10-08. Este documento conserva el análisis previo. La reestructuración
ya está implementada; resultados y límites en [IMPLEMENTATION.md](IMPLEMENTATION.md).
Complementa el [plan](PLAN.md) y el [inventario de eventos](VALIDATION-EVENTS.md).

Conviene abordar esta mejora dentro de la implementación. Las seis skills ya son
breves; el cambio principal debe organizar las instrucciones compartidas y los
nuevos perfiles de presentación para cargar solo los que correspondan. Reducir
lecturas y ambigüedad es el objetivo. La suficiencia del contrato, la autoridad y
la calidad del resultado son condiciones previas a cualquier ahorro.

## Qué se ha comprobado

Se han leído las seis entradas `SKILL.md`, sus referencias v3, las reglas comunes,
el recorrido integral, la referencia de operaciones, el selector de contexto, los
adaptadores de distribución y el control de enlaces del validador. Se ha contrastado
el trabajo local de eficiencia documental para no duplicarlo. Es una inspección
estática del árbol de trabajo; no mide las lecturas efectivas de Codex o Copilot.

| Fuente actual | Tamaño observado | Consecuencia para el diseño |
|---|---|---|
| Seis entradas `SKILL.md` | Entre 21 y 29 líneas; entre 1.143 y 1.742 caracteres por entrada. | Conservar las seis capacidades y su selección implícita. Dividirlas más añade selección sin beneficio acreditado. |
| Referencias `references/v3.md` | Entre 12 y 16 líneas; entre 1.139 y 1.879 caracteres. | Mantener su función de guía por objetivo; mejorar enlaces y condiciones de lectura. No fragmentar cada párrafo. |
| [V3-COMMON.md](../../V3-COMMON.md) | 87 líneas; 6.119 caracteres. | Mezcla invariantes con detalles de migración, controles, ramas y excepciones. Mantener las garantías comunes y trasladar únicamente procedimiento específico. |
| [V31-REVIEW.md](../../V31-REVIEW.md) | 95 líneas; 6.089 caracteres. | Combina el mapa de hitos con campos de configuración, revisión y corrección. Separar orientación general de preparación de una operación concreta. |
| [V3-OPERATIONS.md](../../V3-OPERATIONS.md) | 118 líneas; 8.171 caracteres. | Ya se indica consultar solo los campos necesarios. Conservar esta lectura acotada y dar localizadores claros; no justificar su división solo por longitud. |
| Revisión 2 del plan | Proponía `USER-DECISIONS.md` como referencia completa de todos los perfiles. | Cambiarlo antes de implementarlo: índice y reglas de presentación breves, con detalle por familia. |

Con colaboración integral activa, la ruta documental indicada incluye la entrada
de la skill, su referencia v3, las reglas comunes y el recorrido integral. La suma
estática de esos cuatro archivos, deduplicando rutas, es:

| Recorrido | Caracteres | Palabras separadas por espacio |
|---|---:|---:|
| Consultar | 14.490 | 1.975 |
| Definir | 15.745 | 2.141 |
| Adoptar o migrar | 14.860 | 2.014 |
| Comprobar preparación | 14.767 | 1.993 |
| Implementar | 15.760 | 2.144 |
| Verificar | 15.124 | 2.061 |

Método: texto UTF-8 con saltos normalizados por `Path.read_text`, `len(text)` y
`len(text.split())`. Las medidas incluyen encabezados y metadatos de la entrada.
No incluyen instrucciones del host, datos del proyecto, herramientas ni referencias
condicionales. Tampoco prueban que el host cargue esos archivos enteros, ni representan
tokens facturados. No se suman las seis skills como si se cargasen a la vez.

Los dos recursos comunes aportan 12.208 caracteres a esas rutas. Esto localiza la
oportunidad de organización, pero no demuestra por sí solo qué texto puede omitirse.
La comparación de ahorro deberá incluir la funcionalidad nueva: reducir instrucciones
a costa de una validación menos completa no sería una mejora.

Para recuperar la procedencia de estas cifras, las huellas SHA-256 de los bytes
observados fueron:

| Archivo | SHA-256 |
|---|---|
| V3-COMMON.md | `045cde792e31aa79b10ac19cb6a313a000a6eccb248fef08bbf3617b810387b8` |
| V31-REVIEW.md | `4d483181087c5243f759dfb982ff7aa1915197addcef006eec22f5c97e939ed1` |
| V3-OPERATIONS.md | `469819bf9fd7815a70ba3499be09f0171ab2cb339763ff8e454dfbb769ac1506` |

Las cifras deberán recalcularse al comenzar la implementación, porque existen
cambios concurrentes en estos recursos. No son un límite obligatorio de tamaño.

## Riesgos de interpretación identificados

1. **Guía demasiado amplia para una decisión.** Leer configuración, propuesta,
   ejecución y resultado juntos facilita aplicar una regla válida en otro momento.
   Las instrucciones nuevas aumentarían esa mezcla si se concentrasen en un manual.
2. **Reglas duplicadas o difíciles de localizar.** Los campos de operaciones aparecen
   tanto en la referencia técnica como en el recorrido integral. Varias referencias
   v3 nombran `V31-REVIEW.md` sin enlace directo. Una futura modificación puede dejar
   variantes diferentes o inducir búsquedas innecesarias.
3. **Arrastre de procedimientos históricos.** Algunas guías detalladas de tecnología,
   visuales y cliente pertenecen a recorridos conservados. Su contenido conceptual
   puede ser útil, pero cargar sus comandos y formatos completos en v3 confunde
   disponibilidad con existencia del archivo.
4. **Fragmentación excesiva.** Un archivo por cada evento produciría demasiados
   saltos y podría separar una decisión de sus excepciones o condiciones. El agente
   necesita un conjunto coherente por decisión, incluidas las decisiones agrupadas.
5. **Confundir instrucciones con contrato del proyecto.** Elegir la guía de un evento
   no demuestra que se hayan leído todos los requisitos o adjuntos necesarios. Una
   mejora de presentación no habilita un selector reducido para implementar código.

Son riesgos deducidos de la estructura inspeccionada. No se atribuye una tasa de
errores a los agentes sin observar tareas reales.

## Organización propuesta

Se conservarán los nombres, objetivos e invocación implícita de las seis skills.
El contexto se organizará en cuatro niveles con responsabilidades distintas:

| Nivel | Contenido | Cuándo se lee |
|---|---|---|
| Entrada de la skill | Objetivo, límites y selección del runtime y formato. | Al aplicar esa capacidad. |
| Núcleo compartido | Fuentes, autoridad, vigencia, suficiencia, continuidad y límites de efectos externos; reglas comunes de presentación cuando haya un mensaje de decisión. | En todo recorrido gobernado que lo requiera. Una consulta breve no carga todos los perfiles. |
| Familia de decisión | Información necesaria, formato, efectos, condiciones, excepciones y operaciones relevantes para ese tipo de decisión. | Al preparar o explicar el evento; se añaden las familias de las decisiones agrupadas. |
| Detalle condicionado | Campos concretos, ejemplos, tecnología, visuales, migración o capacidades históricas. | Solo cuando la operación o una condición observada lo exija. |

`docs/USER-DECISIONS.md` será la entrada breve de presentación y el mapa de familias.
El detalle se propone bajo `docs/decision-guides/`, con nueve grupos iniciales:

| Recurso propuesto | Familias cubiertas | Condición de lectura |
|---|---|---|
| `project-setup.md` | EV-02, EV-03, EV-05, EV-06, EV-07, EV-27 | Preparar configuración, adopción o cambios de proceso/runtime. Una simple pregunta de identidad se resuelve con la regla breve. |
| `specifications.md` | EV-08, EV-11 | Presentar especificación funcional/técnica o su cierre. Contiene los siete apartados y el detalle por componente. |
| `planning.md` | EV-12, EV-13 | Presentar plan y límites de ejecución. |
| `assignments.md` | EV-14, EV-15 | Revisar encargo, asignación o relevo. Se añade a planificación solo si se revisan también las tareas. |
| `verification.md` | EV-18, EV-19, EV-20, EV-21 | Preparar comprobación, integración o aceptación; separar los perfiles dentro del mismo recurso. |
| `corrections.md` | EV-10, EV-22, EV-23, EV-24 | Resolver observaciones, rechazo o alcance correctivo. Añadir verificación al presentar nuevas pruebas o aceptación. |
| `exceptions-continuity.md` | EV-17, EV-25, EV-26, EV-28, EV-32 | Excepción, revocación, cambio material de continuidad o recuperación soportada. |
| `conditional-design.md` | EV-01, EV-04, EV-09 | Aclaración compleja, elección tecnológica o dirección visual. La pregunta simple conserva su formato breve. |
| `external-delivery.md` | EV-29, EV-30, EV-31 | Preparación de contenido para cliente o acción externa realmente disponible. |

EV-16 y EV-33 usan la orientación informativa del núcleo. No necesitan cargar una
plantilla de aprobación. Los 18 perfiles del inventario mantienen su identidad;
agruparlos en recursos no mezcla sus contenidos ni sus efectos. Antes de materializar
esta propuesta se comprobará si dos grupos pequeños se leen siempre juntos y
conviene unirlos; no habrá un objetivo artificial de número de archivos.

La selección tendrá un índice directo por familia. Cada entrada indicará evento,
cuándo aplica, archivo y dependencias. Los recursos terminales contendrán su
procedimiento completo y las condiciones que pueden activar otro recurso; no se
creará una cadena indefinida de enlaces. Un vínculo de consulta opcional no será
una instrucción de cargar todos sus destinos.

Ese índice permitirá localizar la guía antes de ejecutar `decision-view`, también
sin proyecto inicializado o ante un estado incompleto. No se requerirá aprobar,
inicializar ni ejecutar una consulta válida para poder leer cómo preparar el evento.

### Qué conservar y qué trasladar

- `V3-COMMON.md` conservará las garantías: Markdown canónico, runtime fijado,
  identidad y autoridad comprobadas, alcance autorizado, decisiones vigentes,
  contenido literal suficiente, conservación de cambios ajenos, veracidad de
  evidencia y límites de efectos externos. Retendrá también los disparadores de
  migración, controles y excepción, aunque su procedimiento detallado esté aparte.
- `V31-REVIEW.md` conservará el mapa H1–H7, la agrupación por persona, las decisiones
  separadas y la continuación autorizada. Sus listados de payloads pasarán a la
  referencia de operaciones; el detalle de presentación irá a las familias.
- `V3-OPERATIONS.md` será la fuente única de campos de comandos. Se añadirán
  secciones o anclas localizables por acción/familia y se indicará leer el bloque
  completo, incluyendo condiciones y excepciones. No se leerá una línea aislada
  que deje fuera una regla relevante. La división en archivos solo se reconsiderará
  si la medición demuestra lecturas completas o búsquedas costosas.
- `references/v3.md` de cada skill contendrá el recorrido propio y enlaces directos
  a las familias aplicables. No copiará plantillas ni todos los campos del CLI.
- Las referencias de otras versiones seguirán aisladas. Para reutilizar un tema
  conceptual se redactará una única guía vigente con sus límites reales y se
  revisarán sus llamadores; no se importarán comandos históricos para ahorrar autoría.

Se mantendrá una matriz de traslado de reglas durante el cambio: fuente anterior,
destino único, condición de lectura y caso que acredita su conservación. Así se
puede revisar que desduplicar no haya eliminado una excepción o una obligación.

## Selección, continuidad y suficiencia

El catálogo finito de perfiles de `v3_decision_presentation.py` incluirá referencias
a los recursos de instrucciones. La misma correspondencia alimentará la salida
de `decision-view` y la comprobación del índice documental, evitando dos mapas
mantenidos de forma independiente. No se añade otro motor de contexto o autoridad.

La consulta podrá devolver `instruction_refs` con familia, motivo, ruta relativa
al runtime fijado y revisión/huella, separadas de las fuentes del proyecto y del
Markdown destinado a la persona. Estas referencias permiten encontrar instrucciones;
no acreditan que el agente las haya leído ni que la presentación sea suficiente.
Los archivos y familias admisibles serán cerrados y propios del paquete. Los textos
del consumidor no podrán introducir una ruta de instrucciones ni una orden ejecutable.

La selección utilizará la acción y su finalidad, los objetos, la política y el estado
observados. Un rol por sí solo no selecciona todo el recorrido. Por ejemplo, `approve`
requiere conocer su finalidad; `start` puede necesitar revisión/recepción; `integrate`
puede incorporar aceptación. Cuando aparezca una condición nueva, se ampliará la
selección antes de seguir. Una combinación desconocida se explica y se aclara;
nunca se resuelve silenciosamente con un perfil genérico que permita aprobar.

La unión de decisiones compatibles carga sus recursos y dependencias una vez por
revisión. La deduplicación de lecturas se limita a contenido efectivamente disponible
en el chat actual y sin cambios; no supone una memoria persistente del host. Tras
chat nuevo, compactación, cambio de runtime o modificación material, se releen las
fuentes necesarias. Un hash, una ruta o una marca de lectura no sustituyen el texto.
No se crean ficheros de sesión, caches de confianza o checkpoints por cada consulta.

Para los datos del proyecto se mantiene el mecanismo vigente de
[v3_context.py](../../../scripts/v3_context.py): la ruta normal conserva contexto
normativo y el selector reducido sigue en comparación. Esta propuesta no activa
`comparison` para ejecutar trabajo. Reutiliza las consultas paginadas y objetos del
[trabajo de eficiencia documental](../v3-efficiency-migration/PLAN.md), sin volver
a implementar transporte o almacenamiento. En una decisión deben estar presentes
todas sus obligaciones; la paginación no habilita aprobación global de páginas ausentes.

## Cómo comprobar que compensa

Se compararán tres referencias con el mismo conjunto de decisiones y resultados
exigidos:

1. El flujo actual, como referencia de coste y carencias conocidas. No se exigirá
   reproducir su falta de información para obtener una cifra menor.
2. La funcionalidad nueva con todas sus guías disponibles en una lectura conjunta,
   únicamente como control de la comparación, sin mantener un segundo producto.
3. La misma funcionalidad con selección por familias y ampliación cuando proceda.

Las tareas de evaluación cubrirán al menos consulta breve, especificación con varios
componentes, plan y tareas propias, relevo e inicio, resultado aceptado, resultado
rechazado, excepción, migración, decisión visual, evento ambiguo, obligaciones fuera
de tablas y continuación tras compactación. Se añadirán ruido de eventos ajenos,
enlaces rotos, rutas de otro runtime, condiciones críticas al final del documento
y cambios de fuente entre lectura y decisión. Los ejemplos serán sintéticos.

| Dimensión | Medida y condición de aceptación |
|---|---|
| Corrección | En los casos evaluados, ninguna obligación crítica omitida, aprobación indebida, firma inventada ni capacidad histórica reactivada. No empeorar decisiones, detalle técnico o resultado de implementación frente a contenido completo. |
| Selección | Cada evento y composición llega a las reglas necesarias. Ausencia de datos produce ampliación/aclaración o detención del paso afectado, nunca suficiencia falsa. |
| Carga de instrucciones | Caracteres y, si existe un tokenizador identificado, tokens; archivos únicos, lecturas repetidas y saltos. Las rutas de un solo evento deben cargar menos que el control con todas las guías, con igual información necesaria. |
| Trabajo completo | Lecturas de instrucciones y proyecto, salidas de herramientas, ampliaciones, reintentos, correcciones, preguntas innecesarias y duración. El ahorro inicial no basta si se pierde en recuperación o errores posteriores. |
| Procedencia | Modelo/host cuando se observen, runtime, fuentes, escenario y medidas separadas. Coste facturado y tokens reales quedan no medidos si el host no los proporciona. |

PV-15 hará la comparación técnica y preparará el protocolo; PV-08 observará el
comportamiento real de los hosts con ese protocolo. Una prueba de enlaces, un
contador o un test del catálogo no demuestra comprensión del agente. La evaluación
es focal de esta implementación y no se convierte en una batería permanente de release.
No se promete un porcentaje de ahorro ni una reducción de errores antes de medirlos.

Si la división no reduce la carga total o provoca omisiones, se ajustará la
agrupación o se conservará junto el contenido necesario. Una mejora de claridad
con mayor consumo podrá documentarse, pero no se presentará como ahorro demostrado.

## Cambios que deben entrar en el plan

- PV-01 fijará invariantes, catálogo y propiedad única de cada regla; sustituirá la
  guía monolítica por índice y familias y conservará una medición inicial reproducible.
- PV-03 expondrá los recursos de instrucciones del perfil sin añadirlos al mensaje
  destinado al usuario. PV-14 completará la selección y la reorganización documental.
- PV-05 integrará las rutas en las seis skills y revisará la continuidad tras
  cambios de evento. PV-06 verificará distribución y resolución desde ambos hosts.
- PV-07 probará rutas, composiciones y conservación de reglas. PV-15 comparará
  carga y preparará la observación de comportamiento que se realiza en PV-08.

Hay una condición de empaquetado concreta: el
[validador actual](../../../scripts/validate_plugin_contract.py) permite una lista
cerrada de referencias compartidas fuera de cada skill, y `distribution/dual.json`
declara archivos adicionales. Deben incorporar los recursos exactos y comprobar
sus enlaces transitivos; no basta con que existan en el checkout ni procede abrir
cualquier ruta externa. Se conservarán los adaptadores que evitan cargar a la vez
las entradas de proyecto y plugin en Copilot.

El análisis justifica abordar la organización ahora, antes de añadir los perfiles.
No justifica crear más skills, activar el selector experimental, desplegar un motor
de búsqueda semántica ni hacer una reorganización general del repositorio.
