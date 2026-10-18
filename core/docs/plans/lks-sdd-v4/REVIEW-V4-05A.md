# Revisión crítica de V4-05A

Fecha: 2026-10-16. Autorización: revisar/corregir esta porción y sus garantías;
**sin instalar, ejecutar H2 ni continuar a V4-06**.

## Dictamen

La porción técnica conserva su verificación después de las correcciones. No se ha
reproducido un defecto funcional nuevo en los scripts del núcleo examinados. Sí
había carencias de guía y de suficiencia de la evidencia, que se corrigen abajo.
AC-34 sigue pendiente de la pareja real H2; V4-05A continúa `in-progress`.

La ejecución S1 anterior demuestra un recorrido sintético con prueba real y cierre,
no selección/lectura de skills por Codex. Las 36 comprobaciones comparten ese
recorrido y no son 36 escenarios ni ensayos funcionales independientes. Los datos
de transporte/tiempo siguen siendo descriptivos y no acreditan ahorro.

## Hallazgos, corrección y comprobación

| Hallazgo crítico | Corrección o disposición | Evidencia |
|---|---|---|
| La guía decía que todas las operaciones compuestas estaban pendientes, aunque work-prepare ya existe. | Se distingue preparación local disponible de las transiciones agrupadas futuras. | Contrato estático y bytes de guía en ambos adaptadores. |
| El recorrido recomendado con --apply no explicaba suficientemente un error posterior a la aplicación. | Se exige comprobar effects/recibo/estado antes de repetir y recuperar la transacción exacta. Para una ya completada se indica hash + --receipt; la falta de pendiente no prueba falta de aplicación. | Prueba real en compatible y operativo: author autorizado aplicado, error de output, efectos/recibo/captura preservados, rechazo sin recibo y recuperación exacta sin duplicar cambios. |
| La guía podía inducir captura del propio registro/reporte en la ventana que está leyendo. | Para usage-record/report/export se usa capture_dir en JSON; se explica no añadir --capture-dir sobre la misma ventana. | Procedimiento corregido, sin cambiar las operaciones ni el presupuesto del diagnóstico. |
| Se llamó independiente a la comparación con context, que usa el mismo selector. | Se corrige a contraste diferencial contra la operación individual del mismo selector. | La comparación prueba integración/composición; no es un oráculo independiente de aplicabilidad. Las regresiones adversas previas conservan su función. |
| El recuento 14/14 y la procedencia limitada no bastaban por sí solos para demostrar conservación completa. | Auditoría de igualdad de identidades y contenido íntegro, resolviendo referencias de almacenamiento y la conversión declarada a importación no verificada. | 14/14 iguales: IDs, binding, etapas, errores, tiempos, métricas y materiales; no se eliminan campos para lograr igualdad. |
| El arreglo del resumen en lista solo tenía dos variantes públicas ensayadas. | Se amplía a compatible/operativo, details, compact y output. | Resumen, reporte y métricas exactos; archivo exportado íntegro y sin escrituras de consulta. |

## Resultado de las comprobaciones

- **Tres casos focales finales pasan**: error tras aplicación directa/recuperación;
  reporte ampliado; instrucciones/ejecución en ambos adaptadores. Dos son ampliaciones
  de casos anteriores y uno es nuevo: no se suman variantes internas como otros casos.
- La base anterior tenía 14 casos distintos; el acumulado justificado es **15**.
  Se reutilizan 12 y se repiten tres; no se afirma haber reejecutado los 15.
- **14/14 observaciones** del S1 anterior se contrastan por ID y contenido completo,
  con procedencia importada no verificada. Integridad no se convierte en autenticidad.
- Se repiten sobre app.py las aserciones reales de Hola y cero parámetros; su huella
  no cambia. Es un componente de revisión, no otro recorrido S1 completo.
- La prueba pública de fallo al exportar una consulta conserva query y failed;
  confirma la retención de etapas anteriores al error. Su comprobación con snapshots
  se registra separadamente; el primer sondeo no instrumentaba esa parte.
- Contrato estático del paquete válido, seis skills y mismo núcleo en adaptadores;
  siete artefactos idénticos entre dos builds corregidos. Diff revisado y sin errores
  de espacios; se conservan las advertencias normales de CRLF/LF de Git.

