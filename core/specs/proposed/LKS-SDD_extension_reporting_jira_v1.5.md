# LKS-SDD — extensión propuesta 1.5: reporting Jira por hitos

Estado: propuesta candidate, no canónica  
Versión de método: 1.5.0  
Plugin de referencia: 0.11.0  
Fecha: 2026-08-26

## 1. Propósito

Esta extensión añade una experiencia opcional de reporting operativo en Jira durante implementación y verificación. No cambia la autoridad del método: los Markdown versionados, las autorizaciones, ejecuciones, checkpoints y evidencias locales siguen gobernando el trabajo. Jira es una vista para coordinación humana, nunca la fuente de alcance, avance, verificación o aprobación.

## 2. Decisiones de producto

Antes del primer plan se elige `repository-only`, `jira-hybrid` o pausa. Jira-only no existe. La opción local MUST conservar una experiencia completa, profesional y sin solicitudes de conexión Atlassian.

En `jira-hybrid` se confirman por separado:

- scope `projection-only` o `milestone-reporting`;
- gate `advisory` o `required-before-execution`;
- política de comentarios `milestones-only` cuando aplica;
- mappings de workflow por estado local, usando status IDs observados.

El producto SHOULD recomendar `milestone-reporting` con gate `advisory` cuando el objetivo sea visibilidad sin acoplar la ejecución local a la disponibilidad de Jira.

## 3. Autoridad y orden canónico

Toda mutación Jira MUST estar precedida por el hecho local durable que representa. El motor local MUST construir un preview determinista desde una única TASK y una fuente existente `TASK/EXEC/CKPT/PROB/EVID`. Una respuesta de Jira MUST NOT modificar automáticamente TASK, AUTH, EXEC, CKPT, evidencia, dependencia o decisión.

La proyección de campos y el reporting de hitos son ciclos separados. Un proyecto puede usar solo proyección. Pausar reporting no suspende la proyección, no borra recibos y no invalida el contrato local.

## 4. Eventos soportados

Los eventos iniciales son `started`, `progress`, `blocked`, `resumed`, `in-review`, `verification-pending`, `verification-failed` y `done`. Cada evento MUST corresponder al estado local admitido. `blocked` exige un problema abierto; `verification-failed` exige evidencia; `done` exige evidencia local verified y enlazada a la TASK.

No se publican eventos por cada archivo, comando, test, mensaje de chat o actualización menor. Los comentarios MUST ser resúmenes saneados de estado, progreso, salud, fuente, checkpoint, bloqueos, evidencia referenciada y siguiente acción. MUST NOT incluir logs completos, secretos, datos personales detectables, rutas absolutas, worklogs o conversaciones.

## 5. Preview, confirmación y recibos

`preview-event` produce un comentario y, solo si existe un mapping confirmado, una transición opcional. Debe incluir marker namespaced, event hash, preview hash, identidad Jira y disposición `write`, `noop`, `awaiting-result` o `reconciliation-required`.

Una persona MAY confirmar el preview completo una sola vez. `authorize-event` MUST persistir antes de escribir un recibo `SYNC-###` independiente por comentario o transición. La confirmación no ejecuta Jira. Cada operación MUST ejecutarse y releerse por separado, y `record-event-result` MUST cerrar su recibo con la identidad y marker o status ID observados.

La transición requiere status ID objetivo confirmado localmente y transition ID observado en una lectura Jira fresca. Los nombres de estado no autorizan una transición.

## 6. Idempotencia, fallo y reconciliación

El marker estable del evento evita comentarios duplicados. Un evento ya registrado con el mismo hash produce `noop`. Un recibo autorizado bloquea otra escritura hasta registrar resultado. Un hash distinto para la misma identidad de evento exige reconciliación.

Los resultados son `succeeded`, `failed`, `conflict` o `uncertain`. Ante `uncertain` el agente MUST NOT reintentar a ciegas. Debe realizar una lectura autorizada y registrar `reconcile-event` como un nuevo recibo append-only anclado en el anterior. Nunca se reescribe historia para aparentar éxito.

## 7. Degradación y privacidad

Con gate `advisory`, indisponibilidad, permiso insuficiente, reporting pausado o fallo externo se informa como degradación y la ejecución local válida puede continuar. Con `required-before-execution`, el bloqueo se aplica únicamente en el límite confirmado y no convierte Jira en evidencia técnica.

El bundle sigue siendo skills-only. Atlassian Rovo se instala, conecta, autentica y autoriza de forma independiente. LKS-SDD no incluye cliente Jira, MCP, conector, credencial, hook, app ni agente ejecutable.

## 8. Migración y compatibilidad

La migración 1.4 → 1.5 es explícita, reversible y de un salto. `repository-only` se conserva con reporting no aplicable. `jira-hybrid` se conserva en `projection-only` con su política anterior; no se infieren reporting, mappings, comentarios, transiciones ni autorizaciones. Los recibos históricos se preservan. Una ejecución reanudable o recibos no resueltos bloquean la migración.

## 9. Evidencia candidate

La candidate debe demostrar offline contrato, migración, autoridad, idempotencia, recibos, reconciliación, privacidad y experiencia local. La interoperabilidad real con Rovo/Jira y la aceptación humana permanecen `not-run` hasta un piloto autorizado; no pueden presentarse como superadas por pruebas deterministas.
