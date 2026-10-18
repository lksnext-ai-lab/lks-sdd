# V4-11 — Destino de reglas e instrucciones

La centralización retira repeticiones, no obligaciones. Las fuentes previas exactas
de las seis skills, sus referencias v3 y la guía común quedan en la evidencia
`v4-11/before/`. Se conservan nombres, descripciones, invocación implícita y las
rutas v2/1.5. Esta matriz es una revisión de destino y cobertura: no acredita
comprensión humana ni cumplimiento semántico automático de todas las instrucciones.

| Regla o condición conservada | Destino vigente | Control o evidencia |
|---|---|---|
| Markdown canónico, índice derivado y ausencia de índice sin inicialización implícita | Seis SKILL.md y V3-COMMON | Contrato estático, enlaces y carga del contrato. |
| Método, colaboración, runtime compatible y migración solo autorizada | V3-COMMON; adopt-existing/references/v3.md; V3-MIGRATION | require_current, runtime_doctor y consultas separadas de escritura. |
| Identidad y autoridad actuales; Git/Windows/chat no las conceden | V3-COMMON; continuidad de implement/assess-readiness | operator, task_authority y preparación; guards previos conservados. |
| Datos observados, CLI compartida, apply autorizado y output revisable | V3-COMMON; V3-OPERATIONS bajo demanda | Parser y límites nativos; se elimina el bloque repetido de seis referencias. |
| Propuesta validada antes del plan y las tareas ejecutables | define/references/v3.md; V3-COMMON; specifications/planning | proposal_ready, author y plan_coverage; V4-10 reutilizado. |
| Cobertura antes de código, decisiones aplazadas y porciones independientes | implement/SKILL.md; V3-COMMON | Preparación, incertidumbre crítica y autoridad por porción. |
| Alcance explícito, legado acotado y clasificación solo acreditada | define/adopt-existing v3; DOCUMENT-CONTEXT bajo condición | v3_scope, v3_context y gobierno; no clasificación por carpeta. |
| Obligaciones literales, negaciones, globales, dependencias y adjuntos | V3-COMMON; contexto de la tarea | Selector y observación visual; hashes/resúmenes no sustituyen fuentes. |
| Evento cambiado, compactación o chat nuevo exige recarga pertinente | V3-COMMON; USER-DECISIONS | Perfiles, recursos por evento y huellas recargadas; no caché de confianza. |
| Presentar contenido y registrar respuesta con receipt/presented | V3-COMMON; USER-DECISIONS bajo decisión | Presentation guard y regresión real de recibos; no segunda firma por registro. |
| Preparación compuesta solo informativa y fallback por capacidad | assess-readiness/implement/verify v3; WORK-PREPARE | Las consultas no aplican; integridad inválida no permite eludir bloqueos. |
| Inicio y resultados agrupados conservan efectos y controles | implement/verify v3; WORK-OPERATIONS por operación | work-continue y work-record-results; ninguna decisión ajena inferida. |
| Actividad optativa sin éxito/porcentaje ficticio; interrupción y recuperación | V3-COMMON; WORK-ACTIVITY bajo condición | Superficies ya verificadas de V4-07A; AC-40 sigue pendiente. |
| Pruebas reales, sujeto exacto, calidad y revisión independiente | implement/verify v3; verification | Evidence/analysis, controles y guards vigentes; no not-run como passed. |
| Defecto, cambio de acuerdo, nueva petición y rechazo conservado | implement/define/verify v3; corrections | V4-10, nuevas pruebas y aceptación separada. |
| Rama/base, actualización compartida, offline y cambios ajenos | V3-COMMON | Git/coordination y transacciones nativas; sin bloqueo distribuido. |
| Ventana diagnóstica desde inicio, sobres completos, huecos y procedencia | V3-COMMON; diagnóstico específico de las seis referencias | Capture/usage; no copiar la vista breve ni inventar métricas del host. |
| Sonar/Dependency-Check separados; error/no uso/no aplicabilidad/éxito distintos | V3-COMMON; implement/verify y verification | Decisión por control y validación de resultados; no Sonar por comando. |
| Excepciones conservan fallo, responsable, motivo, alcance, efecto y vencimiento | V3-COMMON; exceptions-continuity bajo condición | Operaciones y guards previos; no autorización retroactiva. |
| Hito claro, decisiones reutilizadas, efectos separados y acciones externas autorizadas | V3-COMMON; USER-DECISIONS y external-delivery | Interventions y contenido presentado; percepción/aceptación del host pendientes. |

`instruction_refs` conserva su llamada anterior y admite `event` para añadir solo
WORK-PREPARE o WORK-OPERATIONS en las tres operaciones existentes. No carga todas
las guías ni añade perfiles, comandos, hooks o agentes. Ambos adaptadores contienen
los mismos recursos; la ejecución técnica desde un paquete no es aceptación del host.
