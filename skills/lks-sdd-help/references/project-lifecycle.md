# Ciclo de vida y rutas

## Aplicación nueva

1. Encuadre y clasificación.
2. Descubrimiento y alcance.
3. Especificación.
4. Diseño de experiencia e interfaz, cuando resulte aplicable, incluida validación humana de prototipos visuales.
5. Diseño técnico y decisiones.
6. Gobierno de entrega: modelo, versionado, Git, entornos, CI/CD, despliegue y recuperación.
7. Arquitectura por unidades y bindings de perfiles exactos.
8. Resumen automático de cierre de especificación.
9. Propuesta, confirmación humana y validación de cobertura integral `PLAN/REL/TASK`.
10. Readiness simultáneo de especificación, planificación, porción y automatización.
11. `AUTH-###` delimitada, implementación con `EXEC/CKPT` y verificación G3/G4 con evidencia exacta.

El sistema resume la definición tras el encuadre, al cerrar un bloque funcional material, al consolidar solución, UX o decisiones técnicas, antes de readiness, cuando se reabre una dimensión suficiente, al pausar y cuando la persona lo solicita. Evita repetir el snapshot tras cambios menores y declara siempre fase y alcance o incremento. Los estados `unknown`, `partial`, `sufficient` y `not-applicable: motivo` se refieren al alcance indicado; no forman un porcentaje ni equivalen a aprobación.

## Repositorio existente

Empieza con preflight e inventario estático de solo lectura. Después se validan intención y reglas de negocio, se reconcilian realidad y deseo, se elige entre documentación, normalización progresiva o modernización planificada y, solo con autorización, se materializa una baseline documental aditiva. La estrategia elegida no autoriza cambios funcionales durante la adopción.

## Estados separados

- especificación: `ready`, con pendientes no bloqueantes o bloqueada;
- planificación: `not-started`, `partial`, `complete` o `stale`, más integridad válida/inválida;
- porción TASK: `ready`, bloqueada o no seleccionada;
- autorización: ausente, autorizada, revocada u obsoleta;
- implementación: no iniciada, en curso, bloqueada o completada;
- verificación y entrega: no iniciadas, parciales, superadas con evidencia o bloqueadas.

El bloqueo de una parte no paraliza trabajo independiente y un estado listo no equivale a autorización de implementación.

Readiness muestra estos ejes juntos. Una tarea lista no prueba cobertura integral. La acción `ready-to-implement` solo aparece cuando especificación, porción y automatización son favorables, la política de planificación lo permite y existe una autorización vigente; una limitación en cualquier eje no reescribe los demás ni selecciona otra pila.

## Handoff y evidencia

La fase `preimplementation` exige una cadena no vacía desde requisitos confirmados hasta criterios, decisión o no aplicabilidad motivada, incremento y pruebas. La fase `verification` añade evidencia ejecutada y aplicable. Los elementos rechazados, sustituidos o retirados se conservan como historial, pero no alimentan el contrato activo.

Una tarea recorre `backlog → ready → in-progress → in-review → done`; `blocked` y `cancelled` son estados explícitos. La tabla resume; la ficha conserva detalle e historial. `done` exige evidencia ligada a revisión, build, artefacto, entorno y gates. El modelo de entrega puede cambiar durante la vida del producto mediante un nuevo `CHG-###` y una transición efectiva, sin reescribir releases o evidencias anteriores.

Una ejecución crea un checkpoint inicial y lo actualiza al empezar, terminar o bloquear tareas y antes de pausas. Al reanudar se valida el repositorio; según las divergencias se continúa, reconcilia o replantea. Un `PCH-###` conserva cambios de alcance o contrato y vuelve obsoletas únicamente las huellas, tareas y autorizaciones afectadas.

## Evolución del contrato

Las rutas nuevas y adopciones materializadas con 0.14.1 usan método 1.5.0 y esquema 1.5. Los proyectos 1.0/1.1/1.2/1.3/1.4/1.5 continúan en compatibilidad. Cada salto es explícito y reversible. El renderer histórico `1.2 → 1.3` conserva método 1.3.0/plugin 0.9.1; `1.3 → 1.4` añade tracking pendiente; `1.4 → 1.5` añade la política de reporting sin consultar Jira, inferir workflow, publicar comentarios o transicionar tareas.
