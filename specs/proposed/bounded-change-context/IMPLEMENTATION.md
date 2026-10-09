# Ejecución de la mejora documental

Fecha: 2026-10-09. Estado: desarrollo autorizado por la petición de continuar hasta
preparar una nueva release, planificando cada tarea. Base: [PLAN.md](PLAN.md),
[PROPOSAL.md](PROPOSAL.md) y [GLOBAL-AUDIT.md](GLOBAL-AUDIT.md).
Los identificadores siguientes son mantenimiento del plugin, no identidades de personas
ni permisos creados en consumidores. No se modifican fuentes de `specs/canonical/`.

## Decisiones técnicas del desarrollo

- Conservar schema 3.1 y método 3.1.0 mientras las extensiones quepan en los campos
  canónicos existentes. La release candidata se dimensionará por las interfaces efectivas.
- Presentación CLI ordinaria con un único cuerpo literal y recibo; `--compact` permite
  la misma economía junto con `--json`. Conservar el JSON detallado anterior sin esa
  opción, el resultado de biblioteca, `--details` y exportación. Probar las rutas y
  orientar las skills al transporte compacto.
- Reutilizar el modelo únicamente dentro de consultas de una misma operación. Las
  mutaciones y la aplicación de paquetes conservan cargas y guards frescos.
- Resolver unidades por petición, propuesta y plan; conservar cierre transitivo y
  contribuciones entrantes. Las pertenencias contradictorias amplían y diagnostican.
- El contexto de ejecución usará ese mismo cierre. El modo de referencia completo
  permanecerá como diagnóstico explícito, con obligaciones inciertas siempre incluidas.
- La prosa sin ámbito sigue incluida. Admitir declaraciones por fuente en el Markdown
  del proyecto, ligadas al hash del texto y a una decisión de gobierno competente.
  Su ausencia, caducidad o contradicción nunca acreditan exclusión. Reutilizar `governance`
  para revisar lotes; evitar un nuevo entrypoint y clasificaciones inferidas por carpeta.
- La transición de documentos puede ser incremental o incluir un lote inicial asistido.
  El runtime se actualiza mediante migración explícita existente. No forzar una conversión
  general del corpus cuando los acuerdos existentes basten; conservar originales e historia.
- Continuidad ordinaria: último checkpoint simple por tarea; conservar pendientes,
  problemas, decisiones y evidencia, además de hechos expresamente solicitados.
  El historial íntegro se consulta por `trace`/`history`. Un reintento explícito usa una
  clave de operación; observaciones distintas no se deduplican por texto.

## Tareas, dependencias y cierre

Cada fila fija el objetivo y la comprobación antes de editar su código. Una tarea
solo se cierra después de revisar el diff y su evidencia; los fallos actualizan la tarea.

| ID / fase | Trabajo y límites | Dependencia | Comprobación de cierre | Estado |
|---|---|---|---|---|
| EF-00 / F0 | Revisar cambios previos de inventarios sin descartarlos y fijar decisiones/baseline. | Diagnóstico. | Diff delimitado, autoría conservada, tareas y métricas descritas. | Completada |
| EF-01 / F1 | Compactar vistas ordinarias de decisión y revisión; mantener exportación y detalle. | EF-00 | CLI con --compact sin cuerpos repetidos; JSON anterior y recibo conservados; borrador incompleto visible. | Completada técnicamente |
| EF-02 / F2 | Compartir modelo validado en consultas y hechos entre status/interventions. | EF-00 | Una carga en review/readiness; no confianza reutilizada entre llamadas o en mutaciones. | Completada técnicamente |
| EF-03 / F3 | Unificar pertenencias, raíces antes de PLAN y cierre de dependencias/contexto público. | EF-01, EF-02 | Independientes excluidos; globales, compartidos, entrantes, ciclos y contradicciones conservados. | Completada en regresiones focales; semántica del consumidor pendiente |
| EF-04 / F3,F5 | Declaraciones canónicas de prosa y actualización explícita del runtime. | EF-03 | Hash/autoridad/vigencia; fuente mixta global; modificación invalida clasificación; consultas no escriben. | Completada técnicamente |
| EF-05 / F1,F4 | Continuidad pertinente, texto enlazado y reintentos de checkpoints. | EF-03 | Historial recuperable; pendientes y negativos conservados; texto no exige observación visual; claves distintas conservan hechos. | Completada técnicamente |
| EF-06 / F4,F5 | Ajustar seis rutas y ejemplos concisos de cambios, consultas y reanudación. | EF-01–05 | Guías coherentes con CLI; permisos y decisiones vigentes; sin documentación adicional por consulta. | Completada técnicamente; hosts reales no observados |
| EF-07 / F5 | Verificar almacenamiento/migración previos y compatibilidad con consumidores 3.2. | EF-04–06 | Regresiones de inventarios, preservación, runtime y recuperación; sin migraciones reales. | Completada técnicamente: 50/50 |
| EF-08 / F6 | Comparar flujos sintéticos completos y límites de coste. | EF-01–07 | Mismo resultado y obligaciones; caracteres, cargas, parseos, tiempos y costes de preparación explícitos. | Comparación sintética completada; tokens/tiempo real pendientes |
| EF-09 / F6 | Preparar metadatos, notas, validaciones y paquetes de candidata. | EF-08 | Contrato, fixtures, humo, rutas largas y distribución; gates de aprobación/commit pendientes explícitos. | Preparación técnica local completada; commit y gate oficiales pendientes |

