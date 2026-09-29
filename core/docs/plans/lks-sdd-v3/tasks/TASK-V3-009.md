# TASK-V3-009 · Implementación, corrección y cierre de tareas

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento del ciclo de ejecución**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-005](TASK-V3-005.md).
Dependencias para cerrar: [TASK-V3-007](TASK-V3-007.md).

Requisitos de responsabilidad principal: REQ-EQT-022, REQ-EQT-028, REQ-EQT-035.
Casos de aceptación principales: AC-EQT-021, AC-EQT-035.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Primer ciclo ejecutable e invalidación
Priorizar R2 individual con política concreta; ampliarlo a equipo/relevo cuando 006/007
estén integradas. Controles no utilizados se deciden en el consumidor de prueba, no
se eligen automáticamente para simplificar la demostración.

Un cambio de código posterior al análisis obliga a evaluar de nuevo sus entradas
antes de cerrar; probar también cambios locales sin commit y resultado llegado tarde.
Conservar declaración tecnológica y obligaciones existentes aplicables del alcance,
incluida evidencia de integración/persistencia cuando proceda. El nuevo proceso no las
sustituye por Sonar o Dependency-Check ni rebaja la verificación actual.

## Encargo y límites
Conectar autorización, inicio/reanudación, implementación, controles, correcciones,
verificación y cierre. Ejecutar solo la porción autorizada con su tecnología y contrato
literal aplicables. No posponer el primer análisis obligatorio a la validación del PR.

## Entregables e interfaces
- Añadir `scripts/v3_lifecycle.py` / `v3_verification.py`; reutilizar patrones de
  `v2_lifecycle.py`, `v2_quality.py`, `v2_verification.py` y `v2_controls.py`.
- Evaluador 005 único en cada transición material; consumir asignaciones 006, Git 007,
  análisis 008 y decisiones 004, con precondiciones sobre la base realmente modificada.
- AUTH/EXEC/CKPT/EVID trazan operador, porción, política, base, resultados y revisión
  exacta, sin un recibo por comando. El diff real se contrasta con el alcance autorizado.
- Hallazgo → corrección → nueva comprobación. Distinguir deuda previa, falso positivo,
  riesgo aceptado y alcance nuevo; lo nuevo vuelve a propuesta/plan afectados.
- Cierre ordinario exige controles aplicables terminales; reserva/excepción conserva
  resultado técnico, obligaciones pendientes y efectos sobre consumidores.

## Aceptación y evidencia
Ejercicio completo que implementa un cambio de prueba, detecta un fallo de calidad,
corrige dentro de alcance y registra análisis vigente antes de cerrar. Reanudar conserva
autorización válida y análisis aplicable sin repetirlos por cambio de chat. Corrección
fuera de alcance se presenta para decisión. Pruebas técnicas, integración y aceptación
funcional son estados separados. Edición manual a terminado no evita el guard.
Entregar diff del consumidor de prueba, traza de decisiones y evidencia del ciclo,
incluyendo casos de herramientas no utilizadas y excepción válida.

## Riesgos y revisión
No heredar sin revisión atajos v2 basados solo en “done”. Revisión de ejecución/calidad;
016 comprueba la funcionalidad integrada real. Lectura adicional: obligaciones de cierre
y cambios vivos, técnica §§4–7 y flujo actual SPEC/PLAN/TASK.
