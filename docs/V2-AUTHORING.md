# Especificaciones v2: estructura y redacción

El repositorio del proyecto conserva tres niveles: producto, funcionalidades y
trabajo. Un incremento organiza un cambio; una release agrupa una entrega. Ninguno
de ellos es sinónimo de funcionalidad. Una TASK tiene una funcionalidad principal
y puede contribuir a otras, sin duplicar su ficha.

```text
docs/lks-sdd/
  00-control/                 decisiones operativas, autoridad, historia y migración
  01-context/                 finalidad del proyecto y baseline parcial si existe
  02-specification/
    features/
      FTR-001-pedidos/
        specification.md     finalidad, comportamiento y obligaciones de pedidos
        details/             opcional: un detalle que merece documento propio
        assets/              opcional: imágenes/diagramas referenciados
      FTR-002-impresion/
        specification.md
    shared/                  reglas transversales y aplicabilidad
    catalog.md               solo si se solicita exportar la vista derivada
  03-solution/               declaración tecnológica local, decisiones, interfaces, bindings y entornos
  04-delivery/               planes, TASK, ejecución, checkpoints y recibos
  evidence/                  resultados y artefactos inmutables
```

Las carpetas se crean cuando hay contenido. No generar un esqueleto de documentos
vacíos. La anidación es lógica: `parent` identifica un padre principal; `uses` una
capacidad utilizada; `depends_on` una dependencia. La impresión puede pertenecer a
pedidos y ser utilizada por expediciones, manteniendo una sola definición.
No se heredan aprobación, requisitos o estado por ser hija de otra funcionalidad.

## Declaración tecnológica local

Todo proyecto v2 contiene
`03-solution/technology-declaration.md`, indexado en `project.json`. Es Markdown
canónico: cada `TECH-###` declara un asunto, su alcance (`global` o TASK
explícitas), criticidad, evidencia local con hash y procedencia histórica cuando
exista. Los únicos estados admitidos son `observed`, `proposed`, `confirmed`,
`unknown` y `transition`.

Una observación procede de documentación, locks o manifiestos locales y no confirma
una selección. Una propuesta tampoco concede preparación. Solo una declaración
`confirmed`, con evidencia local vigente, puede satisfacer una necesidad tecnológica
crítica. Los `unknown` no críticos pueden permanecer visibles; no acreditan
preparación para una TASK de su alcance. Un `unknown`, `observed`, `proposed` o
`transition` crítico bloquea ese alcance hasta su confirmación explícita.

Las fuentes tecnológicas 1.x retiradas no son conceptos v2 activos en esta
declaración. El recibo de migración conserva su antecedente histórico, pero no
copia su ID o estado como valor confirmado. Los `binding` genéricos siguen
representando relaciones no tecnológicas y no sustituyen una declaración
tecnológica local.

## Formato de un documento

El frontmatter declara versión y tipo. Cada elemento tiene un comentario JSON de
una línea, un ancla explícita y contenido humano. La identidad técnica `uid` no
cambia; el ID es su alias legible. La prosa forma parte del contrato, también las
excepciones fuera de tablas. No repetir una regla en varias fichas: enlazarla.

Use `v2 feature --request ...` para una ficha nueva en borrador y `v2 author` para
un cambio revisado. Ambos muestran primero el diff material mediante preview y
archivan las definiciones anteriores al aplicar. La solicitud no es un documento
canónico: es la descripción de la operación autorizada.

La [plantilla de solicitud](../skills/lks-sdd-define/templates/v2-feature-request.json)
enumera los campos, pero no aporta reglas de negocio. Sustituya los marcadores
antes de proponer aprobación. No se crean TASK ni se generan fuentes ejecutables
por el mero hecho de definir una feature.

## Revisión y evolución

Una corrección del mismo comportamiento mantiene la identidad. Un cambio normativo
incrementa `revision` y archiva su definición. Una capacidad nueva recibe otro ID.
Una sustitución usa `replaces`, `splits` o `merges` y `replacement` con modo
`partial|total`, estado, efectividad y alcance residual cuando corresponda. La
efectividad documenta versión, entorno y flags; aprobar una propuesta futura no
retira la definición actual ni prueba un despliegue.

Las observaciones de despliegue, retirada, rollback o flags se registran aparte
con `v2 delivery`: entorno, versión, artefacto y EVID exactos. El catálogo muestra
definición, trabajo, evidencia y entregas separadas. No inventar retrospectivamente
las features de un producto con años de vida. Su cobertura puede seguir siendo parcial.

## Peticiones extensas y trabajo compartido

Antes de implementar, descomponer la petición en resultados coherentes, mantener
su trazabilidad en PLAN/INC/REL/TASK y comprobar ambas direcciones con `v2 decompose
--id PLAN-###`: nada solicitado sin tarea y nada planificado sin alcance acordado.
Confirmar propietario, dependencias, integración y criterio de aceptación. Una
planificación parcial necesita política incremental expresa y huecos visibles.
La cobertura de una TASK procede de sus requisitos explícitos o de la aceptación
completa trazada de cada requisito. Vincularse a una feature no declara cubiertos
todos sus requisitos, ni los de sus features contribuyentes.

Cada clon puede crear UUID, pero no resolver por su cuenta qué feature equivale a
otra. Ante alias repetidos con UID distinto, detener la integración y revisar.
`v2 rename-aliases` aplica un mapa autorizado en la copia entrante, conserva UID y
alias históricos, corrige relaciones y revoca autoridad que quedó ligada a otra
base. `v2 merge-preview` no sustituye revisión semántica aunque Git fusione limpio.

## Enlaces y snapshots

Escribir `[FR-001 · impresión permitida](<ruta-relativa.md#fr-001>)` y conservar
`<a id="fr-001"></a>`. El validador comprueba archivo, ancla e identidad. Al mover un
documento, incluir sus enlaces entrantes en la misma solicitud; no cambiar IDs.
Los snapshots conservan el árbol relativo y los activos, de modo que sus enlaces
siguen apuntando a la definición histórica, no a la definición actual.

## Consulta y ejecución son vistas distintas

Consultar produce una explicación integrada y enlazada, con tablas, listas o
diagramas cuando ayudan. No modifica el contrato ni lo resume destructivamente.
`context` entrega literalmente todas las obligaciones del trabajo seleccionado,
incluidos contribuyentes y reglas transversales. Nunca implementar solo desde la
vista resumida. Una carencia de intención de negocio exige aclaración, no una
deducción a partir del código.
