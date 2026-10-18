# Revisión crítica correctiva de V4-04

2026-10-16. Plan 0.4. Alcance autorizado: revisar y corregir V4-04 antes de avanzar.
V4-05 permanece sin iniciar. Se conservan la entrega y evidencia iniciales; este
dictamen las complementa y sustituye únicamente en los puntos corregidos.

## Hallazgos y correcciones

| Hallazgo contrastado | Riesgo de la implementación inicial | Corrección y comprobación |
|---|---|---|
| Adjuntos fuera de la identidad reproducida | Podía figurar `reproduced` comparando solo textos, aunque cambiase la imagen. | La selección esperada y real incluye huellas de adjuntos; mutar una imagen impide declarar reproducción. También se contrasta esa identidad al capturar el fixture. |
| Temporal Windows y mezcla de rutas | El nuevo caso con TEMP largo reprodujo un error real de limpieza; aparecieron además diferencias entre rutas normales y extendidas al recorrer documentos. | El temporal se crea y limpia con ruta extendida; escritura y recorrido documental usan representaciones coherentes. Se conserva la comprobación de enlaces y repositorios anidados. No se cambia TEMP/TMP global. |
| Copia pending corrupta ignorada tras publicar | Una entrada válida podía ocultar una copia pending alterada con la misma identidad. | Se exige igualdad byte a byte; inspección y recuperación bloquean sin reparar ni sobrescribir. |
| Expansión por referencias repetidas | Los límites del directorio y de IDs únicos no acotaban por sí solos los lotes resueltos en memoria. | Se cuentan bytes y observaciones resueltos durante lectura, recuperación y publicación. La suma se comprueba antes de leer el siguiente lote o ampliar la colección; se mantienen 64 MiB y 20.000 observaciones. |
| Recuperación sin efectos declarados y ventana pendiente abierta | Se devolvía `writes: []` tras publicar entradas externas; otra invocación podía añadirse antes de recuperar pendientes. | La recuperación enumera sus escrituras reales, es idempotente y no aplica operaciones normativas. Nuevas invocaciones esperan la recuperación; el reintento idéntico propio conserva su tratamiento. |
| Selección focal y conservación vacía | `usage-report` ignoraba `capture_entries`; una ventana sin observaciones podía devolver `already-recorded`. | Informe, conservación y exportación respetan la selección; conservar una ventana vacía produce una causa explícita. Se validan también los tipos de referencias de transporte. |

Seis pruebas focales ejecutadas contra el módulo de captura del snapshot anterior
fallan de la manera esperada. Aíslan copia pending, expansión, referencias, ventana
vacía, nuevas invocaciones pendientes y efectos de recuperación; no constituyen una
comparación completa ni una medición de ahorro. El caso Windows real y la mutación
de adjuntos aportan su cobertura separada. Las campañas intermedias fallidas y las
repeticiones quedan identificadas, incluso cuando había procesos cargados antes de
una corrección; no se convierten en ejecuciones del candidato final.

El ajuste Windows afecta `scripts/v3_contract.py`, implementación del recorrido
documental. No modifica `specs/canonical/`, reglas normativas, esquema ni autoridad.
La comprobación de lectura/importación mantiene los máximos originales; no autoriza
recortar obligaciones, alterar materiales corruptos ni promover procedencia externa.

## Revisión de los resultados anteriores

El ZIP inicial acredita conservación de materiales y reproducción de la selección
de texto en aquel caso. Su manifest era `needs-material`, con la causa «No
substantiated trigger; supply a bounded case and expected behavior». La prueba
admitía tanto ese estado como `ready-for-investigation`. Esa cobertura era demasiado
permisiva para sostener una afirmación general de caso listo para investigar, y no
comprobaba la identidad de los adjuntos. El nuevo ensayo exige expresamente el
estado y la causa observados y comprueba la imagen. No se inventa un disparador
para hacer pasar el paquete ni se reescribe el ZIP histórico.

`stored` acredita la captura de bytes en su alcance, `reproduced` una selección
documental contrastada y `ready-for-investigation` requiere además el material
exigido por el validador. Ninguno prueba ejecución de la aplicación, causa del
incidente, recepción del host, comprensión humana o aceptación de la release.
Los fixtures antiguos con adjuntos sin expectativa completa no obtienen una
superación implícita de la nueva comprobación.

## Verificación y evidencia

El índice `review-verification.json` registra los resultados finales aplicables y
los bytes del candidato. La cobertura de revisión combina 27 pruebas de captura,
19 de observaciones/informes/bundles/rutas de instrucciones y el caso Windows
existente: 47 casos distintos. Los paquetes Codex y Copilot se extraen y ejecutan
sin instalarlos; los recursos nuevos coinciden con las fuentes empaquetadas.
Las campañas repetidas no aumentan el número de casos distintos. El detalle de
intentos, resultados y costes queda en `review-campaigns.json`.

AC-06/07/08 quedan ratificados en el cierre focal del índice final. Se
comprueban texto e imagen retirados, mutación de adjunto, conservación y reenvío,
lotes en un journal, recibos/decisiones, fallos aislados, corrupción canónica,
procedencia importada, contadores de transporte, presupuestos, interrupción y
Windows. La validación de contrato y el diff permanecen obligatorios. La aceptación
de hosts reales y la release completa no se infieren de estas pruebas.

Se reutiliza `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-04`,
con prefijo `review-`: snapshot anterior/final, huellas, negativos anteriores,
pruebas finales, caso portable retenido y ledger. Los archivos de la entrega inicial
no se sobrescriben; los históricos de V4-03 y protocolos congelados se preservan.
Se mantiene la retención del estudio y la excepción de recuperación nativa; no se
reintenta ninguna limpieza rechazada anteriormente.

## Coste y límites de la conclusión

Los tiempos `review-phase-costs.json` sustituyen la muestra anterior solo como
observación de esta candidata, no como comparación de rendimiento. Se midieron
con otras pruebas concurrentes: sus diferencias no permiten atribuir mejora o
regresión al producto. Captura está incluida en la consulta y no se suma dos veces;
conservar, reportar y exportar siguen distinguiéndose. No se ha ejecutado una pareja
controlada contra 3.4.3. El ahorro total, tokens facturados y S8 ≥20 % siguen
pendientes, y la percepción humana queda para uso real sostenido.

Última muestra de componentes: consulta con captura 2,856 s, de los que 0,629 s
corresponden a la escritura diagnóstica; conservación 11,749 s, reporte 0,229 s y
exportación/inspección 2,493 s. Estos valores no son parejas comparables con la
muestra anterior ni con el baseline. La revisión completó 123 ejecuciones de tests:
117 sobre candidatas en desarrollo/finales y seis negativos controlados del módulo
anterior. Se conservan cinco fallos intermedios de candidata; la campaña final de
captura tiene 27/27 superados y los 47 casos distintos tienen resultado final
aplicable superado.

La revisión tiene corte de 1.200 s desde 12:19:32Z, con preparación, correcciones,
fallos, pruebas, esperas y reporte incluidos. No reinicia ni amplía los máximos
globales: 48 intentos completos, 8 h humanas y 12 h de entorno; M6 dos variantes/
cuatro horas compartidas. No añade intentos completos S1–S8 ni variantes M6. El saldo
histórico global continúa sin certificar; el cierre local no demuestra capacidad
para completar el resto de la release.

No se crea versión, commit, integración, push, instalación, activación o publicación.
El siguiente paso del plan es V4-05, pendiente de decisión de continuación.