## Medición y presupuesto

Comparar consultas, corrección cubierta/no cubierta, interfaz, funcionalidad,
contrato compartido, reanudación y adopción/migración en fixtures equivalentes.
Horizonte de evaluación inicial: 20 operaciones, con 8 consultas, 4 reanudaciones,
4 correcciones y 4 decisiones de definición/verificación. Es una hipótesis de
evaluación, no una predicción del uso de cada consumidor. Si se requiere clasificación
inicial, incluir fuentes leídas, declaraciones escritas y revisión; calcular también
el punto de compensación sin limitarlo al horizonte favorable.

Presupuestos técnicos: una copia del cuerpo en presentación ordinaria; una carga
del modelo por consulta lógica; cero escrituras por consulta; añadir historia o
contratos acreditados como independientes no amplía proporcionalmente la presentación.
La referencia completa tiene salida explícita, sin truncamientos semánticos.
Medir latencias con repeticiones solo cuando la variación impida comparar.

Tokens facturados, tiempo humano y conversaciones reales por host necesitan observación
de esos canales. No se sustituyen por caracteres/4 ni por fixtures de biblioteca.
La candidata técnica y su publicación se distinguen de esa aceptación. Una migración
obligatoria no se justifica sin acreditar que compensa su coste; esta implementación
prioriza mejoras compatibles y reconciliación acotada, con transición explícita de runtime.

## Registro de ejecución

- EF-00: revisado estado inicial: ocho archivos de inventarios/almacenamiento modificados
  y la propuesta sin seguimiento Git. Se preservan; branch `codex/fix-legacy-migration-inventory`.
  No existe índice de proyecto consumidor en este repositorio; se continúa el mantenimiento
  documentado, sin inicializar SDD ni registrar personas reales.
- EF-01/02: primeras 16 comprobaciones de presentación y evaluación superadas. Se
  añadió posteriormente `--compact` conservando `--json` detallado; se vuelve a verificar
  esa compatibilidad. Las consultas públicas comparten modelo y status/interventions
  reutilizan hechos; las mutaciones conservan las comprobaciones anteriores.
- EF-03/04: seis regresiones iniciales de flujo superadas: raíces antes de PLAN,
  reglas globales, entrantes, pertenencias compartidas/contradictorias, declaraciones
  sin gobierno y obsoletas. La extensión usa el Markdown del proyecto y `governance`;
  no obliga a cambiar schema/método ni a migrar toda la documentación.
- EF-05: implementadas selección de checkpoints simples, conservación de pendientes
  e historia, claves explícitas de reintento y lectura de logs/código/HTML como texto.
- Regresión integrada inicial: 25 de 26 casos superados. Falló una porción de propuesta
  dentro de una misma petición: el selector confundía pertenencia a la petición con
  conflicto de unidades. Se corrige conservando únicamente discrepancias reales entre
  petición declarada y petición propietaria por relaciones. El informe inicial se
  conserva en `evidence/flow-tests.json`; la repetición focal se registra aparte.
