# TASK-V3-002 · Identidades documentales y escritura recuperable

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento del almacenamiento**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-001](TASK-V3-001.md).

Requisitos de responsabilidad principal: REQ-EQT-016, REQ-EQT-017, REQ-EQT-019, REQ-EQT-040.
Casos de aceptación principales: AC-EQT-014, AC-EQT-015, AC-EQT-020, AC-EQT-040.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Conservación y coste de almacenamiento
Reutilizar la retención actual donde su contrato sea compatible: distinguir fuentes
activas, snapshots aprobados, evidencia e índices/cachés descartables. Ubicación/vigencia
de conservación se documentan según proyecto; no eliminar evidencia requerida por una
decisión o tarea activa ni introducir limpieza periódica automática.

Comprobar bytes, rutas largas, espacios/Unicode, renombres y modificaciones ajenas al
preview en las escrituras nuevas. Inventariar solo el ámbito protegido necesario y
medir coste de lectura junto a 010; el índice no permite omitir altas de reglas globales.
Estos casos concretan integridad/recuperación de AC-EQT-040/050/065/094, sin crear otra
batería de mantenimiento o almacén central.

## Encargo y límites
Dar identidad permanente a cada elemento nuevo y conservar escrituras e historia de forma
recuperable. Evitar contadores centrales y conflictos de un índice tratado como autoridad.
No convertir todavía fuentes v2 ni resolver por heurística entidades heredadas ambiguas.

## Entregables e interfaces
- Añadir `scripts/v3_storage.py`; reutilizar las utilidades seguras de
  `v2_storage.py` sin alterar su semántica. Incorporar snapshots y journal de operación
  al contrato v3, preservando precondiciones y recuperación local.
- UUIDv4 generado una vez por entidad; rutas inequívocas, aliases secundarios y
  referencias por UID completo, calificadas por proyecto si cruzan proyectos.
- Índice reconstruible desde Markdown reconciliado. Cache/índice no deciden autoridad.
- Conservación de documentos aprobados e informes recuperables con inventario/digest;
  no guardar credenciales. Coordinar el tratamiento de evidencia con 008/012.
- Pruebas focales en `tests/`, usando la infraestructura de
  `tests/test_v2_storage.py` y `test_v2_retention.py` como referencia.

## Aceptación y evidencia
Dos clones crean elementos con el mismo alias sin confundir identidades. Reintentar una
operación conserva los UID y no duplica decisiones. Reconstruir el índice recupera las
relaciones sin elegir la última copia. Una interrupción en cada punto material de
escritura permite terminar la operación exacta o restaurar su origen sin perder cambios
posteriores; una base cambiada exige revaluar. El contenido aprobado y la evidencia
siguen recuperables tras eliminar una rama; si faltan, se declara ausencia.
Entregar comparación de inventarios, fixtures de colisión, recuperación y referencias.

## Riesgos y revisión
No prometer atomicidad entre clones ni entre todos los archivos. Revisión de almacenamiento
y evidencia: no introducir una segunda fuente normativa. Lectura adicional: técnica §§3–5,
6.4 y 9.2; almacenamiento/retención actual, solo las funciones reutilizadas.
