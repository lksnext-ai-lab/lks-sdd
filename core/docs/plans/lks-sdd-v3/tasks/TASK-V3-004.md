# TASK-V3-004 · Propuesta exacta, aprobación y planificación

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de definición y planificación**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-002](TASK-V3-002.md).
Dependencias para cerrar: [TASK-V3-003](TASK-V3-003.md).

Requisitos de responsabilidad principal: REQ-EQT-031, REQ-EQT-050, REQ-EQT-051, REQ-EQT-052, REQ-EQT-053, REQ-EQT-060, REQ-EQT-061.
Casos de aceptación principales: AC-EQT-031, AC-EQT-055, AC-EQT-057, AC-EQT-058, AC-EQT-059, AC-EQT-060, AC-EQT-061, AC-EQT-072, AC-EQT-073, AC-EQT-074, AC-EQT-075.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Autoría operativa y primer recorrido
Añadir la autoría v3 necesaria en `scripts/v3_authoring.py`, reutilizando los patrones
de `v2_authoring.py`: inicializar documentos/índice, crear petición/propuesta, registrar
la decisión observada y materializar PLAN/TASK mediante preview y escritura recuperable.
Una biblioteca que solo valida fixtures no satisface estos entregables.

003 aporta configuración y autoridad, 007 la condición real de rama/base y 002 aplica
los cambios. Antes de escribir y cerrar autoría debe estar acreditado el resultado
intermedio **base-git-local** de 007; no se exige su integración de equipo completa.
Preparar primero las funciones y pruebas de componente; R1 acredita la
integración con esos productores antes de anunciar el recorrido como utilizable.
Conectar con 014 cada operación ya real, sin esperar a toda la migración.

Probar que definir no genera código ni tareas comprometidas antes de aceptar la propuesta,
y que crear un segundo cambio reutiliza el proceso vigente sin otro cuestionario inicial.
La adopción sin SDD consume esta autoría desde 011; no se resuelve falsificando un origen v2.

## Encargo y límites
Conectar propuesta funcional/técnica exacta, decisión explícita y PLAN/TASK completo.
El resumen debe permitir entender qué cambia; las huellas se gestionan internamente.
No registrar aprobación desde silencio/comentarios ambiguos ni generar planes ejecutables
de porciones pendientes. Aprobar contenido no autoriza código.

## Entregables e interfaces
- Añadir `scripts/v3_approval.py` y `v3_planning.py`, schemas/plantillas acordados en 001.
  Reutilizar patrones de cobertura de `v2_change_control.py`/`v2_lifecycle.py`.
- Unidades funcionales/técnicas/contratos, descriptor del paquete y snapshots exactos.
  Progreso/localización fuera del contenido normativo aprobado.
- Composición con revisiones distintas, validez por contenido y dependencias; análisis
  de impacto que conserve decisiones independientes y presente incertidumbres.
- Plan con alcance, responsable, aceptación, pruebas, tecnología aplicable, contratos
  internos, contribuyentes, integración y dependencias sin ciclos.
- Aprobación de plan y autorización pueden recogerse juntas sobre un objeto concreto;
  conservar su diferencia y el alcance expresamente autorizado.

## Aceptación y evidencia
Una lista genérica de temas no está lista para validar. La ficha muestra antes/después,
solución, ejemplos, límites y consecuencias. F@1/T@2 reutiliza F@1 solo si su contrato
sigue cubierto. Una interfaz cambiada afecta consumidores aunque sus bytes no cambien.
No se declara equivalencia normativa por juicio del modelo. Una aceptación parcial
solo habilita el plan correspondiente; faltan cobertura/integración o hay ciclos →
diagnóstico. No se crea nueva aprobación al cambiar solo progreso/localización.
Entregar fixtures de revisiones/parcialidad/cobertura y fichas humanas a revisar en 017.

## Riesgos y revisión
Revisión funcional y técnica diferenciadas según el caso. La suficiencia del resumen
requiere revisión semántica, además de checks de hashes. Lectura adicional: funcional
§13 y recorridos; técnica §4 completo; continuidad SPEC/PLAN/TASK actual.
