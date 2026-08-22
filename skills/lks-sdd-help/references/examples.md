# Ejemplos y prompts de inicio

## Respuesta breve

> Explícame LKS-SDD en dos minutos. No modifiques nada.

Resultado esperado: valor práctico, diferencia entre especificación y código, límites de autoridad y una opción de siguiente paso.

## Aplicación nueva

> Usa `$lks-sdd-define` para ayudarme a delimitar una aplicación nueva. Registra propuestas y decisiones por separado y no generes código.

Resultado esperado: si la idea es ambigua, no la generaliza. Pregunta en tandas de una a tres por dominio, usuario, tarea o decisión, entradas, reglas y resultado; ofrece opciones etiquetadas como propuestas, además de otra respuesta o `No lo sé todavía`.

## Idea ambigua

> Quiero una calculadora. Ayúdame a descubrir qué aplicación necesito antes de dar por supuesto su ámbito o funciones.

Resultado esperado: pregunta primero si la calculadora pertenece a un proceso profesional concreto, quién decide o actúa con el resultado y qué entradas, reglas o fuentes hacen válido el cálculo. No selecciona fórmulas, pantallas ni tecnología.

## Estado de la definición

> Muéstrame un resumen sencillo del estado actual. No cambies archivos ni continúes la definición.

Resultado esperado: separa validez estructural y suficiencia; agrupa dimensiones suficientes, parciales y desconocidas, muestra bloqueos y siguiente decisión, no usa porcentajes y ofrece detalle bajo petición.

## Repositorio existente

> Explícame cómo sería la adopción segura de este repositorio. Por ahora, no lo inspecciones ni crees archivos.

Resultado esperado: explicación del preflight, alcance, exclusiones, separación entre `as-is` e intención y pasos de confirmación. Como el prompt prohíbe inspeccionar, no se ejecuta inventario ni se crean archivos.

## Readiness

> Usa `$lks-sdd-assess-readiness` para evaluar `INC-001`. No corrijas documentos ni implementes nada.

Resultado esperado: informa por separado especificación, automatización, completitud integral, porción seleccionada, autorización, implementación, verificación y entrega. Mantiene `TASK-001: ready` aunque la release sea `partial`, sin convertirlo en readiness global, y explica el cambio mínimo para cada eje.

## Cierre con planificación parcial

> La especificación de `INC-001` está cerrada y `TASK-001` está lista. Muéstrame el handoff y qué falta antes de implementar toda la release.

Resultado esperado: resume lo confirmado; declara `planning_completeness: partial`; enumera alcance, aceptación y pruebas sin tarea; recomienda completar la planificación; ofrece planificación integral, porción incremental explícita o pausa; y pide confirmación antes de materializar tareas propuestas.

## Reanudación

> Reanuda la implementación desde el último checkpoint. No repitas trabajo ni supongas que los checks pendientes pasaron.

Resultado esperado: valida rama, revisión, árbol, archivos, huellas y autorización; muestra entregables completos/parciales, checks y bloqueos; recomienda continuar, reconciliar o replanificar; y expone tareas independientes seguras.

## Trazabilidad previa a implementación

> Comprueba la trazabilidad `preimplementation` de `INC-001`. No exijas evidencias de pruebas que todavía no se han ejecutado y no cambies archivos.

Resultado esperado: exige requisito, aceptación, decisión o no aplicabilidad motivada, incremento y prueba; no exige `EVID-###` hasta verificación y no acepta una comprobación vacía.

## Gobierno de entrega inicial

> Ayúdame a definir, antes de implementar, si este proyecto funciona como entrega cerrada, evolución continua o mantenimiento evolutivo; propón versionado, ramas, entornos, promoción, despliegue y reversión. Conserva todo como propuesta hasta mi confirmación.

Resultado esperado: compara `bounded-release`, `continuous-evolution` y `maintenance-stream` según el contexto real; no impone Git Flow, trunk-based ni SemVer; identifica responsables, gates y evidencias; y registra las decisiones confirmadas en `delivery-governance.md`.

## Cambio del modelo de proyecto

> El proyecto pasa de una entrega cerrada a evolutivos continuos. Analiza el impacto y prepara la transición sin reescribir la historia ni darla por aprobada.

Resultado esperado: crea una transición versionada con modelo anterior y propuesto, motivo, fecha efectiva, impacto en ramas, versiones, planes, releases, entornos y trabajo abierto, además de aprobación y rollback pendientes. El cambio solo entra en vigor después del gate humano definido.

## Plan y tablero de tareas

> Muéstrame el tablero de `PLAN-001`, los bloqueos y dependencias; después define `TASK-004` de forma independiente. No implementes código.

Resultado esperado: ofrece una tabla compacta por `REL-###` con símbolo, estado, salud, progreso, versión, dependencias y bloqueo. El detalle de `TASK-004` conserva alcance, trazabilidad, unidades desplegables, plan, aceptación, pruebas, riesgos, problemas y evidencia; la tabla es una vista de seguimiento, no la fuente única de definición.

## Arquitectura multiperfil

> La solución tiene una SPA Angular, una API y un procesador Kafka. Comprueba qué perfiles cerrados existen y cuáles están realmente soportados; no sustituyas mi arquitectura por otra.

Resultado esperado: asigna un `BIND-###` por `UNIT-###`, distingue perfil `active` certificado de `candidate`, y explica que las capabilities se reutilizan pero no homologan una combinación. Un perfil sin certificación exacta puede especificarse, pero bloquea la automatización garantizada de esa unidad.

## Alternativa tecnológica

> Compara la pila preferente con mi alternativa, pero conserva ambas como propuestas hasta que yo confirme una decisión.

## Diseño de frontend

> Sigue definiendo las pantallas y la interacción. Cuando la base sea suficiente, prepara propuestas visuales con ImageGen para que pueda validarlas antes de implementar.

Resultado esperado: `lks-sdd-define` mantiene el contrato UX, genera imágenes solo después de definir comportamiento y las registra como propuestas hasta confirmación humana. No crea código ni una skill adicional.
