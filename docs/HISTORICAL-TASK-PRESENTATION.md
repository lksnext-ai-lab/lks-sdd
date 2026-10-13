# Presentación de tareas históricas migradas — 3.4.2

Fecha: 2026-10-13. Mantenimiento del plugin, cubierto por el
[plan de presentación](plans/specification-review-presentation/PLAN.md).
Preparación local: `3.4.2-rc.1`. La versión estable `3.4.2` tiene autorización propia.

## Decisiones y autorización

La petición de esta conversación autoriza corregir `v3_decision_presentation.py`
y añadir regresiones sintéticas generales para 3.4.2. Fija conservar íntegros
los antecedentes migrados, su procedencia, responsables y pendientes, sin
atribuirles autoridad actual ni relajar los controles de resultados vigentes.
No es una migración ni una autorización de ejecución de un proyecto consumidor.
La petición posterior «Autorizado. Haz el commit, intégralo en main, haz push y
publica la versión estable 3.4.2 tras superar el gate y verificar los paquetes»
autoriza esos pasos sobre esta corrección. La publicación depende del gate y de
los paquetes del commit final. Excluye instalación y migración de consumidores.
Las fuentes en `specs/canonical/` se conservan.

## Hecho y alcance

`_generic` llama a `v3_team.owners` para todas las tareas relacionadas. Un registro
migrado con un responsable ajeno al equipo actual, o sin alcance vigente, impide
construir la vista del resultado actual. La corrección afecta también a consultas
directas de tareas históricas y a continuidades `reconciliation-required`.

## Plan autorizado

- HT-01: verificar la procedencia histórica contra la migración, el mapa de
  identidades, el inventario y los bytes originales con su hash. Rechazar marcas
  falsas o contradictorias; una etiqueta `continuation` sola no basta.
- HT-02: presentar cuerpo y datos completos, responsables literales y pendientes.
  Conservar fuentes y adjuntos; vincular las pruebas de procedencia al receipt y
  a los guards. No evaluar responsables ni controles actuales sobre antecedentes.
- HT-03: mantener propietarios, permisos y controles estrictos para tareas actuales,
  incluso reconciliadas. Mantener el bloqueo de resultados pendientes de reconciliación.
- HT-04: reproducir con fixtures sintéticas relacionadas y directas; comprobar
  procedencias falsas, adjuntos, cambios concurrentes y receipts obsoletos.

## Criterios de aceptación

1. Las vistas de verificación, integración y aceptación conservan antecedentes
   `historical` y `reconciliation-required` sin resolver sus identidades como equipo actual.
2. La presentación conserva datos completos, cuerpos, pendientes, fuentes,
   bases, adjuntos y hashes. La procedencia se vuelve a comprobar al decidir.
3. Propietarios actuales ausentes, inactivos o sin permiso continúan bloqueando.
4. Una procedencia manipulada bloquea; una tarea reconciliada vuelve al recorrido actual.
5. Las mutaciones de contenido, originales, adjuntos o fuentes invalidan receipts
   y guards; un resultado pendiente de reconciliación sigue sin ser aceptable.

## Corrección implementada

`_historical_task` reconoce exclusivamente las dos continuidades migradas sin
reconciliar. Comprueba formato y método, identidad en el mapa de la migración,
integridad del inventario, ruta y hash del original, identidad y estado del bloque
v2 conservado y coherencia de la continuidad. Los inventarios por referencia y
los originales virtuales usan los lectores existentes. La caché dura una consulta;
los originales compartidos se leen, decodifican y hashean una sola vez.

La colección conserva todas las tareas y añade el registro de migración, los
originales y los soportes de almacenamiento necesarios. Las vistas muestran los
metadatos completos y cuerpos literales de las tareas históricas. Sus responsables
no se resuelven mediante alias del equipo vigente. Las consultas directas de
registros cancelados conservan también el cierre de referencias contractuales,
la evidencia relacionada, sus adjuntos y requisitos de observación. Solo la
presentación de una procedencia comprobada puede recuperar estas raíces canceladas;
la selección ordinaria de trabajo retirado conserva su rechazo.

`_generic` usa `owners` para las tareas actuales, incluidas las reconciliadas. Los
alcances históricos permanecen visibles, pero no se observan como código actual.
Los pendientes históricos se presentan como antecedentes; los resultados que
pertenecen a la petición y aún necesitan reconciliación bloquean integrar o aceptar.
Los originales y soportes forman parte de la base presentada y los guards existentes.
Cambiar una dependencia histórica normativa sigue invalidando la autorización
exacta de la tarea actual: la corrección no suprime esa obligación de revisión.

## Reproducción y cobertura

Antes de cambiar el runtime, `test_related_history_preserves_all_data_in_result_profiles`
reprodujo en sus tres variantes el mismo fallo de `owners`:
`Identidad inexistente o alias ambiguo: Former synthetic maintainer`.
Las fixtures son repositorios temporales independientes y no usan datos de consumidores.

Las trece regresiones nuevas cubren las tres vistas de resultados, consultas directas
cerradas/abiertas/canceladas, datos y responsables originales, pendientes, controles
actuales, tareas reconciliadas, procedencias falsas, originales alterados, inventarios
por referencia, estados virtuales, migración real, adjuntos sin observar, receipts
obsoletos y rechazo de un apply tras cambiar el original. Una aceptación vigente
puede prepararse con antecedentes; resultados pendientes de reconciliación se rechazan.

## Verificación

Comprobaciones de desarrollo ejecutadas el 2026-10-13 según
[VALIDATION.md](VALIDATION.md): **51 pruebas distintas superadas, sin skips**.
Las repeticiones de casos durante las correcciones no aumentan este recuento.

| Cobertura | Pruebas distintas superadas |
|---|---:|
| Presentación histórica, incluida procedencia del migrador real | 13 |
| Presentación existente y migración | 19 |
| Integración, gobierno, equipo, contexto y calidad | 16 |
| Revisión de encargos, traspasos y orden de aceptación | 3 |

El módulo histórico pasó sus doce pruebas originales. La última prueba añadida
para referencias de una raíz cancelada pasó junto con la repetición de tres casos
de consultas directas, adjuntos y vistas relacionadas sobre el código final.

Comandos de reproducción:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v3_historical_presentation
python -B -X utf8 tests/run_unit_tests.py --module test_v3_decision_presentation --module test_v3_migration
python -B -X utf8 tests/run_unit_tests.py --module test_v3_integration --module test_v3_governance_quality
python -B -X utf8 tests/run_unit_tests.py --module test_v31_review --test test_task_owner_cannot_skip_review_and_stale_definition_requires_review --test test_two_people_distinct_authority_and_partial_handoff --test test_grouped_result_respects_acceptance_before_integration
python -B -X utf8 scripts/validate_plugin_contract.py .
python -B -X utf8 scripts/validate_fixture_manifest.py
git diff --check
```

Contrato estático válido para `3.4.2-rc.1`, manifiesto de 13 fixtures válido y diff
revisado sin errores de whitespace. HT-01 a HT-04 quedan implementadas y verificadas
en este árbol local. No se alteran fuentes canónicas ni formatos técnicos.

La aprobación estable está en `quality/release-approval-v3.4.2.json`. El commit
integrado debe pasar el preflight estable, la regresión de Windows y la validación
de los paquetes; sus evidencias de Actions identifican SHA, run, assets y hashes.
Esos estados se acreditan después de integrar, sin anticiparlos en este documento.
Instalación, migración de consumidores y aceptación humana de un host quedan fuera.
