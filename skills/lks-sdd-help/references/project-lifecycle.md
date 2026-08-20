# Ciclo de vida y rutas

## Aplicación nueva

1. Encuadre y clasificación.
2. Descubrimiento y alcance.
3. Especificación.
4. Diseño de experiencia e interfaz, cuando resulte aplicable, incluida validación humana de prototipos visuales.
5. Diseño técnico y decisiones.
6. Planificación por incrementos.
7. Readiness del incremento.
8. Implementación autorizada del perfil seleccionado y verificación con evidencia.

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

## Evolución del contrato

Las rutas nuevas y las adopciones materializadas con 0.7.0 usan método 1.1.0 y esquema 1.1. Un proyecto 1.0 puede continuar en modo de compatibilidad. Migrarlo es una operación explícita, reversible y de un salto. Toda entrada de `human_review_required` bloquea siempre la aplicación antes de escribir; la persona debe resolver cada entrada listada en los Markdown canónicos 1.0, validarlos y repetir el preview hasta que la lista quede vacía. Revisar la lista no confirma decisiones automáticamente. La `Identity` agregada no puede separarse en origen: se materializa como tres dominios `pending` con motivo, permite validar el resultado migrado y bloquea readiness hasta su resolución explícita en 1.1.
