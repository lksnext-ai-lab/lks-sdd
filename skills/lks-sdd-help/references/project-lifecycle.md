# Ciclo de vida y rutas

## Aplicación nueva

1. Encuadre y clasificación.
2. Descubrimiento y alcance.
3. Especificación.
4. Diseño técnico y decisiones.
5. Planificación por incrementos.
6. Readiness del incremento.
7. Implementación autorizada del perfil seleccionado y verificación con evidencia.

## Repositorio existente

Empieza con preflight e inventario estático de solo lectura. Después se validan intención y reglas de negocio, se reconcilian realidad y deseo, se elige entre documentación, normalización progresiva o modernización planificada y, solo con autorización, se materializa una baseline documental aditiva. La estrategia elegida no autoriza cambios funcionales durante la adopción.

## Estados de una puerta

- `ready`: no hay bloqueos conocidos para el alcance evaluado.
- `ready-with-non-blocking-pending`: puede continuar, conservando pendientes no bloqueantes.
- `blocked`: faltan decisiones o evidencias indispensables para el alcance indicado.

El bloqueo de una parte no paraliza trabajo independiente y un estado listo no equivale a autorización de implementación.
