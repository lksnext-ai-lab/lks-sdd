# Ciclo de vida y rutas

## Aplicación nueva

1. Encuadre y clasificación.
2. Descubrimiento y alcance.
3. Especificación.
4. Diseño técnico y decisiones.
5. Planificación por incrementos.
6. Readiness del incremento.
7. Implementación y verificación, pendientes en M2.

## Repositorio existente

Empieza con preflight y descubrimiento estático de solo lectura. Después se validan intención y reglas de negocio, se reconcilian realidad y deseo, se elige entre documentación, normalización progresiva o modernización planificada y, solo con autorización, se materializa una baseline documental aditiva. La skill que automatiza esta ruta está en backlog para M3; M1 solo la explica y evita escrituras prematuras.

## Estados de una puerta

- `ready`: no hay bloqueos conocidos para el alcance evaluado.
- `ready-with-non-blocking-pending`: puede continuar, conservando pendientes no bloqueantes.
- `blocked`: faltan decisiones o evidencias indispensables para el alcance indicado.

El bloqueo de una parte no paraliza trabajo independiente y un estado listo no equivale a autorización de implementación.