Se revisan G1/G2 mediante contraste diferencial, auditoría literal y regresiones
previas; G3/G4 mediante el núcleo idéntico y su cobertura anterior; G5 con prueba
real, evidencia y estados separados; G6 con recuperación y no duplicación tras
error; G7/G8 con snapshots, conservación e importación limitada; G9 con inventarios
exactos y builds reproducibles; G10 con doce fuentes protegidas intactas.
La regresión Windows anterior se reutiliza porque no cambia ningún script ni nombre
de archivo del runtime: no se declara una nueva ejecución Windows en este bloque.
Sonar/Dependency-Check siguen not-used en el fixture, no análisis superados.

## Fallo de ensayo conservado

La primera ejecución del nuevo caso omitió --receipt al recuperar una transacción
ya completada y falló. Era un error de llamada del ensayo: sin ese argumento, el
recuperador busca el journal pendiente que ya no existe. Se conserva el resultado
fallido; el caso corregido comprueba tanto ese rechazo como la recuperación con
el recibo exacto en ambos modos. No se cambia el núcleo para aceptar una recuperación
ambigua. Los otros dos casos de esa primera campaña ya pasaron.

## Paquete provisional vigente y reutilización

El anterior candidate-final queda como entrega histórica. El vigente es:

- Carpeta: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\review\candidate-corrected`.
- ZIP Codex SHA-256: `fc3305217a438e9a58e04250dbdbe48dddd115769980326f3be023f1ecbe8096`.
- Runtime: `28c7a5ffc6f25f1277f5b0125e2ee6d20238bb97360c3c0e483f2c4ec05e8f7b`.
- Fuente: `working-tree:6f45fa8293e075d48ce27d62d35fe7e1398c0f41937f6fe1863b26953e2e0148`.
- Canal `development-unreleased`, versión fuente 3.4.3: no es una publicación 4.0.

Frente al paquete S1 original cambian únicamente CLI-PRESENTATION.md, WORK-PREPARE.md,
dos módulos de prueba y package-integrity.json derivado. **Todos los scripts de
runtime son byte a byte idénticos**. Se justifica conservar la evidencia del S1 y
las regresiones no afectadas, y se comprueban las guías y pruebas actualizadas.
No se atribuye al paquete nuevo un S1 completo o una observación de host no ejecutados.
El paquete coincide con la fuente actual normalizada por el builder.

## Presupuesto, límites y continuación

Revisión acotada a 20 min, dentro de los techos existentes: 48 intentos, 8 h humanas,
12 h entorno; M6 dos variantes/cuatro horas. **Cero nuevos intentos completos**:
la cuenta conocida/reservada permanece 45/48 con H2/final/S8/contingencia intactos.
No se repite S1 para inflar la evidencia ni se cobran componentes como si fueran
un host observado. Todos los componentes, errores, builds e informe consumen tiempo.
El proxy actualizado de 29 turnos cerrados es 9,65570 h, no CPU/tiempo humano ni saldo
histórico certificado. No se suman procesos concurrentes como horas adicionales.
La valoración humana sigue diferida al uso real sostenido.

No se instala/registra/activa el paquete; no se hace commit/push ni publicación.
La limpieza rechazada en el bloque anterior continúa pendiente y preservada; no se
intenta otra eliminación en esta revisión. Los paquetes y logs previos se conservan.

**Antes de H2:** presentar este dictamen y el paquete revisado; preparar/admitir su
carga aislada con autorización separada y recuperación; después, pareja real A/B
en chats nuevos con instrucciones y runtime coherentes. Se mantienen los cuatro
umbrales conjuntos: B_out ≥10 % y ≥8.192 B menos, al menos una invocación menos,
B_flow sin aumento y cero confirmaciones redundantes nuevas. E3 no se infiere de
bytes y la percepción humana sigue diferida. No se inicia H2 ni V4-06 en esta revisión.

Evidencia recuperable: `C:\AI-Workspace\management\operations\lks-sdd-v4-h1-20261015\v4-05a\review`; focused-tests.log conserva el fallo inicial y
focused-final-tests.log su corrección, evidence-audit.json y source-reuse-verification.json
justifican las afirmaciones. corrected-package-verification.json fija el paquete exacto.

## Desviación de la cota local

El cierre y la validación estática final han rebasado la cota local de 20 min.
Último registro conservador: 21.14 min; detalle en resource-ledger.json.
No se amplía el presupuesto global ni se continúa a H2; cero intentos completos
adicionales. El saldo histórico global sigue sin certificar. Se registra la
desviación como tal, sin excluir costes de cierre ni presentarla como cumplimiento
de la cota local.