- Sonda actual: una carga física en review/readiness público, frente al doble cálculo
  anterior de readiness; status evalúa sus hechos una vez. Diez checkpoints sin pendientes
  incorporan una fuente actual, con historia recuperable. Latencias recogidas mientras
  había otras regresiones en curso: no acreditan todavía un ahorro de tiempo comparable.
- Corrección focal: 3/3 comprobaciones superadas, incluido el fallo de porción independiente
  en una misma petición y compatibilidad del JSON anterior. Se conserva el primer fallo.
- EF-03: se planifica y comprueba por separado la base semántica del recibo y la
  concurrencia del archivo. El formato de presentación pasa a `/2`: una edición ajena
  dentro del mismo archivo no cambia el recibo; el guard conserva los hashes físicos
  vigentes y detecta cualquier cambio entre presentación efectiva y aplicación.
  Tres comprobaciones de recibos, concurrencia y aprobaciones anteriores superadas.
- EF-09: se prepara `3.3.0-rc.1`, candidata local sin aprobación de publicación. La
  selección y las opciones de transporte son nuevas; schema/método permanecen 3.1/3.1.0.
  La salida detallada JSON sigue disponible con la interfaz anterior. El número estable
  y su aprobación se cerrarán sobre el candidato revisado, sin reutilizar la aprobación 3.2.
- EF-04: comprobación adicional superada: cambiar el ámbito de una prosa ya excluida
  vuelve a mostrar su contenido y adjuntos literales. Una huella propuesta distinta
  del contenido vigente produce una vista incompleta; no se aprueba solo el metadato.
- EF-06: el mismo comando ejecutado desde paquetes Codex y Copilot devuelve la misma
  presentación. Se mantiene el transporte JSON detallado anterior y el compacto explícito.
- EF-08: se prepara comparación reproducible de un recorrido íntegro de biblioteca,
  con cinco contratos independientes, obligación global, diez avances, pausa/reanudación,
  prueba ejecutada del código, integración, aceptación y entrega. Se contabilizan también
  preparación, mutaciones y recálculos de guards. No acredita conversaciones reales.
- EF-09: integridad estática y rutas largas de Windows superadas. Las catorce pruebas
  de humo agotaron 600 segundos con la regresión de almacenamiento de gran volumen
  simultánea; se conserva el informe fallido y se repetirá sin esa carga. No se amplía
  su timeout ni se presenta ese resultado como gate superado.
- EF-03/04: pertenencias contradictorias conservadas y aprobación bloqueada hasta
  aclararlas; las consultas y la continuidad muestran el pendiente. Un campo adicional
  en una petición no sustituye sus relaciones canónicas. La presentación muestra
  documento, ámbito y motivo de cada declaración; solo `governance` de formato /2
  acredita esa extensión. Pruebas con recibo antiguo, ausente y de tipo incorrecto superadas.
- EF-03: se verifica también un archivo compartido por el proyecto que acredita alcance
  y un requisito independiente. El recibo conserva esa independencia semántica y los
  hashes físicos continúan en los guards. Tres regresiones finales de recibos superadas.
- EF-05: comprobada continuidad con reservas, carácter crítico, clasificación incierta
  y resultado fallido. Solo avances explícitos informativos se omiten; se conserva la
  fuente negativa y se presenta su resultado. La prueba final está superada.
- EF-07: el caso de 100.005 archivos históricos ha superado migración, conservación
  de originales, mapas, autores y autorizaciones previos. La batería completa de
  almacenamiento/migración termina con 50/50, sin skips, en 3.993,339 s. Su volumen
  extremo tuvo coste alto en Windows; no describe una consulta normal ni una mejora
  demostrada de la velocidad del corte inicial.
- EF-08: los dos recorridos terminan con los mismos hitos completados, saludo comprobado,
  cero intervenciones pendientes y diez checkpoints conservados. Las presentaciones y
  consultas contabilizadas pasan de 202.100 a 39.199 caracteres (80,6 % menos).
  Son salidas seleccionadas del recorrido; no total de herramientas ni tokens de IA.
