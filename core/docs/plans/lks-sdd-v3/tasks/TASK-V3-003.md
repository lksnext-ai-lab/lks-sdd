# TASK-V3-003 · Proceso, miembros y autoridad

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento del modelo de proyecto**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-002](TASK-V3-002.md).

Requisitos de responsabilidad principal: REQ-EQT-001, REQ-EQT-002, REQ-EQT-003, REQ-EQT-006, REQ-EQT-008, REQ-EQT-010, REQ-EQT-027, REQ-EQT-029, REQ-EQT-030, REQ-EQT-042, REQ-EQT-062.
Casos de aceptación principales: AC-EQT-001, AC-EQT-005, AC-EQT-006, AC-EQT-007, AC-EQT-008, AC-EQT-009, AC-EQT-010, AC-EQT-027, AC-EQT-029, AC-EQT-030, AC-EQT-041, AC-EQT-042, AC-EQT-076, AC-EQT-077, AC-EQT-078.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Entrada al proyecto y primer gobierno
Preparar explícitamente las tres entradas: proyecto nuevo, sistema existente sin SDD y
consumidor SDD con formato conocido. Una consulta solo diagnostica y no inicializa.

En un proyecto nuevo, presentar configuración y autoridad inicial declarada para decisión
agrupada, con su procedencia y garantía real; no adivinar administradores, cuentas o no
uso. Esa primera decisión queda ligada a la inicialización concreta que aplica 004;
las revisiones posteriores se validan contra la autoridad previa vigente.
En un sistema con gobierno ya documentado, reconciliarlo antes de sustituirlo; una
política candidata no puede usarse como prueba de su propia autoridad.

Entregar a 004/011 configuración propuesta o desconocidos concretos. Probar arranque,
cancelación sin activar política y evolución individual→equipo dentro de casos
001/008/041/076. La configuración inicial se mide separada del cambio pequeño ya configurado.

## Encargo y límites
Implementar configuración mínima, evolución del proceso y miembros con autoridad explícita.
Tres recorridos editables: individual breve, equipo coordinado y equipo con revisión
separada; fase de creación/entrega/mantenimiento como dimensión distinta.
No elegir personas, separación de funciones, herramientas o no uso por inferencia.

## Entregables e interfaces
- Añadir `scripts/v3_policy.py`, plantillas y ejemplos de los tres recorridos.
  Datos: pasos, funciones, controles, vigencia, autoridad y cambios de política.
- Resolver identidad declarada/observada/autenticada con procedencia; vinculación de
  operador local a la sesión, sin credenciales ni “usuario activo” compartido.
- Validar acumulación/separación de funciones, altas/bajas/cuentas, revisión de controles
  y efecto sobre trabajo abierto. Mantener los hechos históricos atribuidos.
- Resolver garantías del método/permisos → autoridad vigente conocida → política
  fijada de petición → excepción acotada. Conflictos requieren sustitución explícita.
- Proveer a 005/006/008 decisiones y diagnósticos por alcance; persistir mediante 002.

## Aceptación y evidencia
Un proyecto solo y otro por especialidades usan los mismos datos sin pasos ficticios.
Cambio de nombre/cuenta no duplica miembros; baja de una función invalida actuaciones
futuras afectadas. Una política candidata no se autoautoriza. El paso a equipo/Sonar
declara alcance y vigencia sin reiniciar todas las peticiones. Una revisión independiente
sin revisor habilitado o un flujo imposible se diagnostican antes de activarse.
Identidad ambigua pide el dato mínimo; Windows/Git no constituyen prueba de persona.
Entregar fixtures de los tres perfiles, evolución/revocación y precedencia.

## Riesgos y revisión
Revisión conjunta de gobierno e identidad. Las condiciones de política son predicados
conocidos; no evalúan expresiones ejecutables del repositorio. Lectura adicional:
funcional §§5 y 9; técnica §§5.1 y 8.
