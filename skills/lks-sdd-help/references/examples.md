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

Resultado esperado: informa por separado `specification_readiness` y `automation_support`, mantiene `implementation_authorized: false` y explica el cambio mínimo para cada bloqueo. Una pila alternativa suficientemente definida no se sustituye por H0 aunque carezca de automatización.

## Trazabilidad previa a implementación

> Comprueba la trazabilidad `preimplementation` de `INC-001`. No exijas evidencias de pruebas que todavía no se han ejecutado y no cambies archivos.

Resultado esperado: exige requisito, aceptación, decisión o no aplicabilidad motivada, incremento y prueba; no exige `EVID-###` hasta verificación y no acepta una comprobación vacía.

## Alternativa tecnológica

> Compara la pila preferente con mi alternativa, pero conserva ambas como propuestas hasta que yo confirme una decisión.

## Diseño de frontend

> Sigue definiendo las pantallas y la interacción. Cuando la base sea suficiente, prepara propuestas visuales con ImageGen para que pueda validarlas antes de implementar.

Resultado esperado: `lks-sdd-define` mantiene el contrato UX, genera imágenes solo después de definir comportamiento y las registra como propuestas hasta confirmación humana. No crea código ni una skill adicional.