- EF-08: se registran 156 → 154 cargas físicas y 5.636 → 5.564 parseos en todo el
  recorrido instrumentado: las mejoras de consultas no eliminan el trabajo de mutaciones.
  Los tiempos observados 470,46/380,48 s no acreditan una reducción fiable, por carga
  simultánea y observación única. Las instrucciones comparables crecen 621–950 caracteres.
- EF-08: reconciliar 25 fuentes exige leer sus 98.515 caracteres y escribir 7.139
  caracteres de declaración canónica. La vista ordinaria posterior pasa de 102.220 a
  2.605 caracteres. El escenario compensa la vista extra de clasificación en dos vistas
  equivalentes solo por caracteres; no existe punto de compensación observado de tokens
  ni tiempo humano. La primera revisión conserva otras fuentes inciertas.
- EF-09: las catorce pruebas de humo han pasado al repetirlas tras terminar el caso
  masivo, en 370,882 s y con el timeout original de 600 s. Se conserva el primer timeout.
  Estos checks de desarrollo no sustituyen el gate del commit limpio.
- EF-01/09: verificada la combinación explícita `--compact --output`: consola con
  un cuerpo y recibo, archivo exportado íntegro e igual al resultado detallado. Se
  congela la fuente distribuida después de esta corrección; las notas y evidencia
  quedan fuera del núcleo de los paquetes de desarrollo.
- EF-09: revisado el diff final; contrato y trece fixtures válidos. Siete artefactos
  generados y reproducidos byte a byte, hashes y ZIP íntegros, núcleo de 480 archivos
  idéntico en fuente, plugin Codex, marketplace y Copilot. El informe actual conserva
  85 casos distintos con último resultado favorable, incluidos los 50 de almacenamiento,
  y referencias separadas al humo y Windows. No son un único pase sobre SHA final.
  El preflight final vuelve a señalar solo el árbol sin commit como bloqueo.

## Cobertura del objetivo completo

La tabla distingue comprobaciones técnicas y observación de uso. No da por aceptado
un criterio solo por compilar, generar un paquete o conservar su hash.

| Criterios | Evidencia actual | Reserva |
|---|---|---|
| AC-01,02,09 | `scope-membership-final-tests.json`, `flow-corrections.json`, los dos `complete-flow-*.json`. Cierre antes de PLAN, plan autorizado, ejecución y entrega. | Fixture de biblioteca; consumidor original sin ejecutar. |
| AC-03,05,07,08 | `flow-tests.json` y corrección focal, `receipt-scope-final-tests.json`, `scope-final-tests.json`, `prose-proof-final-tests.json`. Contratos compartidos/entrantes, guard fresco, borradores y discrepancias. | No se declara auditoría semántica de todas las fuentes del consumidor ni aceptación humana. |
| AC-04,06 | `scope-final-tests.json`, `prose-proof-final-tests.json`, presentación y guard de adjuntos. Prosa ajena con imagen/log; variante global que requiere observación. | Texto HTML se inspecciona como fuente; no acredita ejecución del prototipo ni calidad visual del host. |
| AC-10,12,16,19,20 | `flow-final-checks.json`, `continuity-final-tests.json`, `current-flow-probe.json`, `receipt-scope-final-tests.json`. Lectura fresca, continuidad, reintentos, una carga y cero escrituras en consultas. | No se mide retención/caché de contexto conversacional ni intercambio real entre chats. |
| AC-11,17,21 | `prose-transition-final.json`, `complete-flow-comparison.json`. Sin conversión obligatoria del corpus; coste de clasificación incluido y crecimiento independiente acotado. | Prosa no acreditada sigue incluida. El histórico original y la compensación en tokens/tiempo humano están pendientes. |
| AC-13 | `storage-tests.json`, 50/50 en migración/runtime, almacenamiento y recuperación de la batería focal. | No migración de proyectos reales ni aceptación de su continuación. |
| AC-14,15 | `package-parity-tests.json`, `correction-review-tests.json`, rutas de las 58 acciones, integración, dependencia y pruebas focales. | No existe una comparación conversacional completa de las siete familias en ambos hosts. |
| AC-18 | `complete-flow-comparison.json`, `instruction-cost-current.json`, `prose-transition-final.json`. Resultado equivalente y costes internos/salidas distinguidos. | Tokens facturados, tiempo humano y velocidad total fiable no observados; criterio de ahorro real pendiente. |

