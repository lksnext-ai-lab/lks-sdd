# TASK-V3-011 · Adopción y migración: diagnóstico y vista previa

Plan: [v3-plan-02](../PLAN.md). Estado: **pendiente; no autorizada para ejecutar**.
Responsabilidad: **Mantenimiento de migración**; persona/agente por asignar.
Inicio del trabajo independiente: [TASK-V3-001](TASK-V3-001.md).
Dependencias para cerrar: [TASK-V3-005](TASK-V3-005.md).

Requisitos de responsabilidad principal: REQ-EQT-037, REQ-EQT-055, REQ-EQT-065.
Casos de aceptación principales: AC-EQT-037, AC-EQT-063, AC-EQT-088.

Leer las [reglas de ejecución](../EXECUTION.md) y las obligaciones literales asignadas
por la [matriz](../TRACEABILITY.md), incluidas sus dependencias aplicables.
La ficha concreta el trabajo; no sustituye la propuesta aprobada.

## Adopción sin SDD, distinta de migración
Incluir el recorrido de sistema existente sin contrato SDD: inspección estática acotada
por fuentes y finalidad, observaciones con procedencia, intención por confirmar y cobertura
parcial visible. No tratar ausencia documental como ausencia funcional.

Adaptar `v2_adoption.py` mediante `scripts/v3_adoption.py` solo en la parte necesaria.
003 prepara configuración, 004 aplica documentos y 007 aporta rama/base. No inventar
responsables, aceptación previa ni un formato v2 intermedio. Contribuye a 008/037/048
y a R1; la migración 2.x conserva su matriz y su propia autorización.
La escritura de adopción y su cierre exigen **base-git-local** de 007; el diagnóstico
de solo lectura puede avanzar sin ese resultado, mostrando la limitación.

Iniciar pronto el inventario y las muestras de orígenes publicados. Cada fuente real
admitida tiene disposición verificable; historial/revisiones solo equivalentes se
agrupan con una justificación documentada, no multiplicando fixtures idénticos por
número de release. Congelar muestras y resultados esperados antes de escribir la conversión.

## Encargo y límites
Diagnosticar orígenes 2.x y preparar conversión revisable sin modificar el consumidor.
La ruta depende de formato, método y runtime reales, no del prefijo de la versión.
Cubrir schema 2.0/métodos 2.0.0 y 2.1.0 con variantes documentadas; 1.x mantiene su ruta a v2.

## Entregables e interfaces
- Añadir parte de diagnóstico/preview de `scripts/v3_migration.py`, matriz de orígenes
  y muestras reproducibles bajo `tests/fixtures/v3-migration/`.
- Inventariar las revisiones publicadas que documente el repositorio y su formato/runtime.
  Añadir muestras por diferencias documentales reales; marcar probado/pendiente/desconocido.
- Disposición de cada documento/adjunto/evidencia/personalización: conservado, convertido,
  reconciliación necesaria o fuera del ámbito con motivo. Ninguna fuente queda sin tratar.
- Preview exacto, mapa único de identidad/referencias y valores propuestos de proceso.
  UID existentes conservados; nuevos UID fijados una vez en la vista previa.
- Resumen antes/después: automático, conservado, decisiones y tareas continuables,
  indicando aprobación de negocio frente a autorización operativa que debe renovarse.

## Aceptación y evidencia
Diagnóstico no cambia bytes, código, referencias ni runtime. Origen desconocido o
extensión normativa incomprendida no se transforma por cambiar encabezados. Identidad
ambigua se conserva y explica. La vista anticipa decisiones mínimas y no pide revisar
cada archivo/historia cerrada. Un plan abierto no se regenera. Se explican por separado
compatibilidad probada, conservación y continuidad pendiente.
Entregar matriz con procedencia de muestras, previews/inventarios y pruebas de no escritura.

## Riesgos y revisión
La ausencia de una muestra de una revisión limita la declaración de soporte; se debe
completar la ruta o mantener pendiente ese origen, no ocultarlo. Revisión de compatibilidad
y gobierno. Lectura adicional: funcional §11 completo, técnica §9 completo, migración v2.
