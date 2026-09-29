# TASK-V3-013 · Estado del recorrido y orientación al usuario

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de experiencia de uso**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-010](TASK-V3-010.md), [TASK-V3-012](TASK-V3-012.md).

Requisitos de responsabilidad principal: REQ-EQT-012, REQ-EQT-034, REQ-EQT-044, REQ-EQT-045, REQ-EQT-046, REQ-EQT-048.
Casos de aceptación principales: AC-EQT-011, AC-EQT-047, AC-EQT-048, AC-EQT-049, AC-EQT-051, AC-EQT-053, AC-EQT-056.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Diseño de uso desde el principio
Preparar ejemplos de mensajes y transiciones desde 001, contrastados con las obligaciones
aprobadas: configuración, propuesta lista para validar, plan, espera técnica, relevo y
cierre. No esperar a que todos los módulos estén terminados para detectar confusión.

Integrar cada mensaje cuando su productor persista hechos reales; los ejemplos no son
evidencia de ejecución. El cierre de 013 necesita 012 para comprobar migración aplicada,
recuperación y continuidad, además de la vista previa de 011.

Medir con 017 decisiones y tamaño de lectura por recorrido. La vista inicial recomienda
una acción fundada y permite detalle; no obliga a abrir fichas vacías ni a elegir entre
muchas opciones equivalentes. No pedir validación por lecturas ordinarias autorizadas.

## Encargo y límites
Explicar el estado real dentro del proceso de cada petición, con pasos hechos, pendientes,
quién debe actuar y siguiente acción. Mantener agilidad y claridad en consultas, hitos y
reanudación; no presentar un porcentaje global engañoso.

## Entregables e interfaces
- Añadir `scripts/v3_query.py` / `v3_guidance.py`; compartir salida estructurada de 005
  con mensajes de las seis skills, sin un estado paralelo de negocio.
- Vistas por proyecto/petición/TASK: ruta completa, excepciones, no aplicable, parcial,
  espera técnica, revisión humana y actualidad local/remota observada.
- Consulta histórica con actor/función, cambios de cuenta, decisiones, ramas,
  contribuciones, evidencia y fuentes; mostrar lo desconocido, no rellenarlo.
- Mensaje de hito solo tras persistencia confirmada: resultado, situación, pendientes
  y acción. Si la continuación ya está autorizada, explicarlo y continuar.
- Recomendaciones justificadas; excepciones repetidas pueden sugerir revisar política,
  sin modificarla ni programar vigilancia.

## Aceptación y evidencia
Un proyecto con peticiones distintas no parece estar en una única fase. Otro chat
reconstruye política y pendientes sin volcar códigos internos. Cierre con reservas
explica límites y no exige otro “adelante” si ya puede continuar. Una consulta amplia
no carga todos los expedientes históricos. Es posible reconstruir quién hizo/validó
cada porción con el grado de certeza real. Preparar ejemplos comparables para 017,
pruebas de correspondencia con hechos y revisión humana del lenguaje.

## Riesgos y revisión
No reducir claridad a snapshots textuales o cantidad de caracteres. Un comando que acaba
no implica un paso terminado. Revisión funcional de mensajes y técnica de procedencia.
Lectura adicional: funcional §9, recorridos §13 y técnica §6.