Las referencias de evidencia están bajo `evidence/`. El primer informe integrado
con un fallo, la prueba de imagen con fixture inicialmente sin runtime y la sonda de
prosa con una aserción de espacios demasiado estricta se conservan. Sus correcciones
se verifican por separado; no se borra el resultado previo ni se suma como un éxito.

## Entrega local y siguiente paso

### Corte revisado del 2026-10-09

La candidata propuesta es `3.3.0-rc.1`. Se mantiene la rama existente
`codex/fix-legacy-migration-inventory`, con los cambios previos de inventarios
conservados e incluidos en las pruebas. No se han creado commits, etiquetas,
aprobaciones de release ni una instalación activa.

Los paquetes revisables se generan con `--development` fuera del repositorio.
Su canal es `development-unreleased`: permiten inspeccionar distribución y bytes
comunes de Codex/Copilot, pero no son artefactos acreditados del commit final.
Los informes de desarrollo se recogen en
[candidate-validation.json](evidence/candidate-validation.json), con hashes,
comparación de bytes, reproducción del build y referencias a las pruebas. El paquete
local revisado está en
[candidate-working-tree](<C:/Users/j.ormazabal/AppData/Local/Temp/lks-sdd-3.3.0-rc.1-review-20261009-221004/candidate-working-tree>).
El informe [global-review-validation-current.json](evidence/global-review-validation-current.json)
comprueba los documentos, enlaces y evidencia de ese corte; los informes se conservan
como evidencia histórica al continuar la preparación oficial.

El preflight de candidata de ese corte estaba bloqueado únicamente por el árbol Git con cambios.
`AGENTS.md` exige autorización explícita separada para crear commits, hacer push,
publicar o instalar. Tras autorizar el commit revisado, se ejecutarán el preflight
y gate oficiales de canal candidate sobre ese SHA limpio y el builder de release
en un directorio nuevo. Publicación y actualización de consumidores siguen siendo
pasos posteriores con su autorización y comprobación propias.

### Continuación autorizada del 2026-10-10

El usuario responde «sí» a la petición explícita de crear el commit de los cambios
revisados para continuar con el gate oficial. Se planifica el commit, preflight,
gate y build de canal candidate en
[RELEASE-PREPARATION.md](RELEASE-PREPARATION.md). Los informes oficiales quedarán
fuera del repositorio para conservar limpio el SHA evaluado. Esta autorización
es de commit; publicación, push e instalación requieren sus decisiones separadas.

### Límites que conserva la entrega

- La prosa sin ámbito acreditado sigue incluida y su primera revisión puede ser grande.
  No se automatiza una inferencia de independencia a partir de carpetas o antigüedad.
- Las consultas siguen parseando el modelo completo; la paginación limita la salida.
  Reutilizar una carga reduce duplicación interna, no promete I/O sublineal.
- AC-18 y la amortización en tokens/tiempo de AC-21 necesitan uso real. Las cifras
  de caracteres y latencias instrumentadas no los dan por superados.
- El SAT de la incidencia no ha recibido la candidata ni se ha corregido su código.
  Su runtime y prosa requieren una actualización/reconciliación expresamente autorizadas.
- Revisión humana, aceptación real de Codex/Copilot y piloto permanecen `not-run`.

## Preparación de release

Se han ejecutado por separado las comprobaciones técnicas aplicables de
[VALIDATION.md](../../../docs/VALIDATION.md): contrato, trece fixtures, catorce casos
de humo y regresión real de rutas largas de Windows. Su procedencia es desarrollo
sin commit final; no constituyen el gate oficial.
La puerta estable y el build de release exigen commit integrado limpio y aprobación de
versión. Se preparará primero la entrega local concreta, sin simular esas condiciones.
No se crea una aprobación humana ficticia ni se convierte `not-run` en éxito.
