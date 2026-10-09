# Implementación de integral-review-02

Estado: autorizado por la petición «implementalo» de 2026-09-29.
Base: propuesta funcional y técnica `specs/proposed/integral-review/`.
Esta autorización cubre preparación del plan, implementación local y comprobaciones;
no publicación, instalación en consumidores ni operaciones Git remotas.

| Tarea | Alcance y resultado | Aceptación |
|---|---|---|
| IR-01 | Formato 3.1 optativo, lectura dual y adopción explícita; conservación de 3.0 e historia. | AC-IR-12, 15, 16 |
| IR-02 | Revisores por identidad, comentarios, cierre integral y controles contra bypass. | AC-IR-01, 02, 03, 06, 19 |
| IR-03 | Revisión de encargos, cobertura conjunta de tareas propias, asignaciones e independencia. | AC-IR-04, 05, 07, 21, 22, 25, 26 |
| IR-04 | Rechazos, definición correctiva, resolución con evidencia y preparación de entrega. | AC-IR-08, 09, 10, 17, 18 |
| IR-05 | Hitos y cálculo compartido de intervenciones agrupadas, CLI y seis skills. | AC-IR-11, 13, 14, 20, 23, 24 |
| IR-06 | Integración del núcleo, regresión v3, compatibilidad y validación del contrato. | Todos los criterios y sus recorridos negativos |

IR-02/03/04 dependen de IR-01; IR-05 consume esos controles; IR-06 verifica el conjunto.
Cada tarea incluye pruebas de integración con documentos y repositorios temporales.
No se alteran fuentes de `specs/canonical/`. La versión de release no se publica
ni se presenta como aceptada por ejecutar pruebas locales.

Validación: contrato del plugin según `docs/VALIDATION.md`; regresiones focales
de v3 y pruebas del recorrido 3.1, de rechazo y de agrupación; revisión de diff.
La experiencia humana de Codex/Copilot permanece no ejecutada salvo evidencia real.

## Resultado de implementación

IR-01 a IR-06 completados localmente; comprobaciones focales superadas.

- `v31_review.py` acredita revisión integral, tratamiento de objeciones, cierre,
  revisión de encargos, designaciones y adopción explícita.
- `v31_corrections.py` registra rechazo, definición, clasificación y evidencia
  correctiva; una aceptación anterior al fallo no se reactiva al resolverlo.
- `v31_guidance.py` deriva H1–H7 y las intervenciones efectivas por persona.
  Las dispensas conservan reservas y la revisión desactivada figura como no exigida.
- Las composiciones conservan una referencia común de intervención, con decisiones
  separadas sobre contenido exacto. Se mantiene el orden de aceptación del proyecto.
- Las seis skills consumen el recorrido común y cargan la referencia 3.1 cuando
  procede. Consultas e inventarios paginan los detalles sin recortar el contrato.
- Distribución e índice admiten 3.1/3.1.0; el formato predeterminado sigue en 3.0.
  La adopción del runtime fijado y su rollback se comprueban con repos temporales.

El registro de participantes de cada petición se acredita en la decisión de gobierno
con su descriptor exacto. Esta implementación concreta evita una segunda firma
`review-roster`; las designaciones heredadas no añaden intervenciones administrativas.
Los resultados negativos usan `reject-result`, separado de las operaciones positivas.

## Evidencia de desarrollo

Pruebas ejecutadas en Windows con repositorios Git temporales, personas sintéticas y
artefactos de prueba. No son un piloto humano ni un análisis Sonar de producción.

| Comprobación | Resultado observado |
|---|---|
| Contrato del plugin, `validate_plugin_contract.py .` | Superado; seis skills, lectores 1.5/2.0/3.0/3.1. |
| Regresión inicial v3: workflow, integration, governance_quality | 21 casos superados. |
| Regresión focal tras ajustes: ciclo completo, gobierno, dependencias, integración, Sonar/Dependency-Check y reservas | 7 casos superados; incluidos en los 21 anteriores. |
| Migración de formatos anteriores, `test_v3_migration` | 5 casos superados. |
| Runtime distribuido, `test_v3_distribution` | 1 caso superado: v2 → 3.0 → 3.1, CLI fijada y rollback a 3.0. |
| Recorrido integral | 11 casos distintos superados por bloques; repetidos los casos afectados por correcciones. |
| Diff y sintaxis de Python modificado | Sin errores. |

Durante las pruebas se corrigieron dos problemas detectados: los módulos nuevos
faltaban en el bundle de desarrollo; la vista previa de gobierno no conservaba el
snapshot anterior de la política. Sus pruebas de distribución e independencia se
repitieron y pasaron. Los fallos iniciales no se presentan como ejecuciones superadas.

En total se han comprobado 38 casos distintos, con repeticiones focales durante
las correcciones. No se presenta este resultado como un gate de release ni como
una ejecución única de toda la batería.

Para reproducir los casos nuevos:

```powershell
python -B -X utf8 tests/run_unit_tests.py --module test_v31_review
python -B -X utf8 tests/run_unit_tests.py --module test_v3_distribution
python -B -X utf8 scripts/validate_plugin_contract.py .
```

## Límites de lo acreditado

Estado al terminar la implementación local: sin commit, push, publicación ni instalación en consumidores.
En ese momento el manifiesto comercial conservaba 3.0.0; 3.1 identifica el nuevo formato/método
optativo y no una release publicada. La aceptación conversacional real en Codex y
Copilot sigue `not-run`. Se conserva `specs/canonical/` y el alcance excluye CI/CD.

Guía de operación: [V31-REVIEW.md](../../V31-REVIEW.md).

## Corrección de entrada: 2026-09-30

Una captura aportada por el usuario muestra que el agente anuncia implementación
con decisiones de estados aplazadas, sin mostrar primero la cobertura de
especificación y planificación. La captura no acredita el orden completo de
herramientas ni permite afirmar que esos documentos no existían.

Se refuerzan las entradas de define/implement, las reglas comunes v3 y las
instrucciones del proyecto generadas para ambos hosts. Antes de anunciar ejecución
o editar código de aplicación se identifica y explica la cobertura vigente;
si falta, se documenta, valida y planifica primero. Los pendientes se registran y
se evalúa su impacto antes de aislar una parte independiente. La orden de
implementar no se interpreta como dispensa implícita del proceso. Se reutilizan
decisiones vigentes y se preserva la invocación implícita de las seis skills.

Esta corrección es de instrucciones y distribución; no añade interceptores,
servicios ni otro mecanismo de escritura. Se añaden los casos de entrada al
protocolo de aceptación de host, pendientes de observación real. El runtime fijado
de un consumidor requiere su actualización explícita para recibir estas fuentes.

Comprobaciones de esta corrección: validador de las dos skills y contrato del
plugin superados; generación en memoria de adaptadores 3.0/3.1 con seis skills e
integridad comprobada; `test_approval_change_invalidates_start` superado; diff sin
errores. No se han publicado ni instalado estos cambios y los dos casos nuevos
de selección conversacional siguen pendientes de observación.

## Preparación de publicación — 2026-09-30

DEC-V31-001 autoriza integrar y publicar todos los cambios pendientes y actualizar
el plugin en Codex. Se prepara la release 3.1.0; la aprobación está en
`quality/release-approval-v3.1.0.json`. Las pruebas focales documentadas arriba
acreditan desarrollo; la publicación requiere adicionalmente el gate estable
sobre el commit final integrado. Se conserva el estado histórico de los ensayos
conversacionales como pendiente y no se migra ningún consumidor.
