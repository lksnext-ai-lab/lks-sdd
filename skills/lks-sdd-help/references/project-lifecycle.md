# Ciclo de vida y rutas

## Aplicación nueva

1. Encuadre y clasificación.
2. Descubrimiento y alcance.
3. Especificación.
4. Diseño de experiencia e interfaz, cuando resulte aplicable, incluida validación humana de prototipos visuales.
5. Diseño técnico y decisiones.
6. Gobierno de entrega: modelo, versionado, Git, entornos, CI/CD, despliegue y recuperación.
7. Arquitectura por unidades y bindings de perfiles exactos.
8. Planificación `PLAN/REL/TASK` y selección de una tarea ejecutable.
9. Readiness conjunto de especificación, entrega y automatización.
10. Implementación autorizada y verificación G3/G4 con evidencia exacta.

El sistema resume la definición tras el encuadre, al cerrar un bloque funcional material, al consolidar solución, UX o decisiones técnicas, antes de readiness, cuando se reabre una dimensión suficiente, al pausar y cuando la persona lo solicita. Evita repetir el snapshot tras cambios menores y declara siempre fase y alcance o incremento. Los estados `unknown`, `partial`, `sufficient` y `not-applicable: motivo` se refieren al alcance indicado; no forman un porcentaje ni equivalen a aprobación.

## Repositorio existente

Empieza con preflight e inventario estático de solo lectura. Después se validan intención y reglas de negocio, se reconcilian realidad y deseo, se elige entre documentación, normalización progresiva o modernización planificada y, solo con autorización, se materializa una baseline documental aditiva. La estrategia elegida no autoriza cambios funcionales durante la adopción.

## Estados de una puerta

- `ready`: no hay bloqueos conocidos para el alcance evaluado.
- `ready-with-non-blocking-pending`: puede continuar, conservando pendientes no bloqueantes.
- `blocked`: faltan decisiones o evidencias indispensables para el alcance indicado.

El bloqueo de una parte no paraliza trabajo independiente y un estado listo no equivale a autorización de implementación.

Readiness muestra además dos ejes. `specification_readiness` evalúa si el contrato funcional está listo; `automation_support` determina si el perfil confirmado dispone de automatización implementable. El estado combinado solo permite preparar implementación cuando ambos son favorables, pero una limitación de automatización no reescribe la conclusión documental ni selecciona otra pila.

## Handoff y evidencia

La fase `preimplementation` exige una cadena no vacía desde requisitos confirmados hasta criterios, decisión o no aplicabilidad motivada, incremento y pruebas. La fase `verification` añade evidencia ejecutada y aplicable. Los elementos rechazados, sustituidos o retirados se conservan como historial, pero no alimentan el contrato activo.

Una tarea recorre `backlog → ready → in-progress → in-review → done`; `blocked` y `cancelled` son estados explícitos. La tabla resume; la ficha conserva detalle e historial. `done` exige evidencia ligada a revisión, build, artefacto, entorno y gates. El modelo de entrega puede cambiar durante la vida del producto mediante un nuevo `CHG-###` y una transición efectiva, sin reescribir releases o evidencias anteriores.

## Evolución del contrato

Las rutas nuevas y adopciones materializadas con 0.8.0 usan método 1.2.0 y esquema 1.2. Los proyectos 1.0/1.1 continúan en compatibilidad. Cada salto es explícito y reversible. `1.1 → 1.2` crea el contrato de gobierno, arquitectura, planificación y tareas como pendiente; no confirma decisiones, perfiles ni evidencias.
