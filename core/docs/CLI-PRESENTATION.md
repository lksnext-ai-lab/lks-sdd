# Presentación del CLI v3

La implementación local de V4-03 añade `--view operational` a las acciones `v3`.
El valor predeterminado es `--view compatible`. Ambos usan el mismo núcleo,
condiciones, contenido normativo y recibos. Esta entrega de desarrollo todavía no
está publicada ni instalada. La consulta compuesta de preparación está disponible
en la candidata local; véase [preparar trabajo](WORK-PREPARE.md). Las transiciones
agrupadas están descritas en [operaciones de trabajo](WORK-OPERATIONS.md).

```text
python scripts/lks_sdd.py v3 decision-view ROOT --input decision.json --view operational --json
python scripts/lks_sdd.py v3 context ROOT --input context.json --view operational
python scripts/lks_sdd.py v3 review ROOT --input request.json --view operational --output full.json
```

| Opción | Cuerpo y diagnóstico emitidos |
|---|---|
| Compatible, sin opciones nuevas | Comportamiento anterior, incluida compactación de decisión sin `--json`; diagnóstico completo. |
| `--view operational` | Un cuerpo de decisión; contexto literal íntegro en consultas. Diagnóstico con IDs, procedencia, métricas, límites y referencias de etapas, sin repetir inputs, resultados ni textos fuente. |
| `--compact` | Vista compacta anterior; se puede combinar con operational. |
| `--details` | Cuerpo y diagnóstico íntegros, también con operational. |
| `--output FILE` | Guarda el resultado API completo y muestra referencia, resumen y condiciones/impedimentos. Tiene prioridad sobre compact/details para el cuerpo impreso. En operational, el diagnóstico impreso sigue siendo una vista de referencias. |
| `--json` | Conserva JSON válido en todos los modos; no determina autoridad o completitud. |

Operational sin details serializa JSON en una línea, sin alterar los valores de
las cadenas. Solo en `work-continue` y `work-record-results` con estado `completed`,
el recibo operativo omite la repetición del campo superior `contract`: conserva
efectos, escrituras, condiciones, recuperación y siguiente paso. No acredita la
lectura del contrato ni concede autoridad. Antes de trabajo nuevo, consultar el
contrato literal vigente mediante `work-prepare`/`context`. Consultas, previews,
bloqueos y resultados parciales conservan su contrato literal completo.
API, details, output y captura explícitos conservan el resultado completo cuando
su entrega tiene éxito; comprobar su estado antes de reintentar una aplicación.

`--compact` y `--details` son mutuamente excluyentes. Un export no se vuelve a
imprimir por combinarlo con compact. La presentación y su recibo no se alteran por
elegir modo. Issues, condiciones incompletas, negaciones, adjuntos y límites siguen
presentes; no se recorta Markdown ni se concede una aprobación global por exportar.
Leer un archivo exportado y presentar su contenido siguen siendo hechos distintos.
La salida compact+output cambia deliberadamente respecto al defecto anterior que
reimprimía el cuerpo; cumple la referencia breve ya prometida por output. No se
promete igualdad binaria de todos los sobres CLI.

El destino de output debe estar fuera del consumidor y no puede coincidir con su
entrada, tampoco mediante un hardlink. Se comprueba antes de ejecutar la operación.
Esto corrige la posibilidad anterior de sobrescribir documentos o código al
exportar una consulta. Un destino que invada el consumidor o la entrada se rechaza
antes de aplicar. También se rechazan archivos con múltiples hardlinks para impedir
que una ruta externa sobrescriba un archivo del consumidor. Los archivos externos
ordinarios ya existentes conservan la sobrescritura explícita anterior. Un error
posterior de E/S sigue pudiendo ocurrir y debe informar de los efectos ya aplicados.
La referencia conserva `complete`, issues/causas, suficiencia, límites, siguiente
paso y condiciones de revisión cuando existan. No entrega un recibo de decisión:
primero hay que leer/presentar su contenido. Los recibos de efectos aplicados sí se
conservan. Una consulta exportada sin status propio se identifica como `exported`,
en vez del `preview` genérico anterior; ese estado describe transporte.

El campo `usage` de operational usa **`lks-sdd-usage-view/1`**:

- `observation_refs` conserva identidad, fase, procedencia, métricas y aplicaciones
  observadas; `fragment_count` indica cantidad, sin volver a transportar el texto.
  Incluye runtime y estado de ventana originales. `fragment_gaps` identifica las
  fuentes grandes/binarias sin bytes conservados; `diagnostic_gaps` mantiene
  límites de input/result. Estos datos no se confunden con contenido recuperado.
- `complete_observations_emitted: false` declara que no es un lote importable en
  `usage-record`. Los sobres completos permanecen en la API compatible y en el
  resultado guardado explícitamente con `--output`.
- `full_diagnostic` declara si esta llamada exportó el resultado API. Exportarlo
  no completa fuentes ausentes o demasiado grandes de la observación original.
- Un diagnóstico incompleto conserva causa/calidad y gaps; no se presenta como
  captura satisfactoria. La captura externa automática corresponde a V4-04.

Sin `--output`, la presentación no conserva el sobre completo de esta llamada en
un archivo externo. Para retenerlo, seleccione output al invocar; pedir details en
otra llamada describe una nueva ejecución. Esta vista no cambia los registros que
el núcleo conserve mediante operaciones explícitas ya existentes.

Consultas sin exportación no escriben en el consumidor. El error de exportación
después de una aplicación informa de los efectos aplicados y sus recibos; no afirma
que el error los haya deshecho. Recuperación, rollback, autorización y frescura de
guardas siguen en el núcleo actual.
Los efectos se informan también en compatible y con details; elegir formato no
puede ocultar una aplicación ya realizada.

La exportación incluye las observaciones de apply/recover/rollback antes de
escribir el archivo. El metadato de transporte calculado después de guardarlo
describe la salida de esta llamada; no se afirma que ya esté dentro del archivo.

Se reutilizan los helpers de rutas de Windows para la exportación de consultas.
No se crean temporales nuevos ni se modifican ajustes de Windows. La cobertura
focal comprueba rutas largas; el gate estable y la compatibilidad global de 4.0
conservan sus verificaciones separadas.

Las métricas `usage.transport` mantienen su cobertura declarada: cuerpo preparado
sin sobre diagnóstico y descriptor de exportación cuando existe. No son bytes de
flujo completo, tokens facturados ni evidencia de recepción/lectura por el host.
