# TASK-V3-005 · Transiciones, dependencias y excepciones

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento del motor de proceso**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-004](TASK-V3-004.md).

Requisitos de responsabilidad principal: REQ-EQT-005, REQ-EQT-009, REQ-EQT-032, REQ-EQT-041, REQ-EQT-043, REQ-EQT-047.
Casos de aceptación principales: AC-EQT-032, AC-EQT-034, AC-EQT-043, AC-EQT-044, AC-EQT-045, AC-EQT-046, AC-EQT-050, AC-EQT-054.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Coste y separación del evaluador
El evaluador de transiciones es una función sobre hechos tipados; no ejecuta Sonar,
fetch, búsqueda recursiva ni preguntas al usuario por cada invocación. Las operaciones
materiales obtienen/comprueban los hechos mediante sus propietarios y pasan una vista
vigente; antes de mutar se verifican las precondiciones pertinentes.

Puede desarrollarse contra ejemplos del contrato desde 001, pero la transición real
solo se acredita al integrar autoridad, decisiones, base y evidencia. Las dependencias
de cierre de esta ficha se mantienen. Para un bloqueo, producir causa mínima y trabajo
independiente habilitado; evitar repetir el mismo diagnóstico completo en cada skill.

## Encargo y límites
Crear el evaluador compartido del proceso con transiciones ordinarias y excepcionales.
Separar implementado, verificado, cerrado, integrado y aceptado. Incluir pausa, corrección,
cancelación y replanificación; no inferir cumplimiento de una etiqueta “done”.

## Entregables e interfaces
- Añadir `scripts/v3_workflow.py`; entrada: modelo, revisión de política, autoridad,
  asignación, aprobaciones, dependencias, Git/evidencia y excepción pertinente.
- Salida estructurada: avanzar, necesita decisión o incumplimiento; causas, responsable,
  alcance y precondiciones. Los nombres públicos se concretan con 001.
- Dependencias de contrato validado, resultado disponible o verificado, con predicado
  y artefacto exactos; continuación independiente sin modificar el cierre requerido.
- Excepción con regla, causa, ámbito, validador, vigencia y efecto. Cierre con reservas
  conserva fallo/omisión y condiciones de los consumidores.
- Persistencia con revisión comprobada mediante 002, y confirmación antes de anunciar
  finalización. Regularización actual de una desviación, sin aprobación retroactiva.

## Aceptación y evidencia
La excepción vencida/revocada/ajena no habilita una transición nueva. Un caso no previsto
puede presentarse a quien tenga función competente, sin inventar terceros. Aplazar un
análisis no lo convierte en aprobado ni autoriza todo cierre. Un cambio entre evaluación
y escritura impide aplicar la base obsoleta; el trabajo previo permanece recuperable.
Un control pendiente no bloquea una dependencia que solo exige contrato ya validado.
Entregar tabla de transiciones y pruebas negativas de atajos, ciclos, reservas y carrera.

## Riesgos y revisión
Este evaluador debe ser común a inicio, reanudación, verificación, cierre e integración;
009/014 no pueden saltárselo. Revisar con gobierno y ejecución. Lectura adicional:
funcional §§5, 7 y excepciones; técnica §§5–5.2 y 7.
